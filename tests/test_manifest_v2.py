from contextlib import ExitStack, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_manifest_v2 as b
import download_subset as d
import validate_manifest_v2 as v
from task_lock import state_lock
from test_download_subset import sample_row, jpeg_bytes, Response


class BundleTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'data/images').mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'data/images')
        self.folder = Path(self.temp.name)
        self.args = SimpleNamespace(source=self.folder / 'source.jsonl',
                                    images=self.folder / 'images', state=self.folder / 'state',
                                    output=self.folder / 'v2', log=self.folder / 'events.jsonl')
        self.rows = [sample_row('a', 'train'), sample_row('b', 'val'), sample_row('c', 'test')]
        b.write_lines(self.args.source, self.rows)
        log = d.EventLog(self.args.log)
        for row, color in zip(self.rows, ('white', 'black', 'blue')):
            d.download_one(row, self.args.images, self.args.state, log.emit,
                           get=lambda *a, color=color, **k: Response(jpeg_bytes(color=color)))
        d.atomic_json(self.args.state / 'source.json', {
            'source_sha256': d.sha256(self.args.source), 'source_rows': len(self.rows),
            'images': self.args.images.relative_to(ROOT).as_posix()})
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(b, 'load_source', return_value=self.rows))
        self.stack.enter_context(patch.object(v, 'load_source', return_value=self.rows))
        self.stack.enter_context(redirect_stdout(io.StringIO()))
        with state_lock(self.args.state):
            b.build(self.args)

    def tearDown(self):
        self.stack.close()
        self.temp.cleanup()

    def rehash(self, name):
        path = self.args.output / 'provenance.json'
        provenance = d.load_json(path)
        provenance['files_sha256'][name] = d.sha256(self.args.output / name)
        d.atomic_json(path, provenance)

    def test_real_bundle_reconciles_and_validates_local_images(self):
        result = v.validate(self.args.output)
        self.assertEqual((result['requested'], result['accepted'], result['excluded']), (3, 3, 0))
        self.assertEqual(result['accepted_per_split'], {'train': 1, 'val': 1, 'test': 1})
        self.assertTrue(result['local_images_redecoded'])
        self.assertEqual(result['source_sha256'], d.sha256(self.args.source))

    def test_build_refuses_overwrite(self):
        before = d.sha256(self.args.output / 'provenance.json')
        with self.assertRaisesRegex(ValueError, 'never overwrite'):
            with state_lock(self.args.state):
                b.build(self.args)
        self.assertEqual(d.sha256(self.args.output / 'provenance.json'), before)

    def test_snapshot_file_tampering_is_rejected(self):
        (self.args.output / 'train.jsonl').write_text('', encoding='utf-8')
        with self.assertRaisesRegex(AssertionError, 'Snapshot modified'):
            v.validate(self.args.output, check_images=False)

    def test_changed_split_rejected_even_with_updated_snapshot_hash(self):
        path = self.args.output / 'manifest_v2.jsonl'
        rows = d.read_rows(path)
        rows[0]['split'] = 'val'
        b.write_lines(path, rows)
        self.rehash(path.name)
        with self.assertRaisesRegex(AssertionError, 'v1 field/split changed'):
            v.validate(self.args.output, check_images=False)

    def test_local_corruption_requires_full_verification(self):
        path = d.safe_image_path(self.args.images, self.rows[0])
        path.write_bytes(b'corrupt')
        self.assertFalse(v.validate(self.args.output, check_images=False)['local_images_redecoded'])
        with self.assertRaises(d.QualityError):
            v.validate(self.args.output)

    def test_missing_download_log_coverage_is_rejected(self):
        path = self.args.output / 'download_events.jsonl'
        b.write_lines(path, [])
        self.rehash(path.name)
        with self.assertRaisesRegex(AssertionError, 'does not account'):
            v.validate(self.args.output, check_images=False)

    def test_wrong_split_counts_are_rejected(self):
        path = self.args.output / 'summary.json'
        summary = d.load_json(path)
        summary['by_split'][0]['accepted'] += 1
        d.atomic_json(path, summary)
        self.rehash(path.name)
        with self.assertRaisesRegex(AssertionError, 'Counts mismatch'):
            v.validate(self.args.output, check_images=False)


if __name__ == '__main__':
    unittest.main()
