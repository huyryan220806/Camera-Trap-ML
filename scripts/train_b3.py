"""TV3 - Tuần 4: Thử nghiệm trọng số lớp và huấn luyện mô hình B3 (B3 Class-Weighted Crop Classifier).

Nhiệm vụ: W4-03 - Thử trọng số lớp và chốt bộ phân loại (Bàn giao: Quyết định B3 hoặc giữ B2).
Tiêu chí hoàn thành:
1. B3 là biến thể của B2, sử dụng loss có trọng số lớp (class-weighted CrossEntropy).
2. Trọng số lớp được tính toán dựa trên tần suất nghịch đảo (inverse frequency) từ tập train.
3. Cùng dữ liệu snapshot W3-01 đã khóa (provenance SHA-256: d9fd5461...).
4. Cùng ngân sách và siêu tham số với B2 (ResNet-18, SGD lr=0.001, momentum=0.9, 50 epochs, patience=7).
5. Loss gom theo ảnh: mean(crop CE có trọng số per image), rồi mean over images trong batch.
6. Đánh giá cấp ảnh: trung bình vector xác suất softmax rồi argmax.
7. Anti-overwrite run ID (mặc định: b3_run01).
8. Hỗ trợ smoke-test độc lập qua TemporaryDirectory riêng với marker SYNTHETIC_SMOKE.
9. Kiểm định reload checkpoint độc lập đảm bảo tương thích adapter TV4.

Sử dụng:
    # Chạy thử smoke-test:
    python scripts/train_b3.py --smoke-test

    # Chạy huấn luyện chính thức B3:
    python scripts/train_b3.py --config configs/b3_class_weighted.json --run-id b3_run01
"""

