import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import inventory_tv1_w4 as inv
from download_subset import atomic_json, inspect_image, sha256


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.image = self.root / 'data/images/test.png'
        self.image.parent.mkdir(parents=True)
        Image.new('RGB', (100, 100), (40, 80, 120)).save(self.image)
        self.row = {'image_id': 'image1', 'label': 'class_a', 'class_id': 0,
                    'split': 'test', 'sequence_id': 'seq1', 'location': 'loc1',
                    'width': 100, 'height': 100, 'url': 'https://example.org/test.png',
                    'boxes': [{'bbox_xywh': [0, 0, 5, 5]}]}
        self.row['quality'] = {**inspect_image(self.image, self.row), 'local_path': 'data/images/test.png'}
        self.crop = {**self.row, 'bbox_xyxy': [0, 0, 5, 5]}
        self.output = self.root / 'outputs/inventory'
        self.comp = self.root / 'data/processed/comparison_v1'
        atomic_json(self.comp / 'provenance.json', {'fixture': True})
        atomic_json(self.comp / 'class_map.json', {'0': 'class_a'})
        atomic_json(self.comp / 'summary.json', {'by_class_split': [
            {'split': 'test', 'label': 'class_a', 'retained': 1, 'sequences': 1, 'locations': 1, 'b2_crops': 1}]})
        proof = {'status': 'PASS', 'test_opened': False, 'checkpoint_sha256': 'a' * 64,
                 'checkpoint_bytes': 100, 'provenance_sha256': sha256(self.comp / 'provenance.json'), 'best_epoch': 21}
        atomic_json(self.root / 'reports/proof.json', proof)
        self.lock = {**proof, 'lock_id': 'fixture', 'data_inventory_allowed': True,
                     'validation_report': 'reports/proof.json',
                     'validation_report_sha256': sha256(self.root / 'reports/proof.json')}
        self.lock_path = self.root / 'configs/lock.json'
        atomic_json(self.lock_path, self.lock)

    def run_inventory(self):
        with patch.object(inv, 'ROOT', self.root), patch.object(inv, 'validate', return_value={'passed': True}), \
                patch.object(inv, 'read_rows', side_effect=lambda path: [self.crop] if path.parent.name == 'b2' else [self.row]):
            return inv.inventory(self.root, self.output, self.lock_path)

    def test_counts_use_distinct_sequences_not_crop_count(self):
        other = {**self.row, 'image_id': 'image2'}
        rows = [self.row, other]
        crops = [self.crop, self.crop.copy(), {**self.crop, 'image_id': 'image2'}]
        before = copy.deepcopy(rows)
        result = inv.distribution(rows, crops, ['class_a'])
        self.assertEqual(result['total'], {'images': 2, 'sequences': 1, 'locations': 1, 'crops': 3, 'unique_rgb': 1})
        self.assertEqual(rows, before)
        with self.assertRaisesRegex(ValueError, 'metadata mismatch'):
            inv.distribution(rows, [{**c, 'label': 'wrong'} for c in crops], ['class_a'])
        with self.assertRaisesRegex(ValueError, 'parent mismatch'):
            inv.distribution(rows, [self.crop], ['class_a'])

    def test_examples_deterministic_not_relabeling(self):
        other = {**self.row, 'image_id': 'image2'}
        crops = [self.crop, {**self.crop, 'image_id': 'image2'}]
        result = inv.select_examples([self.row, other], crops)
        self.assertEqual(result, inv.select_examples([other, self.row], list(reversed(crops))))
        self.assertEqual(result['duplicate_groups'], [['image1', 'image2']])
        self.assertEqual(result['counts']['small_box_images'], 2)
        for item in result['examples']:
            self.assertFalse(item['label_error_confirmed'])
            self.assertFalse(item['model_prediction_used'])
            self.assertEqual(item['action'], 'retain_unchanged')
        with self.assertRaisesRegex(ValueError, 'geometry'):
            inv.select_examples([self.row], [{**self.crop, 'bbox_xyxy': [0, 0, 101, 5]}])

    def test_lock_proof_and_path_guards(self):
        with patch.object(inv, 'ROOT', self.root):
            self.assertEqual(inv.verify_lock(self.lock_path)['lock_id'], 'fixture')
            atomic_json(self.root / 'reports/proof.json', {'status': 'FAILED'})
            with self.assertRaisesRegex(ValueError, 'Changed validation proof'):
                inv.verify_lock(self.lock_path)
        with self.assertRaisesRegex(ValueError, 'outside'):
            inv.safe_image(self.root, '../outside.jpg')
        with self.assertRaisesRegex(ValueError, 'Outputs must stay'):
            inv.inventory(self.root, self.root / 'data', self.lock_path)

    def test_resume_rehashes_and_detects_changed_missing_files(self):
        before = sha256(self.image)
        first = self.run_inventory()
        self.assertEqual(first['valid_images'], 1)
        self.assertEqual(first['reused_decodes'], 0)
        with patch.object(inv, 'inspect_image', side_effect=AssertionError('Should reuse verified decode')):
            second = self.run_inventory()
        self.assertEqual(second['reused_decodes'], 1)
        self.assertEqual(sha256(self.image), before)
        self.assertEqual(second['label_changes'], 0)
        Image.new('RGB', (100, 100), (200, 0, 0)).save(self.image)
        with self.assertRaisesRegex(ValueError, 'Missing/changed/corrupt'):
            self.run_inventory()
        self.assertFalse(json.loads((self.output / 'quality_checks.json').read_text())[0]['valid'])
        self.image.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing/changed/corrupt'):
            self.run_inventory()
        self.assertEqual(json.loads((self.output / 'inventory.json').read_text())['invalid_images'], 1)

    def test_interrupted_run_keeps_per_image_check(self):
        with patch.object(inv, 'select_examples', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.run_inventory()
        self.assertTrue((self.output / 'state/image1.json').exists())
        self.assertEqual(self.run_inventory()['reused_decodes'], 1)
