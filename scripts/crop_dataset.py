"""TV3 - Tuần 2: Crop pipeline.

Đọc manifest train/val/test của TV1, tải ảnh từ URL (hoặc đọc file local), cắt vùng con vật.
Tính năng:
- Đa luồng (Multi-threading)
- Tiếp tục (Resumable): Kiểm tra tính nguyên vẹn (file tồn tại, hash khớp) trước khi bỏ qua.
- Hỗ trợ chạy trên máy mới: Tự động phát hiện thiếu file và tải lại/cắt lại.
- Fix giới hạn (--limit): Cố định tập đích, chạy bao nhiêu lần cũng không làm phình to dữ liệu.
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
# Cố gắng dùng v2 (pilot v2 của TV1), fallback v1 nếu chưa có.
MANIFEST_V2_DIR = ROOT / "data" / "processed" / "v2"
MANIFEST_V1_DIR = ROOT / "data" / "processed" / "v1"
DEFAULT_OUT = ROOT / "data" / "crops"
TIMEOUT = 20
MIN_SIDE = 8
SPLITS = ["train", "val", "test"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

def load_manifest(split: str) -> list[dict]:
    # Ưu tiên v2
    if (MANIFEST_V2_DIR / f"{split}.jsonl").exists():
        path = MANIFEST_V2_DIR / f"{split}.jsonl"
    else:
        path = MANIFEST_V1_DIR / f"{split}.jsonl"
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def clamp_box(x: float, y: float, w: float, h: float, img_w: int, img_h: int) -> Optional[tuple[int, int, int, int]]:
    x1, y1 = max(0, int(round(x))), max(0, int(round(y)))
    x2, y2 = min(img_w, int(round(x + w))), min(img_h, int(round(y + h)))
    if x2 <= x1 or y2 <= y1 or (x2 - x1) < MIN_SIDE or (y2 - y1) < MIN_SIDE:
        return None
    return x1, y1, x2, y2

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def process_record(record: dict, out_dir: Path, split: str, class_map: dict[str, int]) -> tuple[list[dict], list[dict]]:
    out_dir = out_dir.resolve()
    image_id = record["image_id"]
    url = record.get("url", "")
    boxes = record.get("boxes", [])
    rows, errors = [], []

    if not boxes:
        errors.append({"image_id": image_id, "split": split, "reason": "no_boxes"})
        return rows, errors

    # Cố gắng đọc từ local_path (nếu TV1 đã tải) hoặc tải từ mạng
    raw = None
    local_path = record.get("quality", {}).get("local_path")
    if local_path and (ROOT / local_path).is_file():
        try:
            raw = (ROOT / local_path).read_bytes()
        except Exception:
            pass

    if not raw:
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            raw = resp.content
        except Exception as exc:
            errors.append({"image_id": image_id, "split": split, "reason": "download_failed", "detail": str(exc)})
            return rows, errors

    try:
        img = Image.open(BytesIO(raw)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        errors.append({"image_id": image_id, "split": split, "reason": "decode_failed", "detail": str(exc)})
        return rows, errors

    actual_w, actual_h = img.size

    for box in boxes:
        ann_id = box.get("annotation_id", "")
        box_label = box.get("label", "")

        if not box_label:
            errors.append({"image_id": image_id, "annotation_id": ann_id, "split": split, "reason": "missing_box_label"})
            continue

        bbox = box.get("bbox_xywh")
        if not bbox or len(bbox) != 4:
            errors.append({"image_id": image_id, "annotation_id": ann_id, "split": split, "reason": "missing_bbox"})
            continue

        clamped = clamp_box(*bbox, actual_w, actual_h)
        if not clamped:
            errors.append({"image_id": image_id, "annotation_id": ann_id, "split": split, "reason": "invalid_box_geometry", "bbox_xywh": bbox})
            continue

        x1, y1, x2, y2 = clamped
        crop_img = img.crop((x1, y1, x2, y2))
        
        species_dir = out_dir / split / box_label
        species_dir.mkdir(parents=True, exist_ok=True)
        crop_path = species_dir / f"{image_id[:12]}_{str(ann_id).replace('/', '_')}.jpg"

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

def check_completed(image_id: str, manifest_entries: list[dict], root: Path) -> bool:
    """Kiểm tra xem các crop của một ảnh đã được xử lý xong và file vẫn còn nguyên vẹn chưa."""
    for row in manifest_entries:
        path = root / row["file_path"]
        if not path.is_file():
            return False
        # Xác minh độ toàn vẹn hash
        if sha256_bytes(path.read_bytes()) != row["sha256"]:
            return False
    return True

def crop_split_multithread(split: str, out_dir: Path, limit: int, workers: int) -> None:
    manifest_path = out_dir / f"crop_manifest_{split}.jsonl"
    error_path = out_dir / f"crop_errors_{split}.jsonl"
    
    # Gom nhóm kết quả đã xử lý theo image_id
    existing_success: dict[str, list[dict]] = {}
    existing_fatal: set[str] = set()

    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    r = json.loads(line)
                    existing_success.setdefault(r["image_id"], []).append(r)
                except Exception: pass
                
    if error_path.exists():
        with open(error_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    e = json.loads(line)
                    # Chỉ bỏ qua nếu là lỗi cố định, còn lỗi tải (download_failed) thì phải thử lại
                    if e.get("reason") not in ["download_failed"]:
                        existing_fatal.add(e["image_id"])
                except Exception: pass

    # Tải class map (ưu tiên v2)
    cmap_path = MANIFEST_V2_DIR / "class_map.json" if (MANIFEST_V2_DIR / "class_map.json").exists() else MANIFEST_V1_DIR / "class_map.json"
    class_map: dict[str, str] = json.loads(cmap_path.read_text(encoding="utf-8"))
    label_to_id = {v: int(k) for k, v in class_map.items()}
    
    # CHỐT TẬP ĐÍCH (limit TRƯỚC khi lọc cache)
    records = load_manifest(split)
    target_records = records[:limit] if limit > 0 else records
    
    pending_records = []
    for r in target_records:
        iid = r["image_id"]
        if iid in existing_fatal:
            continue  # Lỗi không thể cứu (VD: sai geometry)
        if iid in existing_success:
            if check_completed(iid, existing_success[iid], ROOT):
                continue  # Đã hoàn tất và ảnh còn nguyên
        pending_records.append(r)
            
    log.info("[%s] %d ảnh trong target list. %d đã hoàn tất, cần chạy %d ảnh", 
             split, len(target_records), len(target_records) - len(pending_records), len(pending_records))
             
    if not pending_records:
        return

    lock = threading.Lock()
    done, total_crops, total_errors = 0, 0, 0
    
    def process_and_save(record: dict):
        rows, errors = process_record(record, out_dir, split, label_to_id)
        if rows:
            with lock:
                with open(manifest_path, "a", encoding="utf-8") as f:
                    for row in rows: f.write(json.dumps(row, ensure_ascii=False) + "\n")
        if errors:
            with lock:
                with open(error_path, "a", encoding="utf-8") as f:
                    for err in errors: f.write(json.dumps(err, ensure_ascii=False) + "\n")
        return len(rows), len(errors)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_and_save, r): r for r in pending_records}
        for future in as_completed(futures):
            c_rows, c_errs = future.result()
            with lock:
                done += 1
                total_crops += c_rows
                total_errors += c_errs
                if done % 100 == 0 or done == len(pending_records):
                    log.info("[%s] Tiến độ: %d/%d (%d crops mới, %d lỗi mới)", split, done, len(pending_records), total_crops, total_errors)
                             
    log.info("[%s] Hoàn tất đợt chạy.", split)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=[*SPLITS, "all"], default="train")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args(argv)

    splits = SPLITS if args.split == "all" else [args.split]
    args.out.mkdir(parents=True, exist_ok=True)

    for s in splits:
        crop_split_multithread(s, args.out, args.limit, args.workers)
    return 0

if __name__ == "__main__":
    sys.exit(main())
