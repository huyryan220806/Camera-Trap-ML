"""Pinned W6 candidate cache; W5/native source and existing defaults stay separate."""
from collections import OrderedDict
import copy
import gc
import json
from pathlib import Path
import subprocess
import threading

from .classifier import MAX_BOXES, crop_coordinates
from .detector import ROOT, digest

REGISTRY = ROOT / 'configs/demo_w6.json'
MODEL_IDS = tuple('DINO_W6_' + run for run in ('R1', 'R2', 'R3', 'R4'))


class W6Cache:
    def __init__(self, base, repo, registry=REGISTRY, capacity=1):
        if capacity != 1:
            raise ValueError('W6 CPU memory policy holds one candidate at a time')
        self.base, self.repo, self.registry_path = base, Path(repo).resolve() if repo else None, Path(registry)
        self.models = OrderedDict()
        self.lock = threading.RLock()
        self.load_count = 0

    def registry(self):
        value = json.loads(self.registry_path.read_text(encoding='utf-8'))
        if value['schema_version'] != 'tv4-w6-1.0' or set(value['models']) != set(MODEL_IDS):
            raise ValueError('Only pinned R1-R4 are registered for this delivery')
        return value

    def names(self):
        return self.base.names()

    def folder(self, entry):
        path = (ROOT / entry['package']).resolve()
        if not path.is_relative_to((ROOT / 'outputs').resolve()):
            raise ValueError('W6 packages must be under outputs')
        return path

    def status(self):
        value = self.base.status()
        for key, entry in self.registry()['models'].items():
            value[key] = {'enabled': bool(self.repo and entry['enabled']),
                'checkpoint_present': (self.folder(entry) / 'best_model.pt').is_file(),
                'training_input': 'crop', 'dataset': 'comparison_v1', 'version': entry['run_id'] + '_attempt01',
                'approval': entry['approval'], 'feature_dim': entry['feature_dim'], 'device': 'cpu'}
        return value

    def validate(self, kind):
        from src.training import dino_w6 as native
        registry = self.registry()
        entry = registry['models'][kind]
        if not self.repo or not entry['enabled']:
            raise ValueError('W6 candidate disabled; no fallback')
        folder = self.folder(entry)
        pins = {'best_model.pt': entry['checkpoint_sha256'], 'config.json': entry['config_raw_sha256'],
            'handoff.json': entry['handoff_sha256'], 'source_index.json': entry['source_index_sha256'],
            'preprocessing.json': entry['preprocessing_sha256'], 'class_map.json': entry['class_map_sha256']}
        if (folder / 'best_model.pt').stat().st_size != entry['checkpoint_bytes']:
            raise ValueError('W6 checkpoint size mismatch')
        for name, expected in pins.items():
            if digest(folder / name) != expected:
                raise ValueError('W6 package checksum mismatch: ' + name)
        for name, expected in [('dino_w6.py', registry['native_source_sha256']),
                               ('dino_probe.py', registry['w5_source_sha256'])]:
            if digest(ROOT / 'src/training' / name) != expected:
                raise ValueError('Locked native loader source changed: ' + name)
        revision = subprocess.check_output(['git', '-C', str(self.repo), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(self.repo), 'status', '--porcelain', '--untracked-files=normal'], text=True).strip()
        if revision != registry['vendor_commit'] or dirty:
            raise ValueError('W6 vendor checkout mismatch/dirty')
        config = json.loads((folder / 'config.json').read_text())
        if native.digest(config) != entry['config_sha256'] or config['run_id'] != entry['run_id']:
            raise ValueError('W6 config identity mismatch')
        if config['pooling'] != entry['pooling'] or config['feature_dim'] != entry['feature_dim']:
            raise ValueError('W6 pooling/dimension mismatch')
        names = json.loads((folder / 'class_map.json').read_text())
        if [names[str(i)] for i in range(8)] != self.names():
            raise ValueError('W6 class order mismatch')
        return native, folder, config, entry, registry

    def logits(self, crops, kind):
        import torch
        if not 1 <= len(crops) <= MAX_BOXES:
            raise ValueError('W6 supports 1-64 per-detection crops')
        with self.lock, torch.inference_mode():
            native, folder, config, entry, registry = self.validate(kind)
            identity = json.dumps({'entry': entry, 'preprocess': config['preprocessing'],
                'native': registry['native_source_sha256'], 'device': 'cpu'}, sort_keys=True)
            hit = identity in self.models
            if not hit:
                self.models.clear(); gc.collect()
                model, transform, payload = native.load_package(folder / 'best_model.pt', entry['checkpoint_sha256'], self.repo, 'cpu')
                if payload['class_map'] != json.loads((folder / 'class_map.json').read_text()) or payload['config'] != config:
                    raise ValueError('Checkpoint config/class map differs from package')
                if any(not torch.isfinite(t).all() for t in payload['model'].values()):
                    raise ValueError('Nonfinite W6 checkpoint tensors')
                model.eval().requires_grad_(False)
                self.models[identity] = model, transform
                self.load_count += 1
            model, transform = self.models[identity]
            logits = torch.cat([native.predict_crops(model, transform, crops[i:i+8], 'cpu') for i in range(0,len(crops),8)])
            if logits.shape != (len(crops),8) or not torch.isfinite(logits).all():
                raise ValueError('Invalid W6 per-box logits')
            return logits, {'classifier_id': kind, 'checkpoint_sha256': entry['checkpoint_sha256'],
                'training_input': 'crop', 'inference_input': 'detector_crop',
                'preprocessing': {**copy.deepcopy(config['preprocessing']), 'image_size':256,
                    'model_version': entry['run_id'] + '_attempt01', 'dataset_version':config['dataset'],
                    'dataset_sha256':config['dataset_sha256'], 'config_sha256':entry['config_sha256'],
                    'source_commit':entry['source_sha'], 'source_sha256':registry['native_source_sha256'],
                    'vendor_commit':registry['vendor_commit'], 'pooling':entry['pooling'], 'feature_dim':entry['feature_dim'],
                    'evaluation_type':'GT-box validation; not detector end-to-end accuracy', 'precision':'FP32',
                    'approval': entry['approval'], 'max_crop_batch':8},
                'cache_hit':hit, 'model_load_count':self.load_count, 'device':'cpu'}

    def predict(self, image, detections, kind):
        if kind not in MODEL_IDS:
            return self.base.predict(image, detections, kind)
        coordinates = [crop_coordinates(d['bbox_xywh'], image.size) for d in detections]
        crops = [image.convert('RGB').crop(box) for box in coordinates]
        logits, metadata = self.logits(crops, kind)
        names = self.names()
        predictions = []
        for scores in logits.softmax(-1).tolist():
            ids = sorted(range(8), key=lambda i:(-scores[i],i))[:3]
            predictions.append([{'class_id':i,'label':names[i],'score':scores[i]} for i in ids])
        return predictions, metadata
