import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_tv4_b2_handoff import metrics_match


class HandoffMetricTests(unittest.TestCase):
    def test_rounded_loss_only_tolerance(self):
        expected = {'weighted_val_loss': 0.8178, 'accuracy': 0.7294, 'confusion_matrix': [[2, 1], [0, 3]]}
        actual = {**expected, 'weighted_val_loss': 0.8177}
        self.assertTrue(metrics_match(actual, expected, crop=True))
        self.assertFalse(metrics_match({**actual, 'accuracy': 0.7295}, expected, crop=True))
        self.assertFalse(metrics_match({**actual, 'weighted_val_loss': 0.8176}, expected, crop=True))
        self.assertEqual(actual['weighted_val_loss'], 0.8177)

    def test_invalid_missing_loss_rejected(self):
        for loss in (None, float('nan'), float('inf'), '0.8178'):
            self.assertFalse(metrics_match({'weighted_val_loss': loss}, {'weighted_val_loss': 0.8178}, crop=True))
        self.assertFalse(metrics_match({}, {}, crop=True))

    def test_image_metrics_exact(self):
        self.assertTrue(metrics_match({'accuracy': .7467}, {'accuracy': .7467}))
        self.assertFalse(metrics_match({'accuracy': .7466}, {'accuracy': .7467}))
