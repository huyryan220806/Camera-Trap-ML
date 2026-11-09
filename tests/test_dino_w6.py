"""W6 invariants using synthetic CPU fixtures. No real training, GPU or Test data.

Run after merging TV2 W6: python -m unittest discover -s tests -p test_dino_w6.py -v
"""
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import torch
from torch import nn
from src.training import dino_probe as old
from src.training import dino_w6 as d
from src.training import dino_w6_control as control


class TinyBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.norm = nn.LayerNorm(384)
        self.linear = nn.Linear(384, 384)
        self.gamma = nn.Parameter(torch.ones(384))

    def forward(self, x):
        return x + self.linear(self.norm(x)) * self.gamma


class TinyBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.patch_embed = nn.Linear(3, 384)
        self.blocks = nn.ModuleList([TinyBlock() for _ in range(4)])
        self.norm = nn.LayerNorm(384)

    def forward_features(self, x):
        x = self.patch_embed(x.mean((-2, -1)))
        for block in self.blocks:
            x = block(x)
        x = self.norm(x)
        return dict(x_norm_clstoken=x, x_norm_patchtokens=torch.stack((x + 1, x + 3), dim=1),
                    x_storage_tokens=torch.full((len(x), 4, 384), 1e9, device=x.device))


def config(recipe='R1'):
    return old.read_json(d.ROOT / f'configs/w6/tv3/{recipe}.candidate.json')


def tensor_rows(n=7):
    return [dict(crop_id=f'c{i}', image_id=f'i{i // 2}', class_id=i // 2 % 8,
                 tensor=torch.tensor([i + .5, 1., 2.]).view(3, 1, 1).expand(3, 4, 4).clone()) for i in range(n)]


def fake_crops(rows, indices, c, root, training):
    xs = []
    for i in indices:
        x = rows[i]['tensor']
        if training and random.random() < c['augmentation']['horizontal_flip']:
            x = x * .9  # Synthetic stochastic augmentation makes RNG resume observable.
        xs.append(x)
    return torch.stack(xs)


