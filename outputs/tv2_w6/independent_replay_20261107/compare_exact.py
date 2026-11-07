import json, math, hashlib
from pathlib import Path

ROOT = Path.cwd()
E = ROOT / 'outputs/tv2_w6/independent_replay_20261107'
PKGS = ROOT / 'outputs/tv2_w6/independent_acceptance_20261107/received'

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def maxdelta(a, b):
    return max((abs(float(x) - float(y)) for ax, bx in zip(a, b) for x, y in zip(ax, bx)), default=0.0)

def compare(run):
    replay = load(E / f'replay_{run}.json')
    pkg = PKGS / run / (run + '_attempt01')
    producer = load(pkg / 'validation.json')

    prod_c = producer['crop_predictions']
    rep_c = replay['evaluation']['crop_predictions']
    prod_i = producer['image_predictions']
    rep_i = replay['evaluation']['image_predictions']

    ids_same = [x.get('crop_id') for x in rep_c] == [x.get('crop_id') for x in prod_c]
    image_ids_same = [x.get('image_id') for x in rep_i] == [x.get('image_id') for x in prod_i]

    crop_logits_mismatches = sum(x != y for a, b in zip(rep_c, prod_c) for x, y in zip(a['logits'], b['logits']))
    crop_prob_mismatches = sum(x != y for a, b in zip(rep_c, prod_c) for x, y in zip(a['probabilities'], b['probabilities']))
    image_prob_mismatches = sum(x != y for a, b in zip(rep_i, prod_i) for x, y in zip(a['probabilities'], b['probabilities']))

    crop_pred_class_mismatches = sum(
        max(range(len(a['probabilities'])), key=a['probabilities'].__getitem__) !=
        max(range(len(b['probabilities'])), key=b['probabilities'].__getitem__)
        for a, b in zip(rep_c, prod_c)
    )
    image_pred_class_mismatches = sum(a['y_pred'] != b['y_pred'] for a, b in zip(rep_i, prod_i))
    image_truth_mismatches = sum(a['y_true'] != b['y_true'] for a, b in zip(rep_i, prod_i))

    out = {
        'run_id': run,
        'replay_sha256': sha(E / f'replay_{run}.json'),
        'producer_validation_sha256': sha(pkg / 'validation.json'),
        'counts': {
            'replay_crops': len(rep_c),
            'producer_crops': len(prod_c),
            'replay_images': len(rep_i),
            'producer_images': len(prod_i)
        },
        'id_order_exact': {
            'crop': ids_same,
            'image': image_ids_same
        },
        'crop_logits': {
            'mismatch_values': crop_logits_mismatches,
            'values': sum(len(x['logits']) for x in rep_c),
            'max_abs_delta': maxdelta([x['logits'] for x in rep_c], [x['logits'] for x in prod_c])
        },
        'crop_probabilities': {
            'mismatch_values': crop_prob_mismatches,
            'values': sum(len(x['probabilities']) for x in rep_c),
            'max_abs_delta': maxdelta([x['probabilities'] for x in rep_c], [x['probabilities'] for x in prod_c])
        },
        'crop_predicted_class_mismatches': crop_pred_class_mismatches,
        'image_probabilities': {
            'mismatch_values': image_prob_mismatches,
            'values': sum(len(x['probabilities']) for x in rep_i),
            'max_abs_delta': maxdelta([x['probabilities'] for x in rep_i], [x['probabilities'] for x in prod_i])
        },
        'image_predicted_class_mismatches': image_pred_class_mismatches,
        'image_truth_mismatches': image_truth_mismatches
    }

    diffs = []
    def walk(a, b, path='metrics'):
        if isinstance(a, dict) and isinstance(b, dict):
            for k in sorted(set(a) | set(b)):
                if k not in a or k not in b:
                    diffs.append({'path': path + '.' + k, 'left': a.get(k), 'right': b.get(k)})
                    continue
                walk(a[k], b[k], path + '.' + k)
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                diffs.append({'path': path, 'left_length': len(a), 'right_length': len(b)})
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f'{path}[{i}]')
        elif a != b:
            diffs.append({
                'path': path,
                'producer': b,
                'replay': a,
                'absolute_delta': abs(a - b) if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
            })

    walk(replay['evaluation']['metrics'], producer['metrics'])

    out['metrics_exact'] = not diffs
    out['metric_mismatch_count'] = len(diffs)
    out['metric_mismatches'] = diffs[:30]
    out['prediction_exact'] = (
        ids_same and image_ids_same and
        crop_logits_mismatches == 0 and
        crop_prob_mismatches == 0 and
        image_prob_mismatches == 0 and
        crop_pred_class_mismatches == 0 and
        image_pred_class_mismatches == 0 and
        image_truth_mismatches == 0
    )
    out['exact_all_required'] = out['prediction_exact'] and out['metrics_exact']
    return out

report = {
    'comparison_policy': 'exact element equality; no tolerance',
    'runs': [compare('R3'), compare('R4')]
}
report['model_replay_status'] = 'PASS' if all(x['exact_all_required'] for x in report['runs']) else 'FAIL'
out_path = E / 'exact_comparison.json'
out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2, ensure_ascii=False))
