"""Unit tests cho TV3 Tuần 3: B2 Crop Classifier, Dataset on-the-fly, Loss Weighting và Image-level Aggregation.

Chạy:
    python -m unittest tests.test_tv3_w3_b2 -v

Không cần GPU, không tải ảnh từ Internet, sử dụng 100% dữ liệu tổng hợp.
"""

import io
import json
import shutil
import tempfile
import unittest
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
from scripts.train_b2 import check_w3_manifest_lock, run_training


class B2ModelTests(unittest.TestCase):
    """Kiểm tra kiến trúc mô hình B2CropClassifier và checkpointing."""

    def test_model_forward_shape_and_probabilities(self):
        model = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
        dummy_input = torch.randn(2, 3, 224, 224)
        logits = model(dummy_input)
        self.assertEqual(logits.shape, (2, 8))

        probs = model.predict_proba(dummy_input)
        self.assertEqual(probs.shape, (2, 8))
        # Tổng xác suất mỗi mẫu phải xấp xỉ 1.0
        row_sums = probs.sum(dim=-1).detach().numpy()
        np.testing.assert_allclose(row_sums, [1.0, 1.0], atol=1e-5)

    def test_checkpoint_save_and_load(self):
        tmp_dir = Path(tempfile.mkdtemp(dir=ROOT / "data"))
        try:
            model = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
            ckpt_path = tmp_dir / "test_model.pt"

            save_checkpoint(
                model=model,
                path=ckpt_path,
                epoch=5,
                val_metrics={"image_macro_f1": 0.85},
                config={"batch_size": 32},
            )
            self.assertTrue(ckpt_path.exists())

            # Nạp lại vào model mới
            model_new = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
            ckpt = load_checkpoint(model=model_new, path=ckpt_path)

            self.assertEqual(ckpt["epoch"], 5)
            self.assertEqual(ckpt["val_metrics"]["image_macro_f1"], 0.85)
            self.assertEqual(ckpt["config"]["batch_size"], 32)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


