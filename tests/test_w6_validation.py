"""Synthetic W6 fixtures only. No images, model loading, training or Test inputs."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src.evaluation import w5_validation as w5
from src.evaluation import w6_validation as w6


def draft_fixture(registry):
    """A DRAFT protocol independent of the repository's current lock state."""
    result=copy.deepcopy(registry)
    result.update(protocol_status='DRAFT',approvals={'TV2':None,'TV3':None},
                  freeze_evidence=None,smoke_evidence=None)
    for run in result['runs'][1:]:
        run['approvals']={'TV2':None,'TV3':None}
    return result


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = w5.read_json(w6.ROOT/'experiments/w6/registry.json')

    def test_real_registry_and_current_gate(self):
        result = w6.validate_registry(self.registry)
        self.assertEqual(result['official_attempts'],0)
        self.assertEqual(result['protocol_status'],self.registry['protocol_status'])
        if result['protocol_status']=='APPROVED':
            lock=w5.read_json(w6.ROOT/self.registry['freeze_evidence'])
            smoke=w5.read_json(w6.ROOT/self.registry['smoke_evidence'])
            self.assertEqual(self.registry['approvals']['TV2'],lock['approval_decisions']['TV2']['path'])
            self.assertEqual(self.registry['approvals']['TV3'],lock['approval_decisions']['TV3']['link'])
            for run in self.registry['runs'][1:3]:
                self.assertEqual(run['approvals'],self.registry['approvals'])
                config=w5.read_json(w6.ROOT/run['config_path'])
                self.assertEqual(config['status'],'FROZEN')
                self.assertEqual(w5.sha256(w6.ROOT/run['config_path']),lock['frozen_configs'][run['run_id']]['raw_sha256'])
                self.assertEqual(w6.digest(config),lock['frozen_configs'][run['run_id']]['canonical_sha256'])
                self.assertEqual(run['source_sha'],lock['source_commit'])
                self.assertEqual(config['runtime']['source_sha'],run['source_sha'])
                self.assertEqual(config['runtime']['runtime_lock'],lock['runtime_lock_canonical_sha256'])
                self.assertEqual(config['smoke_evidence']['sha256'],smoke['records'][run['run_id']]['raw_sha256'])
                w6.official_gate(self.registry,run)
        else:
            self.assertEqual(result['protocol_status'],'DRAFT')
            with self.assertRaisesRegex(ValueError,'DRAFT'):
                w6.official_gate(self.registry,self.registry['runs'][1])

    def test_no_side_effects(self):
        before = copy.deepcopy(self.registry)
        w6.validate_registry(self.registry)
        self.assertEqual(before,self.registry)

    def test_draft_blocks_official(self):
        self.registry=draft_fixture(self.registry)
        self.assertEqual(w6.validate_registry(self.registry)['protocol_status'],'DRAFT')
        with self.assertRaisesRegex(ValueError,'DRAFT'):
            w6.official_gate(self.registry,self.registry['runs'][1])

    def test_approval_string_alone_insufficient(self):
        self.registry=draft_fixture(self.registry)
        self.registry['protocol_status']='APPROVED'
        with self.assertRaisesRegex(ValueError,'missing'):
            w6.official_gate(self.registry,self.registry['runs'][1])

    def test_fake_approved_missing_run_binding_rejected(self):
        r=draft_fixture(self.registry)
        r.update(protocol_status='APPROVED',approvals={'TV2':'SYNTHETIC','TV3':'SYNTHETIC'},
                 freeze_evidence='SYNTHETIC',smoke_evidence='SYNTHETIC')
        run=r['runs'][1]
        run['approvals']={'TV2':'SYNTHETIC','TV3':'SYNTHETIC'}
        run['source_sha']=None
        with self.assertRaisesRegex(ValueError,'source/config/approval missing'):
            w6.official_gate(r,run)

    def test_exact_run_population(self):
        for mutate in (lambda r:r['runs'].pop(),lambda r:r['runs'].reverse(),lambda r:r['runs'].append(r['runs'][1])):
            r=copy.deepcopy(self.registry);mutate(r)
            with self.assertRaises(Exception):w6.validate_registry(r)

    def test_seed_rejected(self):
        self.registry['runs'][3]['seed']=42
        with self.assertRaisesRegex(ValueError,'seed'):w6.validate_registry(self.registry)

    def test_r0_cannot_be_retrained_or_relabelled(self):
        for key,value in [('status','COMPLETED'),('checkpoint_sha256','b'*64),('metrics',{'accuracy':.88,'macro_f1':.9})]:
            r=copy.deepcopy(self.registry);r['runs'][0][key]=value
            with self.assertRaises(ValueError):w6.validate_registry(r)

    def test_dataset_binding(self):
        self.registry['runs'][5]['dataset_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'Dataset'):w6.validate_registry(self.registry)

    def test_config_binding(self):
        self.registry['runs'][1]['config_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'Config SHA'):w6.validate_registry(self.registry)

    def test_r1_r2_plan_invariants(self):
        for index,key,value in [(1,'feature_dim',384),(1,'register_tokens',True),(2,'parent_batch',8),(2,'crop_microbatch',9)]:
            config=w5.read_json(w6.ROOT/self.registry['runs'][index]['config_path']);config[key]=value
            with self.assertRaises(ValueError):w6.validate_recipe_config(config,'R%d' % index)
        config=w5.read_json(w6.ROOT/self.registry['runs'][1]['config_path'])
        config['preprocessing']['resize']=[224,224]
        with self.assertRaisesRegex(ValueError,'preprocessing'):w6.validate_recipe_config(config,'R1')

    def test_unstarted_cannot_have_results(self):
        self.registry['runs'][1]['checkpoint_sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'Unstarted'):w6.validate_registry(self.registry)

    def test_budget_cannot_be_expanded(self):
        self.registry['budgets']['max_new_official_attempts']=7
        with self.assertRaisesRegex(ValueError,'budget'):w6.validate_registry(self.registry)

    def test_failed_oom_still_needs_accounting(self):
        for status in ('FAILED','OOM','STOPPED','RUNNING','COMPLETED'):
            r=copy.deepcopy(self.registry);r['runs'][1]['status']=status
            with self.assertRaisesRegex(ValueError,'accounting'):w6.validate_registry(r)

    def execution_fixture(self):
        r=self.registry
        r.update(protocol_status='APPROVED',approvals={'TV2':'SYNTHETIC','TV3':'SYNTHETIC'},
                 freeze_evidence='SYNTHETIC',smoke_evidence='SYNTHETIC')
        for run in r['runs'][1:3]:
            run.update(status='FAILED',source_sha='a'*40,approvals={'TV2':'SYNTHETIC','TV3':'SYNTHETIC'},
                       attempts=[dict(attempt_id=run['run_id']+'_fixture',status='FAILED',gpu_hours=.1,evidence_path='SYNTHETIC')])
        return r

    def test_failures_consume_budget(self):
        r=self.execution_fixture()
        result=w6.validate_registry(r)
        self.assertEqual(result['official_attempts'],2)
        preparation=sum(p['gpu_hours'] for p in r['tv3_preparation_attempts'])
        self.assertAlmostEqual(result['measured_tv3_preparation_gpu_hours'],preparation)
        self.assertAlmostEqual(result['measured_tv3_gpu_hours'],preparation+.2)

    def test_seventh_attempt_rejected(self):
        r=self.execution_fixture()
        r['runs'][1]['attempts']=[dict(attempt_id=str(i),status='FAILED',gpu_hours=.1,evidence_path='SYNTHETIC') for i in range(6)]
        with self.assertRaisesRegex(ValueError,'six'):w6.validate_registry(r)

    def test_duplicate_attempt_rejected(self):
        r=self.execution_fixture();r['runs'][2]['attempts'][0]['attempt_id']=r['runs'][1]['attempts'][0]['attempt_id']
        with self.assertRaisesRegex(ValueError,'duplicate'):w6.validate_registry(r)

    def test_over_two_hours_or_negative_or_nonfinite_rejected(self):
        for hours in (2.01,-.1,float('nan'),float('inf')):
            r=copy.deepcopy(self.execution_fixture());r['runs'][1]['attempts'][0]['gpu_hours']=hours
            with self.assertRaises(Exception):w6.validate_registry(r)

    def test_unknown_gpu_usage_kept_explicit(self):
        r=self.execution_fixture();r['runs'][1]['attempts'][0]['gpu_hours']=None
        self.assertEqual(w6.validate_registry(r)['unmeasured_attempts'],1)

    def test_replay_budget(self):
        for hours in (2.01,-1,float('nan')):
            self.registry['replay_attempts']=[dict(attempt_id='fixture',gpu_hours=hours,evidence_path='SYNTHETIC')]
            with self.assertRaises(Exception):w6.validate_registry(self.registry)

    def test_seed_and_expansion_conditions(self):
        r=self.execution_fixture()
        for i in (3,4,5,6):
            run=copy.deepcopy(r['runs'][i]);run.update(recipe='R1',config_path='fixture',config_sha256='a'*64,
                source_sha='a'*40,approvals={'TV2':'SYNTHETIC','TV3':'SYNTHETIC'})
            with self.assertRaisesRegex(ValueError,'BLOCKED'):w6.official_gate(r,run)

    def test_preparation_gpu_counts_towards_tv3_total(self):
        self.registry['tv3_preparation_attempts']=[dict(attempt_id='SYNTHETIC',kind='train_only_smoke',gpu_hours=12.1,evidence_path='SYNTHETIC')]
        with self.assertRaisesRegex(ValueError,'TV3 GPU'):w6.validate_registry(self.registry)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.parents=[dict(image_id='a',class_id=0,split='val'),dict(image_id='b',class_id=1,split='val')]
        self.crops=[dict(crop_id=c,image_id=i,class_id=y,split='val') for c,i,y in [('a1','a',0),('a2','a',0),('b1','b',1)]]
        self.records=[dict(crop_id=r['crop_id'],image_id=r['image_id'],ground_truth=r['class_id'],
                           class_scores=[.9,.1,0,0,0,0,0,0] if r['image_id']=='a' else [0,1,0,0,0,0,0,0]) for r in self.crops]
        self.sha='a'*64
        self.images=w5.aggregate(self.records,self.parents,self.crops,'R1',self.sha)

    def evaluate(self):return w6.evaluate(self.records,self.images,self.parents,self.crops,'R1',self.sha)

    def test_metrics_all_eight_classes(self):
        result=self.evaluate();self.assertEqual(result['metrics']['accuracy'],1)
        self.assertEqual(result['metrics']['macro_f1'],.25)
        self.assertEqual(len(result['confusion_matrix']),8)
        self.assertEqual(result['per_class'][7]['support'],0)

    def test_saved_vector_must_equal_aggregation(self):
        self.images[0]['class_scores']=[.8,.2,0,0,0,0,0,0]
        with self.assertRaisesRegex(ValueError,'aggregation'):self.evaluate()

    def test_missing_extra_duplicate_crop(self):
        for rows in (self.records[:-1],self.records+[self.records[0]],self.records+[dict(self.records[0],crop_id='extra')]):
            with self.assertRaises(ValueError):w6.evaluate(rows,self.images,self.parents,self.crops,'R1',self.sha)

    def test_missing_extra_duplicate_image(self):
        for rows in (self.images[:-1],self.images+[self.images[0]],self.images+[dict(self.images[0],image_id='extra')]):
            with self.assertRaises(ValueError):w6.evaluate(self.records,rows,self.parents,self.crops,'R1',self.sha)

    def test_wrong_parent_and_label(self):
        for key,value in [('image_id','b'),('ground_truth',1)]:
            rows=copy.deepcopy(self.records);rows[0][key]=value
            with self.assertRaises(ValueError):w6.evaluate(rows,self.images,self.parents,self.crops,'R1',self.sha)

    def test_nonfinite_invalid_vectors(self):
        for v in ([float('nan')]+[0]*7,[float('inf')]+[0]*7,[0]*8,[.1]*7,[-1,2]+[0]*6,[True]+[0]*7):
            rows=copy.deepcopy(self.records);rows[0]['class_scores']=v
            with self.assertRaises(ValueError):w6.evaluate(rows,self.images,self.parents,self.crops,'R1',self.sha)

    def test_checkpoint_seed_run_identity(self):
        for key,value in [('checkpoint_sha256','b'*64),('experiment_id','R2'),('crop_count',1),('predicted_class',1)]:
            rows=copy.deepcopy(self.images);rows[0][key]=value
            with self.assertRaises(ValueError):w6.evaluate(self.records,rows,self.parents,self.crops,'R1',self.sha)

    def test_test_or_train_population_rejected(self):
        for split in ('test','train'):
            parents=copy.deepcopy(self.parents);parents[0]['split']=split
            with self.assertRaises(ValueError):w6.evaluate(self.records,self.images,parents,self.crops,'R1',self.sha)

    def test_logits_before_mean_and_tie(self):
        for row in self.records:row.pop('class_scores');row['logits']=[0]*8
        self.images=w5.aggregate(self.records,self.parents,self.crops,'R1',self.sha)
        self.assertEqual(self.images[0]['predicted_class'],0);self.evaluate()

    def test_real_loader_no_test_reader(self):
        seen=[];original=w5.read_jsonl
        def guarded(path):
            self.assertNotIn('test',Path(path).name.lower());seen.append(str(path));return original(path)
        with patch.object(w5,'read_jsonl',side_effect=guarded):
            parents,crops,_=w6.load_validation()
        self.assertEqual((len(parents),len(crops),len(seen)),(600,680,3))

    def test_artifact_traversal_and_absolute_rejected(self):
        for path in ('../escape','',str(w6.ROOT.resolve())):
            with self.assertRaises(ValueError):w6.confined(w6.ROOT,path)

    def test_draft_package_rejected_before_predictions_or_checkpoint(self):
        registry=draft_fixture(w5.read_json(w6.ROOT/'experiments/w6/registry.json'))
        with self.assertRaisesRegex(ValueError,'DRAFT'):
            w6.verify_submission(registry,'R1',{},Path('missing'),Path('missing'))

    def test_paired_r0_names(self):
        reference=copy.deepcopy(self.images)
        for r in reference:r.update(experiment_id='DINOv3_LP_run01',checkpoint_sha256=w6.R0_SHA)
        report=w6.paired_report(reference,self.images,self.parents,self.crops,'R1',self.sha)
        self.assertEqual(report['paired_outcomes']['both_correct'],['a','b'])
        self.assertIn('r0_correct_candidate_wrong',report['paired_outcomes'])

    def test_four_of_75_regression_threshold(self):
        parents=[dict(image_id='%d_%d' % (c,i),class_id=c,split='val') for c in range(8) for i in range(75)]
        crops=[dict(crop_id=p['image_id'],image_id=p['image_id'],class_id=p['class_id'],split='val') for p in parents]
        reference=[];candidate=[]
        for p in parents:
            scores=[0.]*8;scores[p['class_id']]=1.
            row=dict(image_id=p['image_id'],ground_truth=p['class_id'],predicted_class=p['class_id'],class_scores=scores,
                     crop_count=1,experiment_id='DINOv3_LP_run01',checkpoint_sha256=w6.R0_SHA)
            reference.append(row);candidate.append(dict(row,experiment_id='R1',checkpoint_sha256=self.sha))
        for cls,n in [(0,3),(4,4)]:
            for i in range(n):
                row=candidate[cls*75+i];row['predicted_class']=5;scores=[0.]*8;scores[5]=1.;row['class_scores']=scores
        report=w6.paired_report(reference,candidate,parents,crops,'R1',self.sha)
        self.assertEqual([r['class_id'] for r in report['recall_regressions']],[4])
        self.assertEqual(report['confusion_pairs']['common_masked_civet']['candidate'],4)


class SelectionTests(unittest.TestCase):
    def candidate(self,run='R1',f1=.85,accuracy=.85,cost=1):
        return dict(run_id=run,seed=42,metrics=dict(macro_f1=f1,accuracy=accuracy),inference_cost_ms=cost,benchmark_identity='SYNTHETIC')

    def test_f1_then_accuracy_then_cost_then_registered_id(self):
        a=self.candidate();b=self.candidate('R2',f1=.86)
        self.assertEqual(w6.select_seed42([a,b]),'R2')
        b['metrics']['macro_f1']=.85;b['metrics']['accuracy']=.86
        self.assertEqual(w6.select_seed42([a,b]),'R2')
        b['metrics']['accuracy']=.85;b['inference_cost_ms']=.5
        self.assertEqual(w6.select_seed42([a,b]),'R2')
        b['inference_cost_ms']=1
        self.assertEqual(w6.select_seed42([b,a]),'R1')

    def test_cost_requires_comparable_measured_setup(self):
        a=self.candidate();b=self.candidate('R2');b['benchmark_identity']='other'
        with self.assertRaisesRegex(ValueError,'unresolved'):w6.select_seed42([a,b])

    def test_never_select_best_seed(self):
        b=self.candidate();b['seed']=43
        with self.assertRaises(ValueError):w6.select_seed42([b])

    def test_sample_sd_not_best_seed_headline(self):
        rows=[dict(seed=s,recipe='R1',dataset='comparison_v1',metrics=dict(accuracy=v,macro_f1=v)) for s,v in [(42,.8),(43,.9),(44,.7)]]
        result=w6.seed_summary(rows)
        self.assertEqual(result['headline']['seed'],42);self.assertAlmostEqual(result['statistics']['accuracy']['sample_sd'],.1)
        self.assertAlmostEqual(result['statistics']['accuracy']['mean'],.8)

    def test_one_seed_sd_unknown_and_mixed_recipe_rejected(self):
        row=dict(seed=42,recipe='R1',dataset='comparison_v1',metrics=dict(accuracy=.8,macro_f1=.8))
        self.assertIsNone(w6.seed_summary([row])['statistics']['accuracy']['sample_sd'])
        with self.assertRaises(ValueError):w6.seed_summary([row,dict(row,seed=43,recipe='R2')])


class PackageTests(unittest.TestCase):
    """Positive and adversarial package fixtures are text bytes, never model weights."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.package=self.root/'package';self.package.mkdir()
        def write(path,value):
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf-8')
        self.write=write
        self.registry=w5.read_json(w6.ROOT/'experiments/w6/registry.json')
        write(self.root/'contracts/w6_registry.schema.json',w5.read_json(w6.ROOT/'contracts/w6_registry.schema.json'))
        reference_config=self.root/self.registry['runs'][0]['config_path']
        reference_config.parent.mkdir(parents=True,exist_ok=True)
        reference_config.write_bytes((w6.ROOT/self.registry['runs'][0]['config_path']).read_bytes())
        self.registry.update(protocol_status='APPROVED',approvals={'TV2':'SYNTHETIC','TV3':'SYNTHETIC'},freeze_evidence='SYNTHETIC',smoke_evidence='SYNTHETIC')
        self.runtime={'fixture':'SYNTHETIC ONLY'}
        for run in [r for r in self.registry['runs'][1:] if r.get('config_path')]:
            c=w5.read_json(w6.ROOT/run['config_path'])
            if run['run_id']=='R1':
                c['status']='FROZEN';c['runtime'].update(source_sha='a'*40,runtime_lock=w6.digest(self.runtime))
                self.config=c
                run.update(config_sha256=w6.digest(c),source_sha='a'*40,status='COMPLETED',checkpoint_sha256=None,
                    metrics={'accuracy':.8,'macro_f1':.8},evidence_paths=['SYNTHETIC'],approvals={'TV2':'SYNTHETIC','TV3':'SYNTHETIC'},
                    attempts=[dict(attempt_id='SYNTHETIC_R1',status='COMPLETED',gpu_hours=.01,evidence_path='SYNTHETIC')])
            write(self.root/run['config_path'],c)
        self.checkpoint=self.package/'fixture.bin';self.checkpoint.write_bytes(b'NOT A MODEL; SYNTHETIC FIXTURE')
        run=self.registry['runs'][1];run['checkpoint_sha256']=w5.sha256(self.checkpoint)
        self.hashes={'val.jsonl':'SYNTHETIC','b2/val.jsonl':'SYNTHETIC'}
        (self.package/'source.py').write_text('# SYNTHETIC FIXTURE\n',encoding='utf-8')
        source={'commit':'a'*40,'files_sha256':{'source.py':w5.sha256(self.package/'source.py')}}
        reload=dict(status='PASS',fresh_process=True,checkpoint_sha256=run['checkpoint_sha256'],evaluation_split='val',
            test_inference_performed=False,manifest_sha256=self.hashes,source_sha='a'*40,config_sha256=run['config_sha256'],
            runtime_sha256=w6.digest(self.runtime),comparison_policy='exact',exact_predictions_and_metrics=True)
        self.handoff=dict(run_id='R1',seed=42,checkpoint_sha256=run['checkpoint_sha256'],checkpoint_bytes=self.checkpoint.stat().st_size,
            config_sha256=run['config_sha256'],source_sha='a'*40,dataset_sha256=w5.PROVENANCE,train_dataset='comparison_v1',
            val_dataset='comparison_v1',evaluation_split='val',class_order=w5.CLASSES,manifest_sha256=self.hashes,
            aggregation='mean_crop_softmax_then_argmax',artifacts={})
        for name,value in [('config',self.config),('source_index',source),('runtime',self.runtime),('reload_report',reload),
                           ('training_log',{'fixture':True}),('crop_predictions',[]),('image_predictions',[])]:
            path=self.package/(name+'.json');write(path,value)
            self.handoff['artifacts'][name]=dict(path=path.name,sha256=w5.sha256(path))

    def verify(self):
        with patch.object(w6,'load_validation',return_value=([],[],self.hashes)):
            return w6.verify_submission(self.registry,'R1',self.handoff,self.package,self.checkpoint,self.root)

    def rewrite_artifact(self,name,value):
        entry=self.handoff['artifacts'][name];path=self.package/entry['path'];self.write(path,value);entry['sha256']=w5.sha256(path)

    def test_positive_synthetic_package(self):self.verify()

    def test_wrong_seed_source_dataset_checkpoint_rejected(self):
        for key,value in [('seed',43),('source_sha','b'*40),('dataset_sha256','b'*64),('checkpoint_sha256','b'*64),('evaluation_split','test')]:
            original=self.handoff[key];self.handoff[key]=value
            with self.assertRaises(ValueError):self.verify()
            self.handoff[key]=original

    def test_checkpoint_bytes_modified(self):
        self.checkpoint.write_bytes(b'CHANGED')
        with self.assertRaisesRegex(ValueError,'Checkpoint bytes'):self.verify()

    def test_missing_and_tampered_artifacts(self):
        for name in list(self.handoff['artifacts']):
            entry=self.handoff['artifacts'][name];path=self.package/entry['path'];before=path.read_bytes();path.write_bytes(b'CHANGED')
            with self.assertRaisesRegex(ValueError,'Artifact SHA'):self.verify()
            path.write_bytes(before)

    def test_source_index_must_bind_real_bytes(self):
        (self.package/'source.py').write_text('# MODIFIED',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Source file SHA'):self.verify()

    def test_runtime_rehashed_artifact_still_bound_to_frozen_config(self):
        self.rewrite_artifact('runtime',{'fixture':'changed runtime'})
        with self.assertRaisesRegex(ValueError,'Runtime lock'):self.verify()

    def test_bare_pass_reload_not_enough(self):
        self.rewrite_artifact('reload_report',{'status':'PASS','fresh_process':True})
        with self.assertRaisesRegex(ValueError,'reload receipt'):self.verify()

    def test_relaxed_tolerance_or_test_reload_rejected(self):
        path=self.package/self.handoff['artifacts']['reload_report']['path'];original=w5.read_json(path)
        for key,value in [('comparison_policy','relaxed'),('evaluation_split','test'),('config_sha256','b'*64),('exact_predictions_and_metrics',False)]:
            bad=copy.deepcopy(original);bad[key]=value;self.rewrite_artifact('reload_report',bad)
            with self.assertRaisesRegex(ValueError,'reload receipt'):self.verify()


class GeometryTests(unittest.TestCase):
    def setUp(self):
        from scripts.review_tv1_w6 import check_geometry
        self.check=check_geometry
        self.parent=dict(image_id='synthetic',class_id=0,label=w5.CLASSES[0],split='train',width=30,height=20,
                         boxes=[dict(annotation_id='ann',label=w5.CLASSES[0],bbox_xywh=[.5,.5,20,16])],quality={'sha256':'SYNTHETIC'})
        self.crop=dict(crop_id='synthetic_ann',image_id='synthetic',annotation_id='ann',class_id=0,label=w5.CLASSES[0],
                       split='train',quality=self.parent['quality'],width=30,height=20,
                       bbox_xyxy=[0,0,20,16],parent_crop_count=1,sample_weight=1)

    def test_round_half_even_geometry_and_weight(self):
        self.assertEqual(self.check([self.parent],[self.crop])['crops'],1)

    def test_geometry_and_weight_mutations(self):
        for key,value in [('bbox_xyxy',[1,1,21,17]),('sample_weight',.5),('parent_crop_count',2),('class_id',1)]:
            bad=copy.deepcopy(self.crop);bad[key]=value
            with self.assertRaises(ValueError):self.check([self.parent],[bad])


if __name__=='__main__':unittest.main()
