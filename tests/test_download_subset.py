import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import download_subset as d
from build_manifest_v2 import reconcile, counts_table, collect_statuses


def sample_row(image_id='a', split='train'):
    name = f'public/test/{image_id}.jpg'
    return {'image_id': image_id, 'file_name': name, 'url': d.BASE + name,
            'split': split, 'label': 'sambar', 'class_id': 2, 'location': image_id,
            'seq_id': image_id, 'sequence_id': image_id, 'width': 20, 'height': 10,
            'boxes': [{'label': 'sambar', 'bbox_xywh': [1, 1, 5, 5]}]}


def jpeg_bytes(size=(20, 10), color='white'):
    data = io.BytesIO()
    Image.new('RGB', size, color).save(data, format='JPEG')
    return data.getvalue()


class Response:
    def __init__(self, data=b'', status=200, length=None, interrupted=False):
        self.data = data
        self.status_code = status
        self.headers = {'Content-Length': str(len(data) if length is None else length), 'ETag': 'test'}
        self.interrupted = interrupted

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def iter_content(self, chunk_size):
        if self.interrupted:
            yield self.data[:20]
            raise requests.ConnectionError('interrupted stream')
        yield self.data


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.folder = Path(self.temp.name)
        self.images = self.folder / 'images'
        self.state = self.folder / 'state'
        self.events = []
        self.row = sample_row()

    def tearDown(self):
        self.temp.cleanup()

    def run_download(self, get, attempts=1):
        return d.download_one(self.row, self.images, self.state, self.events.append,
                              attempts=attempts, get=get, sleep=lambda _: None)

    def test_download_and_offline_resume(self):
        result = self.run_download(lambda *a, **k: Response(jpeg_bytes()))
        self.assertEqual(result['status'], 'valid')
        def no_network(*a, **k):
            self.fail('Valid cached image must not trigger network access')
        resumed = self.run_download(no_network)
        self.assertEqual(resumed['action'], 'reused')
        self.assertEqual(result['sha256'], resumed['sha256'])
        self.assertTrue(d.receipt_path(self.state, self.row).is_file())

    def test_missing_image_logged_without_three_retries(self):
        calls = []
        def missing(*a, **k):
            calls.append(1)
            return Response(status=404)
        result = self.run_download(missing, attempts=3)
        self.assertEqual(result['status'], 'missing_remote')
        self.assertEqual(len(calls), 1)
        self.assertFalse(d.safe_image_path(self.images, self.row).exists())

    def test_retry_transient_http_failure(self):
        responses = iter([Response(status=503), Response(jpeg_bytes())])
        result = self.run_download(lambda *a, **k: next(responses), attempts=2)
        self.assertEqual(result['status'], 'valid')
        self.assertEqual(result['attempt'], 2)

    def test_interrupted_download_restarts_only_partial_image(self):
        result = self.run_download(lambda *a, **k: Response(jpeg_bytes(), interrupted=True))
        self.assertEqual(result['status'], 'download_error')
        path = d.safe_image_path(self.images, self.row)
        self.assertFalse(path.exists())
        self.assertTrue(path.with_name(path.name + '.part').exists())
        resumed = self.run_download(lambda *a, **k: Response(jpeg_bytes()))
        self.assertEqual(resumed['status'], 'valid')
        self.assertEqual(path.read_bytes(), jpeg_bytes())

    def test_wrong_content_length_rejected(self):
        result = self.run_download(lambda *a, **k: Response(jpeg_bytes(), length=90000))
        self.assertEqual(result['status'], 'download_error')

    def test_corrupt_and_dimension_mismatch_excluded(self):
        for payload, reason in [(b'not an image', 'corrupt_image'),
                                (jpeg_bytes((10, 20)), 'dimension_mismatch')]:
            result = self.run_download(lambda *a, **k: Response(payload))
            self.assertEqual(result['status'], reason)
            self.assertFalse(d.safe_image_path(self.images, self.row).exists())

    def test_changed_cache_is_quarantined_and_redownloaded(self):
        self.run_download(lambda *a, **k: Response(jpeg_bytes()))
        d.safe_image_path(self.images, self.row).write_bytes(jpeg_bytes(color='black'))
        result = self.run_download(lambda *a, **k: Response(jpeg_bytes()))
        self.assertEqual(result['action'], 'downloaded')
        self.assertTrue(list((self.state / 'quarantine').glob('*.bin')))
        self.assertTrue(any(e.get('reason') == 'cache_changed' for e in self.events))

    def test_unknown_cached_file_requires_a_proven_download(self):
        path = d.safe_image_path(self.images, self.row)
        path.parent.mkdir(parents=True)
        path.write_bytes(jpeg_bytes())
        result = self.run_download(lambda *a, **k: Response(jpeg_bytes()))
        self.assertEqual(result['action'], 'downloaded')
        self.assertTrue(any(e.get('reason') == 'cache_untracked' for e in self.events))

    def test_unsafe_path_or_foreign_url_rejected(self):
        for changes in [{'file_name': '../outside.jpg'}, {'file_name': 'public/../../outside.jpg'},
                        {'url': 'http://localhost/private'}, {'file_name': 'public/C:bad.jpg'}]:
            with self.assertRaises(ValueError):
                d.safe_image_path(self.images, {**self.row, **changes})

    def test_only_root_is_resolved_when_leaf_does_not_exist(self):
        resolve = Path.resolve
        def guarded_resolve(path, *args, **kwargs):
            self.assertEqual(path, self.images)
            return resolve(path, *args, **kwargs)
        with patch.object(Path, 'resolve', guarded_resolve):
            path = d.safe_image_path(self.images, self.row)
        self.assertEqual(path, self.images / self.row['file_name'])

    def test_truncated_jpeg_not_accepted(self):
        path = self.folder / 'truncated.jpg'
        path.write_bytes(jpeg_bytes()[:-15])
        with self.assertRaises(d.QualityError):
            d.inspect_image(path, self.row)

    def test_interrupted_log_tail_preserved_and_repaired(self):
        path = self.folder / 'events.jsonl'
        path.write_bytes(b'{"event":"old"}\n{"incomplete":')
        log = d.EventLog(path)
        log.emit({'event': 'new'})
        self.assertEqual([r['event'] for r in d.read_rows(path)], ['old', 'new'])
        self.assertIn(b'incomplete', path.with_suffix('.interrupted-tail.bin').read_bytes())

    def test_freeze_refuses_unprocessed_source_rows(self):
        with self.assertRaisesRegex(ValueError, 'not processed'):
            collect_statuses([self.row], self.images, self.state)

    def test_export_rechecks_changed_and_missing_local_images(self):
        self.run_download(lambda *a, **k: Response(jpeg_bytes()))
        path = d.safe_image_path(self.images, self.row)
        path.write_bytes(jpeg_bytes(color='black'))
        checked = collect_statuses([self.row], self.images, self.state)
        self.assertEqual(checked[0]['status'], 'cache_changed')
        path.unlink()
        checked = collect_statuses([self.row], self.images, self.state)
        self.assertEqual(checked[0]['status'], 'missing_local')

    def test_export_rejects_receipt_for_a_different_split(self):
        self.run_download(lambda *a, **k: Response(jpeg_bytes()))
        path = d.receipt_path(self.state, self.row)
        receipt = d.load_json(path)
        receipt['split'] = 'test'
        d.atomic_json(path, receipt)
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            collect_statuses([self.row], self.images, self.state)


