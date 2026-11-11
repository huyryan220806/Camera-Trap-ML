"""Audit and publish a train-only extension without changing the frozen pilot.

Stages: scan (after downloads), sheets, release (after recorded visual review),
verify. Per-image receipts resume decoding after rechecking the encoded bytes.
No model is loaded and no source label or split is reassigned.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import PIL
from PIL import Image, ImageDraw, ImageFont
import scipy
from scipy.fft import dctn

from download_subset import (ROOT, atomic_json, inspect_image, load_json, read_rows,
                             receipt_path, safe_image_path, sha256, utc_now)
from comparison_data import eligible_crops, require, select, audit, repo_path
from prepare_tv1_w5 import encoded, write_bytes, verify_files
from task_lock import state_lock
from split_swg import audit_records

CONFIG = ROOT / 'configs/train_expansion_w6_v1.json'
CODE = ('prepare_tv1_w6.py', 'comparison_data.py', 'download_subset.py',
        'prepare_tv1_w5.py', 'split_swg.py', 'task_lock.py')
QUALITY_KEYS = ('local_path', 'sha256', 'pixel_sha256', 'bytes', 'image_format',
                'image_mode', 'validated_utc')


def fingerprint(config_path):
    config = load_json(config_path)
    require(config['dataset_version'] == 'train_expansion_w6_v1', 'Unsupported version')
    require(config['minimum_crop_side'] == 8 and config['seed'] == 42, 'Unsupported policy')
    require(config['phash_max_distance'] == 4 and config['dhash_max_distance'] == 8,
            'Changed screening policy requires a new release version')
    require(config['model_inference_permitted'] is False, 'No model inference in data audit')
    paths = {config_path.resolve()}
    for directory in (config['candidate_dir'], config['comparison_dir']):
        folder = repo_path(directory)
        provenance = load_json(folder / 'provenance.json')
        for name, digest in provenance['files_sha256'].items():
            require(sha256(folder / name) == digest, 'Frozen file changed: ' + name)
        for name, digest in provenance.get('source_files_sha256', {}).items():
            # comparison provenance paths are relative to its source directory.
            p = ROOT / name if name.startswith(('data/', 'configs/', 'experiments/')) else ROOT / provenance['source_dir'] / name
            require(sha256(p) == digest, 'Frozen upstream source changed: ' + name)
            paths.add(p)
        paths.update(p for p in folder.rglob('*') if p.is_file())
    paths.update(ROOT / name for name in ('configs/comparison_v1.json', 'requirements.txt', 'requirements-data-w6.txt'))
    result = {
        'source_sha256': {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(paths)},
        'code_sha256': {name: sha256(ROOT / 'scripts' / name) for name in CODE},
        'runtime': {'python': platform.python_version(), 'Pillow': PIL.__version__,
                    'numpy': np.__version__, 'scipy': scipy.__version__},
    }
    return config, result


def context(config):
    candidates = read_rows(repo_path(config['candidate_dir']) / 'train_extension_candidates.jsonl')
    holdout = read_rows(repo_path(config['candidate_dir']) / 'holdout_candidates.jsonl')
    baseline = read_rows(repo_path(config['comparison_dir']) / 'manifest.jsonl')
    cmap = load_json(repo_path(config['comparison_dir']) / 'class_map.json')
    require(len(candidates) == 1665 and len(holdout) == 109 and len(baseline) == 4000, 'Unexpected input counts')
    require(all(r['split'] == 'train' for r in candidates), 'Candidate not from train')
    require(all(r['split'] == 'test' for r in holdout), 'Holdout split changed')
    require(len({r['seq_id'] for r in candidates}) == len(candidates), 'Repeated new sequence')
    require(not ({r['seq_id'] for r in candidates} & {r['seq_id'] for r in baseline}), 'Old sequence reused')
    for field in ('image_id', 'file_name'):
        combined = baseline + candidates + holdout
        require(len({r[field] for r in combined}) == len(combined), 'Repeated identity: ' + field)
    metadata = audit_records(baseline + candidates + holdout)
    require(metadata['metadata_leakage_check_passed'], 'Metadata leakage before filtering')
    return baseline, candidates, holdout, cmap, metadata


def receipt_rows(rows, images, state):
    valid, failed = [], []
    for row in rows:
        p = receipt_path(state, row)
        require(p.exists(), 'Unprocessed image; resume download: ' + row['image_id'])
        receipt = load_json(p)
        require(all(receipt.get(k) == row[k] for k in ('image_id', 'file_name', 'url', 'split', 'label')),
                'Receipt identity mismatch: ' + row['image_id'])
        expected = safe_image_path(images, row).relative_to(ROOT).as_posix()
        require(receipt.get('local_path') == expected, 'Receipt path mismatch')
        if receipt['status'] == 'valid':
            valid.append({**row, 'source_version': 'v1', 'quality': {k: receipt[k] for k in QUALITY_KEYS}})
        else:
            failed.append({'image_id': row['image_id'], 'reason': receipt['status'],
                           'detail': receipt.get('detail'), 'status': 'excluded'})
    return valid, failed


def bit_hash(bits):
    return int.from_bytes(np.packbits(np.asarray(bits).reshape(-1)).tobytes(), 'big')


def perceptual_hashes(image):
    gray = image.convert('L')
    pixels = np.asarray(gray.resize((32, 32), Image.Resampling.LANCZOS), dtype=np.float64)
    small = dctn(pixels, type=2, norm='ortho')[:8, :8].reshape(-1)
    bits = small > np.median(small[1:])
    bits[0] = False
    horizontal = np.asarray(gray.resize((9, 8), Image.Resampling.LANCZOS), dtype=np.int16)
    vertical = np.asarray(gray.resize((8, 9), Image.Resampling.LANCZOS), dtype=np.int16)
    return {'phash64': f'{bit_hash(bits):016x}',
            'dhash128': f'{bit_hash(np.concatenate(((horizontal[:, 1:] > horizontal[:, :-1]).ravel(), (vertical[1:] > vertical[:-1]).ravel()))):032x}'}


def checked_feature(row, state):
    quality = row['quality']
    path = repo_path(quality['local_path'])
    require(path.is_relative_to(ROOT / 'data/images'), 'Image path outside data/images')
    require(path.is_file() and sha256(path) == quality['sha256'], 'Missing/changed image: ' + row['image_id'])
    cache = state / 'features' / (hashlib.sha256(row['image_id'].encode()).hexdigest() + '.json')
    identity = {'image_id': row['image_id'], 'sha256': quality['sha256'],
                'pixel_sha256': quality['pixel_sha256'], 'width': row['width'], 'height': row['height']}
    if cache.exists():
        saved = load_json(cache)
        require(saved['identity'] == identity, 'Feature cache identity changed')
        return saved['feature']
    actual = inspect_image(path, row)
    for key in ('sha256', 'pixel_sha256', 'bytes', 'image_format', 'image_mode'):
        require(actual[key] == quality[key], 'Image quality changed: ' + row['image_id'] + '/' + key)
    with Image.open(path) as image:
        feature = {**identity, **perceptual_hashes(image), 'split': row['split'],
                   'label': row['label'], 'seq_id': row['seq_id'], 'location': row['location']}
    atomic_json(cache, {'identity': identity, 'feature': feature})
    return feature


def screen_duplicates(features, new_ids, config):
    exact, near, reasons = [], [], defaultdict(set)
    for key in ('sha256', 'pixel_sha256'):
        groups = defaultdict(list)
        for f in features:
            groups[f[key]].append(f)
        for digest, group in sorted(groups.items()):
            if len(group) < 2:
                continue
            affected = sorted({r['image_id'] for r in group} & new_ids)
            exact.append({'kind': key, 'hash': digest, 'image_ids': sorted(r['image_id'] for r in group),
                          'new_ids_excluded': affected, 'originals_preserved': True})
            for image_id in affected:
                reasons[image_id].add('exact_duplicate_' + key)
    reference = [(f, int(f['phash64'], 16), int(f['dhash128'], 16)) for f in features]
    for a, ah, ad in reference:
        if a['image_id'] not in new_ids:
            continue
        for b, bh, bd in reference:
            if a['image_id'] == b['image_id'] or (b['image_id'] in new_ids and b['image_id'] < a['image_id']):
                continue
            if a['sha256'] == b['sha256'] or a['pixel_sha256'] == b['pixel_sha256']:
                continue
            pd = (ah ^ bh).bit_count()
            if pd > config['phash_max_distance']:
                continue
            dd = (ad ^ bd).bit_count()
            if dd > config['dhash_max_distance']:
                continue
            affected = sorted({a['image_id'], b['image_id']} & new_ids)
            near.append({'image_ids': [a['image_id'], b['image_id']], 'splits': [a['split'], b['split']],
                         'phash_distance': pd, 'dhash_distance': dd, 'new_ids_quarantined': affected,
                         'decision': 'suspected_only_quarantine_pending_review', 'model_used': False})
            for image_id in affected:
                reasons[image_id].add('near_duplicate_pending_review')
    return exact, near, {k: sorted(v) for k, v in sorted(reasons.items())}


def sample_visual(rows, cmap, seed, per_class):
    selected = []
    for label in cmap.values():
        subset = [r for r in rows if r['label'] == label]
        subset.sort(key=lambda r: hashlib.sha256(f'{seed}:w6_visual:{r["image_id"]}'.encode()).hexdigest())
        selected.extend(subset[:per_class])
    return [{'review_index': i + 1, 'image_id': r['image_id'], 'label': r['label'],
             'local_path': r['quality']['local_path'], 'sha256': r['quality']['sha256'],
             'boxes': r['boxes']} for i, r in enumerate(selected)]


def stats(rows):
    return {'images': len(rows), 'sequences': len({r['seq_id'] for r in rows}),
            'locations': len({r['location'] for r in rows}), 'boxes': sum(len(r['boxes']) for r in rows)}


def scan(config, binding, state):
    baseline, candidates, holdout, cmap, metadata = context(config)
    new, failed = receipt_rows(candidates, repo_path(config['images']), repo_path(config['download_state']))
    protected, protected_failed = receipt_rows(holdout, repo_path(config['holdout_images']), repo_path(config['holdout_download_state']))
    require(not protected_failed, 'Holdout content audit incomplete; resume missing images before release')
    geometry_policy = load_json(ROOT / 'configs/comparison_v1.json')
    valid = []
    for row in new:
        _, issues = eligible_crops(row, cmap, geometry_policy)
        if issues:
            failed.append({'image_id': row['image_id'], 'reason': 'invalid_geometry_or_label', 'issues': issues, 'status': 'excluded'})
        else:
            valid.append(row)
    rows = baseline + new + protected
    features = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, f in enumerate(pool.map(lambda r: checked_feature(r, state), rows), 1):
            features.append(f)
            if i % 100 == 0 or i == len(rows):
                print(f'Content audit {i}/{len(rows)}', flush=True)
    exact, near, reasons = screen_duplicates(features, {r['image_id'] for r in candidates}, config)
    kept = [r for r in valid if r['image_id'] not in reasons]
    failures = {r['image_id']: r for r in failed}
    for image_id, why in reasons.items():
        failures.setdefault(image_id, {'image_id': image_id, 'reason': why[0], 'status': 'excluded'})['all_duplicate_flags'] = why
    queue = sample_visual(kept, cmap, config['seed'], config['visual_samples_per_class'])
    summary = {'stage': 'awaiting_visual_review', 'download_valid_train': len(new),
               'download_failed_train': len(candidates) - len(new), 'baseline_verified': len(baseline),
               'holdout_verified': len(protected), 'content_hash_records': len(features),
               'exact_groups_including_preserved_originals': len(exact), 'near_pairs': len(near),
               'preliminary_retained': len(kept), 'preliminary_excluded': len(failures),
               'visual_review_required': len(queue), 'split_changes': 0, 'label_changes': 0,
               'model_inference_run': False, 'new_test_released': False}
    objects = {'new_valid.jsonl': valid, 'holdout_quality.jsonl': protected,
               'features.jsonl': features, 'preliminary_exclusions.jsonl': list(failures.values()),
               'visual_queue.jsonl': queue, 'exact_duplicates.json': exact,
               'near_duplicates.json': near, 'metadata_audit.json': metadata, 'summary.json': summary}
    folder = state / 'audit'
    folder.mkdir(exist_ok=True)
    for name, data in encoded(objects).items():
        write_bytes(folder / name, data)
    atomic_json(folder / 'scan_binding.json', {**binding, 'audit_sha256': {name: sha256(folder / name) for name in objects}})
    return summary


def verify_audit(state, binding):
    folder = state / 'audit'
    receipt = load_json(folder / 'scan_binding.json')
    require({k: receipt[k] for k in binding} == binding, 'Audit inputs/code/runtime changed; inspect before continuing')
    for name, digest in receipt['audit_sha256'].items():
        require(sha256(folder / name) == digest, 'Audit changed: ' + name)
    return folder, receipt


def visual_decisions(queue, review):
    require(review.get('method') == 'visual_sample_not_expert_taxonomic_validation', 'Missing review limitations')
    items = review.get('items', [])
    require(len(items) == len(queue) and len({r['image_id'] for r in items}) == len(items), 'Review missing/duplicate entries')
    indexed = {r['image_id']: r for r in items}
    require(set(indexed) == {r['image_id'] for r in queue}, 'Review does not cover fixed sample')
    rejected = []
    for sample in queue:
        row = indexed[sample['image_id']]
        require(row.get('sha256') == sample['sha256'], 'Review image checksum mismatch')
        require(row.get('decision') in ('retain_metadata_label', 'quarantine'), 'Unsupported visual decision')
        require(bool(row.get('observation')), 'Missing visual observation')
        if row['decision'] == 'quarantine':
            rejected.append({'image_id': row['image_id'], 'reason': 'visual_ambiguity_pending_expert',
                             'detail': row['observation'], 'status': 'excluded'})
    return rejected


def release(config, binding, state):
    folder, scan_binding = verify_audit(state, binding)
    baseline, candidates, holdout, cmap, metadata = context(config)
    review_path = repo_path(config['visual_review_file'])
    review = load_json(review_path)
    require(review.get('queue_sha256') == sha256(folder / 'visual_queue.jsonl'), 'Review queue changed')
    excluded = read_rows(folder / 'preliminary_exclusions.jsonl')
    excluded += visual_decisions(read_rows(folder / 'visual_queue.jsonl'), review)
    require(len({r['image_id'] for r in excluded}) == len(excluded), 'Repeated exclusion')
    rejected = {r['image_id']: r for r in excluded}
    new = [r for r in read_rows(folder / 'new_valid.jsonl') if r['image_id'] not in rejected]
    require(len(new) + len(excluded) == len(candidates), 'Candidate reconciliation failed')
    source = {r['image_id']: r for r in candidates}
    for row in new:
        require({k: row[k] for k in source[row['image_id']]} == source[row['image_id']], 'Source row changed')
    train = [r for r in baseline if r['split'] == 'train'] + new
    protected = read_rows(folder / 'holdout_quality.jsonl')
    full_audit, duplicates = audit(baseline + new + protected)
    require(not ({r['quality']['pixel_sha256'] for r in new} & {r['quality']['pixel_sha256'] for r in baseline + protected}), 'New exact duplicate escaped filter')
    accepted, geometry_rejects, b1, b2 = select(train, cmap, load_json(ROOT / 'configs/comparison_v1.json'))
    require(not geometry_rejects and accepted == train, 'Train geometry changed')
    # Recheck all encoded bytes after visual review; cached decode is accepted only on hash match.
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda row: checked_feature(row, state), baseline + new + protected))
    summary = {'dataset_version': config['dataset_version'], 'quality_ready': True,
               'peer_review_status': 'pending_TV2', 'training_authorized_by_peer_review': False,
               'original_train': stats([r for r in baseline if r['split'] == 'train']),
               'requested_additional': stats(candidates), 'accepted_additional': stats(new),
               'excluded_additional': len(excluded), 'train': stats(train),
               'validation': stats([r for r in baseline if r['split'] == 'val']),
               'historical_test': stats([r for r in baseline if r['split'] == 'test']),
               'holdout_audit_only': stats(protected), 'split_changes': 0, 'label_changes': 0,
               'new_test_released': False, 'model_inference_run': False,
               'exclusion_reasons': dict(sorted(Counter(r['reason'] for r in excluded).items())),
               'by_class': [{'class_id': int(k), 'label': label,
                             'requested': stats([r for r in candidates if r['label'] == label]),
                             'added': stats([r for r in new if r['label'] == label]),
                             'excluded': sum(source[r['image_id']]['label'] == label for r in excluded),
                             'train': stats([r for r in train if r['label'] == label])} for k, label in cmap.items()],
               'valid_new_bytes': sum(r['quality']['bytes'] for r in read_rows(folder / 'new_valid.jsonl')),
               'visual_sample_size': len(review['items']),
               'near_duplicate_limit': config['near_duplicate_note']}
    decisions = [{'image_id': r['image_id'], 'split': r['split'], 'label': r['label'],
                  'decision': 'excluded' if r['image_id'] in rejected else 'retained',
                  'reason': rejected.get(r['image_id'], {}).get('reason')} for r in candidates]
    objects = {'train.jsonl': train, 'additional_train.jsonl': new, 'b1/train.jsonl': b1, 'b2/train.jsonl': b2,
               'excluded.jsonl': [{**source[r['image_id']], 'exclusion': r} for r in excluded],
               'decisions.jsonl': decisions, 'class_map.json': cmap, 'policy.json': config,
               'summary.json': summary, 'audit.json': full_audit, 'preserved_original_duplicates.json': duplicates,
               'visual_review.json': review,
               'baseline_references.json': {'val': 'data/processed/comparison_v1/b2/val.jsonl',
                   'val_sha256': sha256(ROOT / 'data/processed/comparison_v1/b2/val.jsonl'),
                   'test_policy': 'Historical result only; no selection or new inference',
                   'holdout_policy': config['holdout_policy']}}
    for name in ('exact_duplicates.json', 'near_duplicates.json', 'features.jsonl', 'visual_queue.jsonl', 'holdout_quality.jsonl'):
        objects[name] = read_rows(folder / name) if name.endswith('.jsonl') else load_json(folder / name)
    files = encoded(objects)
    provenance = {**binding, 'dataset_version': config['dataset_version'], 'visual_review_sha256': sha256(review_path),
                  'audit_binding': scan_binding, 'quality_ready': True, 'peer_review_status': 'pending_TV2',
                  'files_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}}
    files.update(encoded({'provenance.json': provenance}))
    output = repo_path(config['output_dir'])
    if output.exists():
        verify_files(output, files)
        return {'action': 'verified_existing', 'summary': summary, 'provenance_sha256': sha256(output / 'provenance.json')}
    stage = state / 'staging'
    for name, data in files.items():
        p = stage / name
        if p.exists():
            require(p.read_bytes() == data, 'Interrupted staging differs; preserve and inspect: ' + name)
        else:
            write_bytes(p, data)
    verify_files(stage, files)
    require(fingerprint(CONFIG)[1] == binding, 'Input changed while building release')
    output.parent.mkdir(parents=True, exist_ok=True)
    stage.rename(output)
    return {'action': 'published', 'summary': summary, 'provenance_sha256': sha256(output / 'provenance.json')}


def sheets(config, state):
    queue = read_rows(state / 'audit/visual_queue.jsonl')
    out = ROOT / 'outputs/tv1_w6/visual_sheets'
    out.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
    for start in range(0, len(queue), 8):
        sheet = Image.new('RGB', (1200, 1360), 'white')
        draw = ImageDraw.Draw(sheet)
        for offset, row in enumerate(queue[start:start + 8]):
            x, y = (offset % 2) * 600, (offset // 2) * 340
            draw.text((x + 8, y + 5), f'{row["review_index"]:02d} {row["label"]}', fill='black', font=font)
            draw.text((x + 8, y + 28), row['image_id'][:28], fill='black', font=font)
            with Image.open(repo_path(row['local_path'])) as original:
                image = original.convert('RGB')
                context = image.copy()
                boxes = ImageDraw.Draw(context)
                for box in row['boxes']:
                    bx, by, bw, bh = box['bbox_xywh']
                    boxes.rectangle((bx, by, bx + bw, by + bh), outline='red', width=5)
                context.thumbnail((220, 265))
                sheet.paste(context, (x + 8, y + 62))
                # All boxes are shown, vertically stacked when necessary.
                n = len(row['boxes'])
                for j, box in enumerate(row['boxes']):
                    bx, by, bw, bh = box['bbox_xywh']
                    crop = image.crop((round(bx), round(by), round(bx + bw), round(by + bh)))
                    crop.thumbnail((350, max(30, 265 // n)))
                    sheet.paste(crop, (x + 240, y + 62 + j * (265 // n)))
        sheet.save(out / f'sheet_{start // 8 + 1:02d}.jpg', quality=95)
    return {'sheets': (len(queue) + 7) // 8, 'path': out.relative_to(ROOT).as_posix()}


def verify_release(config, binding, check_images=False):
    """Portable validation from versioned artifacts; no download receipts/state required."""
    output = repo_path(config['output_dir'])
    provenance = load_json(output / 'provenance.json')
    for key in ('source_sha256', 'code_sha256'):
        require(provenance[key] == binding[key], 'Release source/code mismatch: ' + key)
    expected = set(provenance['files_sha256']) | {'provenance.json'}
    require({p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()} == expected,
            'Release file inventory changed')
    for name, digest in provenance['files_sha256'].items():
        require(sha256(output / name) == digest, 'Release checksum mismatch: ' + name)
    baseline, candidates, holdout, cmap, metadata = context(config)
    train = read_rows(output / 'train.jsonl')
    new = read_rows(output / 'additional_train.jsonl')
    excluded = read_rows(output / 'excluded.jsonl')
    source = {r['image_id']: r for r in candidates}
    added_ids, excluded_ids = ({r['image_id'] for r in group} for group in (new, excluded))
    require(len(added_ids) == len(new) and len(excluded_ids) == len(excluded), 'Repeated decision')
    require(not (added_ids & excluded_ids) and added_ids | excluded_ids == set(source), 'Candidate partition mismatch')
    for row in new + excluded:
        require({k: row[k] for k in source[row['image_id']]} == source[row['image_id']], 'Candidate fields modified')
    require(train == [r for r in baseline if r['split'] == 'train'] + new, 'Original train changed')
    require(load_json(output / 'class_map.json') == cmap, 'Class map changed')
    require(load_json(output / 'policy.json') == config, 'Policy changed')
    _, bad, b1, b2 = select(train, cmap, load_json(ROOT / 'configs/comparison_v1.json'))
    require(not bad and b1 == read_rows(output / 'b1/train.jsonl') and b2 == read_rows(output / 'b2/train.jsonl'),
            'Derived B1/B2 view differs')
    protected = read_rows(output / 'holdout_quality.jsonl')
    require(len(protected) == len(holdout), 'Holdout audit incomplete')
    for original, actual in zip(holdout, protected):
        require(all(actual[k] == value for k, value in original.items()), 'Holdout source modified')
    full_audit, duplicates = audit(baseline + new + protected)
    require(full_audit == load_json(output / 'audit.json'), 'Metadata/content audit differs')
    require(duplicates == load_json(output / 'preserved_original_duplicates.json'), 'Original duplicate report differs')
    features = read_rows(output / 'features.jsonl')
    require(len({r['image_id'] for r in features}) == len(features), 'Repeated feature ID')
    feature_index = {r['image_id']: r for r in features}
    require(set(feature_index) - set(source) == {r['image_id'] for r in baseline + protected}, 'Reference hash coverage differs')
    for row in baseline + new + protected:
        feature = feature_index[row['image_id']]
        require(all(feature[k] == row['quality'][k] for k in ('sha256', 'pixel_sha256')), 'Quality/feature mismatch')
    exact, near, reasons = screen_duplicates(features, set(source), config)
    require(exact == load_json(output / 'exact_duplicates.json') and near == load_json(output / 'near_duplicates.json'),
            'Duplicate screen differs')
    require(not (set(reasons) & added_ids), 'Flagged candidate leaked into release')
    queue = read_rows(output / 'visual_queue.jsonl')
    review = load_json(output / 'visual_review.json')
    require(review['queue_sha256'] == sha256(output / 'visual_queue.jsonl'), 'Review queue mismatch')
    require(not ({r['image_id'] for r in visual_decisions(queue, review)} & added_ids), 'Rejected visual sample retained')
    references = load_json(output / 'baseline_references.json')
    require(references['val'] == 'data/processed/comparison_v1/b2/val.jsonl' and
            references['val_sha256'] == sha256(ROOT / references['val']), 'Validation changed')
    summary = load_json(output / 'summary.json')
    require(summary['train'] == stats(train) and summary['accepted_additional'] == stats(new) and
            summary['excluded_additional'] == len(excluded), 'Summary count mismatch')
    require(summary['exclusion_reasons'] == dict(Counter(r['exclusion']['reason'] for r in excluded)), 'Exclusion counts differ')
    require(summary['quality_ready'] is True and summary['peer_review_status'] == 'pending_TV2' and
            summary['training_authorized_by_peer_review'] is False, 'Review status was silently changed')
    for entry in summary['by_class']:
        label = entry['label']
        require(entry['train'] == stats([r for r in train if r['label'] == label]) and
                entry['added'] == stats([r for r in new if r['label'] == label]) and
                entry['requested'] == stats([r for r in candidates if r['label'] == label]) and
                entry['excluded'] == sum(r['label'] == label for r in excluded), 'Per-class counts differ')
    if check_images:
        from comparison_data import image_check
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i, _ in enumerate(pool.map(image_check, baseline + new + protected), 1):
                if i % 250 == 0 or i == len(baseline + new + protected):
                    print(f'Independent image verification {i}/{len(baseline + new + protected)}', flush=True)
    return {'passed': True, 'checked_utc': utc_now(), 'provenance_sha256': sha256(output / 'provenance.json'),
            'images_redecoded': check_images, 'training_images': len(train), 'training_crops': len(b2),
            'additional_retained': len(new), 'additional_excluded': len(excluded),
            'source_files_unchanged': True, 'split_changes': 0, 'label_changes': 0,
            'model_inference_run': False, 'peer_review_status': 'pending_TV2',
            'runtime_matches_release': binding['runtime'] == provenance['runtime']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('scan', 'sheets', 'release', 'verify'))
    parser.add_argument('--check-images', action='store_true', help='Re-decode release images during portable verify')
    args = parser.parse_args()
    config, binding = fingerprint(CONFIG)
    if args.stage == 'verify':
        result = verify_release(config, binding, args.check_images)
        atomic_json(ROOT / 'outputs/tv1_w6/verify_result.json', result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    state = repo_path(config['state_dir'])
    with state_lock(state):
        source = state / 'source_binding.json'
        if source.exists():
            require(load_json(source) == binding, 'Source/config/code/runtime changed since start; inspect state, do not overwrite')
        else:
            atomic_json(source, binding)
        atomic_json(state / 'task_state.json', {'stage': args.stage, 'status': 'running', 'updated_utc': utc_now()})
        try:
            if args.stage == 'scan':
                require(not repo_path(config['output_dir']).exists(), 'Already published; use verify instead of scan')
                result = scan(config, binding, state)
            elif args.stage == 'sheets':
                verify_audit(state, binding)
                result = sheets(config, state)
            else:
                if args.stage == 'verify':
                    require(repo_path(config['output_dir']).exists(), 'No published release to verify')
                result = release(config, binding, state)
            atomic_json(state / 'task_state.json', {'stage': args.stage, 'status': 'complete', 'updated_utc': utc_now(), 'result': result})
            atomic_json(ROOT / f'outputs/tv1_w6/{args.stage}_result.json', result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except BaseException as exc:
            atomic_json(state / 'task_state.json', {'stage': args.stage, 'status': 'failed', 'updated_utc': utc_now(), 'error': repr(exc)})
            raise


if __name__ == '__main__':
    main()
