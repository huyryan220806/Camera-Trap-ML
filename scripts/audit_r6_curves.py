"""Audit saved R6 curves, or supplementary Train/Val eval. Never trains a model.

GPU evaluation writes a separate post-W6 ledger; historical artifacts are read-only.
"""
from pathlib import Path
import argparse
import csv
from datetime import datetime, timezone
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def curves(args):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from src.training import dino_probe as w5
    from src.training import dino_w6_control as control
    h = read(args.run / 'handoff.json')
    history = read(args.run / 'train_log.json')
    c = read(args.run / 'config.json')
    assert c == read(ROOT / 'configs/w6/tv3/R6.3h.frozen.json')
    assert c['run_id'] == 'R6' and c['recipe'] == 'R2'
    control.source_index(h['source_sha'])
    for relative, expected in read(args.run / 'source_index.json')['files_sha256'].items():
        assert w5.sha(args.run / relative) == expected, relative
    assert [r['epoch'] for r in history] == list(range(1, len(history) + 1))
    best = max(history, key=lambda r: r['validation_metrics']['macro_f1'])
    min_loss = min(history, key=lambda r: r['validation_metrics']['image_balanced_crop_ce'])
    fields = ['epoch', 'train_loss_online', 'val_loss', 'val_accuracy', 'val_macro_f1', 'epoch_seconds']
    rows = [dict(epoch=r['epoch'], train_loss_online=r['train_loss'],
        val_loss=r['validation_metrics']['image_balanced_crop_ce'],
        val_accuracy=r['validation_metrics']['accuracy'], val_macro_f1=r['validation_metrics']['macro_f1'],
        epoch_seconds=r['seconds']) for r in history]
    out = args.output
    assert not out.resolve().is_relative_to(args.run.resolve()), 'Never write inside historical run'
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'epoch_metrics.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    for name, series, ylabel in [
        ('cross_entropy', [('train_loss_online', 'Train online (augmentation, changing weights)'),
                           ('val_loss', 'Validation eval (no augmentation)')], 'Mean-parent-mean-crop cross entropy'),
        ('accuracy', [('val_accuracy', 'Validation eval accuracy')], 'Image accuracy'),
        ('macro_f1', [('val_macro_f1', 'Validation eval macro-F1')], 'Image macro-F1')]:
        fig, ax = plt.subplots(figsize=(10, 5.5))
        for key, label in series:
            ax.plot([r['epoch'] for r in rows], [r[key] for r in rows], marker='o', label=label)
        ax.axvline(best['epoch'], color='gray', linestyle='--', label=f"Selected epoch {best['epoch']}")
        ax.set(xlabel='Epoch', ylabel=ylabel, title='R6 — recorded training history')
        ax.set_xticks(range(1, len(rows) + 1))
        ax.grid(alpha=.25)
        ax.legend(fontsize=9)
        fig.tight_layout()
        fig.savefig(out / (name + '.png'), dpi=160)
        plt.close(fig)
    meta = dict(status='STATIC_AUDIT_COMPLETE_GPU_EVAL_PENDING', epochs=len(rows),
        best_macro_f1_epoch=best['epoch'], minimum_val_loss_epoch=min_loss['epoch'],
        first=rows[0], last=rows[-1], selected=rows[best['epoch'] - 1],
        source_commit=h['source_sha'], log_sha256=w5.sha(args.run / 'train_log.json'),
        config_sha256=h['config_sha256'], checkpoint_sha256=h['checkpoint_sha256'],
        runtime_sha256=control.w6.digest(read(args.run / 'runtime.json')),
        extra_tool_sha256=w5.sha(Path(__file__)),
        implementation='src/training/dino_w6.py (document path dino_w6_r6.py does not exist)',
        train_eval_history_available=False, official_test_opened=False)
    write(out / 'curve_audit.json', meta)
    (out / 'REPORT.md').write_text(
        '# R6 cross-entropy audit\n\n'
        f"Selected epoch: {best['epoch']}; lowest validation CE epoch: {min_loss['epoch']}.\n\n"
        f"Train online CE: {rows[0]['train_loss_online']:.6f} -> {rows[-1]['train_loss_online']:.6f}. "
        f"Validation CE: {rows[0]['val_loss']:.6f} -> {rows[-1]['val_loss']:.6f}.\n\n"
        'Validation improves then fluctuates near a plateau. There is no observed loss divergence. '
        'A decreasing online train loss with plateauing validation may suggest increasing train fit; '
        'the gap alone does not prove overfitting because measurement conditions differ.\n\n'
        'The original train curve is an average across optimizer updates with augmentation. '
        'Validation uses one end-of-epoch model in eval mode without augmentation. '
        'Both losses use mean-parent-mean-crop cross entropy; accuracy/F1 use mean crop probabilities per image. '
        'Validation explicitly calls model.eval() and torch.inference_mode(). '
        'Training enables only the last two blocks, final norm and head; other modules remain eval. '
        'Best checkpoint is selected by image macro-F1 with earliest tie; patience is 5.\n\n'
        'No train-eval accuracy/F1 history exists. Only supplementary eval of the selected epoch can be added. '
        'No implementation defect was found in these reviewed paths; full model evidence is pending GPU evaluation. '
        'The task document references dino_w6_r6.py; the actual bound implementation is dino_w6.py.\n\n'
        'Decision: KEEP_R6 pending same-mode supplementary evaluation and TV2 review. '
        'No new candidate training has been performed.\n', encoding='utf-8')
    print(json.dumps(meta, indent=2))


