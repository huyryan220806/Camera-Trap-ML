"""TV3 - Tuần 2: CropDataset – PyTorch Dataset và DataLoader cho ảnh crop.

Sử dụng sau khi đã chạy scripts/crop_dataset.py để tạo crop manifest.

Ví dụ nhanh:
    from src.data.crop_dataset import make_loaders, DEFAULT_TRANSFORMS

    loaders = make_loaders(
        crop_dir="data/crops",
        class_map_path="data/processed/v1/class_map.json",
        batch_size=32,
        num_workers=4,
        seed=42,
    )
    for images, labels in loaders["train"]:
        ...  # images: (B, 3, H, W) float32 tensor, labels: (B,) int64 tensor
"""

import json
import random
from pathlib import Path
from typing import Callable

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CROP_DIR = ROOT / "data" / "crops"
DEFAULT_CLASS_MAP = ROOT / "data" / "processed" / "v1" / "class_map.json"

# ───────────────────────── transforms ────────────────────────────────

# Kích thước đầu vào chuẩn của ResNet/EfficientNet
IMAGE_SIZE = 224

DEFAULT_TRANSFORMS: dict[str, transforms.Compose] = {
    "train": transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.3, contrast=0.3,
                               saturation=0.3, hue=0.05),
        transforms.RandomGrayscale(p=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ]),
    "val": transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ]),
    "test": transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ]),
}


# ───────────────────────── Dataset ────────────────────────────────────

class CropDataset(Dataset):
    """Dataset đọc ảnh crop từ crop manifest do scripts/crop_dataset.py tạo ra.

    Mỗi phần tử trả về (image_tensor, class_id).
    Bỏ qua các dòng có class_id là None (nhãn chưa được ánh xạ).
    Bỏ qua các file ảnh không tồn tại và log cảnh báo.
    """

    def __init__(
        self,
        split: str,
        crop_dir: str | Path = DEFAULT_CROP_DIR,
        class_map_path: str | Path = DEFAULT_CLASS_MAP,
        transform: Callable | None = None,
        root: str | Path = ROOT,
    ) -> None:
        self.split = split
        self.crop_dir = Path(crop_dir)
        self.root = Path(root)
        self.transform = transform or DEFAULT_TRANSFORMS.get(split, DEFAULT_TRANSFORMS["val"])

        # ── class_map ──────────────────────────────────────────────────
        raw: dict[str, str] = json.loads(Path(class_map_path).read_text(encoding="utf-8"))
        # class_map.json: {"0": "large_antlered_muntjac", ...}
        self.label_to_id: dict[str, int] = {v: int(k) for k, v in raw.items()}
        self.id_to_label: dict[int, str] = {int(k): v for k, v in raw.items()}
        self.num_classes: int = len(raw)

        # ── đọc manifest ───────────────────────────────────────────────
        manifest_path = self.crop_dir / f"crop_manifest_{split}.jsonl"
        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy crop manifest: {manifest_path}\n"
                f"Hãy chạy trước: python scripts/crop_dataset.py --split {split}"
            )

        self.samples: list[dict] = []
        skipped = 0
        with open(manifest_path, encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                if row.get("class_id") is None:
                    skipped += 1
                    continue
                file_path = self.root / row["file_path"]
                if not file_path.exists():
                    skipped += 1
                    continue
                self.samples.append({
                    "file_path": file_path,
                    "class_id": int(row["class_id"]),
                    "label": row["label"],
                    "crop_id": row.get("crop_id", ""),
                    "image_id": row.get("image_id", ""),
                    "split": row.get("split", split),
                })

        if skipped:
            import warnings
            warnings.warn(
                f"[CropDataset/{split}] Bỏ qua {skipped} dòng (thiếu class_id hoặc file không tồn tại).",
                stacklevel=2,
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        sample = self.samples[idx]
        img = Image.open(sample["file_path"]).convert("RGB")
        tensor = self.transform(img)
        return tensor, sample["class_id"]

    def class_counts(self) -> dict[str, int]:
        """Số lượng crop mỗi lớp (dùng để tính class weight nếu cần)."""
        from collections import Counter
        return dict(Counter(s["label"] for s in self.samples))


# ───────────────────────── DataLoader factory ─────────────────────────

def seed_worker(worker_id: int) -> None:
    """Đảm bảo tính tái lập của DataLoader worker."""
    worker_seed = torch.initial_seed() % 2**32
    random.seed(worker_seed)


def make_loaders(
    crop_dir: str | Path = DEFAULT_CROP_DIR,
    class_map_path: str | Path = DEFAULT_CLASS_MAP,
    batch_size: int = 32,
    num_workers: int = 0,
    seed: int = 42,
    transforms_dict: dict[str, Callable] | None = None,
    splits: list[str] | None = None,
    root: str | Path = ROOT,
) -> dict[str, DataLoader]:
    """Tạo DataLoader cho từng split.

    Args:
        crop_dir: Thư mục chứa crop manifest và ảnh crop.
        class_map_path: Đường dẫn đến class_map.json của TV1.
        batch_size: Số ảnh mỗi batch.
        num_workers: Số worker song song (0 = chạy trên main process).
        seed: Seed để tái lập (dùng chung với TV2).
        transforms_dict: Override transform cho từng split (tuỳ chọn).
        splits: Danh sách split cần tạo (mặc định: ["train", "val"]).
        root: Thư mục gốc repo.

    Returns:
        Dict {"train": DataLoader, "val": DataLoader, ...}
    """
    if splits is None:
        splits = ["train", "val"]

    tf = transforms_dict or DEFAULT_TRANSFORMS
    g = torch.Generator()
    g.manual_seed(seed)

    loaders: dict[str, DataLoader] = {}
    for split in splits:
        dataset = CropDataset(
            split=split,
            crop_dir=crop_dir,
            class_map_path=class_map_path,
            transform=tf.get(split, DEFAULT_TRANSFORMS["val"]),
            root=root,
        )
        shuffle = (split == "train")
        loaders[split] = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            worker_init_fn=seed_worker if num_workers > 0 else None,
            generator=g if shuffle else None,
            pin_memory=torch.cuda.is_available(),
            drop_last=(split == "train"),   # bỏ batch cuối nếu không đủ số
        )
        print(
            f"[{split}] {len(dataset)} crop, {len(loaders[split])} batch "
            f"(batch_size={batch_size}), classes={dataset.num_classes}"
        )

    return loaders
