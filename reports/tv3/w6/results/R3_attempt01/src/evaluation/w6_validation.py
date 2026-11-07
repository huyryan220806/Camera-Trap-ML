"""W6 artifact-only gates. No model loading, training, downloads or Test reader.

Registry approval fields are evidence references, not authenticated signatures.
Dataset peer review and model replay remain separate human-reviewed decisions.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

from . import w5_validation as w5

ROOT = Path(__file__).resolve().parents[2]
R0_SHA = 'acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3'
R0_SOURCE = 'aa64fd7661827af78ddec4e3e0155b2b9c87b9e2'
R0_CONFIG_RAW_SHA = 'e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce'
EXPANSION_SHA = 'a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5'
SEEDS = [42, 42, 42, 43, 44, 42, 43]
STATUSES = ('REGISTERED', 'CONDITIONAL', 'RUNNING', 'COMPLETED', 'FAILED', 'OOM', 'STOPPED')


def digest(value):
    """W6 config identity: sorted compact UTF-8 JSON, no newline (not W5 digest)."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def pin(value, size=64):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{%d}' % size, value) is not None


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_recipe_config(config, recipe):
    """Check plan invariants; unspecified optimizer/runtime details stay DRAFT."""
    w5.require(config.get('status') in ('DRAFT','FROZEN'), 'Unknown config status')
    p=config['preprocessing']
    w5.require(p == dict(color='RGB',exif_transpose=False,padding=0,bbox='frozen_integer_xyxy_exclusive',
        resize=[256,256],interpolation='bilinear',antialias=True,resize_dtype='uint8',output_dtype='float32',
        scale=True,mean=[.485,.456,.406],std=[.229,.224,.225]), 'DINO preprocessing mismatch')
    w5.require(config['init_checkpoint_sha256'] == R0_SHA and config['backbone'] == 'dinov3_vits16' and
               config['num_classes'] == 8 and config['drop_last'] is False and
               config['loss'] == 'mean_parent_mean_crop_ce_once' and config['selection'] == 'image_macro_f1' and
               config['checkpoint_tie'] == 'earliest_epoch', 'Recipe common invariant mismatch')
    w5.require(config['runtime']['precision'] == 'FP32' and config['runtime']['amp'] is False and
               config['runtime']['tf32'] is False, 'Precision mismatch')
    if recipe == 'R1':
        w5.require(config['pooling'] == 'concat_x_norm_clstoken_mean_x_norm_patchtokens' and
                   config['feature_dim'] == 768 and config['register_tokens'] is False and
                   config['trainable'] == ['head'], 'R1 pooling/trainable mismatch')
        w5.require(config['optimizer'] == dict(name='SGD',lr=.01,momentum=.9,weight_decay=.0001,
                   nesterov=False,dampening=0) and config['epochs'] == 50 and config['patience'] == 7 and
                   config['parent_batch'] == 32 and config['scheduler'] == dict(name='cosine',epochs=50,
                   eta_min=0,step='after_validation'), 'R1 SGD/batch/schedule mismatch')
        w5.require(config['cache']['enabled'] is True and config['cache']['feature_dim'] == 768 and
                   config['augmentation'] == dict(horizontal_flip=0,vertical_flip=0,random_crop=False),
                   'R1 cache/augmentation mismatch')
    elif recipe == 'R2':
        w5.require(config['pooling'] == 'x_norm_clstoken' and config['feature_dim'] == 384 and
                   config['trainable'] == ['last_2_blocks','final_norm','head'], 'R2 trainable mask mismatch')
        w5.require(config['optimizer'] == dict(name='AdamW',backbone_lr=1e-5,head_lr=1e-4,
                   weight_decay=.01,no_decay=['bias','norm']) and config['epochs'] == 20 and
                   config['patience'] == 5 and config['scheduler'] == dict(name='warmup_then_cosine',
                   warmup_epochs=2,epochs=20), 'R2 AdamW/schedule mismatch')
        w5.require(config['parent_batch'] == 16 and type(config['crop_microbatch']) is int and
                   0 < config['crop_microbatch'] <= 8 and config['cache']['enabled'] is False and
                   config['final_parent_batch_denominator'] == 'actual_parent_count' and
                   config['augmentation'] == dict(horizontal_flip=.5,vertical_flip=0,random_crop=False),
                   'R2 parent weighting/cache/augmentation mismatch')
    else:
        w5.require(recipe == 'R0', 'Unknown recipe')


