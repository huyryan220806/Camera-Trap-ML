import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_results import ROOT, load_json, validate_result
from validate_gpu_schedule import validate_schedule


class ResultContractTests(unittest.TestCase):
    def example(self, name='ok'):
        return load_json(ROOT / 'examples/results' / (name + '.json'))

    def test_all_six_examples_match_contract(self):
        paths = sorted((ROOT / 'examples/results').glob('*.json'))
        self.assertEqual(len(paths), 6)
        for path in paths:
            with self.subTest(path=path.name):
                self.assertEqual(validate_result(load_json(path)), [])

    def test_reject_class_map_mismatch(self):
        result = self.example()
        result['detections'][0]['top_k'][0]['label'] = 'sambar'
        self.assertTrue(validate_result(result))

    def test_reject_out_of_bounds_and_normalized_as_pixel_empty_box(self):
        for box in [[1900, 0, 100, 100], [0, 0, 0, 20]]:
            result = self.example(); result['detections'][0]['bbox_xywh'] = box
            self.assertTrue(validate_result(result))

    def test_reject_unsorted_or_duplicate_top_k(self):
        result = self.example(); top = result['detections'][0]['top_k']
        top[0], top[1] = top[1], top[0]
        self.assertTrue(validate_result(result))
        result = self.example(); result['detections'][0]['top_k'][1] = copy.deepcopy(result['detections'][0]['top_k'][0])
        self.assertTrue(validate_result(result))

    def test_status_tracks_review_threshold_including_equality(self):
        result = self.example()
        result['detections'][0]['top_k'][0]['score'] = .7
        self.assertEqual(validate_result(result), [])
        result['detections'][0]['top_k'][0]['score'] = .69
        self.assertTrue(validate_result(result))
        result.update(status='needs_review', needs_review=True)
        self.assertEqual(validate_result(result), [])

    def test_mixed_detections_require_review(self):
        result = self.example('multiple_animals')
        result.update(status='ok', needs_review=False)
        self.assertTrue(validate_result(result))

    def test_no_detection_cannot_be_ok_or_contain_error(self):
        result = self.example('no_detection'); result['status'] = 'ok'
        self.assertTrue(validate_result(result))
        result = self.example('no_detection'); result['error'] = self.example('image_error')['error']
        self.assertTrue(validate_result(result))

    def test_error_cannot_masquerade_as_partial_success(self):
        result = self.example('model_error'); result['detections'] = self.example()['detections']
        self.assertTrue(validate_result(result))
        result = self.example('image_error'); result['error']['code'] = 'CLASSIFIER_FAILED'
        self.assertTrue(validate_result(result))

    def test_nan_and_repeated_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            for text in ['{"score": NaN}', '{"status":"ok","status":"error"}']:
                path = Path(folder) / 'bad.json'; path.write_text(text)
                with self.assertRaises(ValueError): load_json(path)
        result = self.example(); result['detections'][0]['top_k'][0]['score'] = float('nan')
        self.assertTrue(validate_result(result))


class GpuScheduleTests(unittest.TestCase):
    def fixture(self):
        schedule = load_json(ROOT / 'coordination/gpu_bookings.json')
        schedule['resources'][0].update(owner='TV1', gpu_model='test GPU', vram_gb=8, confirmed=True)
        schedule['reservations'] = [{'booking_id':'test-1','resource_id':'local-01','member':'TV2',
            'start':'2026-10-05T19:00:00+07:00','end':'2026-10-05T22:00:00+07:00',
            'purpose':'test','status':'confirmed','commit':None,'run_path':None}]
        return schedule

    def test_empty_shared_register_is_valid_without_claiming_reservations(self):
        self.assertEqual(validate_schedule(load_json(ROOT / 'coordination/gpu_bookings.json')), [])

    def test_conflicting_slots_rejected_and_adjacent_slots_allowed(self):
        schedule = self.fixture()
        second = copy.deepcopy(schedule['reservations'][0]); second['booking_id'] = 'test-2'
        schedule['reservations'].append(second)
        self.assertTrue(validate_schedule(schedule))
        second.update(start='2026-10-05T22:00:00+07:00',end='2026-10-05T23:00:00+07:00')
        self.assertEqual(validate_schedule(schedule), [])

    def test_unconfirmed_resource_and_missing_timezone_rejected(self):
        schedule = self.fixture(); schedule['resources'][0]['confirmed'] = False
        self.assertTrue(validate_schedule(schedule))
        schedule = self.fixture(); schedule['reservations'][0]['start'] = '2026-10-05T19:00:00'
        self.assertTrue(validate_schedule(schedule))

    def test_cancelled_slot_does_not_block_requested_slot(self):
        schedule = self.fixture(); first = schedule['reservations'][0]; first['status'] = 'cancelled'
        second = copy.deepcopy(first); second.update(booking_id='test-2',status='requested')
        schedule['reservations'].append(second)
        self.assertEqual(validate_schedule(schedule), [])


if __name__ == '__main__':
    unittest.main()
