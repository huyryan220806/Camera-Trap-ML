"""Compatibility with original TV2 code. All candidate artifacts are synthetic.

No DINO weights/inference/training and no genuine approval are produced here.
The optional cross-branch tests need `git fetch origin` to obtain 3f76643.
"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import torch
from scripts import audit_dino_tv2 as bridge
from src.training import dino_probe as d
from src.training import dino_handoff as h


def fixture_receipt(c):
    receipt = h.protocol_draft(c)
    receipt.update(status='APPROVED', reviewers={'TV2': 'SYNTHETIC', 'TV3': 'SYNTHETIC'},
                   approval_evidence='Synthetic software test, not real approval', budget_reference='fixture only',
                   seeds=[42], experiments=[c['experiment_id']], max_candidate_runs=1)
    return receipt


class ProtocolTests(unittest.TestCase):
    def test_registration_and_policy_fail_closed(self):
        c = d.read_json(d.ROOT / 'configs/dinov3_lp_w5.json')
        receipt = fixture_receipt(c)
        h.validate_protocol(c, receipt)
        for key, invalid in [('status', 'DRAFT'), ('seeds', []), ('experiments', []),
                             ('max_candidate_runs', 0), ('prediction_tie_rule', 'highest_class_id'),
                             ('checkpoint_tie_rule', 'higher_accuracy'), ('config_sha256', 'wrong'),
                             ('approval_evidence', None), ('budget_reference', None),
                             ('reviewers', {'TV3': 'fixture'}), ('evaluation_split', 'test')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                h.validate_protocol(c, dict(receipt, **{key: invalid}))
        self.assertEqual(h.protocol_draft(c)['status'], 'DRAFT')
        self.assertEqual(h.protocol_draft(c)['experiments'], [])


class TV2CompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        available = subprocess.run(['git', '-C', str(d.ROOT), 'cat-file', '-e', bridge.TV2_COMMIT], capture_output=True)
        if available.returncode:
            raise unittest.SkipTest('Fetch TV2 commit 3f76643 to run cross-branch compatibility tests')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.snapshot = bridge.prepare_reference(Path(cls.tmp.name) / 'tv2')
        spec = importlib.util.spec_from_file_location('tv2_reference', cls.snapshot / 'src/evaluation/w5_validation.py')
        cls.tv2 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tv2)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.c = d.read_json(d.ROOT / 'configs/dinov3_lp_w5.json')
        self.c['model'].update(repo_commit='1' * 40, weights_sha256='2' * 64)
        rows, cmap, gate = d.read_release(verify_images=False)
        self.parents, self.crops, self.hashes = self.tv2.load_frozen_validation(self.snapshot)
        self.assertEqual(self.hashes, h.manifest_hashes(gate))
        # Full frozen population but synthetic scores, including exact class ties.
        generator = torch.Generator().manual_seed(42)
        logits = torch.randn(len(rows['val']), 8, generator=generator)
        logits[:8] = 0
        self.result = d.evaluate_logits(logits, rows['val'], cmap)
        self.checkpoint = self.run / 'best_model.pt'
        self.checkpoint.write_bytes(b'SYNTHETIC CHECKPOINT; no model; artifact auditor does not load weights')
        self.binding = dict(data=gate, class_map=cmap, runtime={'fixture_only': True}, code_commit='3' * 40)
        for name, value in [('config.json', self.c), ('binding.json', self.binding),
                            ('train_log.json', [{'fixture_only': True}])]:
            d.atomic_json(self.run / name, value)
        self.handoff = h.build_handoff(self.run, self.checkpoint, self.c, self.binding, self.result)
        d.atomic_json(self.run / 'handoff.json', self.handoff)
        self.report_path = self.run / 'reload.json'
        self.report = dict(status='PASS', passed=True, fresh_process=True, fixture_only=True,
                           checkpoint_sha256=d.sha(self.checkpoint), evaluation_split='val',
                           manifest_sha256=self.hashes, test_inference_performed=False)
        d.atomic_json(self.report_path, self.report)
        self.assertTrue(h.finish_handoff(self.run, self.report_path, True))
        self.handoff = d.read_json(self.run / 'handoff.json')
        self.receipt = fixture_receipt(self.c)

    def test_real_tv2_cli_accepts_synthetic_bundle_and_compares_published_b2(self):
        protocol = self.run / 'protocol.json'
        d.atomic_json(protocol, self.receipt)
        out = self.snapshot / 'outputs' / self.run.name
        completed = subprocess.run(bridge.audit_command(self.snapshot, self.run, protocol, out),
                                   capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        audit = d.read_json(out / 'audit.json')
        self.assertEqual(audit['status'], 'ARTIFACT_VERIFIED')
        self.assertFalse(audit['model_loaded'])
        self.assertEqual((audit['images'], audit['crops']), (600, 680))
        self.assertEqual(sum(map(len, audit['paired_outcomes'].values())), 600)
        for key in h.METRICS:
            self.assertAlmostEqual(audit['metrics'][key], self.result['metrics'][key], places=12)
        images = self.tv2.read_jsonl(out / 'predictions.jsonl')
        by_id = {p['image_id']: p for p in images}
        for p in self.result['image_predictions']:
            self.assertEqual(by_id[p['image_id']]['predicted_class'], p['y_pred'])
        # Test exact schemas as well as the independent evaluator.
        import jsonschema
        for name, schema in [('val_crops.jsonl', 'w5_crop_prediction.schema.json'),
                             ('val_images.jsonl', 'w5_image_prediction.schema.json')]:
            validator = jsonschema.Draft202012Validator(d.read_json(self.snapshot / 'contracts' / schema))
            for row in self.tv2.read_jsonl(self.run / name):
                validator.validate(row)

    def test_tv2_rejects_draft_tampered_artifact_or_wrong_manifest(self):
        self.tv2.verify_handoff(self.handoff, self.checkpoint, self.hashes, self.receipt, self.run)
        with self.assertRaisesRegex(ValueError, 'approval'):
            self.tv2.verify_handoff(self.handoff, self.checkpoint, self.hashes, h.protocol_draft(self.c), self.run)
        wrong = copy.deepcopy(self.handoff)
        wrong['manifest_sha256']['val.jsonl'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'manifest'):
            self.tv2.verify_handoff(wrong, self.checkpoint, self.hashes, self.receipt, self.run)
        (self.run / 'train_log.json').write_text('[]', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Artifact'):
            self.tv2.verify_handoff(self.handoff, self.checkpoint, self.hashes, self.receipt, self.run)

    def test_no_pass_for_missing_wrong_or_failed_reload(self):
        for changes, process_ok in [({'checkpoint_sha256': '0' * 64}, True),
                                    ({'status': 'FAIL', 'passed': False}, True),
                                    ({'fresh_process': False}, True), ({}, False)]:
            with self.subTest(changes=changes, process_ok=process_ok):
                d.atomic_json(self.report_path, dict(self.report, **changes))
                self.assertFalse(h.finish_handoff(self.run, self.report_path, process_ok))
                self.assertEqual(d.read_json(self.run / 'handoff.json')['fresh_process_reload']['status'], 'FAIL')
        self.assertFalse(h.finish_handoff(self.run, self.run / 'missing.json', False))

    def test_tv2_rejects_missing_crop_and_export_uses_original_softmax(self):
        crops = self.tv2.read_jsonl(self.run / 'val_crops.jsonl')
        self.assertEqual(crops[0]['class_scores'], self.result['crop_predictions'][0]['probabilities'])
        with self.assertRaisesRegex(ValueError, 'Missing/extra crop'):
            self.tv2.aggregate(crops[:-1], self.parents, self.crops, self.c['experiment_id'], d.sha(self.checkpoint))


if __name__ == '__main__':
    unittest.main()
