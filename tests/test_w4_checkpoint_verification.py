"""Independent metadata/weight checks for TV2's Validation-only checkpoint audit."""
import copy
import unittest

from scripts.verify_w4_checkpoints import PROVENANCE, canonical_hash, crop_class_weights, verify_metadata, validation_reference_checks
from src.evaluation.w4_test import PREPROCESSING


class DeliveredCheckpointMetadataTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {str(i): f"species_{i}" for i in range(8)}
        self.config = {"experiment_name": "synthetic_config", "model": {"backbone": "resnet18", "num_classes": 8}}
        self.checkpoint = {
            "is_official": True, "backbone_name": "resnet18", "num_classes": 8, "epoch": 14,
            "provenance_sha256": PROVENANCE, "class_map": {v: int(k) for k, v in self.mapping.items()},
            "id_to_label": {int(k): v for k, v in self.mapping.items()}, "config": copy.deepcopy(self.config),
            "preprocessing": {"resize": 256, "crop_size": 224, "mean": PREPROCESSING["mean"],
                "std": PREPROCESSING["std"], "val_transforms": "Resize(256) -> CenterCrop(224) -> ToTensor() -> Normalize()"}}

    def test_official_b3_metadata_passes_without_rewriting_checkpoint(self):
        before = copy.deepcopy(self.checkpoint)
        verify_metadata(self.checkpoint, self.config, self.mapping, "B3")
        self.assertEqual(self.checkpoint, before)

    def test_b2_best_epoch_contract_passes(self):
        self.checkpoint["epoch"] = 21
        verify_metadata(self.checkpoint, self.config, self.mapping, "B2")

    def test_synthetic_checkpoint_rejected(self):
        self.checkpoint["is_official"] = False
        with self.assertRaisesRegex(ValueError, "official"):
            verify_metadata(self.checkpoint, self.config, self.mapping, "B3")

    def test_mismatched_architecture_or_class_count_rejected(self):
        for key, value in (("backbone_name", "resnet50"), ("num_classes", 7)):
            ck = copy.deepcopy(self.checkpoint)
            ck[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "architecture"):
                verify_metadata(ck, self.config, self.mapping, "B3")

    def test_mismatched_provenance_rejected(self):
        self.checkpoint["provenance_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "provenance"):
            verify_metadata(self.checkpoint, self.config, self.mapping, "B3")

    def test_mismatched_best_epoch_rejected(self):
        self.checkpoint["epoch"] = 21
        with self.assertRaisesRegex(ValueError, "epoch"):
            verify_metadata(self.checkpoint, self.config, self.mapping, "B3")

    def test_mismatched_class_to_id_rejected(self):
        self.checkpoint["class_map"]["species_0"] = 1
        with self.assertRaisesRegex(ValueError, "Class map"):
            verify_metadata(self.checkpoint, self.config, self.mapping, "B3")

    def test_mismatched_id_to_label_rejected(self):
        self.checkpoint["id_to_label"][0] = "wrong"
        with self.assertRaisesRegex(ValueError, "ID mapping"):
            verify_metadata(self.checkpoint, self.config, self.mapping, "B3")

    def test_mismatched_config_rejected(self):
        self.checkpoint["config"]["model"]["backbone"] = "resnet50"
        with self.assertRaisesRegex(ValueError, "config"):
            verify_metadata(self.checkpoint, self.config, self.mapping, "B3")

    def test_mismatched_validation_transform_rejected(self):
        self.checkpoint["preprocessing"]["val_transforms"] = "RandomCrop(224)"
        with self.assertRaisesRegex(ValueError, "preprocessing"):
            verify_metadata(self.checkpoint, self.config, self.mapping, "B3")

    def test_mismatched_normalization_rejected(self):
        self.checkpoint["preprocessing"]["mean"] = [0.] * 3
        with self.assertRaisesRegex(ValueError, "preprocessing"):
            verify_metadata(self.checkpoint, self.config, self.mapping, "B3")


class CropWeightDefinitionTests(unittest.TestCase):
    def test_balanced_crop_counts_have_unit_weights(self):
        weights = crop_class_weights([{"class_id": c} for c in range(8) for _ in range(2)])
        self.assertEqual(weights, [1.] * 8)

    def test_more_crops_per_parent_changes_crop_weights_even_with_balanced_parents(self):
        # One parent per class; class 0 has two crops while all other parents have one.
        samples = [{"class_id": c, "image_id": str(c)} for c in range(8)] + [{"class_id": 0, "image_id": "0"}]
        weights = crop_class_weights(samples)
        self.assertAlmostEqual(weights[1] / weights[0], 2.)
        self.assertAlmostEqual(sum(weights) / 8, 1.)
        self.assertEqual(len({s["image_id"] for s in samples}), 8)

    def test_missing_train_class_rejected(self):
        with self.assertRaises(ValueError):
            crop_class_weights([{"class_id": c} for c in range(7)])

    def test_canonical_hash_ignores_object_key_order(self):
        self.assertEqual(canonical_hash({"a": 1, "b": 2}), canonical_hash({"b": 2, "a": 1}))


class ValidationReferenceCheckTests(unittest.TestCase):
    def setUp(self):
        self.cm = [[1 if a == b else 0 for b in range(8)] for a in range(8)]
        self.metrics = {"macro_f1": 1., "macro_precision": 1., "macro_recall": 1., "accuracy": 1.}
        self.stored = {**self.metrics, "confusion_matrix": copy.deepcopy(self.cm)}
        self.published = {"confusion_matrix": {"matrix": copy.deepcopy(self.cm)}, "misclassified_images": []}

    def test_exact_reference_agreement_passes(self):
        self.assertTrue(all(validation_reference_checks(self.metrics, self.cm, self.stored, self.published, {}).values()))

    def test_same_rounded_metrics_do_not_hide_changed_confusion_matrix(self):
        cm = copy.deepcopy(self.cm)
        cm[0][0], cm[0][1] = 0, 1
        checks = validation_reference_checks(self.metrics, cm, self.stored, self.published, {})
        self.assertTrue(checks["checkpoint_rounded_metrics_match"])
        self.assertFalse(checks["checkpoint_cm_matches"])
        self.assertFalse(all(checks.values()))

    def test_same_counts_do_not_hide_changed_error_image_ids(self):
        published = copy.deepcopy(self.published)
        published["misclassified_images"] = [{"image_id": "one", "true_class_id": 0, "predicted_class_id": 1}]
        checks = validation_reference_checks(self.metrics, self.cm, self.stored, published, {"two": (0, 1)})
        self.assertFalse(checks["published_error_ids_and_labels_match"])
        self.assertFalse(all(checks.values()))


if __name__ == "__main__":
    unittest.main()