class ManifestV2Tests(unittest.TestCase):
    def status(self, row, pixel='pixels', state='valid'):
        return {**row, 'status': state, 'pixel_sha256': pixel, 'sha256': 'encoded',
                'bytes': 123, 'image_format': 'JPEG', 'image_mode': 'RGB',
                'validated_utc': '2026-10-08T00:00:00+00:00', 'local_path': 'data/images/a.jpg'}

    def test_every_original_field_is_preserved_no_rebalancing(self):
        rows = [sample_row('a', 'train'), sample_row('b', 'val'), sample_row('c', 'test')]
        statuses = [self.status(r, pixel=r['image_id']) for r in rows]
        statuses[1]['status'] = 'missing_remote'
        valid, excluded, groups = reconcile(rows, statuses)
        self.assertEqual([r['split'] for r in valid], ['train', 'test'])
        self.assertEqual(excluded[0]['split'], 'val')
        for r in valid + excluded:
            parent = next(x for x in rows if x['image_id'] == r['image_id'])
            self.assertEqual({k: r[k] for k in parent}, parent)
        table = counts_table(rows, valid, excluded, statuses)
        self.assertTrue(all(r['requested'] == r['accepted'] + r['excluded'] for r in table['by_split']))

    def test_cross_split_duplicates_exclude_all_without_moving(self):
        rows = [sample_row('a', 'train'), sample_row('b', 'test')]
        valid, excluded, groups = reconcile(rows, [self.status(r) for r in rows])
        self.assertEqual(valid, [])
        self.assertEqual({r['split'] for r in excluded}, {'train', 'test'})
        self.assertTrue(all(r['exclusion']['reason'] == 'cross_split_exact_duplicate' for r in excluded))
        self.assertEqual(groups[0]['action'], 'exclude_all')

    def test_same_split_duplicate_retained_but_label_conflict_excluded(self):
        rows = [sample_row('a'), sample_row('b')]
        valid, excluded, groups = reconcile(rows, [self.status(r) for r in rows])
        self.assertEqual(len(valid), 2)
        self.assertEqual(groups[0]['action'], 'retain_within_split')
        rows[1]['label'] = 'silver_pheasant'
        valid, excluded, groups = reconcile(rows, [self.status(r) for r in rows])
        self.assertEqual(len(excluded), 2)
        self.assertEqual(groups[0]['reason'], 'duplicate_label_conflict')


if __name__ == '__main__':
    unittest.main()
