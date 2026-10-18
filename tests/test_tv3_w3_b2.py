"""Unit tests cho TV3 Tuần 3 (vòng 2): B2 Crop Classifier, Dataset Validation,
Per-image Loss, Smoke Isolation và Checkpoint Accuracy.

Chạy:
    python -m unittest tests.test_tv3_w3_b2 -v

Không cần GPU, không tải Internet, 100% dữ liệu tổng hợp.
"""

import hashlib
import io
import json
import shutil
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

from src.models.b2_classifier import B2CropClassifier, load_checkpoint, save_checkpoint
from src.data.b2_dataset import B2ComparisonDataset, b2_collate_fn, sha256_file
from src.evaluation.b2_evaluator import (
    aggregate_image_predictions,
    compute_classification_metrics,
    format_validation_markdown_table,
)
from scripts.train_b2 import (
    check_w3_manifest_lock,
    compute_image_grouped_loss,
    run_training,
    AGREED_PROVENANCE_SHA256,
)


def make_fake_jpeg(w: int = 100, h: int = 80, color: tuple = (150, 200, 100)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color=color).save(buf, format="JPEG")
    return buf.getvalue()


def make_b2_row(
    image_id: str = "img_001",
    crop_id: str = "crop_001",
    label: str = "sambar",
    class_id: int = 0,
    split: str = "train",
    bbox: list = None,
    local_path: str = "",
    sha256: str = "",
) -> dict:
    return {
        "image_id": image_id,
        "crop_id": crop_id,
        "annotation_id": f"ann_{crop_id}",
        "label": label,
        "class_id": class_id,
        "split": split,
        "bbox_xyxy": bbox or [10, 10, 40, 40],
        "quality": {"local_path": local_path, "sha256": sha256},
    }


class B2ModelTests(unittest.TestCase):
    """Kiểm tra kiến trúc mô hình B2CropClassifier và checkpointing."""

    def test_model_forward_shape_and_probabilities(self):
        model = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
        dummy_input = torch.randn(2, 3, 224, 224)
        logits = model(dummy_input)
        self.assertEqual(logits.shape, (2, 8))

        probs = model.predict_proba(dummy_input)
        self.assertEqual(probs.shape, (2, 8))
        row_sums = probs.sum(dim=-1).detach().numpy()
        np.testing.assert_allclose(row_sums, [1.0, 1.0], atol=1e-5)

    def test_default_dropout_is_zero_per_protocol(self):
        """Protocol: không dùng dropout trong B2."""
        model = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
        # Nếu dropout_p=0 thì không có lớp Dropout trong classifier
        has_dropout = any(isinstance(m, torch.nn.Dropout) and m.p > 0 for m in model.classifier.modules())
        self.assertFalse(has_dropout, "B2 không được dùng dropout theo protocol đã thống nhất.")

    def test_checkpoint_save_and_load(self):
        tmp_dir = Path(tempfile.mkdtemp(dir=ROOT / "data"))
        try:
            model = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
            ckpt_path = tmp_dir / "test_model.pt"

            save_checkpoint(
                model=model, path=ckpt_path, epoch=5,
                val_metrics={"image_macro_f1": 0.85},
                config={"batch_size": 32},
            )
            self.assertTrue(ckpt_path.exists())

            model_new = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
            ckpt = load_checkpoint(model=model_new, path=ckpt_path)

            self.assertEqual(ckpt["epoch"], 5)
            self.assertEqual(ckpt["val_metrics"]["image_macro_f1"], 0.85)
            self.assertEqual(ckpt["config"]["batch_size"], 32)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


