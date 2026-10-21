"""Validate the frozen B1/B2 bundle against its source and every derived view."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from comparison_data import (ROOT, DEFAULT_OUTPUT, DEFAULT_REPORT, require, repo_path,
                             load_inputs, source_fingerprint, bundle_files, image_check)
from download_subset import atomic_json, load_json, read_rows, sha256, utc_now


def validate(folder=DEFAULT_OUTPUT, check_images=True):
    folder = Path(folder).resolve()
    provenance = load_json(folder / 'provenance.json')
    config_path = repo_path(provenance['config_path'])
    require(sha256(config_path) == provenance['config_sha256'], 'Frozen config changed')
    config, source, rows, cmap = load_inputs(config_path)
    require(config['dataset_version'] == provenance['dataset_version'], 'Dataset version changed')
    require(source_fingerprint(source) == provenance['source_files_sha256'], 'Source snapshot changed')
    files, objects = bundle_files(rows, cmap, config)
    expected = set(files) | set(objects)
    require(set(provenance['files_sha256']) == expected, 'Snapshot file list incomplete')
    actual_files = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    require(actual_files == expected | {'provenance.json'}, 'Unexpected or missing snapshot files')
    for name in expected:
        require(sha256(folder / name) == provenance['files_sha256'][name], 'Snapshot modified: ' + name)
    for name, expected_rows in files.items():
        require(read_rows(folder / name) == expected_rows, 'Derived view/source mismatch: ' + name)
    for name, value in objects.items():
        require(load_json(folder / name) == value, 'Summary/policy/audit mismatch: ' + name)
    if check_images:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i, _ in enumerate(pool.map(image_check, rows), 1):
                if i % 250 == 0 or i == len(rows):
                    print(f'Comparison image verification {i}/{len(rows)}', flush=True)
    require(source_fingerprint(source) == provenance['source_files_sha256'], 'Source changed during validation')
    return {'passed': True, 'checked_utc': utc_now(), 'dataset_version': config['dataset_version'],
            'provenance_sha256': sha256(folder / 'provenance.json'),
            'requested': len(rows), 'retained': len(files['manifest.jsonl']), 'excluded': len(files['excluded.jsonl']),
            'split_changes': 0, 'b1_b2_same_parent_ids': True, 'b1_b2_same_labels_and_splits': True,
            'cross_split_overlap': objects['audit.json']['cross_split_overlap'],
            'local_images_redecoded': check_images, 'perceptual_duplicates_checked': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--report', type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    require(not args.report.resolve().is_relative_to(args.folder.resolve()), 'Report must be outside frozen bundle')
    try:
        result = validate(args.folder, check_images=not args.metadata_only)
    except Exception as exc:
        atomic_json(args.report, {'passed': False, 'checked_utc': utc_now(), 'error': repr(exc)})
        raise
    atomic_json(args.report, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
