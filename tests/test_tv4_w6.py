"""W6 routing, provenance, fail-closed pins and cache identity; no official Test."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import torch
from PIL import Image

from src.demo.classifier import ClassifierCache
from src.demo.dino import DinoCache
from src.demo.dino_w6 import W6Cache, REGISTRY, MODEL_IDS
from src.demo.inference import analyze_classified


class W6Tests(unittest.TestCase):
    def setUp(self):
        self.base=DinoCache(ClassifierCache())
        self.cache=W6Cache(self.base,None)
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture=Path(temporary.name)

    def test_no_r5_r6_and_default_disabled(self):
        status=self.cache.status()
        self.assertEqual(set(self.cache.registry()['models']),set(MODEL_IDS))
        self.assertTrue(all(not status[k]['enabled'] for k in MODEL_IDS))
        self.assertFalse(any('R5' in k or 'R6' in k for k in status))

    def test_pooling_registry_has_distinct_pins(self):
        models=self.cache.registry()['models']
        self.assertEqual(models['DINO_W6_R1']['feature_dim'],768)
        self.assertEqual([models[k]['feature_dim'] for k in MODEL_IDS[1:]],[384]*3)
        self.assertEqual(len({m['checkpoint_sha256'] for m in models.values()}),4)

    def test_legacy_routing(self):
        with patch.object(self.base,'predict',return_value=('legacy',{})) as old:
            self.assertEqual(self.cache.predict(None,[],'B2')[0],'legacy')
            old.assert_called_once()

    def test_pinned_path_cannot_escape_outputs(self):
        with self.assertRaises(ValueError): self.cache.folder({'package':'../outside'})

    def test_per_detection_top3_and_ties(self):
        logits=torch.tensor([[0.]*8,list(range(8))],dtype=torch.float32)
        boxes=[{'bbox_xywh':[0,0,20,40]},{'bbox_xywh':[30,50,20,40]}]
        with patch.object(self.cache,'logits',return_value=(logits,{})) as forward:
            top,_=self.cache.predict(Image.new('RGB',(100,240)),boxes,'DINO_W6_R2')
        self.assertEqual([p['class_id'] for p in top[0]],[0,1,2])
        self.assertEqual([p['class_id'] for p in top[1]],[7,6,5])
        self.assertEqual([im.size for im in forward.call_args.args[0]],[(20,40),(20,40)])

    def test_missing_candidate_is_error_never_legacy_fallback(self):
        stream=io.BytesIO(); Image.new('RGB',(100,100)).save(stream,'PNG')
        detector=Mock(model_sha256='0'*64)
        detector.predict.return_value={'detections':[{'category':'1','conf':.9,'bbox':[.1,.1,.5,.5]}]}
        with patch.object(self.base,'predict',side_effect=AssertionError('fallback forbidden')):
            result=analyze_classified(stream.getvalue(),'fixture.png',classifier='DINO_W6_R2',
                cache=self.cache,adapter=detector)
        self.assertEqual(result['result']['status'],'error')
        self.assertEqual(result['result']['pipeline']['classifier_id'],'DINO_W6_R2')
        self.assertEqual(result['result']['error']['stage'],'classify')
        self.assertEqual(result['result']['detections'],[])

    def test_invalid_registry_format_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'registry.json'
            config=json.loads(REGISTRY.read_text())
            config['models']['DINO_W6_R5']=config['models']['DINO_W6_R2']
            path.write_text(json.dumps(config))
            with self.assertRaises(ValueError): W6Cache(self.base,None,path).registry()

    def test_size_and_hash_mismatch_even_warm(self):
        with tempfile.TemporaryDirectory(dir=REGISTRY.parents[1]/'outputs') as temp:
            folder=Path(temp); (folder/'best_model.pt').write_bytes(b'bad')
            config=json.loads(REGISTRY.read_text()); key='DINO_W6_R2'
            config['models'][key]['package']=str(folder.relative_to(REGISTRY.parents[1]))
            registry=folder/'config.json'; registry.write_text(json.dumps(config))
            cache=W6Cache(self.base,folder,registry)
            cache.models['old']=('dummy','dummy')
            with self.assertRaisesRegex(ValueError,'size mismatch'): cache.validate(key)
            config['models'][key]['checkpoint_bytes']=3; registry.write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError,'checksum mismatch'): cache.validate(key)

    def fake_loader(self):
        registry=self.cache.registry()
        entry=copy.deepcopy(registry['models']['DINO_W6_R2'])
        config={'preprocessing':{'resize':[256,256]},'dataset':'comparison_v1','dataset_sha256':'d'*64}
        native=Mock()
        payload={'class_map':{str(i):name for i,name in enumerate(self.base.names())},
                 'config':config,'model':{'weight':torch.ones(1)}}
        (self.fixture/'class_map.json').write_text(json.dumps(payload['class_map']))
        native.load_package.side_effect=lambda *args:(torch.nn.Identity(),None,payload)
        native.predict_crops.side_effect=lambda model,transform,crops,device:torch.zeros((len(crops),8))
        return native,config,entry,registry

    def test_microbatch_and_cache_invalidation_by_config_identity(self):
        native,config,entry,registry=self.fake_loader()
        crops=[Image.new('RGB',(10,10))]*9
        with patch.object(self.cache,'validate',side_effect=lambda kind:(native,self.fixture,config,entry,registry)):
            _,cold=self.cache.logits(crops,'DINO_W6_R2')
            self.assertFalse(cold['cache_hit'])
            self.assertEqual([len(call.args[2]) for call in native.predict_crops.call_args_list],[8,1])
            _,warm=self.cache.logits(crops,'DINO_W6_R2');self.assertTrue(warm['cache_hit'])
            entry['source_sha']='f'*40
            _,changed=self.cache.logits(crops,'DINO_W6_R2');self.assertFalse(changed['cache_hit'])
        self.assertEqual(native.load_package.call_count,2)

    def test_invalid_logit_shape_and_nonfinite_fail_without_partial_results(self):
        for bad in (torch.zeros((1,7)),torch.full((1,8),float('nan'))):
            native,config,entry,registry=self.fake_loader()
            native.predict_crops.side_effect=None;native.predict_crops.return_value=bad
            self.cache.models.clear()
            with patch.object(self.cache,'validate',return_value=(native,self.fixture,config,entry,registry)):
                with self.assertRaisesRegex(ValueError,'Invalid W6 per-box logits'):
                    self.cache.logits([Image.new('RGB',(10,10))],'DINO_W6_R2')


if __name__=='__main__': unittest.main()
