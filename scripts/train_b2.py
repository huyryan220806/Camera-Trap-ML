"""TV3 - Tuần 3: Huấn luyện mô hình phân loại động vật trên vùng cắt (B2 Crop Classifier).

Tiêu chí hoàn thành:
1. Chỉ chạy chính thức sau khi W3-01 khóa manifest: kiểm tra provenance.json tồn tại
   VÀ SHA-256 khớp với hash đã thống nhất với TV2 (d9fd5461...).
2. Dùng cùng ảnh và ngân sách với B1 theo W3_PROTOCOL_AGREEMENT:
   ResNet18 ImageNet, SGD lr=0.001 momentum=0.9, StepLR step=10 gamma=0.1,
   50 epochs, patience=7, batch=32, FP32, không dropout, không mixed precision.
3. Loss: mean(crop CE per source image), rồi mean over source images trong batch.
4. Đánh giá cấp ảnh: mean softmax probability của các crop cùng image_id rồi argmax.
5. Checkpoint: lưu best theo image-level macro F1, theo dõi best_epoch chính xác,
   lưu last checkpoint kèm metrics của epoch cuối (không phải best).
6. Smoke-test: dùng TemporaryDirectory riêng, ghi marker SYNTHETIC_SMOKE,
   không đụng output của run chính thức.

Sử dụng:
    # Chạy thử smoke-test (không cần GPU hay dữ liệu thật):
    python scripts/train_b2.py --smoke-test

    # Chạy huấn luyện chính thức (sau khi W3-01 khóa manifest):
    python scripts/train_b2.py --config configs/b2_crop_classifier.json
"""

import argparse
import hashlib
import io
import json
import logging
import random
import shutil
import sys
import tempfile
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

# Hash SHA-256 của provenance.json đã được TV2 thống nhất và ký trong biên bản
# W3_PROTOCOL_AGREEMENT_2026-10-18.json (freeze_sha256 field)
AGREED_PROVENANCE_SHA256 = "d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f"


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class DummyB2Dataset(Dataset):
    """Dataset giả lập cho chế độ --smoke-test.

    Dùng TemporaryDirectory riêng, có marker SYNTHETIC_SMOKE trong mọi output.
    Không chia sẻ output dir với run chính thức.
    """

    def __init__(self, num_samples: int = 16, num_classes: int = 8, split: str = "train") -> None:
        self.num_samples = num_samples
        self.num_classes = num_classes
        self.split = split
        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.samples = []
        for i in range(num_samples):
            img_idx = i // 2  # mỗi ảnh 2 crop
            cls_id = img_idx % num_classes
            self.samples.append({
                "image_id": f"dummy_img_{img_idx:03d}",
                "crop_id": f"dummy_crop_{split}_{i:03d}",
                "class_id": cls_id,
                "label": f"species_{cls_id}",
                "_sample_weight": 0.5,  # 2 crop / ảnh
            })

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        s = self.samples[idx]
        buf = io.BytesIO()
        Image.new("RGB", (224, 224), color=(120, (100 + idx * 3) % 256, 80)).save(buf, format="JPEG")
        buf.seek(0)
        img = Image.open(buf)
        tensor = self.transform(img)
        return {
            "image": tensor,
            "class_id": s["class_id"],
            "sample_weight": torch.tensor(s["_sample_weight"], dtype=torch.float32),
            "image_id": s["image_id"],
            "crop_id": s["crop_id"],
            "label": s["label"],
        }


