"""Synthetic CPU-only review tests. No GPU, model download or actual experiment."""
import copy
import json
from pathlib import Path
import tempfile
import shutil
import importlib.util
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from src.training import dino_w6 as d
from src.training import dino_w6_control as c
from src.training import dino_probe as w5
from src.evaluation import w6_validation as v


def fixture():
    registry = w5.read_json(d.ROOT / 'experiments/w6/tv3_R6_3h.proposal.json')
    run = registry['runs'][6]
    run.update(source_sha='a' * 40, config_sha256='b' * 64)
    a = registry['r6_budget_amendment']
    a.update(status='APPROVED', source_sha=run['source_sha'], config_sha256=run['config_sha256'],
             runtime_sha256='c' * 64, approvals={k: {'path': k + '.json', 'sha256': 'd' * 64} for k in ('TV2', 'TV3')})
    run['approvals'] = {k: k + '.json' for k in ('TV2', 'TV3')}
    return registry


def usage(seconds, run='R6', aid=None, kind='official'):
    return {'version': 1, 'sessions': [dict(session_id='synthetic', run_id=run,
        attempt_id=aid or run + '_attempt01', kind=kind, seconds=seconds,
        heartbeat_seconds=0)], 'reconciliations': []}


def denied():
    exc = PermissionError('synthetic Windows lock')
    exc.winerror = 5
    return exc


