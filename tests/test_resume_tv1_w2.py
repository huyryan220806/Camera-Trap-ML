from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import download_subset as d
import resume_tv1_w2 as r
import task_lock as lock
from test_download_subset import sample_row, jpeg_bytes, Response


class LockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.state = Path(self.temp.name) / 'state'

    def tearDown(self):
        self.temp.cleanup()

    def test_exception_releases_lock_and_concurrent_writer_is_blocked(self):
        with self.assertRaisesRegex(ValueError, 'interruption'):
            with lock.state_lock(self.state):
                with self.assertRaisesRegex(RuntimeError, 'active'):
                    with lock.state_lock(self.state):
                        self.fail('Second writer acquired the lock')
                raise ValueError('interruption')
        with lock.state_lock(self.state):
            self.assertTrue((self.state / 'active.lock').exists())
        self.assertFalse((self.state / 'active.lock').exists())
        self.assertTrue((self.state / 'writer.guard').exists())

    def test_abrupt_process_exit_is_recovered_without_deleting_history(self):
        code = ('import os,sys; sys.path.insert(0, ' + repr(str(ROOT / 'scripts')) + ')\n'
                'from task_lock import state_lock\n'
                'with state_lock(' + repr(str(self.state)) + '):\n'
                '    os._exit(0)\n')
        subprocess.run([sys.executable, '-c', code], cwd=ROOT, check=True,
                       capture_output=True, timeout=30)
        self.assertTrue((self.state / 'active.lock').exists())
        with lock.state_lock(self.state):
            self.assertEqual(len(list(self.state.glob('active.interrupted-*.lock'))), 1)

    def test_live_legacy_owner_is_never_removed(self):
        self.state.mkdir()
        active = self.state / 'active.lock'
        active.write_text(f'pid={os.getpid()} started=now\n', encoding='utf-8')
        before = active.read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'still running'):
            with lock.state_lock(self.state):
                self.fail('Must not take over a live legacy process')
        self.assertEqual(active.read_bytes(), before)

    def test_unknown_owner_requires_manual_inspection(self):
        self.state.mkdir()
        active = self.state / 'active.lock'
        active.write_text('incomplete lock', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unreadable'):
            with lock.state_lock(self.state):
                pass
        self.assertTrue(active.exists())


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.folder = Path(self.temp.name)
        self.images, self.state = self.folder / 'images', self.folder / 'state'
        self.output, self.source = self.folder / 'v2', self.folder / 'source.jsonl'
        self.report, self.log = self.folder / 'verification.json', self.folder / 'events.jsonl'
        self.row = sample_row()
        self.source.write_text(json.dumps(self.row) + '\n', encoding='utf-8')
        d.download_one(self.row, self.images, self.state, d.EventLog(self.log).emit,
                       get=lambda *a, **k: Response(jpeg_bytes()))
        self.result = {'passed': True, 'local_images_redecoded': True}
        self.stack = ExitStack()
        self.stack.enter_context(patch.object(r, 'load_source', return_value=[self.row]))
        self.download = self.stack.enter_context(patch.object(r, 'run_download', return_value=0))
        self.build = self.stack.enter_context(patch.object(r, 'build', side_effect=self.publish))
        self.validate = self.stack.enter_context(patch.object(r, 'validate', return_value=self.result))

    def tearDown(self):
        self.stack.close()
        self.temp.cleanup()

    def publish(self, args):
        self.output.mkdir()
        d.atomic_json(self.output / 'provenance.json', {'source_sha256': d.sha256(self.source)})

    def run_task(self):
        return r.resume(self.source, self.images, self.state, self.log, self.output, self.report)

    def test_completed_images_skip_network_and_second_run_preserves_snapshot(self):
        self.assertEqual(self.run_task(), self.result)
        before = (self.output / 'provenance.json').read_bytes()
        self.run_task()
        self.download.assert_not_called()
        self.assertEqual(self.build.call_count, 1)
        self.assertEqual((self.output / 'provenance.json').read_bytes(), before)
        checkpoint = d.load_json(self.state / 'task_state.json')
        self.assertEqual(checkpoint['status'], 'complete')
        self.assertEqual(checkpoint['completed_stages'], ['download', 'build', 'validate'])
        self.assertTrue(self.validate.call_args.kwargs['check_images'])

    def test_changed_or_missing_bytes_require_download(self):
        path = d.safe_image_path(self.images, self.row)
        path.write_bytes(jpeg_bytes(color='black'))
        self.assertTrue(r.needs_download([self.row], self.images, self.state))
        path.unlink()
        self.assertTrue(r.needs_download([self.row], self.images, self.state))

    def test_receipt_split_mismatch_is_not_silently_rewritten(self):
        path = d.receipt_path(self.state, self.row)
        saved = d.load_json(path)
        saved['split'] = 'test'
        d.atomic_json(path, saved)
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            self.run_task()
        self.download.assert_not_called()
        self.build.assert_not_called()

    def test_download_failure_keeps_checkpoint_and_never_freezes(self):
        d.safe_image_path(self.images, self.row).unlink()
        self.download.return_value = 1
        with self.assertRaisesRegex(RuntimeError, 'Some images failed'):
            self.run_task()
        checkpoint = d.load_json(self.state / 'task_state.json')
        self.assertEqual((checkpoint['stage'], checkpoint['status']), ('download', 'failed'))
        self.assertIn('resume_tv1_w2.py', checkpoint['next_command'])
        self.assertFalse(self.output.exists())
        self.build.assert_not_called()

    def test_resume_after_validation_interruption_does_not_rebuild(self):
        self.validate.side_effect = KeyboardInterrupt('quota or process interruption')
        with self.assertRaises(KeyboardInterrupt):
            self.run_task()
        self.assertEqual(d.load_json(self.state / 'task_state.json')['stage'], 'validate')
        self.assertFalse(d.load_json(self.report)['passed'])
        self.validate.side_effect = None
        self.run_task()
        self.assertEqual(self.build.call_count, 1)
        self.download.assert_not_called()
        self.assertTrue(d.load_json(self.report)['passed'])

    def test_checkpoint_is_not_trusted_when_files_are_missing(self):
        d.atomic_json(self.state / 'task_state.json', {'stage': 'complete', 'status': 'complete'})
        d.safe_image_path(self.images, self.row).unlink()
        self.download.return_value = 1
        with self.assertRaises(RuntimeError):
            self.run_task()
        self.download.assert_called_once()

    def test_source_binding_change_is_rejected(self):
        d.atomic_json(self.state / 'source.json', {'source_sha256': 'different'})
        with self.assertRaisesRegex(ValueError, 'different source'):
            self.run_task()
        self.download.assert_not_called()
        self.build.assert_not_called()

    def test_invalid_existing_snapshot_stops_before_download(self):
        self.publish(None)
        self.validate.side_effect = AssertionError('snapshot modified')
        with self.assertRaisesRegex(AssertionError, 'snapshot modified'):
            self.run_task()
        self.download.assert_not_called()
        self.build.assert_not_called()
        self.assertFalse(d.load_json(self.report)['passed'])


if __name__ == '__main__':
    unittest.main()
