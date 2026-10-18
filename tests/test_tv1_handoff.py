"""Native TV1 schema regressions using synthetic images, never real test rows."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from src.training import b1
from src.training.b1_gate import GateError, official_gate, verify_data
from src.training.tv1_handoff import BUNDLE, PROVENANCE, load_handoff


class NativeTV1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="native_tv1_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        config = json.loads((b1.ROOT / "configs/b1.yaml").read_text())
        b1.create_fixture(self.root, config)
        self.snapshot = self.root / "snapshot"
        self.snapshot.mkdir()
        self.values = {}
        policy = {"dataset_version":"comparison_v1","source_dir":"data/processed/v2","source_seed":42,
                  "min_crop_side":8,"padding_fraction":0,"rounding":"python_round_half_even_then_clip",
                  "bad_box_policy":"exclude_entire_image_from_both_models","multi_box_policy":"all_boxes_same_species",
                  "b2_train_weight":"1 / number_of_crops_in_parent_image","evaluation_unit":"image_id",
                  "b2_evaluation_aggregation":"mean_class_probabilities_over_all_parent_crops",
                  "within_split_exact_duplicates":"retain_and_report","test_policy":"integrity_checks_only_no_model_selection"}
        self.put("configs/comparison_v1.json", policy)
        self.put(BUNDLE+"/policy.json", policy)
        cmap={"0":"fixture_a","1":"fixture_b"}
        self.put(BUNDLE+"/class_map.json",cmap)
        self.put("data/processed/v2/class_map.json",cmap)
        audit={"rows":8,"duplicate_image_ids":0,"duplicate_file_paths":0,"metadata_leakage_check_passed":True,
               "image_content_duplicates_checked":True,"cross_split_overlap":dict.fromkeys(("image_id","file_name","seq_id","location"),0)}
        self.put(BUNDLE+"/audit.json",dict(audit,source_audit=audit,b1_b2_same_parent_ids=True,b1_b2_same_labels_and_splits=True))
        splits=[]
        for split in ("train","val"):
            source=[json.loads(x) for x in (self.root/f"source_{split}.jsonl").read_text().splitlines()]
            views=[];crops=[]
            for r in source:
                r['sequence_id']=r['seq_id']
                q=r['quality'];p=self.root/q['local_path']
                with Image.open(p) as im:q.update(bytes=p.stat().st_size,image_format=im.format,image_mode=im.mode)
                # Half-even rounding differs from unrounded source geometry.
                r['boxes'][0]['bbox_xywh']=[0.5,0.5,30.0,62.5]
                common={k:r[k] for k in ('image_id','split','label','class_id','seq_id','sequence_id','location','file_name','url','width','height','quality')}
                views.append(dict(common,sample_id=r['image_id'],input_type='full_image',sample_weight=1.0))
                for box in r['boxes']:
                    x,y,w,h=box['bbox_xywh'];xy=[round(x),round(y),round(x+w),round(y+h)]
                    crops.append(dict(common,annotation_id=box['annotation_id'],bbox_xywh_original=box['bbox_xywh'],bbox_xyxy=xy,
                                      crop_w=xy[2]-xy[0],crop_h=xy[3]-xy[1],crop_id=r['image_id']+'_'+box['annotation_id'],
                                      input_type='ground_truth_crop',parent_crop_count=len(r['boxes']),sample_weight=1/len(r['boxes'])))
            for path,value in [(BUNDLE+'/'+split+'.jsonl',source),('data/processed/v2/'+split+'.jsonl',source),
                               (BUNDLE+'/b1/'+split+'.jsonl',views),(BUNDLE+'/b2/'+split+'.jsonl',crops)]:self.put(path,value)
            splits.append(dict(split=split,requested=4,retained=4,excluded=0,b1_samples=4,b2_crops=6,sequences=4,locations=2))
        self.put(BUNDLE+'/summary.json',dict(requested=8,retained=8,excluded=0,split_changes=0,by_split=splits))
        self.put(BUNDLE+'/excluded.jsonl',[])
        self.put(BUNDLE+'/duplicates.json',[])
        for name in ('audit.json','summary.json','provenance.json','duplicates.json','excluded_v2.jsonl'):
            self.put('data/processed/v2/'+name,[] if name.endswith('.jsonl') else {})
        for name in ('comparison_data.py','freeze_comparison.py','validate_comparison.py'):
            path=self.snapshot/'scripts'/name;path.parent.mkdir(exist_ok=True);path.write_text('# synthetic code bytes\n')
        self.binding={'snapshot':'snapshot','commit':'a'*40}
        self.publish()
        self.mock=patch('src.training.tv1_handoff.subprocess.check_output',side_effect=self.git)
        self.mock.start();self.addCleanup(self.mock.stop)

    def put(self,path,value):
        self.values[path]=value
        p=self.snapshot/path;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(''.join(json.dumps(v)+'\n' for v in value) if path.endswith('.jsonl') else json.dumps(value),encoding='utf-8')

    def digest(self,path):return hashlib.sha256((self.snapshot/path).read_bytes()).hexdigest()

    def publish(self):
        files={p.relative_to(self.snapshot/BUNDLE).as_posix():self.digest(p.relative_to(self.snapshot).as_posix()) for p in (self.snapshot/BUNDLE).rglob('*') if p.is_file() and p.name!='provenance.json'}
        files.update({k:'0'*64 for k in ('test.jsonl','b1/test.jsonl','b2/test.jsonl','manifest.jsonl')})
        source={p.name:self.digest(p.relative_to(self.snapshot).as_posix()) for p in (self.snapshot/'data/processed/v2').iterdir()}
        provenance=dict(dataset_version='comparison_v1',source_dir='data/processed/v2',config_path='configs/comparison_v1.json',
                        config_sha256=self.digest('configs/comparison_v1.json'),files_sha256=files,source_files_sha256=source,
                        script_sha256={p.name:self.digest(p.relative_to(self.snapshot).as_posix()) for p in (self.snapshot/'scripts').iterdir()})
        self.put(PROVENANCE,provenance);self.binding['provenance_sha256']=self.digest(PROVENANCE)
        self.put('reports/tv1_w3/verification.json',dict(passed=True,dataset_version='comparison_v1',provenance_sha256=self.digest(PROVENANCE),
                 local_images_redecoded=True,b1_b2_same_parent_ids=True,b1_b2_same_labels_and_splits=True,split_changes=0,requested=8,retained=8,excluded=0,
                 cross_split_overlap=dict.fromkeys(('image_id','file_name','seq_id','location'),0)))
        self.git_blobs={p:(self.snapshot/p).read_bytes() for p in (PROVENANCE,'reports/tv1_w3/verification.json')}

    def git(self,args,**kwargs):
        self.assertEqual(args[:2],['git','show'])
        return self.git_blobs[args[2].split(':',1)[1]]

    def verify(self,inspect=True):
        return verify_data(load_handoff(self.binding,self.root),self.root,self.root/'images',2,inspect=inspect)

    def test_native_views_rounding_multicrop_and_image_checks(self):
        rows,_,_,proof=self.verify()
        self.assertEqual(len(rows['train']),4)
        self.assertEqual(proof['counts']['train']['crops'],6)
        self.assertTrue(proof['source_images_verified'])
        self.assertFalse(proof['test_rows_opened'])
        self.assertFalse((self.snapshot/BUNDLE/'test.jsonl').exists())

    def test_metadata_pass_never_claims_image_pass(self):
        self.assertEqual(self.verify(False)[3]['status'],'METADATA PASS - IMAGES NOT CHECKED')

    def test_native_data_is_not_protocol_approval(self):
        config=json.loads((b1.ROOT/'configs/b1.yaml').read_text())
        config['data']['tv1_handoff']=self.binding
        with self.assertRaisesRegex(GateError,'PROTOCOL NOT AGREED'):official_gate(config,self.root)

    def test_git_hash_binding_and_local_tamper_fail(self):
        wrong=dict(self.binding,provenance_sha256='f'*64)
        with self.assertRaisesRegex(GateError,'pinned Git hash'):load_handoff(wrong,self.root)
        (self.snapshot/BUNDLE/'b1/train.jsonl').write_text('{}\n')
        with self.assertRaisesRegex(GateError,'SHA-256'):self.verify()

    def test_missing_validator_and_failed_attestation_fail(self):
        (self.snapshot/'scripts/validate_comparison.py').write_text('# changed')
        with self.assertRaisesRegex(GateError,'SHA-256'):self.verify()

    def test_republished_bad_crop_or_projection_is_rejected(self):
        for path,key,value in [(BUNDLE+'/b2/train.jsonl','parent_crop_count',99),
                               (BUNDLE+'/b2/train.jsonl','bbox_xyxy',[0.5,0.5,30.5,63]),
                               (BUNDLE+'/b1/train.jsonl','quality',{})]:
            old=copy.deepcopy(self.values[path]);changed=copy.deepcopy(old);changed[0][key]=value
            self.put(path,changed);self.publish()
            with self.assertRaises(GateError):self.verify()
            self.put(path,old);self.publish()

    def test_republished_leakage_attestation_rejected(self):
        audit=copy.deepcopy(self.values[BUNDLE+'/audit.json']);audit['cross_split_overlap']['location']=1
        self.put(BUNDLE+'/audit.json',audit);self.publish()
        with self.assertRaisesRegex(GateError,'leakage'):self.verify()

    def test_image_path_cannot_be_double_joined_or_escape(self):
        with self.assertRaisesRegex(ValueError,'escapes root'):
            verify_data(load_handoff(self.binding,self.root),self.root,self.root/'images/images',2)


if __name__=='__main__':unittest.main()
