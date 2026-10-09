"""Independently reconcile a frozen v2 bundle with its v1 source and local image bytes."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from download_subset import ROOT, load_json, load_source, read_rows, inspect_image, sha256, atomic_json, utc_now
from build_manifest_v2 import DEFAULT_OUTPUT, counts_table, reconcile
from split_swg import audit_records


def validate(folder, check_images=True):
    folder = Path(folder)
    provenance = load_json(folder / 'provenance.json')
    source = (ROOT / provenance['source_path']).resolve()
    assert source.is_relative_to(ROOT), 'Source must be within repo'
    rows = load_source(source)
    assert sha256(source) == provenance['source_sha256'], 'Source checksum mismatch'
    assert sha256(ROOT / 'data/processed/v1/manifest_v1.jsonl') == provenance['parent_manifest_sha256']
    expected_files = {'manifest_v2.jsonl', 'excluded_v2.jsonl', 'download_statuses.jsonl',
                      'train.jsonl', 'val.jsonl', 'test.jsonl', 'class_map.json',
                      'download_events.jsonl', 'summary.json', 'audit.json', 'duplicates.json'}
    assert set(provenance['files_sha256']) == expected_files, 'Incomplete snapshot file list'
    for name, digest in provenance['files_sha256'].items():
        assert sha256(folder / name) == digest, f'Snapshot modified: {name}'
    assert (folder / 'class_map.json').read_bytes() == (ROOT / 'data/processed/v1/class_map.json').read_bytes()
    accepted = read_rows(folder / 'manifest_v2.jsonl')
    excluded = read_rows(folder / 'excluded_v2.jsonl')
    statuses = read_rows(folder / 'download_statuses.jsonl')
    parent = {r['image_id']: r for r in rows}
    outcome = accepted + excluded
    assert len(outcome) == len(rows), 'Missing or repeated outcomes'
    assert len({r['image_id'] for r in outcome}) == len(rows)
    assert {r['image_id'] for r in outcome} == set(parent)
    assert [r['image_id'] for r in statuses] == [r['image_id'] for r in rows]
    for row in outcome:
        assert {k: row[k] for k in parent[row['image_id']]} == parent[row['image_id']], 'A v1 field/split changed'
    for status in statuses:
        for key in ('image_id', 'split', 'file_name', 'url', 'label'):
            assert status[key] == parent[status['image_id']][key], 'Status identity mismatch'
    expected_accepted, expected_excluded, duplicates = reconcile(rows, statuses)
    assert accepted == expected_accepted and excluded == expected_excluded
    assert load_json(folder / 'duplicates.json') == duplicates
    audit = audit_records(accepted)
    assert audit['metadata_leakage_check_passed'], 'Cross-split metadata overlap'
    snapshot_audit = load_json(folder / 'audit.json')
    assert snapshot_audit['cross_split_overlap'] == audit['cross_split_overlap']
    summary = load_json(folder / 'summary.json')
    assert summary['requested'] == len(rows) and summary['accepted'] == len(accepted) and summary['excluded'] == len(excluded)
    assert summary['split_changes'] == 0
    assert summary['duplicate_groups'] == len(duplicates)
    assert summary['valid_download_bytes'] == sum(r.get('bytes', 0) for r in statuses if r['status'] == 'valid')
    for key, value in counts_table(rows, accepted, excluded, statuses).items():
        assert summary[key] == value, 'Counts mismatch: ' + key
    for split in ('train', 'val', 'test'):
        assert read_rows(folder / (split + '.jsonl')) == [r for r in accepted if r['split'] == split]
    event_ids = {r.get('image_id') for r in read_rows(folder / 'download_events.jsonl') if r.get('event') == 'image_result'}
    assert set(parent) <= event_ids, 'Download log does not account for all source IDs'
    if check_images:
        def check_row(row):
            q = row['quality']
            path = (ROOT / q['local_path']).resolve()
            assert path.is_relative_to(ROOT / 'data/images'), 'Image must remain in ignored data/images'
            actual = inspect_image(path, row)
            for key in ('sha256', 'pixel_sha256', 'bytes', 'image_format', 'image_mode'):
                assert actual[key] == q[key], f'Local image changed: {row["image_id"]}/{key}'
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i, _ in enumerate(pool.map(check_row, accepted), 1):
                if i % 250 == 0 or i == len(accepted):
                    print(f'Independent image verification {i}/{len(accepted)}', flush=True)
    return {'passed': True, 'checked_utc': utc_now(),
            'source_sha256': provenance['source_sha256'], 'provenance_sha256': sha256(folder / 'provenance.json'),
            'requested': len(rows), 'accepted': len(accepted), 'excluded': len(excluded),
            'split_changes': 0, 'accepted_per_split': dict(Counter(r['split'] for r in accepted)),
            'v1_fields_preserved': True, 'checksums_verified': True, 'local_images_redecoded': check_images,
            'exact_cross_split_duplicates_in_accepted': 0, 'perceptual_duplicates_checked': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--metadata-only', action='store_true', help='No local image files required; DOES NOT revalidate image quality')
    parser.add_argument('--report', type=Path, default=ROOT / 'reports/tv1_w2/verification.json')
    args = parser.parse_args()
    try:
        result = validate(args.folder, check_images=not args.metadata_only)
    except Exception as exc:
        atomic_json(args.report, {'passed': False, 'checked_utc': utc_now(), 'error': repr(exc)})
        raise
    atomic_json(args.report, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
