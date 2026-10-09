"""Whole-image B0 data reader; split membership comes solely from TV1 manifest."""

import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from torch.utils.data import Dataset
from torchvision import transforms as T


def read_rows(path: Path, expected_split: str, class_names: list[str]) -> list[dict]:
    rows = []
    seen = set()
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("split") != expected_split:
                raise ValueError(f"{path}:{line_number} has split {row.get('split')!r}")
            class_id = row.get("class_id")
            if type(class_id) is not int or not 0 <= class_id < len(class_names):
                raise ValueError(f"{path}:{line_number} has invalid class_id")
            if row.get("label") != class_names[class_id]:
                raise ValueError(f"{path}:{line_number} has inconsistent label")
            image_id = row.get("image_id")
            if not image_id or image_id in seen:
                raise ValueError(f"{path}:{line_number} has missing/duplicate image_id")
            seen.add(image_id)
            rows.append(row)
    if not rows:
        raise ValueError(f"No {expected_split} rows in {path}")
    return rows


def image_path(image_root: Path, row: dict) -> Path:
    root = image_root.resolve()
    path = (root / row["file_name"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Image path escapes root: {row['file_name']}")
    return path


def inspect_images(rows: list[dict], image_root: Path) -> tuple[list[dict], list[dict]]:
    valid, errors = [], []
    for row in rows:
        path = image_path(image_root, row)
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                image.convert("RGB").load()
            valid.append(row)
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            errors.append({"image_id": row["image_id"], "split": row["split"], "path": str(path), "error": str(exc)})
    return valid, errors


def make_transform(config: dict, train: bool) -> T.Compose:
    size = config["data"]["image_size"]
    resize = config["data"]["resize_size"]
    operations = [T.Resize(resize)]
    if train:
        operations += [T.RandomCrop(size), T.RandomHorizontalFlip(p=0.5), T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.05)]
    else:
        operations += [T.CenterCrop(size)]
    operations += [T.ToTensor(), T.Normalize(config["preprocessing"]["mean"], config["preprocessing"]["std"])]
    return T.Compose(operations)


class FullImageDataset(Dataset):
    def __init__(self, rows: list[dict], image_root: Path, transform: T.Compose):
        self.rows = rows
        self.image_root = image_root
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        with Image.open(image_path(self.image_root, row)) as image:
            return self.transform(image.convert("RGB")), row["class_id"]