def check_w3_manifest_lock(config: dict[str, Any], root: Path) -> None:
    """Kiểm tra điều kiện tiên quyết: W3-01 phải khóa manifest trước khi chạy chính thức.

    Lỗi 3 sửa: không chỉ kiểm tra exists() mà còn xác minh SHA-256 của provenance.json
    khớp với hash đã thống nhất trong W3_PROTOCOL_AGREEMENT_2026-10-18.
    """
    data_cfg = config.get("data", {})
    comp_dir = root / data_cfg.get("comparison_dir", "data/processed/comparison_v1")

    manifest_train = comp_dir / "b2" / "train.jsonl"
    manifest_val = comp_dir / "b2" / "val.jsonl"
    class_map = comp_dir / "class_map.json"
    provenance = comp_dir / "provenance.json"

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
            "Hãy lấy dữ liệu từ nhánh TV1 (origin/feat/metadata-split) trước khi chạy.\n"
            "Để kiểm tra pipeline, dùng: python scripts/train_b2.py --smoke-test\n"
            + "=" * 70
        )
        logger.error(msg)
        raise FileNotFoundError(msg)

    # Lỗi 3 sửa: xác minh SHA-256 của provenance.json
    actual_prov_sha = sha256_file(provenance)
    if actual_prov_sha != AGREED_PROVENANCE_SHA256:
        msg = (
            "\n" + "=" * 70 + "\n"
            "[LỖI XÁC MINH SNAPSHOT]\n"
            f"provenance.json tồn tại nhưng SHA-256 không khớp!\n"
            f"  Kỳ vọng (đã thống nhất với TV2): {AGREED_PROVENANCE_SHA256}\n"
            f"  Thực tế:                          {actual_prov_sha}\n"
            f"  File: {provenance}\n\n"
            "Snapshot này KHÔNG phải bản đã khóa từ TV1 commit 7e9b194.\n"
            "Không được train trên dữ liệu chưa xác minh.\n"
            + "=" * 70
        )
        logger.error(msg)
        raise ValueError(msg)

    logger.info("Gate W3-01 OK: provenance.json SHA-256 khớp (%s...)", actual_prov_sha[:16])


def compute_image_grouped_loss(
    logits: torch.Tensor,
    class_ids: torch.Tensor,
    image_ids: list[str],
    device: torch.device,
) -> torch.Tensor:
    """Tính loss theo protocol B2: mean(crop CE per image) rồi mean over images.

    Lỗi 5 sửa: thay vì sum(w*loss)/sum(w) per batch (không tương đương per-image),
    ta gom crop theo image_id, lấy trung bình CE trong từng ảnh rồi trung bình các ảnh.
    Cách này đảm bảo mỗi ảnh đóng góp đều nhau, bất kể số crop.
    """
    criterion = nn.CrossEntropyLoss(reduction="none")
    loss_per_crop = criterion(logits, class_ids)  # shape: (batch_size,)

    # Gom theo image_id
    image_to_losses: dict[str, list[torch.Tensor]] = {}
    for i, img_id in enumerate(image_ids):
        if img_id not in image_to_losses:
            image_to_losses[img_id] = []
        image_to_losses[img_id].append(loss_per_crop[i])

    # Trung bình crop loss trong từng ảnh → trung bình qua các ảnh
    image_losses = []
    for img_id, crop_losses in image_to_losses.items():
        stacked = torch.stack(crop_losses)
        image_losses.append(stacked.mean())

    return torch.stack(image_losses).mean()


def train_one_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> tuple[float, float]:
    """Huấn luyện 1 epoch theo protocol B2: per-image loss grouping, FP32, SGD."""
    model.train()

    total_loss = 0.0
    total_images = 0
    correct = 0
    total_crops = 0

    for batch in train_loader:
        images = batch["images"].to(device, non_blocking=True)
        class_ids = batch["class_ids"].to(device, non_blocking=True)
        image_ids: list[str] = batch["image_ids"]

        optimizer.zero_grad()

        logits = model(images)

        # Lỗi 5 sửa: loss theo ảnh, không theo weighted crop
        loss = compute_image_grouped_loss(
            logits=logits,
            class_ids=class_ids,
            image_ids=image_ids,
            device=device,
        )
        loss.backward()
        optimizer.step()

        preds = torch.argmax(logits, dim=-1)
        correct += int((preds == class_ids).sum().item())
        total_crops += len(class_ids)

        # Đếm số ảnh duy nhất trong batch để theo dõi loss per-image
        n_unique_images = len(set(image_ids))
        total_loss += float(loss.item()) * n_unique_images
        total_images += n_unique_images

    epoch_loss = total_loss / total_images if total_images > 0 else 0.0
    epoch_acc = correct / total_crops if total_crops > 0 else 0.0
    return epoch_loss, epoch_acc


