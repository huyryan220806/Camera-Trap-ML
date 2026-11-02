"""Candidate routing/failure gates without training or touching official Test."""
import io
import unittest
from unittest.mock import Mock, patch

from PIL import Image
import torch

from src.demo.classifier import ClassifierCache
from src.demo.dino import DinoCache, MODEL_ID
from src.demo.inference import analyze_classified


class DinoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.base = ClassifierCache()
        self.cache = DinoCache(self.base)
        self.image = Image.new('RGB', (100, 80))
        self.boxes = [{'bbox_xywh': [1, 2, 20, 30]}, {'bbox_xywh': [30, 10, 40, 40]}]

    def test_per_box_top3_and_lowest_id_tie(self):
        logits = torch.tensor([[0., 0., 0., 0., 0., 0., 0., 0.], [0., 1., 2., 3., 4., 5., 6., 7.]])
        with patch.object(self.cache, 'logits', return_value=(logits, {})) as forward:
            predictions, _ = self.cache.predict(self.image, self.boxes, MODEL_ID)
        self.assertEqual([p['class_id'] for p in predictions[0]], [0, 1, 2])
        self.assertEqual([p['class_id'] for p in predictions[1]], [7, 6, 5])
        self.assertEqual([im.size for im in forward.call_args.args[0]], [(20, 30), (40, 40)])

    def test_b2_is_separate_and_dino_unconfigured_disabled(self):
        self.assertFalse(self.cache.status()[MODEL_ID]['enabled'])
        with patch.object(self.base, 'predict', return_value=('B2', {})) as base:
            self.assertEqual(self.cache.predict(self.image, self.boxes, 'B2')[0], 'B2')
            base.assert_called_once()

    def test_real_dino_missing_package_is_classifier_error_no_b2_fallback(self):
        stream = io.BytesIO(); self.image.save(stream, 'PNG')
        adapter = Mock()
        adapter.model_sha256 = '0' * 64
        adapter.predict.return_value = {'detections': [{'category':'1','conf':.9,'bbox':[.1,.1,.5,.5]}]}
        with patch.object(self.base, 'predict', side_effect=AssertionError('Unexpected B2 fallback')):
            output = analyze_classified(stream.getvalue(), 'fixture.png', classifier=MODEL_ID,
                                        cache=self.cache, adapter=adapter)
        self.assertEqual(output['result']['status'], 'error')
        self.assertEqual(output['result']['error']['stage'], 'classify')
        self.assertEqual(output['result']['detections'], [])
        self.assertEqual(output['result']['pipeline']['classifier_id'], MODEL_ID)


if __name__ == '__main__':
    unittest.main()
