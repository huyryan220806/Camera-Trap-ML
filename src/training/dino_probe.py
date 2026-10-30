"""TV3 W5: frozen DINO features and image-balanced linear probing.

Only comparison_v1 train/validation are accepted. No network calls, test reader,
automatic model fallback, or implicit changes to a frozen data release.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import random
import re
import subprocess
import sys
import time

import numpy as np
from PIL import Image
import PIL
import torch
from torch import nn
from torch.nn import functional as F
import torchvision
from torchvision import transforms as T
from torchvision.transforms import v2

ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = 'd9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f'
B2_SHA = '8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5'
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]
SPECS = {
    'dinov3_vits16': {'patch_size': 16, 'feature_dim': 384, 'preprocessing': 'dinov3_square256_bilinear_uint8'},
    'dinov2_vits14': {'patch_size': 14, 'feature_dim': 384, 'preprocessing': 'dinov2_short256_center224_bicubic_pil'},
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def atomic_torch(path, value):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    torch.save(value, tmp)
    os.replace(tmp, path)


@contextmanager
def writer_lock(folder):
    """OS lock, released on process death. The guard is never deleted."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'writer.guard').open('a+b') as f:
        if f.tell() == 0:
            f.write(b'0')
            f.flush()
        f.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            f.seek(0)
            if os.name == 'nt':
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def runtime():
    import sklearn
    cuda = torch.cuda.is_available()
    return {'python': sys.version, 'torch': str(torch.__version__),
            'torchvision': str(torchvision.__version__), 'pillow': PIL.__version__,
            'numpy': np.__version__, 'sklearn': sklearn.__version__,
            'cuda': torch.version.cuda, 'cudnn': torch.backends.cudnn.version(),
            'gpu': torch.cuda.get_device_name(0) if cuda else None,
            'vram_bytes': torch.cuda.get_device_properties(0).total_memory if cuda else None,
            'os': platform.platform(), 'cpu': platform.processor(),
            'num_threads': torch.get_num_threads(), 'num_interop_threads': torch.get_num_interop_threads(),
            'amp': False, 'tf32': False, 'deterministic_algorithms': True}


def seed_all(seed):
    os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def transform_for(name):
    if name == 'dinov3_vits16':
        # Official README: tensor uint8 resize before conversion to float.
        return v2.Compose([v2.ToImage(), v2.Resize((256, 256), interpolation=T.InterpolationMode.BILINEAR,
                                                antialias=True), v2.ToDtype(torch.float32, scale=True),
                           v2.Normalize(MEAN, STD)])
    if name == 'dinov2_vits14':
        return T.Compose([T.Resize(256, interpolation=T.InterpolationMode.BICUBIC, antialias=True),
                          T.CenterCrop(224), T.ToTensor(), T.Normalize(MEAN, STD)])
    raise ValueError('Unsupported backbone: ' + name)


def validate_config(c, pinned=True):
    m, t = c['model'], c['training']
    require(m['name'] in SPECS, 'Unsupported model')
    require(c['preprocessing'] == SPECS[m['name']]['preprocessing'], 'Preprocessing/model mismatch')
    require(m['pooling'] == 'x_norm_clstoken' and m['frozen'] is True, 'Only frozen CLS linear probe supported')
    require(c['data']['directory'] == 'data/processed/comparison_v1', 'Only comparison_v1 is released')
    require(c['data']['provenance_sha256'] == PROVENANCE, 'Wrong frozen release')
    require(re.fullmatch(r'[A-Za-z0-9_-]+', c['experiment_id']), 'Unsafe experiment ID')
    require(t['seed'] == 42, 'First registered run uses seed 42; register a new protocol for more seeds')
    require(t['optimizer'] == 'sgd' and t['scheduler'] == 'cosine', 'Unsupported optimizer/scheduler')
    require(t['epochs'] > 0 and t['patience'] > 0 and t['images_per_batch'] > 0, 'Invalid budget')
    require(t['lr'] > 0 and t['weight_decay'] >= 0 and 0 <= t['momentum'] < 1, 'Invalid optimizer settings')
    require(c['runtime']['amp'] is False, 'This implementation uses FP32; AMP is not implemented')
    require(c['runtime']['device'] in ('cpu', 'cuda'), 'Explicit cpu/cuda required')
    require(c['cache']['shard_size'] > 0 and c['cache']['batch_size'] > 0, 'Invalid cache batch')
    if pinned:
        require(re.fullmatch(r'[0-9a-f]{64}', m.get('weights_sha256') or ''), 'Pin pretrained SHA-256 first')
        require(re.fullmatch(r'[0-9a-f]{40}', m.get('repo_commit') or ''), 'Pin backbone Git commit first')


