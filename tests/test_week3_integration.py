"""Shared package exports must survive merging the TV2 and TV3 branches."""
from pathlib import Path
import subprocess
import sys
import unittest


class WeekThreeIntegrationTests(unittest.TestCase):
    def test_base_packages_do_not_eagerly_load_torch(self):
        code = ('import sys; import src.models, src.evaluation; '
                'from src.evaluation import compute_metrics; '
                'assert "torch" not in sys.modules')
        subprocess.run([sys.executable, '-c', code],
                       cwd=Path(__file__).resolve().parents[1], check=True, timeout=30)

    def test_both_evaluation_interfaces_export_original_functions(self):
        from src import evaluation
        from src.evaluation import metrics, b2_evaluator
        for name in evaluation.__all__:
            original = metrics if name in ('compute_metrics', 'load_class_map', 'plot_confusion_matrix') else b2_evaluator
            self.assertIs(getattr(evaluation, name), getattr(original, name))
        with self.assertRaises(AttributeError):
            getattr(evaluation, 'missing_helper')

    def test_native_model_interface_preserved(self):
        from src import models
        from src.models import b2_classifier
        for name in models.__all__:
            self.assertIs(getattr(models, name), getattr(b2_classifier, name))
        with self.assertRaises(AttributeError):
            getattr(models, 'missing_model')