class B2DatasetTests(unittest.TestCase):
    """Kiểm tra B2ComparisonDataset: on-the-fly cropping, sample_weight và validation chặt chẽ."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(dir=ROOT / "data"))

        # Tạo ảnh nguồn giả lập (100 x 80)
        self.img_dir = self.tmp_dir / "images"
        self.img_dir.mkdir()
        self.img_path = self.img_dir / "src_img01.jpg"
        Image.new("RGB", (100, 80), color=(150, 200, 100)).save(self.img_path, format="JPEG")
        self.img_sha = sha256_file(self.img_path)

        # Tạo class_map
        self.class_map_path = self.tmp_dir / "class_map.json"
        self.class_map_path.write_text(json.dumps({"0": "sambar", "1": "serow"}), encoding="utf-8")

        # Đường dẫn tương đối từ ROOT
        rel_img_path = str(self.img_path.relative_to(ROOT)).replace("\\", "/")

        # Tạo B2 manifest: 2 crop cùng 1 ảnh (để kiểm tra sample_weight = 0.5)
        self.b2_manifest = self.tmp_dir / "train.jsonl"
        rows = [
            {
                "image_id": "img_001",
                "crop_id": "crop_001",
                "annotation_id": "ann_001",
                "label": "sambar",
                "class_id": 0,
                "split": "train",
                "bbox_xyxy": [10, 10, 40, 40],
                "quality": {"local_path": rel_img_path, "sha256": self.img_sha},
            },
            {
                "image_id": "img_001",
                "crop_id": "crop_002",
                "annotation_id": "ann_002",
                "label": "sambar",
                "class_id": 0,
                "split": "train",
                "bbox_xyxy": [20, 20, 60, 60],
                "quality": {"local_path": rel_img_path, "sha256": self.img_sha},
            },
        ]
        with open(self.b2_manifest, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_on_the_fly_crop_and_sample_weight(self):
        dataset = B2ComparisonDataset(
            split="train",
            manifest_path=self.b2_manifest,
            class_map_path=self.class_map_path,
            root=ROOT,
            preflight_hash_check=True,
        )
        self.assertEqual(len(dataset), 2)

        # Vì 2 crop cùng thuộc img_001, mỗi crop phải có sample_weight = 1/2 = 0.5
        item0 = dataset[0]
        self.assertEqual(item0["image"].shape, (3, 224, 224))
        self.assertEqual(item0["class_id"], 0)
        self.assertEqual(item0["label"], "sambar")
        self.assertAlmostEqual(float(item0["sample_weight"].item()), 0.5)

        item1 = dataset[1]
        self.assertAlmostEqual(float(item1["sample_weight"].item()), 0.5)

    def test_fail_fast_on_split_mismatch(self):
        with self.assertRaises(ValueError):
            # Dataset yêu cầu split="val" nhưng manifest ghi "train"
            B2ComparisonDataset(
                split="val",
                manifest_path=self.b2_manifest,
                class_map_path=self.class_map_path,
                root=ROOT,
            )

    def test_fail_fast_on_unknown_label(self):
        bad_manifest = self.tmp_dir / "bad.jsonl"
        bad_manifest.write_text(
            json.dumps({
                "image_id": "img_x", "crop_id": "c_x", "label": "unknown_beast",
                "class_id": 99, "split": "train", "bbox_xyxy": [0, 0, 10, 10],
            }) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(ValueError):
            B2ComparisonDataset(
                split="train",
                manifest_path=bad_manifest,
                class_map_path=self.class_map_path,
                root=ROOT,
            )


class ImageAggregationTests(unittest.TestCase):
    """Kiểm tra thuật toán tổng hợp dự đoán cấp ảnh (Image-level aggregation)."""

    def test_aggregation_mean_probability_and_argmax(self):
        # Ảnh 1 có 2 crop:
        # Crop 1: xác suất [0.8, 0.2] (nghiêng về lớp 0)
        # Crop 2: xác suất [0.4, 0.6] (nghiêng về lớp 1)
        # Trung bình: [0.6, 0.4] -> Argmax = 0 (Lớp 0)
        # Ground truth: 0 -> ĐÚNG

        # Ảnh 2 có 1 crop:
        # Crop 1: xác suất [0.1, 0.9] -> Argmax = 1 (Lớp 1)
        # Ground truth: 1 -> ĐÚNG
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
            "accuracy": 0.88,
            "macro_f1": 0.85,
            "macro_precision": 0.86,
            "macro_recall": 0.84,
            "total_unique_images": 600,
        }
        crop_metrics = {
            "accuracy": 0.85,
            "macro_f1": 0.82,
            "macro_precision": 0.83,
            "macro_recall": 0.81,
            "total_samples": 680,
        }
        md = format_validation_markdown_table(image_metrics=img_metrics, crop_metrics=crop_metrics)
        self.assertIn("## Bảng so sánh Validation", md)
        self.assertIn("88.00%", md)
        self.assertIn("85.00%", md)


class TrainingWorkflowTests(unittest.TestCase):
    """Kiểm tra ràng buộc tiêu chí nghiệm thu và chạy thử smoke test."""

    def test_check_w3_manifest_lock_fails_closed(self):
        dummy_cfg = {
            "data": {
                "manifest_train": "data/processed/non_existent_w3/train.jsonl",
                "manifest_val": "data/processed/non_existent_w3/val.jsonl",
                "class_map": "data/processed/non_existent_w3/class_map.json",
                "provenance": "data/processed/non_existent_w3/provenance.json",
            }
        }
        with self.assertRaises(FileNotFoundError):
            check_w3_manifest_lock(dummy_cfg, ROOT)

    def test_smoke_test_pipeline(self):
        """Chạy thử toàn bộ pipeline với --smoke-test (chỉ 2 epoch dummy)."""
        tmp_out = Path(tempfile.mkdtemp(dir=ROOT / "data"))
        try:
            config = {
                "experiment_name": "test_smoke",
                "model": {"backbone": "resnet18", "pretrained": False, "num_classes": 8},
                "training": {
                    "epochs": 2, "batch_size": 4, "learning_rate": 1e-3,
                    "seed": 42, "mixed_precision": False,
                },
                "output": {
                    "dir": str(tmp_out.relative_to(ROOT)),
                    "best_checkpoint": str((tmp_out / "best_model.pt").relative_to(ROOT)),
                    "last_checkpoint": str((tmp_out / "last_model.pt").relative_to(ROOT)),
                    "log_file": str((tmp_out / "train_log.jsonl").relative_to(ROOT)),
                    "val_report": str((tmp_out / "val_report.json").relative_to(ROOT)),
                    "val_table_md": str((tmp_out / "val_table.md").relative_to(ROOT)),
                },
            }
            report = run_training(config=config, smoke_test=True)

            self.assertIn("image_level_metrics", report)
            self.assertTrue((tmp_out / "best_model.pt").exists())
            self.assertTrue((tmp_out / "last_model.pt").exists())
            self.assertTrue((tmp_out / "train_log.jsonl").exists())
            self.assertTrue((tmp_out / "val_report.json").exists())
            self.assertTrue((tmp_out / "val_table.md").exists())
        finally:
            shutil.rmtree(tmp_out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
