"""TV3 W5 command line: preflight, pin, cache, train/resume, fresh reload."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import torch
from torch import nn
from src.training import dino_probe as d
from src.training import dino_handoff as h


def new_output(path):
    path = Path(path)
    d.require(not path.exists(), f'Output already exists: {path}; use a new attempt path')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def pin(args):
    c = d.read_json(args.config)
    d.validate_config(c, pinned=False)
    repo = Path(args.repo).resolve()
    weights = Path(args.weights).resolve()
    c['model'].update(repo_dir=str(repo), repo_commit=d.git_revision(repo), weights_path=str(weights),
                      weights_sha256=d.sha(weights), weights_source=args.source)
    # Store portable repo-relative paths when available.
    for field, path in [('repo_dir', repo), ('weights_path', weights)]:
        if path.is_relative_to(ROOT):
            c['model'][field] = path.relative_to(ROOT).as_posix()
    d.validate_config(c)
    out = new_output(args.output)
    proposal_path = new_output(out.with_suffix('.protocol.json'))
    proposal = h.protocol_draft(c)
    d.atomic_json(out, c)
    d.atomic_json(proposal_path, proposal)
    print(f'Pinned config: {out}\nProtocol proposal: {proposal_path}')


def preflight(args):
    out = new_output(args.output)
    c = d.read_json(args.config)
    d.validate_config(c, pinned=False)
    d.seed_all(c['training']['seed'])
    rows, cmap, gate = d.read_release(verify_images=True)
    result = {'data': gate, 'runtime': d.runtime(), 'config_sha256': d.digest(c),
              'counts': {s: {'images': len(d.groups_for(r)), 'crops': len(r)} for s, r in rows.items()},
              'backbone_smoke': 'NOT_RUN', 'protocol_status': 'NOT_CHECKED', 'test_opened': False}
    if args.with_model:
        d.validate_config(c)
        device = c['runtime']['device']
        model = d.load_backbone(c, device)
        transform = d.transform_for(c['model']['name'])
        x = torch.stack([d.crop_tensor(r, transform) for r in rows['train'][:2]]).to(device)
        with torch.inference_mode():
            features = d.extract(model, x)
        result['backbone_smoke'] = {'shape': list(features.shape), 'frozen': all(not p.requires_grad for p in model.parameters())}
    d.atomic_json(out, result)
    print(json.dumps(result, indent=2))


def preparation(args):
    c = d.read_json(args.config)
    d.validate_config(c)
    protocol = d.check_protocol(c, Path(args.protocol))
    device = c['runtime']['device']
    d.require(device != 'cuda' or torch.cuda.is_available(), 'CUDA unavailable; no silent fallback')
    d.seed_all(c['training']['seed'])
    env = d.runtime()
    rows, cmap, gate = d.read_release(verify_images=True)
    return c, protocol, env, rows, cmap, gate


def comparison(result, c, history, gate, env):
    # Recompute full-precision baseline values from its frozen confusion matrix.
    ref_path = ROOT / 'reports/tv3/validation_comparison.json'
    d.require(d.sha(ref_path) == '51becb94cc4837657fade7e341dd9f874079136bbc763ad4e7266d40c24c3806', 'Historical B2 reference changed')
    ref = d.read_json(ref_path)['image_level_metrics']
    matrix = torch.tensor(ref['confusion_matrix'], dtype=torch.float64)
    tp = matrix.diag()
    precision = tp / matrix.sum(0).clamp(min=1)
    recall = tp / matrix.sum(1).clamp(min=1)
    f1 = 2 * precision * recall / (precision + recall).clamp(min=1e-30)
    baseline = {'experiment_id': 'b2_run01', 'backbone': 'resnet18', 'checkpoint_sha256': d.B2_SHA,
                'reference_report_sha256': d.sha(ref_path), 'source': 'historical_validation_confusion_matrix',
                'accuracy': float(tp.sum() / matrix.sum()), 'macro_f1': float(f1.mean()),
                'macro_precision': float(precision.mean()), 'macro_recall': float(recall.mean()),
                'images': 600, 'crops': 680, 'seed': 42}
    candidate = dict(result['metrics'], experiment_id=c['experiment_id'], backbone=c['model']['name'],
                     seed=c['training']['seed'], pretrained=c['model'],
                     train_images=2800, train_crops=3125, head_seconds=sum(h['seconds'] for h in history))
    return {'baseline': baseline, 'candidate': candidate, 'dataset': gate, 'runtime': env,
            'test_opened': False, 'claim': 'Validation comparison; different architecture, pretraining and training recipe, not equal compute.'}


def train(args):
    c, protocol, env, rows, cmap, gate = preparation(args)
    run = ROOT / 'outputs/tv3_w5/runs' / c['experiment_id']
    # Locks live outside the run so a new run is atomically reserved with mkdir.
    with d.writer_lock(ROOT / 'outputs/tv3_w5/locks' / c['experiment_id']):
        if args.resume:
            d.require((run / 'binding.json').is_file(), 'No resumable run binding')
        else:
            run.mkdir(parents=True, exist_ok=False)
        binding = {'config': c, 'protocol': protocol, 'runtime': env, 'data': gate,
                   'code_sha256': d.source_code_hash(), 'cli_sha256': d.sha(Path(__file__)),
                   'handoff_code_sha256': d.sha(Path(h.__file__)),
                   'code_commit': d.git_revision(ROOT), 'class_map': cmap}
        if args.resume:
            d.require(d.read_json(run / 'binding.json') == binding, 'Run inputs changed; use a new experiment ID')
            d.require(d.read_json(run / 'status.json').get('status') != 'COMPLETE', 'Completed run is immutable')
        else:
            d.atomic_json(run / 'binding.json', binding)
            d.atomic_json(run / 'config.json', c)
        d.atomic_json(run / 'status.json', {'status': 'RUNNING', 'started_utc': datetime.now(timezone.utc).isoformat()})
        try:
            started = time.perf_counter()
            folder, index = d.cache_features(c, rows, gate, env)
            features = d.load_features(folder, index, rows)
            d.atomic_json(run / 'cache_reference.json', {'key': index['key'], 'index_sha256': d.sha(folder / 'index.json'),
                                                       'extraction_seconds_recorded': sum(s['seconds'] for s in index['shards'].values())})
            # Seed again: head initialization independent of whether extraction was resumed.
            d.seed_all(c['training']['seed'])
            head, epoch, result, history = d.train_head(c, features, rows, cmap, run, binding, args.resume)
            backbone = d.load_backbone(c, 'cpu')
            payload = {'format': 'TV3_DINO_LINEAR_V1', 'config': c, 'binding': binding, 'epoch': epoch,
                       'head': head, 'backbone': backbone.state_dict(), 'class_map': cmap,
                       'label_to_id': {v: int(k) for k, v in cmap.items()}, 'feature_pooling': 'x_norm_clstoken',
                       'validation': result, 'cache_key': index['key']}
            checkpoint = run / 'best_model.pt'
            d.atomic_torch(checkpoint, payload)
            d.atomic_json(run / 'validation.json', result)
            table = comparison(result, c, history, gate, env)
            table['checkpoint'] = {'path': str(checkpoint), 'sha256': d.sha(checkpoint), 'bytes': checkpoint.stat().st_size}
            table['elapsed_this_attempt_seconds'] = time.perf_counter() - started
            d.atomic_json(run / 'validation_comparison.json', table)
            import csv
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            matrix = result['metrics']['confusion_matrix']
            with (run / 'confusion_matrix.csv').open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['true/pred'] + [cmap[str(i)] for i in range(8)])
                for i, row in enumerate(matrix):
                    writer.writerow([cmap[str(i)]] + row)
            fig, ax = plt.subplots(figsize=(10, 9))
            ax.imshow(matrix, cmap='Blues')
            ax.set_xticks(range(8), [cmap[str(i)] for i in range(8)], rotation=65, ha='right')
            ax.set_yticks(range(8), [cmap[str(i)] for i in range(8)])
            ax.set(xlabel='Predicted', ylabel='True', title=c['experiment_id'] + ' — validation images')
            for i in range(8):
                for j in range(8):
                    ax.text(j, i, str(matrix[i][j]), ha='center', va='center')
            fig.tight_layout()
            fig.savefig(run / 'confusion_matrix.png', dpi=160)
            plt.close(fig)
            card = (f"# {c['experiment_id']}\n\n"
                    f"Frozen {c['model']['name']} + Linear(384,8), seed 42; best epoch {epoch}.\n\n"
                    "comparison_v1: 2,800 source train images / 3,125 GT crops; "
                    "600 validation images / 680 GT crops. Geometry/padding fixed by TV1. "
                    "One deterministic feature per crop; no stochastic augmentation. "
                    "Loss averages crop CE within images then averages images. "
                    "Validation averages crop softmax vectors per source image.\n\n"
                    f"Validation accuracy: {result['metrics']['accuracy']!r}; macro-F1: {result['metrics']['macro_f1']!r}.\n\n"
                    "Intended use: research classification of eight SWG classes. "
                    "Scores are not calibrated; GT crops differ from detector crops. "
                    "This run does not establish independent Test performance, geographic transfer, "
                    "88% independent accuracy or seed stability. B3 reference remains unresolved. "
                    "Demo predictions must remain separate per detection box.\n\n"
                    f"Pretrained source: {c['model']['weights_source']}\n\n"
                    f"Pretrained SHA-256: {c['model']['weights_sha256']}\n\n"
                    f"Checkpoint SHA-256: {table['checkpoint']['sha256']}\n\n"
                    "See config.json, binding.json, validation.json, validation_comparison.json and reload report. "
                    "Do not treat this package as reproduced until the fresh reload report passes.\n")
            (run / 'MODEL_CARD.md').write_text(card, encoding='utf-8')
            d.atomic_json(run / 'handoff.json', h.build_handoff(run, checkpoint, c, binding, result))
            lines = ['| Model | Validation accuracy | Macro-F1 | Images / crops |', '|---|---:|---:|---:|']
            for r in [table['baseline'], table['candidate']]:
                lines.append(f"| {r['experiment_id']} | {r['accuracy']:.8f} | {r['macro_f1']:.8f} | 600 / 680 |")
            (run / 'validation_comparison.md').write_text('\n'.join(lines) + '\n\n' + table['claim'] + '\n', encoding='utf-8')
            # Separate process re-extracts EVERY validation crop without using the feature cache.
            attempt = run / ('reload_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
            command = [sys.executable, '-X', 'utf8', str(Path(__file__).resolve()), 'reload', '--checkpoint', str(checkpoint),
                       '--sha256', d.sha(checkpoint), '--output', str(attempt), '--device', c['runtime']['device']]
            completed = subprocess.run(command, check=False)
            passed = h.finish_handoff(run, attempt, completed.returncode == 0)
            d.atomic_json(run / 'status.json', {'status': 'COMPLETE' if passed else 'RELOAD_MISMATCH',
                                               'reload_report': str(attempt), 'checkpoint_sha256': d.sha(checkpoint)})
            d.require(passed, 'Reload did not reproduce the full validation reference; inspect evidence')
        except BaseException as exc:
            d.atomic_json(run / 'status.json', {'status': 'INTERRUPTED' if isinstance(exc, KeyboardInterrupt) else 'FAILED',
                                               'error': repr(exc), 'resume': 'Last complete epoch; partial epoch is replayed.'})
            raise


def reload_model(args):
    out = new_output(args.output)
    checkpoint = Path(args.checkpoint)
    d.require(d.sha(checkpoint) == args.sha256, 'Checkpoint SHA mismatch')
    # Establish deterministic mode before creating a CUDA context.
    d.seed_all(42)
    backbone, head, transform, payload = d.load_package(checkpoint, args.sha256, args.device, args.repo)
    rows, cmap, gate = d.read_release(verify_images=True)
    d.require(cmap == payload['class_map'] and gate == payload['binding']['data'], 'Reload data binding mismatch')
    parts = []
    bs = payload['config']['cache']['batch_size']
    with torch.inference_mode():
        for start in range(0, len(rows['val']), bs):
            x = torch.stack([d.crop_tensor(r, transform) for r in rows['val'][start:start + bs]]).to(args.device)
            parts.append(d.extract(backbone, x).float().cpu())
        # Same head evaluation batch as training, avoiding incidental GEMM shape changes.
        logits = head(torch.cat(parts).to(args.device)).cpu()
    actual = d.evaluate_logits(logits, rows['val'], cmap)
    report = d.compare_predictions(payload['validation'], actual)
    predictions_path = out.with_suffix('.predictions.json')
    new_output(predictions_path)
    d.atomic_json(predictions_path, actual)
    report.update(checkpoint_sha256=args.sha256, runtime=d.runtime(), device=args.device,
                  status='PASS' if report['passed'] else 'FAIL', evaluation_split='val',
                  manifest_sha256=h.manifest_hashes(gate), test_inference_performed=False,
                  fresh_process=True, validation_images=len(actual['image_predictions']),
                  validation_crops=len(actual['crop_predictions']), test_opened=False,
                  predictions_path=str(predictions_path), predictions_sha256=d.sha(predictions_path))
    d.atomic_json(out, report)
    print(json.dumps(report, indent=2))
    d.require(report['passed'], 'Full-precision reload differs; do not mark checkpoint reproduced')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    for action in ['pin', 'preflight', 'cache', 'train']:
        s = sub.add_parser(action)
        s.add_argument('--config', required=True, type=Path)
        if action in ('pin', 'preflight'):
            s.add_argument('--output', required=True, type=Path)
        if action == 'pin':
            s.add_argument('--repo', required=True)
            s.add_argument('--weights', required=True)
            s.add_argument('--source', required=True, help='Public source/model identifier, never a signed URL or token')
        if action == 'preflight':
            s.add_argument('--with-model', action='store_true')
        if action in ('cache', 'train'):
            s.add_argument('--protocol', required=True)
        if action == 'train':
            s.add_argument('--resume', action='store_true')
    s = sub.add_parser('reload')
    s.add_argument('--checkpoint', required=True)
    s.add_argument('--sha256', required=True)
    s.add_argument('--output', required=True, type=Path)
    s.add_argument('--device', choices=['cpu', 'cuda'], default='cuda')
    s.add_argument('--repo', help='Local architecture checkout on another machine, at pinned commit')
    args = p.parse_args()
    if args.action == 'pin':
        pin(args)
    elif args.action == 'preflight':
        preflight(args)
    elif args.action == 'cache':
        c, protocol, env, rows, cmap, gate = preparation(args)
        folder, _ = d.cache_features(c, rows, gate, env)
        print(folder)
    elif args.action == 'train':
        train(args)
    elif args.action == 'reload':
        reload_model(args)


if __name__ == '__main__':
    main()
