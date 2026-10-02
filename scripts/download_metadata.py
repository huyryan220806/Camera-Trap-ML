"""Download only the two public SWG metadata archives, preserving provenance."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://storage.googleapis.com/public-datasets-lila/swg-camera-traps/'
FILES = ['swg_camera_traps.zip', 'swg_camera_traps.bounding_boxes.with_species.zip']


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    dest = ROOT / 'data/raw'
    dest.mkdir(parents=True, exist_ok=True)
    provenance_path = dest / 'sources.json'
    prior = json.loads(provenance_path.read_text()) if provenance_path.exists() else []
    prior = {p['filename']: p for p in prior}
    records = []
    for name in FILES:
        path = dest / name
        if path.exists():
            print(f'Using local archive: {name}', flush=True)
            record = prior.get(name, {'filename': name, 'url': BASE + name, 'origin': 'existing local file; remote version not verified'})
        else:
            temp = dest / (name + '.part')
            for attempt in range(3):
                try:
                    with urlopen(BASE + name, timeout=90) as response, temp.open('wb') as out:
                        headers = dict(response.headers)
                        size = 0
                        while chunk := response.read(1024 * 1024):
                            out.write(chunk)
                            size += len(chunk)
                        assert size == int(headers['Content-Length'])
                    with ZipFile(temp) as z:
                        assert z.testzip() is None
                    temp.replace(path)
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(2)
            record = {'filename': name, 'url': BASE + name, 'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'etag': headers.get('ETag'), 'last_modified': headers.get('Last-Modified')}
        digest = sha256(path)
        if record.get('sha256') and record['sha256'] != digest:
            raise ValueError(f'Local archive checksum changed: {name}')
        record.update(sha256=digest, bytes=path.stat().st_size)
        with ZipFile(path) as z:
            record['members'] = [{'name': n.filename, 'bytes': n.file_size} for n in z.infolist()]
        records.append(record)
        provenance_path.write_text(json.dumps(records, indent=2), encoding='utf-8')
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
