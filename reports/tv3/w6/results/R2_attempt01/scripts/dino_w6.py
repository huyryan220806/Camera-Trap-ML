"""TV3 W6: prepare -> smoke -> freeze proposal -> peer approval -> train -> reload -> package.

No command grants TV2 approval. Source and config must be committed before train.
Run from the repository root. See docs/handoff_tv3_w6.md for PowerShell commands.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import torch
from src.training import dino_probe as old
from src.training import dino_w6 as d
from src.training import dino_w6_control as control
from src.training import dino_w6_delivery as delivery


def new_file(path):
    path = Path(path)
    old.require(not path.exists(), 'Output exists; preserve it and use a new path: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def safe_id(value):
    import re
    old.require(re.fullmatch(r'[A-Za-z0-9_-]+', value) is not None, 'Unsafe attempt ID')
    return value


def read_config(path):
    c = old.read_json(path)
    d.validate_config(c)
    return c


def state_equal(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and torch.equal(a.cpu(), b.cpu())
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(state_equal(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return len(a) == len(b) and all(state_equal(x, y) for x, y in zip(a, b))
    return a == b


def prepare(args):
    c = read_config(args.base)
    registry = old.read_json(args.registry)
    run = next(r for r in registry['runs'] if r['run_id'] == args.run_id)
    old.require(args.run_id in ('R3', 'R4', 'R5', 'R6') and not run['attempts'], 'Prepare conditional runs only')
    decision = registry['recipe_selection']
    old.require(decision and decision['evidence_path'], 'Need TV2 recipe decision')
    recipe = decision['recipe']
    if args.run_id in ('R3', 'R4'):
        old.require(decision['improves_r0'] is True and recipe in ('R1', 'R2'), 'Seed repeats need improvement')
    else:
        review = registry['data_review']
        old.require(review['status'] == 'PASS' and review['release_sha256'] == d.EXPANSION_SHA and review['evidence_path'],
                    'R5/R6 blocked pending TV2 release review')
    old.require(c['recipe'] == recipe or recipe == 'R0' and c['recipe'] == 'R1', 'Use selected recipe config as base')
    c.update(run_id=args.run_id, seed=run['seed'], dataset=run['dataset'], dataset_sha256=run['dataset_sha256'],
             status='DRAFT', recipe=recipe)
    c.pop('smoke_evidence', None)
    c['runtime'].update(source_sha=None, runtime_lock=None)
    if recipe == 'R0':
        c.update(pooling='x_norm_clstoken', feature_dim=384, init_mode='W5_backbone_only_new_384_head')
        c['cache'].update(feature_dim=384, namespace='w6_R0_cls_384')
    d.validate_config(c)
    old.atomic_json(new_file(args.output), c)


def preflight(args):
    c = read_config(args.config)
    runtime = d.configure_runtime(c)
    sources = control.source_index(c['runtime']['source_sha'])
    old.require(old.sha(args.init_checkpoint) == d.R0_SHA, 'Init checkpoint SHA mismatch')
    old.require(old.git_revision(args.repo) == d.VENDOR, 'Vendor commit mismatch')
    registry = old.read_json(args.registry) if args.registry else None
    rows, _, gate = d.read_data(c, registry, pixels=True)
    result = dict(status='PASS', official_training=False, model_forward=False, test_opened=False,
                   config_raw_sha256=old.sha(args.config), config_sha256=d.digest(c), data=gate,
                   counts={s: dict(images=len(old.groups_for(v)), crops=len(v)) for s, v in rows.items()},
                   runtime=runtime, source_index=sources, init_checkpoint_sha256=d.R0_SHA,
                   command=sys.argv, protocol_status=(registry or {}).get('protocol_status', 'NOT_CHECKED'))
    old.atomic_json(new_file(args.output), result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def smoke(args):
    c = read_config(args.config)
    runtime = d.configure_runtime(c)
    sources = control.source_index()
    registry = old.read_json(args.registry) if args.registry else None
    rows, cmap, gate = d.read_data(c, registry, train_only=True)
    # Include the largest multi-crop parent and a real incomplete parent batch.
    groups = sorted(old.groups_for(rows['train']), key=lambda g: -len(g))[:c['parent_batch'] + 3]
    selected = [rows['train'][i] for group in groups for i in group]
    old.require(len(groups) == c['parent_batch'] + 3 and max(map(len, groups)) > 1, 'Smoke needs multi-crop and final batch')
    d.verify_pixels(selected)
    attempt = safe_id(args.attempt)
    folder = ROOT / 'outputs/tv3_w6/smoke' / attempt
    folder.mkdir(parents=True, exist_ok=False)
    report = dict(status='RUNNING', official_training=False, validation_inference=False, test_opened=False,
                   settings_sha256=control.settings_digest(c), config_sha256=d.digest(c),
                   config_raw_sha256=old.sha(args.config), runtime=runtime, source_index=sources,
                   command=sys.argv, data=gate, parent_count=len(groups), crop_count=len(selected),
                   selected_crop_ids=[r['crop_id'] for r in selected], attempt_id=attempt, recipe=c['recipe'])
    try:
        with control.gpu_session(attempt, c['run_id'], 'train_only_smoke', args.booking) as (tick, _):
            torch.cuda.reset_peak_memory_stats()
            model, model_map = d.initialize(c, args.init_checkpoint, args.repo, 'cuda')
            old.require(model_map == cmap, 'Init class map differs')
            model.train()
            mask = d.named_mask(model)
            frozen_before = {n: p.detach().cpu().clone() for n, p in model.named_parameters() if not p.requires_grad}
            optimizer = d.optimizer_for(model, c)
            scheduler = d.scheduler_for(optimizer, c)
            optimizer.zero_grad(set_to_none=True)
            d.backward_parent_batch(model, rows['train'], groups[:c['parent_batch']], c, 'cuda', tick=tick)
            gradients = {n: dict(present=p.grad is not None,
                                 finite=bool(torch.isfinite(p.grad).all()) if p.grad is not None else None)
                         for n, p in model.named_parameters()}
            optimizer.step()
            scheduler.step()
            old.require(all(torch.equal(v, dict(model.named_parameters())[n].detach().cpu())
                            for n, v in frozen_before.items()), 'Frozen parameters changed')
            saved = dict(model=d.cpu_state(model), optimizer=optimizer.state_dict(), scheduler=scheduler.state_dict(),
                         rng=old.rng_state(), sampler=dict(next_epoch=1), bad_epochs=2, best_epoch=1, amp_scaler=None)
            old.atomic_torch(folder / 'resume_fixture.pt', saved)
            saved = torch.load(folder / 'resume_fixture.pt', map_location='cpu', weights_only=True)

            def tail_step():
                model.train()
                optimizer.zero_grad(set_to_none=True)
                loss = d.backward_parent_batch(model, rows['train'], groups[c['parent_batch']:], c, 'cuda', tick=tick)
                optimizer.step()
                scheduler.step()
                return dict(loss=loss, model=d.cpu_state(model), optimizer=copy.deepcopy(optimizer.state_dict()),
                            scheduler=copy.deepcopy(scheduler.state_dict()), rng=old.rng_state())

            expected = tail_step()
            model.load_state_dict(saved['model'], strict=True)
            optimizer.load_state_dict(saved['optimizer'])
            scheduler.load_state_dict(saved['scheduler'])
            old.restore_rng(saved['rng'])
            actual = tail_step()
            old.require(state_equal(expected, actual), 'Train-only resume differs')
            old.require(all(torch.equal(v, dict(model.named_parameters())[n].detach().cpu())
                            for n, v in frozen_before.items()), 'Frozen parameters changed after tail')
            model.eval()
            with torch.inference_mode():
                sample = d.crop_batch(rows['train'], groups[0][:1], c, ROOT, False).to('cuda')
                before = model(sample).cpu()
                model.load_state_dict(d.cpu_state(model), strict=True)
                after = model(sample).cpu()
            old.require(torch.equal(before, after), 'Strict load changed logits')
            report.update(status='PASS', named_parameters=mask, gradient_evidence=gradients,
                          module_modes_train={n: m.training for n, m in model.train().named_modules()},
                          frozen_unchanged=True, strict_load_exact=True, resume_exact=True,
                          tail_parent_count=3, microbatch=c['crop_microbatch'], head_dimension=c['feature_dim'],
                          peak_allocated_vram=torch.cuda.max_memory_allocated(),
                          resume_fixture_sha256=old.sha(folder / 'resume_fixture.pt'), exit_code=0)
    except BaseException as exc:
        report.update(status='FAIL', error=repr(exc), exit_code=1)
        raise
    finally:
        report['usage'] = control.load_usage()
        old.atomic_json(folder / 'receipt.json', report)
    print(folder / 'receipt.json')


def freeze(args):
    c = read_config(args.config)
    report = old.read_json(args.smoke)
    old.require(report['status'] == 'PASS' and report['settings_sha256'] == control.settings_digest(c) and
                report['official_training'] is False and report['validation_inference'] is False,
                'Need matching train-only smoke PASS')
    sources = control.source_index(report['source_index']['commit'])
    old.require(sources == report['source_index'], 'Source differs from smoke')
    # Freeze records evidence; approval fields remain empty for real peer review.
    config_out = new_file(args.output)
    old.require(config_out.resolve().is_relative_to((ROOT / 'configs/w6').resolve()), 'Frozen config must be in configs/w6')
    report_path = ROOT / 'reports/tv3/w6/smoke' / (report['attempt_id'] + '.json')
    new_file(report_path)
    shutil.copyfile(args.smoke, report_path)
    c.update(status='FROZEN', smoke_evidence=dict(path=report_path.relative_to(ROOT).as_posix(), sha256=old.sha(report_path)))
    c['runtime'].update(source_sha=sources['commit'], runtime_lock=d.digest(report['runtime']))
    d.validate_config(c)
    registry = control.registry_with_usage(old.read_json(args.registry))
    row = next(r for r in registry['runs'] if r['run_id'] == c['run_id'])
    old.require(not row['attempts'], 'Cannot refreeze a run that has already started')
    row.update(recipe=c['recipe'], config_path=config_out.resolve().relative_to(ROOT).as_posix(),
               config_sha256=d.digest(c), source_sha=sources['commit'], approvals={'TV2': None, 'TV3': None})
    # Completed historical runs still require their actual global approval in
    # TV2's schema. Keep that receipt; the NEW run's approvals above stay null.
    # Before the first experiment there is no historical approval to preserve.
    if not any(r['attempts'] for r in registry['runs']):
        registry.update(protocol_status='DRAFT', approvals={'TV2': None, 'TV3': None},
                        smoke_evidence=report_path.relative_to(ROOT).as_posix(),
                        freeze_evidence=config_out.resolve().relative_to(ROOT).as_posix())
    proposal = new_file(args.proposal)
    old.atomic_json(config_out, c)
    control.tv2().validate_registry(registry)
    old.atomic_json(proposal, registry)
    print(f'FROZEN config, NEW RUN APPROVAL PENDING: {config_out}\nRegistry proposal: {proposal}\nCanonical SHA: {d.digest(c)}')


def training(args):
    c = read_config(args.config)
    runtime = d.configure_runtime(c)
    registry, _, sources = control.approved_gate(c, args.config, args.registry, runtime)
    rows, cmap, gate = d.read_data(c, registry, pixels=True)
    attempt = safe_id(args.attempt)
    run = ROOT / 'outputs/tv3_w6/runs' / attempt
    binding = dict(config_sha256=d.digest(c), config_file_raw_sha256=old.sha(args.config), runtime=runtime,
                   data=gate, source_index=sources, class_map=cmap, attempt_id=attempt,
                   execution_commit=old.git_revision(ROOT))
    if args.resume:
        previous = old.read_json(run / 'binding.json')
        # Documentation/approval commits may advance; executed source must be byte-identical.
        binding['execution_commit'] = previous['execution_commit']
        old.require(previous == binding, 'Resume input/runtime/source/config changed')
        status = old.read_json(run / 'status.json')
        old.require(status['status'] != 'COMPLETED' and not status.get('training_complete'),
                    'Training already complete; use reload, never retrain this run')
    else:
        previous_runs = list((ROOT / 'outputs/tv3_w6/runs').glob('*/binding.json'))
        for path in previous_runs:
            old_config = path.parent / 'config.json'
            if old_config.exists():
                old.require(old.read_json(old_config)['run_id'] != c['run_id'],
                            'Run already has an attempt; resume it or obtain a revised TV2 registration')
        run.mkdir(parents=True, exist_ok=False)
        old.atomic_json(run / 'binding.json', binding)
        old.atomic_json(run / 'config.json', c)
        shutil.copyfile(args.registry, run / 'registry.approved.json')
    old.atomic_json(run / 'status.json', dict(status='RUNNING', training_complete=False, command=sys.argv))
    try:
        with control.gpu_session(attempt, c['run_id'], 'official', args.booking, args.resume) as (tick, _):
            torch.cuda.reset_peak_memory_stats()
            model, loaded_map = d.initialize(c, args.init_checkpoint, args.repo, 'cuda')
            old.require(loaded_map == cmap, 'Initialization class mapping mismatch')
            features = None
            if c['cache']['enabled']:
                features, cache = d.cache_features(model, c, rows, gate, runtime, sources, tick=tick)
                old.atomic_json(run / 'cache_reference.json', cache)
            state, result = d.train_epochs(model, c, rows, cmap, run, binding, features, args.resume, tick=tick)
            delivery.export_training(run, model, c, binding, state, result)
            delivery.comparison(run)
            old.atomic_json(run / 'status.json', dict(status='STOPPED', training_complete=True,
                                                      reason='TRAINED_AWAITING_FRESH_PROCESS_RELOAD', command=sys.argv))
    except BaseException as exc:
        state = ('OOM' if isinstance(exc, torch.cuda.OutOfMemoryError) else
                 'STOPPED' if isinstance(exc, (KeyboardInterrupt, control.BudgetExceeded)) else 'FAILED')
        old.atomic_json(run / 'status.json', dict(status=state, training_complete=False, error=repr(exc), command=sys.argv))
        raise
    finally:
        old.atomic_json(run / 'usage.json', control.load_usage())
        # Any unmeasured crash remains a blocker; do not manufacture a completed receipt.
        old.atomic_json(run / 'registry.result.json', control.registry_with_usage(registry))
    print(f'Training complete. Next: reload in a NEW process. Run: {run}')


def reload_model(args):
    run = Path(args.run).resolve()
    c = read_config(run / 'config.json')
    runtime = d.configure_runtime(c)
    binding = old.read_json(run / 'binding.json')
    old.require(runtime == binding['runtime'] and control.source_index(binding['source_index']['commit']) == binding['source_index'],
                'Exact reload requires identical source/runtime; do not widen tolerance')
    checkpoint = run / 'best_model.pt'
    handoff = old.read_json(run / 'handoff.json')
    registry = old.read_json(run / 'registry.approved.json')
    # Validation only; expansion data need not be present at the receiver.
    _, cmap, gate = old.read_release(verify_images=False)
    rows = d.read_jsonl(ROOT / 'data/processed/comparison_v1/b2/val.jsonl')
    d.verify_pixels(rows)
    report_path = new_file(run / (safe_id(args.receipt) + '.json'))
    status = old.read_json(run / 'status.json')
    old.require(status.get('training_complete') is True and status['status'] != 'COMPLETED',
                'Need completed training awaiting reload; a successful reload is already final')
    report = dict(status='FAIL', fresh_process=True, command=sys.argv, evaluation_split='val', test_inference_performed=False,
                   checkpoint_sha256=handoff['checkpoint_sha256'], config_sha256=d.digest(c),
                   source_sha=binding['source_index']['commit'], runtime_sha256=d.digest(runtime), runtime=runtime,
                   comparison_policy='exact', manifest_sha256={n: gate['files'][n] for n in
                       ('class_map.json', 'train.jsonl', 'val.jsonl', 'b2/train.jsonl', 'b2/val.jsonl')})
    try:
        with control.gpu_session(binding['attempt_id'], c['run_id'], 'reload', args.booking, resume=True) as (tick, _):
            model, _, payload = d.load_package(checkpoint, handoff['checkpoint_sha256'], args.repo, 'cuda')
            old.require(payload['class_map'] == cmap and payload['binding'] == binding, 'Reload payload binding')
            result = old.evaluate_logits(d.validation_logits(model, c, rows, 'cuda', tick=tick), rows, cmap)
            comparison = old.compare_predictions(payload['validation'], result)
            predictions = new_file(report_path.with_suffix('.predictions.json'))
            old.atomic_json(predictions, result)
            report.update(comparison, status='PASS' if comparison['passed'] else 'FAIL',
                          validation_images=len(result['image_predictions']), validation_crops=len(result['crop_predictions']),
                          predictions_sha256=old.sha(predictions), predictions_path=predictions.name)
            old.require(comparison['passed'], 'Exact fresh-process reload failed; preserve evidence and report to TV2')
    except BaseException as exc:
        report.update(status='FAIL', error=repr(exc))
        raise
    finally:
        old.atomic_json(report_path, report)
        handoff['artifacts']['reload_report'] = dict(path=report_path.name, sha256=old.sha(report_path))
        handoff['fresh_process_reload'] = report['status']
        old.atomic_json(run / 'handoff.json', handoff)
        old.atomic_json(run / 'status.json', dict(status='COMPLETED' if report['status'] == 'PASS' else 'FAILED',
                                                  training_complete=True, reload_report=report_path.name))
        old.atomic_json(run / 'usage.json', control.load_usage())
        old.atomic_json(run / 'registry.result.json', control.registry_with_usage(registry))
    print(json.dumps(report, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    for name in ('preflight', 'smoke', 'freeze', 'train'):
        s = sub.add_parser(name)
        s.add_argument('--config', type=Path, required=True)
        s.add_argument('--registry', type=Path, required=name in ('freeze', 'train'))
        if name in ('preflight', 'smoke', 'train'):
            s.add_argument('--init-checkpoint', type=Path, default=ROOT / 'outputs/tv3_w5/runs/DINOv3_LP_run01/best_model.pt')
            s.add_argument('--repo', type=Path, default=ROOT / 'outputs/tv3_w5/vendor/dinov3')
        if name in ('smoke', 'train'):
            s.add_argument('--attempt', required=True)
            s.add_argument('--booking', required=True, help='Actual agreed GPU/device/time slot, recorded verbatim')
        if name in ('preflight', 'freeze'):
            s.add_argument('--output', type=Path, required=True)
        if name == 'freeze':
            s.add_argument('--smoke', type=Path, required=True)
            s.add_argument('--proposal', type=Path, required=True)
        if name == 'train':
            s.add_argument('--resume', action='store_true')
    s = sub.add_parser('prepare')
    s.add_argument('--base', type=Path, required=True)
    s.add_argument('--run-id', choices=['R3', 'R4', 'R5', 'R6'], required=True)
    s.add_argument('--registry', type=Path, required=True)
    s.add_argument('--output', type=Path, required=True)
    s = sub.add_parser('reload')
    s.add_argument('--run', type=Path, required=True)
    s.add_argument('--receipt', default='reload01')
    s.add_argument('--repo', type=Path, default=ROOT / 'outputs/tv3_w5/vendor/dinov3')
    s.add_argument('--booking', required=True)
    s = sub.add_parser('package')
    s.add_argument('--run', type=Path, required=True)
    s.add_argument('--registry', type=Path, required=True)
    s.add_argument('--output', type=Path, required=True)
    s.add_argument('--report-dir', type=Path)
    s = sub.add_parser('report')
    s.add_argument('--registry', type=Path, required=True)
    s.add_argument('--output', type=Path, required=True)
    s = sub.add_parser('settle-usage')
    s.add_argument('--receipt', type=Path, required=True)
    args = p.parse_args()
    if args.action == 'package':
        print(json.dumps(delivery.package(args.run, args.registry, args.output, args.report_dir), indent=2))
    elif args.action == 'report':
        print(json.dumps(delivery.summarize(args.registry, args.output), indent=2, ensure_ascii=False))
    elif args.action == 'settle-usage':
        print(control.reconcile_usage(args.receipt))
    else:
        dict(prepare=prepare, preflight=preflight, smoke=smoke, freeze=freeze, train=training, reload=reload_model)[args.action](args)


if __name__ == '__main__':
    main()
