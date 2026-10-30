"""Scientific invariants and recovery checks; no download or real training."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import torch
from PIL import Image
from src.training import dino_probe as d
from src.training import dino_handoff as h


class FakeBackbone(torch.nn.Module):
    def forward_features(self, x):
        return {'x_norm_clstoken': x.mean((1, 2, 3)).unsqueeze(1).repeat(1, 384)}


class DinoTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        self.config = d.read_json(d.ROOT / 'configs/dinov3_lp_w5.json')

    def test_preprocessing_specific_to_backbone(self):
        im = Image.new('RGB', (310, 180), (80, 90, 120))
        self.assertEqual(tuple(d.transform_for('dinov3_vits16')(im).shape), (3, 256, 256))
        self.assertEqual(tuple(d.transform_for('dinov2_vits14')(im).shape), (3, 224, 224))
        c = copy.deepcopy(self.config)
        c['model']['name'] = 'dinov2_vits14'
        with self.assertRaisesRegex(ValueError, 'Preprocessing'):
            d.validate_config(c, pinned=False)

    def test_requires_release_and_real_weight_pins(self):
        with self.assertRaisesRegex(ValueError, 'pretrained SHA'):
            d.validate_config(self.config)
        c = copy.deepcopy(self.config)
        c['data']['directory'] = 'data/processed/w5_candidates_v1'
        with self.assertRaisesRegex(ValueError, 'released'):
            d.validate_config(c, pinned=False)

    def test_frozen_metadata_and_parent_coverage(self):
        rows, cmap, gate = d.read_release(verify_images=False)
        self.assertEqual((len(rows['train']), len(rows['val'])), (3125, 680))
        self.assertEqual((len(d.groups_for(rows['train'])), len(d.groups_for(rows['val']))), (2800, 600))
        self.assertEqual(len(cmap), 8)
        self.assertFalse(gate['test_opened'])
        self.assertEqual(gate['verified_source_images'], 0)

    def test_image_loss_uses_weight_once(self):
        logits = torch.tensor([[3., 0.], [0., 3.], [0., 3.]], requires_grad=True)
        labels = torch.tensor([0, 1, 1])
        loss = d.image_balanced_loss(logits, labels, [[0], [1, 2]])
        reference = (torch.nn.functional.cross_entropy(logits[:1], labels[:1]) +
                     torch.nn.functional.cross_entropy(logits[1:], labels[1:])) / 2
        self.assertTrue(torch.equal(loss, reference))
        loss.backward()
        self.assertTrue(torch.allclose(logits.grad[1], logits.grad[2]))
        self.assertTrue(torch.allclose(logits.grad[0].abs(), 2 * logits.grad[1].abs()))

    def test_mean_probability_not_mean_logits(self):
        # Mean logits chooses class 0, mean softmax chooses class 1.
        logits = torch.tensor([[10., 0.], [0., 2.], [0., 2.]])
        rows = [dict(crop_id=str(i), image_id='same', class_id=1) for i in range(3)]
        result = d.evaluate_logits(logits, rows, {'0': 'a', '1': 'b'})
        self.assertEqual(int(logits.mean(0).argmax()), 0)
        self.assertEqual(result['image_predictions'][0]['y_pred'], 1)
        self.assertEqual(result['metrics']['images'], 1)
        self.assertEqual(result['metrics']['accuracy'], 1.)
        rows[1]['class_id'] = 0
        with self.assertRaisesRegex(ValueError, 'labels'):
            d.evaluate_logits(logits, rows, {'0': 'a', '1': 'b'})

    def test_receipt_must_bind_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'protocol.json'
            d.atomic_json(p, {'status': 'PROPOSED'})
            with self.assertRaisesRegex(ValueError, 'agreement'):
                d.check_protocol(self.config, p)
            receipt = h.protocol_draft(self.config)
            receipt.update(status='APPROVED', reviewers={'TV2': 'fixture', 'TV3': 'fixture'},
                           seeds=[42], max_candidate_runs=1, experiments=[self.config['experiment_id']],
                           approval_evidence='synthetic unit fixture only', budget_reference='fixture')
            d.atomic_json(p, receipt)
            d.check_protocol(self.config, p)
            self.config['training']['lr'] *= 2
            with self.assertRaisesRegex(ValueError, 'bind'):
                d.check_protocol(self.config, p)

    def test_cache_resume_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'image.png'
            Image.new('RGB', (16, 16), (50, 100, 150)).save(source)
            c = copy.deepcopy(self.config)
            c['runtime']['device'] = 'cpu'
            rows = {s: [dict(crop_id=s, image_id=s, class_id=0, bbox_xyxy=[0, 0, 16, 16],
                             quality={'local_path': 'image.png', 'sha256': d.sha(source)})] for s in ('train', 'val')}
            with patch.object(d, 'load_backbone', return_value=FakeBackbone()):
                folder, index = d.cache_features(c, rows, {}, {}, root)
            with patch.object(d, 'load_backbone', side_effect=AssertionError('must reuse completed shards')):
                d.cache_features(c, rows, {}, {}, root)
            self.assertEqual(d.load_features(folder, index, rows)['train'].shape, (1, 384))
            c2 = copy.deepcopy(c)
            c2['model']['weights_sha256'] = 'new'
            self.assertNotEqual(d.digest(d.cache_identity(c, {}, {})), d.digest(d.cache_identity(c2, {}, {})))
            (folder / 'train_000000.pt').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'Corrupt'):
                d.cache_features(c, rows, {}, {}, root)

    def test_epoch_resume_matches_uninterrupted(self):
        c = copy.deepcopy(self.config)
        c['runtime']['device'] = 'cpu'
        c['training'].update(epochs=4, patience=10, images_per_batch=2)
        generator = torch.Generator().manual_seed(8)
        features = {s: torch.randn(6, 384, generator=generator) for s in ('train', 'val')}
        rows = {s: [dict(crop_id=str(i), image_id=str(i // 2), class_id=i // 2 % 2) for i in range(6)] for s in ('train', 'val')}
        with tempfile.TemporaryDirectory() as tmp:
            full, resumed = Path(tmp) / 'full', Path(tmp) / 'resume'
            full.mkdir()
            resumed.mkdir()
            d.seed_all(42)
            expected = d.train_head(c, features, rows, {'0': 'a', '1': 'b'}, full, {'fixture': True})
            original = d.atomic_json
            def interrupt_after_epoch(path, value):
                original(path, value)
                if len(value) == 2:
                    raise KeyboardInterrupt()
            d.seed_all(42)
            with patch.object(d, 'atomic_json', side_effect=interrupt_after_epoch):
                with self.assertRaises(KeyboardInterrupt):
                    d.train_head(c, features, rows, {'0': 'a', '1': 'b'}, resumed, {'fixture': True})
            d.seed_all(42)
            actual = d.train_head(c, features, rows, {'0': 'a', '1': 'b'}, resumed, {'fixture': True}, True)
            self.assertEqual(expected[1:3], actual[1:3])
            for k in expected[0]:
                self.assertTrue(torch.equal(expected[0][k], actual[0][k]))
            with self.assertRaisesRegex(ValueError, 'changed'):
                d.train_head(c, features, rows, {'0': 'a', '1': 'b'}, resumed, {'fixture': False}, True)

    def test_reload_detects_tiny_unrounded_difference(self):
        rows = [dict(crop_id='c', image_id='i', class_id=0)]
        a = d.evaluate_logits(torch.tensor([[1., 0.]]), rows, {'0': 'a', '1': 'b'})
        b = copy.deepcopy(a)
        b['crop_predictions'][0]['logits'][0] += 1e-8
        self.assertFalse(d.compare_predictions(a, b)['passed'])
        self.assertTrue(d.compare_predictions(a, a)['passed'])

    def test_cli_exports_package_and_refuses_existing_run(self):
        from scripts import dino_w5 as cli
        c = copy.deepcopy(self.config)
        c['runtime']['device'] = 'cpu'
        c['training'].update(epochs=1, patience=2)
        rows = {s: [dict(crop_id=str(i), image_id=str(i), class_id=i) for i in range(8)] for s in ('train', 'val')}
        cmap = {str(i): 'class_' + str(i) for i in range(8)}
        features = {s: torch.randn(8, 384) for s in rows}
        _, _, gate = d.read_release(verify_images=False)
        args = SimpleNamespace(resume=False)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / 'cache'
            cache.mkdir()
            d.atomic_json(cache / 'index.json', {'fixture': True})
            def fake_reload(command, check):
                path = Path(command[command.index('--output') + 1])
                checkpoint = Path(command[command.index('--checkpoint') + 1])
                d.atomic_json(path, dict(passed=True, status='PASS', fixture_only=True, fresh_process=True,
                                        checkpoint_sha256=d.sha(checkpoint), evaluation_split='val',
                                        manifest_sha256=h.manifest_hashes(gate), test_inference_performed=False))
                return SimpleNamespace(returncode=0)
            with patch.object(cli, 'ROOT', root), \
                 patch.object(cli, 'preparation', return_value=(c, {}, {}, rows, cmap, gate)), \
                 patch.object(d, 'git_revision', return_value='fixture'), \
                 patch.object(d, 'cache_features', return_value=(cache, {'key': 'fixture', 'shards': {}})), \
                 patch.object(d, 'load_features', return_value=features), \
                 patch.object(d, 'load_backbone', return_value=FakeBackbone()), \
                 patch.object(cli, 'comparison', return_value={'baseline': dict(experiment_id='b2', accuracy=0.5, macro_f1=0.5),
                                                               'candidate': dict(experiment_id='fixture', accuracy=0.5, macro_f1=0.5),
                                                               'claim': 'fixture only'}), \
                 patch.object(cli.subprocess, 'run', side_effect=fake_reload):
                cli.train(args)
                run = root / 'outputs/tv3_w5/runs' / c['experiment_id']
                self.assertEqual(d.read_json(run / 'status.json')['status'], 'COMPLETE')
                payload = torch.load(run / 'best_model.pt', weights_only=True)
                self.assertEqual(payload['format'], 'TV3_DINO_LINEAR_V1')
                self.assertEqual(len(payload['validation']['crop_predictions']), 8)
                for name in ['last_model.pt', 'handoff.json', 'MODEL_CARD.md', 'confusion_matrix.csv', 'confusion_matrix.png']:
                    self.assertTrue((run / name).is_file(), name)
                with self.assertRaises(FileExistsError):
                    cli.train(args)
                args.resume = True
                with self.assertRaisesRegex(ValueError, 'immutable'):
                    cli.train(args)

    def test_reload_report_exports_real_comparison_status(self):
        from scripts import dino_w5 as cli
        rows, cmap, gate = d.read_release(verify_images=False)
        rows = {'val': rows['val'][:8]}
        head = torch.nn.Linear(384, 8).eval()
        features = torch.ones(8, 384)
        with torch.inference_mode():
            result = d.evaluate_logits(head(features), rows['val'], cmap)
        payload = dict(class_map=cmap, binding={'data': gate}, config=self.config, validation=result)
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = Path(tmp) / 'synthetic.pt'
            checkpoint.write_bytes(b'synthetic fixture only')
            args = SimpleNamespace(checkpoint=checkpoint, sha256=d.sha(checkpoint), device='cpu', repo=None,
                                   output=Path(tmp) / 'reload_pass.json')
            with patch.object(d, 'load_package', return_value=(FakeBackbone(), head, None, payload)), \
                 patch.object(d, 'read_release', return_value=(rows, cmap, gate)), \
                 patch.object(d, 'crop_tensor', return_value=torch.ones(3, 16, 16)), \
                 patch('builtins.print'):
                cli.reload_model(args)
                report = d.read_json(args.output)
                self.assertEqual(report['status'], 'PASS')
                self.assertEqual(report['manifest_sha256'], h.manifest_hashes(gate))
                self.assertEqual(report['evaluation_split'], 'val')
                self.assertFalse(report['test_inference_performed'])
                self.assertEqual(report['validation_crops'], 8)
                # Preserve failure evidence; an incorrect reference must not earn PASS.
                payload['validation']['crop_predictions'][0]['logits'][0] += 1e-8
                args.output = Path(tmp) / 'reload_fail.json'
                with self.assertRaisesRegex(ValueError, 'differs'):
                    cli.reload_model(args)
                self.assertEqual(d.read_json(args.output)['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
