"""Resume the frozen 4,000-image TV1 week-2 task from durable files, not chat history."""
import argparse
import json
import os
from types import SimpleNamespace

from download_subset import (ROOT, DEFAULT_SOURCE, DEFAULT_IMAGES, DEFAULT_STATE, DEFAULT_LOG,
                             atomic_json, load_json, load_source, receipt_path, run_download,
                             safe_image_path, sha256, utc_now)
from build_manifest_v2 import DEFAULT_OUTPUT, build
from task_lock import state_lock
from validate_manifest_v2 import validate

RESUME_COMMAND = '.venv/Scripts/python.exe scripts/resume_tv1_w2.py'


def needs_download(rows, images, state):
    """Fast byte-level preflight; final verification still fully decodes every image."""
    for i, row in enumerate(rows, 1):
        receipt = receipt_path(state, row)
        if not receipt.is_file():
            return True
        saved = load_json(receipt)
        for key in ('image_id', 'file_name', 'url', 'split', 'label'):
            if saved.get(key) != row[key]:
                raise ValueError('Receipt identity mismatch; do not reuse a different source or split')
        path = safe_image_path(images, row)
        if saved.get('local_path') != path.relative_to(ROOT).as_posix():
            raise ValueError('Receipt destination mismatch')
        if saved.get('status') != 'valid' or not path.is_file() or sha256(path) != saved.get('sha256'):
            return True
        if i % 500 == 0 or i == len(rows):
            print(f'Cached byte checksums {i}/{len(rows)}', flush=True)
    return False


def resume(source=DEFAULT_SOURCE, images=DEFAULT_IMAGES, state=DEFAULT_STATE,
           log=DEFAULT_LOG, output=DEFAULT_OUTPUT, report=None, workers=8):
    report = report or ROOT / 'reports/tv1_w2/verification.json'
    args = SimpleNamespace(source=source, images=images.resolve(), state=state, log=log,
                           output=output, workers=workers, attempts=3, limit=None)
    with state_lock(state):
        checkpoint = {'task': 'tv1_week2_pilot_4000', 'pid': os.getpid(),
                      'source_path': source.relative_to(ROOT).as_posix(),
                      'source_sha256': sha256(source), 'next_command': RESUME_COMMAND,
                      'completed_stages': []}

        def save(stage, status='running', **extra):
            checkpoint.update(stage=stage, status=status, updated_utc=utc_now(), **extra)
            atomic_json(state / 'task_state.json', checkpoint)
            print(f'[{stage}] {status}', flush=True)

        try:
            save('preflight')
            rows = load_source(source)
            binding = {'source_sha256': sha256(source), 'source_rows': len(rows),
                       'images': args.images.relative_to(ROOT).as_posix()}
            checkpoint.update(binding)
            if (state / 'source.json').exists() and load_json(state / 'source.json') != binding:
                raise ValueError('State belongs to a different source or destination')
            if output.exists():
                # Reject a damaged/different snapshot before spending time or bandwidth.
                validate(output, check_images=False)
                if load_json(output / 'provenance.json')['source_sha256'] != binding['source_sha256']:
                    raise ValueError('Existing snapshot belongs to a different source')
            save('download')
            if needs_download(rows, args.images, state):
                if run_download(args):
                    raise RuntimeError('Some images failed; inspect the download log and rerun the same command. No snapshot was rewritten.')
            else:
                atomic_json(state / 'source.json', binding)
                print('All source images match valid receipts; no network download needed.', flush=True)
            checkpoint['completed_stages'].append('download')
            save('build')
            if output.exists():
                print('Frozen v2 already exists; preserving it byte-for-byte.', flush=True)
            else:
                build(args)
            checkpoint['completed_stages'].append('build')
            save('validate')
            result = validate(output, check_images=True)
            atomic_json(report, result)
            checkpoint['completed_stages'].append('validate')
            save('complete', 'complete', result=result, next_command=RESUME_COMMAND)
            return result
        except BaseException as exc:
            atomic_json(report, {'passed': False, 'checked_utc': utc_now(),
                                 'stage': checkpoint.get('stage'), 'error': repr(exc)})
            save(checkpoint.get('stage', 'preflight'), 'failed', error=repr(exc))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.workers <= 16:
        parser.error('workers must be 1..16')
    result = resume(workers=args.workers)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
