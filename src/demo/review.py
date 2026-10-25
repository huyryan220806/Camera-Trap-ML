"""Durable human decisions, separate from immutable model output and datasets."""
from datetime import datetime, timezone
import copy
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import sys
import threading


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def runtime_info():
    cpu = platform.processor()
    ram = None
    if os.name == 'nt':
        import ctypes
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                cpu = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
            class Memory(ctypes.Structure):
                _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
                    (k, ctypes.c_ulonglong) for k in ('total', 'avail', 'page', 'page_avail', 'virtual', 'virtual_avail', 'extended')]
            memory = Memory()
            memory.length = ctypes.sizeof(memory)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                ram = round(memory.total / 1024**3, 2)
        except OSError:
            pass
    versions = {}
    for package in ('torch', 'torchvision', 'Pillow', 'megadetector'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    torch = sys.modules.get('torch')
    return {'cpu': cpu, 'logical_cpus': os.cpu_count(), 'ram_gib': ram,
            'os': platform.platform(), 'python': platform.python_version(), 'versions': versions,
            'device': 'cpu', 'torch_threads': torch.get_num_threads() if torch else None,
            'image_batch_size': 1, 'detector_batch_size': 1, 'classifier_max_crop_batch_size': 8,
            'detector_image_size': 1280, 'classifier_image_size': 224}


class ReviewConflict(ValueError):
    pass


class ReviewStore:
    def __init__(self, directory, names):
        self.directory = Path(directory)
        self.names = set(names)
        self.lock = threading.RLock()

    def path(self, request_id):
        if not isinstance(request_id, str) or not re.fullmatch(r'[a-f0-9-]{36}', request_id):
            raise ValueError('Invalid request ID')
        return self.directory / request_id

    def create(self, original, source_sha256, wall_ms):
        result = original.get('result', original)
        runtime = runtime_info()
        classifier_ran = bool(original.get('provenance', {}).get('classifier'))
        count = len(result['detections']) if classifier_ran else 0
        runtime['classifier_actual_crop_batches'] = [min(8, count - offset) for offset in range(0, count, 8)]
        if result.get('error') and result['error']['stage'] == 'classify':
            runtime['classifier_actual_crop_batches'] = None
        session = {'schema_version': 'review-session-1.0', 'request_id': result['request_id'],
                   'created_utc': utc_now(), 'source_sha256': source_sha256,
                   'original': copy.deepcopy(original), 'runtime': runtime,
                   'inference_wall_ms': wall_ms,
                   'timing_scope': 'Decode + detector + classifier + checksum/cache access; excludes upload, preview, journal, browser and human review',
                   'review_policy': 'Human annotations only; never modifies original predictions or frozen datasets',
                   'review': {'revision': 0, 'operator': '', 'note': '', 'image_outcome': 'pending',
                              'box_reviews': [{'detection_id': d['detection_id'], 'decision': 'pending', 'label': None}
                                              for d in result['detections']]}, 'events': []}
        with self.lock:
            folder = self.path(result['request_id'])
            folder.mkdir(parents=True, exist_ok=False)
            with (folder / 'inference.json').open('x', encoding='utf-8') as stream:
                json.dump(session, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
        return session

    def read(self, request_id):
        with self.lock:
            folder = self.path(request_id)
            session = json.loads((folder / 'inference.json').read_text(encoding='utf-8'))
            events = folder / 'events.jsonl'
            if events.exists():
                # A truncated/corrupt journal fails visibly; it is never silently discarded.
                for line in events.read_text(encoding='utf-8').splitlines():
                    event = json.loads(line)
                    if event['revision'] != session['review']['revision'] + 1:
                        raise ValueError('Review journal revision mismatch')
                    session['events'].append(event)
                    session['review'] = event['review']
            return session

    def save(self, request_id, payload):
        with self.lock:
            session = self.read(request_id)
            if type(payload.get('revision')) is not int or payload['revision'] != session['review']['revision']:
                raise ReviewConflict('Phiên duyệt đã thay đổi. Nạp lại trước khi lưu.')
            operator, note = payload.get('operator'), payload.get('note', '')
            if not isinstance(operator, str) or not 1 <= len(operator.strip()) <= 80:
                raise ValueError('Cần tên người duyệt, tối đa 80 ký tự.')
            if not isinstance(note, str) or len(note) > 2000:
                raise ValueError('Ghi chú tối đa 2000 ký tự.')
            outcome = payload.get('image_outcome')
            if outcome not in ('pending', 'reviewed', 'unresolved', 'detector_miss', 'empty'):
                raise ValueError('Invalid image outcome')
            result = session['original'].get('result', session['original'])
            detections = {d['detection_id']: d for d in result['detections']}
            boxes = payload.get('box_reviews')
            if not isinstance(boxes, list) or len(boxes) != len(detections):
                raise ValueError('Need one review entry per original detection')
            cleaned, seen = [], set()
            for box in boxes:
                if not isinstance(box, dict):
                    raise ValueError('Invalid box review')
                identifier, decision, label = box.get('detection_id'), box.get('decision'), box.get('label')
                if identifier not in detections or identifier in seen:
                    raise ValueError('Unknown or repeated detection')
                seen.add(identifier)
                if decision in ('confirmed', 'corrected'):
                    if label not in self.names:
                        raise ValueError('Choose a known class, or mark unresolved')
                    top = detections[identifier].get('top_k', [])
                    decision = 'confirmed' if top and label == top[0]['label'] else 'corrected'
                elif decision not in ('pending', 'unresolved', 'not_animal') or label is not None:
                    raise ValueError('Invalid review decision')
                cleaned.append({'detection_id': identifier, 'decision': decision, 'label': label})
            if outcome == 'reviewed' and (not cleaned or any(b['decision'] in ('pending', 'unresolved') for b in cleaned)):
                raise ValueError('Còn vùng chưa xác nhận; chọn Chưa xác định hoặc duyệt đủ các vùng.')
            if outcome == 'empty' and any(b['decision'] != 'not_animal' for b in cleaned):
                raise ValueError('Ảnh trống không thể có vùng đã xác nhận động vật.')
            if result['status'] == 'error' and outcome not in ('pending', 'unresolved'):
                raise ValueError('Lỗi suy luận không được ghi thành ảnh trống hoặc detector bỏ sót.')
            if outcome == 'detector_miss' and not note.strip():
                raise ValueError('Ghi vị trí hoặc nội dung động vật bị bỏ sót.')
            revision = session['review']['revision'] + 1
            review = {'revision': revision, 'operator': operator.strip(), 'note': note.strip(),
                      'image_outcome': outcome, 'box_reviews': cleaned}
            event = {'revision': revision, 'created_utc': utc_now(), 'review': review}
            with (self.path(request_id) / 'events.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            return self.read(request_id)
