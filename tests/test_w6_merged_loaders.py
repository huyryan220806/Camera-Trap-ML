"""Exercise merged loader routing with real frozen metadata, without model training."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.demo.classifier import ClassifierCache
from src.demo.dino import DinoCache
from src.demo.dino_w6 import W6Cache
from src.demo.detector import ROOT, digest


class MergedW6LoadersTests(unittest.TestCase):
    def test_all_frozen_candidates_route_to_exact_source_snapshots(self):
        original = json.loads((ROOT / 'configs/demo_w6_r6.json').read_text())
        for run in ('R1', 'R2', 'R3', 'R4', 'R6'):
            with self.subTest(run=run), tempfile.TemporaryDirectory(dir=ROOT / 'outputs') as temp:
                folder = Path(temp)
                config = copy.deepcopy(original)
                entry = config['models']['DINO_W6_' + run]
                source = ROOT / 'reports/tv3/w6/results' / (run + '_attempt01')
                for name in ('config.json', 'handoff.json', 'source_index.json',
                             'preprocessing.json', 'class_map.json'):
                    shutil.copyfile(source / name, folder / name)
                # Metadata/source checks are real; a dummy checkpoint avoids inference.
                (folder / 'best_model.pt').write_bytes(b'fixture')
                entry.update(package=folder.relative_to(ROOT).as_posix(),
                             checkpoint_bytes=7,
                             checkpoint_sha256=hashlib.sha256(b'fixture').hexdigest())
                registry = folder / 'registry.json'
                registry.write_text(json.dumps(config), encoding='utf-8')
                cache = W6Cache(DinoCache(ClassifierCache()), folder, registry)
                with patch('src.demo.dino_w6.subprocess.check_output',
                           side_effect=[original['vendor_commit'] + '\n', '']):
                    native, _, frozen, _, _ = cache.validate('DINO_W6_' + run)
                expected = 'dino_w6_r6.py' if run == 'R6' else 'dino_w6_r1_r4.py'
                self.assertEqual(Path(native.__file__).name, expected)
                self.assertEqual(digest(Path(native.__file__)),
                                 entry.get('native_source_sha256', original['native_source_sha256']))
                self.assertEqual(frozen['run_id'], run)

    def test_training_entrypoint_keeps_r6_three_hour_support(self):
        from src.training.dino_w6 import validate_config
        config = json.loads((ROOT / 'configs/w6/tv3/R6.3h.frozen.json').read_text())
        validate_config(config)
        self.assertEqual(config['max_gpu_hours'], 3)
        self.assertEqual(digest(ROOT / 'src/training/dino_w6.py'),
                         digest(ROOT / 'src/training/dino_w6_r6.py'))


if __name__ == '__main__':
    unittest.main()
