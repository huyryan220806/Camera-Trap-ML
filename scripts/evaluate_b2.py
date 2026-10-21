"""TV3 - Tuần 3: Đánh giá mô hình B2 Crop Classifier độc lập.

Tính toán và xuất:
1. Crop-level classification metrics
2. Image-level aggregated metrics (trung bình xác suất các crop cùng image_id rồi argmax)
3. Confusion matrix và per-class F1/Precision/Recall
4. Báo cáo định dạng JSON và bảng so sánh Markdown

Sử dụng:
    python scripts/evaluate_b2.py --checkpoint outputs/b2_crop_classifier/best_model.pt
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.b2_classifier import B2CropClassifier, load_checkpoint
from src.data.b2_dataset import B2ComparisonDataset, b2_collate_fn
from src.evaluation.b2_evaluator import evaluate_b2_model, format_validation_markdown_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("evaluate_b2")


def main() -> None:
    parser = argparse.ArgumentParser(description="Đánh giá mô hình B2 Crop Classifier độc lập.")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="outputs/b2_crop_classifier/best_model.pt",
        help="Đường dẫn tới checkpoint B2.",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="val",
        choices=["val", "test", "train"],
        help="Tập dữ liệu cần đánh giá.",
    )
    parser.add_argument(
        "--comparison-dir",
        type=str,
        default="data/processed/comparison_v1",
        help="Thư mục chứa comparison_v1 của TV1.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Kích thước batch.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/b2_crop_classifier",
        help="Thư mục xuất báo cáo.",
    )
    args = parser.parse_args()

    ckpt_path = ROOT / args.checkpoint
    if not ckpt_path.exists():
        logger.error("Không tìm thấy checkpoint: %s", ckpt_path)
        sys.exit(1)

    comp_dir = ROOT / args.comparison_dir
    manifest_path = comp_dir / "b2" / f"{args.split}.jsonl"
    class_map_path = comp_dir / "class_map.json"

    if not manifest_path.exists() or not class_map_path.exists():
        logger.error("Không tìm thấy dữ liệu comparison_v1 tại: %s", comp_dir)
        sys.exit(1)

    raw_map = json.loads(class_map_path.read_text(encoding="utf-8"))
    id_to_label = {int(k): v for k, v in raw_map.items()}
    num_classes = len(raw_map)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Thiết bị đánh giá: %s", device)

    # Khởi tạo dataset và loader
    dataset = B2ComparisonDataset(
        split=args.split,
        manifest_path=manifest_path,
        class_map_path=class_map_path,
        root=ROOT,
    )
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=2,
        collate_fn=b2_collate_fn,
    )

    # Nạp mô hình từ checkpoint
    model = B2CropClassifier(num_classes=num_classes, backbone_name="resnet18", pretrained=False)
    checkpoint_data = load_checkpoint(model=model, path=ckpt_path, map_location=device)
    model.to(device)
    logger.info("Đã nạp checkpoint từ epoch %d.", checkpoint_data.get("epoch", -1))

    # Đánh giá
    results = evaluate_b2_model(
        model=model,
        data_loader=loader,
        device=device,
        num_classes=num_classes,
        id_to_label=id_to_label,
    )

    crop_met = results["crop_level"]
    img_met = results["image_level"]

    logger.info("=" * 60)
    logger.info("KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH B2 TRÊN TẬP %s:", args.split.upper())
    logger.info("  [Cấp Crop] - Acc: %.2f%% | Macro F1: %.2f%% (Tổng: %d crops)",
                crop_met["accuracy"] * 100, crop_met["macro_f1"] * 100, crop_met["total_samples"])
    logger.info("  [CẤP ẢNH TỔNG HỢP] - Acc: %.2f%% | Macro F1: %.2f%% (Tổng: %d ảnh)",
                img_met["accuracy"] * 100, img_met["macro_f1"] * 100, img_met["total_unique_images"])
    logger.info("=" * 60)

    # Xuất file kết quả
    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / f"eval_report_{args.split}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    md_table = format_validation_markdown_table(image_metrics=img_met, crop_metrics=crop_met)
    table_path = out_dir / f"eval_table_{args.split}.md"
    table_path.write_text(md_table, encoding="utf-8")

    logger.info("Đã lưu báo cáo tại: %s", report_path)
    logger.info("Đã lưu bảng Markdown tại: %s", table_path)


if __name__ == "__main__":
    main()
