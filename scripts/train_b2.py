"""TV3 - Tuần 3: Huấn luyện mô hình phân loại động vật trên vùng cắt (B2 Crop Classifier).

Tiêu chí hoàn thành:
1. Chỉ chạy chính thức sau khi W3-01 khóa manifest (data/processed/comparison_v1/provenance.json).
2. Dùng cùng ảnh và ngân sách với B1 (backbone ResNet18, 15 epochs, optimizer AdamW, lr 1e-4).
3. Trọng số mất mát theo ảnh: sample_weight = 1.0 / parent_crop_count.
4. Đánh giá cấp ảnh: Trung bình vector xác suất (softmax) các crop cùng image_id rồi argmax.
5. Lưu checkpoint tốt nhất, cấu hình huấn luyện và bảng so sánh validation.

Sử dụng:
    # Chạy thử smoke-test kiểm tra toàn bộ pipeline (không cần GPU hay dữ liệu thật):
    python scripts/train_b2.py --smoke-test

    # Chạy huấn luyện chính thức (sau khi W3-01 khóa manifest):
    python scripts/train_b2.py --config configs/b2_crop_classifier.json
"""

import argparse
import io
import json
import logging
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.b2_classifier import B2CropClassifier, save_checkpoint
from src.data.b2_dataset import B2ComparisonDataset, b2_collate_fn, make_b2_loaders
from src.evaluation.b2_evaluator import evaluate_b2_model, format_validation_markdown_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_b2")


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class DummyB2Dataset(Dataset):
    """Dataset giả lập cho chế độ --smoke-test."""

    def __init__(self, num_samples: int = 16, num_classes: int = 8, split: str = "train") -> None:
        self.num_samples = num_samples
        self.num_classes = num_classes
        self.split = split
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.samples = []
        for i in range(num_samples):
            img_idx = i // 2  # mỗi ảnh 2 crop
            cls_id = img_idx % num_classes
            self.samples.append({
                "image_id": f"dummy_img_{img_idx:03d}",
                "crop_id": f"dummy_crop_{i:03d}",
                "class_id": cls_id,
                "label": f"species_{cls_id}",
                "sample_weight": 0.5,
            })

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        s = self.samples[idx]
        buf = io.BytesIO()
        Image.new("RGB", (224, 224), color=(120, 100 + idx * 5, 80)).save(buf, format="JPEG")
        buf.seek(0)
        img = Image.open(buf)
        tensor = self.transform(img)
        return {
            "image": tensor,
            "class_id": s["class_id"],
            "sample_weight": torch.tensor(s["sample_weight"], dtype=torch.float32),
            "image_id": s["image_id"],
            "crop_id": s["crop_id"],
            "label": s["label"],
        }


def check_w3_manifest_lock(config: dict[str, Any], root: Path) -> None:
    """Kiểm tra điều kiện tiên quyết: W3-01 phải khóa manifest trước khi chạy chính thức."""
    data_cfg = config.get("data", {})
    manifest_train = root / data_cfg.get("manifest_train", "data/processed/comparison_v1/b2/train.jsonl")
    manifest_val = root / data_cfg.get("manifest_val", "data/processed/comparison_v1/b2/val.jsonl")
    class_map = root / data_cfg.get("class_map", "data/processed/comparison_v1/class_map.json")
    provenance = root / data_cfg.get("provenance", "data/processed/comparison_v1/provenance.json")

    missing = []
    if not manifest_train.exists():
        missing.append(str(manifest_train))
    if not manifest_val.exists():
        missing.append(str(manifest_val))
    if not class_map.exists():
        missing.append(str(class_map))
    if not provenance.exists():
        missing.append(str(provenance))

    if missing:
        msg = (
            "\n" + "=" * 70 + "\n"
            "[LỖI TIÊU CHÍ NGHIỆM THU TUẦN 3]\n"
            "Chưa thể chạy huấn luyện B2 chính thức vì thiếu file khóa dữ liệu W3-01:\n"
            + "\n".join(f"  - {f}" for f in missing)
            + "\n\nQuy tắc: 'Chỉ chạy chính thức sau khi W3-01 khóa manifest'.\n"
            "Hãy đảm bảo TV1 đã hoàn tất scripts/freeze_comparison.py trước khi chạy.\n"
            "Để chạy thử nghiệm toàn bộ code mà không cần dữ liệu thật, hãy dùng:\n"
            "  python scripts/train_b2.py --smoke-test\n"
            + "=" * 70
        )
        logger.error(msg)
        raise FileNotFoundError(msg)


