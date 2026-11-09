"""W6 models, data and epoch transactions; W5 implementation is immutable.

No network, Test reader or implicit fallback. CLI gates live in dino_w6_control.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import time

from PIL import Image
import torch
from torch import nn
from torch.nn import functional as F

from . import dino_probe as w5

ROOT = w5.ROOT
R0_SHA = 'acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3'
PRETRAINED_SHA = '08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d'
VENDOR = '6876159a11b4df116f30f667f8c9888617df0751'
EXPANSION_SHA = 'a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5'
FORMAT = 'TV3_DINO_W6_V1'
PREPROCESS = dict(color='RGB', exif_transpose=False, padding=0,
                  bbox='frozen_integer_xyxy_exclusive', resize=[256, 256],
                  interpolation='bilinear', antialias=True, resize_dtype='uint8',
                  output_dtype='float32', scale=True, mean=w5.MEAN, std=w5.STD)
DETAILS = dict(adamw_betas=[0.9, 0.999], adamw_eps=1e-8, adamw_amsgrad=False,
               optimizer_foreach=False, warmup='epoch1=0.5,epoch2=1;cosine(epoch-2)/18;epoch20=0',
               mode='R2:last_two_blocks_norm_head_train_rest_eval;R1_R0:head_train_backbone_eval',
               flip='independent_per_crop_before_resize', validation_crop_batch=8,
               sampler='python_shuffle_parent_groups_epoch_boundary', gradient_clip=None)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def validate_config(c):
    """Keep TV2 dictionaries exact; extra implementation decisions have their own field."""
    recipe = c['recipe']
    w5.require(recipe in ('R0', 'R1', 'R2'), 'Unknown recipe')
    w5.require(c['status'] in ('DRAFT', 'FROZEN'), 'Config status')
    w5.require(c['run_id'] in ('R1', 'R2', 'R3', 'R4', 'R5', 'R6'), 'Never overwrite R0/W5')
    seeds = dict(R1=42, R2=42, R3=43, R4=44, R5=42, R6=43)
    w5.require(c['seed'] == seeds[c['run_id']], 'Unregistered seed')
    if c['run_id'] in ('R1', 'R2'):
        w5.require(recipe == c['run_id'], 'Run/recipe mismatch')
    expanded = c['run_id'] in ('R5', 'R6')
    w5.require(c['dataset'] == ('train_expansion_w6_v1' if expanded else 'comparison_v1') and
               c['dataset_sha256'] == (EXPANSION_SHA if expanded else w5.PROVENANCE), 'Dataset SHA/version mismatch')
    w5.require(recipe != 'R0' or expanded, 'R0 fallback only for approved expansion')
    w5.require(c['init_checkpoint_sha256'] == R0_SHA and c['vendor_commit'] == VENDOR and
               c['pretrained_sha256'] == PRETRAINED_SHA and c['backbone'] == 'dinov3_vits16', 'Initialization pins')
    w5.require(c['preprocessing'] == PREPROCESS and c['implementation'] == DETAILS, 'Unregistered implementation')
    w5.require(c['runtime']['device'] == 'cuda' and c['runtime']['precision'] == 'FP32' and
               c['runtime']['amp'] is False and c['runtime']['tf32'] is False and
               c['runtime']['deterministic'] is True and c['runtime']['num_threads'] == 10 and
               c['runtime']['num_interop_threads'] == 10, 'Runtime must be explicitly reviewed')
    w5.require(c['num_classes'] == 8 and c['drop_last'] is False and (c['max_gpu_hours'] == 2 or
+               c['max_gpu_hours'] == 3 and c['run_id'] == 'R6' and recipe == 'R2') and
               c['loss'] == 'mean_parent_mean_crop_ce_once' and c['selection'] == 'image_macro_f1' and
               c['checkpoint_tie'] == 'earliest_epoch', 'Common recipe invariant')
    if recipe == 'R2':
        w5.require(c['pooling'] == 'x_norm_clstoken' and c['feature_dim'] == 384 and
                   c['init_mode'] == 'W5_full_backbone_and_head' and
                   c['trainable'] == ['last_2_blocks', 'final_norm', 'head'], 'FT model specification')
        w5.require(c['optimizer'] == dict(name='AdamW', backbone_lr=1e-5, head_lr=1e-4,
                    weight_decay=.01, no_decay=['bias', 'norm']) and
                   c['scheduler'] == dict(name='warmup_then_cosine', warmup_epochs=2, epochs=20), 'FT recipe')
        w5.require((c['epochs'], c['patience'], c['parent_batch']) == (20, 5, 16) and
                   type(c['crop_microbatch']) is int and 0 < c['crop_microbatch'] <= 8 and
                   c['cache'] == {'enabled': False} and
                   c['augmentation'] == dict(horizontal_flip=.5, vertical_flip=0, random_crop=False) and
                   c['final_parent_batch_denominator'] == 'actual_parent_count', 'FT batch/augmentation')
    else:
        dim = 768 if recipe == 'R1' else 384
        pooling = 'concat_x_norm_clstoken_mean_x_norm_patchtokens' if recipe == 'R1' else 'x_norm_clstoken'
        w5.require(c['pooling'] == pooling and c['feature_dim'] == dim and c['trainable'] == ['head'] and
                   c['init_mode'] == ('W5_backbone_only_new_768_head' if recipe == 'R1' else 'W5_backbone_only_new_384_head'),
                   'Frozen model specification')
        w5.require(c['optimizer'] == dict(name='SGD', lr=.01, momentum=.9, weight_decay=.0001,
                    nesterov=False, dampening=0) and c['scheduler'] == dict(name='cosine', epochs=50,
                    eta_min=0, step='after_validation'), 'Frozen SGD recipe')
        w5.require((c['epochs'], c['patience'], c['parent_batch'], c['crop_microbatch']) == (50, 7, 32, 32) and
                   c['augmentation'] == dict(horizontal_flip=0, vertical_flip=0, random_crop=False) and
                   c['cache']['enabled'] is True and c['cache']['feature_dim'] == dim and
                   c['cache']['shard_size'] == 128 and c['register_tokens'] is False, 'Frozen batch/cache')


def configure_runtime(c):
    torch.set_num_threads(c['runtime']['num_threads'])
    torch.set_num_interop_threads(c['runtime']['num_interop_threads'])
    w5.seed_all(c['seed'])
    w5.require(torch.cuda.is_available(), 'CUDA unavailable; do not switch to CPU or AMP')
    return w5.runtime()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def verify_pixels(rows, root=ROOT):
    """Only rows explicitly supplied from permitted train/val manifests are decoded."""
    seen = set()
    for r in rows:
        if r['image_id'] in seen:
            continue
        path = (root / r['quality']['local_path']).resolve()
        w5.require(path.is_relative_to((root / 'data/images').resolve()), 'Image outside cache')
        w5.require(w5.sha(path) == r['quality']['sha256'], 'Image bytes changed: ' + r['image_id'])
        with Image.open(path) as im:
            rgb = im.convert('RGB')
            w5.require(rgb.size == (r['width'], r['height']), 'Image dimensions changed')
            pixel = hashlib.sha256(f'RGB:{rgb.width}:{rgb.height}:'.encode() + rgb.tobytes()).hexdigest()
            w5.require(pixel == r['quality']['pixel_sha256'], 'RGB changed: ' + r['image_id'])
        seen.add(r['image_id'])
    return len(seen)


def read_data(c, registry=None, root=ROOT, pixels=False, train_only=False):
    # Read metadata only here; smoke never decodes or evaluates validation images.
    rows, cmap, gate = w5.read_release(root, verify_images=False)
    if c['dataset'] != 'comparison_v1':
        review = (registry or {}).get('data_review', {})
        w5.require(review.get('status') == 'PASS' and review.get('release_sha256') == EXPANSION_SHA and
                   review.get('evidence_path'), 'Expansion BLOCKED: need TV2 data acceptance')
        folder = root / 'data/processed/train_expansion_w6_v1'
        w5.require(w5.sha(folder / 'provenance.json') == EXPANSION_SHA, 'Expansion provenance changed')
        provenance = w5.read_json(folder / 'provenance.json')
        w5.require(provenance['quality_ready'] is True, 'Expansion quality not ready')
        for name, value in provenance['files_sha256'].items():
            path = (folder / name).resolve()
            w5.require(path.is_relative_to(folder.resolve()) and w5.sha(path) == value, 'Expansion file changed: ' + name)
        w5.require(w5.read_json(folder / 'class_map.json') == cmap, 'Expansion class map changed')
        expanded = read_jsonl(folder / 'b2/train.jsonl')
        original = {r['crop_id']: r for r in rows['train']}
        by_crop = {r['crop_id']: r for r in expanded}
        w5.require(len(by_crop) == len(expanded) == 4729 and
                   len(w5.groups_for(expanded)) == 4246, 'Expansion counts')
        w5.require(all(by_crop.get(k) == v for k, v in original.items()), 'Original train rows modified')
        parents = {r['image_id']: r for r in read_jsonl(folder / 'b1/train.jsonl')}
        counts = Counter(r['image_id'] for r in expanded)
        w5.require(set(counts) == set(parents), 'Expansion parents mismatch')
        for r in expanded:
            p = parents[r['image_id']]
            box = r['bbox_xyxy']
            w5.require(r['split'] == 'train' and cmap[str(r['class_id'])] == r['label'] == p['label'] and
                       r['quality'] == p['quality'] and r['parent_crop_count'] == counts[r['image_id']] and
                       abs(r['sample_weight'] - 1 / counts[r['image_id']]) < 1e-12, 'Expansion label/weight')
            w5.require(len(box) == 4 and all(type(x) is int for x in box) and
                       0 <= box[0] < box[2] <= r['width'] and 0 <= box[1] < box[3] <= r['height'], 'Expansion box')
        for field in ('image_id', 'file_name', 'seq_id', 'location'):
            w5.require(not ({r[field] for r in expanded} & {r[field] for r in rows['val']}), 'Train/val leakage: ' + field)
        for field in ('sha256', 'pixel_sha256', 'local_path'):
            w5.require(not ({r['quality'][field] for r in expanded} &
                            {r['quality'][field] for r in rows['val']}), 'Train/val content leakage: ' + field)
        rows['train'] = expanded
        gate['expansion'] = dict(provenance_sha256=EXPANSION_SHA, files=provenance['files_sha256'])
    gate.update(train_dataset=c['dataset'], train_dataset_sha256=c['dataset_sha256'])
    if train_only:
        rows = {'train': rows['train']}
    if pixels:
        gate['verified_source_images'] = verify_pixels([r for split in rows.values() for r in split], root)
    return rows, cmap, gate


class Classifier(nn.Module):
    def __init__(self, backbone, c):
        super().__init__()
        self.backbone = backbone
        self.head = nn.Linear(c['feature_dim'], 8)
        self.pooling = c['pooling']
        self.recipe = c['recipe']
        backbone.requires_grad_(False)
        if self.recipe == 'R2':
            w5.require(len(backbone.blocks) >= 2 and not getattr(backbone, 'chunked_blocks', False), 'Unsupported block layout')
            w5.require(not getattr(backbone, 'untie_cls_and_patch_norms', False), 'Separate CLS norm needs new review')
            for block in backbone.blocks[-2:]:
                block.requires_grad_(True)
            backbone.norm.requires_grad_(True)
        self.train(False)

    def train(self, mode=True):
        # Frozen submodules remain eval, even when called through model.train().
        super().train(False)
        self.training = mode
        self.head.train(mode)
        if self.recipe == 'R2' and mode:
            for block in self.backbone.blocks[-2:]:
                block.train(True)
            self.backbone.norm.train(True)
        return self

    def features(self, x):
        out = self.backbone.forward_features(x)
        cls = out['x_norm_clstoken']
        w5.require(cls.ndim == 2 and cls.shape[1] == 384, 'CLS shape')
        if self.pooling == 'concat_x_norm_clstoken_mean_x_norm_patchtokens':
            patches = out['x_norm_patchtokens']
            w5.require(patches.ndim == 3 and patches.shape[1] > 0 and patches.shape[2] == 384, 'Patch shape')
            cls = torch.cat((cls, patches.mean(1)), dim=1)
        w5.require(torch.isfinite(cls).all().item(), 'Nonfinite feature')
        return cls

    def forward(self, x):
        return self.head(self.features(x))


def initialize(c, checkpoint, repo, device, root=ROOT):
    w5.require(w5.sha(checkpoint) == c['init_checkpoint_sha256'] == R0_SHA, 'Wrong W5 init checkpoint')
    payload = torch.load(checkpoint, map_location='cpu', weights_only=True)
    w5.require(payload['format'] == 'TV3_DINO_LINEAR_V1', 'Initialization must be W5 package')
    base = copy.deepcopy(payload['config'])
    w5.require(base['model']['repo_commit'] == VENDOR and base['model']['weights_sha256'] == PRETRAINED_SHA,
               'W5 pretrained/vendor identity')
    base['model']['repo_dir'] = str(Path(repo).resolve())
    backbone = w5.load_backbone(base, 'cpu', root, state_dict=payload['backbone'])
    # Independent from cache construction or resumed extraction RNG.
    w5.seed_all(c['seed'])
    model = Classifier(backbone, c)
    if c['recipe'] == 'R2':
        model.head.load_state_dict(payload['head'], strict=True)
    return model.to(device), payload['class_map']


def named_mask(model):
    return {name: dict(trainable=p.requires_grad, shape=list(p.shape), numel=p.numel())
            for name, p in model.named_parameters()}


def optimizer_for(model, c):
    if c['recipe'] != 'R2':
        o = c['optimizer']
        return torch.optim.SGD(model.head.parameters(), lr=o['lr'], momentum=o['momentum'],
                               weight_decay=o['weight_decay'], nesterov=False, dampening=0, foreach=False)
    # Exempt actual norm parameters and biases, not every 1-D vector (LayerScale
    # is not a normalization layer and retains the registered weight decay).
    norm_ids = {id(p) for module in model.modules()
                if isinstance(module, nn.LayerNorm) or module.__class__.__name__ == 'RMSNorm'
                for p in module.parameters(recurse=False)}
    buckets = {}
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        owner = 'head' if name.startswith('head.') else 'backbone'
        decay = 0.0 if name.endswith('.bias') or id(p) in norm_ids else c['optimizer']['weight_decay']
        key = (owner, decay)
        buckets.setdefault(key, []).append(p)
    groups = [dict(params=params, lr=c['optimizer'][owner + '_lr'], weight_decay=decay,
                   group_name=f'{owner}:decay={decay}') for (owner, decay), params in buckets.items()]
    return torch.optim.AdamW(groups, betas=tuple(DETAILS['adamw_betas']), eps=DETAILS['adamw_eps'],
                             amsgrad=False, foreach=False)


def schedule_factor(epoch, c):
    """epoch is zero-based. R2: .5,1,cos(pi/18)/2+.5,...,0."""
    if c['recipe'] != 'R2':
        return .5 * (1 + math.cos(math.pi * epoch / c['epochs']))
    if epoch < 2:
        return (epoch + 1) / 2
    return .5 * (1 + math.cos(math.pi * (epoch - 1) / (c['epochs'] - 2)))


def scheduler_for(optimizer, c):
    if c['recipe'] != 'R2':
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=c['epochs'], eta_min=0)
    return torch.optim.lr_scheduler.LambdaLR(optimizer, lambda epoch: schedule_factor(epoch, c))


def crop_batch(rows, indices, c, root, training):
    transform = w5.transform_for('dinov3_vits16')
    tensors = []
    for i in indices:
        r = rows[i]
        with Image.open(root / r['quality']['local_path']) as im:
            crop = im.convert('RGB').crop(tuple(r['bbox_xyxy']))
            if training and random.random() < c['augmentation']['horizontal_flip']:
                crop = crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            tensors.append(transform(crop))
    return torch.stack(tensors)


def backward_parent_batch(model, rows, chosen, c, device, root=ROOT, features=None, tick=lambda: None):
    """One update: sum CE/(crops_in_parent * actual_parents), across microbatches."""
    w5.require(chosen and all(chosen), 'Empty parent batch')
    entries = [(i, 1 / (len(group) * len(chosen))) for group in chosen for i in group]
    total = 0.0
    for start in range(0, len(entries), c['crop_microbatch']):
        tick()
        part = entries[start:start + c['crop_microbatch']]
        indices, weights = zip(*part)
        if features is None:
            logits = model(crop_batch(rows, indices, c, root, True).to(device))
        else:
            logits = model.head(features[list(indices)].to(device))
        targets = torch.tensor([rows[i]['class_id'] for i in indices], device=device)
        loss = (F.cross_entropy(logits, targets, reduction='none') *
                torch.tensor(weights, dtype=logits.dtype, device=device)).sum()
        w5.require(torch.isfinite(loss).item(), 'Nonfinite training loss')
        loss.backward()
        total += float(loss.detach())
    for name, p in model.named_parameters():
        if p.requires_grad:
            w5.require(p.grad is not None and torch.isfinite(p.grad).all().item(), 'Missing/nonfinite gradient: ' + name)
        else:
            w5.require(p.grad is None, 'Frozen gradient: ' + name)
    return total


def cache_identity(c, rows, gate, runtime, sources):
    return dict(format='TV3_W6_FEATURES_V1', pooling=c['pooling'], feature_dim=c['feature_dim'],
                init_sha256=c['init_checkpoint_sha256'], pretrained_sha256=c['pretrained_sha256'],
                vendor=c['vendor_commit'], preprocessing=c['preprocessing'], runtime=runtime, sources=sources,
                data=gate, ordered_rows_sha256={s: digest(v) for s, v in rows.items()},
                extraction_batch=c['crop_microbatch'], shard_size=c['cache']['shard_size'])


def cache_features(model, c, rows, gate, runtime, sources, root=ROOT, tick=lambda: None):
    w5.require(c['recipe'] != 'R2' and c['cache']['enabled'], 'Trainable backbone cannot use a feature cache')
    identity = cache_identity(c, rows, gate, runtime, sources)
    folder = root / 'outputs/tv3_w6/features' / digest(identity)
    folder.mkdir(parents=True, exist_ok=True)
    index_path = folder / 'index.json'
    index = w5.read_json(index_path) if index_path.exists() else dict(identity=identity, shards={})
    w5.require(index['identity'] == identity, 'Cache identity mismatch')
    result = {}
    model.eval()
    for split, all_rows in rows.items():
        parts = []
        for start in range(0, len(all_rows), c['cache']['shard_size']):
            tick()
            name = f'{split}_{start:06d}.pt'
            path = folder / name
            subset = all_rows[start:start + c['cache']['shard_size']]
            ids = [r['crop_id'] for r in subset]
            if name in index['shards']:
                w5.require(w5.sha(path) == index['shards'][name], 'Corrupt cached shard: ' + name)
                part = torch.load(path, map_location='cpu', weights_only=True)
            else:
                batch_features = []
                with torch.inference_mode():
                    for offset in range(0, len(subset), c['crop_microbatch']):
                        tick()
                        inds = list(range(offset, min(offset + c['crop_microbatch'], len(subset))))
                        x = crop_batch(subset, inds, c, root, False).to(c['runtime']['device'])
                        batch_features.append(model.features(x).cpu())
                part = dict(crop_ids=ids, features=torch.cat(batch_features))
                w5.atomic_torch(path, part)
                index['shards'][name] = w5.sha(path)
                w5.atomic_json(index_path, index)
            w5.require(part['crop_ids'] == ids and part['features'].shape == (len(ids), c['feature_dim']) and
                       torch.isfinite(part['features']).all().item(), 'Invalid shard contents')
            parts.append(part['features'])
        result[split] = torch.cat(parts)
    return result, dict(key=digest(identity), index_sha256=w5.sha(index_path))


def validation_logits(model, c, rows, device, root=ROOT, features=None, tick=lambda: None):
    model.eval()
    with torch.inference_mode():
        if c['recipe'] != 'R2':
            # Extraction batch boundaries match the 128-crop shards, including reload.
            if features is None:
                parts = []
                size, batch = c['cache']['shard_size'], c['crop_microbatch']
                for start in range(0, len(rows), size):
                    for off in range(start, min(start + size, len(rows)), batch):
                        tick()
                        inds = list(range(off, min(off + batch, start + size, len(rows))))
                        parts.append(model.features(crop_batch(rows, inds, c, root, False).to(device)).cpu())
                features = torch.cat(parts)
            return model.head(features.to(device)).cpu()
        parts = []
        batch = c['implementation']['validation_crop_batch']
        for start in range(0, len(rows), batch):
            tick()
            inds = list(range(start, min(start + batch, len(rows))))
            parts.append(model(crop_batch(rows, inds, c, root, False).to(device)).cpu())
        return torch.cat(parts)


def cpu_state(model):
    return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}


def train_epochs(model, c, rows, cmap, folder, binding, features=None, resume=False,
                 root=ROOT, tick=lambda: None, epoch_callback=lambda state: None):
    # sklearn/scipy first import can consume Python's global RNG. Complete it
    # BEFORE seeding/restoring RNG, not during the first validation epoch.
    from sklearn import metrics as _metrics
    device = c['runtime']['device']
    optimizer = optimizer_for(model, c)
    scheduler = scheduler_for(optimizer, c)
    state = dict(epoch=0, history=[], best_score=-1., best_epoch=0, bad_epochs=0, best_state=None)
    path = folder / 'last_model.pt'
    if resume and path.exists():
        state = torch.load(path, map_location='cpu', weights_only=True)
        w5.require(state['binding'] == binding and state['format'] == FORMAT + '_RESUME', 'Resume binding changed')
        w5.require(state['sampler'] == dict(kind=DETAILS['sampler'], next_epoch=state['epoch']), 'Sampler state mismatch')
        model.load_state_dict(state['model'], strict=True)
        optimizer.load_state_dict(state['optimizer'])
        scheduler.load_state_dict(state['scheduler'])
        w5.restore_rng(state['rng'])
    else:
        w5.seed_all(c['seed'])
    groups = w5.groups_for(rows['train'])
    for epoch in range(state['epoch'], c['epochs']):
        if state['bad_epochs'] >= c['patience']:
            break
        tick()
        started = time.perf_counter()
        model.train()
        order = list(range(len(groups)))
        random.shuffle(order)
        total = 0.0
        rates = [g['lr'] for g in optimizer.param_groups]
        for start in range(0, len(order), c['parent_batch']):
            chosen = [groups[i] for i in order[start:start + c['parent_batch']]]
            optimizer.zero_grad(set_to_none=True)
            loss = backward_parent_batch(model, rows['train'], chosen, c, device, root,
                                         features['train'] if features else None, tick)
            optimizer.step()
            total += loss * len(chosen)
        logits = validation_logits(model, c, rows['val'], device, root,
                                   features['val'] if features else None, tick)
        result = w5.evaluate_logits(logits, rows['val'], cmap)
        score = result['metrics']['macro_f1']
        if score > state['best_score']:
            state.update(best_score=score, best_epoch=epoch + 1, bad_epochs=0, best_state=cpu_state(model))
        else:
            state['bad_epochs'] += 1
        scheduler.step()
        if device == 'cuda':
            torch.cuda.synchronize()
        state['history'].append(dict(epoch=epoch + 1, learning_rates=rates, train_loss=total / len(groups),
                                     validation_metrics=result['metrics'], seconds=time.perf_counter() - started,
                                     peak_allocated_vram=torch.cuda.max_memory_allocated() if device == 'cuda' else 0))
        state.update(format=FORMAT + '_RESUME', binding=binding, epoch=epoch + 1, model=cpu_state(model),
                     optimizer=optimizer.state_dict(), scheduler=scheduler.state_dict(), rng=w5.rng_state(),
                     sampler=dict(kind=DETAILS['sampler'], next_epoch=epoch + 1), amp_scaler=None)
        # Single atomic transaction; partial epochs replay with original RNG and patience.
        w5.atomic_torch(path, state)
        w5.atomic_json(folder / 'train_log.json', state['history'])
        print(f"{c['run_id']} epoch={epoch+1} macro_f1={score!r}", flush=True)
        epoch_callback(state)
    w5.require(state['best_state'] is not None, 'No complete epoch')
    model.load_state_dict(state['best_state'], strict=True)
    logits = validation_logits(model, c, rows['val'], device, root, features['val'] if features else None, tick)
    return state, w5.evaluate_logits(logits, rows['val'], cmap)


def load_package(checkpoint, expected_sha256, repo, device='cpu'):
    """TV4 loader: W6 format is distinct from the W5 locked adapter."""
    w5.require(w5.sha(checkpoint) == expected_sha256, 'Checkpoint SHA mismatch')
    payload = torch.load(checkpoint, map_location='cpu', weights_only=True)
    w5.require(payload['format'] == FORMAT, 'Expected W6 full-backbone checkpoint')
    c = payload['config']
    validate_config(c)
    w5.require(c['status'] == 'FROZEN' and digest(c) == payload['binding']['config_sha256'], 'Package config binding')
    state = payload['model']
    base = dict(model=dict(name='dinov3_vits16', repo_dir=str(Path(repo).resolve()), repo_commit=VENDOR))
    backbone_state = {k.removeprefix('backbone.'): v for k, v in state.items() if k.startswith('backbone.')}
    backbone = w5.load_backbone(base, 'cpu', state_dict=backbone_state)
    model = Classifier(backbone, c)
    model.load_state_dict(state, strict=True)
    model.to(device).eval()
    return model, w5.transform_for('dinov3_vits16'), payload


def predict_crops(model, transform, crops, device):
    """Independent per-box logits [N,8]; callers own box geometry and softmax."""
    w5.require(bool(crops), 'Empty crop list')
    model.eval()
    with torch.inference_mode():
        return model(torch.stack([transform(im.convert('RGB')) for im in crops]).to(device)).cpu()
