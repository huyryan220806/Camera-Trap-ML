"""Install the pinned B0 checkpoint atomically; reruns reuse verified weights."""
import argparse
import json
from pathlib import Path
import shutil
import sys

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.demo.classifier import ClassifierCache
from src.demo.detector import digest
from download_subset import atomic_json, utc_now
from task_lock import state_lock

URL = 'https://drive.usercontent.google.com/download?id=18ESoOAV8KqvSV2StS808BvKkcWaNSpUr&export=download&confirm=t'


def prepare(source=None):
    cache = ClassifierCache()
    entry = cache.registry()['B0']
    path = cache.path(entry)
    state = ROOT / 'outputs/tv4/classifier_setup'
    with state_lock(state):
        try:
            atomic_json(state / 'progress.json', {'status': 'running', 'checked_utc': utc_now()})
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                part = path.with_suffix('.part')
                if source:
                    source = Path(source)
                    if source.stat().st_size != entry['checkpoint_bytes'] or digest(source) != entry['sha256']:
                        raise ValueError('Source checkpoint SHA/size differs from pinned B0')
                    shutil.copyfile(source, part)
                else:
                    with requests.get(URL, stream=True, timeout=(20, 60)) as response:
                        response.raise_for_status()
                        if 'text/html' in response.headers.get('Content-Type', ''):
                            raise ValueError('Download returned HTML, not checkpoint bytes')
                        count = 0
                        with part.open('wb') as stream:
                            for block in response.iter_content(1024 * 1024):
                                count += len(block)
                                if count > entry['checkpoint_bytes']:
                                    raise ValueError('Downloaded checkpoint is too large')
                                stream.write(block)
                if part.stat().st_size != entry['checkpoint_bytes'] or digest(part) != entry['sha256']:
                    raise ValueError('Checkpoint download/copy SHA mismatch')
                part.replace(path)
            with cache.lock:
                _, _, _, metadata = cache._get('B0')
            result = {'status': 'complete', 'checked_utc': utc_now(), 'classifier': metadata,
                      'checkpoint_bytes': path.stat().st_size, 'retrained': False}
            atomic_json(state / 'progress.json', result)
            print(json.dumps(result, indent=2))
        except BaseException as exc:
            atomic_json(state / 'progress.json', {'status': 'failed', 'checked_utc': utc_now(), 'error': str(exc)})
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Existing handed-off B0 instead of downloading')
    args = parser.parse_args()
    prepare(args.source)
