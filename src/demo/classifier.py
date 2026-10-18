"""Verified ResNet18 checkpoints with a bounded, process-local CPU cache."""
from collections import OrderedDict
import copy
import json
import math
from pathlib import Path
import re
import threading

from .detector import ROOT, digest

REGISTRY_PATH = ROOT / 'configs/demo_classifiers.json'
CLASS_MAP_PATH = 'data/processed/v1/class_map.json'
MAX_BOXES = 64


def crop_coordinates(box, size):
    if len(box) != 4 or any(type(v) not in (int, float) or not math.isfinite(v) for v in box):
        raise ValueError('Invalid crop coordinates')
    x, y, w, h = box
    width, height = size
    if min(x, y) < 0 or min(w, h) <= 0 or x + w > width + 1e-5 or y + h > height + 1e-5:
        raise ValueError('Crop outside source raster')
    left, top = max(0, round(x)), max(0, round(y))
    right, bottom = min(width, round(x + w)), min(height, round(y + h))
    if right - left < 8 or bottom - top < 8:
        raise ValueError('Crop smaller than 8 pixels; review the image')
    return left, top, right, bottom


def validate_preprocessing(spec):
    if set(spec) != {'resize_mode', 'resize_size', 'image_size', 'mean', 'std'}:
        raise ValueError('Incomplete preprocessing contract')
    if spec['resize_mode'] not in ('center_crop', 'stretch'):
        raise ValueError('Unknown resize mode')
    if any(type(spec[k]) is not int or not 8 <= spec[k] <= 1024 for k in ('image_size', 'resize_size')):
        raise ValueError('Invalid transform sizes')
    if spec['resize_mode'] == 'center_crop' and spec['resize_size'] < spec['image_size']:
        raise ValueError('Resize cannot be smaller than center crop')
    if spec['resize_mode'] == 'stretch' and spec['resize_size'] != spec['image_size']:
        raise ValueError('Stretch dimensions must match image size')
    for key in ('mean', 'std'):
        if len(spec[key]) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in spec[key]):
            raise ValueError('Invalid normalization')
    if any(v <= 0 for v in spec['std']):
        raise ValueError('Normalization std must be positive')


def checkpoint_model(checkpoint, kind, entry, names):
    import torch
    from torchvision import transforms as T
    from torchvision.models import resnet18

    expected = {i: name for i, name in enumerate(names)}
    mapping = checkpoint.get('idx_to_class', {})
    if mapping not in (expected, {str(i): name for i, name in expected.items()}):
        raise ValueError('Checkpoint needs an explicit matching idx_to_class; never guess class order')
    if checkpoint.get('class_to_idx') != {name: i for i, name in expected.items()} or checkpoint.get('num_classes') != len(names):
        raise ValueError('Checkpoint class mapping differs from SWG v1')
    spec = entry['preprocessing']
    validate_preprocessing(spec)
    if kind in ('B0', 'B1'):
        if checkpoint.get('model_name') != 'resnet18' or checkpoint.get('freeze_backbone') is not (kind == 'B0'):
            raise ValueError('Wrong B0/B1 architecture or freeze policy')
        if kind == 'B1' and checkpoint.get('kind') != 'OFFICIAL':
            raise ValueError('B1 requires an OFFICIAL checkpoint, not synthetic smoke')
        config = checkpoint['config']
        trained = {'resize_mode': 'center_crop', 'resize_size': config['data']['resize_size'],
                   'image_size': config['data']['image_size'], 'mean': config['preprocessing']['mean'],
                   'std': config['preprocessing']['std']}
        if trained != spec or entry['training_input'] != 'full_image':
            raise ValueError('B0/B1 preprocessing differs from checkpoint')
        state = checkpoint['model_state_dict']
    else:
        # TV3 wrapper is backbone ResNet18 + Dropout/Linear. Dropout is identity in eval.
        if checkpoint.get('kind') != 'OFFICIAL' or checkpoint.get('config', {}).get('model', {}).get('backbone') != 'resnet18':
            raise ValueError('B2 requires an OFFICIAL ResNet18 checkpoint')
        if checkpoint.get('inference_preprocessing') != spec or entry['training_input'] != 'crop':
            raise ValueError('B2 requires explicit, matching inference_preprocessing')
        state = {}
        for name, tensor in checkpoint['model_state_dict'].items():
            if name.startswith('backbone.'):
                target = name[len('backbone.'):]
            elif name in ('classifier.1.weight', 'classifier.1.bias'):
                target = 'fc.' + name.rsplit('.', 1)[-1]
            else:
                raise ValueError('Unsupported B2 state key: ' + name)
            if target in state:
                raise ValueError('Repeated model state key')
            state[target] = tensor
    if any(not torch.is_tensor(t) or not torch.isfinite(t).all() for t in state.values()):
        raise ValueError('Non-finite or invalid model tensors')
    model = resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, len(names))
    model.load_state_dict(state, strict=True)
    model.eval().requires_grad_(False)
    resize = spec['resize_size'] if spec['resize_mode'] == 'center_crop' else (spec['image_size'],) * 2
    operations = [T.Resize(resize, interpolation=T.InterpolationMode.BILINEAR, antialias=True)]
    if spec['resize_mode'] == 'center_crop':
        operations.append(T.CenterCrop(spec['image_size']))
    operations += [T.ToTensor(), T.Normalize(spec['mean'], spec['std'])]
    return model, T.Compose(operations)