class AmendmentTests(unittest.TestCase):
    def test_reload_revalidates_amendment_before_inference(self):
        spec = importlib.util.spec_from_file_location('r6_review_cli', d.ROOT / 'scripts/dino_w6.py')
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        config = w5.read_json(d.ROOT / 'configs/w6/tv3/R6.3h.candidate.json')
        runtime = {'synthetic': True}
        binding = dict(runtime=runtime, source_index={'commit': 'a' * 40})
        with patch.object(cli, 'read_config', return_value=config), \
                patch.object(d, 'configure_runtime', return_value=runtime), \
                patch.object(c, 'source_index', return_value=binding['source_index']), \
                patch.object(w5, 'read_json', side_effect=[binding, {}, fixture()]), \
                patch.object(v, 'validate_registry', side_effect=ValueError('bad receipt')) as check, \
                patch.object(d, 'validation_logits') as inference:
            with self.assertRaisesRegex(ValueError, 'bad receipt'):
                cli.reload_model(SimpleNamespace(run='synthetic_not_opened'))
            check.assert_called_once()
            inference.assert_not_called()

    def test_full_approved_validator_and_config_cap_binding(self):
        r = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in ('configs', 'contracts'):
                shutil.copytree(d.ROOT / folder, root / folder)
            config_path = root / r['runs'][6]['config_path']
            config = w5.read_json(config_path)
            config['runtime'].update(source_sha='a' * 40, runtime_lock='c' * 64)
            config['status'] = 'FROZEN'
            w5.atomic_json(config_path, config)
            a = r['r6_budget_amendment']
            a['config_sha256'] = r['runs'][6]['config_sha256'] = d.digest(config)
            binding = {k: a[k] for k in ('run_id', 'attempt_id', 'max_gpu_hours',
                'config_sha256', 'source_sha', 'runtime_sha256')}
            for role, ref in a['approvals'].items():
                w5.atomic_json(root / ref['path'], dict(role=role, decision='APPROVE_R6_3H', binding=binding))
                ref['sha256'] = w5.sha(root / ref['path'])
            self.assertEqual(v.validate_registry(r, root)['official_attempts'], 5)
            v.official_gate(r, r['runs'][6])
            r['runs'][6].update(status='FAILED', attempts=[dict(attempt_id='R6_attempt01', status='FAILED',
                gpu_hours=2.9, evidence_path='synthetic')])
            self.assertEqual(v.validate_registry(r, root)['official_attempts'], 6)
            r['runs'][6]['attempts'][0]['gpu_hours'] = 3.01
            with self.assertRaisesRegex(Exception, 'maximum|budget'):
                v.validate_registry(r, root)
            r['runs'][6]['attempts'][0]['gpu_hours'] = 2.9
            r['r6_budget_amendment']['status'] = 'PENDING'
            with self.assertRaisesRegex(Exception, 'maximum|pending'):
                v.validate_registry(r, root)
            r['r6_budget_amendment']['status'] = 'APPROVED'
            r['budgets']['per_attempt_gpu_hours'] = 3
            with self.assertRaisesRegex(ValueError, 'budget'):
                v.validate_registry(r, root)

    def test_proposal_retains_history_and_blocks_official(self):
        r = w5.read_json(d.ROOT / 'experiments/w6/tv3_R6_3h.proposal.json')
        result = v.validate_registry(r)
        self.assertEqual(result['official_attempts'], 5)
        self.assertAlmostEqual(result['measured_tv3_gpu_hours'], 4.060724169611111)
        self.assertEqual(r['runs'][5]['status'], 'FAILED')
        self.assertEqual(r['runs'][6]['attempts'], [])
        with self.assertRaises(ValueError):
            v.official_gate(r, r['runs'][6])

    def test_only_r6_config_accepts_three(self):
        original = w5.read_json(d.ROOT / 'configs/w6/tv3/R6.frozen.json')
        candidate = w5.read_json(d.ROOT / 'configs/w6/tv3/R6.3h.candidate.json')
        d.validate_config(candidate)
        expected = copy.deepcopy(original)
        expected.update(status='DRAFT', max_gpu_hours=3)
        expected.pop('smoke_evidence')
        expected['runtime'].update(source_sha=None, runtime_lock=None)
        self.assertEqual(candidate, expected)
        for n in range(1, 6):
            bad = w5.read_json(d.ROOT / f'configs/w6/tv3/R{n}.frozen.json')
            bad['max_gpu_hours'] = 3
            with self.assertRaises(ValueError):
                d.validate_config(bad)
        for cap in (0, 2.5, 4, float('nan')):
            bad = copy.deepcopy(candidate)
            bad['max_gpu_hours'] = cap
            with self.assertRaises(ValueError):
                d.validate_config(bad)

    def test_explicit_policy_required_for_three_hours(self):
        for reg in (None, {}, {'r6_budget_amendment': dict(fixture()['r6_budget_amendment'], status='PENDING')}):
            with self.assertRaises(ValueError):
                c.usage_totals(usage(8000), reg)
        self.assertEqual(c.usage_totals(usage(10800), fixture())[0], 10800)
        with self.assertRaises(ValueError):
            c.usage_totals(usage(10800.01), fixture())

    def test_other_runs_and_attempt_ids_cannot_borrow_exception(self):
        for run in ('R1', 'R2', 'R3', 'R4', 'R5'):
            with self.assertRaises(ValueError):
                c.usage_totals(usage(7201, run), fixture())
        with self.assertRaises(ValueError):
            c.usage_totals(usage(10, aid='R6_attempt02'), fixture())
        bad = usage(10)
        bad['sessions'].append(dict(bad['sessions'][0], run_id='R5'))
        with self.assertRaisesRegex(ValueError, 'mixed'):
            c.usage_totals(bad, fixture())

    def test_total_twelve_and_six_attempts_remain(self):
        ledger = usage(1000)
        for n in range(1, 7):
            ledger['sessions'].append(usage(10, run='R1', aid=f'synthetic_{n}')['sessions'][0])
        with self.assertRaises(ValueError):
            c.usage_totals(ledger, fixture())
        ledger = usage(10800)
        ledger['sessions'].append(usage(32401, aid='smoke', kind='train_only_smoke')['sessions'][0])
        with self.assertRaises(ValueError):
            c.usage_totals(ledger, fixture())

    def test_reload_shares_attempt_budget(self):
        ledger = usage(10000)
        ledger['sessions'].append(usage(801, kind='reload')['sessions'][0])
        with self.assertRaises(ValueError):
            c.usage_totals(ledger, fixture())
        ledger['sessions'][-1]['seconds'] = 799
        self.assertEqual(c.usage_totals(ledger, fixture())[1], {'R6_attempt01': 10799})

    def test_amendment_approval_and_binding_rejections(self):
        for key, value in [('source_sha', 'f' * 40), ('config_sha256', 'f' * 64),
                           ('runtime_sha256', None), ('max_gpu_hours', 4), ('run_id', 'R5')]:
            r = fixture()
            r['r6_budget_amendment'][key] = value
            with self.assertRaises(ValueError):
                v.r6_amendment(r)
        r = fixture()
        r['r6_budget_amendment']['approvals']['TV2'] = None
        with self.assertRaises(ValueError):
            v.official_gate(r, r['runs'][6])

    def test_evidence_content_and_hash_must_match(self):
        r = fixture()
        a = r['r6_budget_amendment']
        binding = {k: a[k] for k in ('run_id', 'attempt_id', 'max_gpu_hours',
                    'config_sha256', 'source_sha', 'runtime_sha256')}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for role, ref in a['approvals'].items():
                path = root / ref['path']
                w5.atomic_json(path, dict(role=role, decision='APPROVE_R6_3H', binding=binding))
                ref['sha256'] = w5.sha(path)
            v.verify_r6_amendment_evidence(r, root)
            path = root / 'TV2.json'
            w5.atomic_json(path, dict(role='TV2', decision='WRONG', binding=binding))
            with self.assertRaisesRegex(ValueError, 'hash'):
                v.verify_r6_amendment_evidence(r, root)
            a['approvals']['TV2']['sha256'] = w5.sha(path)
            with self.assertRaisesRegex(ValueError, 'content'):
                v.verify_r6_amendment_evidence(r, root)

    def test_unknown_and_duplicate_reconciliation_block(self):
        ledger = usage(None)
        with self.assertRaises(ValueError):
            c.usage_totals(ledger, fixture())
        ledger['reconciliations'] = [dict(session_id='synthetic', seconds=6405.3003492)]
        self.assertAlmostEqual(c.usage_totals(ledger, fixture())[0], 6405.3003492)
        ledger['reconciliations'] *= 2
        with self.assertRaises(ValueError):
            c.usage_totals(ledger, fixture())

    def test_session_stops_with_reserve_and_saves_actual_usage(self):
        now = [0.0]
        with tempfile.TemporaryDirectory() as tmp, patch.object(c.time, 'perf_counter', side_effect=lambda: now[0]):
            root = Path(tmp)
            with self.assertRaises(c.BudgetExceeded):
                with c.gpu_session('R6_attempt01', 'R6', 'official', 'synthetic CPU only',
                                   root=root, registry=fixture()) as (tick, _):
                    now[0] = 10740
                    tick()
            ledger = c.load_usage(root)
            self.assertEqual(ledger['sessions'][0]['status'], 'STOPPED')
            self.assertEqual(ledger['sessions'][0]['seconds'], 10740)

    def test_exclusive_writer_prevents_second_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with w5.writer_lock(root / 'outputs/tv3_w6/gpu_lock'):
                with self.assertRaises(Exception):
                    with c.gpu_session('R6_attempt01', 'R6', 'official', 'synthetic', root=root, registry=fixture()):
                        self.fail('Must never enter concurrent session')
            self.assertEqual(c.load_usage(root)['sessions'], [])

    def test_settlement_is_exactly_once_and_does_not_discard_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = usage(None, run='R5')
            ledger['sessions'][0]['heartbeat_seconds'] = 6400
            w5.atomic_json(root / 'outputs/tv3_w6/usage.json', ledger)
            receipt = dict(session_id='synthetic', status='REVIEWED', reviewers={'TV2': 'synthetic', 'TV3': 'synthetic'},
                evidence='synthetic', process_confirmed_stopped=True, elapsed_seconds=6405.3003492)
            path = root / 'receipt.json'
            w5.atomic_json(path, receipt)
            self.assertAlmostEqual(c.reconcile_usage(path, root=root)[0], 6405.3003492)
            settled = (root / 'outputs/tv3_w6/usage.json').read_bytes()
            with self.assertRaisesRegex(ValueError, 'settled'):
                c.reconcile_usage(path, root=root)
            self.assertEqual((root / 'outputs/tv3_w6/usage.json').read_bytes(), settled)