def read_release(root=ROOT, verify_images=True):
    folder = root / 'data/processed/comparison_v1'
    require(sha(folder / 'provenance.json') == PROVENANCE, 'Frozen provenance changed')
    p = read_json(folder / 'provenance.json')
    paths = ['class_map.json', 'train.jsonl', 'val.jsonl', 'b1/train.jsonl', 'b1/val.jsonl', 'b2/train.jsonl', 'b2/val.jsonl']
    for name in paths:
        require(sha(folder / name) == p['files_sha256'][name], 'Frozen file changed: ' + name)
    cmap = read_json(folder / 'class_map.json')
    require(set(cmap) == set(map(str, range(8))), 'Expected 8 fixed class IDs')
    rows, checked = {}, set()
    for split, nimages, ncrops in [('train', 2800, 3125), ('val', 600, 680)]:
        crops = [json.loads(s) for s in (folder / f'b2/{split}.jsonl').read_text(encoding='utf-8').splitlines()]
        sources = [json.loads(s) for s in (folder / f'b1/{split}.jsonl').read_text(encoding='utf-8').splitlines()]
        by_id = {s['image_id']: s for s in sources}
        counts = Counter(s['image_id'] for s in crops)
        require(len(crops) == ncrops and len(counts) == nimages, 'Unexpected release counts')
        require(set(counts) == set(by_id), 'B1/B2 source ID mismatch')
        require(len({s['crop_id'] for s in crops}) == len(crops), 'Duplicate crop IDs')
        for row in crops:
            source = by_id[row['image_id']]
            require(row['split'] == split and cmap[str(row['class_id'])] == row['label'] == source['label'], 'Label/split mismatch')
            require(row['quality'] == source['quality'], 'Crop/source hash mismatch')
            require(row['parent_crop_count'] == counts[row['image_id']], 'Parent count mismatch')
            require(abs(row['sample_weight'] - 1 / counts[row['image_id']]) < 1e-12, 'Invalid crop weight')
            box = row['bbox_xyxy']
            require(len(box) == 4 and all(type(v) is int for v in box), 'Crop bounds must be locked integers')
            require(0 <= box[0] < box[2] <= row['width'] and 0 <= box[1] < box[3] <= row['height'], 'Invalid bounds')
            if verify_images and row['image_id'] not in checked:
                path = (root / row['quality']['local_path']).resolve()
                require(path.is_relative_to((root / 'data/images').resolve()), 'Source path outside image cache')
                require(sha(path) == row['quality']['sha256'], 'Source byte hash mismatch: ' + str(path))
                with Image.open(path) as im:
                    rgb = im.convert('RGB')
                    require(rgb.size == (row['width'], row['height']), 'Source dimensions mismatch')
                    pixel = hashlib.sha256(f'RGB:{rgb.width}:{rgb.height}:'.encode() + rgb.tobytes()).hexdigest()
                    require(pixel == row['quality']['pixel_sha256'], 'Source RGB hash mismatch')
                checked.add(row['image_id'])
                if len(checked) % 250 == 0:
                    print(f'Preflight train/val {len(checked)}/3400', flush=True)
        rows[split] = crops
    require(not ({r['image_id'] for r in rows['train']} & {r['image_id'] for r in rows['val']}), 'Train/val overlap')
    return rows, cmap, {'provenance_sha256': PROVENANCE, 'files': {n: p['files_sha256'][n] for n in paths},
                        'verified_source_images': len(checked), 'test_opened': False}


def git_revision(repo):
    return subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()


def load_backbone(c, device, root=ROOT, state_dict=None):
    m = c['model']
    repo = (root / m['repo_dir']).resolve()
    require(git_revision(repo) == m['repo_commit'], 'Backbone repository commit changed')
    require(not subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=normal'], text=True).strip(),
            'Backbone checkout must be clean')
    if m['name'] == 'dinov3_vits16':
        # Upstream hubconf also imports segmentation and its optional dependencies.
        # Call the same official backbone factory without importing unrelated heads.
        import importlib
        sys.path.insert(0, str(repo))
        try:
            module = importlib.import_module('dinov3.hub.backbones')
            require(Path(module.__file__).resolve().is_relative_to(repo), 'DINOv3 imported from a different checkout')
            model = module.dinov3_vits16(pretrained=False)
        finally:
            sys.path.pop(0)
    else:
        model = torch.hub.load(str(repo), m['name'], source='local', pretrained=False)
    if state_dict is None:
        path = root / m['weights_path']
        require(sha(path) == m['weights_sha256'], 'Pretrained weight hash mismatch')
        state_dict = torch.load(path, map_location='cpu', weights_only=True)
    model.load_state_dict(state_dict, strict=True)
    model.requires_grad_(False).eval().to(device)
    return model


