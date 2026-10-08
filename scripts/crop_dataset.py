"""TV3 - Tuần 2: Crop pipeline.

Đọc manifest train/val/test của TV1, tải ảnh từ URL, cắt vùng con vật theo
bounding box đã làm sạch (bbox_xywh), lưu file ảnh crop và ghi crop manifest.

Chạy:
    python scripts/crop_dataset.py --split train --out data/crops
    python scripts/crop_dataset.py --split val   --out data/crops
    python scripts/crop_dataset.py --split test  --out data/crops

Hoặc cả 3 split cùng lúc:
    python scripts/crop_dataset.py --split all   --out data/crops
"""

import argparse
import hashlib
import json
import logging
import sys
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "data" / "processed" / "v1"
DEFAULT_OUT = ROOT / "data" / "crops"
TIMEOUT = 20          # giây / request
MIN_SIDE = 8          # bỏ crop nhỏ hơn 8×8 pixel sau khi clamp
SPLITS = ["train", "val", "test"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ───────────────────────────── helpers ──────────────────────────────

def load_manifest(split: str) -> list[dict]:
    path = MANIFEST_DIR / f"{split}.jsonl"
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def fetch_image(url: str) -> bytes:
    resp = requests.get(url, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.content


def clamp_box(x: float, y: float, w: float, h: float,
              img_w: int, img_h: int) -> tuple[int, int, int, int] | None:
    """Clamp box vào kích thước ảnh thực tế, trả về (x1,y1,x2,y2) integer.

    - Bỏ qua nếu box hoàn toàn nằm ngoài ảnh.
    - Bỏ qua nếu sau clamp diện tích < MIN_SIDE×MIN_SIDE.
    - Chấp nhận tràn nhỏ (do floating-point) bằng cách clamp.
    """
    x1 = max(0, int(round(x)))
    y1 = max(0, int(round(y)))
    x2 = min(img_w, int(round(x + w)))
    y2 = min(img_h, int(round(y + h)))
    if x2 <= x1 or y2 <= y1:
        return None
    if (x2 - x1) < MIN_SIDE or (y2 - y1) < MIN_SIDE:
        return None
    return x1, y1, x2, y2


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ───────────────────────────── core logic ───────────────────────────

def process_record(record: dict, out_dir: Path, split: str, errors: list) -> list[dict]:
    """Xử lý một dòng manifest: tải ảnh, cắt từng box hợp lệ.

    Trả về danh sách các row crop manifest.
    Ghi lỗi vào `errors` (không raise để tiếp tục batch).
    """
    out_dir = out_dir.resolve()   # đảm bảo absolute path
    image_id = record["image_id"]
    url = record.get("url", "")
    label_img = record.get("label", "")   # nhãn cấp ảnh (chỉ dùng để log)
    boxes = record.get("boxes", [])       # đã làm sạch bởi TV1
    img_w = record.get("width", 0)
    img_h = record.get("height", 0)

    # ── 1. Không có box nào ──────────────────────────────────────────
    if not boxes:
        errors.append({"image_id": image_id, "split": split, "reason": "no_boxes"})
        return []

    # ── 2. Tải ảnh ───────────────────────────────────────────────────
    try:
        raw = fetch_image(url)
    except Exception as exc:
        errors.append({"image_id": image_id, "split": split,
                        "reason": "download_failed", "detail": str(exc)})
        return []

    try:
        img = Image.open(BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        errors.append({"image_id": image_id, "split": split,
                        "reason": "decode_failed", "detail": str(exc)})
        return []

    actual_w, actual_h = img.size   # kích thước thực tế từ file

    rows: list[dict] = []

    for box in boxes:
        ann_id = box.get("annotation_id", "")
        box_label = box.get("label", "")

        # ── 3. Kiểm tra nhãn box ─────────────────────────────────────
        # Nếu box không có nhãn riêng, KHÔNG được dùng nhãn cấp ảnh
        # (tránh gán nhãn sai khi ảnh có nhiều loài).
        if not box_label:
            errors.append({
                "image_id": image_id, "annotation_id": ann_id,
                "split": split, "reason": "missing_box_label",
            })
            continue

        # ── 4. Lấy tọa độ ────────────────────────────────────────────
        bbox = box.get("bbox_xywh")
        if not bbox or len(bbox) != 4:
            errors.append({
                "image_id": image_id, "annotation_id": ann_id,
                "split": split, "reason": "missing_bbox",
            })
            continue

        bx, by, bw, bh = bbox

        # ── 5. Clamp và kiểm tra kích thước ──────────────────────────
        clamped = clamp_box(bx, by, bw, bh, actual_w, actual_h)
        if clamped is None:
            errors.append({
                "image_id": image_id, "annotation_id": ann_id,
                "split": split, "reason": "invalid_box_geometry",
                "bbox_xywh": bbox, "image_size": [actual_w, actual_h],
            })
            continue

        x1, y1, x2, y2 = clamped
        crop_img = img.crop((x1, y1, x2, y2))

        # ── 6. Lưu file crop ─────────────────────────────────────────
        # Cấu trúc thư mục: <out_dir>/<split>/<label>/<image_id>_<ann_id>.jpg
        species_dir = out_dir / split / box_label
        species_dir.mkdir(parents=True, exist_ok=True)

        safe_ann = str(ann_id).replace("/", "_")
        filename = f"{image_id[:12]}_{safe_ann}.jpg"
        crop_path = species_dir / filename

        crop_buf = BytesIO()
        crop_img.save(crop_buf, format="JPEG", quality=95)
        crop_bytes = crop_buf.getvalue()
        crop_path.write_bytes(crop_bytes)

        rows.append({
            # ── truy xuất ngược ──────────────────────────────
            "crop_id": f"{image_id}_{ann_id}",
            "image_id": image_id,
            "annotation_id": ann_id,
            "split": split,                  # kế thừa từ manifest gốc
            "label": box_label,
            "class_id": None,                # được gán trong bước sau
            "source_url": url,
            "bbox_xywh_original": bbox,      # tọa độ từ manifest TV1
            "bbox_xyxy_clamped": [x1, y1, x2, y2],
            "crop_w": x2 - x1,
            "crop_h": y2 - y1,
            "image_w": actual_w,
            "image_h": actual_h,
            "file_path": crop_path.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(crop_bytes),
        })

    return rows


# ───────────────────────────── main ─────────────────────────────────

def crop_split(split: str, out_dir: Path) -> tuple[list[dict], list[dict]]:
    """Chạy crop pipeline cho một split. Trả về (rows, errors)."""
    records = load_manifest(split)
    log.info("[%s] %d ảnh trong manifest", split, len(records))

    all_rows: list[dict] = []
    all_errors: list[dict] = []

    for i, record in enumerate(records, 1):
        rows = process_record(record, out_dir, split, all_errors)
        all_rows.extend(rows)
        if i % 500 == 0 or i == len(records):
            log.info("[%s] %d/%d ảnh xử lý — %d crop lưu — %d lỗi",
                     split, i, len(records), len(all_rows), len(all_errors))

    return all_rows, all_errors


def assign_class_ids(rows: list[dict], class_map_path: Path) -> None:
    """Gán class_id vào rows theo class_map.json của TV1 (sửa in-place)."""
    class_map: dict[str, str] = json.loads(class_map_path.read_text(encoding="utf-8"))
    label_to_id = {v: int(k) for k, v in class_map.items()}
    for row in rows:
        row["class_id"] = label_to_id.get(row["label"])


def write_manifest(rows: list[dict], out_dir: Path, split: str) -> Path:
    path = out_dir / f"crop_manifest_{split}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    log.info("Đã ghi %d dòng → %s", len(rows), path)
    return path


def write_error_log(errors: list[dict], out_dir: Path, split: str) -> Path:
    path = out_dir / f"crop_errors_{split}.json"
    path.write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Đã ghi %d lỗi → %s", len(errors), path)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TV3 Tuần 2 – Crop pipeline")
    parser.add_argument("--split", choices=[*SPLITS, "all"], default="train",
                        help="Tập cần crop (mặc định: train)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="Thư mục đầu ra (mặc định: data/crops)")
    args = parser.parse_args(argv)

    splits = SPLITS if args.split == "all" else [args.split]
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    class_map_path = MANIFEST_DIR / "class_map.json"

    for split in splits:
        rows, errors = crop_split(split, out_dir)
        assign_class_ids(rows, class_map_path)
        write_manifest(rows, out_dir, split)
        write_error_log(errors, out_dir, split)

        saved = sum(1 for r in rows)
        ok = sum(1 for r in rows if r["class_id"] is not None)
        log.info("[%s] Hoàn tất: %d crop đã lưu, %d có class_id, %d lỗi",
                 split, saved, ok, len(errors))

    return 0


if __name__ == "__main__":
    sys.exit(main())
