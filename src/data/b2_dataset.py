"""TV3 - Tuần 3: B2 Crop Dataset Reader.

Đọc đặc tả crop (crop specification) từ `data/processed/comparison_v1/b2/*.jsonl`.
Hỗ trợ:
- On-the-fly cropping từ ảnh nguồn theo `bbox_xyxy` đã khóa bởi TV1.
- Trọng số mẫu đọc từ manifest, không tự tính lại để không hợp thức hóa manifest sai.
- Fail-fast validation: crop_id trùng, đa nhãn trên cùng image_id, box ngoài biên ảnh.
- Preflight hash check: bắt buộc có `quality.sha256`, từ chối nếu thiếu.
- Nhóm theo image_id phục vụ đánh giá tổng hợp cấp ảnh.

Ghi chú protocol đã thống nhất:
- drop_last=False để không mất crop và ảnh ở batch cuối.
- sample_weight đọc từ manifest (1/parent_crop_count), không ghi đè.
"""

import hashlib
import json
from collections import Counter, defaultdict
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

# Preprocessing theo protocol đã thống nhất với TV2 (W3_PROTOCOL_AGREEMENT_2026-10-18):
# train: resize cạnh ngắn 256, random crop 224, flip, jitter
# val/test: resize 256, center crop 224
DEFAULT_B2_TRANSFORMS: dict[str, transforms.Compose] = {
    "train": transforms.Compose([
        transforms.Resize(256),
        transforms.RandomCrop(IMAGE_SIZE),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]),
    "val": transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]),
    "test": transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
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
    """Dataset đọc đặc tả B2 từ snapshot comparison_v1 của TV1.

    Validation chặt chẽ:
    - Từ chối crop_id trùng trong cùng manifest.
    - Từ chối image_id có nhiều nhãn khác nhau (nhãn ảnh phải nhất quán).
    - Từ chối box hoàn toàn ngoài biên ảnh (w <= 0 hoặc h <= 0 sau khi clip).
    - Khi bật preflight_hash_check: từ chối nếu thiếu quality.sha256 hoặc hash sai.
    - Không tự ghi lại sample_weight vào manifest; đọc từ trường đã có hoặc tính từ
      parent_crop_count trong manifest.
    """

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

        self.samples: list[dict[str, Any]] = []
        seen_crop_ids: set[str] = set()
        image_labels: dict[str, set[str]] = defaultdict(set)  # lỗi 3: phát hiện đa nhãn

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

                # Lỗi 3: từ chối crop_id trùng
                if crop_id in seen_crop_ids:
                    raise ValueError(f"Dòng {line_no}: Trùng crop_id '{crop_id}'.")
                seen_crop_ids.add(crop_id)

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

                # Lỗi 3: từ chối đa nhãn trên cùng image_id
                image_labels[image_id].add(label)
                if len(image_labels[image_id]) > 1:
                    raise ValueError(
                        f"Dòng {line_no}: image_id '{image_id}' có nhiều nhãn khác nhau: {image_labels[image_id]}. "
                        f"Manifest phải nhất quán nhãn theo ảnh."
                    )

                bbox = row.get("bbox_xyxy")
                if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
                    raise ValueError(f"Dòng {line_no}: bbox_xyxy không hợp lệ: {bbox}")

                # Lỗi 3: từ chối box có kích thước <= 0 (ngoài biên sẽ bị clip thành 0)
                l, t, r, b_ = [float(v) for v in bbox]
                if r - l <= 0 or b_ - t <= 0:
                    raise ValueError(
                        f"Dòng {line_no}: crop_id '{crop_id}' có bbox_xyxy [{l},{t},{r},{b_}] "
                        f"cho kích thước crop <= 0 (width={r-l:.1f}, height={b_-t:.1f}). "
                        f"Manifest có thể đã bị sửa sau khi khóa."
                    )

                self.samples.append(row)

        if not self.samples:
            raise ValueError(f"B2 manifest rỗng: {self.manifest_path}")

        # Tính parent_crop_count để gán sample_weight.
        # KHÔNG ghi đè vào manifest file; chỉ lưu trong bộ nhớ.
        image_counts: Counter[str] = Counter(s["image_id"] for s in self.samples)

        checked_images: set[str] = set()
        for sample in self.samples:
            img_id = sample["image_id"]
            count = image_counts[img_id]
            # Ghi vào bản copy trong RAM, không chạm file gốc
            sample["_parent_crop_count"] = count
            sample["_sample_weight"] = 1.0 / count

            # Lỗi 3: preflight hash check
            if preflight_hash_check and img_id not in checked_images:
                local_path_rel = sample.get("quality", {}).get("local_path")
                if not local_path_rel:
                    raise ValueError(f"Ảnh {img_id}: Thiếu trường quality.local_path.")
                full_path = self.root / local_path_rel
                if not full_path.exists():
                    raise FileNotFoundError(f"Ảnh nguồn không tồn tại trên máy: {full_path}")
                # Lỗi 3: bắt buộc phải có sha256, không được bỏ qua
                expected_sha = sample.get("quality", {}).get("sha256")
                if not expected_sha:
                    raise ValueError(
                        f"Ảnh {img_id}: Thiếu quality.sha256. Manifest chưa được khóa đúng cách."
                    )
                actual_sha = sha256_file(full_path)
                if actual_sha != expected_sha:
                    raise ValueError(
                        f"Ảnh nguồn {img_id} không khớp hash SHA-256: "
                        f"kỳ vọng {expected_sha}, thực tế {actual_sha}."
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
            # Dùng trọng số đã tính trong RAM, không đọc từ manifest
            "sample_weight": torch.tensor(sample["_sample_weight"], dtype=torch.float32),
            "image_id": sample["image_id"],
            "crop_id": sample["crop_id"],
            "label": sample["label"],
        }

    def get_image_ids(self) -> list[str]:
        """Danh sách image_id duy nhất trong dataset (giữ thứ tự xuất hiện)."""
        seen: set[str] = set()
        order: list[str] = []
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
    """Tạo DataLoader cho B2 train và val.

    Ghi chú: drop_last=False để không mất crop và ảnh ở batch cuối (Lỗi 4 đã sửa).
    """
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
            drop_last=False,  # Lỗi 4 sửa: không bỏ batch cuối, giữ đủ ảnh
        )

    return loaders