def validate_registry(registry, root=ROOT):
    """Validate structure and budgets, including failed attempts; never mutates."""
    import jsonschema
    jsonschema.Draft202012Validator(w5.read_json(Path(root) / 'contracts/w6_registry.schema.json')).validate(registry)
    w5.require(registry['budgets'] == dict(max_new_official_attempts=6, tv3_gpu_hours=12,
                per_attempt_gpu_hours=2, tv2_replay_gpu_hours=2), 'Unregistered budget')
    runs = registry['runs']
    w5.require([r['run_id'] for r in runs] == ['R%d' % i for i in range(7)], 'Need ordered R0-R6 exactly once')
    w5.require([r['seed'] for r in runs] == SEEDS, 'Unregistered seed')
    r0 = runs[0]
    w5.require(r0['status'] == 'REFERENCE' and not r0['attempts'] and
               r0['checkpoint_sha256'] == R0_SHA and r0['metrics'] == dict(
                   accuracy=0.845, macro_f1=0.8444008279545706), 'R0 immutable reference')
    preparations = registry['tv3_preparation_attempts']
    w5.require(len({p['attempt_id'] for p in preparations}) == len(preparations), 'Duplicate preparation attempt')
    w5.require(all(finite(p['gpu_hours']) and p['gpu_hours'] >= 0 for p in preparations), 'Invalid preparation usage')
    total_hours = sum(p['gpu_hours'] for p in preparations)
    attempts = []
    for index, run in enumerate(runs):
        expected_dataset = 'train_expansion_w6_v1' if index >= 5 else 'comparison_v1'
        w5.require(run['dataset'] == expected_dataset and run['dataset_sha256'] == (
            EXPANSION_SHA if index >= 5 else w5.PROVENANCE), 'Dataset identity mismatch')
        if index == 0:
            w5.require(run['config_path'] == 'configs/dinov3_lp_w5.local.json' and run['source_sha'] == R0_SOURCE,
                       'R0 source/config identity mismatch')
            config_path = confined(root,run['config_path'])
            w5.require(w5.sha256(config_path) == R0_CONFIG_RAW_SHA and
                       digest(w5.read_json(config_path)) == run['config_sha256'], 'R0 config SHA mismatch')
            continue
        if run['config_path'] is not None:
            config_path = confined(root, run['config_path'])
            w5.require(config_path.is_relative_to((Path(root)/'configs/w6').resolve()), 'W6 config path required')
            config = w5.read_json(config_path)
            w5.require(digest(config) == run['config_sha256'], 'Config SHA mismatch')
            w5.require(config['run_id'] == run['run_id'] and config['seed'] == run['seed'], 'Config run/seed mismatch')
            w5.require(config['dataset'] == run['dataset'] and config['dataset_sha256'] == run['dataset_sha256'],
                       'Config dataset mismatch')
            validate_recipe_config(config,run['recipe'])
        w5.require(index not in (1,2) or run['recipe'] == 'R%d' % index, 'Recipe/run mismatch')
        w5.require(run['status'] in STATUSES, 'Invalid new-run status')
        w5.require(run['metrics'] is None or run['status'] == 'COMPLETED', 'Metrics require completed run')
        w5.require(run['metrics'] is None or all(finite(v) and 0 <= v <= 1 for v in run['metrics'].values()),
                   'Nonfinite metric')
        if run['status'] in ('REGISTERED', 'CONDITIONAL'):
            w5.require(not run['attempts'] and run['checkpoint_sha256'] is None and run['metrics'] is None,
                       'Unstarted run has execution artifacts')
        for attempt in run['attempts']:
            attempts.append(attempt['attempt_id'])
            hours = attempt['gpu_hours']
            w5.require(hours is None or finite(hours) and 0 <= hours <= 2, 'Per-attempt GPU budget exceeded')
            total_hours += hours or 0
        if run['attempts'] or run['status'] in ('RUNNING', 'COMPLETED', 'FAILED', 'OOM', 'STOPPED'):
            w5.require(run['attempts'], 'Execution must retain attempt accounting')
            official_gate(registry, run)
        if run['status'] == 'COMPLETED':
            w5.require(pin(run['checkpoint_sha256']) and run['metrics'] is not None and run['evidence_paths'],
                       'Completed run missing result/evidence')
            w5.require(run['attempts'][-1]['status'] == 'COMPLETED' and
                       all(a['gpu_hours'] is not None for a in run['attempts']),
                       'Completed run missing final completion/measured GPU usage')
    w5.require(len(attempts) == len(set(attempts)) <= 6, 'Official attempts duplicate/exceed six')
    w5.require(total_hours <= 12, 'TV3 GPU budget exceeded')
    replays = registry['replay_attempts']
    w5.require(len({r['attempt_id'] for r in replays}) == len(replays), 'Duplicate replay attempt')
    w5.require(all(finite(r['gpu_hours']) and r['gpu_hours'] >= 0 for r in replays) and
               sum(r['gpu_hours'] for r in replays) <= 2, 'TV2 replay budget exceeded')
    return dict(status='VALID', protocol_status=registry['protocol_status'],
                official_attempts=len(attempts), measured_tv3_gpu_hours=total_hours,
                measured_tv3_preparation_gpu_hours=sum(p['gpu_hours'] for p in preparations),
                unmeasured_attempts=sum(a['gpu_hours'] is None for r in runs for a in r['attempts']),
                measured_tv2_replay_gpu_hours=sum(r['gpu_hours'] for r in replays))


