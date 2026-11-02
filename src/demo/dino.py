"""Explicit opt-in DINO candidate. B2 remains in its separate existing cache."""
from pathlib import Path
import threading
import time

from .classifier import crop_coordinates, MAX_BOXES
from .detector import digest, ROOT

MODEL_ID = 'DINOv3_LP_run01'
CHECKPOINT_SHA = 'acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3'
ARCHITECTURE_COMMIT = '6876159a11b4df116f30f667f8c9888617df0751'
SOURCE_COMMIT = 'aa64fd7661827af78ddec4e3e0155b2b9c87b9e2'


class DinoCache:
    def __init__(self, base, package=None, repo=None):
        self.base = base
        self.package = Path(package).resolve() if package else None
        self.repo = Path(repo).resolve() if repo else None
        self.lock = threading.RLock()
        self.loaded = None
        self.load_count = 0

    def names(self):
        return self.base.names()

    def status(self):
        result = self.base.status()
        result[MODEL_ID] = {'enabled': bool(self.package and self.repo),
            'checkpoint_present': bool(self.package and (self.package / 'best_model.pt').is_file()),
            'training_input': 'crop'}
        return result

    def validate(self):
        import subprocess
        from src.training import dino_probe as native
        if not self.package or not self.repo:
            raise ValueError('DINO candidate not configured; select B2 explicitly')
        checkpoint = self.package / 'best_model.pt'
        if checkpoint.stat().st_size != 86851958 or digest(checkpoint) != CHECKPOINT_SHA:
            raise ValueError('DINO checkpoint SHA/size mismatch')
        if subprocess.check_output(['git', '-C', str(self.repo), 'rev-parse', 'HEAD'], text=True).strip() != ARCHITECTURE_COMMIT:
            raise ValueError('DINO architecture commit mismatch')
        if subprocess.check_output(['git', '-C', str(self.repo), 'status', '--porcelain', '--untracked-files=normal'], text=True).strip():
            raise ValueError('DINO architecture checkout must be clean')
        # Hash the tracked source against the locked native implementation, including warm requests.
        source = ROOT / 'src/training/dino_probe.py'
        expected = subprocess.check_output(['git', '-C', str(ROOT), 'show', SOURCE_COMMIT + ':src/training/dino_probe.py'])
        import hashlib
        if digest(source) != hashlib.sha256(expected).hexdigest():
            raise ValueError('DINO native loader source differs from pinned training source')
        return native, checkpoint

    def logits(self, crops):
        import torch
        if not 1 <= len(crops) <= MAX_BOXES:
            raise ValueError('DINO supports 1-64 crops')
        with self.lock, torch.inference_mode():
            native, checkpoint = self.validate()
            hit = self.loaded is not None
            started = time.perf_counter()
            if not hit:
                torch.set_num_threads(min(4, torch.get_num_threads()))
                torch.backends.cuda.matmul.allow_tf32 = False
                torch.backends.cudnn.allow_tf32 = False
                backbone, head, transform, payload = native.load_package(checkpoint, CHECKPOINT_SHA, device='cpu', repo_dir=self.repo)
                config = payload['config']
                names = [payload['class_map'][str(i)] for i in range(8)]
                if names != self.names() or config['model']['name'] != 'dinov3_vits16' or config['model']['repo_commit'] != ARCHITECTURE_COMMIT:
                    raise ValueError('DINO architecture/class mapping mismatch')
                if config['preprocessing'] != 'dinov3_square256_bilinear_uint8':
                    raise ValueError('DINO preprocessing mismatch')
                if any(not torch.isfinite(t).all() for section in ('backbone', 'head') for t in payload[section].values()):
                    raise ValueError('Non-finite DINO checkpoint')
                head.requires_grad_(False)
                self.loaded = backbone, head, transform
                self.load_count += 1
            backbone, head, transform = self.loaded
            rows = []
            for offset in range(0, len(crops), 8):
                rows.append(native.predict_crops(backbone, head, transform, crops[offset:offset + 8], 'cpu'))
            logits = torch.cat(rows)
            if logits.shape != (len(crops), 8) or not torch.isfinite(logits).all():
                raise ValueError('Invalid DINO per-crop logits')
            return logits, {'classifier_id': MODEL_ID, 'checkpoint_sha256': CHECKPOINT_SHA,
                'training_input': 'crop', 'inference_input': 'detector_crop',
                'preprocessing': {'id': 'dinov3_square256_bilinear_uint8', 'rgb': True, 'exif_transpose': False,
                    'image_size': 256, 'pooling': 'x_norm_clstoken', 'architecture_commit': ARCHITECTURE_COMMIT,
                    'source_commit': SOURCE_COMMIT, 'precision': 'float32', 'max_crop_batch': 8,
                    'adapter_wall_ms': round((time.perf_counter() - started) * 1000, 3)},
                'cache_hit': hit, 'model_load_count': self.load_count, 'device': 'cpu'}

    def predict(self, image, detections, kind):
        if kind != MODEL_ID:
            return self.base.predict(image, detections, kind)
        boxes = [crop_coordinates(d['bbox_xywh'], image.size) for d in detections]
        crops = [image.convert('RGB').crop(box) for box in boxes]
        logits, metadata = self.logits(crops)
        names = self.names()
        predictions = []
        for scores in logits.softmax(-1).tolist():
            ids = sorted(range(8), key=lambda i: (-scores[i], i))[:3]
            predictions.append([{'class_id': i, 'label': names[i], 'score': scores[i]} for i in ids])
        return predictions, metadata
