import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_tv1_w5 as w
from download_subset import load_json


def row(name, split='train', location=None, sequence=None):
    return {'image_id': name, 'file_name': f'public/test/{name}.jpg',
            'sequence_id': sequence or name, 'seq_id': sequence or name,
            'location': location or name, 'split': split, 'label': 'sambar',
            'class_id': 0, 'width': 40, 'height': 30,
            'boxes': [{'annotation_id': name + '-box', 'label': 'sambar',
                       'bbox_xywh': [1, 1, 12, 10]}]}


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.config = load_json(ROOT / 'configs/data_w5_candidates_v1.json')
        self.config['additional_train_per_class_cap'] = 2
        self.geometry = load_json(ROOT / 'configs/comparison_v1.json')
        self.baseline = [row('old_train'), row('old_val', 'val'), row('old_test', 'test')]

    def build(self, extra, exposed=()):
        return w.build_candidates(self.baseline + extra, self.baseline, {'0': 'sambar'},
                                  self.geometry, set(exposed), self.config)

    def test_validation_and_old_test_locations_never_become_training(self):
        result = self.build([row('extra_val', 'val'),
                             row('test_other_frame', 'test', location='old_test'),
                             row('extra_train')])
        self.assertEqual([r['image_id'] for r in result['train_extension_candidates.jsonl']], ['extra_train'])
        self.assertEqual(result['holdout_candidates.jsonl'], [])
        self.assertEqual(result['summary.json']['source_split_changes'], 0)

    def test_exposure_excludes_entire_location_not_only_known_frame(self):
        result = self.build([row('history', 'test', location='unused_test_site'),
                             row('new_frame', 'test', location='unused_test_site'),
                             row('fresh_site', 'test')], exposed=['history'])
        self.assertEqual([r['image_id'] for r in result['holdout_candidates.jsonl']], ['fresh_site'])

    def test_new_validation_site_is_not_promoted_to_independent_test(self):
        result = self.build([row('fresh_val', 'val')])
        self.assertEqual(result['holdout_candidates.jsonl'], [])
        self.assertEqual(result['summary.json']['decision_counts']['reserved_validation'], 1)

    def test_sequence_diversity_excludes_pilot_bursts_and_repeated_new_bursts(self):
        extra = [row('old_burst', location='old_train', sequence='old_train'),
                 row('one', location='new_site', sequence='new_seq'),
                 row('two', location='new_site', sequence='new_seq')]
        result = self.build(extra)
        chosen = result['train_extension_candidates.jsonl']
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]['seq_id'], 'new_seq')
        self.assertEqual(result['summary.json']['train_pool']['images'], 3)

    def test_same_seed_survives_source_reordering(self):
        extra = [row(f'new_{i}', location=f'site_{i % 3}') for i in range(12)]
        first = self.build(extra)
        second = self.build(list(reversed(extra)))
        self.assertEqual(w.encoded(first), w.encoded(second))
        self.assertEqual(len({r['location'] for r in first['train_extension_candidates.jsonl']}), 2)

    def test_invalid_second_box_excludes_whole_parent(self):
        bad = row('tiny_second')
        bad['boxes'].append({'annotation_id': 'tiny', 'label': 'sambar', 'bbox_xywh': [1, 1, 4, 4]})
        result = self.build([bad, row('valid')])
        self.assertEqual([r['image_id'] for r in result['train_extension_candidates.jsonl']], ['valid'])
        self.assertEqual(result['excluded_invalid.jsonl'][0]['issues'][0]['reason'], 'crop_below_min_side')

    def test_leakage_is_rejected_even_when_the_row_would_be_excluded(self):
        bad = row('leak', 'val', location='old_train')
        bad['boxes'] = []
        with self.assertRaisesRegex(ValueError, 'leakage'):
            self.build([bad])

    def test_unknown_exposure_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'unknown image'):
            self.build([], exposed=['not_in_source'])

    def test_source_and_baseline_are_not_mutated(self):
        baseline_before = copy.deepcopy(self.baseline)
        extra = [row('new_test', 'test'), row('new_train')]
        extra_before = copy.deepcopy(extra)
        self.build(extra)
        self.assertEqual(self.baseline, baseline_before)
        self.assertEqual(extra, extra_before)

    def test_sparse_holdout_is_not_released_for_evaluation(self):
        summary = self.build([row('new_test', 'test')])['summary.json']
        self.assertEqual(summary['holdout_status'], 'NOT_READY_INSUFFICIENT_SUPPORT')
        self.assertFalse(summary['training_ready'])
        self.assertFalse(summary['holdout_ready'])
        self.assertEqual(summary['per_class'][0]['holdout_failed_support_checks'], ['images', 'sequences', 'locations'])


class PublicationTests(unittest.TestCase):
    def test_interrupted_stage_resumes_and_existing_release_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); stage = root / 'staging'; release = root / 'release'
            files = {'a.json': b'{"a":1}\n', 'b.jsonl': b'{"id":"b"}\n'}
            stage.mkdir(); (stage / 'a.json').write_bytes(files['a.json'])
            self.assertEqual(w.publish(release, stage, files), 'published')
            before = {p.name: p.stat().st_mtime_ns for p in release.iterdir()}
            self.assertEqual(w.publish(release, stage, files), 'verified_existing')
            self.assertEqual(before, {p.name: p.stat().st_mtime_ns for p in release.iterdir()})
            changed = {**files, 'a.json': b'{"a":2}\n'}
            with self.assertRaisesRegex(ValueError, 'Release modified'):
                w.publish(release, stage, changed)
            self.assertEqual((release / 'a.json').read_bytes(), files['a.json'])

    def test_inconsistent_staging_and_missing_verify_target_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); stage = root / 'staging'; release = root / 'release'
            with self.assertRaisesRegex(ValueError, 'not built'):
                w.publish(release, stage, {'a': b'new'}, verify_only=True)
            self.assertFalse(stage.exists())
            stage.mkdir(); (stage / 'a').write_bytes(b'old')
            with self.assertRaisesRegex(ValueError, 'Staging changed'):
                w.publish(release, stage, {'a': b'new'})
            self.assertEqual((stage / 'a').read_bytes(), b'old')


if __name__ == '__main__':
    unittest.main()
