"""Resume verified weights setup and optional train-only detector smoke test."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.demo.detector import MODEL_PATH, MODEL_URL, MODEL_MD5, MODEL_VERSION, digest, analyze, MegaDetectorAdapter
from download_subset import atomic_json, utc_now, load_json
from task_lock import state_lock

STATE = ROOT / 'outputs/tv4/setup'


def sample_rows():
    source = ROOT / 'data/processed/v2/train.jsonl'
    rows = []
    if source.exists():
        with source.open(encoding='utf-8') as f:
            for line in f:
                row = json.loads(line)
                if row['split'] != 'train':
                    raise ValueError('Demo samples must come from train only')
                path = (ROOT / row['quality']['local_path']).resolve()
                if not path.is_relative_to(ROOT / 'data/images'):
                    raise ValueError('Sample path outside image directory')
                if path.is_file():
                    rows.append(row)
                if len(rows) == 8:
                    break
    return rows


def prepare():
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists():
        if digest(MODEL_PATH, 'md5') != MODEL_MD5:
            raise ValueError('Existing weights checksum mismatch; preserve and investigate this file')
        print('Reusing verified MegaDetector weights.', flush=True)
    else:
        part = MODEL_PATH.with_suffix('.pt.part')
        with requests.get(MODEL_URL, stream=True, timeout=(20, 90)) as response:
            response.raise_for_status()
            count, printed = 0, 0
            with part.open('wb') as f:
                for chunk in response.iter_content(1024 * 1024):
                    count += len(chunk)
                    if count > 400 * 1024 * 1024:
                        raise ValueError('Unexpected model size')
                    f.write(chunk)
                    if count - printed > 16 * 1024 * 1024:
                        print(f'Model download: {count // 1024 // 1024} MiB', flush=True)
                        printed = count
            if digest(part, 'md5') != MODEL_MD5:
                raise ValueError('Downloaded weights checksum mismatch; not loading them')
            part.replace(MODEL_PATH)
    metadata = {'model_version': MODEL_VERSION, 'url': MODEL_URL, 'md5': MODEL_MD5,
                'sha256': digest(MODEL_PATH), 'bytes': MODEL_PATH.stat().st_size,
                'verified_utc': utc_now(), 'training_overlap_swg': True}
    atomic_json(MODEL_PATH.with_suffix('.json'), metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    with state_lock(STATE):
        state = {'task': 'tv4_week2_demo', 'stage': 'weights', 'status': 'running',
                 'resume_command': '.venv/Scripts/python.exe scripts/prepare_tv4_demo.py --smoke'}
        def checkpoint(**changes):
            state.update(updated_utc=utc_now(), **changes)
            atomic_json(STATE / 'progress.json', state)
        try:
            checkpoint()
            weights = prepare()
            checkpoint(stage='smoke' if args.smoke else 'weights', weights_sha256=weights['sha256'])
            if args.smoke:
                rows = sample_rows()
                if not rows:
                    raise ValueError('No local train images. Resume TV1 downloads first.')
                row = rows[0]
                path = ROOT / row['quality']['local_path']
                output = ROOT / 'reports/tv4_w2/detector_smoke.json'
                old = load_json(output) if output.exists() else None
                fingerprint = {'image_sha256': digest(path), 'weights_sha256': weights['sha256'],
                               'adapter_sha256': digest(ROOT / 'src/demo/detector.py'),
                               'package_version': importlib.metadata.version('megadetector')}
                if old and old.get('fingerprint') == fingerprint and old['result']['status'] != 'error':
                    print('Reusing matching successful smoke report.', flush=True)
                else:
                    result = analyze(path.read_bytes(), path.name, 'megadetector', adapter=MegaDetectorAdapter())
                    atomic_json(output, {'checked_utc': utc_now(), 'split': 'train',
                                         'image_id': row['image_id'], 'fingerprint': fingerprint, 'result': result})
                    if result['status'] == 'error':
                        raise RuntimeError('Real detector smoke failed; see reports/tv4_w2/detector_smoke.json')
                    print(json.dumps(result, indent=2), flush=True)
            checkpoint(stage='complete', status='complete')
        except BaseException as exc:
            checkpoint(status='failed', error=repr(exc))
            raise


if __name__ == '__main__':
    main()
