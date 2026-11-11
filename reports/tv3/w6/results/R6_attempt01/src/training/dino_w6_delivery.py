"""W6 checkpoint/export contract for independent TV2 audit and TV4 integration."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil
import zipfile

from . import dino_probe as w5
from . import dino_handoff as old_export
from . import dino_w6 as w6
from . import dino_w6_control as control

METRICS = ('accuracy', 'macro_f1', 'macro_precision', 'macro_recall')


def json_once(path, value):
    if path.exists():
        w5.require(w5.read_json(path) == value, 'Existing final artifact differs: ' + str(path))
    else:
        w5.atomic_json(path, value)


def export_training(run, model, c, binding, state, result, root=w5.ROOT):
    payload = dict(format=w6.FORMAT, config=c, binding=binding, model=w6.cpu_state(model),
                   epoch=state['best_epoch'], class_map=binding['class_map'], validation=result,
                   pooling=c['pooling'], feature_dim=c['feature_dim'], trainable=w6.named_mask(model))
    checkpoint = run / 'best_model.pt'
    if checkpoint.exists():
        import torch
        previous = torch.load(checkpoint, map_location='cpu', weights_only=True)
        old_state = previous.pop('model')
        metadata = {k: v for k, v in payload.items() if k != 'model'}
        w5.require(previous == metadata and old_state.keys() == payload['model'].keys() and
                   all(torch.equal(old_state[k], v) for k, v in payload['model'].items()),
                   'Existing best checkpoint differs; preserve it for investigation')
    else:
        w5.atomic_torch(checkpoint, payload)
    json_once(run / 'validation.json', result)
    w5.atomic_json(run / 'train_log.json', state['history'])
    json_once(run / 'config.json', c)
    json_once(run / 'runtime.json', binding['runtime'])
    json_once(run / 'class_map.json', binding['class_map'])
    json_once(run / 'preprocessing.json', dict(validation=c['preprocessing'], train_augmentation=c['augmentation']))
    json_once(run / 'source_index.json', binding['source_index'])
    for relative, expected in binding['source_index']['files_sha256'].items():
        source, target = root / relative, run / relative
        w5.require(w5.sha(source) == expected, 'Source changed during training')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            w5.require(w5.sha(target) == expected, 'Existing packaged source differs')
        else:
            shutil.copyfile(source, target)
    old_export.export_predictions(run, result, c['run_id'], w5.sha(checkpoint))
    hashes = old_export.manifest_hashes(binding['data'])
    artifacts = {name: old_export.artifact(run, run / file) for name, file in (
        ('config', 'config.json'), ('source_index', 'source_index.json'), ('training_log', 'train_log.json'),
        ('runtime', 'runtime.json'), ('crop_predictions', 'val_crops.jsonl'), ('image_predictions', 'val_images.jsonl'),
        ('class_mapping', 'class_map.json'), ('preprocessing', 'preprocessing.json'), ('binding', 'binding.json'))}
    handoff = dict(format=w6.FORMAT, run_id=c['run_id'], experiment_id=binding['attempt_id'], recipe=c['recipe'],
                   seed=c['seed'], checkpoint_sha256=w5.sha(checkpoint), checkpoint_bytes=checkpoint.stat().st_size,
                   checkpoint_path='best_model.pt', last_checkpoint_sha256=w5.sha(run / 'last_model.pt'),
                   config_sha256=w6.digest(c), config_raw_sha256=w5.sha(run / 'config.json'),
                   source_sha=binding['source_index']['commit'], execution_commit=binding['execution_commit'],
                   dataset_sha256=c['dataset_sha256'], train_dataset=c['dataset'], val_dataset='comparison_v1',
                   evaluation_split='val', class_order=[binding['class_map'][str(i)] for i in range(8)],
                   manifest_sha256=hashes, training_data_hashes=binding['data'],
                   aggregation='mean_crop_softmax_then_argmax', vendor_commit=c['vendor_commit'],
                   init_checkpoint_sha256=c['init_checkpoint_sha256'], pooling=c['pooling'], feature_dim=c['feature_dim'],
                   trainable_parameters=[n for n, p in model.named_parameters() if p.requires_grad],
                   best_epoch=state['best_epoch'], completed_epochs=state['epoch'],
                   validation_metrics={k: result['metrics'][k] for k in METRICS},
                   fresh_process_reload='PENDING', tv2_model_replay='PENDING', tv4_adapter='PENDING',
                   test_inference_performed=False, artifacts=artifacts,
                   loader='src.training.dino_w6.load_package / predict_crops')
    w5.atomic_json(run / 'handoff.json', handoff)
    matrix = result['metrics']['confusion_matrix']
    with (run / 'confusion_matrix.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['true/pred'] + handoff['class_order'])
        for i, values in enumerate(matrix):
            writer.writerow([handoff['class_order'][i]] + values)
    # Both numeric matrix and a figure are portable artifacts.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.imshow(matrix, cmap='Blues')
    ax.set_xticks(range(8), handoff['class_order'], rotation=65, ha='right')
    ax.set_yticks(range(8), handoff['class_order'])
    ax.set(xlabel='Predicted', ylabel='True', title=c['run_id'] + ' / validation GT crops')
    for i in range(8):
        for j in range(8):
            ax.text(j, i, str(matrix[i][j]), ha='center', va='center')
    fig.tight_layout()
    fig.savefig(run / 'confusion_matrix.png', dpi=160)
    plt.close(fig)
    card = f"""# {binding['attempt_id']}

