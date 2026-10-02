import json
from pathlib import Path
import tempfile
import unittest

import matplotlib
import numpy as np

matplotlib.use("Agg")

from src.evaluation.metrics import compute_metrics, load_class_map, plot_confusion_matrix


ROOT = Path(__file__).resolve().parents[1]
CLASS_MAP = ROOT / "data" / "processed" / "v1" / "class_map.json"


class EvaluationMetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.labels, cls.target_names = load_class_map(CLASS_MAP)

    def test_project_class_map_has_eight_classes_in_numeric_order(self):
        self.assertEqual(self.labels, list(range(8)))
        self.assertEqual(len(self.target_names), 8)

    def test_all_eight_classes_predicted_correctly(self):
        result = compute_metrics(self.labels, self.labels, CLASS_MAP)
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["macro_f1"], 1.0)
        self.assertEqual(result["confusion_matrix"].shape, (8, 8))

    def test_single_present_class_still_averages_over_all_classes(self):
        result = compute_metrics([0, 0, 0], [0, 0, 0], CLASS_MAP)
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["macro_f1"], 0.125)
        self.assertEqual(result["confusion_matrix"].shape, (8, 8))

    def test_unpredicted_ground_truth_class_has_zero_recall_and_f1(self):
        result = compute_metrics([0, 1, 1], [0, 0, 0], CLASS_MAP)
        class_name = self.target_names[1]
        self.assertEqual(result["classification_report"][class_name]["recall"], 0.0)
        self.assertEqual(result["classification_report"][class_name]["f1-score"], 0.0)
        self.assertFalse(np.isnan(result["macro_f1"]))

    def test_empty_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            compute_metrics([], [], CLASS_MAP)

    def test_length_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "same length"):
            compute_metrics([0, 1, 2], [0, 1], CLASS_MAP)

    def test_unknown_class_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown class ID"):
            compute_metrics([0, 99], [0, 0], CLASS_MAP)

    def test_plot_includes_missing_classes_and_saves_figure(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "confusion_matrix.png"
            fig, matrix = plot_confusion_matrix(
                [0, 0, 0], [0, 0, 0], output_path, CLASS_MAP
            )
            self.assertEqual(matrix.shape, (8, 8))
            self.assertTrue(output_path.is_file())
            fig.clf()

    def test_name_to_id_class_map_is_supported(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "class_map.json"
            path.write_text(json.dumps({"class_b": 1, "class_a": 0}), encoding="utf-8")
            labels, names = load_class_map(path)
            self.assertEqual(labels, [0, 1])
            self.assertEqual(names, ["class_a", "class_b"])


if __name__ == "__main__":
    unittest.main()
