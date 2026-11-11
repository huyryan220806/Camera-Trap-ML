import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PKG = OUT / 'received'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

producer = read(PKG / 'validation.json')
replay = read(OUT / 'replay.json')['evaluation']
assert len(producer['crop_predictions']) == len(replay['crop_predictions']) == 680
assert len(producer['image_predictions']) == len(replay['image_predictions']) == 600

def vector_result(key, field):
    a, b = replay[key], producer[key]
    assert [r['crop_id' if key == 'crop_predictions' else 'image_id'] for r in a] == [r['crop_id' if key == 'crop_predictions' else 'image_id'] for r in b]
    diffs = [abs(x-y) for ra, rb in zip(a,b) for x,y in zip(ra[field], rb[field])]
    return {'values':len(diffs), 'mismatches':sum(d != 0 for d in diffs), 'max_abs_delta':max(diffs, default=0)}

comparison = {
    'policy':'exact element equality, atol=0, rtol=0; same pinned runtime',
    'crop_logits':vector_result('crop_predictions','logits'),
    'crop_probabilities':vector_result('crop_predictions','probabilities'),
    'image_probabilities':vector_result('image_predictions','probabilities'),
    'crop_id_order_exact':True, 'image_id_order_exact':True,
    'crop_predicted_class_mismatches':sum(max(range(8),key=a['probabilities'].__getitem__) != max(range(8),key=b['probabilities'].__getitem__) for a,b in zip(replay['crop_predictions'],producer['crop_predictions'])),
    'image_predicted_class_mismatches':sum(a['y_pred'] != b['y_pred'] for a,b in zip(replay['image_predictions'],producer['image_predictions'])),
    'image_truth_mismatches':sum(a['y_true'] != b['y_true'] for a,b in zip(replay['image_predictions'],producer['image_predictions'])),
    'metrics_exact':replay['metrics'] == producer['metrics'],
    'replay_sha256':sha(OUT / 'replay.json'),
    'producer_validation_sha256':sha(PKG / 'validation.json')}

# Artifact-level: independently recalculate image means, predictions, CM and metrics.
crops = producer['crop_predictions']
images = producer['image_predictions']
groups = defaultdict(list)
for row in crops:
    assert len(row['probabilities']) == 8 and abs(sum(row['probabilities'])-1) <= 1e-5
    groups[row['image_id']].append(row['probabilities'])
for row in images:
    p = [sum(v[k] for v in groups[row['image_id']])/len(groups[row['image_id']]) for k in range(8)]
    assert all(abs(x-y) <= 1e-10 for x,y in zip(p,row['probabilities']))
    assert row['crop_count'] == len(groups[row['image_id']])
    assert row['y_pred'] == max(range(8),key=row['probabilities'].__getitem__)
cm = [[0]*8 for _ in range(8)]
for row in images:
    cm[row['y_true']][row['y_pred']] += 1
assert cm == producer['metrics']['confusion_matrix']
f1 = []
for k in range(8):
    tp = cm[k][k]
    f1.append(2*tp/(sum(cm[k])+sum(r[k] for r in cm)))
accuracy = sum(cm[k][k] for k in range(8))/600
macro_f1 = sum(f1)/8
assert abs(accuracy-producer['metrics']['accuracy']) <= 1e-10
assert abs(macro_f1-producer['metrics']['macro_f1']) <= 1e-10

r0_path = ROOT / 'reports/tv2/w5_acceptance/2026-11-02/attempt_01/tv2_predictions.jsonl'
assert sha(r0_path) == '9be94d303882476202a653bbd9b1d89d8bfa48c4f7114ccd193c84f5de1ef3b7'
r0 = {r['image_id']:r for r in (json.loads(s) for s in r0_path.read_text(encoding='utf-8').splitlines() if s)}
r6 = {r['image_id']:r for r in images}
assert len(r0) == len(r6) == 600 and set(r0) == set(r6)
paired = {'r0_correct_r6_wrong':[], 'r0_wrong_r6_correct':[], 'both_correct':[], 'both_wrong':[]}
r0_cm = [[0]*8 for _ in range(8)]
for iid in sorted(r0):
    a,b = r0[iid],r6[iid]
    assert a['ground_truth'] == b['y_true']
    ac = a['ground_truth'] == a['predicted_class']
    bc = b['y_true'] == b['y_pred']
    paired['both_correct' if ac and bc else 'both_wrong' if not ac and not bc else 'r0_correct_r6_wrong' if ac else 'r0_wrong_r6_correct'].append(iid)
    r0_cm[a['ground_truth']][a['predicted_class']] += 1
assert sum(r0_cm[k][k] for k in range(8)) == 507
assert sum(cm[k][k] for k in range(8)) == 519
per_class_delta = [cm[k][k]-r0_cm[k][k] for k in range(8)]
assert all(d > -4 for d in per_class_delta)
comparison['artifact_level'] = {'image_mean_atol':1e-10,'probability_sum_atol':1e-5,'metric_arithmetic_atol':1e-10,
                                 'accuracy':accuracy,'macro_f1':macro_f1,'correct':519,'r0_correct':507,
                                 'per_class_correct_delta_vs_r0':per_class_delta}
comparison['paired_vs_r0'] = {k:len(v) for k,v in paired.items()}
comparison['paired_ids'] = paired
comparison['pass_exact'] = all(comparison[k]['mismatches']==0 for k in ('crop_logits','crop_probabilities','image_probabilities')) and comparison['crop_predicted_class_mismatches']==0 and comparison['image_predicted_class_mismatches']==0 and comparison['image_truth_mismatches']==0 and comparison['metrics_exact']
(OUT / 'exact_comparison.json').write_text(json.dumps(comparison,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in comparison.items() if k!='paired_ids'},indent=2))
