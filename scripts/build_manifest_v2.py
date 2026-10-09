"""Freeze an audited quality-filtered subset without modifying any v1 field or split."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import tempfile

from download_subset import (ROOT, DEFAULT_SOURCE, DEFAULT_IMAGES, DEFAULT_STATE, DEFAULT_LOG,
                             SPLITS, QualityError, inspect_image, load_json, load_source,
                             receipt_path, safe_image_path, sha256, utc_now, atomic_json)
from split_swg import audit_records

DEFAULT_OUTPUT = ROOT / 'data/processed/v2'


def reconcile(rows, statuses):
    """Exclude exact cross-split pixel duplicates/label conflicts, never move a split."""
    by_id = {r['image_id']: r for r in rows}
    groups = defaultdict(list)
    for status in statuses:
        if status['status'] == 'valid':
            groups[status['pixel_sha256']].append(by_id[status['image_id']])
    duplicates, reasons = [], {}
    for pixel_hash, group in groups.items():
        if len(group) < 2:
            continue
        split_conflict = len({r['split'] for r in group}) > 1
        label_conflict = len({r['label'] for r in group}) > 1
        reason = 'cross_split_exact_duplicate' if split_conflict else 'duplicate_label_conflict' if label_conflict else None
        duplicates.append({'pixel_sha256': pixel_hash, 'image_ids': [r['image_id'] for r in group],
                           'splits': sorted({r['split'] for r in group}),
                           'labels': sorted({r['label'] for r in group}),
                           'action': 'exclude_all' if reason else 'retain_within_split', 'reason': reason})
        if reason:
            for row in group:
                reasons[row['image_id']] = reason
    accepted, excluded = [], []
    for status in statuses:
        row = by_id[status['image_id']]
        reason = reasons.get(row['image_id']) or (status['status'] if status['status'] != 'valid' else None)
        if reason:
            excluded.append({**row, 'exclusion': {'reason': reason, 'download_status': status['status'],
                                                'detail': status.get('detail')}})
        else:
            accepted.append({**row, 'source_version': 'v1', 'quality': {
                key: status[key] for key in ('local_path', 'sha256', 'pixel_sha256', 'bytes',
                                             'image_format', 'image_mode', 'validated_utc')}})
    return accepted, excluded, duplicates


def counts_table(rows, accepted, excluded, statuses):
    def measure(split, label=None):
        match = lambda r: r['split'] == split and (label is None or r['label'] == label)
        selected = [r for r in rows if match(r)]
        valid = [r for r in accepted if match(r)]
        dropped = [r for r in excluded if match(r)]
        return {'split': split, 'label': label, 'requested': len(selected), 'accepted': len(valid),
                'excluded': len(dropped), 'exclusion_reasons': dict(Counter(r['exclusion']['reason'] for r in dropped))}
    return {'by_split': [measure(s) for s in SPLITS],
            'by_class_split': [measure(s, label) for label in sorted({r['label'] for r in rows}) for s in SPLITS],
            'download_status_counts': dict(Counter(r['status'] for r in statuses))}


def write_lines(path, rows):
    with Path(path).open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')


def collect_statuses(rows, images, state):
    def check_row(row):
        receipt = receipt_path(state, row)
        if not receipt.exists():
            raise ValueError(f'Image not processed: {row["image_id"]}. Resume download before freezing v2.')
        saved = load_json(receipt)
        for key in ('image_id', 'file_name', 'url', 'split', 'label'):
            if saved.get(key) != row[key]:
                raise ValueError(f'Receipt identity mismatch: {row["image_id"]}/{key}')
        expected_path = safe_image_path(images, row).relative_to(ROOT).as_posix()
        if saved.get('local_path') != expected_path:
            raise ValueError('Receipt has an unexpected local path: ' + row['image_id'])
        checked = dict(saved)
        if saved['status'] == 'valid':
            path = safe_image_path(images, row)
            try:
                quality = inspect_image(path, row)
                if quality['sha256'] != saved['sha256']:
                    raise QualityError('cache_changed', 'File changed since download; retry before export')
                checked.update(quality)
            except FileNotFoundError:
                checked.update(status='missing_local', detail='File missing at export')
            except QualityError as exc:
                checked.update(status=exc.status, detail=str(exc))
        return checked

    statuses = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, checked in enumerate(pool.map(check_row, rows), 1):
            statuses.append(checked)
            if i % 100 == 0 or i == len(rows):
                print(f'Quality validation {i}/{len(rows)}', flush=True)
    return statuses


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--images', type=Path, default=DEFAULT_IMAGES)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    parser.add_argument('--log', type=Path, default=DEFAULT_LOG)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    from task_lock import state_lock
    with state_lock(args.state):
        build(args)


def build(args):
    """Publish once, with state_lock held throughout validation and publication."""
    if args.output.exists():
        raise ValueError('Output is frozen or already exists. Choose a NEW --output; never overwrite v2.')
    rows = load_source(args.source)
    binding = {'source_sha256': sha256(args.source), 'source_rows': len(rows),
               'images': args.images.resolve().relative_to(ROOT).as_posix()}
    if load_json(args.state / 'source.json') != binding:
        raise ValueError('Download state does not belong to this source/destination')
    statuses = collect_statuses(rows, args.images, args.state)
    accepted, excluded, duplicates = reconcile(rows, statuses)
    audit = audit_records(accepted)
    if not audit['metadata_leakage_check_passed']:
        raise ValueError('Metadata leakage detected in accepted rows')
    # Exact decoded RGB hashes are a mechanical integrity check, not a near-duplicate search.
    audit.update(image_content_duplicates_checked=True,
                 image_content_note='SHA-256 of bytes and decoded RGB pixels checked only for this downloaded subset; perceptual duplicates NOT checked.')
    summary = {'generated_utc': utc_now(), 'requested': len(rows), 'accepted': len(accepted),
               'excluded': len(excluded), 'split_changes': 0,
               'valid_download_bytes': sum(r.get('bytes', 0) for r in statuses if r['status'] == 'valid'),
               'duplicate_groups': len(duplicates), **counts_table(rows, accepted, excluded, statuses)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=args.output.name + '.staging-', dir=args.output.parent))
    write_lines(stage / 'manifest_v2.jsonl', accepted)
    write_lines(stage / 'excluded_v2.jsonl', excluded)
    write_lines(stage / 'download_statuses.jsonl', statuses)
    for split in SPLITS:
        write_lines(stage / (split + '.jsonl'), [r for r in accepted if r['split'] == split])
    shutil.copyfile(ROOT / 'data/processed/v1/class_map.json', stage / 'class_map.json')
    shutil.copyfile(args.log, stage / 'download_events.jsonl')
    for name, value in [('summary.json', summary), ('audit.json', audit), ('duplicates.json', duplicates)]:
        atomic_json(stage / name, value)
    files = {p.name: sha256(p) for p in stage.iterdir() if p.is_file()}
    provenance = {'schema_version': '2.0', 'generated_utc': utc_now(),
                  'source_path': args.source.resolve().relative_to(ROOT).as_posix(),
                  'source_sha256': sha256(args.source), 'parent_manifest_sha256': sha256(ROOT / 'data/processed/v1/manifest_v1.jsonl'),
                  'source_seed': load_json(ROOT / 'configs/split_v1.json')['seed'],
                  'selection': 'All rows in the supplied frozen v1 subset; no new sampling, balancing or split assignment',
                  'exclusion_policy': 'Unavailable/corrupt/dimension-mismatched/changed files excluded; exclude ALL exact RGB duplicates across splits or conflicting labels; retain same-label within-split duplicates and report them',
                  'test_policy': 'Only automated integrity checks on test pixels; no visual/model-based selection or tuning',
                  'script_sha256': {p: sha256(ROOT / 'scripts' / p) for p in ('download_subset.py', 'build_manifest_v2.py', 'task_lock.py')},
                  'files_sha256': files}
    atomic_json(stage / 'provenance.json', provenance)
    stage.rename(args.output)
    print(json.dumps(summary, indent=2), flush=True)
    return summary


if __name__ == '__main__':
    main()
