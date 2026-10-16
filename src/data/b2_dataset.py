"""TV3 - Tuần 3: B2 Crop Dataset Reader.

Đọc trực tiếp đặc tả crop (crop specification) từ `data/processed/comparison_v1/b2/*.jsonl`.
Hỗ trợ:
- On-the-fly cropping trực tiếp từ ảnh nguồn theo `bbox_xyxy` đã khóa.
- Trọng số mẫu `sample_weight = 1.0 / parent_crop_count` để không thiên vị ảnh nhiều con vật.
- Fail-fast validation: kiểm tra split, class map, tọa độ, và file ảnh.
- Preflight hash check: đối chiếu SHA-256 ảnh nguồn theo `quality.sha256`.
- Nhóm thông tin theo `image_id` phục vụ đánh giá tổng hợp cấp ảnh (image-level aggregation).
"""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMPARISON_DIR = ROOT / "data" / "processed" / "comparison_v1"
DEFAULT_CLASS_MAP = DEFAULT_COMPARISON_DIR / "class_map.json"

IMAGE_SIZE = 224

DEFAULT_B2_TRANSFORMS: dict[str, transforms.Compose] = {
    "train": transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]),
    "val": transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]),
    "test": transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]),
}


def sha256_file(path: Path) -> str:
    """Tính hash SHA-256 của file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class B2ComparisonDataset(Dataset):
    """Dataset đọc đặc tả B2 từ snapshot comparison_v1 của TV1."""

    def __init__(
        self,
        split: str,
        manifest_path: str | Path | None = None,
        class_map_path: str | Path | None = None,
        transform: Callable | None = None,
        root: str | Path = ROOT,
        preflight_hash_check: bool = False,
    ) -> None:
        self.split = split.lower()
        if self.split not in {"train", "val", "test"}:
            raise ValueError(f"Split không hợp lệ: '{self.split}'. Chỉ chấp nhận train, val hoặc test.")

        self.root = Path(root)
        self.transform = transform or DEFAULT_B2_TRANSFORMS.get(self.split, DEFAULT_B2_TRANSFORMS["val"])

        # Đường dẫn mặc định
        if manifest_path is None:
            manifest_path = DEFAULT_COMPARISON_DIR / "b2" / f"{self.split}.jsonl"
        self.manifest_path = Path(manifest_path)

        if class_map_path is None:
            class_map_path = DEFAULT_CLASS_MAP
        self.class_map_path = Path(class_map_path)

        if not self.class_map_path.exists():
            raise FileNotFoundError(f"Không tìm thấy class_map tại: {self.class_map_path}")

        raw_map: dict[str, str] = json.loads(self.class_map_path.read_text(encoding="utf-8"))
        self.label_to_id: dict[str, int] = {v: int(k) for k, v in raw_map.items()}
        self.id_to_label: dict[int, str] = {int(k): v for k, v in raw_map.items()}
        self.num_classes: int = len(raw_map)

        if not self.manifest_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy B2 manifest: {self.manifest_path}. "
                f"Hãy đảm bảo W3-01 (scripts/freeze_comparison.py) đã được chạy thành công."
            )

        # Đọc toàn bộ manifest vào bộ nhớ đệm
        self.samples: list[dict[str, Any]] = []
        image_counts: Counter[str] = Counter()

        # Pass 1: Kiểm tra cấu trúc và đếm crop mỗi ảnh
        with open(self.manifest_path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line_str = line.strip()
                if not line_str:
                    continue
                row = json.loads(line_str)

                crop_id = row.get("crop_id")
                image_id = row.get("image_id")
                if not crop_id:
                    raise ValueError(f"Dòng {line_no}: Thiếu crop_id.")
                if not image_id:
                    raise ValueError(f"Dòng {line_no}: Thiếu image_id.")

                row_split = row.get("split")
                if row_split != self.split:
                    raise ValueError(
                        f"Dòng {line_no}: Dataset yêu cầu split '{self.split}' nhưng file ghi '{row_split}'."
                    )

                label = row.get("label")
                class_id = row.get("class_id")
                if label not in self.label_to_id:
                    raise ValueError(f"Dòng {line_no}: Nhãn '{label}' không nằm trong class_map.")
                expected_id = self.label_to_id[label]
                if class_id != expected_id:
                    raise ValueError(
                        f"Dòng {line_no}: Nhãn '{label}' có class_id kỳ vọng là {expected_id}, nhưng ghi {class_id}."
                    )

                bbox = row.get("bbox_xyxy")
                if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
                    raise ValueError(f"Dòng {line_no}: bbox_xyxy không hợp lệ: {bbox}")

                image_counts[image_id] += 1
                self.samples.append(row)

        if not self.samples:
            raise ValueError(f"B2 manifest rỗng: {self.manifest_path}")

        # Pass 2: Gán sample_weight = 1.0 / parent_crop_count
        checked_images: set[str] = set()
        for sample in self.samples:
            img_id = sample["image_id"]
            count = image_counts[img_id]
            sample["parent_crop_count"] = count
            sample["sample_weight"] = 1.0 / count

            # Kiểm tra file nguồn nếu bật preflight check
            if preflight_hash_check and img_id not in checked_images:
                local_path_rel = sample.get("quality", {}).get("local_path")
                if not local_path_rel:
                    raise ValueError(f"Ảnh {img_id}: Thiếu trường quality.local_path.")
                full_path = self.root / local_path_rel
                if not full_path.exists():
                    raise FileNotFoundError(f"Ảnh nguồn không tồn tại trên máy: {full_path}")
                expected_sha = sample.get("quality", {}).get("sha256")
                if expected_sha:
                    actual_sha = sha256_file(full_path)
                    if actual_sha != expected_sha:
                        raise ValueError(
                            f"Ảnh nguồn {img_id} không khớp hash SHA-256: kỳ vọng {expected_sha}, thực tế {actual_sha}."
                        )
                checked_images.add(img_id)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        """Cắt vùng crop từ ảnh nguồn on-the-fly và trả về tensor + nhãn + metadata."""
        sample = self.samples[idx]

        local_path_rel = sample["quality"]["local_path"]
        full_path = self.root / local_path_rel
        if not full_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file ảnh nguồn: {full_path}")

        bbox = sample["bbox_xyxy"]
        with Image.open(full_path) as source:
            crop_img = source.convert("RGB").crop(tuple(bbox))

        tensor = self.transform(crop_img)

        return {
            "image": tensor,
            "class_id": sample["class_id"],
            "sample_weight": torch.tensor(sample["sample_weight"], dtype=torch.float32),
            "image_id": sample["image_id"],
            "crop_id": sample["crop_id"],
            "label": sample["label"],
        }

    def get_image_ids(self) -> list[str]:
        """Danh sách image_id duy nhất trong dataset."""
        seen = set()
        order = []
        for s in self.samples:
            img_id = s["image_id"]
            if img_id not in seen:
                seen.add(img_id)
                order.append(img_id)
        return order

    def class_counts(self) -> dict[str, int]:
        """Thống kê số lượng crop theo nhãn."""
        return dict(Counter(s["label"] for s in self.samples))


def b2_collate_fn(batch: list[dict[str, Any]]) -> dict[str, Any]:
    """Collate function gom batch cho B2CropClassifier."""
    images = torch.stack([item["image"] for item in batch])
    class_ids = torch.tensor([item["class_id"] for item in batch], dtype=torch.long)
    sample_weights = torch.stack([item["sample_weight"] for item in batch])
    image_ids = [item["image_id"] for item in batch]
    crop_ids = [item["crop_id"] for item in batch]
    labels = [item["label"] for item in batch]

    return {
        "images": images,
        "class_ids": class_ids,
        "sample_weights": sample_weights,
        "image_ids": image_ids,
        "crop_ids": crop_ids,
        "labels": labels,
    }


def make_b2_loaders(
    comparison_dir: str | Path = DEFAULT_COMPARISON_DIR,
    batch_size: int = 32,
    num_workers: int = 0,
    seed: int = 42,
    splits: list[str] | None = None,
    root: str | Path = ROOT,
    preflight_hash_check: bool = False,
) -> dict[str, DataLoader]:
    """Tạo DataLoader cho B2 train và val."""
    if splits is None:
        splits = ["train", "val"]

    comp_dir = Path(comparison_dir)
    class_map_path = comp_dir / "class_map.json"

    g = torch.Generator()
    g.manual_seed(seed)

    loaders: dict[str, DataLoader] = {}
    for s in splits:
        manifest_path = comp_dir / "b2" / f"{s}.jsonl"
        dataset = B2ComparisonDataset(
            split=s,
            manifest_path=manifest_path,
            class_map_path=class_map_path,
            root=root,
            preflight_hash_check=preflight_hash_check,
        )
        is_train = (s == "train")
        loaders[s] = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=is_train,
            num_workers=num_workers,
            collate_fn=b2_collate_fn,
            generator=g if is_train else None,
            pin_memory=torch.cuda.is_available(),
            drop_last=is_train,
        )

    return loaders
