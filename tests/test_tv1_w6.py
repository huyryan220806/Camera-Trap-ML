"""Quality gates: frozen inputs, exact/near duplicates, review and safe resume."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_tv1_w6 as w
from download_subset import inspect_image, receipt_path, atomic_json
from prepare_tv1_w5 import encoded, write_bytes, verify_files


def feature(image_id, sha, pixel, phash='0000000000000000', dhash='00000000000000000000000000000000', split='train'):
    return dict(image_id=image_id, sha256=sha, pixel_sha256=pixel, phash64=phash, dhash128=dhash, split=split)


class DataGateTests(unittest.TestCase):
    config = {'phash_max_distance': 4, 'dhash_max_distance': 8}

    def test_exact_cross_split_excludes_only_new_and_preserves_original(self):
        old = feature('old', 'same', 'same', split='val')
        new = feature('new', 'same', 'same')
        exact, near, reasons = w.screen_duplicates([old, new], {'new'}, self.config)
        self.assertEqual(set(reasons), {'new'})
        self.assertEqual(near, [])
        self.assertTrue(all(r['new_ids_excluded'] == ['new'] for r in exact))
        self.assertEqual(old['split'], 'val')

    def test_reencoding_identical_rgb_still_rejected(self):
        _, _, reasons = w.screen_duplicates([feature('a', 'jpeg1', 'same'), feature('b', 'jpeg2', 'same')], {'b'}, self.config)
        self.assertEqual(reasons['b'], ['exact_duplicate_pixel_sha256'])

    def test_two_new_duplicates_both_quarantined_no_arbitrary_survivor(self):
        _, _, reasons = w.screen_duplicates([feature('a', 'same', 'same'), feature('b', 'same', 'same')], {'a', 'b'}, self.config)
        self.assertEqual(set(reasons), {'a', 'b'})

    def test_old_duplicate_not_dropped_or_called_new_failure(self):
        exact, _, reasons = w.screen_duplicates([feature('a', 'same', 'same', split='test'), feature('b', 'same', 'same', split='test')], set(), self.config)
        self.assertEqual(reasons, {})
        self.assertTrue(exact)

    def test_near_screen_requires_both_hash_thresholds(self):
        rows = [feature('old', 'a', 'a'), feature('new', 'b', 'b', dhash='ffffffffffffffffffffffffffffffff')]
        _, near, reasons = w.screen_duplicates(rows, {'new'}, self.config)
        self.assertFalse(near)
        self.assertFalse(reasons)
        rows[1]['dhash128'] = '00000000000000000000000000000001'
        _, near, reasons = w.screen_duplicates(rows, {'new'}, self.config)
        self.assertEqual(reasons['new'], ['near_duplicate_pending_review'])
        self.assertEqual(near[0]['decision'], 'suspected_only_quarantine_pending_review')

    def test_fixed_visual_sample_invariant_to_input_order(self):
        rows = [{'image_id': str(i), 'label': 'sambar', 'quality': {'local_path': str(i), 'sha256': str(i)}, 'boxes': []} for i in range(30)]
        self.assertEqual(w.sample_visual(rows, {'0': 'sambar'}, 42, 10), w.sample_visual(rows[::-1], {'0': 'sambar'}, 42, 10))
        self.assertEqual(len(w.sample_visual(rows, {'0': 'sambar'}, 42, 10)), 10)

    def test_visual_review_missing_duplicate_or_wrong_image_fails(self):
        queue = [{'image_id': 'a', 'sha256': 'x'}]
        review = {'method': 'visual_sample_not_expert_taxonomic_validation', 'items': []}
        with self.assertRaisesRegex(ValueError, 'missing'):
            w.visual_decisions(queue, review)
        item = {'image_id': 'a', 'sha256': 'wrong', 'decision': 'retain_metadata_label', 'observation': 'animal visible'}
        review['items'] = [item]
        with self.assertRaisesRegex(ValueError, 'checksum'):
            w.visual_decisions(queue, review)
        item['sha256'] = 'x'
        review['items'] = [item, item]
        with self.assertRaisesRegex(ValueError, 'missing/duplicate'):
            w.visual_decisions(queue, review)

    def test_visual_ambiguity_excluded_without_relabel(self):
        item = {'image_id': 'a', 'sha256': 'x', 'decision': 'quarantine', 'observation': 'too occluded to assess'}
        review = {'method': 'visual_sample_not_expert_taxonomic_validation', 'items': [item]}
        out = w.visual_decisions([{'image_id': 'a', 'sha256': 'x'}], review)
        self.assertEqual(out[0]['reason'], 'visual_ambiguity_pending_expert')
        self.assertNotIn('label', out[0])

    def test_resume_rechecks_bytes_even_with_cached_feature(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'data/images') as folder:
            folder = Path(folder)
            path = folder / 'a.jpg'
            Image.new('RGB', (32, 32), 'red').save(path)
            row = {'image_id': 'a', 'width': 32, 'height': 32, 'boxes': [], 'split': 'train',
                   'label': 'sambar', 'seq_id': 's', 'location': 'l'}
            q = inspect_image(path, row)
            row['quality'] = {**q, 'local_path': path.relative_to(ROOT).as_posix()}
            original = w.checked_feature(row, folder / 'state')
            with patch.object(w, 'inspect_image', side_effect=AssertionError('cached decode should be reused')):
                self.assertEqual(w.checked_feature(row, folder / 'state'), original)
            Image.new('RGB', (32, 32), 'blue').save(path)
            with self.assertRaisesRegex(ValueError, 'changed image'):
                w.checked_feature(row, folder / 'state')

    def test_download_receipt_cannot_change_split_or_hide_missing_rows(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            folder = Path(folder)
            row = {'image_id': 'x', 'file_name': 'public/x.jpg',
                   'url': 'https://storage.googleapis.com/public-datasets-lila/swg-camera-traps/public/x.jpg',
                   'split': 'train', 'label': 'sambar'}
            with self.assertRaisesRegex(ValueError, 'Unprocessed'):
                w.receipt_rows([row], folder / 'images', folder / 'state')
            atomic_json(receipt_path(folder / 'state', row), {**row, 'split': 'test', 'status': 'valid'})
            with self.assertRaisesRegex(ValueError, 'identity'):
                w.receipt_rows([row], folder / 'images', folder / 'state')

    def test_missing_remote_gets_explicit_exclusion(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            folder = Path(folder)
            row = {'image_id': 'x', 'file_name': 'public/x.jpg',
                   'url': 'https://storage.googleapis.com/public-datasets-lila/swg-camera-traps/public/x.jpg',
                   'split': 'train', 'label': 'sambar'}
            local = (folder / 'images/public/x.jpg').relative_to(ROOT).as_posix()
            atomic_json(receipt_path(folder / 'state', row), {**row, 'status': 'missing_remote', 'detail': 'HTTP 404', 'local_path': local})
            valid, failed = w.receipt_rows([row], folder / 'images', folder / 'state')
            self.assertFalse(valid)
            self.assertEqual(failed[0]['reason'], 'missing_remote')

    def test_write_once_inventory_rejects_mutation_and_extras(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            folder = Path(folder)
            files = encoded({'a.json': {'x': 1}, 'b/train.jsonl': [{'split': 'train'}]})
            for name, content in files.items():
                write_bytes(folder / name, content)
            verify_files(folder, files)
            (folder / 'a.json').write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'modified'):
                verify_files(folder, files)
            write_bytes(folder / 'a.json', files['a.json'])
            (folder / 'unexpected').write_text('extra')
            with self.assertRaisesRegex(ValueError, 'file set'):
                verify_files(folder, files)


if __name__ == '__main__':
    unittest.main()
