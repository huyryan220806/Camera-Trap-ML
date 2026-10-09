import base64
import io
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock, patch
from http.server import ThreadingHTTPServer

from jsonschema import Draft202012Validator
from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from src.demo import detector as d
from run_demo import make_handler


def picture():
    buffer = io.BytesIO()
    Image.new('RGB', (100, 50), 'green').save(buffer, 'JPEG')
    return buffer.getvalue()


class DetectorTests(unittest.TestCase):
    def test_mock_is_labelled_and_has_no_species(self):
        result = d.analyze(picture(), '../test.jpg')
        self.assertEqual(result['pipeline']['mode'], 'mock')
        self.assertEqual(result['image']['file_name'], 'test.jpg')
        self.assertEqual(result['detections'][0]['bbox_xywh'], [25, 10, 40, 30])
        self.assertIsNone(result['detections'][0]['species'])
        self.assertIsNone(result['pipeline']['weights_sha256'])

    def test_modes_and_error_states_match_new_schema(self):
        schema = json.loads((ROOT / 'contracts/detector_demo.schema.json').read_text())
        for scenario in ('animal', 'empty', 'error'):
            with self.assertLogs(level='ERROR') if scenario == 'error' else self.subTest(scenario=scenario):
                result = d.analyze(picture(), 'a.jpg', scenario=scenario)
            Draft202012Validator(schema).validate(result)
        bad = d.analyze(b'corrupt', 'bad.jpg')
        Draft202012Validator(schema).validate(bad)
        self.assertIsNone(bad['image']['width'])
        self.assertEqual(bad['error']['stage'], 'read')

    def test_real_failure_never_falls_back_to_mock(self):
        adapter = Mock()
        adapter.predict.side_effect = RuntimeError('private stack detail')
        with self.assertLogs(level='ERROR'):
            result = d.analyze(picture(), 'a.jpg', 'megadetector', adapter=adapter)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['pipeline']['mode'], 'megadetector')
        self.assertEqual(result['detections'], [])
        self.assertNotIn('private stack detail', json.dumps(result))

    def test_normalization_filter_and_threshold_equality(self):
        raw = {'detections': [{'category': c, 'conf': s, 'bbox': [0.1, 0.2, 0.3, 0.4]}
                              for c, s in [('1', .2), ('1', .19), ('2', .8), ('3', .7)]]}
        boxes, ignored = d.adapt_detections(raw, 1000, 500, .2)
        self.assertEqual(len(boxes), 1)
        self.assertEqual(ignored, 2)
        self.assertAlmostEqual(boxes[0]['bbox_xywh'][3], 200)

    def test_malformed_boxes_or_failure_are_not_empty_success(self):
        for box in ([0, 0, -1, .1], [0, 0, 2, .2], [float('nan'), 0, .2, .2]):
            with self.assertRaises(ValueError):
                d.adapt_detections({'detections': [{'category': '1', 'conf': .8, 'bbox': box}]}, 100, 100, .2)
        for raw in ({}, {'failure': 'inference error'}, {'detections': None}):
            with self.assertRaises(ValueError):
                d.adapt_detections(raw, 100, 100, .2)

    def test_threshold_and_mode_validation(self):
        for threshold in (True, -1, 2, float('nan'), float('inf'), '0.2'):
            with self.assertRaises(ValueError):
                d.analyze(picture(), 'a.jpg', threshold=threshold)
        with self.assertRaises(ValueError):
            d.analyze(picture(), 'a.jpg', mode='automatic-fallback')

    def test_empty_at_high_threshold(self):
        result = d.analyze(picture(), 'a.jpg', threshold=1)
        self.assertEqual(result['status'], 'no_detection')
        self.assertTrue(result['needs_review'])

    def test_limits_and_truncated_image(self):
        with self.assertRaises(ValueError):
            d.decode_image(b'0' * (d.MAX_IMAGE_BYTES + 1))
        with self.assertRaises(OSError):
            d.decode_image(picture()[:-20])
        with patch.object(d, 'MAX_PIXELS', 10):
            with self.assertRaises(ValueError):
                d.decode_image(picture())


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(Mock(), []))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_static_and_config_do_not_expose_repository(self):
        self.assertEqual(requests.get(self.url, timeout=10).status_code, 200)
        self.assertEqual(requests.get(self.url + '/.git/config', timeout=10).status_code, 404)
        self.assertEqual(requests.get(self.url + '/api/config', timeout=10).json()['samples'], [])

    def test_mock_post_and_corrupt_image(self):
        data = {'image_base64': base64.b64encode(picture()).decode(), 'file_name': 'x.jpg', 'mode': 'mock'}
        response = requests.post(self.url + '/api/analyze', json=data, timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['result']['status'], 'detected')
        self.assertTrue(response.json()['preview'].startswith('data:image/jpeg'))
        data['image_base64'] = base64.b64encode(b'invalid').decode()
        response = requests.post(self.url + '/api/analyze', json=data, timeout=10)
        self.assertEqual(response.json()['result']['error']['stage'], 'read')
        self.assertIsNone(response.json()['preview'])

    def test_external_origin_and_host_are_rejected(self):
        self.assertEqual(requests.post(self.url + '/api/analyze', json={}, headers={'Origin': 'https://example.com'}, timeout=10).status_code, 403)
        self.assertEqual(requests.get(self.url, headers={'Host': 'attacker.example'}, timeout=10).status_code, 403)

    def test_bad_requests_rejected(self):
        for data in ({'sample_id': 'unknown'}, {'image_base64': '!@invalid'}, {'threshold': 'bad'}, []):
            self.assertEqual(requests.post(self.url + '/api/analyze', json=data, timeout=10).status_code, 400)


if __name__ == '__main__':
    unittest.main()
