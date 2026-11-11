import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PKG = OUT / 'received'
DEST = ROOT / 'reports/tv2/TV2_W6_R6_MODEL_REPLAY_RECEIPT_2026-11-10.json'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

audit = read(OUT / 'artifact_audit.json')
replay = read(OUT / 'replay.json')
cmp = read(OUT / 'exact_comparison.json')
log = read(PKG / 'train_log.json')
hand = read(PKG / 'handoff.json')
usage = read(PKG / 'usage.json')
reg = read(PKG / 'registry.result.json')
reload = read(PKG / 'reload01.json')
official = next(x for x in usage['sessions'] if x['attempt_id']=='R6_attempt01' and x['kind']=='official')
reload_session = next(x for x in usage['sessions'] if x['attempt_id']=='R6_attempt01' and x['kind']=='reload')
recon = next(x for x in usage['reconciliations'] if x['receipt']['attempt_id']=='R5_attempt01')
total_seconds = sum(x['seconds'] or 0 for x in usage['sessions']) + sum(x['seconds'] for x in usage['reconciliations'])
best = max(log,key=lambda x:x['validation_metrics']['macro_f1'])
r5 = next(x for x in reg['runs'] if x['run_id']=='R5')
r6 = next(x for x in reg['runs'] if x['run_id']=='R6')
assert len(log)==18 and [x['epoch'] for x in log]==list(range(1,19)) and best['epoch']==13
assert r5['status']=='FAILED' and r5['metrics'] is None
assert r6['status']=='COMPLETED' and len(r6['attempts'])==1
assert reload['status']=='PASS' and reload['fresh_process'] and reload['exact_predictions_and_metrics']
assert cmp['pass_exact'] and audit['crc']=='PASS' and audit['indexed_files']==36
assert official['status']==reload_session['status']=='COMPLETED'
assert official['seconds'] <= 10800 and total_seconds <= 43200
assert recon['receipt']['reviewers']['TV3']['decision_r5']=='FAILED_NO_RESUME'
assert abs(r6['attempts'][0]['gpu_hours']-(official['seconds']+reload_session['seconds'])/3600)<1e-12
receipt = {
 'receipt_id':'TV2_W6_R6_INDEPENDENT_MODEL_REPLAY_2026-11-10',
 'created_utc':datetime.now(timezone.utc).isoformat(),
 'decision':'TV2_MODEL_REPLAY_ACCEPTED',
 'scope':'R6_attempt01; frozen comparison_v1 Validation only; independent TV2 model replay',
 'tv3_result_commit':'450f15bde6899faffac3c9389156d04c15196568',
 'tv3_result_commit_verified_on_github':True,
 'zip':{'path':'reports/tv3/w6/w6_2/R6_attempt01.zip','sha256':audit['zip_sha256'],'bytes':audit['zip_bytes'],
        'safe_paths':audit['safe_paths'],'crc':audit['crc'],'entries':audit['entries'],
        'indexed_files_verified':audit['indexed_files'],
        'unindexed_entries':['package_index.json','registry.delivery.json'],
        'package_index_sha256':sha(PKG/'package_index.json'),
        'registry_delivery_sha256':sha(PKG/'registry.delivery.json'),
        'registry_delivery_equals_result':(PKG/'registry.delivery.json').read_bytes()==(PKG/'registry.result.json').read_bytes()},
 'checkpoint':{'best_sha256':sha(PKG/'best_model.pt'),'last_sha256':sha(PKG/'last_model.pt'),
               'loader':'src.training.dino_w6.load_package','weights_only':True,'strict_state_loading':replay['strict_state_load'],
               'source_commit':replay['source_commit'],'vendor_commit':replay['vendor_commit'],
               'config_raw_sha256':sha(PKG/'config.json'),'config_canonical_sha256':replay['config_sha256'],
               'class_map_sha256':sha(PKG/'class_map.json'),'preprocessing_sha256':sha(PKG/'preprocessing.json')},
 'validation':{'images':600,'crops':680,'source_image_bytes_and_rgb_verified':True,
               'provenance_sha256':sha(ROOT/'data/processed/comparison_v1/provenance.json'),
               'crop_manifest_sha256':sha(ROOT/'data/processed/comparison_v1/b2/val.jsonl')},
 'runtime':{'python':replay['python'],'torch':replay['torch'],'torchvision':replay['torchvision'],
            'pillow':replay['pillow'],'numpy':replay['numpy'],'sklearn':replay['sklearn'],
            'cuda':replay['cuda'],'cudnn':replay['cudnn'],'gpu':replay['gpu'],
            'fp32':True,'amp':False,'tf32':False,'deterministic':True},
 'replay':{'policy':cmp['policy'],'crop_logits':cmp['crop_logits'],'crop_probabilities':cmp['crop_probabilities'],
           'image_probabilities':cmp['image_probabilities'],'crop_class_mismatches':cmp['crop_predicted_class_mismatches'],
           'image_class_mismatches':cmp['image_predicted_class_mismatches'],'truth_mismatches':cmp['image_truth_mismatches'],
           'metrics_exact':cmp['metrics_exact'],'accuracy':replay['evaluation']['metrics']['accuracy'],
           'macro_f1':replay['evaluation']['metrics']['macro_f1'],
           'wall_seconds':replay['inference_wall_seconds'],'gpu_hours':replay['gpu_hours'],
           'replay_sha256':sha(OUT/'replay.json'),'comparison_sha256':sha(OUT/'exact_comparison.json')},
 'training':{'epochs_completed':len(log),'best_epoch':best['epoch'],'best_macro_f1':best['validation_metrics']['macro_f1'],
             'fresh_process_reload':reload['status'],'reload_predictions_sha256':sha(PKG/'reload01.predictions.json')},
 'gpu_accounting':{'r6_official_seconds':official['seconds'],'r6_official_gpu_hours':official['seconds']/3600,
                   'r6_reload_seconds':reload_session['seconds'],'r6_total_gpu_hours':(official['seconds']+reload_session['seconds'])/3600,
                   'r6_official_limit_gpu_hours':3,'tv3_total_gpu_hours':total_seconds/3600,'tv3_limit_gpu_hours':12,
                   'tv2_prior_replay_gpu_hours':0.1408824127,'tv2_this_replay_gpu_hours':replay['gpu_hours'],
                   'tv2_cumulative_replay_gpu_hours':0.1408824127+replay['gpu_hours'],'tv2_replay_limit_gpu_hours':2,
                   'official_attempts_used':6,'official_attempts_limit':6,
                   'booking_official':official['booking'],'booking_reload':reload_session['booking'],
                   'r5_registry_status':r5['status'],'r5_reconciled_seconds':recon['seconds'],
                   'r5_ledger_raw_status':'RUNNING / seconds=null (retained historical row; reconciliation is authoritative)',
                   'r5_counted_as_completed_seed':False},
 'r0_comparison':{'r0_predictions_sha256':sha(ROOT/'reports/tv2/w5_acceptance/2026-11-02/attempt_01/tv2_predictions.jsonl'),
                  'r0_correct':507,'r6_correct':519,'accuracy_delta':0.02,
                  'macro_f1_delta':replay['evaluation']['metrics']['macro_f1']-0.8444008279545706,
                  'paired_counts':cmp['paired_vs_r0'],
                  'per_class_correct_delta':cmp['artifact_level']['per_class_correct_delta_vs_r0'],
                  'no_class_loses_four_or_more':True},
 'limits':{'training_performed':False,'official_test_opened':False,'tv4_adapter_acceptance':'PENDING',
           'r5_seed_completed':False,'demo_selection_decision':'SEPARATE_GATE'}
}
DEST.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'decision':receipt['decision'],'receipt_sha256':sha(DEST),'tv3_gpu_hours':total_seconds/3600,'tv2_replay_gpu_hours':replay['gpu_hours']},indent=2))
