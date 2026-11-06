import hashlib, json, math, zipfile
from pathlib import Path
ROOT=Path.cwd()
STAGE=ROOT/'outputs/tv2_w6/independent_acceptance_20261106'
PKG=STAGE/'received'
OUT=STAGE/'artifact_audit.json'
expected_zip={'R1':'998901556b51789a52fc7a650eac504a4f6e23a1118af00450c7a18aeb9bb2fe','R2':'30f380cab3aa89f5b63c54507f7b7b63d2479e73f52710283e4f557e27fda223'}
class_names=json.loads((ROOT/'outputs/tv2_w6/independent_acceptance_20261106/received/R1/R1_attempt01/class_map.json').read_text(encoding='utf-8'))
if isinstance(class_names,dict):
    names=[class_names[str(i)] if str(i) in class_names else class_names.get(i) for i in range(8)]
else: names=class_names
if names and isinstance(names[0],dict): names=[x.get('name') or x.get('class_name') for x in names]
run_paths={'R0':ROOT/'reports/tv2/w5_acceptance/2026-11-02/attempt_01/independent_replay/predictions.json','R1':PKG/'R1/R1_attempt01/validation.json','R2':PKG/'R2/R2_attempt01/validation.json'}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def readjson(p): return json.loads(p.read_text(encoding='utf-8'))
def calculate(run,p):
    o=readjson(p); imgs=o['image_predictions']; crops=o['crop_predictions']
    ids=[x['image_id'] for x in imgs]
    dup_img=sorted({x for x in ids if ids.count(x)>1})
    cropids=[x.get('crop_id') for x in crops]
    dup_crop=sorted({x for x in cropids if cropids.count(x)>1})
    byimg={}
    for c in crops: byimg.setdefault(c['image_id'],[]).append(c.get('probabilities',c.get('class_scores')))
    maxmean=0.0; missing=[]; label_mismatch=[]; score_bad=[]
    for i in imgs:
        arr=byimg.get(i['image_id'])
        if not arr: missing.append(i['image_id']); continue
        if len(arr)!=i.get('crop_count'): label_mismatch.append(i['image_id'])
        means=[sum(float(v[k]) for v in arr)/len(arr) for k in range(8)]
        probs=i.get('probabilities',i.get('class_scores'))
        d=max(abs(means[k]-float(probs[k])) for k in range(8)); maxmean=max(maxmean,d)
        if d>1e-10: score_bad.append((i['image_id'],d))
        if not math.isclose(sum(float(x) for x in probs),1.0,abs_tol=1e-5,rel_tol=0): label_mismatch.append(i['image_id']+':sum')
    cm=[[0]*8 for _ in range(8)]
    per=[]
    for i in imgs:
        y=int(i.get('y_true',i.get('ground_truth'))); pred=int(i.get('y_pred',i.get('predicted_class')))
        cm[y][pred]+=1
    for c in range(8):
        tp=cm[c][c]; support=sum(cm[c]); predicted=sum(cm[r][c] for r in range(8)); precision=tp/predicted if predicted else 0; recall=tp/support if support else 0; f1=2*precision*recall/(precision+recall) if precision+recall else 0
        per.append({'class_id':c,'class':names[c],'correct':tp,'support':support,'precision':precision,'recall':recall,'f1':f1})
    correct=sum(cm[i][i] for i in range(8)); accuracy=correct/len(imgs); macro_f1=sum(x['f1'] for x in per)/8; macro_p=sum(x['precision'] for x in per)/8; macro_r=sum(x['recall'] for x in per)/8
    return {'run':run,'image_count':len(imgs),'image_ids_unique':len(set(ids)),'duplicate_image_ids':dup_img,'crop_count':len(crops),'crop_ids_unique':len(set(cropids)),'duplicate_crop_ids':dup_crop,'unrepresented_image_ids':sorted(set(ids)-set(byimg)),'unexpected_crop_image_ids':sorted(set(byimg)-set(ids)),'crop_count_or_score_errors':label_mismatch,'max_abs_image_vs_mean_crop_score_delta':maxmean,'mean_score_mismatches_gt_1e-10':score_bad[:10],'accuracy':accuracy,'correct':correct,'macro_precision':macro_p,'macro_recall':macro_r,'macro_f1':macro_f1,'per_class':per,'confusion_matrix':cm,'producer_metrics':o.get('metrics')}