class WriterTests(unittest.TestCase):
    def test_transient_replace_retries_preserve_content(self):
        real_replace = w5.os.replace
        count = [0]
        def replace(src, dst):
            count[0] += 1
            if count[0] < 3:
                raise denied()
            return real_replace(src, dst)
        with tempfile.TemporaryDirectory() as tmp, patch.object(c.time, 'sleep') as sleep:
            path = Path(tmp) / 'usage.json'
            w5.atomic_json(path, {'old': True})
            with patch.object(w5.os, 'replace', side_effect=replace):
                c.write_usage(path, {'new': True})
            self.assertEqual(w5.read_json(path), {'new': True})
            self.assertEqual(count[0], 3)
            self.assertEqual(sleep.call_count, 2)

    def test_permanent_replace_error_retains_old_and_tmp(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(c.time, 'sleep') as sleep:
            path = Path(tmp) / 'usage.json'
            w5.atomic_json(path, {'old': True})
            before = path.read_bytes()
            with patch.object(w5.os, 'replace', side_effect=denied()) as replace:
                with self.assertRaises(PermissionError):
                    c.write_usage(path, {'new': True})
            self.assertEqual(replace.call_count, 6)
            self.assertEqual(sleep.call_count, 5)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(w5.read_json(path.with_suffix('.json.tmp')), {'new': True})

    def test_other_errors_not_retried(self):
        for exc in (PermissionError('ordinary permission failure'), OSError('disk full')):
            with patch.object(w5, 'atomic_json', side_effect=exc) as writer, patch.object(c.time, 'sleep') as sleep:
                with self.assertRaises(OSError):
                    c.write_usage(Path('unused'), {})
                self.assertEqual(writer.call_count, 1)
                sleep.assert_not_called()

    def test_final_retry_time_is_accounted(self):
        now = [0.0]
        real_write = w5.atomic_json
        failed_once = [False]
        def writer(path, value):
            if value['sessions'][0]['seconds'] is not None and not failed_once[0]:
                failed_once[0] = True
                raise denied()
            real_write(path, value)
        def sleep(delay):
            now[0] += delay
        with tempfile.TemporaryDirectory() as tmp, patch.object(c.time, 'perf_counter', side_effect=lambda: now[0]), \
                patch.object(c.time, 'sleep', side_effect=sleep), patch.object(w5, 'atomic_json', side_effect=writer):
            with c.gpu_session('R6_attempt01', 'R6', 'official', 'synthetic CPU', root=Path(tmp), registry=fixture()):
                now[0] = 10
            self.assertAlmostEqual(c.load_usage(Path(tmp))['sessions'][0]['seconds'], 10.05)


if __name__ == '__main__':
    unittest.main()
