"""Loopback-only camera-trap demo. Uploaded images stay in memory."""
import argparse
import base64
import binascii
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import logging
import hashlib
import time
import mimetypes
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.demo.detector import (analyze, decode_image, MegaDetectorAdapter, MODEL_VERSION,
                               MODEL_PATH, PACKAGE_VERSION, package_version, MAX_IMAGE_BYTES)
from prepare_tv4_demo import sample_rows
from src.demo.classifier import ClassifierCache, REGISTRY_PATH
from src.demo.inference import analyze_classified
from src.demo.review import ReviewStore, ReviewConflict

WEB = ROOT / 'app'


def make_handler(adapter, rows, classifier_cache=None, review_store=None):
    samples = {str(i): row for i, row in enumerate(rows)}
    classifier_cache = classifier_cache or ClassifierCache()
    review_store = review_store or ReviewStore(ROOT / 'outputs/tv4/w4/sessions', classifier_cache.names())

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(60)

        def local_request(self):
            hosts = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            origin = self.headers.get('Origin')
            return self.headers.get('Host') in hosts and (not origin or origin in {'http://' + h for h in hosts})

        def respond(self, status, body, content_type='application/json; charset=utf-8'):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.local_request():
                return self.respond(403, {'error': 'Local requests only'})
            path = urlsplit(self.path).path
            if path == '/api/config':
                return self.respond(200, {'model_version': MODEL_VERSION, 'package_version': package_version(),
                    'expected_package_version': PACKAGE_VERSION, 'weights_present': MODEL_PATH.is_file(),
                    'classifiers': classifier_cache.status(),
                    'class_names': classifier_cache.names(),
                    'samples': [{'id': k, 'name': f'Train {int(k) + 1:02d}', 'file_name': r['file_name'].split('/')[-1]}
                                for k, r in samples.items()]})
            if path.startswith('/api/review/'):
                try:
                    return self.respond(200, review_store.read(path.rsplit('/', 1)[-1]))
                except (FileNotFoundError, ValueError):
                    return self.respond(404, {'error': 'Không tìm thấy phiên duyệt hợp lệ.'})
            if path.startswith('/api/sample/'):
                row = samples.get(path.rsplit('/', 1)[-1])
                if row is None:
                    return self.respond(404, {'error': 'Unknown sample'})
                try:
                    image = decode_image((ROOT / row['quality']['local_path']).read_bytes())
                    image.thumbnail((1600, 1600))
                    output = io.BytesIO()
                    image.save(output, 'JPEG', quality=90)
                    return self.respond(200, output.getvalue(), 'image/jpeg')
                except (OSError, ValueError):
                    return self.respond(422, {'error': 'Sample image unavailable'})
            files = {'/': 'index.html', '/app.js': 'app.js', '/review.js': 'review.js', '/style.css': 'style.css',
                     '/vendor/lucide.js': 'vendor/lucide.js'}
            if path not in files:
                return self.respond(404, {'error': 'Not found'})
            file = WEB / files[path]
            return self.respond(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] + '; charset=utf-8')

        def do_POST(self):
            if not self.local_request():
                return self.respond(403, {'error': 'Local requests only'})
            path = urlsplit(self.path).path
            if path not in ('/api/analyze', '/api/review'):
                return self.respond(404, {'error': 'Not found'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= MAX_IMAGE_BYTES * 4 // 3 + 8192:
                    return self.respond(413, {'error': 'Anh vuot gioi han 16 MiB'})
                if path == '/api/review' and size > 65536:
                    return self.respond(413, {'error': 'Bản duyệt vượt giới hạn 64 KiB.'})
                if self.headers.get_content_type() != 'application/json':
                    return self.respond(415, {'error': 'Expected JSON'})
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    raise ValueError('Expected object')
                if path == '/api/review':
                    return self.respond(200, review_store.save(payload.get('request_id'), payload))
                if 'sample_id' in payload:
                    row = samples.get(str(payload['sample_id']))
                    if row is None:
                        raise ValueError('Unknown train sample')
                    data = (ROOT / row['quality']['local_path']).read_bytes()
                    name = row['file_name'].split('/')[-1]
                else:
                    data = base64.b64decode(payload.get('image_base64', ''), validate=True)
                    name = payload.get('file_name', 'upload.jpg')
                classifier = payload.get('classifier', 'none')
                envelope = None
                started = time.perf_counter()
                if classifier == 'none':
                    result = analyze(data, name, payload.get('mode', 'mock'), payload.get('threshold', 0.2),
                                     payload.get('scenario', 'animal'), adapter)
                else:
                    envelope = analyze_classified(data, name, classifier=classifier, cache=classifier_cache,
                        mode=payload.get('mode', 'megadetector'), threshold=payload.get('threshold', 0.2),
                        review_threshold=payload.get('review_threshold', 0.7),
                        scenario=payload.get('scenario', 'animal'), adapter=adapter)
                    result = envelope['result']
                wall_ms = round((time.perf_counter() - started) * 1000, 3)
                session = review_store.create(envelope or result, hashlib.sha256(data).hexdigest(), wall_ms)
                # Render a raster without EXIF so preview and box coordinates always agree.
                preview = None
                if result['image']['width'] is not None:
                    image = decode_image(data)
                    image.thumbnail((1600, 1600))
                    buffer = io.BytesIO()
                    image.save(buffer, 'JPEG', quality=90)
                    preview = 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')
                self.respond(200, {'result': result, 'preview': preview, 'classification': envelope, 'review_session': session})
            except ReviewConflict as error:
                self.respond(409, {'error': str(error)})
            except FileNotFoundError:
                self.respond(404, {'error': 'Không tìm thấy ảnh hoặc phiên duyệt.'})
            except (ValueError, TypeError, binascii.Error, KeyError) as error:
                message = str(error) if path == '/api/review' else 'Yeu cau khong hop le. Kiem tra anh, che do va nguong.'
                self.respond(400, {'error': message})
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                logging.exception('Demo request failed')
                self.respond(500, {'error': 'Loi may chu; xem log cuc bo.'})

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--classifiers', type=Path, default=REGISTRY_PATH)
    args = parser.parse_args()
    handler = make_handler(MegaDetectorAdapter(), sample_rows(), ClassifierCache(args.classifiers))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    print(f'CameraTrapML demo: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