runs={k:calculate(k,p) for k,p in run_paths.items()}
# Match all image IDs/labels across references and candidates, calculate paired outcomes.
base={x['image_id']:x for x in readjson(run_paths['R0'])['image_predictions']}
paired={}
for run in ('R1','R2'):
    cand={x['image_id']:x for x in readjson(run_paths[run])['image_predictions']}
    fixes=[]; losses=[]; per_class={str(i):{'fixes':0,'losses':0} for i in range(8)}
    changed=[]
    for iid,b in base.items():
        c=cand[iid]; by=int(b.get('y_true',b.get('ground_truth'))); cy=int(c.get('y_true',c.get('ground_truth')))
        assert by==cy, (run,iid,'label mismatch')
        bpred=int(b.get('y_pred',b.get('predicted_class'))); cpred=int(c.get('y_pred',c.get('predicted_class')))
        if bpred!=cpred: changed.append(iid)
        if bpred!=by and cpred==by: fixes.append(iid); per_class[str(by)]['fixes']+=1
        if bpred==by and cpred!=by: losses.append(iid); per_class[str(by)]['losses']+=1
    paired[run]={'paired_image_count':len(base),'ids_exact_match':set(base)==set(cand),'fixed_wrong_to_correct':len(fixes),'lost_correct_to_wrong':len(losses),'prediction_changed':len(changed),'fix_image_ids':fixes,'loss_image_ids':losses,'per_true_class_fix_loss':per_class}
# two confusable pairs: errors in each direction and changes in paired states
pairs={'common_palm_civet_vs_masked_palm_civet':(4,5),'muntjac_vs_sambar':(0,2)}
pair_stats={}
for pname,(a,b) in pairs.items():
    pair_stats[pname]={}
    for run in ('R0','R1','R2'):
        cm=runs[run]['confusion_matrix']; pair_stats[pname][run]={'a_to_b':cm[a][b],'b_to_a':cm[b][a]}
# package inventory check (exact outer hash, CRC, paths, package_index hashes and sizes)
packages={}
for run,zip_hash in expected_zip.items():
    zip_path=ROOT/f'reports/tv3/w6/{run}_attempt01.zip'
    actual_sha=sha(zip_path)
    assert actual_sha==zip_hash,(run,'archive sha mismatch',actual_sha)
    root=PKG/run/f'{run}_attempt01'; index=readjson(root/'package_index.json')
    with zipfile.ZipFile(zip_path) as z:
        bad=z.testzip(); assert bad is None,(run,'CRC failure',bad)
        entries={i.filename:i for i in z.infolist() if not i.is_dir()}
    listed=set(index)
    actual=set(entries)-{f'{run}_attempt01/package_index.json',f'{run}_attempt01/registry.delivery.json'}
    normalized={x.removeprefix(f'{run}_attempt01/'):x for x in actual}
    assert set(normalized)==listed,(run,'package membership mismatch',sorted(set(normalized)^listed))
    checks=[]
    for rel,meta in index.items():
        p=root/rel
        h=sha(p); size=p.stat().st_size
        checks.append({'path':rel,'sha256_match':h==meta['sha256'],'size_match':size==meta['bytes'],'sha256':h,'bytes':size})
    assert all(x['sha256_match'] and x['size_match'] for x in checks),(run,'package index mismatch')
    packages[run]={'zip_sha256':actual_sha,'zip_crc':'PASS','archive_file_count':len(entries),'package_index_count':len(index),'all_payload_hashes_and_sizes_match':all(x['sha256_match'] and x['size_match'] for x in checks),'files':checks}
# official attempts/usage from each delivery registry
registries={}
for run in ('R1','R2'):
    root=PKG/run/f'{run}_attempt01'
    reg=readjson(root/'registry.result.json'); usage=readjson(root/'usage.json')
    run_entry=next(x for x in reg['runs'] if x['run_id']==run)
    sessions=usage.get('sessions',[])
    off=[x for x in sessions if x.get('kind')=='official']
    registries[run]={'status':run_entry['status'],'attempts':run_entry.get('attempts'),'checkpoint_sha256':run_entry.get('checkpoint_sha256'),'metrics':run_entry.get('metrics'),'source_sha':run_entry.get('source_sha'),'config_sha256':run_entry.get('config_sha256'),'registry_official_attempt_count':len(run_entry.get('attempts',[])),'usage_sessions':sessions,'official_session_seconds':sum(float(x.get('seconds',0)) for x in off),'usage_claims':usage.get('totals',usage.get('gpu_hours',usage))}
result={'packages':packages,'runs':runs,'paired':paired,'confusion_pairs':pair_stats,'registry_usage':registries,'class_names':names}
OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'packages':{k:{a:v for a,v in x.items() if a!='files'} for k,x in packages.items()},'runs':{k:{a:v for a,v in x.items() if a not in ('per_class','confusion_matrix','producer_metrics')} for k,x in runs.items()},'paired':{k:{a:v for a,v in x.items() if a not in ('fix_image_ids','loss_image_ids','per_true_class_fix_loss')} for k,x in paired.items()},'confusion_pairs':pair_stats,'registry_usage':{k:{a:v for a,v in x.items() if a not in ('usage_sessions',)} for k,x in registries.items()}},indent=2,ensure_ascii=False))