def official_gate(registry, run):
    w5.require(registry['protocol_status'] == 'APPROVED', 'BLOCKED: protocol DRAFT')
    w5.require(all(registry['approvals'].get(k) for k in ('TV2', 'TV3')) and
               registry['freeze_evidence'] and registry['smoke_evidence'], 'BLOCKED: approval/freeze/smoke missing')
    w5.require(pin(run['source_sha'], 40) and pin(run['config_sha256']) and run['config_path'] and
               all(run['approvals'].get(k) for k in ('TV2', 'TV3')), 'BLOCKED: run source/config/approval missing')
    w5.require(run['recipe'] in ('R0', 'R1', 'R2'), 'BLOCKED: unresolved recipe')
    if run['run_id'] in ('R3', 'R4'):
        decision = registry['recipe_selection']
        w5.require(decision and decision['recipe'] == run['recipe'] and decision['improves_r0'] is True and
                   decision['evidence_path'], 'BLOCKED: seed repeats require winning recipe')
    if run['run_id'] in ('R5', 'R6'):
        review = registry['data_review']
        w5.require(review['status'] == 'PASS' and review['release_sha256'] == EXPANSION_SHA and
                   review['evidence_path'], 'BLOCKED: expansion not accepted by TV2')
        w5.require(registry['recipe_selection'] and
                   registry['recipe_selection']['recipe'] == run['recipe'] and
                   registry['recipe_selection']['evidence_path'], 'BLOCKED: expansion recipe/fallback decision missing')


def load_validation(root=ROOT):
    parents, crops, hashes = w5.load_frozen_validation(root)
    w5.require((len(parents), len(crops)) == (600, 680), 'Need 600 images / 680 crops')
    w5.require(Counter(r['class_id'] for r in parents) == Counter({i: 75 for i in range(8)}), 'Need 75 images/class')
    return parents, crops, hashes


def confined(root, relative):
    w5.require(isinstance(relative, str) and relative.strip() and not Path(relative).is_absolute(), 'Need relative artifact path')
    result = (Path(root) / relative).resolve()
    w5.require(result.is_relative_to(Path(root).resolve()), 'Artifact outside package')
    return result


