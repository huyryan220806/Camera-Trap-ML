"""Pinned MegaDetector adapter and explicitly labelled mock results."""
import hashlib
import importlib.metadata
import io
import logging
import math
from pathlib import Path
import threading
import time
import uuid
import warnings

from PIL import Image, ImageFile

ROOT = Path(__file__).resolve().parents[2]
MODEL_VERSION = 'MDv5a.0.1'
PACKAGE_VERSION = '10.0.25'
MODEL_URL = 'https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5a.0.1.pt'
MODEL_MD5 = '60f8e7ec1308554df258ed1f4040bc4f'
MODEL_PATH = ROOT / 'outputs/tv4/models/md_v5a.0.1.pt'
TRAINING_SOURCE = 'https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md#can-you-share-the-training-data'
LIMITATION = 'MegaDetector MDv5a da dung SWG khi huan luyen; thu tren SWG khong phai danh gia doc lap. Chua co classifier loai.'
MAX_IMAGE_BYTES = 16 * 1024 * 1024
MAX_PIXELS = 24_000_000
ImageFile.LOAD_TRUNCATED_IMAGES = False


def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def package_version():
    try:
        return importlib.metadata.version('megadetector')
    except importlib.metadata.PackageNotFoundError:
        return None


def decode_image(data):
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Image must be nonempty and at most 16 MiB')
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in ('JPEG', 'MPO', 'PNG', 'WEBP'):
                raise ValueError('Supported formats: JPEG, MPO, PNG, WEBP')
            if image.width * image.height > MAX_PIXELS:
                raise ValueError('Image exceeds 24 megapixels')
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            return image.convert('RGB')  # Original raster, no EXIF rotation (same as v2).


def adapt_detections(raw, width, height, threshold):
    if raw.get('failure') or not isinstance(raw.get('detections'), list):
        raise ValueError('Detector failed or returned no detections array')
    detections, ignored = [], 0
    for item in raw['detections']:
        category, score, box = item['category'], item['conf'], item['bbox']
        if category not in ('1', '2', '3') or isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError('Invalid detector category or score')
        if not math.isfinite(score) or not 0 <= score <= 1 or len(box) != 4:
            raise ValueError('Invalid detector score or box')
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in box):
            raise ValueError('Invalid detector coordinates')
        x, y, w, h = box
        if min(x, y) < -1e-5 or min(w, h) <= 0 or x + w > 1.00001 or y + h > 1.00001:
            raise ValueError('Detector box is outside original image')
        if score < threshold:
            continue
        if category != '1':
            ignored += 1
            continue
        x1, y1 = max(0, x) * width, max(0, y) * height
        x2, y2 = min(1, x + w) * width, min(1, y + h) * height
        if x2 <= x1 or y2 <= y1:
            raise ValueError('Empty clipped detector box')
        detections.append({'detection_id': f'animal-{len(detections) + 1}', 'category': 'animal',
                           'bbox_xywh': [x1, y1, x2 - x1, y2 - y1], 'score': float(score),
                           'species': None})
    return detections, ignored


class MegaDetectorAdapter:
    def __init__(self, path=MODEL_PATH):
        self.path = Path(path)
        self.model = None
        self.model_sha256 = None
        self.lock = threading.Lock()

    def predict(self, image, threshold):
        with self.lock:
            if self.model is None:
                if package_version() != PACKAGE_VERSION:
                    raise RuntimeError('Install the pinned requirements-tv4.txt')
                if not self.path.is_file() or digest(self.path, 'md5') != MODEL_MD5:
                    raise RuntimeError('Missing or changed weights; run scripts/prepare_tv4_demo.py')
                import torch
                from megadetector.detection.run_detector import load_detector
                torch.set_num_threads(min(4, torch.get_num_threads()))
                self.model_sha256 = digest(self.path)
                self.model = load_detector(str(self.path), force_cpu=True)
            return self.model.generate_detections_one_image(image, detection_threshold=threshold,
                                                            image_size=1280, augment=False)


def analyze(data, file_name, mode='mock', threshold=0.2, scenario='animal', adapter=None):
    if mode not in ('mock', 'megadetector') or scenario not in ('animal', 'empty', 'error'):
        raise ValueError('Unknown mode or scenario')
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('Threshold must be finite and between 0 and 1')
    start = time.perf_counter()
    result = {'schema_version': 'detector-demo-1.0', 'request_id': str(uuid.uuid4()),
              'image': {'file_name': Path(str(file_name).replace('\\', '/')).name[:200] or 'image',
                        'width': None, 'height': None},
              'pipeline': {'mode': mode, 'detector_id': MODEL_VERSION if mode == 'megadetector' else 'mock-geometry-v1',
                           'package_version': package_version() if mode == 'megadetector' else None,
                           'weights_sha256': None, 'detector_threshold': threshold,
                           'classifier_id': None, 'device': 'cpu', 'image_size': 1280,
                           'coordinate_space': 'original_raster_pixels_no_exif_rotation'},
              'status': 'error', 'needs_review': True, 'detections': [], 'ignored_non_animals': 0,
              'error': None, 'elapsed_ms': 0, 'training_overlap_swg': True,
              'limitation': LIMITATION, 'training_source': TRAINING_SOURCE}
    try:
        image = decode_image(data)
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        result['error'] = {'stage': 'read', 'code': 'IMAGE_DECODE_ERROR',
                           'message': 'Khong doc duoc anh. Ho tro JPEG/PNG/WEBP, toi da 16 MiB va 24 MP.'}
    else:
        result['image'].update(width=image.width, height=image.height)
        try:
            if mode == 'mock':
                raw = {'detections': [{'category': '1', 'conf': 0.91, 'bbox': [0.25, 0.2, 0.4, 0.6]}]}
                if scenario == 'empty':
                    raw = {'detections': []}
                elif scenario == 'error':
                    raw = {'failure': 'mock error'}
            else:
                if adapter is None:
                    raise RuntimeError('No real detector configured')
                raw = adapter.predict(image, threshold)
                result['pipeline']['weights_sha256'] = adapter.model_sha256
            result['detections'], result['ignored_non_animals'] = adapt_detections(raw, image.width, image.height, threshold)
            result['status'] = 'detected' if result['detections'] else 'no_detection'
        except Exception:
            logging.exception('Detector failed (mode=%s)', mode)
            result['detections'] = []
            result['error'] = {'stage': 'detect', 'code': 'DETECTOR_FAILED',
                               'message': 'Detector khong chay duoc. Kiem tra weights, moi truong va log may chu; khong tu chuyen sang mock.'}
    result['elapsed_ms'] = round((time.perf_counter() - start) * 1000, 2)
    return result
