"""Freeze seed42 train-only 24-image benchmark before inference; verify original bytes/RGB."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path
import random
import sys

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/tv4/w6/benchmark_fixture'


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    manifest = ROOT / 'data/processed/comparison_v1/train.jsonl'
    assert hashlib.sha256(manifest.read_bytes()).hexdigest() == '537d467f7f0ec1ea9fb6a182a37caf0ca1b4f572818789eb6a8c7fc118ef0a11'
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    rng = random.Random(42)
    selected = []
    for label in range(8):
        pool = sorted((r for r in rows if r['class_id'] == label), key=lambda r: r['image_id'])
        selected.extend(rng.sample(pool, 3))
    assert len({r['image_id'] for r in selected}) == 24 and all(r['split'] == 'train' for r in selected)
    fixture = {'seed': 42, 'selection': 'Python Random(42), sample3 per class from image_id-sorted train pools, class order0..7',
        'train_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(), 'images': selected}
    (OUT / 'images.json').write_text(json.dumps(fixture, indent=2), encoding='utf-8')

    def fetch(row):
        path = (ROOT / row['quality']['local_path']).resolve()
        assert path.is_relative_to((ROOT / 'data/images').resolve())
        if path.exists():
            data = path.read_bytes()
        else:
            response = requests.get(row['url'], timeout=(15, 90))
            response.raise_for_status(); data = response.content
        assert hashlib.sha256(data).hexdigest() == row['quality']['sha256'], row['image_id']
        with Image.open(io.BytesIO(data)) as im:
            rgb = im.convert('RGB')
            pixel = hashlib.sha256(f'RGB:{rgb.width}:{rgb.height}:'.encode() + rgb.tobytes()).hexdigest()
            assert rgb.size == (row['width'], row['height']) and pixel == row['quality']['pixel_sha256']
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(data)
        print('Verified train', row['image_id'], flush=True)
        return row['image_id']

    with ThreadPoolExecutor(max_workers=4) as pool:
        verified = list(pool.map(fetch, selected))
    (OUT / 'verification.json').write_text(json.dumps({'status':'PASS','images':verified,'test_opened':False},indent=2))


if __name__ == '__main__':
    main()
