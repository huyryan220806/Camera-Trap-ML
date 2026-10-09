"""Regression tests for W2 run immutability and fail-before-inference provenance."""

import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import torch
from torch import nn

from scripts import prepare_b0_pilot, validate_b0
from src.training import b0, run_artifacts
from src.training.provenance import verify_validation_provenance


class TinyClassifier(nn.Module):
    """Exercise real forward/backward/save/load without downloading weights."""
    def __init__(self):
        super().__init__()
        self.backbone = nn.Parameter(torch.ones(3), requires_grad=False)
        self.fc = nn.Linear(3, 2)

    def forward(self, images):
        return self.fc(images.mean(dim=(2, 3)) * self.backbone)


def snapshot(folder):
    return {str(p.relative_to(folder)): (p.read_bytes(), hashlib.sha256(p.read_bytes()).hexdigest())
            for p in folder.rglob("*") if p.is_file()}


class B0IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / "experiments/fixture"
        self.run.mkdir(parents=True)
        self.images = self.root / "images"
        self.images.mkdir()
        self.names = ["a", "b"]
        self.class_map = self.root / "class_map.json"
        self.class_map.write_text(json.dumps({"0": "a", "1": "b"}))
        self.rows = {}
        for split in ("train", "val"):
            self.rows[split] = []
            for label in range(2):
                for index in range(2):
                    image_id = f"{split}-{label}-{index}"
                    row = {"image_id": image_id, "file_name": image_id + ".png", "class_id": label,
                           "label": self.names[label], "split": split}
                    Image.new("RGB", (32, 32), (40 + label * 60, 20, 90)).save(self.images / row["file_name"])
                    self.rows[split].append(row)
            self.write_rows(self.run / f"selected_{split}.jsonl", self.rows[split])
            self.write_rows(self.run / f"used_{split}.jsonl", self.rows[split])
        self.source = self.root / "pilot.jsonl"
        self.write_rows(self.source, self.rows["train"] + self.rows["val"])
        self.config = {
            "experiment": {"id": "fixture", "seed": 42},
            "model": {"num_classes": 2, "freeze_backbone": True},
            "data": {"image_root": "images", "class_map": "class_map.json", "source_manifest": "pilot.jsonl",
                     "train_manifest": "experiments/fixture/selected_train.jsonl",
                     "validation_manifest": "experiments/fixture/selected_val.jsonl",
                     "test_used_for_selection": False, "batch_size": 2, "num_workers": 0,
                     "image_size": 24, "resize_size": 32},
            "training": {"checkpoint_metric": "macro_f1", "lr": 0.001, "weight_decay": 0.0001},
            "preprocessing": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
            "dataset": {},
        }
        self.freeze_hashes()
        self.config_path = self.root / "config.json"
        self.config_path.write_text(json.dumps(self.config))
        (self.run / "config.yaml").write_text(json.dumps(self.config))
        (self.run / "image_errors.json").write_text("[]")
        (self.run / "logs").mkdir()
        (self.run / "logs/train_log.csv").write_text("epoch,loss\n4,1.0\n")
        self.checkpoint = {
            "config": self.config, "model_name": "resnet18", "freeze_backbone": True, "num_classes": 2,
            "class_to_idx": {"a": 0, "b": 1}, "idx_to_class": {0: "a", 1: "b"},
            "epoch": 4, "model_state_dict": TinyClassifier().state_dict(),
            "validation_metrics": dict.fromkeys(("macro_f1", "macro_precision", "macro_recall", "accuracy"), 0.5),
        }

    @staticmethod
    def write_rows(path, rows):
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def freeze_hashes(self):
        self.config["dataset"].update({
            "source_manifest_sha256": run_artifacts.file_sha256(self.source),
            "validation_manifest_sha256": run_artifacts.file_sha256(self.run / "used_val.jsonl"),
            "class_map_sha256": run_artifacts.file_sha256(self.class_map),
        })

    def smoke(self):
        with patch.object(b0, "ROOT", self.root), patch.object(b0, "build_b0", side_effect=lambda *a, **kw: TinyClassifier()), patch.object(b0.torch.cuda, "is_available", return_value=False):
            b0.train(self.config_path, smoke=True)

    def assert_rejected_before_inference(self, message):
        with patch.object(validate_b0.torch, "load", return_value=self.checkpoint), patch.object(validate_b0, "build_b0") as model, patch.object(validate_b0, "DataLoader") as loader, patch.object(validate_b0, "evaluate") as evaluate:
            with self.assertRaisesRegex(ValueError, message):
                validate_b0.validate_checkpoint(self.root / "checkpoint.pth", root=self.root)
            model.assert_not_called()
            loader.assert_not_called()
            evaluate.assert_not_called()

    def test_a_smoke_preserves_completed_run_bytes_and_hashes(self):
        before = snapshot(self.run)
        self.smoke()
        self.assertEqual(before, snapshot(self.run))

    def test_b_smoke_with_missing_validation_image_preserves_run(self):
        (self.images / self.rows["val"][0]["file_name"]).unlink()
        before = snapshot(self.run)
        self.smoke()
        self.assertEqual(before, snapshot(self.run))
        self.assertEqual(len((self.run / "used_val.jsonl").read_text().splitlines()), 4)

    def test_c_existing_run_rejected_before_preparation(self):
        before = snapshot(self.run)
        with patch.object(b0, "ROOT", self.root), patch.object(b0, "prepare_data") as prepare:
            with self.assertRaisesRegex(FileExistsError, "Run ID already exists.*Use a new run ID"):
                b0.train(self.config_path)
            prepare.assert_not_called()
        self.assertEqual(before, snapshot(self.run))

    def test_d_prepare_failure_after_train_inspection_publishes_nothing(self):
        output = self.root / "new"
        output.mkdir()
        with patch.object(b0, "ROOT", self.root), patch.object(b0, "inspect_images", side_effect=[(self.rows["train"], []), OSError("injected validation failure")]):
            with self.assertRaisesRegex(OSError, "injected"):
                b0.prepare_data(self.config, output, self.names)
        self.assertEqual(snapshot(output), {})

    def test_d_atomic_publication_rolls_back_all_files(self):
        before = snapshot(self.run)
        replace = os.replace
        calls = 0

        def fail_second(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected replace failure")
            return replace(source, destination)

        payloads = {self.run / "used_train.jsonl": b"new train", self.run / "used_val.jsonl": b"new val"}
        with patch.object(run_artifacts.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "injected"):
                run_artifacts.atomic_write_files(payloads)
        self.assertEqual(before, snapshot(self.run))

    def test_smoke_exception_preserves_run(self):
        before = snapshot(self.run)
        with patch.object(b0, "inspect_images", side_effect=OSError("injected")):
            with self.assertRaisesRegex(OSError, "injected"):
                self.smoke()
        self.assertEqual(before, snapshot(self.run))

    def test_reservation_rejects_each_existing_run_marker(self):
        for name in ("config.yaml", "logs", "results", "checkpoints", "used_train.jsonl", "used_val.jsonl", ".training_started"):
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=self.root) as folder:
                run = Path(folder)
                (run / name).write_text("old")
                before = snapshot(run)
                with self.assertRaises(FileExistsError):
                    run_artifacts.reserve_run(run)
                self.assertEqual(before, snapshot(run))

    def test_selected_inputs_allow_first_reservation_but_not_second(self):
        run = self.root / "new"
        run.mkdir()
        (run / "selected_train.jsonl").write_text("input")
        run_artifacts.reserve_run(run)
        with self.assertRaises(FileExistsError):
            run_artifacts.reserve_run(run)

    def test_new_fixture_run_can_train_save_and_verify_once(self):
        config = copy.deepcopy(self.config)
        config["experiment"]["id"] = "new_fixture"
        config["training"].update(epochs=1, early_stopping_patience=1)
        self.config_path.write_text(json.dumps(config))
        before = snapshot(self.run)
        with patch.object(b0, "ROOT", self.root), patch.object(b0, "build_b0", side_effect=lambda *a, **kw: TinyClassifier()), patch.object(b0.torch.cuda, "is_available", return_value=False):
            b0.train(self.config_path)
            with self.assertRaises(FileExistsError):
                b0.train(self.config_path)
        result = json.loads((self.root / "experiments/new_fixture/results/reload_validation.json").read_text())
        self.assertTrue(result["reload_successful"])
        self.assertEqual(result["provenance"]["status"], "PASS")
        self.assertEqual(before, snapshot(self.run))

    def test_prepare_cli_rejects_completed_run(self):
        before = snapshot(self.run)
        with patch.object(prepare_b0_pilot, "ROOT", self.root), patch("sys.argv", ["prepare", "--config", str(self.config_path), "--select-only"]):
            with self.assertRaisesRegex(FileExistsError, "Use a new run ID"):
                prepare_b0_pilot.main()
        self.assertEqual(before, snapshot(self.run))

    def test_e_changed_image_id_rejected(self):
        rows = copy.deepcopy(self.rows["val"])
        rows[0]["image_id"] = "foreign"
        self.write_rows(self.run / "used_val.jsonl", rows)
        self.assert_rejected_before_inference("Validation manifest hash mismatch")

    def test_f_changed_class_map_rejected(self):
        self.class_map.write_text('{"0": "b", "1": "a"}')
        self.assert_rejected_before_inference("Class map hash mismatch")

    def test_g_added_deleted_modified_validation_rows_rejected(self):
        for rows in (self.rows["val"][:-1], self.rows["val"] + [self.rows["val"][0]], list(reversed(self.rows["val"]))):
            with self.subTest(rows=len(rows)):
                self.write_rows(self.run / "used_val.jsonl", rows)
                self.assert_rejected_before_inference("Validation manifest hash mismatch")

    def test_h_changed_source_rejected(self):
        self.source.write_text(self.source.read_text() + "\n")
        self.assert_rejected_before_inference("Source manifest hash mismatch")

    def use_quality_metadata(self):
        for rows in self.rows.values():
            for row in rows:
                row["quality"] = {"local_path": "images/" + row["file_name"],
                                  "sha256": run_artifacts.file_sha256(self.images / row["file_name"])}
                row["file_name"] = "unavailable-original/" + row["file_name"]
        self.write_rows(self.source, self.rows["train"] + self.rows["val"])
        self.write_rows(self.run / "used_val.jsonl", self.rows["val"])
        self.freeze_hashes()

    def test_i_changed_decodable_image_bytes_rejected(self):
        self.use_quality_metadata()
        Image.new("RGB", (32, 32), "red").save(self.root / self.rows["val"][0]["quality"]["local_path"])
        self.assert_rejected_before_inference("Image SHA-256 mismatch")

    def test_v2_local_path_and_sha_verified(self):
        self.use_quality_metadata()
        _, _, _, proof = verify_validation_provenance(self.checkpoint, self.root)
        self.assertEqual(proof["image_sha256_verified"], 4)
        self.assertEqual(proof["images_without_frozen_sha256"], 0)

    def test_v1_without_image_hash_reports_limitation(self):
        _, _, _, proof = verify_validation_provenance(self.checkpoint, self.root)
        self.assertEqual(proof["images_without_frozen_sha256"], 4)

    def test_source_membership_checked_even_with_matching_manifest_hash(self):
        rows = copy.deepcopy(self.rows["val"])
        rows[0]["image_id"] = "foreign"
        self.write_rows(self.run / "used_val.jsonl", rows)
        self.freeze_hashes()
        self.assert_rejected_before_inference("row provenance mismatch")

    def test_source_row_path_mismatch_rejected(self):
        rows = copy.deepcopy(self.rows["val"])
        rows[0]["file_name"] = rows[1]["file_name"]
        self.write_rows(self.run / "used_val.jsonl", rows)
        self.freeze_hashes()
        self.assert_rejected_before_inference("row provenance mismatch")

    def test_inverse_checkpoint_mapping_checked(self):
        self.checkpoint["idx_to_class"] = {0: "b", 1: "a"}
        self.assert_rejected_before_inference("class map mismatch")

    def test_missing_class_hash_requires_exact_mapping(self):
        del self.config["dataset"]["class_map_sha256"]
        verify_validation_provenance(self.checkpoint, self.root)
        self.class_map.write_text('{"0": "b", "1": "a"}')
        self.assert_rejected_before_inference("class map mismatch")

    def test_missing_frozen_validation_hash_rejected(self):
        del self.config["dataset"]["validation_manifest_sha256"]
        self.assert_rejected_before_inference("Missing frozen validation manifest hash")

    def test_successful_validator_runs_inference_after_provenance(self):
        with patch.object(validate_b0.torch, "load", return_value=self.checkpoint), patch.object(validate_b0, "build_b0", return_value=TinyClassifier()), patch.object(validate_b0, "evaluate", return_value=(self.checkpoint["validation_metrics"], [0, 0, 1, 1], [0, 1, 0, 1], 0.7)) as evaluate:
            result = validate_b0.validate_checkpoint(self.root / "checkpoint.pth", root=self.root)
        evaluate.assert_called_once()
        self.assertEqual(result["reload"], "PASS")
        self.assertEqual(result["provenance"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
