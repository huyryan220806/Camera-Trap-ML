"""TV2 W4 synthetic tests: no SWG pixels, official weights or Test inference."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from src.evaluation import w4_test as w4


def probability(a, pa, b=7):
    p = [0.] * 8
    p[a], p[b] = pa, 1 - pa
    return p


class AggregationTests(unittest.TestCase):
    def setUp(self):
        self.expected = [{"crop_id": "a", "image_id": "one", "class_id": 0},
                         {"crop_id": "b", "image_id": "one", "class_id": 0},
                         {"crop_id": "c", "image_id": "two", "class_id": 1}]
        self.predictions = [{**r, "probabilities": p} for r, p in zip(self.expected,
                            [probability(0, .9, 1), probability(0, .3, 1), probability(1, 1.)])]

    def test_all_crops_mean_probability_and_one_prediction_per_image(self):
        result = w4.aggregate_predictions(self.predictions, self.expected)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0]["confidence"], .6)
        self.assertEqual(result[0]["num_crops"], 2)
        self.assertEqual(result[0]["predicted_class_id"], 0)

    def test_order_independent_associations(self):
        self.assertEqual(w4.aggregate_predictions(self.predictions[::-1], self.expected),
                         w4.aggregate_predictions(self.predictions, self.expected))

    def test_exact_tie_chooses_lowest_id(self):
        result = w4.aggregate_predictions([{**self.expected[0], "probabilities": probability(0, .5, 1)}], self.expected[:1])
        self.assertEqual(result[0]["predicted_class_id"], 0)

    def test_missing_crop_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.aggregate_predictions(self.predictions[:-1], self.expected)

    def test_duplicate_crop_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.aggregate_predictions(self.predictions + self.predictions[:1], self.expected)

    def test_extra_crop_rejected(self):
        self.predictions[0]["crop_id"] = "unknown"
        with self.assertRaises(w4.EvaluationBlocked):
            w4.aggregate_predictions(self.predictions, self.expected)

    def test_wrong_parent_rejected(self):
        self.predictions[0]["image_id"] = "two"
        with self.assertRaises(w4.EvaluationBlocked):
            w4.aggregate_predictions(self.predictions, self.expected)

    def test_changed_ground_truth_rejected(self):
        self.predictions[0]["class_id"] = 2
        with self.assertRaises(w4.EvaluationBlocked):
            w4.aggregate_predictions(self.predictions, self.expected)

    def test_nonfinite_negative_and_non_normalized_vectors_rejected(self):
        for p in ([float("nan")] * 8, [-.1, 1.1] + [0.] * 6, [.1] * 8, [1.] * 7):
            with self.subTest(p=p), self.assertRaises(w4.EvaluationBlocked):
                w4.aggregate_predictions([{**self.expected[0], "probabilities": p}], self.expected[:1])

    def test_empty_expected_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.aggregate_predictions([], [])


class PopulationTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {str(i): f"class_{i}" for i in range(8)}
        self.splits = {s: [{"image_id": s, "file_name": s + ".jpg", "location": s, "seq_id": s,
                           "split": s, "class_id": 0, "label": "class_0", "width": 20, "height": 20,
                           "quality": {"sha256": hashlib.sha256(s.encode()).hexdigest(), "local_path": s + ".jpg"}}]
                       for s in ("train", "val", "test")}
        self.crops = [{**self.splits["test"][0], "crop_id": "test_crop", "bbox_xyxy": [0, 0, 10, 10],
                       "parent_crop_count": 1, "sample_weight": 1.}]

    def test_complete_population_passes(self):
        parents, groups = w4.validate_population(self.splits, self.crops, self.mapping)
        self.assertEqual(set(parents), {"test"})
        self.assertEqual(len(groups["test"]), 1)

    def test_each_cross_split_leakage_dimension_rejected(self):
        for field in ("image_id", "file_name", "location", "seq_id"):
            splits = copy.deepcopy(self.splits)
            splits["val"][0][field] = splits["train"][0][field]
            with self.subTest(field=field), self.assertRaisesRegex(w4.EvaluationBlocked, "Leakage"):
                w4.validate_population(splits, self.crops, self.mapping)

    def test_source_file_sha_leakage_rejected(self):
        self.splits["val"][0]["quality"]["sha256"] = self.splits["train"][0]["quality"]["sha256"]
        with self.assertRaisesRegex(w4.EvaluationBlocked, "file_sha256"):
            w4.validate_population(self.splits, self.crops, self.mapping)

    def test_duplicate_parent_rejected(self):
        self.splits["test"] *= 2
        with self.assertRaises(w4.EvaluationBlocked):
            w4.validate_population(self.splits, self.crops, self.mapping)

    def test_missing_parent_crop_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.validate_population(self.splits, [], self.mapping)

    def test_duplicate_crop_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.validate_population(self.splits, self.crops * 2, self.mapping)

    def test_wrong_class_order_rejected(self):
        self.mapping["0"] = "different"
        with self.assertRaises(w4.EvaluationBlocked):
            w4.validate_population(self.splits, self.crops, self.mapping)

    def test_wrong_crop_label_rejected(self):
        self.crops[0]["class_id"] = 2
        with self.assertRaises(w4.EvaluationBlocked):
            w4.validate_population(self.splits, self.crops, self.mapping)

    def test_box_outside_source_rejected(self):
        self.crops[0]["bbox_xyxy"] = [0, 0, 21, 10]
        with self.assertRaises(w4.EvaluationBlocked):
            w4.validate_population(self.splits, self.crops, self.mapping)

    def test_crop_count_and_weight_must_match(self):
        for field, value in (("parent_crop_count", 2), ("sample_weight", .5)):
            crops = copy.deepcopy(self.crops)
            crops[0][field] = value
            with self.subTest(field=field), self.assertRaises(w4.EvaluationBlocked):
                w4.validate_population(self.splits, crops, self.mapping)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.selection = self.root / "selection.json"
        self.protocol = self.root / "protocol.json"
        self.selection.write_text(json.dumps({"status": "FINAL MODEL LOCK PENDING", "final_selection_closed": False,
                                               "blockers": ["missing B2", "missing B3 provenance"]}))
        self.protocol.write_text(json.dumps({"status": "PENDING"}))

    def test_pending_lock_blocks_before_any_git_checkpoint_or_test_access(self):
        with patch.object(w4, "committed_bytes", side_effect=AssertionError("too early")), \
             patch.object(w4, "digest", side_effect=AssertionError("too early")), \
             patch.object(w4, "read_rows", side_effect=AssertionError("Test opened")):
            with self.assertRaisesRegex(w4.EvaluationBlocked, "FINAL MODEL LOCK PENDING"):
                w4.evaluate(self.root, self.selection, self.protocol, self.root / "missing.pt")
        self.assertFalse((self.root / "outputs").exists())

    def test_closed_boolean_alone_does_not_unlock(self):
        self.selection.write_text(json.dumps({"status": "LOCKED", "final_selection_closed": True, "blockers": ["missing B2"]}))
        with self.assertRaisesRegex(w4.EvaluationBlocked, "FINAL MODEL LOCK PENDING"):
            w4.verify_gate(self.root, self.selection, self.protocol, self.root / "missing.pt")

    def test_pending_protocol_blocks_even_when_selection_marked_closed(self):
        self.selection.write_text(json.dumps({"status": "LOCKED", "final_selection_closed": True, "blockers": []}))
        with self.assertRaisesRegex(w4.EvaluationBlocked, "protocol"):
            w4.verify_gate(self.root, self.selection, self.protocol, self.root / "missing.pt")

    def test_uncommitted_lock_rejected(self):
        with patch.object(subprocess, "check_output", side_effect=subprocess.CalledProcessError(128, "git")):
            with self.assertRaisesRegex(w4.EvaluationBlocked, "must be committed"):
                w4.committed_bytes(self.root, self.selection)

    def test_dirty_lock_rejected(self):
        with patch.object(subprocess, "check_output", return_value=b"old committed content"):
            with self.assertRaisesRegex(w4.EvaluationBlocked, "Uncommitted change"):
                w4.committed_bytes(self.root, self.selection)

    def test_identical_committed_lock_passes(self):
        with patch.object(subprocess, "check_output", return_value=self.selection.read_bytes()):
            self.assertEqual(w4.committed_bytes(self.root, self.selection), self.selection.read_bytes())

    def test_checkpoint_real_bytes_hash_and_size(self):
        checkpoint = self.root / "fixture.pt"
        checkpoint.write_bytes(b"synthetic checkpoint bytes")
        sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        w4.verify_checkpoint(checkpoint, sha, checkpoint.stat().st_size)
        with self.assertRaises(w4.EvaluationBlocked):
            w4.verify_checkpoint(checkpoint, "0" * 64, checkpoint.stat().st_size)
        with self.assertRaises(w4.EvaluationBlocked):
            w4.verify_checkpoint(checkpoint, sha, 1)

    def test_missing_checkpoint_rejected(self):
        with self.assertRaisesRegex(w4.EvaluationBlocked, "not available"):
            w4.verify_checkpoint(self.root / "missing.pt", "0" * 64, 1)

    def test_one_official_run_and_no_unsafe_resume(self):
        run = w4.reserve_run(self.root, "W4_test_eval01")
        (run / "state.json").write_text('{"status":"INTERRUPTED"}')
        with self.assertRaisesRegex(w4.EvaluationBlocked, "already reserved"):
            w4.reserve_run(self.root, "W4_test_eval01")
        self.assertIn("INTERRUPTED", (run / "state.json").read_text())

    def test_alternate_official_run_id_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.reserve_run(self.root, "W4_test_eval02")

    def test_path_escape_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.repository_file(self.root, "../secret.txt")


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.mapping = Path(self.temp.name) / "class_map.json"
        self.mapping.write_text(json.dumps({str(i): f"class_{i}" for i in reversed(range(8))}))
        self.parents = {str(i): {"class_id": i} for i in range(8)}
        self.predictions = [{"image_id": str(i), "true_class_id": i, "predicted_class_id": i} for i in range(8)]

    def test_perfect_eight_class_metrics_and_matrix(self):
        metrics, cm, rows = w4.metrics_and_integrity(self.predictions, self.parents, self.mapping)
        self.assertTrue(all(v == 1 for v in metrics.values()))
        self.assertEqual(sum(map(sum, cm)), 8)
        self.assertEqual([r["class_id"] for r in rows], list(range(8)))
        self.assertEqual(sum(r["support"] for r in rows), 8)

    def test_independent_hand_computed_error_and_zero_division(self):
        self.predictions[0]["predicted_class_id"] = 1
        metrics, cm, rows = w4.metrics_and_integrity(self.predictions, self.parents, self.mapping)
        self.assertEqual(cm[0][1], 1)
        self.assertEqual(metrics["accuracy"], 7 / 8)
        self.assertAlmostEqual(metrics["macro_f1"], (6 + 2 / 3) / 8)
        self.assertEqual(rows[0]["precision"], 0.)
        self.assertEqual(rows[1]["precision"], .5)

    def test_missing_classes_still_eight_by_eight_and_macro_over_eight(self):
        metrics, cm, _ = w4.metrics_and_integrity(self.predictions[:1], {"0": self.parents["0"]}, self.mapping)
        self.assertEqual(metrics["macro_f1"], 1 / 8)
        self.assertEqual((len(cm), len(cm[0])), (8, 8))

    def test_duplicate_parent_prediction_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.metrics_and_integrity(self.predictions + self.predictions[:1], self.parents, self.mapping)

    def test_missing_parent_prediction_rejected(self):
        with self.assertRaises(w4.EvaluationBlocked):
            w4.metrics_and_integrity(self.predictions[:-1], self.parents, self.mapping)

    def test_relabelled_ground_truth_rejected(self):
        self.predictions[0]["true_class_id"] = 1
        with self.assertRaises(w4.EvaluationBlocked):
            w4.metrics_and_integrity(self.predictions, self.parents, self.mapping)


class FrozenContractTests(unittest.TestCase):
    """Exercise the successful gate and mutate independent frozen dependencies."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.comp = self.root / "data/processed/comparison_v1"
        (self.comp / "b2").mkdir(parents=True)
        mapping = {str(i): f"species_{i}" for i in range(8)}
        (self.comp / "class_map.json").write_text(json.dumps(mapping))
        for name in ("test.jsonl", "b2/test.jsonl"):
            (self.comp / name).write_text("[]\n")
        provenance = {"dataset_version": "comparison_v1", "files_sha256": {
            name: w4.digest(self.comp / name) for name in ("test.jsonl", "b2/test.jsonl", "class_map.json")}}
        (self.comp / "provenance.json").write_text(json.dumps(provenance))
        config = self.root / "configs/b2_crop_classifier.json"
        config.parent.mkdir()
        config.write_text("{}")
        evidence = self.root / "decision.md"
        evidence.write_text("Synthetic decision evidence")
        for name in w4.CODE_FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic code hash fixture")
        self.selection = self.root / "selection.json"
        self.protocol = self.root / "protocol.json"
        self.s = {"status": "LOCKED", "final_selection_closed": True, "blockers": [], "model": "B2",
                  "run_id": "b2_run01", "evaluation_models": ["B2"], "checkpoint_sha256": w4.B2_SHA256,
                  "checkpoint_bytes": 89548866, "selection_split": "val", "test_used_for_selection": False,
                  "review_status": "PASS WITH LIMITATIONS", "locked_utc": "2026-10-22T00:00:00+00:00",
                  "evidence_verified": dict.fromkeys(("b2_checkpoint_metadata", "b2_independent_reload",
                     "b3_original_validation_artifact", "b3_checkpoint_hash", "b3_train_val_provenance", "decision_before_test"), True),
                  "preprocessing": w4.PREPROCESSING, "class_map": mapping, "provenance_sha256": w4.digest(self.comp / "provenance.json"),
                  "config_sha256": w4.digest(config), "decision_evidence_sha256": {"decision.md": w4.digest(evidence)}}
        self.p = {"status": "LOCKED", "evaluation_models": ["B2"], "checkpoint_sha256": w4.B2_SHA256,
                  "evaluation_unit": "source_image", "aggregation": w4.AGGREGATION, "metrics": w4.METRICS,
                  "preprocessing": w4.PREPROCESSING, "run_id": "W4_test_eval01", "class_map": mapping,
                  "execution": {"device": "cpu", "crop_batch_size": 32, "num_threads": 4, "seed": 42},
                  "threshold_policy": {"status": "NOT_SELECTED", "value": None, "classification": "argmax_all_images", "calibrated": False},
                  "code_sha256": {name: w4.digest(self.root / name) for name in w4.CODE_FILES},
                  "provenance_sha256": self.s["provenance_sha256"], "test_manifest_sha256": w4.digest(self.comp / "test.jsonl"),
                  "b2_test_manifest_sha256": w4.digest(self.comp / "b2/test.jsonl")}

    def gate(self):
        self.selection.write_text(json.dumps(self.s))
        self.p["model_selection_lock_sha256"] = w4.digest(self.selection)
        self.protocol.write_text(json.dumps(self.p))
        # Git byte checks and actual checkpoint bytes have separate tests above.
        with patch.object(w4, "committed_bytes", side_effect=lambda root, p: p.read_bytes()), \
             patch.object(w4, "verify_checkpoint") as checkpoint_check:
            result = w4.verify_gate(self.root, self.selection, self.protocol, self.root / "synthetic.pt")
            checkpoint_check.assert_called_once_with(self.root / "synthetic.pt", w4.B2_SHA256, 89548866)
            return result

    def test_complete_contract_passes(self):
        self.assertEqual(self.gate()[0]["model"], "B2")

    def test_missing_original_b3_evidence_rejected(self):
        self.s["evidence_verified"]["b3_original_validation_artifact"] = False
        with self.assertRaisesRegex(w4.EvaluationBlocked, "evidence missing"):
            self.gate()

    def test_changed_evaluator_bytes_rejected(self):
        (self.root / w4.CODE_FILES[0]).write_text("changed")
        with self.assertRaisesRegex(w4.EvaluationBlocked, "code changed"):
            self.gate()

    def test_changed_manifest_bytes_rejected(self):
        (self.comp / "b2/test.jsonl").write_text("changed")
        with self.assertRaisesRegex(w4.EvaluationBlocked, "dataset changed"):
            self.gate()

    def test_changed_decision_evidence_rejected(self):
        (self.root / "decision.md").write_text("changed")
        with self.assertRaisesRegex(w4.EvaluationBlocked, "Decision evidence changed"):
            self.gate()

    def test_b1_or_b3_cannot_be_added_to_test_plan(self):
        for extra in ("B1", "B3"):
            self.p["evaluation_models"] = ["B2", extra]
            with self.subTest(extra=extra), self.assertRaisesRegex(w4.EvaluationBlocked, "preregistered"):
                self.gate()

    def test_threshold_cannot_be_swept_on_test(self):
        self.p["threshold_policy"] = {"value": .5}
        with self.assertRaisesRegex(w4.EvaluationBlocked, "threshold"):
            self.gate()

    def test_wrong_class_mapping_rejected(self):
        self.p["class_map"] = {"0": "wrong"}
        with self.assertRaisesRegex(w4.EvaluationBlocked, "Class mapping"):
            self.gate()

    def test_crop_level_metric_policy_rejected(self):
        self.p["evaluation_unit"] = "crop"
        with self.assertRaisesRegex(w4.EvaluationBlocked, "aggregation"):
            self.gate()

    def test_changed_execution_policy_rejected(self):
        self.p["execution"] = {"device": "cuda"}
        with self.assertRaisesRegex(w4.EvaluationBlocked, "Execution"):
            self.gate()


