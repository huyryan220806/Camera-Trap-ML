"""B1 scientific gates and training integration; all image inputs are synthetic."""

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import torch

from src.data.b0_dataset import make_transform
from src.models.b0 import parameter_counts
from src.models.b1 import build_b1
from src.training import b1
from src.training.b1_gate import (GateError, committed_receipt, official_gate, protocol_settings,
                                  relative_path, validate_config, verify_data)
from src.training.run_artifacts import file_sha256, reserve_run


class B1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test_B1_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = json.loads((b1.ROOT / "configs/b1.yaml").read_text())
        self.config["model"]["num_classes"] = 2
        self.config["data"].update(image_root="images", batch_size=2, image_size=32, resize_size=40)
        self.config["training"].update(epochs=2, early_stopping_patience=2)
        self.receipt = b1.create_fixture(self.root, self.config)
        self.config_path = self.root / "config.json"
        self.config_path.write_text(json.dumps(self.config))

    def read(self, name):
        path = self.root / self.receipt["files"][name]["path"]
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    def write(self, name, rows, *, update_source=False):
        path = self.root / self.receipt["files"][name]["path"]
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))
        self.receipt["files"][name]["sha256"] = file_sha256(path)
        if update_source:
            self.write(f"source_{name}", rows)

    def verify(self):
        return verify_data(self.receipt, self.root, self.root / "images", 2)

    def test_valid_fixture_counts_and_no_test(self):
        rows, names, _, proof = self.verify()
        self.assertEqual(len(rows["train"]), 4)
        self.assertEqual(names, ["fixture_a", "fixture_b"])
        self.assertFalse(proof["test_rows_opened"])

    def test_official_proposed_config_fails_before_run_or_model(self):
        with patch.object(b1, "build_b1") as build:
            with self.assertRaisesRegex(GateError, "MANIFEST NOT FROZEN"):
                b1.train(self.config_path, root=self.root)
            build.assert_not_called()
        self.assertFalse((self.root / "experiments").exists())

    def test_frozen_data_does_not_imply_protocol_agreement(self):
        self.config["data"].update(freeze_receipt="receipt.json", freeze_sha256="a"*64, freeze_git_ref="b"*40+":receipt.json")
        receipt = {"status": "FROZEN", "owner": "TV1", "task": "W3-01", "dataset_version": "fixture"}
        with patch("src.training.b1_gate.committed_receipt", return_value=receipt):
            with self.assertRaisesRegex(GateError, "PROTOCOL NOT AGREED"):
                official_gate(self.config, self.root)

    def test_agreement_must_pin_actual_settings(self):
        self.config["data"].update(freeze_receipt="receipt.json", freeze_sha256="a"*64, freeze_git_ref="b"*40+":receipt.json")
        self.config["protocol"].update(status="AGREED", receipt="p.json", sha256="c"*64, git_ref="d"*40+":p.json")
        self.config["runtime"]["budget_reference"] = "fixture-budget"
        receipt = {"status": "FROZEN", "owner": "TV1", "task": "W3-01", "dataset_version": "fixture"}
        agreement = {"status": "AGREED", "approved_by": ["TV2", "TV3"], "freeze_sha256": "a"*64, "settings": protocol_settings(self.config), "budget_reference": "fixture-budget"}
        with patch("src.training.b1_gate.committed_receipt", side_effect=[receipt, agreement]):
            self.assertEqual(official_gate(self.config, self.root)[0], receipt)
        agreement = copy.deepcopy(agreement)
        agreement["settings"]["training"]["epochs"] += 1
        with patch("src.training.b1_gate.committed_receipt", side_effect=[receipt, agreement]):
            with self.assertRaisesRegex(GateError, "differs"):
                official_gate(self.config, self.root)

    def test_receipt_checks_real_git_bytes(self):
        subprocess.run(["git", "init", "-q", str(self.root / "repo")], check=True)
        repo = self.root / "repo"
        receipt = repo / "receipt.json"
        receipt.write_text('{"status":"fixture"}')
        subprocess.run(["git", "add", "receipt.json"], cwd=repo, check=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"], cwd=repo, check=True)
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        self.assertEqual(committed_receipt(repo, "receipt.json", file_sha256(receipt), commit+":receipt.json")["status"], "fixture")
        receipt.write_text('{"status":"modified"}')
        with self.assertRaisesRegex(GateError, "committed handoff"):
            committed_receipt(repo, "receipt.json", file_sha256(receipt), commit+":receipt.json")

    def test_invalid_configs(self):
        for section, field, value in [("experiment", "id", "../B0_run01"), ("experiment", "seed", True), ("model", "fine_tune", "fc"), ("data", "test_used_for_selection", True), ("data", "input_type", "crop"), ("data", "batch_size", 0), ("training", "lr", float("nan")), ("training", "epochs", 0), ("training", "optimizer", "adam"), ("runtime", "device", "cpu")]:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.config)
                changed[section][field] = value
                with self.assertRaises(GateError):
                    validate_config(changed)

    def test_manifest_hash_drift(self):
        (self.root / "train.jsonl").write_text("[]\n")
        with self.assertRaisesRegex(GateError, "SHA-256"):
            self.verify()

    def test_source_membership_mismatch(self):
        rows = self.read("val")
        rows[0]["location"] = "changed"
        self.write("val", rows)
        with self.assertRaisesRegex(GateError, "provenance"):
            self.verify()

    def test_location_sequence_and_content_leakage(self):
        original = self.read("val")
        train = self.read("train")
        for key in ("location", "seq_id", "sha256", "pixel_sha256"):
            with self.subTest(key=key):
                changed = copy.deepcopy(original)
                if key in ("sha256", "pixel_sha256"):
                    changed[0]["quality"][key] = train[0]["quality"][key]
                else:
                    changed[0][key] = train[0][key]
                self.write("val", changed, update_source=True)
                with self.assertRaisesRegex(GateError, "leakage"):
                    self.verify()

    def test_duplicate_ids_and_paths(self):
        original = self.read("train")
        for key in ("image_id", "file_name"):
            with self.subTest(key=key):
                changed = copy.deepcopy(original)
                changed[1][key] = changed[0][key]
                self.write("train", changed, update_source=True)
                with self.assertRaises(ValueError):
                    self.verify()

    def test_identical_content_with_conflicting_labels_rejected(self):
        rows = self.read("train")
        rows[2]["quality"]["sha256"] = rows[0]["quality"]["sha256"]
        self.write("train", rows, update_source=True)
        with self.assertRaisesRegex(GateError, "Duplicate"):
            self.verify()

    def test_empty_invalid_label_and_missing_class(self):
        original = self.read("train")
        invalid = copy.deepcopy(original)
        invalid[0]["class_id"] = 99
        for rows in ([], invalid, original[:2]):
            with self.subTest(count=len(rows)):
                self.write("train", rows, update_source=True)
                with self.assertRaises(ValueError):
                    self.verify()

    def test_missing_corrupt_and_changed_images_fail_without_filtering(self):
        path = self.root / self.read("val")[0]["quality"]["local_path"]
        before = (self.root / "val.jsonl").read_bytes()
        path.unlink()
        with self.assertRaisesRegex(GateError, "Image invalid"):
            self.verify()
        path.write_bytes(b"corrupt")
        rows = self.read("val")
        rows[0]["quality"]["sha256"] = file_sha256(path)
        self.write("val", rows, update_source=True)
        with self.assertRaisesRegex(GateError, "Image invalid"):
            self.verify()
        Image.new("RGB", (64, 64), "red").save(path)
        with self.assertRaisesRegex(GateError, "SHA-256"):
            self.verify()
        self.assertEqual(len(before.splitlines()), len(self.read("val")))

    def test_pixel_hash_is_recomputed(self):
        rows = self.read("val")
        rows[0]["quality"]["pixel_sha256"] = "f"*64
        self.write("val", rows, update_source=True)
        with self.assertRaisesRegex(GateError, "pixel SHA-256"):
            self.verify()

    def test_test_row_rejected(self):
        rows = self.read("val")
        rows[0]["split"] = "test"
        self.write("val", rows)
        with self.assertRaisesRegex(ValueError, "split"):
            self.verify()

    def test_class_map_hash_and_mapping(self):
        path = self.root / "class_map.json"
        path.write_text('{"0":"fixture_b","1":"fixture_a"}')
        with self.assertRaisesRegex(GateError, "SHA-256"):
            self.verify()
        self.receipt["files"]["class_map"]["sha256"] = file_sha256(path)
        with self.assertRaisesRegex(ValueError, "label"):
            self.verify()

    def test_crop_missing_or_multiple_or_wrong_box(self):
        original = self.read("crop_train")
        wrong = copy.deepcopy(original)
        wrong[0]["bbox_xywh_original"] = [1, 2, 3, 4]
        for rows in (original[:-1], original + [original[0]], wrong):
            with self.subTest(count=len(rows)):
                self.write("crop_train", rows)
                with self.assertRaises(GateError):
                    self.verify()

    def test_box_label_and_geometry(self):
        original = self.read("train")
        for key, value in (("label", "wrong"), ("bbox_xywh", [0, 0, 1000, 64])):
            rows = copy.deepcopy(original)
            rows[0]["boxes"][0][key] = value
            self.write("train", rows, update_source=True)
            with self.assertRaisesRegex(GateError, "[Bb]ox"):
                self.verify()

    def test_exclusion_accounting(self):
        self.write("excluded", [{"image_id": "unknown", "split": "train", "reason": "fixture"}])
        with self.assertRaisesRegex(GateError, "accounting"):
            self.verify()

    def test_path_escape_rejected(self):
        with self.assertRaises(GateError):
            relative_path(self.root, "../outside")

    def test_transform_and_loader_reproducibility(self):
        rows, _, _, _ = self.verify()
        transform = make_transform(self.config, False)
        image = Image.open(self.root / rows["val"][0]["quality"]["local_path"])
        with image:
            self.assertTrue(torch.equal(transform(image), transform(image)))
        def batch():
            b1.set_seed(42)
            loader, _ = b1.make_loaders(self.config, rows, self.root)
            return next(iter(loader))
        first, second = batch(), batch()
        self.assertTrue(torch.equal(first[0], second[0]))
        self.assertTrue(torch.equal(first[1], second[1]))
        self.assertEqual(tuple(first[0].shape), (2, 3, 32, 32))

    def test_resnet_backbone_gradients_batchnorm_and_step(self):
        torch.set_num_threads(2)
        model = build_b1(2, pretrained=False)
        self.assertEqual(parameter_counts(model)["frozen"], 0)
        optimizer = torch.optim.SGD([p for p in model.parameters() if p.requires_grad], lr=0.01)
        before = model.conv1.weight.detach().clone()
        bn_before = model.bn1.running_mean.clone()
        model.train()
        logits = model(torch.randn(2, 3, 32, 32))
        self.assertEqual(tuple(logits.shape), (2, 2))
        loss = torch.nn.functional.cross_entropy(logits, torch.tensor([0, 1]))
        self.assertTrue(torch.isfinite(loss))
        loss.backward()
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()))
        optimizer.step()
        self.assertFalse(torch.equal(before, model.conv1.weight))
        self.assertFalse(torch.equal(bn_before, model.bn1.running_mean))
        model.eval()
        frozen = model.bn1.running_mean.clone()
        with torch.no_grad():
            model(torch.randn(2, 3, 32, 32))
        self.assertTrue(torch.equal(frozen, model.bn1.running_mean))

    def test_end_to_end_real_resnet_checkpoint_and_tamper_rejection(self):
        run = self.root / "run"
        reserve_run(run)
        result = b1._execute(self.config, self.receipt, self.root, run, torch.device("cpu"), synthetic=True)
        self.assertEqual(result["reload"], "PASS")
        self.assertTrue(result["gradient_checked"])
        self.assertEqual(set(result["metric_absolute_differences"].values()), {0.0})
        with self.assertRaises(FileExistsError):
            reserve_run(run)
        checkpoint = run / "checkpoints/best_model.pth"
        with self.assertRaisesRegex(GateError, "kind"):
            b1.validate_checkpoint(checkpoint, file_sha256(checkpoint), root=self.root)
        with self.assertRaisesRegex(GateError, "SHA-256"):
            b1.validate_checkpoint(checkpoint, "0"*64, root=self.root)
        (self.root / "val.jsonl").write_text("\n")
        with self.assertRaisesRegex(GateError, "SHA-256"):
            b1.validate_checkpoint(checkpoint, file_sha256(checkpoint), root=self.root, expected_kind="SYNTHETIC_SMOKE")

    def test_smoke_preserves_project_and_existing_run(self):
        sentinel = self.root / "experiments/B0_run01/checkpoints/best_model.pth"
        sentinel.parent.mkdir(parents=True)
        sentinel.write_bytes(b"historical W2")
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with patch.object(b1, "_execute", return_value={"reload": "PASS"}) as execute:
            result = b1.smoke(self.config_path)
            self.assertFalse(execute.call_args.args[3].is_relative_to(self.root))
            self.assertFalse(execute.call_args.args[3].exists())
        self.assertFalse(result["official_training"])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_failure_keeps_reserved_run_and_records_status(self):
        run = self.root / "run"
        reserve_run(run)
        with patch.object(b1, "_fit", side_effect=RuntimeError("fixture failure")):
            with self.assertRaises(RuntimeError):
                b1._execute(self.config, self.receipt, self.root, run, torch.device("cpu"), synthetic=True)
        self.assertEqual(json.loads((run / "status.json").read_text())["status"], "FAILED")
        with self.assertRaises(FileExistsError):
            reserve_run(run)


if __name__ == "__main__":
    unittest.main()
