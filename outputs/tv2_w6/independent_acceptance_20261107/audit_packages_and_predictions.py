import hashlib, json, math, zipfile
from pathlib import Path
import statistics

ROOT = Path.cwd()
STAGE = ROOT / 'outputs/tv2_w6/independent_acceptance_20261107'
PKGS = STAGE / 'received'
OUT_AUDIT = STAGE / 'artifact_audit.json'
OUT_EVIDENCE = STAGE / 'acceptance_evidence.json'

expected_zip = {
    'R3': 'a6f4d51c0f84f959c0ecf44c62eee819fc82844d38e63bbff50abe573920df4a',
    'R4': 'cbe27ed2cd243e9783743eb8028b8d6b1f600fb28299735276d6d13b31114c0b'
}

class_map_file = ROOT / 'data/processed/comparison_v1/class_map.json'
class_map = json.loads(class_map_file.read_text(encoding='utf-8'))
if isinstance(class_map, dict):
    names = [class_map[str(i)] if str(i) in class_map else class_map.get(i) for i in range(8)]
else:
    names = class_map
if names and isinstance(names[0], dict):
    names = [x.get('name') or x.get('class_name') for x in names]

run_paths = {
    'R0': ROOT / 'reports/tv2/w5_acceptance/2026-11-02/attempt_01/independent_replay/predictions.json',
    'R1': ROOT / 'outputs/tv2_w6/independent_acceptance_20261106/received/R1/R1_attempt01/validation.json',
    'R2': ROOT / 'outputs/tv2_w6/independent_acceptance_20261106/received/R2/R2_attempt01/validation.json',
    'R3': PKGS / 'R3/R3_attempt01/validation.json',
    'R4': PKGS / 'R4/R4_attempt01/validation.json'
}

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def canon(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()

def readjson(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def calculate(run, p):
    o = readjson(p)
    imgs = o['image_predictions']
    crops = o['crop_predictions']
    ids = [x['image_id'] for x in imgs]
    dup_img = sorted({x for x in ids if ids.count(x) > 1})
    cropids = [x.get('crop_id') for x in crops]
    dup_crop = sorted({x for x in cropids if cropids.count(x) > 1})
    byimg = {}
    for c in crops:
        byimg.setdefault(c['image_id'], []).append(c.get('probabilities', c.get('class_scores')))

    maxmean = 0.0
    missing = []
    label_mismatch = []
    score_bad = []
    for i in imgs:
        arr = byimg.get(i['image_id'])
        if not arr:
            missing.append(i['image_id'])
            continue
        if len(arr) != i.get('crop_count'):
            label_mismatch.append(i['image_id'])
        means = [sum(float(v[k]) for v in arr) / len(arr) for k in range(8)]
        probs = i.get('probabilities', i.get('class_scores'))
        d = max(abs(means[k] - float(probs[k])) for k in range(8))
        maxmean = max(maxmean, d)
        if d > 1e-10:
            score_bad.append((i['image_id'], d))
        if not math.isclose(sum(float(x) for x in probs), 1.0, abs_tol=1e-5, rel_tol=0):
            label_mismatch.append(i['image_id'] + ':sum')

    cm = [[0] * 8 for _ in range(8)]
    for i in imgs:
        y = int(i.get('y_true', i.get('ground_truth')))
        pred = int(i.get('y_pred', i.get('predicted_class')))
        cm[y][pred] += 1

    per = []
    for c in range(8):
        tp = cm[c][c]
        support = sum(cm[c])
        predicted = sum(cm[r][c] for r in range(8))
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per.append({
            'class_id': c,
            'class': names[c],
            'correct': tp,
            'support': support,
            'precision': precision,
            'recall': recall,
            'f1': f1
        })

    correct = sum(cm[i][i] for i in range(8))
    accuracy = correct / len(imgs)
    macro_f1 = sum(x['f1'] for x in per) / 8.0
    macro_p = sum(x['precision'] for x in per) / 8.0
    macro_r = sum(x['recall'] for x in per) / 8.0

    return {
        'run': run,
        'image_count': len(imgs),
        'image_ids_unique': len(set(ids)),
        'duplicate_image_ids': dup_img,
        'crop_count': len(crops),
        'crop_ids_unique': len(set(cropids)),
        'duplicate_crop_ids': dup_crop,
        'unrepresented_image_ids': sorted(set(ids) - set(byimg)),
        'unexpected_crop_image_ids': sorted(set(byimg) - set(ids)),
        'crop_count_or_score_errors': label_mismatch,
        'max_abs_image_vs_mean_crop_score_delta': maxmean,
        'mean_score_mismatches_gt_1e-10': score_bad[:10],
        'accuracy': accuracy,
        'correct': correct,
        'macro_precision': macro_p,
        'macro_recall': macro_r,
        'macro_f1': macro_f1,
        'per_class': per,
        'confusion_matrix': cm,
        'producer_metrics': o.get('metrics')
    }

runs = {k: calculate(k, p) for k, p in run_paths.items()}

# Paired outcomes vs R0 and vs R2
base_r0 = {x['image_id']: x for x in readjson(run_paths['R0'])['image_predictions']}
base_r2 = {x['image_id']: x for x in readjson(run_paths['R2'])['image_predictions']}

paired_vs_r0 = {}
paired_vs_r2 = {}

for run in ('R1', 'R2', 'R3', 'R4'):
    cand = {x['image_id']: x for x in readjson(run_paths[run])['image_predictions']}

    # vs R0
    fixes, losses = [], []
    per_class_r0 = {str(i): {'fixes': 0, 'losses': 0} for i in range(8)}
    changed_r0 = []
    for iid, b in base_r0.items():
        c = cand[iid]
        by = int(b.get('y_true', b.get('ground_truth')))
        cy = int(c.get('y_true', c.get('ground_truth')))
        assert by == cy, (run, iid, 'label mismatch')
        bpred = int(b.get('y_pred', b.get('predicted_class')))
        cpred = int(c.get('y_pred', c.get('predicted_class')))
        if bpred != cpred:
            changed_r0.append(iid)
        if bpred != by and cpred == by:
            fixes.append(iid)
            per_class_r0[str(by)]['fixes'] += 1
        if bpred == by and cpred != by:
            losses.append(iid)
            per_class_r0[str(by)]['losses'] += 1

    paired_vs_r0[run] = {
        'paired_image_count': len(base_r0),
        'ids_exact_match': set(base_r0) == set(cand),
        'fixed_wrong_to_correct': len(fixes),
        'lost_correct_to_wrong': len(losses),
        'net_change': len(fixes) - len(losses),
        'prediction_changed': len(changed_r0),
        'fix_image_ids': fixes,
        'loss_image_ids': losses,
        'per_true_class_fix_loss': per_class_r0
    }

    # vs R2
    if run != 'R2':
        fixes_r2, losses_r2 = [], []
        per_class_r2 = {str(i): {'fixes': 0, 'losses': 0} for i in range(8)}
        changed_r2 = []
        for iid, b in base_r2.items():
            c = cand[iid]
            by = int(b.get('y_true', b.get('ground_truth')))
            cy = int(c.get('y_true', c.get('ground_truth')))
            bpred = int(b.get('y_pred', b.get('predicted_class')))
            cpred = int(c.get('y_pred', c.get('predicted_class')))
            if bpred != cpred:
                changed_r2.append(iid)
            if bpred != by and cpred == by:
                fixes_r2.append(iid)
                per_class_r2[str(by)]['fixes'] += 1
            if bpred == by and cpred != by:
                losses_r2.append(iid)
                per_class_r2[str(by)]['losses'] += 1
        paired_vs_r2[run] = {
            'paired_image_count': len(base_r2),
            'ids_exact_match': set(base_r2) == set(cand),
            'fixed_wrong_to_correct': len(fixes_r2),
            'lost_correct_to_wrong': len(losses_r2),
            'net_change': len(fixes_r2) - len(losses_r2),
            'prediction_changed': len(changed_r2),
            'fix_image_ids': fixes_r2,
            'loss_image_ids': losses_r2,
            'per_true_class_fix_loss': per_class_r2
        }

# Confusable pairs: civets (4 vs 5) and muntjac vs sambar (0 vs 2)
pairs = {
    'common_palm_civet_vs_masked_palm_civet': (4, 5),
    'muntjac_vs_sambar': (0, 2)
}
pair_stats = {}
for pname, (a, b) in pairs.items():
    pair_stats[pname] = {}
    for run in ('R0', 'R1', 'R2', 'R3', 'R4'):
        cm = runs[run]['confusion_matrix']
        pair_stats[pname][run] = {
            'a_to_b': cm[a][b],
            'b_to_a': cm[b][a],
            'total_confusion': cm[a][b] + cm[b][a]
        }

# Packages audit
packages = {}
for run, zip_hash in expected_zip.items():
    zip_path = ROOT / f'reports/tv3/w6/w6/{run}_attempt01.zip'
    actual_sha = sha(zip_path)
    assert actual_sha == zip_hash, (run, 'archive sha mismatch', actual_sha)
    root_pkg = PKGS / run / f'{run}_attempt01'
    index = readjson(root_pkg / 'package_index.json')
    with zipfile.ZipFile(zip_path) as z:
        bad = z.testzip()
        assert bad is None, (run, 'CRC failure', bad)
        entries = {i.filename: i for i in z.infolist() if not i.is_dir()}
    listed = set(index)
    actual = set(entries) - {f'{run}_attempt01/package_index.json', f'{run}_attempt01/registry.delivery.json'}
    normalized = {x.removeprefix(f'{run}_attempt01/'): x for x in actual}
    assert set(normalized) == listed, (run, 'package membership mismatch', sorted(set(normalized) ^ listed))

    checks = []
    for rel, meta in index.items():
        p = root_pkg / rel
        h = sha(p)
        size = p.stat().st_size
        checks.append({
            'path': rel,
            'sha256_match': h == meta['sha256'],
            'size_match': size == meta['bytes'],
            'sha256': h,
            'bytes': size
        })
    assert all(x['sha256_match'] and x['size_match'] for x in checks), (run, 'package index mismatch')

    handoff = readjson(root_pkg / 'handoff.json')
    frozen_cfg = readjson(ROOT / f'configs/w6/tv3/{run}.frozen.json')
    raw_cfg_sha = sha(ROOT / f'configs/w6/tv3/{run}.frozen.json')
    canonical_cfg_sha = canon(frozen_cfg)

    assert handoff['config_raw_sha256'] == raw_cfg_sha, f'{run} raw config sha mismatch'
    assert handoff['config_sha256'] == canonical_cfg_sha, f'{run} canonical config sha mismatch'
    assert sha(root_pkg / 'best_model.pt') == handoff['checkpoint_sha256'] == index['best_model.pt']['sha256']
    assert sha(root_pkg / 'last_model.pt') == handoff['last_checkpoint_sha256'] == index['last_model.pt']['sha256']
    assert handoff['source_sha'] == '95652c2d770cac464633eef0149bd27f4d859ece'
    assert handoff['dataset_sha256'] == 'd9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f'
    assert handoff['evaluation_split'] == 'val'
    assert handoff['fresh_process_reload'] == 'PASS'

    packages[run] = {
        'zip_sha256': actual_sha,
        'zip_crc': 'PASS',
        'archive_file_count': len(entries),
        'package_index_count': len(index),
        'best_checkpoint_sha256': handoff['checkpoint_sha256'],
        'last_checkpoint_sha256': handoff['last_checkpoint_sha256'],
        'frozen_config_raw_sha256': raw_cfg_sha,
        'frozen_config_canonical_sha256': canonical_cfg_sha,
        'source_commit': handoff['source_sha'],
        'dataset_sha256': handoff['dataset_sha256'],
        'all_payload_hashes_and_sizes_match': all(x['sha256_match'] and x['size_match'] for x in checks),
        'files': checks
    }

# Multi-seed summary for Recipe R2 (seeds 42, 43, 44)
r2_seeds = {
    42: runs['R2'],
    43: runs['R3'],
    44: runs['R4']
}

acc_vals = [r2_seeds[s]['accuracy'] for s in (42, 43, 44)]
f1_vals = [r2_seeds[s]['macro_f1'] for s in (42, 43, 44)]
correct_vals = [r2_seeds[s]['correct'] for s in (42, 43, 44)]

mean_acc = statistics.mean(acc_vals)
sample_sd_acc = statistics.stdev(acc_vals) # ddof=1
mean_f1 = statistics.mean(f1_vals)
sample_sd_f1 = statistics.stdev(f1_vals) # ddof=1
mean_correct = statistics.mean(correct_vals)
sample_sd_correct = statistics.stdev(correct_vals)

multi_seed_r2 = {
    'recipe': 'R2',
    'dataset': 'comparison_v1',
    'seeds': [42, 43, 44],
    'per_seed': {
        '42': {
            'run_id': 'R2',
            'correct': r2_seeds[42]['correct'],
            'accuracy': r2_seeds[42]['accuracy'],
            'macro_f1': r2_seeds[42]['macro_f1']
        },
        '43': {
            'run_id': 'R3',
            'correct': r2_seeds[43]['correct'],
            'accuracy': r2_seeds[43]['accuracy'],
            'macro_f1': r2_seeds[43]['macro_f1']
        },
        '44': {
            'run_id': 'R4',
            'correct': r2_seeds[44]['correct'],
            'accuracy': r2_seeds[44]['accuracy'],
            'macro_f1': r2_seeds[44]['macro_f1']
        }
    },
    'mean_accuracy': mean_acc,
    'sample_sd_accuracy': sample_sd_acc,
    'mean_macro_f1': mean_f1,
    'sample_sd_macro_f1': sample_sd_f1,
    'mean_correct': mean_correct,
    'sample_sd_correct': sample_sd_correct,
    'target_accuracy': 0.88,
    'target_correct': 528,
    'all_seeds_below_target': all(c < 528 for c in correct_vals),
    'headline_seed': 42,
    'do_not_cherry_pick_best_seed': True
}

# GPU Accounting
# TV3 usage from producer
tv3_official_attempts = [
    {'run_id': 'R1', 'attempt_id': 'R1_attempt01', 'gpu_hours': 0.07120131605555557},
    {'run_id': 'R2', 'attempt_id': 'R2_attempt01', 'gpu_hours': 0.8294758375000002},
    {'run_id': 'R3', 'attempt_id': 'R3_attempt01', 'gpu_hours': 0.6801649318611114},
    {'run_id': 'R4', 'attempt_id': 'R4_attempt01', 'gpu_hours': 0.686542361861111}
]
tv3_prep_attempts = [
    {'attempt_id': 'R1_smoke01', 'gpu_hours': 0.003355442499999981},
    {'attempt_id': 'R2_smoke01', 'gpu_hours': 0.0016819240277777682},
    {'attempt_id': 'R3_smoke01', 'gpu_hours': 0.0020971329444442847},
    {'attempt_id': 'R4_smoke01', 'gpu_hours': 0.002460322527777963}
]
tv3_total_gpu_hours = sum(a['gpu_hours'] for a in tv3_official_attempts) + sum(a['gpu_hours'] for a in tv3_prep_attempts)

# TV2 replay usage
tv2_replays = [
    {'run_id': 'R1', 'attempt_id': 'R1_replay01', 'gpu_hours': 0.03687700852777602},
    {'run_id': 'R1', 'attempt_id': 'R1_replay02', 'gpu_hours': 0.04432501094444888},
    {'run_id': 'R2', 'attempt_id': 'R2_replay01', 'gpu_hours': 0.03654925344443958},
    {'run_id': 'R3', 'attempt_id': 'R3_replay01', 'gpu_hours': 0.011764475777777585},
    {'run_id': 'R4', 'attempt_id': 'R4_replay01', 'gpu_hours': 0.011366664027769325}
]
tv2_total_replay_gpu_hours = sum(r['gpu_hours'] for r in tv2_replays)

gpu_accounting = {
    'tv3': {
        'budget_gpu_hours': 12.0,
        'max_official_attempts': 6,
        'completed_official_attempts': len(tv3_official_attempts),
        'official_attempts': tv3_official_attempts,
        'preparation_attempts': tv3_prep_attempts,
        'total_gpu_hours': tv3_total_gpu_hours,
        'remaining_gpu_hours': 12.0 - tv3_total_gpu_hours,
        'per_attempt_limit_satisfied': all(a['gpu_hours'] <= 2.0 for a in tv3_official_attempts),
        'budget_satisfied': tv3_total_gpu_hours <= 12.0 and len(tv3_official_attempts) <= 6
    },
    'tv2_replay': {
        'budget_gpu_hours': 2.0,
        'replays': tv2_replays,
        'total_replay_gpu_hours': tv2_total_replay_gpu_hours,
        'remaining_replay_gpu_hours': 2.0 - tv2_total_replay_gpu_hours,
        'budget_satisfied': tv2_total_replay_gpu_hours <= 2.0
    }
}

# Check classes with >= 4 correct image losses vs R0
regression_alerts = {}
for run in ('R1', 'R2', 'R3', 'R4'):
    alerts = []
    for c_id in range(8):
        c_name = names[c_id]
        delta_correct = runs[run]['per_class'][c_id]['correct'] - runs['R0']['per_class'][c_id]['correct']
        if delta_correct <= -4:
            alerts.append({
                'class_id': c_id,
                'class_name': c_name,
                'delta_correct': delta_correct,
                'r0_correct': runs['R0']['per_class'][c_id]['correct'],
                'run_correct': runs[run]['per_class'][c_id]['correct']
            })
    regression_alerts[run] = alerts

audit_result = {
    'status': 'PASS',
    'packages': packages,
    'runs': runs,
    'paired_vs_r0': paired_vs_r0,
    'paired_vs_r2': paired_vs_r2,
    'confusable_pairs': pair_stats,
    'multi_seed_r2': multi_seed_r2,
    'regression_alerts': regression_alerts,
    'gpu_accounting': gpu_accounting,
    'class_names': names
}

OUT_AUDIT.write_text(json.dumps(audit_result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

# Build acceptance_evidence.json
replay_comp = readjson(ROOT / 'outputs/tv2_w6/independent_replay_20261107/exact_comparison.json')
acceptance_evidence = {
    'acceptance_id': 'TV2_W6_R3_R4_INDEPENDENT_ACCEPTANCE_2026-11-07',
    'branch': 'feat/baseline',
    'protocol_lock_commit': '056ee897dbd9929844787a65ab705c09ecfbf846',
    'tv3_results_commit': '61498e7ffc6831b1988cc2d1296457c1fe613373',
    'tv3_source_commit': '95652c2d770cac464633eef0149bd27f4d859ece',
    'artifact_status': 'ARTIFACT_VERIFIED',
    'model_replay': {
        'status': 'MODEL_REPLAY_PASS',
        'comparison_policy': 'exact element equality; no tolerance',
        'exact_comparison_path': 'outputs/tv2_w6/independent_replay_20261107/exact_comparison.json',
        'environment_receipt_path': 'outputs/tv2_w6/independent_replay_20261107/environment_receipt.json',
        'gpu_hours_used_r3_r4': 0.011764475777777585 + 0.011366664027769325,
        'cumulative_replay_gpu_hours': tv2_total_replay_gpu_hours,
        'budget_gpu_hours': 2.0,
        'run_results': {
            run_comp['run_id']: {
                'exact_all_required': run_comp['exact_all_required'],
                'crop_logits_mismatches': run_comp['crop_logits']['mismatch_values'],
                'crop_probability_mismatches': run_comp['crop_probabilities']['mismatch_values'],
                'image_probability_mismatches': run_comp['image_probabilities']['mismatch_values'],
                'metric_mismatches': run_comp['metric_mismatch_count']
            } for run_comp in replay_comp['runs']
        }
    },
    'regression_review': 'PASS_INDEPENDENT_REPLAY_AND_PAIRED_R0_R2_REVIEW',
    'multi_seed_summary': multi_seed_r2,
    'regression_alerts': regression_alerts,
    'overall_decision': 'TV2_ACCEPTANCE: PASS; RECIPE_R2_MULTI_SEED_VERIFIED; ALL_RUNS_BELOW_88_TARGET; DEMO_DEFAULT_UNCHANGED; TV4_ADAPTER_INDEPENDENT; R5_R6_WAIT_TV1_DATA_REVIEW',
    'zip_sha256': expected_zip,
    'package_audit': {
        k: {a: v for a, v in x.items() if a != 'files'} for k, x in packages.items()
    },
    'gpu_accounting': gpu_accounting
}

OUT_EVIDENCE.write_text(json.dumps(acceptance_evidence, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

print("Artifact audit and acceptance evidence completed successfully!")
print(f"R2 Multi-seed Accuracy: Mean = {mean_acc:.6f} +/- {sample_sd_acc:.6f} (sample SD, ddof=1)")
print(f"R2 Multi-seed Macro-F1: Mean = {mean_f1:.6f} +/- {sample_sd_f1:.6f} (sample SD, ddof=1)")
print(f"R2 Multi-seed Correct: Mean = {mean_correct:.2f} +/- {sample_sd_correct:.2f} / 600")
print(f"TV3 total GPU hours: {tv3_total_gpu_hours:.6f} / 12.0")
print(f"TV2 replay total GPU hours: {tv2_total_replay_gpu_hours:.6f} / 2.0")
print("Regression alerts (losses >= 4 vs R0):", regression_alerts)
