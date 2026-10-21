"""Build/resume a write-once comparison dataset; never reassign or refill splits."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import tempfile

from comparison_data import (ROOT, DEFAULT_CONFIG, DEFAULT_OUTPUT, DEFAULT_STATE, DEFAULT_REPORT,
                             require, load_inputs, source_fingerprint, bundle_files, image_check, repo_path)
from download_subset import atomic_json, load_json, sha256, utc_now
from build_manifest_v2 import write_lines
from task_lock import state_lock
from validate_comparison import validate

COMMAND = '.venv/Scripts/python.exe scripts/freeze_comparison.py'


def verify_images(rows, state):
    """A completed receipt skips decoding only after rechecking the source bytes."""
    def check_one(row):
        key = hashlib.sha256(row['image_id'].encode()).hexdigest()
        receipt = state / 'records' / (key + '.json')
        expected = {'image_id': row['image_id'], 'quality': row['quality']}
        reused = False
        if receipt.exists() and load_json(receipt) == expected:
            path = repo_path(row['quality']['local_path'])
            require(path.is_file() and sha256(path) == row['quality']['sha256'],
                    'Cached image missing/changed: ' + row['image_id'] + '; restore week-2 cache, do not alter snapshot')
            reused = True
        if not reused:
            image_check(row)
            atomic_json(receipt, expected)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, _ in enumerate(pool.map(check_one, rows), 1):
            if i % 100 == 0 or i == len(rows):
                print(f'Pre-publication quality {i}/{len(rows)}', flush=True)


def freeze(config_path=DEFAULT_CONFIG, output=DEFAULT_OUTPUT, state=DEFAULT_STATE, report=DEFAULT_REPORT):
    config_path, output, state, report = (Path(p).resolve() for p in (config_path, output, state, report))
    require(not state.is_relative_to(output) and not report.is_relative_to(output), 'State/report must be outside frozen output')
    require(config_path.is_relative_to(ROOT), 'Config must be within repo')
    with state_lock(state):
        checkpoint = {'task': 'tv1_week3_comparison', 'pid': os.getpid(), 'next_command': COMMAND}

        def save(stage, status='running', **extra):
            checkpoint.update(stage=stage, status=status, updated_utc=utc_now(), **extra)
            atomic_json(state / 'task_state.json', checkpoint)
            print(f'[{stage}] {status}', flush=True)

        try:
            save('source_validation')
            config, source, rows, cmap = load_inputs(config_path)
            binding = {'config_sha256': sha256(config_path), 'source_files_sha256': source_fingerprint(source),
                       'output': output.as_posix(), 'source_dir': source.relative_to(ROOT).as_posix()}
            if (state / 'source.json').exists():
                require(load_json(state / 'source.json') == binding, 'State/source/config changed; use a NEW version and state')
            else:
                atomic_json(state / 'source.json', binding)
            if output.exists():
                save('verify_existing_snapshot')
                existing = load_json(output / 'provenance.json')
                require(existing['config_sha256'] == binding['config_sha256'] and
                        existing['source_files_sha256'] == binding['source_files_sha256'], 'Existing snapshot belongs to another source/config')
                result = validate(output, check_images=True)
            else:
                save('eligibility')
                files, objects = bundle_files(rows, cmap, config)
                save('image_quality')
                verify_images(rows, state)
                require(source_fingerprint(source) == binding['source_files_sha256'] and
                        sha256(config_path) == binding['config_sha256'], 'Source/config changed during build')
                save('publish')
                output.parent.mkdir(parents=True, exist_ok=True)
                stage = Path(tempfile.mkdtemp(prefix=output.name + '.staging-', dir=output.parent))
                for name, records in files.items():
                    (stage / name).parent.mkdir(parents=True, exist_ok=True)
                    write_lines(stage / name, records)
                for name, value in objects.items():
                    atomic_json(stage / name, value)
                provenance = {'dataset_version': config['dataset_version'], 'generated_utc': utc_now(),
                              'config_path': config_path.relative_to(ROOT).as_posix(), **binding,
                              'script_sha256': {name: sha256(ROOT / 'scripts' / name) for name in
                                                ('comparison_data.py', 'freeze_comparison.py', 'validate_comparison.py')},
                              'files_sha256': {name: sha256(stage / name) for name in sorted(set(files) | set(objects))},
                              'images': 'Original files referenced by quality.local_path; no copy, resize or EXIF rotation',
                              'scope': 'Pilot v2; inherited split; one image label confirmed by all image-level box labels',
                              'near_duplicates_checked': False}
                # Local state may use absolute paths, but portable published artifacts must not.
                provenance.pop('output')
                atomic_json(stage / 'provenance.json', provenance)
                validate(stage, check_images=False)
                stage.rename(output)
                save('independent_verification')
                result = validate(output, check_images=True)
            atomic_json(report, result)
            save('complete', 'complete', result=result)
            return result
        except BaseException as exc:
            result = {'passed': False, 'checked_utc': utc_now(), 'stage': checkpoint.get('stage'), 'error': repr(exc)}
            atomic_json(report, result)
            save(checkpoint.get('stage', 'preflight'), 'failed', error=repr(exc))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    parser.add_argument('--report', type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    print(json.dumps(freeze(args.config, args.output, args.state, args.report), indent=2))


if __name__ == '__main__':
    main()