def extract(model, x):
    feature = model.forward_features(x)['x_norm_clstoken']
    require(feature.ndim == 2 and feature.shape[1] == 384 and torch.isfinite(feature).all().item(), 'Bad backbone features')
    return feature


def source_code_hash():
    return sha(Path(__file__))


def cache_identity(c, gate, env):
    return {'model': c['model'], 'preprocessing': c['preprocessing'], 'gate': gate,
            'implementation_sha256': source_code_hash(), 'runtime': env,
            'extraction': c['cache'], 'device': c['runtime']['device']}


def crop_tensor(row, transform, root=ROOT):
    # Geometry is applied once; no re-rounding, EXIF rotation, padding or JPEG cache.
    path = root / row['quality']['local_path']
    require(sha(path) == row['quality']['sha256'], 'Image changed after preflight')
    with Image.open(path) as im:
        return transform(im.convert('RGB').crop(tuple(row['bbox_xyxy'])))


def cache_features(c, rows, gate, env, root=ROOT):
    identity = cache_identity(c, gate, env)
    key = digest(identity)
    folder = root / 'outputs/tv3_w5/features' / key
    device = c['runtime']['device']
    with writer_lock(folder):
        index_path = folder / 'index.json'
        index = read_json(index_path) if index_path.exists() else {'identity': identity, 'key': key, 'shards': {}}
        require(index['identity'] == identity, 'Cache identity mismatch')
        model = None
        transform = transform_for(c['model']['name'])
        for split in ('train', 'val'):
            size = c['cache']['shard_size']
            for start in range(0, len(rows[split]), size):
                batch_rows = rows[split][start:start + size]
                name = f'{split}_{start:06d}.pt'
                path = folder / name
                ids = [r['crop_id'] for r in batch_rows]
                if name in index['shards']:
                    require(sha(path) == index['shards'][name]['sha256'], 'Corrupt shard: ' + name)
                    require(index['shards'][name]['crop_ids'] == ids, 'Shard crop ordering mismatch')
                    continue
                if model is None:
                    model = load_backbone(c, device, root)
                features = []
                started = time.perf_counter()
                with torch.inference_mode():
                    bs = c['cache']['batch_size']
                    for offset in range(0, len(batch_rows), bs):
                        x = torch.stack([crop_tensor(r, transform, root) for r in batch_rows[offset:offset + bs]]).to(device)
                        features.append(extract(model, x).float().cpu())
                atomic_torch(path, {'features': torch.cat(features), 'crop_ids': ids})
                index['shards'][name] = {'sha256': sha(path), 'crop_ids': ids, 'seconds': time.perf_counter() - started}
                atomic_json(index_path, index)
                print(f'Cached {split}: {start + len(batch_rows)}/{len(rows[split])}', flush=True)
        index['complete'] = True
        atomic_json(index_path, index)
    return folder, index


def load_features(folder, index, rows):
    result = {}
    for split in ('train', 'val'):
        parts, ids = [], []
        for name in sorted(n for n in index['shards'] if n.startswith(split + '_')):
            require(sha(folder / name) == index['shards'][name]['sha256'], 'Corrupt feature shard')
            part = torch.load(folder / name, map_location='cpu', weights_only=True)
            require(part['crop_ids'] == index['shards'][name]['crop_ids'], 'Shard IDs changed')
            parts.append(part['features'])
            ids.extend(part['crop_ids'])
        require(ids == [r['crop_id'] for r in rows[split]], 'Cache does not cover the full manifest in order')
        result[split] = torch.cat(parts)
        require(result[split].shape == (len(ids), 384) and torch.isfinite(result[split]).all().item(), 'Invalid cache shape/value')
    return result


def groups_for(rows):
    groups = defaultdict(list)
    for i, r in enumerate(rows):
        groups[r['image_id']].append(i)
    return list(groups.values())