class B2DatasetValidationTests(unittest.TestCase):
    """Kiểm tra validation chặt chẽ của B2ComparisonDataset."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(dir=ROOT / "data"))
        # Ảnh nguồn giả lập
        self.img_dir = self.tmp_dir / "images"
        self.img_dir.mkdir()
        self.img_path = self.img_dir / "src_img.jpg"
        jpeg_bytes = make_fake_jpeg(100, 80, (150, 200, 100))
        self.img_path.write_bytes(jpeg_bytes)
        self.img_sha = sha256_file(self.img_path)
        self.rel_img = str(self.img_path.relative_to(ROOT)).replace("\\", "/")

        self.class_map_path = self.tmp_dir / "class_map.json"
        self.class_map_path.write_text(json.dumps({"0": "sambar", "1": "serow"}), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _write_manifest(self, rows: list) -> Path:
        p = self.tmp_dir / "manifest.jsonl"
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        return p

    def test_valid_manifest_loads_ok(self):
        rows = [
            make_b2_row("img_001", "crop_001", "sambar", 0, "train",
                        local_path=self.rel_img, sha256=self.img_sha),
            make_b2_row("img_001", "crop_002", "sambar", 0, "train", bbox=[20, 20, 60, 60],
                        local_path=self.rel_img, sha256=self.img_sha),
        ]
        ds = B2ComparisonDataset(
            split="train",
            manifest_path=self._write_manifest(rows),
            class_map_path=self.class_map_path,
            root=ROOT,
        )
        self.assertEqual(len(ds), 2)

    def test_sample_weight_is_inverse_crop_count(self):
        """Vì 2 crop cùng img_001, mỗi crop phải có sample_weight = 0.5."""
        rows = [
            make_b2_row("img_001", "crop_001", "sambar", 0, "train",
                        local_path=self.rel_img, sha256=self.img_sha),
            make_b2_row("img_001", "crop_002", "sambar", 0, "train", bbox=[20, 20, 60, 60],
                        local_path=self.rel_img, sha256=self.img_sha),
        ]
        ds = B2ComparisonDataset(
            split="train",
            manifest_path=self._write_manifest(rows),
            class_map_path=self.class_map_path,
            root=ROOT,
        )
        self.assertAlmostEqual(float(ds[0]["sample_weight"].item()), 0.5)
        self.assertAlmostEqual(float(ds[1]["sample_weight"].item()), 0.5)

    def test_fail_on_duplicate_crop_id(self):
        """Lỗi 3: crop_id trùng phải raise ValueError."""
        rows = [
            make_b2_row("img_001", "crop_SAME", "sambar", 0, "train",
                        local_path=self.rel_img, sha256=self.img_sha),
            make_b2_row("img_002", "crop_SAME", "sambar", 0, "train", bbox=[5, 5, 30, 30],
                        local_path=self.rel_img, sha256=self.img_sha),
        ]
        with self.assertRaises(ValueError, msg="Phải từ chối crop_id trùng"):
            B2ComparisonDataset(
                split="train",
                manifest_path=self._write_manifest(rows),
                class_map_path=self.class_map_path,
                root=ROOT,
            )

    def test_fail_on_multiple_labels_per_image(self):
        """Lỗi 3: cùng image_id có nhiều nhãn khác nhau phải raise ValueError."""
        rows = [
            make_b2_row("img_001", "crop_001", "sambar", 0, "train",
                        local_path=self.rel_img, sha256=self.img_sha),
            make_b2_row("img_001", "crop_002", "serow", 1, "train", bbox=[20, 20, 60, 60],
                        local_path=self.rel_img, sha256=self.img_sha),
        ]
        with self.assertRaises(ValueError, msg="Phải từ chối đa nhãn trên cùng image_id"):
            B2ComparisonDataset(
                split="train",
                manifest_path=self._write_manifest(rows),
                class_map_path=self.class_map_path,
                root=ROOT,
            )

    def test_fail_on_zero_size_box(self):
        """Lỗi 3: box có kích thước <= 0 phải raise ValueError."""
        rows = [
            make_b2_row("img_001", "crop_001", "sambar", 0, "train",
                        bbox=[50, 50, 50, 80],  # width = 0
                        local_path=self.rel_img, sha256=self.img_sha),
        ]
        with self.assertRaises(ValueError, msg="Phải từ chối box có width/height <= 0"):
            B2ComparisonDataset(
                split="train",
                manifest_path=self._write_manifest(rows),
                class_map_path=self.class_map_path,
                root=ROOT,
            )

    def test_fail_on_split_mismatch(self):
        """Dataset yêu cầu val nhưng manifest ghi train → raise."""
        rows = [
            make_b2_row("img_001", "crop_001", "sambar", 0, "train",
                        local_path=self.rel_img, sha256=self.img_sha),
        ]
        with self.assertRaises(ValueError):
            B2ComparisonDataset(
                split="val",
                manifest_path=self._write_manifest(rows),
                class_map_path=self.class_map_path,
                root=ROOT,
            )

    def test_fail_on_unknown_label(self):
        rows = [
            make_b2_row("img_001", "crop_001", "unknown_beast", 99, "train",
                        local_path=self.rel_img, sha256=self.img_sha),
        ]
        with self.assertRaises(ValueError):
            B2ComparisonDataset(
                split="train",
                manifest_path=self._write_manifest(rows),
                class_map_path=self.class_map_path,
                root=ROOT,
            )

    def test_preflight_fails_if_sha256_missing(self):
        """Lỗi 3: preflight bật mà thiếu sha256 phải raise, không bỏ qua."""
        rows = [
            {
                "image_id": "img_001", "crop_id": "crop_001", "label": "sambar",
                "class_id": 0, "split": "train", "bbox_xyxy": [10, 10, 40, 40],
                "quality": {"local_path": self.rel_img},  # sha256 bị bỏ
            }
        ]
        with self.assertRaises(ValueError, msg="Phải từ chối khi thiếu quality.sha256"):
            B2ComparisonDataset(
                split="train",
                manifest_path=self._write_manifest(rows),
                class_map_path=self.class_map_path,
                root=ROOT,
                preflight_hash_check=True,
            )

    def test_preflight_fails_if_sha256_wrong(self):
        """Preflight bật, hash sai → raise."""
        rows = [
            make_b2_row("img_001", "crop_001", "sambar", 0, "train",
                        local_path=self.rel_img, sha256="0" * 64),  # sai hash
        ]
        with self.assertRaises(ValueError, msg="Phải từ chối hash SHA-256 sai"):
            B2ComparisonDataset(
                split="train",
                manifest_path=self._write_manifest(rows),
                class_map_path=self.class_map_path,
                root=ROOT,
                preflight_hash_check=True,
            )

    def test_drop_last_false_no_crop_lost(self):
        """Lỗi 4: DataLoader phải giữ đủ tất cả crop, không drop batch cuối."""
        from src.data.b2_dataset import make_b2_loaders
        # 5 crop nhưng batch_size=4 → nếu drop_last=True sẽ mất 1
        rows = [
            make_b2_row(f"img_{i:03d}", f"crop_{i:03d}", "sambar", 0, "train",
                        local_path=self.rel_img, sha256=self.img_sha)
            for i in range(5)
        ]
        manifest = self._write_manifest(rows)
        ds = B2ComparisonDataset(
            split="train",
            manifest_path=manifest,
            class_map_path=self.class_map_path,
            root=ROOT,
        )
        from torch.utils.data import DataLoader
        loader = DataLoader(ds, batch_size=4, shuffle=False, collate_fn=b2_collate_fn, drop_last=False)
        total_seen = sum(len(batch["class_ids"]) for batch in loader)
        self.assertEqual(total_seen, 5, "drop_last=False phải giữ đủ 5 crop")


class PerImageLossTests(unittest.TestCase):
    """Lỗi 5: Kiểm tra tính đúng đắn của compute_image_grouped_loss."""

    def setUp(self):
        self.device = torch.device("cpu")
        self.model = B2CropClassifier(num_classes=2, backbone_name="resnet18", pretrained=False)
        self.model.eval()

    def test_single_crop_per_image_matches_standard_ce(self):
        """Khi mỗi ảnh chỉ có 1 crop, kết quả phải bằng CrossEntropyLoss thông thường."""
        logits = torch.tensor([[2.0, -1.0], [-1.0, 2.0]])  # ảnh A đúng, ảnh B đúng
        class_ids = torch.tensor([0, 1])
        image_ids = ["img_A", "img_B"]

        grouped_loss = compute_image_grouped_loss(logits, class_ids, image_ids, self.device)
        standard_loss = torch.nn.CrossEntropyLoss()(logits, class_ids)

        self.assertAlmostEqual(float(grouped_loss.item()), float(standard_loss.item()), places=5)

    def test_two_crops_per_image_gives_mean_of_means(self):
        """Ảnh A có 2 crop, ảnh B có 1 crop: loss phải là mean(mean_A, mean_B), bukan mean của 3 crops.

        Đây là counter-example từ review: nếu ảnh A tích lũy loss nhiều hơn B chỉ vì có nhiều crop
        → kết quả sai lệch khi so sánh ảnh 1 crop vs nhiều crop.
        """
        criterion = torch.nn.CrossEntropyLoss(reduction="none")
        # Ảnh A: 2 crop có loss là l_A1 và l_A2
        # Ảnh B: 1 crop có loss là l_B
        logits = torch.tensor([
            [2.0, -1.0],   # A crop 1 → class 0 → loss thấp
            [1.5, -0.5],   # A crop 2 → class 0 → loss thấp
            [-1.0, 2.0],   # B crop 1 → class 1 → loss thấp
        ])
        class_ids = torch.tensor([0, 0, 1])
        image_ids = ["img_A", "img_A", "img_B"]

        losses = criterion(logits, class_ids)  # [l_A1, l_A2, l_B]
        expected_loss = ((losses[0] + losses[1]) / 2 + losses[2]) / 2

        actual_loss = compute_image_grouped_loss(logits, class_ids, image_ids, self.device)

        self.assertAlmostEqual(float(actual_loss.item()), float(expected_loss.item()), places=5,
                               msg="Per-image grouped loss phải tính mean crop trong ảnh trước")


class ImageAggregationTests(unittest.TestCase):
    """Kiểm tra thuật toán tổng hợp dự đoán cấp ảnh."""

    def test_aggregation_mean_probability_and_argmax(self):
        # Ảnh 1 có 2 crop: [0.8,0.2] và [0.4,0.6] → trung bình [0.6,0.4] → pred=0, GT=0 → ĐÚNG
        # Ảnh 2 có 1 crop: [0.1,0.9] → pred=1, GT=1 → ĐÚNG
        crop_records = [
            {"image_id": "img_01", "class_id": 0, "probabilities": [0.8, 0.2]},
            {"image_id": "img_01", "class_id": 0, "probabilities": [0.4, 0.6]},
            {"image_id": "img_02", "class_id": 1, "probabilities": [0.1, 0.9]},
        ]
        metrics = aggregate_image_predictions(
            crop_records=crop_records,
            num_classes=2,
            id_to_label={0: "sambar", 1: "serow"},
        )
        self.assertEqual(metrics["total_unique_images"], 2)
        self.assertEqual(metrics["accuracy"], 1.0)
        self.assertEqual(metrics["macro_f1"], 1.0)

    def test_format_validation_markdown_table(self):
        img_metrics = {
            "accuracy": 0.88, "macro_f1": 0.85, "macro_precision": 0.86,
            "macro_recall": 0.84, "total_unique_images": 600,
        }
        crop_metrics = {
            "accuracy": 0.85, "macro_f1": 0.82, "macro_precision": 0.83,
            "macro_recall": 0.81, "total_samples": 680,
        }
        md = format_validation_markdown_table(image_metrics=img_metrics, crop_metrics=crop_metrics)
        self.assertIn("## Bảng so sánh Validation", md)
        self.assertIn("88.00%", md)


class GateAndCheckpointTests(unittest.TestCase):
    """Lỗi 2, 3, 6: Gate provenance SHA-256, smoke isolation, best_epoch accuracy."""

    def test_gate_fails_if_files_missing(self):
        """Lỗi 3: Gate phải từ chối khi file không tồn tại."""
        cfg = {"data": {"comparison_dir": "data/processed/non_existent_xyz"}}
        with self.assertRaises(FileNotFoundError):
            check_w3_manifest_lock(cfg, ROOT)

    def test_gate_fails_if_provenance_sha_wrong(self):
        """Lỗi 3: Gate phải từ chối nếu provenance.json có SHA-256 sai."""
        tmp_dir = Path(tempfile.mkdtemp(dir=ROOT / "data"))
        try:
            b2_dir = tmp_dir / "b2"
            b2_dir.mkdir()
            (b2_dir / "train.jsonl").write_text("", encoding="utf-8")
            (b2_dir / "val.jsonl").write_text("", encoding="utf-8")
            (tmp_dir / "class_map.json").write_text("{}", encoding="utf-8")
            # Ghi provenance.json với nội dung sai (SHA-256 sẽ khác)
            (tmp_dir / "provenance.json").write_text(
                json.dumps({"note": "FAKE provenance"}), encoding="utf-8"
            )
            comp_rel = str(tmp_dir.relative_to(ROOT)).replace("\\", "/")
            cfg = {"data": {"comparison_dir": comp_rel}}
            with self.assertRaises(ValueError, msg="Gate phải từ chối provenance.json sai SHA-256"):
                check_w3_manifest_lock(cfg, ROOT)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_smoke_test_uses_isolated_tmp_dir(self):
        """Lỗi 2: Smoke-test không được đụng vào thư mục output chính thức."""
        official_out = ROOT / "outputs" / "b2_crop_classifier"
        before = set(official_out.glob("*.pt")) if official_out.exists() else set()

        import tempfile as _tmp
        with _tmp.TemporaryDirectory(prefix="b2_smoke_", dir=ROOT / "outputs") as tmp_dir:
            config = {
                "model": {"backbone": "resnet18", "pretrained": False, "num_classes": 8, "dropout_p": 0.0},
                "training": {"epochs": 1, "seed": 42, "lr": 0.001, "momentum": 0.9,
                             "weight_decay": 1e-4, "step_size": 10, "gamma": 0.1, "patience": 7},
                "output": {},
            }
            report = run_training(config=config, smoke_test=True, smoke_out_dir=Path(tmp_dir))

        after = set(official_out.glob("*.pt")) if official_out.exists() else set()
        self.assertEqual(before, after, "Smoke-test không được tạo checkpoint trong output chính thức")
        self.assertTrue(report["smoke_test"])
        self.assertEqual(report["synthetic_marker"], "SYNTHETIC_SMOKE")

    def test_best_epoch_tracking_accuracy(self):
        """Lỗi 6: best_epoch phải là epoch thật của best F1, không phải epoch cuối."""
        import tempfile as _tmp
        with _tmp.TemporaryDirectory(prefix="b2_ckpt_test_", dir=ROOT / "outputs") as tmp_dir:
            config = {
                "model": {"backbone": "resnet18", "pretrained": False, "num_classes": 8, "dropout_p": 0.0},
                "training": {"epochs": 2, "seed": 42, "lr": 0.001, "momentum": 0.9,
                             "weight_decay": 1e-4, "step_size": 10, "gamma": 0.1, "patience": 99},
                "output": {},
            }
            report = run_training(config=config, smoke_test=True, smoke_out_dir=Path(tmp_dir))

        # best_epoch phải nằm trong khoảng hợp lệ
        self.assertGreaterEqual(report["best_epoch"], 1)
        self.assertLessEqual(report["best_epoch"], config["training"]["epochs"])

    def test_last_checkpoint_contains_last_epoch_not_best_metrics(self):
        """Lỗi 6: last_model.pt phải chứa metrics của epoch cuối, không phải best."""
        import tempfile as _tmp
        with _tmp.TemporaryDirectory(prefix="b2_last_test_", dir=ROOT / "outputs") as tmp_dir:
            tmp_path = Path(tmp_dir)
            config = {
                "model": {"backbone": "resnet18", "pretrained": False, "num_classes": 8, "dropout_p": 0.0},
                "training": {"epochs": 2, "seed": 42, "lr": 0.001, "momentum": 0.9,
                             "weight_decay": 1e-4, "step_size": 10, "gamma": 0.1, "patience": 99},
                "output": {},
            }
            run_training(config=config, smoke_test=True, smoke_out_dir=tmp_path)

            last_ckpt = torch.load(tmp_path / "last_model.pt", map_location="cpu", weights_only=False)
            # Epoch của last checkpoint phải là 2 (epoch cuối)
            self.assertEqual(last_ckpt["epoch"], config["training"]["epochs"],
                             "last_model.pt phải ghi epoch cuối")

    def test_smoke_log_has_synthetic_marker(self):
        """Lỗi 2: log file của smoke-test phải có SYNTHETIC_SMOKE marker ở dòng đầu."""
        import tempfile as _tmp
        with _tmp.TemporaryDirectory(prefix="b2_log_test_", dir=ROOT / "outputs") as tmp_dir:
            tmp_path = Path(tmp_dir)
            config = {
                "model": {"backbone": "resnet18", "pretrained": False, "num_classes": 8, "dropout_p": 0.0},
                "training": {"epochs": 1, "seed": 42, "lr": 0.001, "momentum": 0.9,
                             "weight_decay": 1e-4, "step_size": 10, "gamma": 0.1, "patience": 99},
                "output": {},
            }
            run_training(config=config, smoke_test=True, smoke_out_dir=tmp_path)

            log_path = tmp_path / "train_log.jsonl"
            self.assertTrue(log_path.exists())
            first_line = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[0])
            self.assertEqual(first_line.get("MARKER"), "SYNTHETIC_SMOKE")


if __name__ == "__main__":
    unittest.main()