def run_training(
    config: dict[str, Any],
    smoke_test: bool = False,
    smoke_out_dir: Path | None = None,
) -> dict[str, Any]:
    """Tiến trình huấn luyện chính."""
    train_cfg = config.get("training", {})
    model_cfg = config.get("model", {})
    out_cfg = config.get("output", {})

    seed = train_cfg.get("seed", 42)
    set_seed(seed)

    device_str = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_str)
    logger.info("Sử dụng thiết bị huấn luyện: %s", device)

    num_classes = model_cfg.get("num_classes", 8)
    backbone = model_cfg.get("backbone", "resnet18")

    # Lỗi 2 sửa: smoke-test dùng thư mục riêng, không đụng output chính thức
    if smoke_test:
        if smoke_out_dir is None:
            raise ValueError("smoke_out_dir phải được cung cấp khi smoke_test=True.")
        out_dir = smoke_out_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[SMOKE-TEST] Sử dụng Dummy Dataset (16 train / 8 val mẫu), output: %s", out_dir)
        train_ds = DummyB2Dataset(num_samples=16, num_classes=num_classes, split="train")
        val_ds = DummyB2Dataset(num_samples=8, num_classes=num_classes, split="val")
        train_loader = DataLoader(train_ds, batch_size=4, shuffle=True, drop_last=False, collate_fn=b2_collate_fn)
        val_loader = DataLoader(val_ds, batch_size=4, shuffle=False, drop_last=False, collate_fn=b2_collate_fn)
        id_to_label = {i: f"species_{i}" for i in range(num_classes)}
        epochs = train_cfg.get("epochs", 2)
        pretrained = False
    else:
        # Lỗi 1 sửa: đường dẫn từ config key "comparison_dir", không dùng "dataset_version"
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

        out_dir = ROOT / out_cfg.get("dir", "outputs/b2_crop_classifier")
        out_dir.mkdir(parents=True, exist_ok=True)

    # Khởi tạo Model theo protocol: ResNet18 ImageNet, không dropout
    logger.info("Khởi tạo B2CropClassifier (Backbone: %s, Pretrained: %s)...", backbone, pretrained)
    model = B2CropClassifier(
        num_classes=num_classes,
        backbone_name=backbone,
        pretrained=pretrained,
        dropout_p=model_cfg.get("dropout_p", 0.0),  # Protocol: không dropout
    ).to(device)

    # Optimizer & Scheduler theo protocol: SGD, StepLR
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

    # Đường dẫn output
    best_ckpt_path = out_dir / out_cfg.get("best_checkpoint_name", "best_model.pt")
    last_ckpt_path = out_dir / out_cfg.get("last_checkpoint_name", "last_model.pt")
    log_file = out_dir / out_cfg.get("log_file_name", "train_log.jsonl")
    val_report_path = out_dir / out_cfg.get("val_report_name", "validation_comparison.json")
    val_table_path = out_dir / out_cfg.get("val_table_md_name", "validation_comparison.md")

    # Lỗi 2 sửa: ghi marker SYNTHETIC_SMOKE vào log header nếu là smoke test
    if smoke_test:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"MARKER": "SYNTHETIC_SMOKE", "note": "Do not use as official B2 result."}) + "\n")
    else:
        # Run chính thức: mở log ở chế độ write (không append vào run cũ)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({"MARKER": "OFFICIAL_RUN", "config_hash": _config_hash(config)}) + "\n")

    # Huấn luyện từng epoch
    best_image_f1 = -1.0
    best_epoch = -1  # Lỗi 6 sửa: theo dõi riêng
    best_val_metrics: dict[str, Any] = {}
    last_val_metrics: dict[str, Any] = {}  # Lỗi 6 sửa: lưu metrics epoch cuối riêng

    logger.info("Bắt đầu huấn luyện B2 với ngân sách %d epochs...", epochs)
    start_time = time.time()
    no_improve = 0

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        train_loss, train_acc = train_one_epoch(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            device=device,
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
            "Epoch [%d/%d] (%0.1fs) Loss=%.4f Acc=%.1f%% | Val Loss=%.4f CropF1=%.1f%% ImgAcc=%.1f%% ImgF1=%.1f%%",
            epoch, epochs, epoch_time, train_loss, train_acc * 100,
            val_eval["val_loss"], crop_f1 * 100, img_acc * 100, img_f1 * 100,
        )

        # Lỗi 6 sửa: lưu last_val_metrics đúng với epoch hiện tại
        last_val_metrics = val_eval

        # Lưu checkpoint tốt nhất dựa trên Image-level Macro F1
        if img_f1 > best_image_f1:
            best_image_f1 = img_f1
            best_epoch = epoch  # Lỗi 6 sửa: ghi epoch thật, không dùng epochs
            best_val_metrics = val_eval
            save_checkpoint(
                model=model,
                path=best_ckpt_path,
                epoch=epoch,
                optimizer=optimizer,
                scheduler=scheduler,
                val_metrics=val_eval,
                config=config,
            )
            no_improve = 0
            logger.info("--> Best checkpoint tại epoch %d (ImgF1=%.2f%%).", epoch, img_f1 * 100)
        else:
            no_improve += 1
            if not smoke_test and no_improve >= patience:
                logger.info("Early stopping tại epoch %d (không cải thiện %d epochs).", epoch, patience)
                break

    total_time = time.time() - start_time
    logger.info("Hoàn tất sau %.1fs! Best epoch=%d, Best ImgF1=%.2f%%", total_time, best_epoch, best_image_f1 * 100)

    # Lỗi 6 sửa: lưu last checkpoint với metrics của epoch cuối (không phải best)
    save_checkpoint(
        model=model,
        path=last_ckpt_path,
        epoch=epoch,  # epoch cuối đã chạy
        optimizer=optimizer,
        scheduler=scheduler,
        val_metrics=last_val_metrics,  # metrics thực của epoch cuối
        config=config,
    )

    # Xuất báo cáo
    report_payload = {
        "task": "W3-02 B2 Crop Classifier",
        "smoke_test": smoke_test,
        "synthetic_marker": "SYNTHETIC_SMOKE" if smoke_test else None,
        "best_epoch": best_epoch,  # Lỗi 6 sửa: epoch thật
        "total_epochs_run": epoch,
        "total_training_time_sec": round(total_time, 2),
        "config": config,
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
    logger.info("Đã xuất bảng so sánh tại: %s", val_table_path)

    return report_payload


def _config_hash(config: dict[str, Any]) -> str:
    """Hash nhanh config để ghi vào log header."""
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser(description="Huấn luyện B2 Crop Classifier (TV3 Tuần 3).")
    parser.add_argument("--config", type=str, default="configs/b2_crop_classifier.json", help="File cấu hình.")
    parser.add_argument("--smoke-test", action="store_true", help="Chạy thử nghiệm pipeline trên dữ liệu giả lập.")
    args = parser.parse_args()

    cfg_path = ROOT / args.config
    if cfg_path.exists():
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
    else:
        logger.warning("Không tìm thấy file cấu hình %s, sử dụng cấu hình mặc định.", cfg_path)
        config = {}

    if args.smoke_test:
        # Lỗi 2 sửa: tạo thư mục tạm riêng, tự dọn sau khi xong
        with tempfile.TemporaryDirectory(prefix="b2_smoke_", dir=ROOT / "outputs") as tmp_dir:
            logger.info("[SMOKE-TEST] Output tạm tại: %s", tmp_dir)
            run_training(config=config, smoke_test=True, smoke_out_dir=Path(tmp_dir))
        logger.info("[SMOKE-TEST] Đã dọn thư mục tạm. Pipeline OK!")
    else:
        run_training(config=config, smoke_test=False)


if __name__ == "__main__":
    main()
