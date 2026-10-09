"""TV3 - Tuần 2: Crop pipeline.

Đọc manifest train/val/test của TV1, tải ảnh từ URL, cắt vùng con vật theo
bounding box đã làm sạch (bbox_xywh), lưu file ảnh crop và ghi crop manifest.

Tính năng:
- Đa luồng (Multi-threading) để tải và cắt ảnh siêu tốc.
- Tiếp tục (Resumable): Ghi trực tiếp (append) vào JSONL, chạy lại sẽ tự bỏ qua ảnh đã xử lý.
- Giới hạn (Limit): Dễ dàng giới hạn số lượng ảnh chạy thử.

Chạy:
    python scripts/crop_dataset.py --split train --out data/crops --limit 4000 --workers 16
"""

import argparse
import hashlib
import json
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import Optional

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
              img_w: int, img_h: int) -> Optional[tuple[int, int, int, int]]:
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

def process_record(record: dict, out_dir: Path, split: str, class_map: dict[str, int]) -> tuple[list[dict], list[dict]]:
    """Xử lý một dòng manifest: tải ảnh, cắt từng box hợp lệ."""
    out_dir = out_dir.resolve()
    image_id = record["image_id"]
    url = record.get("url", "")
    boxes = record.get("boxes", [])
    
    rows: list[dict] = []
    errors: list[dict] = []

    if not boxes:
        errors.append({"image_id": image_id, "split": split, "reason": "no_boxes"})
        return rows, errors

    try:
        raw = fetch_image(url)
    except Exception as exc:
        errors.append({"image_id": image_id, "split": split,
                        "reason": "download_failed", "detail": str(exc)})
        return rows, errors

    try:
        img = Image.open(BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        errors.append({"image_id": image_id, "split": split,
                        "reason": "decode_failed", "detail": str(exc)})
        return rows, errors

    actual_w, actual_h = img.size

    for box in boxes:
        ann_id = box.get("annotation_id", "")
        box_label = box.get("label", "")

        if not box_label:
            errors.append({
                "image_id": image_id, "annotation_id": ann_id,
                "split": split, "reason": "missing_box_label",
            })
            continue

        bbox = box.get("bbox_xywh")
        if not bbox or len(bbox) != 4:
            errors.append({
                "image_id": image_id, "annotation_id": ann_id,
                "split": split, "reason": "missing_bbox",
            })
            continue

        bx, by, bw, bh = bbox
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
            "crop_id": f"{image_id}_{ann_id}",
            "image_id": image_id,
            "annotation_id": ann_id,
            "split": split,
            "label": box_label,
            "class_id": class_map.get(box_label),
            "source_url": url,
            "bbox_xywh_original": bbox,
            "bbox_xyxy_clamped": [x1, y1, x2, y2],
            "crop_w": x2 - x1,
            "crop_h": y2 - y1,
            "image_w": actual_w,
            "image_h": actual_h,
            "file_path": crop_path.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(crop_bytes),
        })

    return rows, errors


# ───────────────────────────── runner ────────────────────────────────

def get_processed_ids(manifest_path: Path, error_path: Path) -> set[str]:
    """Đọc manifest và error log để tìm các ảnh đã xử lý thành công hoặc thất bại."""
    processed = set()
    for path in (manifest_path, error_path):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            processed.add(json.loads(line)["image_id"])
                        except Exception:
                            pass
    return processed


def append_jsonl(path: Path, items: list[dict], lock: threading.Lock) -> None:
    if not items:
        return
    with lock:
        with open(path, "a", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")


def crop_split_multithread(split: str, out_dir: Path, limit: int, workers: int) -> None:
    manifest_path = out_dir / f"crop_manifest_{split}.jsonl"
    error_path = out_dir / f"crop_errors_{split}.jsonl"  # Đổi sang jsonl để append
    
    # 1. Quét file cũ để chạy tiếp (resume)
    processed_ids = get_processed_ids(manifest_path, error_path)
    
    class_map: dict[str, str] = json.loads((MANIFEST_DIR / "class_map.json").read_text(encoding="utf-8"))
    label_to_id = {v: int(k) for k, v in class_map.items()}
    
    records = load_manifest(split)
    target_records = []
    
    # 2. Lọc ảnh chưa làm và áp dụng giới hạn
    for r in records:
        if r["image_id"] not in processed_ids:
            target_records.append(r)
        if limit > 0 and len(target_records) >= limit:
            break
            
    log.info("[%s] %d ảnh trong manifest gốc, đã xong %d, còn cần chạy %d ảnh", 
             split, len(records), len(processed_ids), len(target_records))
             
    if not target_records:
        log.info("[%s] Không còn ảnh nào cần xử lý.", split)
        return

    lock = threading.Lock()
    done = 0
    total_crops = 0
    total_errors = 0
    
    def process_and_save(record: dict):
        rows, errors = process_record(record, out_dir, split, label_to_id)
        append_jsonl(manifest_path, rows, lock)
        append_jsonl(error_path, errors, lock)
        return len(rows), len(errors)

    log.info("[%s] Bắt đầu chạy với %d luồng...", split, workers)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_and_save, r): r for r in target_records}
        for future in as_completed(futures):
            c_rows, c_errs = future.result()
            
            with lock:
                done += 1
                total_crops += c_rows
                total_errors += c_errs
                if done % 100 == 0 or done == len(target_records):
                    log.info("[%s] Tiến độ: %d/%d ảnh (%d crops mới, %d lỗi mới)", 
                             split, done, len(target_records), total_crops, total_errors)
                             
    log.info("[%s] Hoàn tất đợt chạy: thêm %d crops, %d lỗi.", split, total_crops, total_errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TV3 Tuần 2 – Crop pipeline (Đa luồng & Lưu tiếp tục)")
    parser.add_argument("--split", choices=[*SPLITS, "all"], default="train",
                        help="Tập cần crop (mặc định: train)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="Thư mục đầu ra (mặc định: data/crops)")
    parser.add_argument("--limit", type=int, default=0,
                        help="Giới hạn số ảnh xử lý (mặc định 0 = làm hết)")
    parser.add_argument("--workers", type=int, default=16,
                        help="Số luồng tải song song (mặc định 16)")
    args = parser.parse_args(argv)

    splits = SPLITS if args.split == "all" else [args.split]
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    for split in splits:
        crop_split_multithread(split, out_dir, args.limit, args.workers)

    return 0


if __name__ == "__main__":
    sys.exit(main())
