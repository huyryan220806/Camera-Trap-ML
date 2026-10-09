"""Resumable, image-level download of a frozen SWG v1 subset."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import threading
import time
import warnings

from PIL import Image, ImageFile
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://storage.googleapis.com/public-datasets-lila/swg-camera-traps/'
DEFAULT_SOURCE = ROOT / 'data/processed/v1/pilot_v1.jsonl'
DEFAULT_IMAGES = ROOT / 'data/images/swg_pilot_v2'
DEFAULT_STATE = ROOT / 'data/interim/download_pilot_v2'
DEFAULT_LOG = ROOT / 'reports/tv1_w2/download_events.jsonl'
MAX_BYTES = 32 * 1024 * 1024
SPLITS = ('train', 'val', 'test')
ImageFile.LOAD_TRUNCATED_IMAGES = False


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_rows(path):
    with Path(path).open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


def safe_image_path(image_dir, row):
    name = row['file_name']
    relative = PurePosixPath(name)
    if (not isinstance(name, str) or '\\' in name or ':' in name or
            relative.is_absolute() or '..' in relative.parts or
            not relative.parts or relative.parts[0] != 'public'):
        raise ValueError('Unsafe or non-public image path')
    if row['url'] != BASE + name:
        raise ValueError('URL must refer to the exact public SWG image path')
    root = Path(image_dir).resolve()
    # Do not resolve a non-existent leaf while other threads are creating its parents
    # (Windows can normalize that transient path inconsistently). Reject links explicitly.
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink() or path.is_junction():
            raise ValueError('Links/junctions are not allowed inside the image destination')
    return path


def load_source(source=DEFAULT_SOURCE):
    source = Path(source).resolve()
    provenance = load_json(ROOT / 'data/processed/v1/provenance.json')
    v1 = ROOT / 'data/processed/v1/manifest_v1.jsonl'
    pilot = ROOT / 'data/processed/v1/pilot_v1.jsonl'
    if sha256(v1) != provenance['manifest_sha256'] or sha256(pilot) != provenance['pilot_sha256']:
        raise ValueError('Frozen v1 manifest/pilot checksum changed')
    parents = {r['image_id']: r for r in read_rows(v1)}
    rows = read_rows(source)
    if not rows or len({r['image_id'] for r in rows}) != len(rows):
        raise ValueError('Source is empty or has repeated image IDs')
    if len({r['file_name'] for r in rows}) != len(rows):
        raise ValueError('Repeated source file path')
    for row in rows:
        if parents.get(row['image_id']) != row:
            raise ValueError('Source row differs from frozen v1: ' + row['image_id'])
        if row['split'] not in SPLITS:
            raise ValueError('Unknown split')
        safe_image_path(DEFAULT_IMAGES, row)
    return rows


class QualityError(ValueError):
    def __init__(self, status, detail):
        super().__init__(detail)
        self.status = status


def inspect_image(path, row):
    """Check encoded bytes, complete decoding and original pixel geometry; no EXIF rotation."""
    path = Path(path)
    if not 0 < path.stat().st_size <= MAX_BYTES:
        raise QualityError('invalid_size', 'Empty file or file exceeds byte limit')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                image.load()
                width, height = image.size
                if (width, height) != (row['width'], row['height']):
                    raise QualityError('dimension_mismatch', f'Decoded {width}x{height}; metadata {row["width"]}x{row["height"]}')
                rgb = image.convert('RGB')
                pixels = hashlib.sha256(f'RGB:{width}:{height}:'.encode() + rgb.tobytes()).hexdigest()
                info = {'width': width, 'height': height, 'image_format': image.format,
                        'image_mode': image.mode, 'pixel_sha256': pixels}
    except QualityError:
        raise
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise QualityError('corrupt_image', str(exc)) from exc
    for box in row['boxes']:
        x, y, w, h = box['bbox_xywh']
        if not (0 <= x < x + w <= width + 1e-6 and 0 <= y < y + h <= height + 1e-6):
            raise QualityError('box_outside_image', 'Original box does not fit decoded image')
    info.update(sha256=sha256(path), bytes=path.stat().st_size, validated_utc=utc_now())
    return info


class EventLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        # A killed process can leave one unfinished line. Preserve it for audit before repair.
        if self.path.exists():
            raw = self.path.read_bytes()
            if raw and not raw.endswith(b'\n'):
                last = raw.rfind(b'\n') + 1
                with self.path.with_suffix('.interrupted-tail.bin').open('ab') as backup:
                    backup.write(raw[last:] + b'\n')
                with self.path.open('r+b') as f:
                    f.truncate(last)

    def emit(self, event):
        with self.lock, self.path.open('a', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps({'utc': utc_now(), **event}, ensure_ascii=False, allow_nan=False) + '\n')
            f.flush()
            os.fsync(f.fileno())


def receipt_path(state_dir, row):
    # Hash the ID for a filesystem-safe, unique state filename.
    key = hashlib.sha256(row['image_id'].encode()).hexdigest()
    return Path(state_dir) / 'records' / (key + '.json')


def download_one(row, image_dir, state_dir, emit, attempts=3, get=None, sleep=time.sleep):
    path = safe_image_path(image_dir, row)
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = receipt_path(state_dir, row)
    prior = load_json(receipt) if receipt.exists() else {}
    identity = {k: row[k] for k in ('image_id', 'file_name', 'url', 'split', 'label')}
    base = {**identity, 'local_path': path.relative_to(ROOT).as_posix()}

    def finish(status, **fields):
        result = {**base, 'status': status, 'checked_utc': utc_now(), **fields}
        atomic_json(receipt, result)
        emit({'event': 'image_result', **result})
        return result

    if path.exists():
        try:
            quality = inspect_image(path, row)
            if prior.get('status') != 'valid':
                raise QualityError('cache_untracked', 'No valid receipt establishes the origin of this cached file')
            if prior.get('status') == 'valid' and prior.get('sha256') != quality['sha256']:
                raise QualityError('cache_changed', 'Cached bytes differ from the last valid receipt')
            return finish('valid', action='reused', etag=prior.get('etag'),
                          last_modified=prior.get('last_modified'), **quality)
        except QualityError as exc:
            emit({'event': 'cache_rejected', **base, 'reason': exc.status, 'detail': str(exc)})
            quarantine = Path(state_dir) / 'quarantine' / (row['image_id'] + '-' + sha256(path) + '.bin')
            quarantine.parent.mkdir(parents=True, exist_ok=True)
            path.replace(quarantine)

    # Resume at image granularity: verified images are reused; incomplete .part files restart.
    part = path.with_name(path.name + '.part')
    session = requests.Session() if get is None else None
    get = session.get if session else get
    try:
        for attempt in range(1, attempts + 1):
            status, detail, http_status = 'download_error', '', None
            emit({'event': 'download_started', **base, 'attempt': attempt,
                  'restarted_partial_bytes': part.stat().st_size if part.exists() else 0})
            try:
                with get(row['url'], stream=True, timeout=(15, 60), allow_redirects=False,
                         headers={'Accept-Encoding': 'identity'}) as response:
                    http_status = response.status_code
                    if http_status != 200:
                        status = 'missing_remote' if http_status in (404, 410) else 'http_error'
                        detail = f'HTTP {http_status}'
                        retryable = http_status in (408, 429) or http_status >= 500
                    else:
                        length = response.headers.get('Content-Length')
                        expected = int(length) if length is not None else None
                        if expected is not None and (expected <= 0 or expected > MAX_BYTES):
                            raise QualityError('invalid_size', f'Invalid Content-Length: {expected}')
                        count = 0
                        with part.open('wb') as f:
                            for chunk in response.iter_content(chunk_size=256 * 1024):
                                if not chunk:
                                    continue
                                count += len(chunk)
                                if count > MAX_BYTES:
                                    raise QualityError('invalid_size', 'Download exceeds byte limit')
                                f.write(chunk)
                            f.flush()
                            os.fsync(f.fileno())
                        if expected is not None and count != expected:
                            raise requests.ConnectionError(f'Incomplete body: {count}/{expected} bytes')
                        quality = inspect_image(part, row)
                        part.replace(path)
                        return finish('valid', action='downloaded', attempt=attempt, http_status=200,
                                      etag=response.headers.get('ETag'),
                                      last_modified=response.headers.get('Last-Modified'), **quality)
            except QualityError as exc:
                status, detail, retryable = exc.status, str(exc), True
            except (requests.RequestException, OSError, ValueError) as exc:
                status, detail, retryable = 'download_error', str(exc), True
            emit({'event': 'attempt_failed', **base, 'attempt': attempt, 'status': status,
                  'http_status': http_status, 'detail': detail})
            if not retryable or attempt == attempts:
                return finish(status, action='failed', attempt=attempt,
                              http_status=http_status, detail=detail)
            sleep(min(2 ** attempt, 10))
    finally:
        if session:
            session.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--images', type=Path, default=DEFAULT_IMAGES)
    parser.add_argument('--state', type=Path, default=DEFAULT_STATE)
    parser.add_argument('--log', type=Path, default=DEFAULT_LOG)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--attempts', type=int, default=3)
    parser.add_argument('--limit', type=int, help='Smoke-test only; final export still accounts for the complete source')
    args = parser.parse_args(argv)
    if not 1 <= args.workers <= 16 or not 1 <= args.attempts <= 5 or (args.limit is not None and args.limit <= 0):
        parser.error('workers: 1..16; attempts: 1..5; limit must be positive')
    args.images = args.images.resolve()
    if not args.images.is_relative_to(ROOT):
        parser.error('Images must be inside the repository (data/images is ignored by Git)')
    from task_lock import state_lock
    with state_lock(args.state):
        return run_download(args)


def run_download(args):
    """Run with state_lock held by the CLI or the resumable pipeline."""
    rows = load_source(args.source)
    args.state.mkdir(parents=True, exist_ok=True)
    binding = {'source_sha256': sha256(args.source), 'source_rows': len(rows),
               'images': args.images.relative_to(ROOT).as_posix()}
    binding_path = args.state / 'source.json'
    if binding_path.exists() and load_json(binding_path) != binding:
        raise ValueError('State belongs to a different source or destination; use a new state directory')
    atomic_json(binding_path, binding)
    log = EventLog(args.log)
    log.emit({'event': 'run_started', **binding, 'limit': args.limit, 'workers': args.workers,
              'attempts': args.attempts, 'script_sha256': sha256(Path(__file__)),
              'resume_policy': 'Reuse verified receipt-backed files; restart incomplete image bytes'})
    selected = rows[:args.limit] if args.limit else rows
    totals = Counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_one, row, args.images, args.state, log.emit, args.attempts): row for row in selected}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
            except Exception as exc:
                log.emit({'event': 'worker_error', 'image_id': futures[future]['image_id'],
                          'detail': repr(exc), 'action': 'Fix the local error and resume; do not classify it as a missing remote image'})
                totals['worker_error'] += 1
                print(f'Local worker error: {futures[future]["image_id"]}: {exc}', flush=True)
                continue
            totals[result['status']] += 1
            totals['bytes_valid'] += result.get('bytes', 0)
            if i % 50 == 0 or i == len(selected):
                print(f'{i}/{len(selected)} {dict(totals)}', flush=True)
    log.emit({'event': 'run_finished', **binding, 'processed': len(selected), 'totals': dict(totals)})
    return int(totals['valid'] != len(selected))


if __name__ == '__main__':
    raise SystemExit(main())