def image_balanced_loss(logits, targets, groups):
    losses = F.cross_entropy(logits, targets, reduction='none')
    return torch.stack([losses[g].mean() for g in groups]).mean()


def evaluate_logits(logits, rows, cmap):
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
    require(logits.shape == (len(rows), len(cmap)), 'Logit shape mismatch')
    require(torch.isfinite(logits).all().item(), 'Non-finite logits')
    probs = logits.softmax(-1).double()
    predictions = []
    for group in groups_for(rows):
        labels = {rows[i]['class_id'] for i in group}
        require(len(labels) == 1, 'Inconsistent image labels')
        mean = probs[group].mean(0)
        predictions.append({'image_id': rows[group[0]]['image_id'], 'y_true': labels.pop(),
                            'y_pred': int(mean.argmax()), 'probabilities': mean.tolist(), 'crop_count': len(group)})
    truth = [p['y_true'] for p in predictions]
    pred = [p['y_pred'] for p in predictions]
    labels = list(range(len(cmap)))
    metrics = {'accuracy': float(accuracy_score(truth, pred)),
               'image_balanced_crop_ce': float(image_balanced_loss(logits, torch.tensor([r['class_id'] for r in rows]), groups_for(rows))),
               'macro_f1': float(f1_score(truth, pred, labels=labels, average='macro', zero_division=0)),
               'macro_precision': float(precision_score(truth, pred, labels=labels, average='macro', zero_division=0)),
               'macro_recall': float(recall_score(truth, pred, labels=labels, average='macro', zero_division=0)),
               'confusion_matrix': confusion_matrix(truth, pred, labels=labels).tolist(),
               'per_class': classification_report(truth, pred, labels=labels, target_names=[cmap[str(i)] for i in labels],
                                                   output_dict=True, zero_division=0),
               'images': len(predictions), 'crops': len(rows)}
    crop_predictions = [dict(crop_id=r['crop_id'], image_id=r['image_id'], y_true=r['class_id'],
                             logits=logits[i].tolist(), probabilities=probs[i].tolist()) for i, r in enumerate(rows)]
    return {'metrics': metrics, 'image_predictions': predictions, 'crop_predictions': crop_predictions}


def check_protocol(c, path):
    from src.training.dino_handoff import validate_protocol
    receipt = read_json(path)
    validate_protocol(c, receipt)
    return {'path': str(path), 'sha256': sha(path), 'content': receipt}


