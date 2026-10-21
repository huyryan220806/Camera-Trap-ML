"""Synthetic checkpoint/HTTP regressions; not official B1/B2 model results."""
import base64
from concurrent.futures import ThreadPoolExecutor
import copy
import io
import json
from pathlib import Path
import tempfile
import threading
import sys
import unittest
from unittest.mock import Mock, patch
from http.server import ThreadingHTTPServer

from PIL import Image
import requests
import torch

from src.demo.classifier import ClassifierCache, checkpoint_model, crop_coordinates, ROOT
from src.demo.detector import digest
from src.demo.inference import analyze_classified, validate_envelope
from src.models.b0 import build_b0
from src.data.b0_dataset import make_transform
sys.path.insert(0, str(ROOT / 'scripts'))
from scripts.run_demo import make_handler
from scripts.prepare_tv4_classifier import prepare


def picture():
    stream = io.BytesIO()
    Image.new('RGB', (120, 100), (85, 140, 50)).save(stream, 'JPEG')
    return stream.getvalue()


class TwoAnimals:
    model_sha256 = 'a' * 64

    def predict(self, image, threshold):
        return {'detections': [
            {'category': '1', 'conf': 0.9, 'bbox': [0, 0, .4, .8]},
            {'category': '1', 'conf': 0.8, 'bbox': [.5, .1, .4, .8]},
            {'category': '2', 'conf': 0.9, 'bbox': [0, 0, .2, .2]}]}


class ClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        (cls.root / 'outputs').mkdir()
        (cls.root / 'data/processed/v1').mkdir(parents=True)
        classes = (ROOT / 'data/processed/v1/class_map.json').read_bytes()
        (cls.root / 'data/processed/v1/class_map.json').write_bytes(classes)
        cls.names = list(json.loads(classes).values())
        cls.registry = json.loads((ROOT / 'configs/demo_classifiers.json').read_text())
        cls.registry['models']['B2']['checkpoint_format'] = 'tv4-v1'
        cls.config = json.loads((ROOT / 'experiments/B0_run01/config.yaml').read_text())
        torch.manual_seed(42)
        model = build_b0(8, pretrained=False)
        cls.state = model.state_dict()
        cls.base = {'model_name': 'resnet18', 'model_state_dict': cls.state, 'freeze_backbone': True,
                    'num_classes': 8, 'idx_to_class': dict(enumerate(cls.names)),
                    'class_to_idx': {v: i for i, v in enumerate(cls.names)}, 'config': cls.config}
        cls.checkpoints = {}
        for kind in ('B0', 'B1', 'B2'):
            checkpoint = {**cls.base, 'kind': 'OFFICIAL', 'freeze_backbone': kind == 'B0'}
            if kind == 'B2':
                checkpoint['config'] = {'model': {'backbone': 'resnet18'}}
                checkpoint['inference_preprocessing'] = cls.registry['models']['B2']['preprocessing']
                checkpoint['model_state_dict'] = {
                    ('classifier.1.' + k[3:] if k.startswith('fc.') else 'backbone.' + k): v
                    for k, v in cls.state.items()}
            cls.checkpoints[kind] = checkpoint
            path = cls.root / 'outputs' / (kind + '.pth')
            torch.save(checkpoint, path)
            cls.registry['models'][kind].update(enabled=True, checkpoint='outputs/' + path.name,
                                               sha256=digest(path), checkpoint_bytes=path.stat().st_size)
        cls.registry_path = cls.root / 'registry.json'

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.registry_path.write_text(json.dumps(self.registry))
        self.cache = ClassifierCache(self.registry_path, self.root)
        self.image = Image.new('RGB', (120, 100), (85, 140, 50))
        self.boxes = [{'bbox_xywh': [0, 0, 48, 80]}, {'bbox_xywh': [60, 10, 48, 80]}]

    def test_real_architecture_top3_and_warm_cache(self):
        first, cold = self.cache.predict(self.image, self.boxes, 'B0')
        second, warm = self.cache.predict(self.image, self.boxes, 'B0')
        self.assertEqual(first, second)
        self.assertFalse(cold['cache_hit'])
        self.assertTrue(warm['cache_hit'])
        self.assertEqual(warm['model_load_count'], 1)
        self.assertEqual(len(first), 2)
        for top in first:
            self.assertEqual(len({p['class_id'] for p in top}), 3)
            self.assertEqual([p['score'] for p in top], sorted((p['score'] for p in top), reverse=True))

    def test_b1_b2_switch_and_bounded_cache(self):
        for kind in ('B0', 'B1', 'B2'):
            top, metadata = self.cache.predict(self.image, self.boxes, kind)
            self.assertEqual(metadata['classifier_id'], kind)
            self.assertEqual(len(top[0]), 3)
        self.assertEqual(len(self.cache.models), 2)
        self.cache.predict(self.image, self.boxes, 'B0')
        self.assertEqual(self.cache.load_count, 4)

    def test_concurrent_first_requests_load_once(self):
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: self.cache.predict(self.image, self.boxes, 'B0'), range(3)))
        self.assertEqual(self.cache.load_count, 1)
        self.assertEqual(sum(not m['cache_hit'] for _, m in results), 1)

    def test_hash_checked_even_when_warm(self):
        self.cache.predict(self.image, self.boxes, 'B0')
        with patch('src.demo.classifier.digest', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'checksum'):
                self.cache.predict(self.image, self.boxes, 'B0')

    def test_registry_change_invalidates_cache(self):
        self.cache.predict(self.image, self.boxes, 'B0')
        altered = copy.deepcopy(self.registry)
        alternate = self.root / 'outputs/alternate.pth'
        changed = {**self.base, 'epoch': 9}
        torch.save(changed, alternate)
        altered['models']['B0'].update(checkpoint='outputs/alternate.pth', sha256=digest(alternate),
                                      checkpoint_bytes=alternate.stat().st_size)
        self.registry_path.write_text(json.dumps(altered))
        _, metadata = self.cache.predict(self.image, self.boxes, 'B0')
        self.assertFalse(metadata['cache_hit'])
        self.assertEqual(self.cache.load_count, 2)

    def test_disabled_missing_and_bad_size_do_not_load(self):
        for change in ({'enabled': False}, {'checkpoint': 'outputs/missing.pth'},
                       {'checkpoint_bytes': 1}, {'sha256': None}, {'checkpoint': '../private.pth'}):
            with self.subTest(change=change):
                config = copy.deepcopy(self.registry)
                config['models']['B0'].update(change)
                self.registry_path.write_text(json.dumps(config))
                with self.assertRaises((ValueError, OSError)):
                    self.cache.predict(self.image, self.boxes, 'B0')
        self.assertEqual(self.cache.load_count, 0)

    def test_wrong_mapping_transform_and_kind_rejected(self):
        for kind, changes in [('B0', {'idx_to_class': {}}), ('B0', {'class_to_idx': {}}),
                              ('B0', {'freeze_backbone': False}), ('B1', {'kind': 'SYNTHETIC_SMOKE'}),
                              ('B2', {'inference_preprocessing': {}}), ('B2', {'idx_to_class': {}})]:
            with self.subTest(kind=kind, changes=changes), self.assertRaises(ValueError):
                checkpoint_model({**self.checkpoints[kind], **changes}, kind, self.registry['models'][kind], self.names)
        entry = copy.deepcopy(self.registry['models']['B0'])
        entry['preprocessing']['resize_size'] = 240
        with self.assertRaises(ValueError):
            checkpoint_model(self.base, 'B0', entry, self.names)

    def test_nonfinite_and_wrong_shape_weights_rejected(self):
        for weight in (torch.full_like(self.state['fc.weight'], float('nan')), torch.zeros(7, 512)):
            state = {**self.state, 'fc.weight': weight}
            with self.assertRaises((ValueError, RuntimeError)):
                checkpoint_model({**self.base, 'model_state_dict': state}, 'B0', self.registry['models']['B0'], self.names)

    def test_transform_and_b2_remapping_match(self):
        self.image.paste((210, 20, 30), (0, 0, 60, 100))
        b0, transform = checkpoint_model(self.base, 'B0', self.registry['models']['B0'], self.names)
        self.assertTrue(torch.equal(transform(self.image), make_transform(self.config, False)(self.image)))
        b2, _ = checkpoint_model(self.checkpoints['B2'], 'B2', self.registry['models']['B2'], self.names)
        tensor = torch.randn(2, 3, 224, 224)
        with torch.inference_mode():
            self.assertTrue(torch.equal(b0(tensor), b2(tensor)))

    def native_b2(self):
        entry = copy.deepcopy(self.registry['models']['B2'])
        entry['checkpoint_format'] = 'tv3-native-v1'
        spec = entry['preprocessing']
        checkpoint = {
            'model_state_dict': self.checkpoints['B2']['model_state_dict'],
            'config': {'model': {'backbone': 'resnet18', 'num_classes': 8}},
            'num_classes': 8, 'backbone_name': 'resnet18', 'is_official': True,
            'class_map': self.base['class_to_idx'], 'id_to_label': self.base['idx_to_class'],
            'provenance_sha256': entry['provenance_sha256'],
            'preprocessing': {'resize': 256, 'crop_size': 224, 'mean': spec['mean'], 'std': spec['std'],
                              'val_transforms': 'Resize(256) -> CenterCrop(224) -> ToTensor() -> Normalize()'},
        }
        return checkpoint, entry

    def test_native_b2_remapping_and_center_crop_equivalent(self):
        checkpoint, entry = self.native_b2()
        model, transform = checkpoint_model(checkpoint, 'B2', entry, self.names)
        canonical, _ = checkpoint_model(self.checkpoints['B2'], 'B2', self.registry['models']['B2'], self.names)
        tensor = torch.randn(2, 3, 224, 224)
        with torch.inference_mode():
            self.assertTrue(torch.equal(model(tensor), canonical(tensor)))
        self.assertTrue(torch.equal(transform(self.image), make_transform(self.config, False)(self.image)))
        self.assertNotIn('kind', checkpoint)  # Adapter must not mutate the artifact metadata.

    def test_native_b2_rejects_missing_or_inconsistent_handoff(self):
        checkpoint, entry = self.native_b2()
        changes = [
            {'is_official': False}, {'is_official': 1}, {'class_map': {}}, {'id_to_label': {}},
            {'provenance_sha256': '0' * 64}, {'backbone_name': 'resnet50'},
            {'config': {'model': {'backbone': 'resnet18', 'num_classes': 7}}},
            {'preprocessing': {}}, {'kind': 'OFFICIAL'},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                checkpoint_model({**checkpoint, **change}, 'B2', entry, self.names)
        for change in ({'provenance_sha256': None}, {'checkpoint_format': 'guess'}):
            with self.subTest(entry=change), self.assertRaises(ValueError):
                checkpoint_model(checkpoint, 'B2', {**entry, **change}, self.names)

    def test_native_b2_cache_safe_load_and_multiple_boxes(self):
        checkpoint, entry = self.native_b2()
        path = self.root / 'outputs/native_b2.pth'
        torch.save(checkpoint, path)
        config = copy.deepcopy(self.registry)
        entry.update(checkpoint='outputs/native_b2.pth', sha256=digest(path), checkpoint_bytes=path.stat().st_size)
        config['models']['B2'] = entry
        self.registry_path.write_text(json.dumps(config))
        first, cold = self.cache.predict(self.image, self.boxes, 'B2')
        second, warm = self.cache.predict(self.image, self.boxes, 'B2')
        self.assertEqual(first, second)
        self.assertEqual(len(first), 2)
        self.assertFalse(cold['cache_hit'])
        self.assertTrue(warm['cache_hit'])
        self.assertEqual(warm['model_load_count'], 1)

    def test_prepare_b1_copy_resume_and_no_network(self):
        config = copy.deepcopy(self.registry)
        with tempfile.TemporaryDirectory(dir=self.root / 'outputs') as temp:
            relative = Path(temp).relative_to(self.root) / 'installed.pth'
            config['models']['B1']['checkpoint'] = relative.as_posix()
            self.registry_path.write_text(json.dumps(config))
            with patch('scripts.prepare_tv4_classifier.requests.get') as network, patch('builtins.print'):
                first = prepare(self.root / 'outputs/B1.pth', 'B1', self.cache)
                second = prepare(model='B1', cache=self.cache)
            network.assert_not_called()
            self.assertEqual(first['status'], 'complete')
            self.assertTrue(second['classifier']['cache_hit'])
            self.assertEqual(digest(self.root / relative), config['models']['B1']['sha256'])

    def test_prepare_refuses_disabled_model_and_bad_source(self):
        config = copy.deepcopy(self.registry)
        config['models']['B2']['enabled'] = False
        config['models']['B1']['checkpoint'] = 'outputs/should_not_exist.pth'
        self.registry_path.write_text(json.dumps(config))
        with patch('scripts.prepare_tv4_classifier.requests.get') as network:
            with self.assertRaisesRegex(ValueError, 'pending verified handoff'):
                prepare(model='B2', cache=self.cache)
            with self.assertRaisesRegex(ValueError, 'SHA/size'):
                prepare(self.root / 'outputs/B0.pth', 'B1', self.cache)
        network.assert_not_called()
        self.assertFalse((self.root / 'outputs/should_not_exist.pth').exists())

    def test_each_box_uses_its_own_pixels(self):
        self.image.paste((210, 20, 30), (0, 0, 60, 100))
        self.image.paste((20, 30, 210), (60, 0, 120, 100))
        predictions, _ = self.cache.predict(self.image, self.boxes, 'B0')
        self.assertNotEqual(predictions[0], predictions[1])

    def test_bad_logits_fail_before_top3(self):
        for logits in (torch.full((2, 8), float('nan')), torch.zeros(2, 7)):
            with self.subTest(shape=logits.shape):
                model = Mock(return_value=logits)
                with patch.object(self.cache, '_get', return_value=(model, lambda _: torch.zeros(3, 224, 224), self.names, {})):
                    with self.assertRaises(ValueError):
                        self.cache.predict(self.image, self.boxes, 'B0')

    def test_invalid_review_threshold_is_rejected(self):
        for value in (True, -1, 2, float('nan'), '0.7'):
            with self.assertRaises(ValueError):
                analyze_classified(picture(), 'a.jpg', mode='mock', review_threshold=value)

    def test_invalid_and_tiny_boxes_fail_without_partial_output(self):
        for box in ([0, 0, 1, 1], [-1, 0, 20, 20], [0, 0, 1000, 20], [float('nan'), 0, 20, 20]):
            with self.assertRaises(ValueError):
                crop_coordinates(box, (120, 100))
        with self.assertRaises(ValueError):
            self.cache.predict(self.image, self.boxes * 33, 'B0')
        with self.assertRaises(ValueError):
            self.cache.predict(self.image, [], 'B0')
        self.assertEqual(crop_coordinates([.4, .6, 20, 30], (120, 100)), (0, 1, 20, 31))

    def test_inference_envelope_and_ignored_person(self):
        output = analyze_classified(picture(), 'a.jpg', cache=self.cache, adapter=TwoAnimals(), review_threshold=1)
        validate_envelope(output)
        self.assertEqual(len(output['result']['detections']), 2)
        self.assertEqual(output['result']['status'], 'needs_review')
        self.assertEqual(output['provenance']['ignored_non_animals'], 1)
        self.assertFalse(output['provenance']['scores_calibrated'])
        self.assertIn('distribution shift', ' '.join(output['provenance']['warnings']))

    def test_decode_empty_and_detector_error_skip_classifier(self):
        never = Mock()
        bad = analyze_classified(b'bad', 'bad.jpg', cache=never, adapter=TwoAnimals())
        empty = analyze_classified(picture(), 'a.jpg', mode='mock', scenario='empty', cache=never)
        failed = analyze_classified(picture(), 'a.jpg', mode='mock', scenario='error', cache=never)
        self.assertEqual(bad['result']['error']['stage'], 'read')
        self.assertEqual(empty['result']['status'], 'no_detection')
        self.assertEqual(failed['result']['error']['stage'], 'detect')
        never.predict.assert_not_called()

    def test_classifier_error_has_no_fake_or_partial_predictions(self):
        cache = Mock()
        cache.predict.side_effect = ValueError('bad checkpoint')
        output = analyze_classified(picture(), 'a.jpg', cache=cache, adapter=TwoAnimals())
        self.assertEqual(output['result']['pipeline']['mode'], 'inference')
        self.assertEqual(output['result']['error']['stage'], 'classify')
        self.assertEqual(output['result']['detections'], [])

    def test_mock_multiple_is_explicit_without_loading(self):
        never = Mock()
        output = analyze_classified(picture(), 'a.jpg', cache=never, mode='mock', scenario='multiple')
        self.assertEqual(output['result']['pipeline']['mode'], 'mock')
        self.assertEqual(output['result']['pipeline']['classifier_id'], 'mock-scores-v1')
        self.assertEqual(len(output['result']['detections']), 2)
        self.assertIsNone(output['provenance']['classifier'])
        never.predict.assert_not_called()

    def test_http_classifier_and_export_contract(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(TwoAnimals(), [], self.cache))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = 'http://127.0.0.1:' + str(server.server_port)
        try:
            config = requests.get(url + '/api/config', timeout=10).json()
            self.assertTrue(config['classifiers']['B0']['checkpoint_present'])
            payload = {'image_base64': base64.b64encode(picture()).decode(), 'classifier': 'B0', 'mode': 'megadetector'}
            response = requests.post(url + '/api/analyze', json=payload, timeout=30)
            self.assertEqual(response.status_code, 200)
            validate_envelope(response.json()['classification'])
            self.assertTrue(response.json()['preview'].startswith('data:image/jpeg'))
            payload['classifier'] = 'unknown'
            self.assertEqual(requests.post(url + '/api/analyze', json=payload, timeout=10).status_code, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