def verify_submission(registry, run_id, handoff, package, checkpoint, root=ROOT):
    """Called BEFORE prediction files are opened. Artifact audit is not replay."""
    validate_registry(registry, root)
    run = next((r for r in registry['runs'][1:] if r['run_id'] == run_id), None)
    w5.require(run is not None, 'Only new registered W6 runs accepted')
    official_gate(registry, run)
    w5.require(run['status'] == 'COMPLETED', 'Need completed handoff')
    parents, crops, hashes = load_validation(root)
    for key, expected in dict(run_id=run_id, seed=run['seed'], checkpoint_sha256=run['checkpoint_sha256'],
            config_sha256=run['config_sha256'], source_sha=run['source_sha'],
            dataset_sha256=run['dataset_sha256'], train_dataset=run['dataset'],
            val_dataset='comparison_v1', evaluation_split='val', class_order=w5.CLASSES,
            manifest_sha256=hashes, aggregation='mean_crop_softmax_then_argmax').items():
        w5.require(handoff.get(key) == expected, 'Handoff identity mismatch: ' + key)
    w5.require(w5.sha256(checkpoint) == run['checkpoint_sha256'], 'Checkpoint bytes mismatch')
    w5.require(type(handoff.get('checkpoint_bytes')) is int and
               handoff['checkpoint_bytes'] == Path(checkpoint).stat().st_size, 'Checkpoint size mismatch')
    artifacts = handoff.get('artifacts', {})
    for name in ('config', 'source_index', 'training_log', 'runtime', 'crop_predictions', 'image_predictions', 'reload_report'):
        entry = artifacts.get(name, {})
        path = confined(package, entry.get('path'))
        w5.require(pin(entry.get('sha256')) and w5.sha256(path) == entry['sha256'], 'Artifact SHA mismatch: ' + name)
    config = w5.read_json(confined(package, artifacts['config']['path']))
    w5.require(digest(config) == run['config_sha256'], 'Package config digest mismatch')
    w5.require(config.get('status') == 'FROZEN' and config.get('runtime',{}).get('source_sha') == run['source_sha'] and
               config.get('runtime',{}).get('runtime_lock'), 'Training config/runtime not frozen')
    sources = w5.read_json(confined(package, artifacts['source_index']['path']))
    w5.require(sources.get('commit') == run['source_sha'] and sources.get('files_sha256'), 'Source index identity mismatch')
    for relative, expected in sources['files_sha256'].items():
        w5.require(pin(expected) and w5.sha256(confined(package,relative)) == expected, 'Source file SHA mismatch')
    runtime = w5.read_json(confined(package,artifacts['runtime']['path']))
    w5.require(digest(runtime) == config['runtime']['runtime_lock'], 'Runtime lock mismatch')
    reload = w5.read_json(confined(package, artifacts['reload_report']['path']))
    w5.require(reload.get('status') == 'PASS' and reload.get('fresh_process') is True and
               reload.get('checkpoint_sha256') == run['checkpoint_sha256'] and
               reload.get('evaluation_split') == 'val' and reload.get('test_inference_performed') is False and
               reload.get('manifest_sha256') == hashes and reload.get('source_sha') == run['source_sha'] and
               reload.get('config_sha256') == run['config_sha256'] and reload.get('runtime_sha256') == digest(runtime) and
               reload.get('comparison_policy') == 'exact' and reload.get('exact_predictions_and_metrics') is True,
               'Invalid producer reload receipt')
    return run, parents, crops


def evaluate(crop_predictions, image_predictions, parents, crops, run_id, checkpoint_sha256):
    """Reuse W5 mean-softmax and all-eight-class arithmetic; verify saved vectors."""
    generated = w5.aggregate(crop_predictions, parents, crops, run_id, checkpoint_sha256)
    result = w5.audit_predictions(image_predictions, parents, crops, run_id, checkpoint_sha256)
    saved = w5.unique(image_predictions, 'image_id')
    for row in generated:
        actual = saved[row['image_id']]
        w5.require(row['predicted_class'] == actual['predicted_class'] and
                   all(abs(a-b) <= 1e-10 for a,b in zip(row['class_scores'], actual['class_scores'])),
                   'Saved image vector differs from crop aggregation')
    return result


