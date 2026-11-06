import hashlib,json,subprocess,zipfile
from pathlib import Path
from PIL import Image
ROOT=Path.cwd(); E=ROOT/'outputs/tv2_w6/independent_replay_20261106'; PKGS=(ROOT/'outputs/tv2_w6/independent_acceptance_20261106/received').resolve()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def j(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def canon(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
expected_zip={'R1':'998901556b51789a52fc7a650eac504a4f6e23a1118af00450c7a18aeb9bb2fe','R2':'30f380cab3aa89f5b63c54507f7b7b63d2479e73f52710283e4f557e27fda223'}
expected_cfg={'R1':('92bf5966fe2b4e228fb52b0ae975c8e5044ca1c35b6a4d06ab79f5733cef507c','2ab03b7e13d798b8aace5e4b3542a189389c43c7630f4132303b9200fced63bf'),'R2':('a649fe30c436fee538d9a58a904685a558aebd77a1df3af91409f55f1a86f36c','55dea8ab328e43581642deb964631d391a5b88596feb191a5fa5911a7a94acb7')}
expected_data={'provenance.json':'d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f','class_map.json':'122c3a8c6b297c1d63c3b18db91cf6b3f279a2f979e6b3e77824dbdd086fc58e','train.jsonl':'537d467f7f0ec1ea9fb6a182a37caf0ca1b4f572818789eb6a8c7fc118ef0a11','val.jsonl':'4a18d30378619a39a317af93e1a375ba95162b234380cbf373f26308ac0dfd34','b1/train.jsonl':'4686794d71e497bd5d6bd50ec60681e0ec7553569ddc51419e98aef57a4abd3c','b1/val.jsonl':'31e232f83cbdfb149f54377a4872505d01854ea75d4c83e7d93774402cc16c0d','b2/train.jsonl':'023c3cbf31c42e6e35547a5d928fa93cc00a31a0657879d5e775b4a9d37ce3d3','b2/val.jsonl':'7a4c1b2edf1712e675b5b84c581733f3112b950d2318d4f9ae51d33dd366067e'}
checks={'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'protocol_lock_commit':'18c8ec3a6a58c47b04dbe8606217478145baed6c','protocol_status':j(ROOT/'experiments/w6/registry.json')['protocol_status'],'runtime_lock_canonical_sha256':'7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a'}
assert checks['branch']=='feat/baseline' and checks['head']=='4696a6ef2dd8a3e61013be297e2aeaafe55fb060'
package_rows={}
for run in ('R1','R2'):
 z=ROOT/f'reports/tv3/w6/{run}_attempt01.zip'; assert sha(z)==expected_zip[run]
 with zipfile.ZipFile(z) as a: assert a.testzip() is None; zcount=sum(not x.is_dir() for x in a.infolist())
 pkg=PKGS/run/f'{run}_attempt01'; idx=j(pkg/'package_index.json'); actual={x.filename.removeprefix(f'{run}_attempt01/') for x in zipfile.ZipFile(z).infolist() if not x.is_dir() and x.filename not in (f'{run}_attempt01/package_index.json',f'{run}_attempt01/registry.delivery.json')}; assert actual==set(idx)
 for rel,meta in idx.items(): assert sha(pkg/rel)==meta['sha256'] and (pkg/rel).stat().st_size==meta['bytes']
 hand=j(pkg/'handoff.json'); cfgpath=ROOT/f'configs/w6/tv3/{run}.frozen.json'; cfg=j(cfgpath); raw=sha(cfgpath); ch=canon(cfg); assert (raw,ch)==expected_cfg[run] and (raw,ch)==(hand['config_raw_sha256'],hand['config_sha256'])
 for file,decl in [('best_model.pt',hand['checkpoint_sha256']),('last_model.pt',hand['last_checkpoint_sha256'])]: assert sha(pkg/file)==decl==idx[file]['sha256']
 assert hand['source_sha']=='127cac5b64d37fdda630a2f84b006a8e420dc9ed' and hand['dataset_sha256']==expected_data['provenance.json'] and hand['evaluation_split']=='val'
 package_rows[run]={'zip_sha256':sha(z),'crc':'PASS','archive_files':zcount,'index_files':len(idx),'all_payloads_hash_size_match':True,'config_raw_sha256':raw,'config_canonical_sha256':ch,'best_checkpoint_sha256':hand['checkpoint_sha256'],'last_checkpoint_sha256':hand['last_checkpoint_sha256'],'source_commit':hand['source_sha'],'runtime':j(pkg/'runtime.json')}
manifest=ROOT/'data/processed/comparison_v1'; data={}
for rel,want in expected_data.items(): got=sha(manifest/rel); assert got==want,(rel,got,want); data[rel]=got
parents=[json.loads(x) for x in (manifest/'b1/val.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
crops=[json.loads(x) for x in (manifest/'b2/val.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
assert len(parents)==600 and len({x['image_id'] for x in parents})==600 and len(crops)==680 and len({x['crop_id'] for x in crops})==680
pixel_ok=0
for x in parents:
 q=x['quality']; fp=(ROOT/q['local_path']).resolve(); assert fp.is_relative_to((ROOT/'data/images').resolve()) and fp.is_file() and fp.stat().st_size==q['bytes'] and sha(fp)==q['sha256']
 with Image.open(fp) as im:
  rgb=im.convert('RGB'); assert rgb.size==(x['width'],x['height']); pix=hashlib.sha256(f'RGB:{rgb.width}:{rgb.height}:'.encode()+rgb.tobytes()).hexdigest(); assert pix==q['pixel_sha256']
 pixel_ok+=1
src=j(E/'source_snapshot_verification.json'); assert src['github_raw_snapshot_verification']=='PASS' and src['both_packages_identical_to_remote_source_commit']
vendor=ROOT/'outputs/tv2_w6/independent_replay_20261106/vendor/dinov3'; vendor_sha=subprocess.check_output(['git','-C',str(vendor),'rev-parse','HEAD'],text=True).strip(); vendor_status=subprocess.check_output(['git','-C',str(vendor),'status','--porcelain','--untracked-files=normal'],text=True); assert vendor_sha=='6876159a11b4df116f30f667f8c9888617df0751' and not vendor_status.strip()
checks.update({'source_commit':'127cac5b64d37fdda630a2f84b006a8e420dc9ed','source_snapshot':'PASS','source_files_verified':12,'vendor_commit':vendor_sha,'vendor_clean':True,'dataset_sha256':expected_data['provenance.json'],'dataset_files':data,'validation_images':pixel_ok,'validation_crops':len(crops),'validation_unique_image_ids':len({x['image_id'] for x in parents}),'validation_unique_crop_ids':len({x['crop_id'] for x in crops}),'validation_bytes_and_rgb_hashes':'PASS','test_or_train_images_opened':False})
result={'status':'PASS','checks':checks,'packages':package_rows}; (E/'preflight.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','branch':checks['branch'],'head':checks['head'],'vendor':vendor_sha,'source':'PASS (12 files)','dataset':{'images':pixel_ok,'crops':len(crops),'raw_and_RGB':'PASS'},'packages':{k:{x:y for x,y in v.items() if x in ('zip_sha256','crc','archive_files','index_files','config_canonical_sha256','best_checkpoint_sha256','last_checkpoint_sha256')} for k,v in package_rows.items()}},indent=2,ensure_ascii=False))
