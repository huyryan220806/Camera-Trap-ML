"""TV3 - Tuần 2: CropDataset – PyTorch Dataset và DataLoader cho ảnh crop.

Fail-fast:
- Trả về lỗi ValueError nếu nhãn không khớp, id không tồn tại, hoặc sai split.
"""

import json
import random
import hashlib
from pathlib import Path
from typing import Callable

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CROP_DIR = ROOT / "data" / "crops"
DEFAULT_CLASS_MAP = ROOT / "data" / "processed" / "v1" / "class_map.json"

IMAGE_SIZE = 224

DEFAULT_TRANSFORMS: dict[str, transforms.Compose] = {
    "train": transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3, hue=0.05),
        transforms.RandomGrayscale(p=0.05),
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

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

class CropDataset(Dataset):
    def __init__(
        self,
        split: str,
        crop_dir: str | Path = DEFAULT_CROP_DIR,
        class_map_path: str | Path = DEFAULT_CLASS_MAP,
        transform: Callable | None = None,
        root: str | Path = ROOT,
        preflight_hash_check: bool = False
    ) -> None:
        self.split = split
        self.crop_dir = Path(crop_dir)
        self.root = Path(root)
        self.transform = transform or DEFAULT_TRANSFORMS.get(split, DEFAULT_TRANSFORMS["val"])

        if not Path(class_map_path).exists():
            # Thử tự động sang v2 nếu dùng mặc định
            v2_path = self.root / "data" / "processed" / "v2" / "class_map.json"
            if Path(class_map_path) == DEFAULT_CLASS_MAP and v2_path.exists():
                class_map_path = v2_path

        raw: dict[str, str] = json.loads(Path(class_map_path).read_text(encoding="utf-8"))
        self.label_to_id: dict[str, int] = {v: int(k) for k, v in raw.items()}
        self.num_classes: int = len(raw)

        manifest_path = self.crop_dir / f"crop_manifest_{split}.jsonl"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Không tìm thấy crop manifest: {manifest_path}")

        self.samples: list[dict] = []
        seen_ids = set()

        with open(manifest_path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                row = json.loads(line)
                
                # Validation cực kỳ nghiêm ngặt theo yêu cầu của Reviewer
                crop_id = row.get("crop_id")
                if not crop_id:
                    raise ValueError(f"Dòng {line_no}: Thiếu crop_id.")
                if crop_id in seen_ids:
                    raise ValueError(f"Dòng {line_no}: Trùng lặp crop_id '{crop_id}'.")
                seen_ids.add(crop_id)

                row_split = row.get("split")
                if row_split != self.split:
                    raise ValueError(f"Dòng {line_no}: Yêu cầu split '{self.split}' nhưng dòng này lại ghi split '{row_split}'.")

                row_label = row.get("label")
                row_class_id = row.get("class_id")
                
                if row_label not in self.label_to_id:
                    raise ValueError(f"Dòng {line_no}: Nhãn '{row_label}' không tồn tại trong class_map.")
                
                expected_id = self.label_to_id[row_label]
                if row_class_id != expected_id:
                    raise ValueError(f"Dòng {line_no}: Nhãn '{row_label}' yêu cầu class_id {expected_id}, nhưng dữ liệu lại ghi {row_class_id}.")

                file_path = self.root / row["file_path"]
                if not file_path.exists():
                    raise FileNotFoundError(f"Dòng {line_no}: Không tìm thấy file ảnh crop: {file_path}")

                if preflight_hash_check:
                    actual_hash = sha256_bytes(file_path.read_bytes())
                    if actual_hash != row.get("sha256"):
                        raise ValueError(f"Dòng {line_no}: Mã hash không khớp cho file {file_path}.")

                self.samples.append({
                    "file_path": file_path,
                    "class_id": expected_id,
                    "label": row_label,
                    "crop_id": crop_id,
                    "image_id": row.get("image_id", ""),
                    "split": row_split,
                })

        if not self.samples:
            raise ValueError(f"Dataset {split} trống.")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        sample = self.samples[idx]
        img = Image.open(sample["file_path"]).convert("RGB")
        tensor = self.transform(img)
        return tensor, sample["class_id"]

    def class_counts(self) -> dict[str, int]:
        from collections import Counter
        return dict(Counter(s["label"] for s in self.samples))

def seed_worker(worker_id: int) -> None:
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
    preflight_hash_check: bool = False
) -> dict[str, DataLoader]:
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
            preflight_hash_check=preflight_hash_check
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
            drop_last=(split == "train"),
        )

    return loaders