def train_one_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler | None,
    device: torch.device,
    use_amp: bool = False,
) -> tuple[float, float]:
    """Huấn luyện 1 epoch với sample weighting per-image."""
    model.train()
    criterion = nn.CrossEntropyLoss(reduction="none")

    total_loss = 0.0
    total_weight = 0.0
    correct = 0
    total_samples = 0

    for batch in train_loader:
        images = batch["images"].to(device, non_blocking=True)
        class_ids = batch["class_ids"].to(device, non_blocking=True)
        weights = batch["sample_weights"].to(device, non_blocking=True)

        optimizer.zero_grad()

        if use_amp and scaler:
            with torch.amp.autocast("cuda"):
                logits = model(images)
                loss_per_sample = criterion(logits, class_ids)
                weighted_loss = torch.sum(loss_per_sample * weights) / (torch.sum(weights) + 1e-8)
            scaler.scale(weighted_loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(images)
            loss_per_sample = criterion(logits, class_ids)
            weighted_loss = torch.sum(loss_per_sample * weights) / (torch.sum(weights) + 1e-8)
            weighted_loss.backward()
            optimizer.step()

        preds = torch.argmax(logits, dim=-1)
        correct += int((preds == class_ids).sum().item())
        total_samples += len(class_ids)

        total_loss += float(weighted_loss.item()) * len(class_ids)
        total_weight += len(class_ids)

    epoch_loss = total_loss / total_weight if total_weight > 0 else 0.0
    epoch_acc = correct / total_samples if total_samples > 0 else 0.0
    return epoch_loss, epoch_acc


def run_training(config: dict[str, Any], smoke_test: bool = False) -> dict[str, Any]:
    """Tiến trình huấn luyện chính."""
    train_cfg = config.get("training", {})
    model_cfg = config.get("model", {})
    out_cfg = config.get("output", {})

    seed = train_cfg.get("seed", 42)
    set_seed(seed)

    device_str = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_str)
    logger.info("Sử dụng thiết bị huấn luyện: %s", device)

    # Thư mục xuất kết quả
    out_dir = ROOT / out_cfg.get("dir", "outputs/b2_crop_classifier")
    out_dir.mkdir(parents=True, exist_ok=True)

    num_classes = model_cfg.get("num_classes", 8)
    backbone = model_cfg.get("backbone", "resnet18")
    pretrained = model_cfg.get("pretrained", True)

    # 1. Khởi tạo Datasets / Loaders
    if smoke_test:
        logger.info("[SMOKE-TEST] Sử dụng Dummy Dataset 16 mẫu kiểm tra pipeline...")
        train_ds = DummyB2Dataset(num_samples=16, num_classes=num_classes, split="train")
        val_ds = DummyB2Dataset(num_samples=8, num_classes=num_classes, split="val")
        train_loader = DataLoader(train_ds, batch_size=4, shuffle=True, collate_fn=b2_collate_fn)
        val_loader = DataLoader(val_ds, batch_size=4, shuffle=False, collate_fn=b2_collate_fn)
        id_to_label = {i: f"species_{i}" for i in range(num_classes)}
        epochs = 2
    else:
        check_w3_manifest_lock(config, ROOT)
        comp_dir = ROOT / config["data"]["dataset_version"]
        batch_size = train_cfg.get("batch_size", 32)
        num_workers = config["data"].get("num_workers", 2)
        loaders = make_b2_loaders(
            comparison_dir=comp_dir,
            batch_size=batch_size,
            num_workers=num_workers,
            seed=seed,
            root=ROOT,
            preflight_hash_check=config["data"].get("preflight_hash_check", False),
        )
        train_loader = loaders["train"]
        val_loader = loaders["val"]
        class_map_path = comp_dir / "class_map.json"
        raw_map = json.loads(class_map_path.read_text(encoding="utf-8"))
        id_to_label = {int(k): v for k, v in raw_map.items()}
        epochs = train_cfg.get("epochs", 15)

    # 2. Khởi tạo Model
    logger.info("Khởi tạo mô hình B2CropClassifier (Backbone: %s, Pretrained: %s)...", backbone, pretrained)
    model = B2CropClassifier(
        num_classes=num_classes,
        backbone_name=backbone,
        pretrained=pretrained if not smoke_test else False,
        dropout_p=model_cfg.get("dropout_p", 0.2),
    ).to(device)

    # 3. Optimizer & Scheduler
    lr = train_cfg.get("learning_rate", 1e-4)
    weight_decay = train_cfg.get("weight_decay", 1e-4)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    use_amp = train_cfg.get("mixed_precision", True) and (device_str == "cuda")
    scaler = torch.amp.GradScaler("cuda") if use_amp else None

    # 4. Huấn luyện từng epoch
    best_image_f1 = -1.0
    best_metrics: dict[str, Any] = {}
    train_history = []
    log_file = ROOT / out_cfg.get("log_file", "outputs/b2_crop_classifier/train_log.jsonl")

    logger.info("Bắt đầu huấn luyện B2 với ngân sách %d epochs...", epochs)
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        train_loss, train_acc = train_one_epoch(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            scaler=scaler,
            device=device,
            use_amp=use_amp,
        )
        scheduler.step()

        # Đánh giá validation (cả crop-level và image-level)
        val_eval = evaluate_b2_model(
            model=model,
            data_loader=val_loader,
            device=device,
            num_classes=num_classes,
            id_to_label=id_to_label,
        )
        epoch_time = time.time() - epoch_start

        crop_f1 = val_eval["crop_level"]["macro_f1"]
        img_f1 = val_eval["image_level"]["macro_f1"]
        img_acc = val_eval["image_level"]["accuracy"]

        log_entry = {
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 4),
            "val_loss": val_eval["val_loss"],
            "val_crop_f1": crop_f1,
            "val_image_acc": img_acc,
            "val_image_f1": img_f1,
            "lr": optimizer.param_groups[0]["lr"],
            "epoch_time_sec": round(epoch_time, 2),
        }
        train_history.append(log_entry)

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        logger.info(
            "Epoch [%d/%d] (%0.1fs) - Train Loss: %.4f, Acc: %.2f%% | Val Loss: %.4f | "
            "Cấp Crop F1: %.2f%% | CẤP ẢNH Acc: %.2f%%, F1: %.2f%%",
            epoch, epochs, epoch_time, train_loss, train_acc * 100, val_eval["val_loss"],
            crop_f1 * 100, img_acc * 100, img_f1 * 100,
        )

        # Lưu checkpoint tốt nhất dựa trên Image-level Macro F1
        if img_f1 > best_image_f1:
            best_image_f1 = img_f1
            best_metrics = val_eval
            best_ckpt_path = ROOT / out_cfg.get("best_checkpoint", "outputs/b2_crop_classifier/best_model.pt")
            save_checkpoint(
                model=model,
                path=best_ckpt_path,
                epoch=epoch,
                optimizer=optimizer,
                scheduler=scheduler,
                val_metrics=val_eval,
                config=config,
            )
            logger.info("--> Đã lưu checkpoint B2 tốt nhất tại: %s (Image Macro F1: %.2f%%)", best_ckpt_path, img_f1 * 100)

    total_training_time = time.time() - start_time
    logger.info("Hoàn tất huấn luyện sau %0.1f giây! Best Image-level F1: %.2f%%", total_training_time, best_image_f1 * 100)

    # 5. Lưu checkpoint cuối cùng
    last_ckpt_path = ROOT / out_cfg.get("last_checkpoint", "outputs/b2_crop_classifier/last_model.pt")
    save_checkpoint(
        model=model,
        path=last_ckpt_path,
        epoch=epochs,
        optimizer=optimizer,
        scheduler=scheduler,
        val_metrics=best_metrics,
        config=config,
    )

    # 6. Xuất báo cáo và bảng so sánh Markdown
    val_report_path = ROOT / out_cfg.get("val_report", "outputs/b2_crop_classifier/validation_comparison.json")
    val_table_path = ROOT / out_cfg.get("val_table_md", "outputs/b2_crop_classifier/validation_comparison.md")

    report_payload = {
        "task": "W3-02 B2 Crop Classifier",
        "best_epoch": best_metrics.get("epoch", epochs),
        "total_training_time_sec": round(total_training_time, 2),
        "config": config,
        "image_level_metrics": best_metrics.get("image_level", {}),
        "crop_level_metrics": best_metrics.get("crop_level", {}),
    }
    with open(val_report_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2, ensure_ascii=False)

    md_table = format_validation_markdown_table(
        image_metrics=best_metrics.get("image_level", {}),
        crop_metrics=best_metrics.get("crop_level", {}),
    )
    val_table_path.write_text(md_table, encoding="utf-8")
    logger.info("Đã xuất bảng so sánh validation tại: %s", val_table_path)

    return report_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Huấn luyện mô hình B2 Crop Classifier (TV3 Tuần 3).")
    parser.add_argument("--config", type=str, default="configs/b2_crop_classifier.json", help="Đường dẫn file cấu hình.")
    parser.add_argument("--smoke-test", action="store_true", help="Chạy thử nghiệm kiểm tra pipeline trên dữ liệu giả lập.")
    args = parser.parse_args()

    cfg_path = ROOT / args.config
    if cfg_path.exists():
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
    else:
        logger.warning("Không tìm thấy file cấu hình %s, sử dụng cấu hình mặc định.", cfg_path)
        config = {}

    run_training(config=config, smoke_test=args.smoke_test)


if __name__ == "__main__":
    main()
