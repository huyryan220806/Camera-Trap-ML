"""Install a pinned handed-off classifier; reruns reuse verified weights."""
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

URLS = {
    'B0': 'https://drive.usercontent.google.com/download?id=18ESoOAV8KqvSV2StS808BvKkcWaNSpUr&export=download&confirm=t',
    'B1': 'https://drive.usercontent.google.com/download?id=19efNKKDz0IwhoUYGrBr5X9fI_CnQ-EPq&export=download&confirm=t',
}


def prepare(source=None, model='B0', cache=None):
    cache = cache or ClassifierCache()
    if model not in ('B0', 'B1', 'B2'):
        raise ValueError('Unknown classifier')
    entry = cache.registry()[model]
    if entry['enabled'] is not True:
        raise ValueError(f'{model} is pending verified handoff; do not enable it from a report alone')
    path = cache.path(entry)
    state = cache.root / 'outputs/tv4/classifier_setup'
    if model != 'B0':
        state = state / model
    with state_lock(state):
        try:
            atomic_json(state / 'progress.json', {'status': 'running', 'model': model, 'checked_utc': utc_now()})
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                part = path.with_suffix('.part')
                if source:
                    source = Path(source)
                    if source.stat().st_size != entry['checkpoint_bytes'] or digest(source) != entry['sha256']:
                        raise ValueError('Source checkpoint SHA/size differs from pinned ' + model)
                    shutil.copyfile(source, part)
                else:
                    if model not in URLS:
                        raise ValueError('No verified download URL; provide --source for ' + model)
                    with requests.get(URLS[model], stream=True, timeout=(20, 60)) as response:
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
                _, _, _, metadata = cache._get(model)
            result = {'status': 'complete', 'model': model, 'checked_utc': utc_now(), 'classifier': metadata,
                      'checkpoint_bytes': path.stat().st_size, 'retrained': False}
            atomic_json(state / 'progress.json', result)
            print(json.dumps(result, indent=2))
            return result
        except BaseException as exc:
            atomic_json(state / 'progress.json', {'status': 'failed', 'model': model, 'checked_utc': utc_now(), 'error': str(exc)})
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Existing handed-off checkpoint instead of downloading')
    parser.add_argument('--model', choices=('B0', 'B1', 'B2'), default='B0')
    args = parser.parse_args()
    prepare(args.source, args.model)
