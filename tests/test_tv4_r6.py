"""R6 opt-in and locked native selection; R5 remains excluded."""
import json
from pathlib import Path
import tempfile
import unittest

from src.demo.classifier import ClassifierCache
from src.demo.dino import DinoCache
from src.demo.dino_w6 import W6Cache, MODEL_IDS, SUPPORTED_MODEL_IDS
from src.demo.detector import ROOT, digest


class R6Tests(unittest.TestCase):
    def setUp(self):
        self.cache=W6Cache(DinoCache(ClassifierCache()),None,ROOT/'configs/demo_w6_r6.json')

    def test_explicit_opt_in_preserves_legacy_and_excludes_r5(self):
        models=self.cache.registry()['models']
        self.assertEqual(set(models),set(SUPPORTED_MODEL_IDS))
        self.assertNotIn('DINO_W6_R5',models)
        legacy=W6Cache(self.cache.base,None)
        self.assertEqual(set(legacy.registry()['models']),set(MODEL_IDS))
        with self.assertRaisesRegex(ValueError,'not configured'):
            legacy.validate('DINO_W6_R6')

    def test_r6_metadata_and_pins_are_distinct(self):
        entry=self.cache.registry()['models']['DINO_W6_R6']
        self.assertEqual(entry['checkpoint_sha256'],'24e3f51418dd7492a7537dff629794547c4540e8929bfe3e566105a6486581ef')
        self.assertEqual(entry['dataset_version'],'train_expansion_w6_v1')
        self.assertEqual(entry['native_module'],'dino_w6_r6')
        self.assertEqual(digest(ROOT/'src/training/dino_w6_r6.py'),entry['native_source_sha256'])
        self.assertNotEqual(entry['native_source_sha256'],self.cache.registry()['native_source_sha256'])
        self.assertEqual(self.cache.status()['DINO_W6_R6']['dataset'],'train_expansion_w6_v1')

    def test_registry_r5_injection_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'registry.json'; value=self.cache.registry()
            value['models']['DINO_W6_R5']=value['models']['DINO_W6_R6']
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):W6Cache(self.cache.base,None,path).registry()


if __name__=='__main__':unittest.main()
