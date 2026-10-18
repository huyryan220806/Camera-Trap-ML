from contextlib import ExitStack, redirect_stdout
import copy
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import comparison_data as c
import freeze_comparison as f
import validate_comparison as v
from build_manifest_v2 import write_lines
from download_subset import atomic_json, inspect_image, load_json, read_rows, sha256


def row(image_id='a', split='train'):
    return {'image_id': image_id, 'file_name': f'public/test/{image_id}.jpg',
            'url': f'https://storage.googleapis.com/public-datasets-lila/swg-camera-traps/public/test/{image_id}.jpg',
            'split': split, 'seq_id': image_id, 'sequence_id': image_id, 'location': image_id,
            'width': 40, 'height': 30, 'label': 'sambar', 'class_id': 0,
            'boxes': [{'annotation_id': image_id + '-box', 'label': 'sambar', 'bbox_xywh': [1, 1, 12, 10]}],
            'quality': {'pixel_sha256': hashlib.sha256(image_id.encode()).hexdigest()}}


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.config = load_json(c.DEFAULT_CONFIG)
        self.cmap = {'0': 'sambar', '1': 'silver_pheasant'}

    def select(self, records):
        return c.select(records, self.cmap, self.config)

    def test_multiple_boxes_one_species_keeps_one_b1_image(self):
        record = row()
        record['boxes'].append({**record['boxes'][0], 'annotation_id': 'other'})
        kept, dropped, b1, b2 = self.select([record])
        self.assertEqual((len(kept), len(dropped), len(b1), len(b2)), (1, 0, 1, 2))
        self.assertEqual({r['image_id'] for r in b1}, {r['image_id'] for r in b2})
        self.assertEqual(sum(r['sample_weight'] for r in b2), 1)
        self.assertEqual(kept[0], record)

    def test_one_small_box_excludes_whole_parent_not_just_box(self):
        record = row()
        record['boxes'].append({'annotation_id': 'tiny', 'label': 'sambar', 'bbox_xywh': [1, 1, 3, 3]})
        kept, dropped, b1, b2 = self.select([record, row('ok')])
        self.assertEqual([r['image_id'] for r in kept], ['ok'])
        self.assertEqual(dropped[0]['exclusion']['reason'], 'crop_below_min_side')
        self.assertEqual({r['image_id'] for r in b1}, {'ok'})
        self.assertEqual({r['image_id'] for r in b2}, {'ok'})

    def test_mixed_species_and_ambiguous_image_excluded(self):
        mixed = row()
        mixed['boxes'][0]['label'] = 'silver_pheasant'
        ambiguous = row('ambiguous')
        ambiguous['label'] = ['sambar', 'silver_pheasant']
        kept, dropped, _, _ = self.select([mixed, ambiguous, row('ok')])
        self.assertEqual(len(kept), 1)
        self.assertEqual({r['exclusion']['reason'] for r in dropped},
                         {'box_label_disagrees_with_image', 'unknown_or_ambiguous_image_label'})

    def test_missing_duplicate_or_invalid_annotations_excluded(self):
        for mutation, expected in (
            (lambda r: r.update(boxes=[]), 'no_boxes'),
            (lambda r: r['boxes'][0].pop('annotation_id'), 'missing_annotation_id'),
            (lambda r: r['boxes'].append(dict(r['boxes'][0])), 'duplicate_annotation_id'),
            (lambda r: r.update(class_id=1), 'class_id_label_mismatch'),
        ):
            with self.subTest(reason=expected):
                record = row()
                mutation(record)
                _, excluded, _, _ = self.select([record, row('ok')])
                self.assertEqual(excluded[0]['exclusion']['reason'], expected)

    def test_nonfinite_negative_and_small_geometry_rejected(self):
        for coords in ([1, 1, float('nan'), 10], [1, 1, True, 10], [-1, 1, 10, 10],
                       [1, 1, 100, 10], [1, 1, 7, 10], [1, 2, 3]):
            with self.subTest(coords=coords):
                xyxy, reason = c.geometry({'bbox_xywh': coords}, 40, 30, 8)
                self.assertIsNone(xyxy)
                self.assertIsNotNone(reason)

    def test_rounding_matches_tv3_and_eight_pixels_is_accepted(self):
        self.assertEqual(c.geometry({'bbox_xywh': [0.5, 1.5, 8, 8]}, 40, 30, 8), ([0, 2, 8, 10], None))

    def test_source_leakage_rejected_even_if_offending_row_would_be_filtered(self):
        for key in ('image_id', 'file_name', 'seq_id', 'location'):
            with self.subTest(key=key):
                first, second = row(), row('b', 'val')
                second[key] = first[key]
                if key == 'seq_id':
                    second['sequence_id'] = first['sequence_id']
                second['boxes'] = []
                with self.assertRaisesRegex(ValueError, 'leakage'):
                    self.select([first, second])

    def test_missing_group_identity_and_alias_mismatch_fail(self):
        for key in ('location', 'seq_id', 'sequence_id'):
            record = row()
            record[key] = ''
            with self.assertRaises(ValueError):
                self.select([record])
        record = row()
        record['sequence_id'] = 'other'
        with self.assertRaisesRegex(ValueError, 'aliases'):
            self.select([record])

    def test_sequence_cannot_span_two_locations_even_inside_train(self):
        first, second = row(), row('b')
        second['seq_id'] = second['sequence_id'] = first['seq_id']
        with self.assertRaisesRegex(ValueError, 'spans locations'):
            self.select([first, second])

    def test_exact_duplicate_across_splits_fails_within_split_is_reported(self):
        first, second = row(), row('b', 'val')
        second['quality'] = copy.deepcopy(first['quality'])
        with self.assertRaisesRegex(ValueError, 'duplicate crosses'):
            self.select([first, second])
        second['split'] = 'train'
        accepted, _, _, _ = self.select([first, second])
        report, duplicates = c.audit(accepted)
        self.assertEqual(report['exact_duplicate_groups'], 1)
        self.assertEqual(duplicates[0]['action'], 'retain_and_report')

    def test_statistics_balance_and_no_split_changes(self):
        records = [row('a'), row('b', 'val'), row('c', 'test'), row('d', 'val')]
        records[-1]['boxes'] = []
        files, objects = c.bundle_files(records, self.cmap, self.config)
        for counts in objects['summary.json']['by_split'] + objects['summary.json']['by_class_split']:
            self.assertEqual(counts['requested'], counts['retained'] + counts['excluded'])
        self.assertEqual(files['val.jsonl'], [records[1]])
        self.assertEqual(objects['summary.json']['split_changes'], 0)

    def test_all_invalid_refuses_empty_snapshot(self):
        record = row()
        record['boxes'] = []
        with self.assertRaisesRegex(ValueError, 'empty dataset'):
            self.select([record])


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'data/images').mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'data/images')
        self.folder = Path(self.temp.name)
        self.source = self.folder / 'source'
        self.source.mkdir()
        self.output, self.state, self.report = (self.folder / name for name in ('comparison', 'state', 'report.json'))
        self.config_path = self.folder / 'config.json'
        config = load_json(c.DEFAULT_CONFIG)
        config['source_dir'] = self.source.relative_to(ROOT).as_posix()
        atomic_json(self.config_path, config)
        self.rows = [row('a'), row('b', 'val'), row('c', 'test')]
        for record, color in zip(self.rows, ('white', 'black', 'blue')):
            path = self.folder / (record['image_id'] + '.jpg')
            Image.new('RGB', (40, 30), color).save(path)
            quality = inspect_image(path, record)
            record['quality'] = {k: quality[k] for k in ('sha256', 'pixel_sha256', 'bytes', 'image_format', 'image_mode', 'validated_utc')}
            record['quality']['local_path'] = path.relative_to(ROOT).as_posix()
        write_lines(self.source / 'manifest_v2.jsonl', self.rows)
        atomic_json(self.source / 'class_map.json', {'0': 'sambar', '1': 'silver_pheasant'})
        atomic_json(self.source / 'provenance.json', {'source_seed': 42,
                    'files_sha256': {name: sha256(self.source / name) for name in ('manifest_v2.jsonl', 'class_map.json')}})
        self.stack = ExitStack()
        # The v2 parent-chain validator has its own suite; this fixture isolates comparison publication.
        self.stack.enter_context(patch.object(c, 'validate_v2'))
        self.stack.enter_context(redirect_stdout(io.StringIO()))

    def tearDown(self):
        self.stack.close()
        self.temp.cleanup()

    def freeze(self):
        return f.freeze(self.config_path, self.output, self.state, self.report)

    def rehash(self, name):
        path = self.output / 'provenance.json'
        provenance = load_json(path)
        provenance['files_sha256'][name] = sha256(self.output / name)
        atomic_json(path, provenance)

    def test_publish_and_resume_preserve_every_snapshot_byte(self):
        first = self.freeze()
        before = {p.relative_to(self.output).as_posix(): sha256(p) for p in self.output.rglob('*') if p.is_file()}
        with patch.object(f, 'bundle_files', side_effect=AssertionError('No rebuild')):
            second = self.freeze()
        after = {p.relative_to(self.output).as_posix(): sha256(p) for p in self.output.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertTrue(first['passed'] and second['passed'])
        self.assertTrue(second['local_images_redecoded'])

    def test_interruption_resumes_saved_receipts_and_publishes_once(self):
        real = f.image_check
        def interrupted(record):
            if record['image_id'] == 'b':
                raise OSError('Simulated interruption')
            return real(record)
        with patch.object(f, 'image_check', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.freeze()
        self.assertFalse(self.output.exists())
        completed = len(list((self.state / 'records').glob('*.json')))
        self.assertGreaterEqual(completed, 1)
        self.assertLess(completed, 3)
        self.assertEqual(load_json(self.state / 'task_state.json')['status'], 'failed')
        with patch.object(f, 'image_check', wraps=real) as checker:
            self.freeze()
        checked_ids = {call.args[0]['image_id'] for call in checker.call_args_list}
        self.assertNotIn('a', checked_ids)
        self.assertIn('b', checked_ids)
        self.assertEqual(len(checked_ids), 3 - completed)

    def test_interrupted_publication_leaves_only_staging_then_recovers(self):
        with patch.object(f, 'write_lines', side_effect=OSError('Disk error')):
            with self.assertRaises(OSError):
                self.freeze()
        self.assertFalse(self.output.exists())
        self.assertTrue(list(self.output.parent.glob('comparison.staging-*')))
        self.assertTrue(self.freeze()['passed'])

    def test_raw_manifest_tampering_rejected(self):
        self.freeze()
        (self.output / 'b1/train.jsonl').write_text('', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Snapshot modified'):
            v.validate(self.output, check_images=False)

    def test_semantic_tampering_rejected_even_after_rehash(self):
        self.freeze()
        for name, key, value in (
            ('b2/train.jsonl', 'label', 'silver_pheasant'),
            ('train.jsonl', 'split', 'val'),
            ('b2/train.jsonl', 'bbox_xyxy', [0, 0, 10, 10]),
            ('b2/train.jsonl', 'sample_weight', 0.1),
        ):
            with self.subTest(name=name, key=key):
                path = self.output / name
                before = path.read_bytes()
                records = read_rows(path)
                records[0][key] = value
                write_lines(path, records)
                self.rehash(name)
                with self.assertRaisesRegex(ValueError, 'Derived view/source mismatch'):
                    v.validate(self.output, check_images=False)
                path.write_bytes(before)
                self.rehash(name)

    def test_false_counts_rejected_after_rehash(self):
        self.freeze()
        path = self.output / 'summary.json'
        counts = load_json(path)
        counts['retained'] = 999
        atomic_json(path, counts)
        self.rehash('summary.json')
        with self.assertRaisesRegex(ValueError, 'Summary/policy/audit mismatch'):
            v.validate(self.output, check_images=False)

    def test_changed_policy_fails_without_rewriting_frozen_data(self):
        self.freeze()
        before = sha256(self.output / 'manifest.jsonl')
        config = load_json(self.config_path)
        config['min_crop_side'] = 9
        atomic_json(self.config_path, config)
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.freeze()
        self.assertEqual(sha256(self.output / 'manifest.jsonl'), before)

    def test_source_changed_rejected_even_with_new_source_hashes(self):
        self.freeze()
        source = read_rows(self.source / 'manifest_v2.jsonl')
        source[0]['split'] = 'val'
        write_lines(self.source / 'manifest_v2.jsonl', source)
        with self.assertRaisesRegex(ValueError, 'Source snapshot changed'):
            v.validate(self.output, check_images=False)

    def test_missing_image_stops_build_without_silently_excluding_it(self):
        path = ROOT / self.rows[0]['quality']['local_path']
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.freeze()
        self.assertFalse(self.output.exists())
        self.assertFalse(load_json(self.report)['passed'])

    def test_corruption_after_publication_cannot_pass_full_validation(self):
        self.freeze()
        (ROOT / self.rows[0]['quality']['local_path']).write_bytes(b'corrupt')
        self.assertFalse(v.validate(self.output, check_images=False)['local_images_redecoded'])
        with self.assertRaises(ValueError):
            self.freeze()
        self.assertFalse(load_json(self.report)['passed'])

    def test_unexpected_frozen_file_rejected(self):
        self.freeze()
        (self.output / 'untracked.txt').write_text('unexpected', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unexpected'):
            v.validate(self.output, check_images=False)


if __name__ == '__main__':
    unittest.main()