class ClassifierCache:
    def __init__(self, registry_path=REGISTRY_PATH, root=ROOT, capacity=2):
        if type(capacity) is not int or capacity < 1:
            raise ValueError('Cache capacity must be positive')
        self.root, self.registry_path = Path(root).resolve(), Path(registry_path)
        self.capacity, self.lock = capacity, threading.RLock()
        self.models = OrderedDict()
        self.load_count = 0

    def registry(self):
        registry = json.loads(self.registry_path.read_text(encoding='utf-8'))
        if registry.get('schema_version') != '1.0' or set(registry['models']) != {'B0', 'B1', 'B2'}:
            raise ValueError('Invalid classifier registry')
        return registry['models']

    def names(self):
        classes = json.loads((self.root / CLASS_MAP_PATH).read_text(encoding='utf-8'))
        if set(classes) != {str(i) for i in range(8)} or len(set(classes.values())) != 8:
            raise ValueError('Expected eight unique SWG v1 classes')
        return [classes[str(i)] for i in range(8)]

    def path(self, entry):
        raw = Path(entry['checkpoint'])
        path = (self.root / raw).resolve()
        if raw.is_absolute() or not path.is_relative_to(self.root / 'outputs'):
            raise ValueError('Demo checkpoints must be under outputs/')
        return path

    def status(self):
        with self.lock:
            return {key: {'enabled': entry['enabled'] is True,
                          'checkpoint_present': self.path(entry).is_file(),
                          'training_input': entry['training_input']}
                    for key, entry in self.registry().items()}

    def _get(self, kind):
        import torch
        entry = self.registry()[kind]
        if entry['enabled'] is not True:
            raise ValueError(f'{kind} checkpoint has not been handed off; no fallback')
        expected = entry['sha256']
        if not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected):
            raise ValueError('Missing pinned checkpoint SHA-256')
        path = self.path(entry)
        if type(entry['checkpoint_bytes']) is not int or not 0 < entry['checkpoint_bytes'] <= 256 * 1024 * 1024:
            raise ValueError('Missing or excessive checkpoint size')
        if path.stat().st_size != entry['checkpoint_bytes'] or digest(path) != expected:
            raise ValueError('Checkpoint checksum/size mismatch')
        names = self.names()
        key = (kind, json.dumps(entry, sort_keys=True), tuple(names))
        hit = key in self.models
        if not hit:
            checkpoint = torch.load(path, map_location='cpu', weights_only=True)
            model, transform = checkpoint_model(checkpoint, kind, entry, names)
            if digest(path) != expected:
                raise ValueError('Checkpoint changed during load')
            torch.set_num_threads(min(4, torch.get_num_threads()))
            self.models[key] = (model, transform)
            self.load_count += 1
            while len(self.models) > self.capacity:
                self.models.popitem(last=False)
        self.models.move_to_end(key)
        model, transform = self.models[key]
        return model, transform, names, {
            'classifier_id': kind, 'checkpoint_sha256': expected,
            'training_input': entry['training_input'], 'inference_input': 'detector_crop',
            'preprocessing': copy.deepcopy(entry['preprocessing']),
            'cache_hit': hit, 'model_load_count': self.load_count, 'device': 'cpu'}

    def predict(self, image, detections, kind):
        import torch
        if kind not in ('B0', 'B1', 'B2') or not 1 <= len(detections) <= MAX_BOXES:
            raise ValueError('Unknown classifier or unsupported number of boxes (1-64)')
        coordinates = [crop_coordinates(d['bbox_xywh'], image.size) for d in detections]
        with self.lock, torch.inference_mode():
            model, transform, names, metadata = self._get(kind)
            predictions = []
            for offset in range(0, len(coordinates), 8):
                batch = torch.stack([transform(image.crop(box)) for box in coordinates[offset:offset + 8]])
                logits = model(batch)
                if logits.shape != (len(batch), len(names)) or not torch.isfinite(logits).all():
                    raise ValueError('Classifier returned invalid logits')
                scores = logits.softmax(dim=1)
                for row in scores.tolist():
                    ids = sorted(range(len(names)), key=lambda i: (-row[i], i))[:3]
                    predictions.append([{'class_id': i, 'label': names[i], 'score': row[i]} for i in ids])
            return predictions, metadata
