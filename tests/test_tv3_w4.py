"""TV3 - Tuần 4: Kiểm thử tự động (Unit Tests) cho B3 Class-Weighted và Error Analysis.

Chạy:
    python -m unittest tests.test_tv3_w4 -v
    hoặc:
    python tests/test_tv3_w4.py

Không phụ thuộc external test runner (chỉ dùng Python standard library unittest).
Không yêu cầu GPU, chạy an toàn trên mọi máy.
"""

import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.train_b3 import (
    compute_class_weights,
    compute_image_grouped_loss_weighted,
    run_training_b3,
)
from scripts.error_analysis import (
    _build_confusion_matrix,
    _top_confused_pairs,
    _per_class_error_breakdown,
    _summary_statistics,
    _generate_markdown_report,
    run_error_analysis,
    sha256_file,
)
from src.models.b2_classifier import B2CropClassifier, load_checkpoint, save_checkpoint
from src.data.b2_dataset import B2ComparisonDataset


class TestTV3Week4(unittest.TestCase):
    """Bộ kiểm thử đơn vị cho toàn bộ chức năng Tuần 4."""

    def test_b3_config_validity(self):
        """Kiểm tra cấu hình configs/b3_class_weighted.json hợp lệ và đúng chuẩn W4."""
        config_path = ROOT / "configs" / "b3_class_weighted.json"
        self.assertTrue(config_path.exists(), f"Thiếu file cấu hình {config_path}")

        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(config["experiment_name"], "b3_class_weighted_comparison_v1")
        self.assertEqual(config["model"]["backbone"], "resnet18")
        self.assertEqual(config["model"]["num_classes"], 8)
        self.assertEqual(config["training"]["optimizer"], "sgd")
        self.assertEqual(config["training"]["lr"], 0.001)
        self.assertEqual(config["training"]["momentum"], 0.9)
        self.assertEqual(config["training"]["weight_decay"], 0.0001)
        self.assertEqual(config["training"]["epochs"], 50)
        self.assertEqual(config["training"]["patience"], 7)
        self.assertEqual(config["training"]["class_weight_method"], "inverse_frequency")
        self.assertIn("class_weighted", config["training"]["loss"])

    def test_class_weights_balanced_and_imbalanced(self):
        """Kiểm tra tính toán trọng số lớp trong các trường hợp cân bằng và mất cân bằng."""
        # 1. Trường hợp cân bằng: mỗi lớp 100 mẫu
        balanced_samples = []
        for c in range(8):
            for i in range(100):
                balanced_samples.append({
                    "image_id": f"img_{c}_{i}",
                    "class_id": c,
                })

        weights_bal = compute_class_weights(balanced_samples, num_classes=8)
        self.assertEqual(weights_bal.shape, (8,))
        self.assertTrue(torch.allclose(weights_bal, torch.ones(8), atol=1e-5))

        # 2. Trường hợp mất cân bằng: lớp 0 chỉ có 10 mẫu, các lớp khác 100 mẫu
        imbalanced_samples = []
        for c in range(8):
            n_samples = 10 if c == 0 else 100
            for i in range(n_samples):
                imbalanced_samples.append({
                    "image_id": f"img_{c}_{i}",
                    "class_id": c,
                })

        weights_imbal = compute_class_weights(imbalanced_samples, num_classes=8)
        self.assertEqual(weights_imbal.shape, (8,))
        self.assertGreater(weights_imbal[0].item(), weights_imbal[1].item())
        self.assertGreater(weights_imbal[0].item(), 2.0)
        self.assertTrue(torch.isclose(weights_imbal.mean(), torch.tensor(1.0), atol=1e-5))

    def test_class_weighted_loss_gradient(self):
        """Kiểm tra loss có trọng số lớp làm thay đổi loss tương ứng."""
        torch.manual_seed(42)
        logits = torch.randn(4, 8, requires_grad=True)
        class_ids = torch.tensor([0, 1, 0, 1], dtype=torch.long)
        image_ids = ["img_1", "img_2", "img_3", "img_4"]

        unweighted_loss = compute_image_grouped_loss_weighted(
            logits=logits,
            class_ids=class_ids,
            image_ids=image_ids,
            class_weights=torch.ones(8),
        )

        weights = torch.tensor([3.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        weighted_loss = compute_image_grouped_loss_weighted(
            logits=logits,
            class_ids=class_ids,
            image_ids=image_ids,
            class_weights=weights,
        )

        self.assertGreater(weighted_loss.item(), unweighted_loss.item())

    def test_b3_smoke_test_execution(self):
        """Chạy thử nghiệm smoke test B3 và kiểm định toàn bộ pipeline sinh checkpoint."""
        with tempfile.TemporaryDirectory(prefix="test_b3_smoke_") as tmp_dir:
            tmp_path = Path(tmp_dir)

            config = {
                "experiment_name": "test_b3_smoke",
                "model": {"backbone": "resnet18", "num_classes": 8, "dropout_p": 0.0},
                "training": {
                    "epochs": 2,
                    "patience": 2,
                    "batch_size": 4,
                    "seed": 42,
                    "lr": 0.001,
                    "momentum": 0.9,
                    "weight_decay": 0.0001,
                    "step_size": 1,
                    "gamma": 0.1,
                    "class_weight_method": "inverse_frequency",
                },
                "output": {
                    "best_checkpoint_name": "best_model.pt",
                    "last_checkpoint_name": "last_model.pt",
                    "log_file_name": "train_log.jsonl",
                    "val_report_name": "val_report.json",
                    "val_table_md_name": "val_table.md",
                },
            }

            report = run_training_b3(
                config=config,
                smoke_test=True,
                smoke_out_dir=tmp_path,
            )

            self.assertTrue(report["smoke_test"])
            self.assertEqual(report["synthetic_marker"], "SYNTHETIC_SMOKE")
            self.assertEqual(report["total_epochs_run"], 2)

            best_ckpt = tmp_path / "best_model.pt"
            last_ckpt = tmp_path / "last_model.pt"
            log_file = tmp_path / "train_log.jsonl"
            val_report = tmp_path / "val_report.json"
            val_table = tmp_path / "val_table.md"

            self.assertTrue(best_ckpt.exists(), "best_model.pt không được tạo")
            self.assertTrue(last_ckpt.exists(), "last_model.pt không được tạo")
            self.assertTrue(log_file.exists(), "train_log.jsonl không được tạo")
            self.assertTrue(val_report.exists(), "val_report.json không được tạo")
            self.assertTrue(val_table.exists(), "val_table.md không được tạo")

            log_lines = log_file.read_text(encoding="utf-8").strip().split("\n")
            header = json.loads(log_lines[0])
            self.assertEqual(header["MARKER"], "SYNTHETIC_SMOKE")
            self.assertIn("class_weights", header)

            test_model = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
            loaded = load_checkpoint(test_model, best_ckpt, map_location="cpu", weights_only=True)
            self.assertEqual(loaded["num_classes"], 8)
            self.assertFalse(loaded["is_official"])
            self.assertIn("class_map", loaded)
            self.assertIn("preprocessing", loaded)

    def test_error_analysis_components(self):
        """Kiểm tra các hàm phân tích lỗi độc lập với dữ liệu mẫu."""
        id_to_label = {
            0: "large_antlered_muntjac",
            1: "annamite_striped_rabbit",
            2: "sambar",
            3: "chinese_serow",
            4: "common_palm_civet",
            5: "masked_palm_civet",
            6: "silver_pheasant",
            7: "eurasian_wild_pig",
        }

        y_true = [0, 0, 0, 0, 2, 2, 6, 6, 7, 7]
        y_pred = [2, 2, 2, 0, 2, 2, 6, 6, 7, 0]

        cm = _build_confusion_matrix(y_true, y_pred, num_classes=8)
        self.assertEqual(cm[0][2], 3)
        self.assertEqual(cm[0][0], 1)
        self.assertEqual(cm[7][0], 1)

        top_pairs = _top_confused_pairs(cm, id_to_label, top_n=5)
        self.assertEqual(len(top_pairs), 2)
        self.assertEqual(top_pairs[0]["true_label"], "large_antlered_muntjac")
        self.assertEqual(top_pairs[0]["predicted_label"], "sambar")
        self.assertEqual(top_pairs[0]["count"], 3)

        breakdown = _per_class_error_breakdown(y_true, y_pred, num_classes=8, id_to_label=id_to_label)
        muntjac_stats = breakdown["large_antlered_muntjac"]
        self.assertEqual(muntjac_stats["total"], 4)
        self.assertEqual(muntjac_stats["errors"], 3)
        self.assertEqual(muntjac_stats["error_rate"], 0.75)
        self.assertEqual(muntjac_stats["most_common_mistake"], "sambar")

        summary = _summary_statistics(y_true, y_pred, breakdown, top_pairs)
        self.assertEqual(summary["total_images"], 10)
        self.assertEqual(summary["total_misclassified"], 4)
        self.assertEqual(summary["overall_accuracy"], 0.6)

        md_report = _generate_markdown_report(
            model_name="test_b2",
            checkpoint_path="outputs/test/best_model.pt",
            summary=summary,
            top_confused=top_pairs,
            per_class_breakdown=breakdown,
            misclassified=[{
                "image_id": "img_001",
                "true_label": "large_antlered_muntjac",
                "predicted_label": "sambar",
                "confidence": 0.65,
            }],
            confusion_matrix=cm,
            id_to_label=id_to_label,
            num_classes=8,
            metadata={"checkpoint_sha256": "abc123sha"},
        )
        self.assertIn("# Báo cáo Phân tích Lỗi", md_report)
        self.assertIn("large_antlered_muntjac", md_report)
        self.assertIn("sambar", md_report)
        self.assertIn("abc123sha", md_report)

    def test_b3_checkpoint_compatibility_tv4(self):
        """Kiểm tra format checkpoint B3 tương thích hoàn toàn với adapter TV4."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_ckpt = Path(tmp_dir) / "test_ckpt.pt"
            model = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)

            id_to_label = {i: f"species_{i}" for i in range(8)}
            label_to_id = {v: k for k, v in id_to_label.items()}
            preprocessing = {
                "resize": 256,
                "crop_size": 224,
                "mean": [0.485, 0.456, 0.406],
                "std": [0.229, 0.224, 0.225],
            }

            save_checkpoint(
                model=model,
                path=tmp_ckpt,
                epoch=10,
                val_metrics={"image_level": {"macro_f1": 0.75}},
                class_map=label_to_id,
                id_to_label=id_to_label,
                is_official=True,
                preprocessing=preprocessing,
                backbone_name="resnet18",
                num_classes=8,
            )

            data = torch.load(tmp_ckpt, map_location="cpu", weights_only=True)
            required_keys = [
                "epoch", "model_state_dict", "val_metrics",
                "class_map", "id_to_label", "is_official",
                "preprocessing", "backbone_name", "num_classes",
            ]
            for key in required_keys:
                self.assertIn(key, data, f"Thiếu key '{key}' cần thiết cho TV4")

    def test_error_analysis_anti_overwrite(self):
        """Kiểm tra cơ chế chống ghi đè (Anti-overwrite) của error_analysis.py."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            fake_out = tmp_path / "reports"
            fake_out.mkdir()

            # Tạo file giả lập đã tồn tại
            target_json = fake_out / "error_analysis_b2.json"
            target_json.write_text("{\"marker\": \"original_evidence\"}", encoding="utf-8")

            # Tạo checkpoint giả lập
            ckpt_path = tmp_path / "b2_model.pt"
            model = B2CropClassifier(num_classes=8, backbone_name="resnet18", pretrained=False)
            save_checkpoint(model, ckpt_path, epoch=1, num_classes=8, backbone_name="resnet18")

            # 1. Gọi run_error_analysis khi file đã tồn tại và không có cờ overwrite -> Phải ném FileExistsError
            with self.assertRaises(FileExistsError):
                run_error_analysis(
                    checkpoint_path=ckpt_path,
                    output_dir=fake_out,
                    overwrite=False,
                )

            # 2. File ban đầu phải được giữ nguyên vẹn không bị sửa đổi
            self.assertIn("original_evidence", target_json.read_text(encoding="utf-8"))

    def test_preflight_hash_check_rejection(self):
        """Kiểm tra B2ComparisonDataset từ chối ảnh nếu sha256 không khớp khi bật preflight_hash_check."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            class_map_file = tmp_root / "class_map.json"
            class_map_file.write_text(json.dumps({"0": "species_0"}), encoding="utf-8")

            # Tạo ảnh giả lập
            img_file = tmp_root / "test_img.jpg"
            img = Image.new("RGB", (100, 100), color=(255, 0, 0))
            img.save(img_file, format="JPEG")

            # Tạo manifest với sha256 sai (sai hash)
            manifest_file = tmp_root / "val.jsonl"
            row = {
                "image_id": "img_001",
                "crop_id": "crop_001",
                "split": "val",
                "label": "species_0",
                "class_id": 0,
                "bbox_xyxy": [0, 0, 50, 50],
                "quality": {
                    "local_path": "test_img.jpg",
                    "sha256": "wrong_sha256_hash_here_1234567890",
                },
            }
            manifest_file.write_text(json.dumps(row) + "\n", encoding="utf-8")

            # Bật preflight_hash_check=True -> Phải ném ValueError do hash không khớp
            with self.assertRaises(ValueError):
                B2ComparisonDataset(
                    split="val",
                    manifest_path=manifest_file,
                    class_map_path=class_map_file,
                    root=tmp_root,
                    preflight_hash_check=True,
                )


if __name__ == "__main__":
    unittest.main()