def evaluate(args):
    from src.training import dino_probe as w5
    from src.training import dino_w6 as d
    from src.training import dino_w6_control as control
    from src.training.curve_audit import preserved_eval
    import torch
    out = args.output
    assert args.booking.strip(), 'Need actual GPU booking'
    assert 0 < args.max_minutes <= 60, 'Supplementary evaluation cap must be <=60 minutes'
    assert not out.resolve().is_relative_to(args.run.resolve()), 'Never write inside historical run'
    assert not out.exists(), 'Preserve prior evidence; choose a new output path'
    c = read(args.run / 'config.json')
    assert c['run_id'] == 'R6' and d.digest(c) == '08a01874ccc2cf0f21e652ed082893bfc666e4489c01e7b5cb36404bebe67a70', 'Wrong R6 frozen config'
    runtime = d.configure_runtime(c)
    assert runtime == read(args.run / 'runtime.json'), 'Runtime lock mismatch'
    control.source_index(read(args.run / 'source_index.json')['commit'])
    registry = read(args.run / 'registry.approved.json')
    rows, cmap, gate = d.read_data(c, registry, pixels=True)
    assert (len(w5.groups_for(rows['train'])), len(rows['train']), len(w5.groups_for(rows['val'])), len(rows['val'])) == (4246, 4729, 600, 680)
    h = read(args.run / 'handoff.json')
    assert h['checkpoint_sha256'] == '24e3f51418dd7492a7537dff629794547c4540e8929bfe3e566105a6486581ef', 'Wrong accepted R6 checkpoint'
    out.mkdir(parents=True)
    ledger = dict(kind='POST_W6_SUPPLEMENTARY_EVAL_ONLY', status='RUNNING', booking=args.booking,
        max_seconds=args.max_minutes * 60, started_utc=datetime.now(timezone.utc).isoformat(),
        seconds=None, heartbeat_seconds=0, checkpoint_sha256=h['checkpoint_sha256'],
        tool_sha256=w5.sha(Path(__file__)), helper_sha256=w5.sha(ROOT / 'src/training/curve_audit.py'),
        official_attempt_created=False, historical_w6_ledger_changed=False)
    started = time.perf_counter()
    last_write = [-5.0]
    def tick():
        elapsed = time.perf_counter() - started
        if elapsed - last_write[0] >= 5:
            ledger['heartbeat_seconds'] = elapsed
            control.write_usage(out / 'usage.json', ledger)
            write(out / 'PROGRESS.json', dict(step='EVALUATING_SELECTED_R6_CHECKPOINT',
                elapsed_seconds=elapsed, no_training=True))
            last_write[0] = elapsed
        if elapsed >= ledger['max_seconds'] - 15:
            raise TimeoutError('Supplementary GPU budget reached; retain output and report')
    with w5.writer_lock(ROOT / 'outputs/tv3_w6/gpu_lock'):
        try:
            tick()
            model, _, payload = d.load_package(args.run / 'best_model.pt', h['checkpoint_sha256'], args.repo, 'cuda')
            assert payload['epoch'] == 13 and payload['class_map'] == cmap and payload['config'] == c
            assert payload['binding'] == read(args.run / 'binding.json')
            results = {}
            for split in ('train', 'val'):
                with preserved_eval(model):
                    logits = d.validation_logits(model, c, rows[split], 'cuda', tick=tick)
                result = w5.evaluate_logits(logits, rows[split], cmap)
                write(out / (split + '_eval.json'), result)
                results[split] = result
            comparison = w5.compare_predictions(payload['validation'], results['val'])
            write(out / 'validation_exact_comparison.json', comparison)
            assert comparison['passed'], 'Validation differs from original R6; report to TV2'
            summary = dict(status='PASS', checkpoint_epoch=13, evaluation_mode='eval_no_augmentation',
                train_scope='FULL_TRAIN_4246_IMAGES_4729_CROPS', loss='mean_parent_mean_crop_ce',
                train_eval=results['train']['metrics'], val_eval=results['val']['metrics'],
                train_eval_loss=results['train']['metrics']['image_balanced_crop_ce'],
                train_eval_accuracy=results['train']['metrics']['accuracy'],
                train_eval_macro_f1=results['train']['metrics']['macro_f1'],
                validation_exact_comparison=comparison, config_sha256=d.digest(c), runtime=runtime,
                data=gate, checkpoint_sha256=h['checkpoint_sha256'], official_test_opened=False)
            write(out / 'summary.json', summary)
            ledger['status'] = 'COMPLETED'
            print(json.dumps(summary, indent=2))
        except BaseException as exc:
            ledger.update(status='FAILED', error=repr(exc))
            raise
        finally:
            try:
                torch.cuda.synchronize()
            except Exception as exc:
                ledger.update(status='FAILED', synchronize_error=repr(exc))
            def refresh():
                ledger['seconds'] = time.perf_counter() - started
                ledger['ended_utc'] = datetime.now(timezone.utc).isoformat()
            control.write_usage(out / 'usage.json', ledger, refresh=refresh)
            write(out / 'PROGRESS.json', dict(step=ledger['status'], seconds=ledger['seconds'], no_training=True))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['curves', 'evaluate'])
    p.add_argument('--run', type=Path, default=ROOT / 'outputs/tv3_w6/runs/R6_attempt01')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--repo', type=Path, default=ROOT / 'outputs/tv3_w5/vendor/dinov3')
    p.add_argument('--booking', default='')
    p.add_argument('--max-minutes', type=float, default=30)
    args = p.parse_args()
    if args.action == 'curves':
        curves(args)
    else:
        evaluate(args)


if __name__ == '__main__':
    main()