def rng_state():
    n = np.random.get_state()
    return {'python': random.getstate(), 'numpy': [n[0], n[1].tolist(), n[2], n[3], n[4]],
            'torch': torch.get_rng_state(), 'cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}


def restore_rng(s):
    random.setstate(s['python'])
    n = s['numpy']
    np.random.set_state((n[0], np.array(n[1], dtype=np.uint32), n[2], n[3], n[4]))
    torch.set_rng_state(s['torch'])
    if s['cuda']:
        torch.cuda.set_rng_state_all(s['cuda'])


def train_head(c, features, rows, cmap, folder, binding, resume=False):
    t = c['training']
    device = c['runtime']['device']
    head = nn.Linear(384, len(cmap)).to(device)
    optimizer = torch.optim.SGD(head.parameters(), lr=t['lr'], momentum=t['momentum'], weight_decay=t['weight_decay'])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=t['epochs'])
    path = folder / 'last_model.pt'
    start, history, best, bad, best_state, best_epoch = 0, [], -1., 0, None, 0
    if resume and path.exists():
        ck = torch.load(path, map_location='cpu', weights_only=True)
        require(ck['binding'] == binding, 'Resume config/cache/code/runtime changed; use a new experiment ID')
        head.load_state_dict(ck['head'])
        optimizer.load_state_dict(ck['optimizer'])
        scheduler.load_state_dict(ck['scheduler'])
        start, history, best, bad = ck['epoch'], ck['history'], ck['best'], ck['bad']
        best_state, best_epoch = ck['best_head'], ck['best_epoch']
        restore_rng(ck['rng'])
    train_x, val_x = features['train'].to(device), features['val'].to(device)
    targets = torch.tensor([r['class_id'] for r in rows['train']], device=device)
    groups = groups_for(rows['train'])
    for epoch in range(start, t['epochs']):
        if bad >= t['patience']:
            break
        started = time.perf_counter()
        if device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        order = torch.randperm(len(groups)).tolist()
        total_loss = 0.
        head.train()
        for offset in range(0, len(order), t['images_per_batch']):
            chosen = [groups[i] for i in order[offset:offset + t['images_per_batch']]]
            indices = [i for g in chosen for i in g]
            local_groups, cursor = [], 0
            for g in chosen:
                local_groups.append(list(range(cursor, cursor + len(g))))
                cursor += len(g)
            optimizer.zero_grad(set_to_none=True)
            loss = image_balanced_loss(head(train_x[indices]), targets[indices], local_groups)
            require(torch.isfinite(loss).item(), 'Non-finite train loss')
            loss.backward()
            optimizer.step()
            total_loss += float(loss.detach()) * len(chosen)
        head.eval()
        with torch.inference_mode():
            validation = evaluate_logits(head(val_x).cpu(), rows['val'], cmap)
        score = validation['metrics']['macro_f1']
        if score > best:
            best, bad, best_epoch = score, 0, epoch + 1
            best_state = {k: v.detach().cpu().clone() for k, v in head.state_dict().items()}
        else:
            bad += 1
        lr = optimizer.param_groups[0]['lr']
        scheduler.step()
        if device == 'cuda':
            torch.cuda.synchronize()
        history.append({'epoch': epoch + 1, 'lr': lr, 'train_loss': total_loss / len(groups),
                        'val_macro_f1': score, 'val_accuracy': validation['metrics']['accuracy'],
                        'val_loss': validation['metrics']['image_balanced_crop_ce'],
                        'seconds': time.perf_counter() - started,
                        'peak_allocated_vram': torch.cuda.max_memory_allocated() if device == 'cuda' else 0})
        # Authoritative epoch transaction includes log, best, optimizer, RNG. Partial epochs replay.
        atomic_torch(path, {'binding': binding, 'epoch': epoch + 1, 'head': head.state_dict(),
                           'optimizer': optimizer.state_dict(), 'scheduler': scheduler.state_dict(),
                           'rng': rng_state(), 'amp_scaler': None, 'history': history, 'best': best,
                           'bad': bad, 'best_head': best_state, 'best_epoch': best_epoch})
        atomic_json(folder / 'train_log.json', history)
        print(f'Epoch {epoch+1}: image macro-F1={score:.8f}', flush=True)
    require(best_state is not None, 'No completed epoch')
    head.load_state_dict(best_state)
    head.eval()
    with torch.inference_mode():
        result = evaluate_logits(head(val_x).cpu(), rows['val'], cmap)
    return best_state, best_epoch, result, history


def compare_predictions(reference, actual):
    require([p['crop_id'] for p in reference['crop_predictions']] == [p['crop_id'] for p in actual['crop_predictions']], 'Reload crop order mismatch')
    a = np.array([p['logits'] for p in reference['crop_predictions']])
    b = np.array([p['logits'] for p in actual['crop_predictions']])
    # Strict reference reproduction. A mismatch is reported; tolerances are not widened.
    return {'passed': reference == actual, 'exact_predictions_and_metrics': reference == actual,
            'max_abs_logit_delta': float(np.max(np.abs(a - b))),
            'image_prediction_changes': sum(x['y_pred'] != y['y_pred'] for x, y in
                                            zip(reference['image_predictions'], actual['image_predictions']))}


def load_package(checkpoint, expected_sha256, device='cpu', repo_dir=None):
    require(sha(checkpoint) == expected_sha256, 'Checkpoint SHA mismatch')
    payload = torch.load(checkpoint, map_location='cpu', weights_only=True)
    require(payload['format'] == 'TV3_DINO_LINEAR_V1', 'Unsupported checkpoint')
    c = payload['config']
    validate_config(c)
    if repo_dir is not None:
        c = json.loads(json.dumps(c))
        c['model']['repo_dir'] = str(repo_dir)
    backbone = load_backbone(c, device, state_dict=payload['backbone'])
    head = nn.Linear(384, 8).to(device).eval()
    head.load_state_dict(payload['head'], strict=True)
    return backbone, head, transform_for(c['model']['name']), payload


def predict_crops(backbone, head, transform, crops, device):
    """TV4 interface: independent logits [N,8] for RGB PIL crops, no box aggregation."""
    require(len(crops) > 0, 'Empty crop batch')
    with torch.inference_mode():
        return head(extract(backbone, torch.stack([transform(im.convert('RGB')) for im in crops]).to(device))).cpu()