Format: {w6.FORMAT}. Recipe {c['recipe']}, pooling `{c['pooling']}`,
feature dimension {c['feature_dim']}; seed {c['seed']}. Full backbone + head.
Best epoch {state['best_epoch']}; completed {state['epoch']} epochs.
Train: {c['dataset']}; validation: comparison_v1, 600 images / 680 GT crops.
Accuracy {result['metrics']['accuracy']!r}; macro-F1 {result['metrics']['macro_f1']!r}.

Checkpoint SHA-256: `{handoff['checkpoint_sha256']}`.
Use `src.training.dino_w6.load_package`, not the locked W5 loader.
RGB, square 256 uint8 bilinear antialias, ImageNet normalization, no EXIF.
Training loss averages within parent then across parents; validation averages
crop softmax vectors. Full-precision vectors and per-class metrics are in validation.json.

Fresh-process reload, independent TV2 model replay and TV4 adapter equivalence
are separate acceptance steps; see handoff.json and the actual receipts.
No Test evaluation. Validation reuse, one reference seed, GT boxes and balanced
classes limit generalization claims. Scores are not calibrated. R2 changes
optimizer and augmentation too; no isolated two-block causal claim or SOTA claim.
Seed42 stays headline; never replace it by a better seed43/44. No guarantee of 88%.
"""
    (run / 'MODEL_CARD.md').write_text(card, encoding='utf-8')
    return checkpoint


def comparison(run, root=w5.ROOT):
    """Saved vectors only, using TV2 arithmetic; never re-evaluates the R0 model."""
    v = control.tv2()
    from src.evaluation import w5_validation as auditor
    h = w5.read_json(run / 'handoff.json')
    parents, crops, _ = v.load_validation(root)
    images = auditor.read_jsonl(run / 'val_images.jsonl')
    actual = v.evaluate(auditor.read_jsonl(run / 'val_crops.jsonl'), images, parents, crops, h['run_id'], h['checkpoint_sha256'])
    reference = root / 'reports/tv2/w5_acceptance/2026-11-02/attempt_01/tv2_predictions.jsonl'
    control.committed_file(reference, 'cfcf00615847d52fba73ee3e44fe0e6076bb840c', root)
    paired = v.paired_report(auditor.read_jsonl(reference), images, parents, crops, h['run_id'], h['checkpoint_sha256'])
    table = dict(r0=dict(accuracy=.845, macro_f1=.8444008279545706), candidate=actual, paired=paired,
                 recipe=h['recipe'], seed=h['seed'], train_dataset=h['train_dataset'],
                 selection_status='PENDING_TV2', independent_model_replay='NOT_RUN')
    w5.atomic_json(run / 'validation_comparison.json', table)
    text = ('| Run | Seed | Accuracy | Macro-F1 |\n|---|---:|---:|---:|\n'
            '| R0 (W5) | 42 | 0.845 | 0.8444008279545706 |\n'
            f"| {h['run_id']} | {h['seed']} | {actual['metrics']['accuracy']!r} | {actual['metrics']['macro_f1']!r} |\n\n"
            'Same 600 validation images / 680 GT crops. No Test. TV2 selection/replay pending.\n')
    (run / 'validation_comparison.md').write_text(text, encoding='utf-8')


def summarize(registry_path, output, root=w5.ROOT):
    """Saved-artifact audit and per-recipe seed statistics; does not grant selection."""
    v = control.tv2()
    from src.evaluation import w5_validation as auditor
    registry = w5.read_json(registry_path)
    accounting = v.validate_registry(registry, root)
    rows, grouped, candidates = [], {}, []
    for registered in registry['runs']:
        item = {k: registered[k] for k in ('run_id', 'recipe', 'seed', 'dataset', 'status', 'attempts')}
        item['metrics'] = registered['metrics']
        if registered['run_id'] != 'R0' and registered['status'] == 'COMPLETED':
            attempt = registered['attempts'][-1]['attempt_id']
            folder = v.confined(root / 'outputs/tv3_w6/runs', attempt)
            handoff = w5.read_json(folder / 'handoff.json')
            _, parents, crops = v.verify_submission(registry, registered['run_id'], handoff, folder, folder / 'best_model.pt', root)
            audit = v.evaluate(auditor.read_jsonl(folder / 'val_crops.jsonl'), auditor.read_jsonl(folder / 'val_images.jsonl'),
                               parents, crops, registered['run_id'], registered['checkpoint_sha256'])
            for name in ('accuracy', 'macro_f1'):
                w5.require(abs(audit['metrics'][name] - registered['metrics'][name]) <= 1e-10, 'Registry/result mismatch')
            item.update(metrics=audit['metrics'], checkpoint_sha256=registered['checkpoint_sha256'],
                        per_class=audit['per_class'], confusion_matrix=audit['confusion_matrix'])
            key = (registered['recipe'], registered['dataset'])
            grouped.setdefault(key, []).append(dict(run_id=registered['run_id'], recipe=key[0], dataset=key[1],
                                                   seed=registered['seed'], metrics=audit['metrics']))
            if registered['run_id'] in ('R1', 'R2'):
                candidates.append(dict(run_id=registered['run_id'], seed=42, metrics=audit['metrics']))
        rows.append(item)
    summaries = []
    for (recipe, dataset), group in grouped.items():
        expected = {42, 43} if dataset == 'train_expansion_w6_v1' else {42, 43, 44}
        if any(r['seed'] == 42 for r in group):
            summary = v.seed_summary(group)
            summary['missing_seeds'] = sorted(expected - {r['seed'] for r in group})
            summaries.append(dict(recipe=recipe, dataset=dataset, expected_seeds=sorted(expected), **summary))
        else:
            summaries.append(dict(recipe=recipe, dataset=dataset, status='MISSING_SEED42', per_seed=group))
    proposal = dict(status='PENDING_TV2', reason='Need both R1/R2 or explicit TV2 exception for a failed run')
    if len(candidates) == 2:
        try:
            selected = v.select_seed42(candidates)
            winner = next(r for r in candidates if r['run_id'] == selected)
            proposal.update(candidate=selected, improves_r0=winner['metrics']['macro_f1'] > .8444008279545706,
                            accuracy_not_lower=winner['metrics']['accuracy'] >= .845,
                            reason='Metric ordering only; independent replay/regressions/adapter still require review')
        except ValueError as exc:
            proposal['reason'] = str(exc)  # Cost tie stays pending; never invent a benchmark.
    result = dict(status='PRODUCER_ARTIFACT_SUMMARY', accounting=accounting, runs=rows, seed_groups=summaries,
                  selection_proposal=proposal, registry_sha256=w5.sha(registry_path),
                  tv2_independent_replay='PENDING', tv4_integration='PENDING', test_inference_performed=False)
    output = Path(output)
    w5.require(not output.exists() and not output.with_suffix('.md').exists(), 'Use a new summary output')
    w5.atomic_json(output, result)
    lines = ['| Run | Recipe | Seed | Dataset | Status | Accuracy | Macro-F1 |',
             '|---|---|---:|---|---|---:|---:|']
    for r in rows:
        metrics = r['metrics'] or {}
        lines.append(f"| {r['run_id']} | {r['recipe']} | {r['seed']} | {r['dataset']} | {r['status']} | "
                     f"{metrics.get('accuracy', '—')} | {metrics.get('macro_f1', '—')} |")
    lines += ['', 'All attempts and seed mean/sample SD are in the JSON. Seed42 remains headline.',
              'Producer artifact summary; independent TV2 replay, recipe decision and TV4 integration remain separate.']
    output.with_suffix('.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return result


def package(run, registry_path, output, report_dir=None, root=w5.ROOT):
    v = control.tv2()
    h = w5.read_json(run / 'handoff.json')
    registry = w5.read_json(registry_path)
    v.verify_submission(registry, h['run_id'], h, run, run / 'best_model.pt', root)
    for artifact in h['artifacts'].values():
        w5.require(w5.sha(v.confined(run, artifact['path'])) == artifact['sha256'], 'Artifact changed before packaging')
    w5.require(w5.sha(run / 'last_model.pt') == h['last_checkpoint_sha256'], 'Last checkpoint changed')
    output = Path(output)
    w5.require(not output.exists() and not output.with_suffix('.sha256.json').exists(), 'Use a new ZIP output')
    files = sorted(p for p in run.rglob('*') if p.is_file() and p.suffix not in ('.tmp', '.pyc') and
                   '__pycache__' not in p.parts and p.name != 'writer.guard')
    # No vendor tree, pretrained file, signed link or unrelated outputs is copied.
    index = {p.relative_to(run).as_posix(): dict(sha256=w5.sha(p), bytes=p.stat().st_size) for p in files}
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, arcname=run.name + '/' + p.relative_to(run).as_posix())
        z.writestr(run.name + '/package_index.json', json.dumps(index, indent=2, allow_nan=False))
        z.write(registry_path, arcname=run.name + '/registry.delivery.json')
    with zipfile.ZipFile(output) as z:
        w5.require(z.testzip() is None, 'ZIP CRC failed')
        import hashlib
        for name, entry in index.items():
            w5.require(hashlib.sha256(z.read(run.name + '/' + name)).hexdigest() == entry['sha256'], 'ZIP payload changed')
    receipt = dict(zip_sha256=w5.sha(output), bytes=output.stat().st_size,
                   checkpoint_sha256=h['checkpoint_sha256'], files=index, tv2_model_replay='PENDING', tv4_adapter='PENDING')
    w5.atomic_json(output.with_suffix('.sha256.json'), receipt)
    if report_dir:
        report_dir = Path(report_dir)
        report_dir.mkdir(parents=True, exist_ok=False)
        for p in files:
            if p.suffix in ('.pt', '.pth', '.ckpt'):
                continue
            target = report_dir / p.relative_to(run)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
        w5.atomic_json(report_dir / 'package_index.json', index)
        w5.atomic_json(report_dir / 'delivery.json', receipt)
    return receipt