def paired_report(reference, candidate, parents, crops, run_id, checkpoint_sha256):
    ref = w5.audit_predictions(reference, parents, crops, 'DINOv3_LP_run01', R0_SHA)
    actual = w5.audit_predictions(candidate, parents, crops, run_id, checkpoint_sha256)
    old_pairs = w5.compare_predictions(reference, candidate)
    pairs = {k.replace('b2_', 'r0_'): v for k,v in old_pairs.items()}
    cm, before = actual['confusion_matrix'], ref['confusion_matrix']
    return dict(paired_outcomes=pairs, metric_delta={k: actual['metrics'][k]-v for k,v in ref['metrics'].items()},
        recall_regressions=[dict(class_id=i, lost_correct=before[i][i]-cm[i][i],
                                 recall_delta=actual['per_class'][i]['recall']-ref['per_class'][i]['recall'])
                            for i in range(8) if before[i][i]-cm[i][i] >= 4],
        confusion_pairs={name: dict(r0=before[a][b]+before[b][a], candidate=cm[a][b]+cm[b][a])
                         for name,a,b in [('common_masked_civet',4,5), ('muntjac_sambar',0,2)]})


def select_seed42(candidates):
    """Input rows must come from verified audits; latency uses one benchmark setup."""
    w5.require(candidates and all(c['run_id'] in ('R1','R2') and c['seed'] == 42 for c in candidates),
               'Select only R1/R2 seed 42')
    w5.require(len({c['run_id'] for c in candidates}) == len(candidates), 'Duplicate candidate')
    for c in candidates:
        w5.require(all(finite(c['metrics'][k]) and 0 <= c['metrics'][k] <= 1 for k in ('macro_f1','accuracy')),
                   'Invalid candidate metrics')
    tied = candidates
    for key in ('macro_f1', 'accuracy'):
        best = max(c['metrics'][key] for c in tied)
        tied = [c for c in tied if c['metrics'][key] == best]
    if len(tied) > 1:
        w5.require(all(finite(c.get('inference_cost_ms')) and c['inference_cost_ms'] > 0 and
                       c.get('benchmark_identity') for c in tied) and
                   len({c['benchmark_identity'] for c in tied}) == 1, 'Cost tie unresolved: need comparable benchmark')
        best_cost = min(c['inference_cost_ms'] for c in tied)
        tied = [c for c in tied if c['inference_cost_ms'] == best_cost]
    return min(tied, key=lambda c: int(c['run_id'][1:]))['run_id']


def seed_summary(rows):
    """Never replace seed42 headline with best seed; incomplete groups stay explicit."""
    w5.require(rows and len({r['seed'] for r in rows}) == len(rows) and
               all(r['seed'] in (42,43,44) for r in rows), 'Duplicate/unregistered seeds')
    w5.require(len({(r['recipe'],r['dataset']) for r in rows}) == 1, 'Do not pool recipes/datasets')
    w5.require(any(r['seed'] == 42 for r in rows), 'Seed42 headline required')
    w5.require(all(finite(r['metrics'][k]) and 0 <= r['metrics'][k] <= 1 for r in rows
                   for k in ('accuracy', 'macro_f1')), 'Invalid seed metric')
    return dict(headline=next(r for r in rows if r['seed'] == 42), per_seed=sorted(rows,key=lambda r:r['seed']),
                n=len(rows), missing_seeds=sorted({42,43,44}-{r['seed'] for r in rows}),
                statistics={k: dict(mean=statistics.mean(r['metrics'][k] for r in rows),
                    sample_sd=statistics.stdev(r['metrics'][k] for r in rows) if len(rows)>1 else None)
                    for k in ('accuracy','macro_f1')})
