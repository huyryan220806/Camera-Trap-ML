import copy
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import Mock

from PIL import Image
import requests
from src.demo.inference import analyze_classified
from src.demo.review import ReviewConflict, ReviewStore
from scripts.benchmark_tv4_w4 import unmatched_gt
from scripts.run_demo import make_handler


def example(scenario='multiple'):
    data = io.BytesIO()
    Image.new('RGB', (100, 100), 'green').save(data, format='JPEG')
    return analyze_classified(data.getvalue(), 'synthetic.jpg', mode='mock', scenario=scenario)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ReviewStore(self.temp.name, ['sambar', 'chinese_serow'])
        self.original = example()
        self.session = self.store.create(self.original, 'a' * 64, 12.5)
        self.identifier = self.session['request_id']

    def tearDown(self):
        self.temp.cleanup()

    def payload(self):
        return {**copy.deepcopy(self.session['review']), 'operator': 'TV1'}

    def test_low_scores_are_review_not_unknown_species(self):
        self.assertEqual(self.original['result']['status'], 'needs_review')
        self.assertTrue(self.original['result']['needs_review'])
        self.assertFalse(self.original['provenance']['scores_calibrated'])
        self.assertEqual(len(self.original['result']['detections'][0]['top_k']), 3)
        self.assertEqual(self.session['runtime']['classifier_actual_crop_batches'], [])

    def test_real_classifier_batch_sizes_are_explicit(self):
        original = example()
        original['provenance']['classifier'] = {'classifier_id': 'B2'}
        saved = self.store.create(original, 'f' * 64, 11)
        self.assertEqual(saved['runtime']['classifier_actual_crop_batches'], [2])

    def test_correction_persists_and_original_is_immutable(self):
        path = self.store.path(self.identifier) / 'inference.json'
        before = path.read_bytes()
        payload = self.payload()
        payload['box_reviews'][0].update(decision='corrected', label='sambar')
        saved = self.store.save(self.identifier, payload)
        again = ReviewStore(self.temp.name, self.store.names).read(self.identifier)
        self.assertEqual(saved, again)
        self.assertEqual(again['review']['box_reviews'][0]['label'], 'sambar')
        self.assertEqual(again['original'], self.original)
        self.assertEqual(path.read_bytes(), before)
        with self.assertRaises(ReviewConflict):
            self.store.save(self.identifier, payload)

    def test_unknown_label_and_incomplete_review_rejected(self):
        payload = self.payload()
        payload['box_reviews'][0].update(decision='corrected', label='novel_species')
        with self.assertRaises(ValueError): self.store.save(self.identifier, payload)
        payload = self.payload()
        payload['image_outcome'] = 'reviewed'
        with self.assertRaises(ValueError): self.store.save(self.identifier, payload)

    def test_partial_detector_miss_and_empty_outputs(self):
        payload = self.payload()
        payload.update(image_outcome='detector_miss', note='Animal at left edge, no matching box')
        self.assertEqual(self.store.save(self.identifier, payload)['review']['image_outcome'], 'detector_miss')
        empty = self.store.create(example('empty'), 'b' * 64, 3)
        self.assertEqual(empty['original']['result']['status'], 'no_detection')
        self.assertEqual(empty['review']['image_outcome'], 'pending')
        body = {**empty['review'], 'operator': 'TV1', 'image_outcome': 'detector_miss', 'note': 'Visible animal center'}
        self.assertEqual(self.store.save(empty['request_id'], body)['review']['image_outcome'], 'detector_miss')

    def test_miss_requires_note_and_errors_are_not_misses(self):
        payload = self.payload()
        payload['image_outcome'] = 'detector_miss'
        with self.assertRaises(ValueError): self.store.save(self.identifier, payload)
        with self.assertLogs(level='ERROR'):
            error = self.store.create(example('error'), 'c' * 64, 3)
        body = {**error['review'], 'operator': 'TV1', 'image_outcome': 'detector_miss', 'note': 'failed'}
        with self.assertRaises(ValueError): self.store.save(error['request_id'], body)

    def test_duplicate_box_and_path_traversal_rejected(self):
        payload = self.payload()
        payload['box_reviews'][1] = payload['box_reviews'][0]
        with self.assertRaises(ValueError): self.store.save(self.identifier, payload)
        with self.assertRaises(ValueError): self.store.read('../outside')

    def test_gt_matching_is_one_to_one(self):
        gt = [[0, 0, 10, 10], [0, 0, 10, 10]]
        self.assertEqual(len(unmatched_gt(gt, [{'bbox_xywh': [0, 0, 10, 10]}])), 1)
        self.assertEqual(unmatched_gt(gt, []), [0, 1])

    def test_api_persistence_and_stale_revision(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(Mock(), [], review_store=self.store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            body = {**self.payload(), 'request_id': self.identifier}
            self.assertEqual(requests.post(url + '/api/review', json=body, timeout=10).status_code, 200)
            self.assertEqual(requests.post(url + '/api/review', json=body, timeout=10).status_code, 409)
            self.assertEqual(requests.get(url + '/api/review/' + self.identifier, timeout=10).json()['review']['revision'], 1)
            self.assertEqual(requests.post(url + '/api/review', json=body, headers={'Origin': 'https://example.com'}, timeout=10).status_code, 403)
            missing = {**body, 'request_id': 'f' * 36}
            self.assertEqual(requests.post(url + '/api/review', json=missing, timeout=10).status_code, 404)
        finally:
            server.shutdown(); server.server_close(); thread.join()


if __name__ == '__main__':
    unittest.main()
