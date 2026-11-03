"""Synthetic software fixtures only: never model-quality evidence or Test access."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.evaluation.w5_validation import (CLASSES, PROVENANCE, aggregate, audit_predictions,
    compare_predictions, load_frozen_validation, sha256, softmax, verify_handoff)


class W5ValidationTests(unittest.TestCase):
    def setUp(self):
        self.parents = [dict(image_id='a', class_id=0, split='val'), dict(image_id='b', class_id=1, split='val')]
        self.crops = [dict(crop_id=cid, image_id=iid, class_id=cls, split='val')
                      for cid,iid,cls in [('a1','a',0),('a2','a',0),('b1','b',1)]]
        self.records = [dict(crop_id=cid, image_id=iid, ground_truth=cls, class_scores=p)
                        for cid,iid,cls,p in [('a1','a',0,[.9,.1,0,0,0,0,0,0]),
                                             ('a2','a',0,[.3,.7,0,0,0,0,0,0]),
                                             ('b1','b',1,[0,1,0,0,0,0,0,0])]]
        self.digest = 'a'*64

    def predictions(self):
        return aggregate(self.records,self.parents,self.crops,'synthetic_fixture',self.digest)

    def test_mean_softmax_is_image_level(self):
        rows=self.predictions()
        self.assertEqual(len(rows),2)
        self.assertAlmostEqual(rows[0]['class_scores'][0],.6)
        self.assertEqual(rows[0]['crop_count'],2)
        self.assertEqual(audit_predictions(rows,self.parents,self.crops,'synthetic_fixture',self.digest)['metrics']['accuracy'],1.)

    def test_logits_softmax_before_mean_not_mean_logits(self):
        records=copy.deepcopy(self.records)
        for r, logits in zip(records,[[2.,0,0,0,0,0,0,0],[-1.,1,0,0,0,0,0,0],[0.,1,0,0,0,0,0,0]]):
            r.pop('class_scores'); r['logits']=logits
        rows=aggregate(records,self.parents,self.crops,'synthetic_fixture',self.digest)
        self.assertAlmostEqual(rows[0]['class_scores'][0],(softmax(records[0]['logits'])[0]+softmax(records[1]['logits'])[0])/2)

    def test_softmax_large_logits(self):
        self.assertAlmostEqual(sum(softmax([10000.,9999.,0,0,0,0,0,0])),1.)

    def test_exact_prediction_tie_lowest_class(self):
        self.records[0]['class_scores']=self.records[1]['class_scores']=[.5,.5,0,0,0,0,0,0]
        self.assertEqual(self.predictions()[0]['predicted_class'],0)

    def test_missing_crop(self):
        self.records.pop()
        with self.assertRaisesRegex(ValueError,'Missing/extra'): self.predictions()

    def test_duplicate_crop_prediction(self):
        self.records.append(copy.deepcopy(self.records[0]))
        with self.assertRaisesRegex(ValueError,'Duplicate'): self.predictions()

    def test_duplicate_image_manifest(self):
        self.parents.append(copy.deepcopy(self.parents[0]))
        with self.assertRaisesRegex(ValueError,'Duplicate'): self.predictions()

    def test_missing_parent_crop(self):
        self.crops=self.crops[:2]
        with self.assertRaisesRegex(ValueError,'parent'): self.predictions()

    def test_label_association(self):
        self.records[0]['ground_truth']=1
        with self.assertRaisesRegex(ValueError,'ground truth'): self.predictions()

    def test_bad_scores(self):
        for scores in ([float('nan')]+[0]*7, [float('inf')]+[0]*7, [.1]*7, [0]*8, [-1,2,0,0,0,0,0,0], [True]+[0]*7):
            with self.subTest(scores=scores):
                self.records[0]['class_scores']=scores
                with self.assertRaises(ValueError): self.predictions()

    def test_score_and_logit_ambiguity(self):
        self.records[0]['logits']=[0]*8
        with self.assertRaisesRegex(ValueError,'exactly'): self.predictions()

    def test_test_split_rejected(self):
        for rows in (self.parents,self.crops):
            rows[0]['split']='test'
            with self.assertRaisesRegex(ValueError,'Validation only'): self.predictions()
            rows[0]['split']='val'

    def test_bad_class_id(self):
        for value in (8,-1,True,1.5):
            self.parents[0]['class_id']=value
            with self.assertRaises(ValueError): self.predictions()

    def test_saved_argmax_consistency(self):
        rows=self.predictions(); rows[0]['predicted_class']=1
        with self.assertRaisesRegex(ValueError,'Argmax'): audit_predictions(rows,self.parents,self.crops,'synthetic_fixture',self.digest)

    def test_saved_crop_count_consistency(self):
        rows=self.predictions(); rows[0]['crop_count']=1
        with self.assertRaisesRegex(ValueError,'Crop count'): audit_predictions(rows,self.parents,self.crops,'synthetic_fixture',self.digest)

    def test_saved_missing_duplicate_image(self):
        for rows in (self.predictions()[:1], self.predictions()+self.predictions()[:1]):
            with self.assertRaises(ValueError): audit_predictions(rows,self.parents,self.crops,'synthetic_fixture',self.digest)

    def test_saved_checkpoint_and_experiment(self):
        for key,value in [('experiment_id','wrong'),('checkpoint_sha256','b'*64)]:
            rows=self.predictions(); rows[0][key]=value
            with self.assertRaisesRegex(ValueError,'checkpoint'): audit_predictions(rows,self.parents,self.crops,'synthetic_fixture',self.digest)

    def test_independent_metrics_equal_sklearn_all_eight_classes(self):
        from sklearn.metrics import f1_score,precision_score,recall_score
        self.records[-1]['class_scores']=[1,0,0,0,0,0,0,0]
        result=audit_predictions(self.predictions(),self.parents,self.crops,'synthetic_fixture',self.digest)
        for key,fn in [('f1',f1_score),('precision',precision_score),('recall',recall_score)]:
            self.assertAlmostEqual(result['metrics']['macro_'+key],fn([0,1],[0,0],labels=list(range(8)),average='macro',zero_division=0))
        self.assertEqual(sum(sum(r) for r in result['confusion_matrix']),2)
        self.assertEqual(result['per_class'][7]['support'],0)

    def test_paired_outcomes(self):
        left=self.predictions(); right=copy.deepcopy(left); right[0]['predicted_class']=1
        self.assertEqual(compare_predictions(left,right)['b2_correct_candidate_wrong'],['a'])

    def test_population_mismatch_in_comparison(self):
        with self.assertRaisesRegex(ValueError,'population'): compare_predictions(self.predictions(),self.predictions()[:1])

    def test_frozen_loader_never_opens_test(self):
        from src.evaluation import w5_validation as module
        observed=[]
        original=module.read_jsonl
        def guarded(path):
            observed.append(str(path))
            self.assertNotIn('test',Path(path).name.lower())
            return original(path)
        root=Path(__file__).resolve().parents[1]
        with patch.object(module,'read_jsonl',side_effect=guarded):
            parents,crops,_=load_frozen_validation(root)
        self.assertEqual((len(parents),len(crops)),(600,680))
        self.assertEqual(len(observed),3)


class W5HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'synthetic.bin'; self.path.write_bytes(b'synthetic software fixture; no model')
        self.hashes={'train.jsonl':'fixture','val.jsonl':'fixture'}
        self.protocol=dict(status='APPROVED',reviewers={'TV3':'synthetic fixture reviewer'},selection_metric='image_macro_f1',
                           checkpoint_tie_rule='earliest_epoch',prediction_tie_rule='lowest_class_id',
                           max_candidate_runs=1,experiments=['synthetic_fixture'],seeds=[42])
        self.handoff=dict(experiment_id='synthetic_fixture',seed=42,evaluation_split='val',dataset_version='comparison_v1',
            train_dataset_version='comparison_v1',val_dataset_version='comparison_v1',class_order=CLASSES.copy(),
            provenance_sha256=PROVENANCE,manifest_sha256=self.hashes,aggregation='mean_crop_softmax_then_argmax',
            model_name='synthetic_fixture',architecture='synthetic',pretrained_source='synthetic',model_version='fixture',
            training_log='synthetic',training_commit='fixture',device='cpu',training_status='complete',
            preprocessing={'synthetic':True},fresh_process_reload={'status':'PASS','evidence':'synthetic fixture only'},
            checkpoint_sha256=sha256(self.path),checkpoint_bytes=self.path.stat().st_size)
        log=Path(self.tmp.name)/'fixture.log'; log.write_text('Synthetic fixture, not training evidence',encoding='utf-8')
        reload=Path(self.tmp.name)/'reload.json'
        reload.write_text(json.dumps(dict(status='PASS',fresh_process=True,checkpoint_sha256=sha256(self.path),
            evaluation_split='val',manifest_sha256=self.hashes,test_inference_performed=False)),encoding='utf-8')
        self.handoff['artifacts']={name:dict(path=str(p),sha256=sha256(p)) for name,p in
                                   [('training_config',log),('training_log',log),('reload_report',reload)]}

    def verify(self): verify_handoff(self.handoff,self.path,self.hashes,self.protocol)

    def test_complete_synthetic_handoff(self): self.verify()

    def test_draft_blocks_candidate(self):
        self.protocol['status']='DRAFT'
        with self.assertRaisesRegex(ValueError,'TV3 approval'): self.verify()

    def test_class_order_mismatch(self):
        self.handoff['class_order']=list(reversed(CLASSES))
        with self.assertRaisesRegex(ValueError,'Class order'): self.verify()

    def test_checkpoint_hash_mismatch(self):
        self.path.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'): self.verify()

    def test_manifest_hash_mismatch(self):
        self.handoff['manifest_sha256']={}
        with self.assertRaisesRegex(ValueError,'manifest hash'): self.verify()

    def test_test_and_expanded_data_rejected(self):
        for key,value in [('evaluation_split','test'),('train_dataset_version','expanded')]:
            old=self.handoff[key]; self.handoff[key]=value
            with self.assertRaises(ValueError): self.verify()
            self.handoff[key]=old

    def test_unregistered_seed_and_budget(self):
        self.handoff['seed']=99
        with self.assertRaisesRegex(ValueError,'seed'): self.verify()
        self.handoff['seed']=42; self.protocol['max_candidate_runs']=0
        with self.assertRaisesRegex(ValueError,'budget'): self.verify()

    def test_no_reload_evidence(self):
        self.handoff['fresh_process_reload']={'status':'PASS'}
        with self.assertRaisesRegex(ValueError,'reload evidence'): self.verify()

    def test_no_preprocessing(self):
        self.handoff['preprocessing']={}
        with self.assertRaisesRegex(ValueError,'preprocessing'): self.verify()

    def test_bare_pass_without_physical_artifacts_rejected(self):
        self.handoff['artifacts']={}
        with self.assertRaisesRegex(ValueError,'Missing artifact'): self.verify()

    def test_tampered_reload_artifact(self):
        Path(self.handoff['artifacts']['reload_report']['path']).write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'hash mismatch'): self.verify()


if __name__=='__main__': unittest.main()