import argparse
import hashlib
import json
import logging
import random
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.b2_classifier import B2CropClassifier, save_checkpoint, load_checkpoint
from src.data.b2_dataset import (
    B2ComparisonDataset,
    ImageGroupedBatchSampler,
    b2_collate_fn,
    make_b2_loaders,
)
from src.evaluation.b2_evaluator import evaluate_b2_model, format_validation_markdown_table
from scripts.train_b2 import (
    AGREED_PROVENANCE_SHA256,
    DummyB2Dataset,
    check_w3_manifest_lock,
    set_seed,
    sha256_file,
    _config_hash,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_b3")


def compute_class_weights(
    train_samples: list[dict[str, Any]],
    num_classes: int = 8,
    method: str = "inverse_frequency",
    basis: str = "crop",
) -> torch.Tensor:
    """Tính trọng số lớp dựa trên phân phối tập huấn luyện.

    Công thức chuẩn inverse frequency (sklearn-style):
        weight[c] = total_samples / (num_classes * count[c])
    Sau đó chuẩn hóa sao cho trung bình trọng số = 1.0 để giữ nguyên thang đo learning rate.

    Tham số:
        train_samples: Danh sách mẫu từ dataset train
        num_classes: Số lượng lớp (8)
        method: Phương pháp tính ('inverse_frequency' hoặc 'balanced')
        basis: Cơ sở đếm ('crop' hoặc 'image')
    """
    if basis == "image":
        img_to_cls: dict[str, int] = {}
        for s in train_samples:
            img_to_cls[s["image_id"]] = s["class_id"]
        counts = Counter(img_to_cls.values())
        total = len(img_to_cls)
    else:
        counts = Counter(s["class_id"] for s in train_samples)
        total = len(train_samples)

    weights = np.ones(num_classes, dtype=np.float32)
    for c in range(num_classes):
        cnt = counts.get(c, 0)
        if cnt > 0:
            weights[c] = total / (num_classes * cnt)
        else:
            weights[c] = 1.0

    # Chuẩn hóa về mean = 1.0
    weights = weights / np.mean(weights)

    return torch.from_numpy(weights).float()


def compute_image_grouped_loss_weighted(
    logits: torch.Tensor,
    class_ids: torch.Tensor,
    image_ids: list[str],
    class_weights: torch.Tensor | None = None,
) -> torch.Tensor:
    """Tính loss gom nhóm theo ảnh kèm trọng số lớp cho B3.

    Các bước:
    1. CrossEntropyLoss có trọng số lớp: CE(c) = -w_c * log(p_c) với reduction='none'.
    2. Gom crop loss theo từng image_id.
    3. Lấy trung bình loss các crop của từng ảnh.
    4. Lấy trung bình qua tất cả các ảnh duy nhất trong batch.

    Cách này đảm bảo:
    - Mỗi ảnh đóng góp công bằng, không bị ảnh hưởng bởi số lượng crop/cá thể.
    - Các lớp thiểu số hoặc khó nhận diện được ưu tiên gradient thông qua trọng số w_c.
    """
    criterion = nn.CrossEntropyLoss(weight=class_weights, reduction="none")
    loss_per_crop = criterion(logits, class_ids)

    image_to_losses: dict[str, list[torch.Tensor]] = {}
    for i, img_id in enumerate(image_ids):
        if img_id not in image_to_losses:
            image_to_losses[img_id] = []
        image_to_losses[img_id].append(loss_per_crop[i])

    image_losses = []
    for img_id, crop_losses in image_to_losses.items():
        image_losses.append(torch.stack(crop_losses).mean())

    return torch.stack(image_losses).mean()


def train_one_epoch_b3(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    class_weights: torch.Tensor | None = None,
    epoch: int = 1,
) -> tuple[float, float]:
    """Huấn luyện 1 epoch B3 với loss gom nhóm theo ảnh và trọng số lớp."""
    model.train()

    if hasattr(train_loader, "batch_sampler") and hasattr(train_loader.batch_sampler, "set_epoch"):
        train_loader.batch_sampler.set_epoch(epoch)

    total_loss = 0.0
    total_images = 0
    correct = 0
    total_crops = 0

    device_weights = class_weights.to(device) if class_weights is not None else None

    for batch in train_loader:
        images = batch["images"].to(device, non_blocking=True)
        class_ids = batch["class_ids"].to(device, non_blocking=True)
        image_ids: list[str] = batch["image_ids"]

        optimizer.zero_grad()

        logits = model(images)

        loss = compute_image_grouped_loss_weighted(
            logits=logits,
            class_ids=class_ids,
            image_ids=image_ids,
            class_weights=device_weights,
        )
        loss.backward()
        optimizer.step()

        preds = torch.argmax(logits, dim=-1)
        correct += int((preds == class_ids).sum().item())
        total_crops += len(class_ids)

        n_unique_images = len(set(image_ids))
        total_loss += float(loss.item()) * n_unique_images
        total_images += n_unique_images

    epoch_loss = total_loss / total_images if total_images > 0 else 0.0
    epoch_acc = correct / total_crops if total_crops > 0 else 0.0
    return epoch_loss, epoch_acc


def run_training_b3(
    config: dict[str, Any],
    smoke_test: bool = False,
    smoke_out_dir: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Quy trình huấn luyện B3 Class-Weighted Crop Classifier."""
    train_cfg = config.get("training", {})
    model_cfg = config.get("model", {})
    out_cfg = config.get("output", {})

    seed = train_cfg.get("seed", 42)
    set_seed(seed)

    device_str = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_str)
    logger.info("Thiết bị huấn luyện B3: %s", device)

    num_classes = model_cfg.get("num_classes", 8)
    backbone = model_cfg.get("backbone", "resnet18")

    if smoke_test:
        if smoke_out_dir is None:
            raise ValueError("smoke_out_dir phải được cung cấp khi smoke_test=True.")
        out_dir = smoke_out_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[SMOKE-TEST] Chạy với Dummy Dataset (16 train / 8 val), output: %s", out_dir)
        train_ds = DummyB2Dataset(num_samples=16, num_classes=num_classes, split="train")
        val_ds = DummyB2Dataset(num_samples=8, num_classes=num_classes, split="val")
        train_sampler = ImageGroupedBatchSampler(train_ds.samples, batch_size=4, shuffle=True, seed=seed)
        train_loader = DataLoader(train_ds, batch_sampler=train_sampler, collate_fn=b2_collate_fn)
        val_loader = DataLoader(val_ds, batch_size=4, shuffle=False, drop_last=False, collate_fn=b2_collate_fn)
        id_to_label = {i: f"species_{i}" for i in range(num_classes)}
        epochs = train_cfg.get("epochs", 2)
        pretrained = False
        class_weights = torch.ones(num_classes, dtype=torch.float32)
    else:
        check_w3_manifest_lock(config, ROOT)
        data_cfg = config.get("data", {})
        comp_dir = ROOT / data_cfg.get("comparison_dir", "data/processed/comparison_v1")
        batch_size = train_cfg.get("batch_size", 32)
        num_workers = data_cfg.get("num_workers", 0)

        loaders = make_b2_loaders(
            comparison_dir=comp_dir,
            batch_size=batch_size,
            num_workers=num_workers,
            seed=seed,
            root=ROOT,
            preflight_hash_check=data_cfg.get("preflight_hash_check", False),
        )
        train_loader = loaders["train"]
        val_loader = loaders["val"]

        class_map_path = comp_dir / "class_map.json"
        raw_map = json.loads(class_map_path.read_text(encoding="utf-8"))
        id_to_label = {int(k): v for k, v in raw_map.items()}
        epochs = train_cfg.get("epochs", 50)
        pretrained = model_cfg.get("pretrained", True)

        # Tính class weights từ tập train
        weight_method = train_cfg.get("class_weight_method", "inverse_frequency")
        train_dataset = train_loader.dataset
        class_weights = compute_class_weights(
            train_samples=train_dataset.samples,
            num_classes=num_classes,
            method=weight_method,
            basis="crop",
        )

        logger.info("--- BẢNG TRỌNG SỐ LỚP B3 (Cơ sở Crop Inverse Frequency) ---")
        for c in range(num_classes):
            lbl = id_to_label.get(c, str(c))
            cnt = sum(1 for s in train_dataset.samples if s["class_id"] == c)
            logger.info("  Lớp %d [%s]: %d crops | Trọng số = %.4f", c, lbl, cnt, float(class_weights[c].item()))

        effective_run_id = run_id or config.get("run_id") or out_cfg.get("run_id", "b3_run01")
        out_base = ROOT / out_cfg.get("dir", "outputs/b3_class_weighted")
        out_dir = out_base / effective_run_id
        if out_dir.exists() and any(out_dir.iterdir()):
            msg = (
                f"\n{'=' * 70}\n"
                f"[LỖI TỪ CHỐI GHI ĐÈ RUN CŨ]\n"
                f"Thư mục run '{out_dir}' đã tồn tại và chứa dữ liệu!\n"
                f"Để bảo vệ kết quả thí nghiệm trước đó, hệ thống từ chối ghi đè.\n"
                f"Hãy đổi run_id trong config hoặc truyền --run-id mới (ví dụ: b3_run02).\n"
                f"{'=' * 70}"
            )
            logger.error(msg)
            raise FileExistsError(msg)
        out_dir.mkdir(parents=True, exist_ok=True)

    label_to_id = {v: k for k, v in id_to_label.items()}
    preprocessing_meta = {
        "resize": 256,
        "crop_size": 224,
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
        "train_transforms": "Resize(256) -> RandomCrop(224) -> RandomHorizontalFlip(0.5) -> ColorJitter(b=0.2, c=0.2, s=0.1, h=0.05) -> ToTensor() -> Normalize()",
        "val_transforms": "Resize(256) -> CenterCrop(224) -> ToTensor() -> Normalize()",
    }

    logger.info("Khởi tạo mô hình B3 (Backbone: %s, Pretrained: %s)...", backbone, pretrained)
    model = B2CropClassifier(
        num_classes=num_classes,
        backbone_name=backbone,
        pretrained=pretrained,
        dropout_p=model_cfg.get("dropout_p", 0.0),
    ).to(device)

    lr = train_cfg.get("lr", 0.001)
    momentum = train_cfg.get("momentum", 0.9)
    weight_decay = train_cfg.get("weight_decay", 0.0001)
    step_size = train_cfg.get("step_size", 10)
    gamma = train_cfg.get("gamma", 0.1)
    patience = train_cfg.get("patience", 7)

    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=lr,
        momentum=momentum,
        weight_decay=weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=step_size, gamma=gamma)

    best_ckpt_path = out_dir / out_cfg.get("best_checkpoint_name", "best_model.pt")
    last_ckpt_path = out_dir / out_cfg.get("last_checkpoint_name", "last_model.pt")
    log_file = out_dir / out_cfg.get("log_file_name", "train_log.jsonl")
    val_report_path = out_dir / out_cfg.get("val_report_name", "validation_comparison.json")
    val_table_path = out_dir / out_cfg.get("val_table_md_name", "validation_comparison.md")

    log_header = {
        "MARKER": "SYNTHETIC_SMOKE" if smoke_test else "OFFICIAL_B3_RUN",
        "config_hash": _config_hash(config),
        "class_weights": {id_to_label.get(i, str(i)): round(float(class_weights[i].item()), 4) for i in range(num_classes)},
    }
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(log_header, ensure_ascii=False) + "\n")

    best_image_f1 = -1.0
    best_epoch = -1
    best_val_metrics: dict[str, Any] = {}
    last_val_metrics: dict[str, Any] = {}

    logger.info("Bắt đầu huấn luyện B3 với ngân sách %d epochs...", epochs)
    start_time = time.time()
    no_improve = 0

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        train_loss, train_acc = train_one_epoch_b3(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            device=device,
            class_weights=class_weights,
            epoch=epoch,
        )
        scheduler.step()

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

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

        logger.info(
            "B3 Epoch [%d/%d] (%0.1fs) Loss=%.4f Acc=%.1f%% | Val Loss=%.4f CropF1=%.1f%% ImgAcc=%.1f%% ImgF1=%.1f%%",
            epoch, epochs, epoch_time, train_loss, train_acc * 100,
            val_eval["val_loss"], crop_f1 * 100, img_acc * 100, img_f1 * 100,
        )

        last_val_metrics = val_eval

        if img_f1 > best_image_f1:
            best_image_f1 = img_f1
            best_epoch = epoch
            best_val_metrics = val_eval
            save_checkpoint(
                model=model,
                path=best_ckpt_path,
                epoch=epoch,
                optimizer=optimizer,
                scheduler=scheduler,
                val_metrics=val_eval,
                config=config,
                class_map=label_to_id,
                id_to_label=id_to_label,
                is_official=not smoke_test,
                provenance_sha256=AGREED_PROVENANCE_SHA256 if not smoke_test else None,
                preprocessing=preprocessing_meta,
                backbone_name=backbone,
                num_classes=num_classes,
            )
            no_improve = 0
            logger.info("--> Best B3 checkpoint tại epoch %d (ImgF1=%.2f%%).", epoch, img_f1 * 100)
        else:
            no_improve += 1
            if not smoke_test and no_improve >= patience:
                logger.info("B3 Early stopping tại epoch %d (không cải thiện %d epochs).", epoch, patience)
                break

    total_time = time.time() - start_time
    logger.info("Hoàn tất huấn luyện B3 sau %.1fs! Best epoch=%d, Best ImgF1=%.2f%%", total_time, best_epoch, best_image_f1 * 100)

    save_checkpoint(
        model=model,
        path=last_ckpt_path,
        epoch=epoch,
        optimizer=optimizer,
        scheduler=scheduler,
        val_metrics=last_val_metrics,
        config=config,
        class_map=label_to_id,
        id_to_label=id_to_label,
        is_official=not smoke_test,
        provenance_sha256=AGREED_PROVENANCE_SHA256 if not smoke_test else None,
        preprocessing=preprocessing_meta,
        backbone_name=backbone,
        num_classes=num_classes,
    )

    # Kiểm định reload độc lập
    logger.info("Kiểm định reload độc lập checkpoint B3 tại: %s", best_ckpt_path)
    reload_model = B2CropClassifier(num_classes=num_classes, backbone_name=backbone, pretrained=False)
    loaded_data = load_checkpoint(model=reload_model, path=best_ckpt_path, map_location="cpu")
    if loaded_data.get("epoch") != best_epoch:
        raise ValueError(f"Reload thất bại: epoch trong checkpoint ({loaded_data.get('epoch')}) != best_epoch ({best_epoch})")
    if loaded_data.get("is_official") != (not smoke_test):
        raise ValueError("Reload thất bại: marker is_official không khớp")
    reload_model.eval()
    with torch.no_grad():
        dummy_out = reload_model(torch.randn(1, 3, 224, 224))
        if dummy_out.shape != (1, num_classes):
            raise ValueError(f"Reload thất bại: forward pass shape sai: {dummy_out.shape}")
    logger.info("Kiểm định reload checkpoint B3 thành công: mô hình hợp lệ và sẵn sàng.")

    report_payload = {
        "task": "W4-03 B3 Class Weighted Crop Classifier",
        "smoke_test": smoke_test,
        "synthetic_marker": "SYNTHETIC_SMOKE" if smoke_test else None,
        "best_epoch": best_epoch,
        "total_epochs_run": epoch,
        "total_training_time_sec": round(total_time, 2),
        "config": config,
        "class_weights": {id_to_label.get(i, str(i)): round(float(class_weights[i].item()), 4) for i in range(num_classes)},
        "image_level_metrics": best_val_metrics.get("image_level", {}),
        "crop_level_metrics": best_val_metrics.get("crop_level", {}),
    }
    with open(val_report_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2, ensure_ascii=False)

    md_table = format_validation_markdown_table(
        image_metrics=best_val_metrics.get("image_level", {}),
        crop_metrics=best_val_metrics.get("crop_level", {}),
    )
    val_table_path.write_text(md_table, encoding="utf-8")
    logger.info("Đã xuất báo cáo B3 tại: %s", val_table_path)

    return report_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Huấn luyện B3 Class-Weighted Crop Classifier (TV3 Tuần 4).")
    parser.add_argument("--config", type=str, default="configs/b3_class_weighted.json", help="File cấu hình.")
    parser.add_argument("--smoke-test", action="store_true", help="Chạy thử nghiệm pipeline trên dữ liệu giả lập.")
    parser.add_argument("--run-id", type=str, default=None, help="Mã định danh lần chạy (ví dụ: b3_run01).")
    args = parser.parse_args()

    cfg_path = ROOT / args.config
    if cfg_path.exists():
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
    else:
        logger.warning("Không tìm thấy file cấu hình %s, sử dụng cấu hình mặc định.", cfg_path)
        config = {}

    (ROOT / "outputs").mkdir(parents=True, exist_ok=True)

    if args.smoke_test:
        with tempfile.TemporaryDirectory(prefix="b3_smoke_", dir=ROOT / "outputs") as tmp_dir:
            logger.info("[SMOKE-TEST] Output tạm tại: %s", tmp_dir)
            run_training_b3(config=config, smoke_test=True, smoke_out_dir=Path(tmp_dir), run_id=args.run_id)
        logger.info("[SMOKE-TEST] Đã dọn thư mục tạm. B3 Pipeline OK!")
    else:
        run_training_b3(config=config, smoke_test=False, run_id=args.run_id)


if __name__ == "__main__":
    main()