class SyntheticExportTests(unittest.TestCase):
    """Test the entire export path on synthetic pixels in a disposable directory."""
    def setUp(self):
        PopulationTests.setUp(self)

    def test_export_and_interrupted_run_guard_without_swg_or_training(self):
        import torch
        from PIL import Image
        from torch import nn
        class Tiny(nn.Module):
            def forward(self, batch):
                if self.training or torch.is_grad_enabled():
                    raise AssertionError("Inference must use eval and disable gradients")
                return torch.tensor([[8.] + [0.] * 7]).repeat(len(batch), 1)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            comp = root / "data/processed/comparison_v1"
            (comp / "b2").mkdir(parents=True)
            path = root / "test.jpg"
            Image.new("RGB", (20, 20), (10, 20, 30)).save(path)
            self.splits["test"][0]["quality"]["sha256"] = w4.digest(path)
            self.crops[0]["quality"]["sha256"] = w4.digest(path)
            for split, rows in self.splits.items():
                (comp / f"{split}.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
            (comp / "b2/test.jsonl").write_text(json.dumps(self.crops[0]))
            (comp / "class_map.json").write_text(json.dumps(self.mapping))
            checkpoint = root / "fixture.pt"
            torch.save({"epoch": 21}, checkpoint)
            selection, protocol = root / "selection.json", root / "protocol.json"
            selection.write_text("{}")
            protocol.write_text("{}")
            frozen_s = {"best_epoch": 21, "provenance_sha256": "synthetic"}
            frozen_p = {"run_id": "W4_test_eval01", "class_map": self.mapping,
                        "expected_population": {"images": 1, "crops": 1, "sequences": 1, "locations": 1,
                                                "per_class_support": {"0": 1}}}
            with patch.object(w4, "verify_gate", return_value=(frozen_s, frozen_p)), \
                 patch.object(w4, "B2_SHA256", w4.digest(checkpoint)), \
                 patch("src.demo.classifier.checkpoint_model", return_value=(Tiny().eval(), lambda im: torch.zeros(3, 8, 8))):
                run = w4.evaluate(root, selection, protocol, checkpoint)
                expected = {"test_metrics.json", "per_class_metrics.csv", "confusion_matrix.csv", "confusion_matrix.png",
                            "evaluation_config.json", "evaluation_manifest.json", "checkpoint_verification.json",
                            "evaluation_log.txt", "test_predictions.csv", "error_analysis.md", "environment.json"}
                self.assertTrue(expected <= {p.name for p in run.iterdir()})
                self.assertEqual(w4.load_json(run / "test_metrics.json")["support"], 1)
                self.assertEqual(w4.load_json(run / "state.json")["status"], "COMPLETE")
                manifest = w4.load_json(run / "evaluation_manifest.json")
                self.assertTrue(all(w4.digest(run / p) == h for p, h in manifest["files_sha256"].items()))
                with self.assertRaisesRegex(w4.EvaluationBlocked, "already reserved"):
                    w4.evaluate(root, selection, protocol, checkpoint)


if __name__ == "__main__":
    unittest.main()
