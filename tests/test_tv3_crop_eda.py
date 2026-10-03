"""Tests for TV3 crop EDA helpers. Uses synthetic data only; no image download, no test split."""
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import matplotlib
matplotlib.use('Agg')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from prepare_swg import valid_bbox  # noqa: E402
import tv3_crop_eda as eda  # noqa: E402


def record(i, species='sambar', split='train', loc=None):
    return {'image_id': f'img{i:04d}', 'split': split, 'label': species, 'location': loc or f'L{i % 4}',
            'sequence_id': f'seq{i:04d}', 'url': f'http://example/{i}.jpg',
            'boxes': [{'label': species, 'bbox_xywh': [1, 1, 5, 5]}]}


class IjsonDecimalTests(unittest.TestCase):
    def test_decimal_coordinates_are_read_as_float_and_accepted(self):
        doc = json.dumps({
            'images': [{'id': 'a', 'width': 100, 'height': 50}],
            'annotations': [{'image_id': 'a', 'bbox': [10.5, 5.25, 20.75, 10.5]},
                            {'image_id': 'a', 'bbox': [-0.81, 5.0, 10.0, 10.0]},
                            {'image_id': 'a'}],
        }).encode()
        images = list(eda.iter_items(io.BytesIO(doc), 'images'))
        anns = list(eda.iter_items(io.BytesIO(doc), 'annotations'))
        self.assertIsInstance(anns[0]['bbox'][0], float)
        result = eda.scan_box_annotations(images, anns)
        self.assertEqual(result['valid_boxes'], 1)
        self.assertEqual(result['geometry_errors'], 1)
        self.assertEqual(result['missing_bbox_records'], 1)
        self.assertNotIn('nonfinite_bbox', result['status_counts'])


class BoxEdgeTests(unittest.TestCase):
    im = {'width': 100, 'height': 50}

    def status(self, ann):
        return valid_bbox(ann, self.im)[1]

    def test_negative_coordinates_rejected(self):
        self.assertNotEqual(self.status({'bbox': [-0.1, 0, 10, 10]}), 'valid')
        self.assertNotEqual(self.status({'bbox': [0, -0.1, 10, 10]}), 'valid')

    def test_one_pixel_box_not_scaled(self):
        self.assertEqual(valid_bbox({'bbox': [10, 10, 1, 1]}, self.im), ([10, 10, 1, 1], 'valid'))

    def test_overflow_within_tolerance_is_clipped(self):
        box, status = valid_bbox({'bbox': [90, 40, 10.5, 10.5]}, self.im)
        self.assertEqual(status, 'valid')
        self.assertEqual(box, [90, 40, 10, 10])

    def test_overflow_beyond_tolerance_rejected(self):
        self.assertNotEqual(self.status({'bbox': [90, 40, 12, 10]}), 'valid')

    def test_missing_bbox(self):
        self.assertEqual(self.status({}), 'no_bbox')


class SamplingTests(unittest.TestCase):
    def setUp(self):
        self.records = [record(i) for i in range(30)] + [record(100 + i, split='test') for i in range(10)] \
            + [record(200 + i, split='val') for i in range(10)]

    def test_seed_is_reproducible(self):
        a = [r['image_id'] for r in eda.sample_species(self.records, 'sambar', seed=42)]
        b = [r['image_id'] for r in eda.sample_species(list(reversed(self.records)), 'sambar', seed=42)]
        self.assertEqual(a, b)

    def test_only_unique_train_ids(self):
        picked = eda.sample_species(self.records, 'sambar')
        ids = [r['image_id'] for r in picked]
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        self.assertTrue(all(r['split'] == 'train' for r in picked))
        self.assertEqual(eda.ids_not_in_train([{'image_id': i} for i in ids], self.records), [])

    def test_does_not_fill_from_val_or_test(self):
        recs = [record(i) for i in range(3)] + [record(100 + i, split='test') for i in range(20)]
        self.assertEqual(len(eda.sample_species(recs, 'sambar')), 3)

    def test_images_without_boxes_skipped(self):
        recs = [dict(record(i), boxes=[]) for i in range(5)]
        self.assertEqual(eda.sample_species(recs, 'sambar'), [])


class DownloadFailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=ROOT))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_failed_downloads_are_logged_and_not_counted(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new('RGB', (20, 20), 'white').save(buf, format='JPEG')
        good = buf.getvalue()

        def fake_fetch(url):
            n = int(url.rsplit('/', 1)[1].split('.')[0])
            if n % 3 == 0:
                raise ConnectionError('simulated')
            if n % 3 == 1:
                return b'not an image'
            return good

        recs = [record(i) for i in range(6)]
        audit, errors, counts = eda.process_species('sambar', recs, self.tmp, fetch=fake_fetch, n=6)
        self.assertEqual(counts['selected'], 6)
        self.assertEqual(counts['saved'], 2)
        self.assertEqual(counts['failed'], 4)
        types = [e['type'] for e in errors]
        self.assertEqual(types.count('download_failed'), 2)
        self.assertEqual(types.count('decode_failed'), 2)
        self.assertEqual(len(list(self.tmp.glob('*_raw.jpg'))), 2)
        self.assertEqual(sum(1 for r in audit if r['status'] == 'saved'), 2)


if __name__ == '__main__':
    unittest.main()