class W6Tests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(1)
        old.seed_all(42)

    def test_candidate_configs_match_tv2_contract_and_no_approval(self):
        v = control.tv2()
        for recipe in ('R1', 'R2'):
            c = config(recipe)
            d.validate_config(c)
            v.validate_recipe_config(c, recipe)
            self.assertEqual(c['status'], 'DRAFT')
            self.assertIsNone(c['runtime']['source_sha'])
            self.assertIsNone(c['runtime']['runtime_lock'])
            self.assertEqual(d.digest(c), v.digest(c))
        with self.assertRaisesRegex(ValueError, 'DRAFT'):
            v.official_gate({'protocol_status': 'DRAFT'}, {})

    def test_config_rejects_unsupported_seed_data_precision_or_recipe(self):
        for key, value in [('seed', 123), ('dataset_sha256', '0' * 64), ('parent_batch', 64), ('feature_dim', 384)]:
            c = config()
            c[key] = value
            with self.assertRaises(ValueError):
                d.validate_config(c)
        c = config('R2')
        c['runtime']['amp'] = True
        with self.assertRaisesRegex(ValueError, 'Runtime'):
            d.validate_config(c)

    def test_cls_patch_concatenation_excludes_storage_tokens(self):
        c = config()
        model = d.Classifier(TinyBackbone(), c)
        x = torch.randn(2, 3, 4, 4)
        features = model.features(x)
        out = model.backbone.forward_features(x)
        self.assertEqual(tuple(features.shape), (2, 768))
        self.assertTrue(torch.equal(features[:, :384], out['x_norm_clstoken']))
        self.assertTrue(torch.equal(features[:, 384:], out['x_norm_patchtokens'].mean(1)))
        self.assertLess(float(features.abs().max()), 100)
        self.assertEqual(tuple(model(x).shape), (2, 8))

    def test_trainable_mask_and_modes(self):
        for recipe in ('R1', 'R2'):
            model = d.Classifier(TinyBackbone(), config(recipe)).train()
            for name, p in model.named_parameters():
                expected = name.startswith('head.') or recipe == 'R2' and name.startswith(
                    ('backbone.blocks.2.', 'backbone.blocks.3.', 'backbone.norm.'))
                self.assertEqual(p.requires_grad, expected, name)
            self.assertFalse(model.backbone.training)
            self.assertFalse(model.backbone.blocks[0].training)
            self.assertEqual(model.backbone.blocks[-1].training, recipe == 'R2')
            self.assertTrue(model.head.training)
            model.eval()
            self.assertFalse(any(m.training for m in model.modules()))

    def test_adamw_bias_norm_exemption_but_layerscale_decays(self):
        model = d.Classifier(TinyBackbone(), config('R2'))
        opt = d.optimizer_for(model, config('R2'))
        groups = {id(p): g for g in opt.param_groups for p in g['params']}
        self.assertEqual(sum(len(g['params']) for g in opt.param_groups), sum(p.requires_grad for p in model.parameters()))
        for name, p in model.named_parameters():
            if not p.requires_grad:
                self.assertNotIn(id(p), groups)
                continue
            self.assertEqual(groups[id(p)]['lr'], 1e-4 if name.startswith('head.') else 1e-5)
            expected = 0 if '.norm.' in name or name.endswith('.bias') else .01
            self.assertEqual(groups[id(p)]['weight_decay'], expected, name)

    def test_accumulated_gradient_equals_parent_mean_with_partial_batch(self):
        c = config('R2')
        c['crop_microbatch'] = 2
        c['augmentation']['horizontal_flip'] = 0
        model = d.Classifier(TinyBackbone(), c).train()
        reference = copy.deepcopy(model)
        rows = tensor_rows(6)
        # Parent 0 has 5 crops, parent 1 has 1. Final batch is 2, not configured 16.
        for i, r in enumerate(rows):
            r['image_id'], r['class_id'] = ('a', 0) if i < 5 else ('b', 1)
        groups = [[0, 1, 2, 3, 4], [5]]
        frozen = {n: p.detach().clone() for n, p in model.named_parameters() if not p.requires_grad}
        with patch.object(d, 'crop_batch', side_effect=fake_crops):
            loss = d.backward_parent_batch(model, rows, groups, c, 'cpu')
        logits = reference(torch.stack([r['tensor'] for r in rows]))
        expected = old.image_balanced_loss(logits, torch.tensor([r['class_id'] for r in rows]), groups)
        expected.backward()
        self.assertAlmostEqual(loss, float(expected), places=6)
        for (name, p), (_, q) in zip(model.named_parameters(), reference.named_parameters()):
            if p.requires_grad:
                self.assertTrue(torch.allclose(p.grad, q.grad, atol=2e-6, rtol=2e-5), name)
            else:
                self.assertIsNone(p.grad)
        d.optimizer_for(model, c).step()
        for name, before in frozen.items():
            self.assertTrue(torch.equal(before, dict(model.named_parameters())[name]), name)

    def test_warmup_endpoints_and_scheduler_resume(self):
        c = config('R2')
        self.assertEqual(d.schedule_factor(0, c), .5)
        self.assertEqual(d.schedule_factor(1, c), 1.)
        self.assertEqual(d.schedule_factor(19, c), 0.)
        self.assertLess(d.schedule_factor(2, c), 1.)
        c = config('R1')
        self.assertEqual(d.schedule_factor(0, c), 1.)
        self.assertEqual(d.schedule_factor(50, c), 0.)

    def test_cache_identity_tracks_pooling_source_runtime_crop_pixels(self):
        c, rows = config(), {'train': [{'crop_id': 'a', 'quality': {'sha256': 'a'}}]}
        before = d.digest(d.cache_identity(c, rows, {}, {}, {}))
        for changed in ('pooling', 'feature_dim', 'init_checkpoint_sha256', 'pretrained_sha256'):
            other = copy.deepcopy(c)
            other[changed] = str(other[changed]) + 'changed'
            self.assertNotEqual(before, d.digest(d.cache_identity(other, rows, {}, {}, {})))
        self.assertNotEqual(before, d.digest(d.cache_identity(c, rows, {}, {'torch': 'other'}, {})))
        self.assertNotEqual(before, d.digest(d.cache_identity(c, rows, {}, {}, {'code': 'other'})))
        rows['train'][0]['quality']['sha256'] = 'other'
        self.assertNotEqual(before, d.digest(d.cache_identity(c, rows, {}, {}, {})))

    def test_cache_reuses_valid_shards_and_rejects_corruption(self):
        c = config()
        c['runtime']['device'] = 'cpu'
        rows = {'train': tensor_rows(), 'val': tensor_rows(4)}
        # Cache identity accepts JSON metadata, not tensor fixture values.
        values = {id(r): r.pop('tensor') for split in rows.values() for r in split}
        def crops(rs, ids, *args):
            return torch.stack([values[id(rs[i])] for i in ids])
        model = d.Classifier(TinyBackbone(), c)
        with tempfile.TemporaryDirectory() as tmp, patch.object(d, 'crop_batch', side_effect=crops):
            root = Path(tmp)
            features, ref = d.cache_features(model, c, rows, {}, {}, {}, root)
            self.assertEqual(tuple(features['train'].shape), (7, 768))
            with patch.object(model, 'features', side_effect=AssertionError('must reuse')):
                again, _ = d.cache_features(model, c, rows, {}, {}, {}, root)
            self.assertTrue(torch.equal(features['train'], again['train']))
            path = root / 'outputs/tv3_w6/features' / ref['key'] / 'train_000000.pt'
            path.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'Corrupt'):
                d.cache_features(model, c, rows, {}, {}, {}, root)
        with self.assertRaisesRegex(ValueError, 'cannot use'):
            d.cache_features(model, config('R2'), {}, {}, {}, {})

    def test_dataset_sha_change_and_unreviewed_expansion_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'data/processed/comparison_v1/provenance.json'
            path.parent.mkdir(parents=True)
            path.write_text('{}', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'provenance'):
                d.read_data(config(), root=root)
        c = config()
        c.update(dataset='train_expansion_w6_v1', dataset_sha256=d.EXPANSION_SHA, run_id='R5')
        with patch.object(old, 'read_release', return_value=({}, {}, {})):
            with self.assertRaisesRegex(ValueError, 'BLOCKED'):
                d.read_data(c, registry={'data_review': {'status': 'PENDING'}})

    def test_epoch_resume_restores_rng_optimizer_patience_and_weights(self):
        from scripts.dino_w6 import state_equal
        for recipe in ('R1', 'R2'):
            c = config(recipe)
            c['runtime']['device'] = 'cpu'
            c.update(epochs=4, patience=3, parent_batch=2, crop_microbatch=2)
            rows = {'train': tensor_rows(7), 'val': tensor_rows(8)}
            cmap = {str(i): 'class' + str(i) for i in range(8)}
            initial = d.Classifier(TinyBackbone(), c)
            features = ({s: torch.randn(len(rs), c['feature_dim']) for s, rs in rows.items()}
                        if recipe == 'R1' else None)
            with tempfile.TemporaryDirectory() as tmp, patch.object(d, 'crop_batch', side_effect=fake_crops):
                root = Path(tmp)
                full, interrupted = root / 'full', root / 'interrupted'
                full.mkdir()
                interrupted.mkdir()
                state_a, result_a = d.train_epochs(copy.deepcopy(initial), c, rows, cmap, full, {}, features)
                def stop(state):
                    if state['epoch'] == 2:
                        raise KeyboardInterrupt()
                with self.assertRaises(KeyboardInterrupt):
                    d.train_epochs(copy.deepcopy(initial), c, rows, cmap, interrupted, {}, features, epoch_callback=stop)
                state_b, result_b = d.train_epochs(copy.deepcopy(initial), c, rows, cmap, interrupted, {}, features, resume=True)
                self.assertEqual(result_a, result_b)
                for name in ('epoch', 'best_epoch', 'best_score', 'bad_epochs', 'best_state', 'model', 'optimizer', 'scheduler', 'rng', 'sampler'):
                    self.assertTrue(state_equal(state_a[name], state_b[name]), name)
                with self.assertRaisesRegex(ValueError, 'binding'):
                    d.train_epochs(copy.deepcopy(initial), c, rows, cmap, interrupted, {'changed': True}, features, resume=True)

    def test_last_checkpoint_does_not_reset_early_stop(self):
        c = config()
        c['runtime']['device'] = 'cpu'
        c.update(epochs=10, patience=1, parent_batch=2)
        rows = {'train': tensor_rows(3), 'val': tensor_rows(3)}
        features = {s: torch.randn(3, 768) for s in rows}
        cmap = {str(i): 'c' + str(i) for i in range(8)}
        fake = dict(metrics={'macro_f1': .5})
        with tempfile.TemporaryDirectory() as tmp, patch.object(old, 'evaluate_logits', return_value=fake):
            folder = Path(tmp)
            model = d.Classifier(TinyBackbone(), c)
            state, _ = d.train_epochs(model, c, rows, cmap, folder, {}, features)
            self.assertEqual((state['epoch'], state['best_epoch'], state['bad_epochs']), (2, 1, 1))
            with patch.object(d, 'backward_parent_batch', side_effect=AssertionError('must not train')):
                resumed, _ = d.train_epochs(model, c, rows, cmap, folder, {}, features, resume=True)
            self.assertEqual(resumed['epoch'], 2)

    def test_full_w6_checkpoint_load_and_per_box_logits(self):
        c = config('R2')
        c['status'] = 'FROZEN'
        model = d.Classifier(TinyBackbone(), c).eval()
        payload = dict(format=d.FORMAT, config=c, model=d.cpu_state(model), binding={'config_sha256': d.digest(c)})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'best.pt'
            old.atomic_torch(path, payload)
            with patch.object(old, 'load_backbone', return_value=TinyBackbone()):
                loaded, _, _ = d.load_package(path, old.sha(path), tmp)
            x = torch.randn(2, 3, 4, 4)
            self.assertTrue(torch.equal(model(x), loaded(x)))
            with self.assertRaisesRegex(ValueError, 'SHA'):
                d.load_package(path, '0' * 64, tmp)

    def test_budget_failure_count_unknown_usage_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(RuntimeError):
                with control.gpu_session('R1_attempt01', 'R1', 'official', 'synthetic CPU fixture', root=root):
                    raise RuntimeError('simulated interruption')
            usage = control.load_usage(root)
            self.assertEqual(usage['sessions'][0]['status'], 'FAILED')
            self.assertEqual(len(control.usage_totals(usage)[1]), 1)
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                with control.gpu_session('R1_attempt01', 'R1', 'official', 'fixture', root=root):
                    pass
            with control.gpu_session('R1_attempt01', 'R1', 'official', 'fixture', resume=True, root=root):
                pass
            self.assertEqual(len(control.usage_totals(control.load_usage(root))[1]), 1)
            usage['sessions'][0]['seconds'] = None
            with self.assertRaisesRegex(ValueError, 'Unmeasured'):
                control.usage_totals(usage)
            usage['sessions'][0]['seconds'] = 7201
            with self.assertRaisesRegex(ValueError, 'budget'):
                control.usage_totals(usage)

    def test_exact_reload_rejects_tiny_vector_change(self):
        rows = [dict(crop_id='x', image_id='x', class_id=0)]
        result = old.evaluate_logits(torch.ones(1, 8), rows, {str(i): str(i) for i in range(8)})
        altered = copy.deepcopy(result)
        altered['crop_predictions'][0]['logits'][0] += 1e-8
        self.assertFalse(old.compare_predictions(result, altered)['passed'])


if __name__ == '__main__':
    unittest.main()
