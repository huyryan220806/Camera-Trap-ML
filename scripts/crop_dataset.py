"""TV3 - Tuần 2: Crop pipeline.

Đọc manifest train/val/test của TV1, tải ảnh từ URL (hoặc đọc file local), cắt vùng con vật.

Tính năng:
- Đa luồng (Multi-threading)
- Resumable chặt chẽ: Kiểm tra từng box (annotation_id), không skip khi box chưa đủ.
- Writer an toàn: Upsert sau mỗi ảnh, không gom vào RAM chờ cuối đợt.
- JSONL recovery: Phục hồi file bị cắt ngay khi load, kể cả khi pending=0.
- Chốt run: Lưu fingerprint vào run_meta_<split>.json, fail-closed nếu có artifact
  mà thiếu metadata.
- Kiểm tra SHA-256 ảnh nguồn cho cả local lẫn HTTP.

Chạy lần đầu (tập train, giới hạn 4000 ảnh đầu manifest):
    python scripts/crop_dataset.py --split train --out data/crops/v1_run01 --manifest-version v1 --limit 4000

Chạy tiếp tục sau gián đoạn (cùng lệnh, code tự detect):
    python scripts/crop_dataset.py --split train --out data/crops/v1_run01 --manifest-version v1 --limit 4000

Khi TV1 đã merge v2:
    python scripts/crop_dataset.py --split train --out data/crops/v2_run01 --manifest-version v2 --limit 4000
"""

import argparse
import hashlib
import json
import logging
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_V2_DIR = ROOT / "data" / "processed" / "v2"
MANIFEST_V1_DIR = ROOT / "data" / "processed" / "v1"
DEFAULT_OUT = ROOT / "data" / "crops" / "v1_run01"
TIMEOUT = 20
MIN_SIDE = 8
SPLITS = ["train", "val", "test"]
# Lỗi per-box không retry (vấn đề data, không phải mạng/disk)
BOX_FATAL_REASONS = {"invalid_box_geometry", "missing_box_label", "missing_bbox"}
# Lỗi per-image có thể retry
IMAGE_RETRYABLE_REASONS = {"download_failed", "decode_failed", "source_hash_mismatch"}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


# ──────────────────────── helpers ───────────────────────────────────

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_jsonl(path: Path) -> str:
    """Hash toàn bộ file manifest để phát hiện thay đổi nguồn."""
    return sha256_file(path) if path.exists() else ""


def clamp_box(x: float, y: float, w: float, h: float,
              img_w: int, img_h: int) -> Optional[tuple[int, int, int, int]]:
    x1, y1 = max(0, int(round(x))), max(0, int(round(y)))
    x2, y2 = min(img_w, int(round(x + w))), min(img_h, int(round(y + h)))
    if x2 <= x1 or y2 <= y1 or (x2 - x1) < MIN_SIDE or (y2 - y1) < MIN_SIDE:
        return None
    return x1, y1, x2, y2


# ──────────────────────── JSONL đọc/ghi an toàn ─────────────────────

def load_jsonl_safe(path: Path) -> list[dict]:
    """Đọc JSONL, phục hồi dòng cuối bị cắt. Lỗi ở giữa file → raise."""
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    truncated = False
    for i, line in enumerate(raw_lines):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError:
            if i < len(raw_lines) - 1:
                # Lỗi ở giữa file → không chấp nhận, dừng ngay
                raise ValueError(
                    f"Dòng JSON lỗi ở giữa file {path} dòng {i + 1}. "
                    "File có thể bị hỏng, cần kiểm tra thủ công."
                )
            else:
                log.warning("Dòng cuối bị cắt trong %s, bỏ qua (do gián đoạn trước đó).", path)
                truncated = True
    return rows


def repair_jsonl_if_needed(path: Path) -> list[dict]:
    """Đọc JSONL, nếu phát hiện dòng bị cắt thì GHI LẠI file sạch ngay lập tức.

    Mục 4 fix: Đảm bảo file trên đĩa luôn hợp lệ cho CropDataset, kể cả khi
    pending=0 và runner return sớm.
    """
    if not path.exists():
        return []
    rows = []
    need_repair = False
    with path.open("r", encoding="utf-8") as f:
        raw_lines = f.readlines()
    for i, line in enumerate(raw_lines):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError:
            if i < len(raw_lines) - 1:
                raise ValueError(
                    f"Dòng JSON lỗi ở giữa file {path} dòng {i + 1}. "
                    "File có thể bị hỏng, cần kiểm tra thủ công."
                )
            else:
                log.warning("Dòng cuối bị cắt trong %s, sửa và ghi lại file ngay.", path)
                need_repair = True
    if need_repair:
        atomic_rewrite_jsonl(path, rows)
        log.info("Đã phục hồi %s: %d dòng hợp lệ.", path.name, len(rows))
    return rows


def atomic_rewrite_jsonl(path: Path, rows: list[dict]) -> None:
    """Ghi lại toàn bộ file JSONL một cách atomic (ghi sang file tạm rồi rename)."""
    tmp = path.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        shutil.move(str(tmp), str(path))
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


# ──────────────────────── run fingerprint ───────────────────────────

def build_fingerprint(manifest_path: Path, class_map_path: Path,
                       limit: int, split: str, manifest_version: str) -> dict:
    return {
        "manifest_version": manifest_version,
        "split": split,
        "limit": limit,
        "manifest_sha256": sha256_jsonl(manifest_path),
        "class_map_sha256": sha256_jsonl(class_map_path),
    }


def load_or_create_run_meta(out_dir: Path, fingerprint: dict,
                             manifest_path: Path, error_path: Path) -> None:
    """Đảm bảo run meta nhất quán.

    Mục 2 fix: Nếu output có artifact nhưng thiếu metadata → fail-closed.
    """
    split = fingerprint.get("split", "unknown")
    meta_path = out_dir / f"run_meta_{split}.json"
    if meta_path.exists():
        saved = json.loads(meta_path.read_text(encoding="utf-8"))
        for key in ("manifest_version", "split", "limit", "manifest_sha256", "class_map_sha256"):
            if saved.get(key) != fingerprint.get(key):
                raise ValueError(
                    f"Fingerprint không khớp cho key '{key}': "
                    f"saved={saved.get(key)!r}, current={fingerprint.get(key)!r}.\n"
                    f"Dùng --out khác để tạo run mới, hoặc xóa {meta_path} nếu muốn reset."
                )
        log.info("Fingerprint khớp, tiếp tục run cũ.")
    else:
        # Fail-closed: nếu đã có manifest/error nhưng thiếu meta → chặn
        has_existing = manifest_path.exists() or error_path.exists()
        if has_existing:
            raise ValueError(
                f"Thư mục {out_dir} đã có artifact cho split '{split}' "
                f"({manifest_path.name} hoặc {error_path.name}) "
                f"nhưng thiếu file {meta_path.name}.\n"
                f"Không thể xác minh nguồn dữ liệu. Dùng --out mới hoặc "
                f"tạo {meta_path.name} thủ công nếu chắc chắn nguồn đúng."
            )
        meta_path.write_text(json.dumps(fingerprint, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        log.info("Tạo run mới, đã lưu fingerprint.")


# ──────────────────────── process_record ────────────────────────────

def load_source_image(record: dict) -> tuple[Optional[bytes], str]:
    """Tải ảnh từ local_path (TV1) hoặc URL. Trả về (bytes, nguồn).

    Mục 3 fix: Kiểm tra SHA-256 cho CẢ local lẫn HTTP.
    """
    quality = record.get("quality", {})
    expected_sha = quality.get("sha256")
    local_path = quality.get("local_path")

    raw = None
    source = ""

    # Thử đọc local trước
    if local_path:
        p = ROOT / local_path
        if p.is_file():
            raw = p.read_bytes()
            source = "local"

    # Fallback sang HTTP
    if raw is None:
        url = record.get("url", "")
        if not url:
            return None, "no_url"
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            raw = resp.content
            source = "network"
        except Exception as exc:
            return None, f"download_failed:{exc}"

    # Kiểm tra SHA-256 thống nhất cho cả 2 nhánh
    if expected_sha and sha256_bytes(raw) != expected_sha:
        return None, "source_hash_mismatch"

    return raw, source


def process_record(record: dict, out_dir: Path, split: str,
                   class_map: dict[str, int]) -> tuple[list[dict], list[dict]]:
    """Xử lý một dòng manifest. Trả về (crops, errors), mỗi cái là list dict."""
    out_dir = out_dir.resolve()
    image_id = record["image_id"]
    boxes = record.get("boxes", [])
    rows, errors = [], []

    if not boxes:
        errors.append({"image_id": image_id, "split": split, "reason": "no_boxes"})
        return rows, errors

    raw, source = load_source_image(record)
    if raw is None:
        reason = source if source in IMAGE_RETRYABLE_REASONS else source.split(":")[0]
        if reason == "source_hash_mismatch":
            errors.append({"image_id": image_id, "split": split,
                           "reason": "source_hash_mismatch",
                           "detail": "SHA-256 ảnh nguồn không khớp metadata TV1"})
        else:
            errors.append({"image_id": image_id, "split": split,
                           "reason": "download_failed", "detail": source})
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
        crop_id = f"{image_id}_{ann_id}"

        if not box_label:
            errors.append({"image_id": image_id, "annotation_id": ann_id,
                           "crop_id": crop_id, "split": split,
                           "reason": "missing_box_label"})
            continue

        bbox = box.get("bbox_xywh")
        if not bbox or len(bbox) != 4:
            errors.append({"image_id": image_id, "annotation_id": ann_id,
                           "crop_id": crop_id, "split": split, "reason": "missing_bbox"})
            continue

        clamped = clamp_box(*bbox, actual_w, actual_h)
        if not clamped:
            errors.append({"image_id": image_id, "annotation_id": ann_id,
                           "crop_id": crop_id, "split": split,
                           "reason": "invalid_box_geometry", "bbox_xywh": bbox})
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
            "crop_id": crop_id,
            "image_id": image_id,
            "annotation_id": ann_id,
            "split": split,
            "label": box_label,
            "class_id": class_map.get(box_label),
            "source_url": record.get("url", ""),
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


# ──────────────────────── completion check theo box ─────────────────

def get_box_ids_from_record(record: dict) -> set[str]:
    """Tập annotation_id của ảnh (không tính box geometry lỗi vì chưa biết)."""
    return {f"{record['image_id']}_{b.get('annotation_id', '')}"
            for b in record.get("boxes", [])}


def check_completed_per_box(record: dict,
                             done_crops: dict[str, dict],
                             fatal_box_ids: set[str],
                             root: Path) -> bool:
    """
    Kiểm tra hoàn tất theo từng box (annotation_id), không phải theo ảnh.
    - Mỗi box phải hoặc có crop hợp lệ (file tồn tại + hash khớp), hoặc có lỗi vĩnh viễn.
    - Nếu còn box chưa giải quyết → chưa xong.
    """
    boxes = record.get("boxes", [])
    if not boxes:
        return True  # no_boxes được ghi vào error log, coi là xong

    image_id = record["image_id"]
    for box in boxes:
        ann_id = box.get("annotation_id", "")
        crop_id = f"{image_id}_{ann_id}"

        if crop_id in fatal_box_ids:
            continue  # box này lỗi vĩnh viễn, bỏ qua

        if crop_id not in done_crops:
            return False  # box chưa được xử lý

        row = done_crops[crop_id]
        path = root / row["file_path"]
        if not path.is_file():
            return False  # file bị mất
        if sha256_bytes(path.read_bytes()) != row["sha256"]:
            return False  # file bị hỏng
    return True


# ──────────────────────── writer: upsert không trùng ────────────────

def upsert_rows(existing_rows: list[dict], new_rows: list[dict]) -> list[dict]:
    """Thay thế dòng cũ theo crop_id thay vì append blindly. Trả về danh sách dedup."""
    by_id: dict[str, dict] = {r["crop_id"]: r for r in existing_rows}
    for r in new_rows:
        by_id[r["crop_id"]] = r  # ghi đè nếu đã có
    return list(by_id.values())


def upsert_errors(existing_errors: list[dict], new_errors: list[dict]) -> list[dict]:
    """Dedup error log theo (image_id, annotation_id, reason)."""
    def key(e):
        return (e.get("image_id", ""), e.get("annotation_id", ""), e.get("reason", ""))
    by_key: dict[tuple, dict] = {key(e): e for e in existing_errors}
    for e in new_errors:
        by_key[key(e)] = e
    return list(by_key.values())


# ──────────────────────── main runner ───────────────────────────────

def crop_split_multithread(split: str, out_dir: Path, limit: int,
                           workers: int, manifest_version: str) -> None:
    out_dir = out_dir.resolve()
    manifest_path = out_dir / f"crop_manifest_{split}.jsonl"
    error_path = out_dir / f"crop_errors_{split}.jsonl"

    # Chọn manifest source theo --manifest-version (KHÔNG auto-fallback)
    if manifest_version == "v2":
        source_dir = MANIFEST_V2_DIR
        if not (source_dir / f"{split}.jsonl").exists():
            raise FileNotFoundError(
                f"--manifest-version v2 được yêu cầu nhưng {source_dir / split}.jsonl chưa tồn tại. "
                "Hãy chờ TV1 merge hoặc dùng --manifest-version v1."
            )
    else:
        source_dir = MANIFEST_V1_DIR

    cmap_path = (source_dir / "class_map.json" if (source_dir / "class_map.json").exists()
                 else MANIFEST_V1_DIR / "class_map.json")
    class_map_raw: dict[str, str] = json.loads(cmap_path.read_text(encoding="utf-8"))
    label_to_id = {v: int(k) for k, v in class_map_raw.items()}

    src_manifest = source_dir / f"{split}.jsonl"
    all_records = [json.loads(l) for l in src_manifest.open(encoding="utf-8") if l.strip()]

    # CHỐT TẬP ĐÍCH trước khi lọc cache
    target_records = all_records[:limit] if limit > 0 else all_records

    # Kiểm tra fingerprint, từ chối nếu đổi nguồn mà không đổi --out
    # Mục 2 fix: truyền manifest_path/error_path để fail-closed khi thiếu meta
    fp = build_fingerprint(src_manifest, cmap_path, limit, split, manifest_version)
    load_or_create_run_meta(out_dir, fp, manifest_path, error_path)

    # Mục 4 fix: Phục hồi JSONL bị cắt NGAY LÚC NÀY (trước khi check pending),
    # đảm bảo file trên đĩa luôn sạch cho CropDataset dù có return sớm hay không.
    existing_rows = repair_jsonl_if_needed(manifest_path)
    existing_errors = repair_jsonl_if_needed(error_path)

    # Index các kết quả cũ
    done_crops: dict[str, dict] = {r["crop_id"]: r for r in existing_rows}
    # Box bị lỗi vĩnh viễn (chỉ lỗi PER-BOX, không bao gồm lỗi per-image)
    fatal_box_ids: set[str] = {
        e.get("crop_id", "")
        for e in existing_errors
        if e.get("reason") in BOX_FATAL_REASONS and e.get("crop_id")
    }

    # Lọc ảnh cần xử lý (check per-box)
    pending_records = [
        r for r in target_records
        if not check_completed_per_box(r, done_crops, fatal_box_ids, ROOT)
    ]

    log.info("[%s] target=%d, đã xong=%d, cần chạy=%d",
             split, len(target_records),
             len(target_records) - len(pending_records), len(pending_records))

    if not pending_records:
        log.info("[%s] Không còn gì cần làm.", split)
        return

    # Mục 1 fix: Persist sau MỖI ẢNH thay vì gom hết vào RAM chờ cuối đợt.
    # Dùng lock bảo vệ đọc-upsert-ghi để tránh race condition giữa các thread.
    lock = threading.Lock()
    done = 0
    total_new_crops = 0
    total_new_errors = 0

    def process_and_persist(record: dict):
        """Xử lý 1 ảnh rồi upsert + atomic rewrite NGAY LẬP TỨC."""
        rows, errors = process_record(record, out_dir, split, label_to_id)
        if rows or errors:
            with lock:
                # Đọc lại file hiện tại, upsert, ghi lại
                cur_rows = load_jsonl_safe(manifest_path)
                cur_errors = load_jsonl_safe(error_path)
                if rows:
                    merged_rows = upsert_rows(cur_rows, rows)
                    atomic_rewrite_jsonl(manifest_path, merged_rows)
                if errors:
                    merged_errors = upsert_errors(cur_errors, errors)
                    atomic_rewrite_jsonl(error_path, merged_errors)
        return len(rows), len(errors)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_and_persist, r): r for r in pending_records}
        for future in as_completed(futures):
            c_rows, c_errs = future.result()
            with lock:
                done += 1
                total_new_crops += c_rows
                total_new_errors += c_errs
                if done % 50 == 0 or done == len(pending_records):
                    log.info("[%s] %d/%d ảnh, +%d crops, +%d lỗi",
                             split, done, len(pending_records),
                             total_new_crops, total_new_errors)

    # Đọc lại manifest cuối cùng để báo cáo chính xác
    final_rows = load_jsonl_safe(manifest_path)
    final_errors = load_jsonl_safe(error_path)
    log.info("[%s] Hoàn tất: %d crops tổng, %d lỗi tổng.",
             split, len(final_rows), len(final_errors))


# ──────────────────────── CLI ────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="TV3 Tuần 2 – Crop pipeline (resumable, atomic, fingerprinted)"
    )
    parser.add_argument("--split", choices=[*SPLITS, "all"], default="train")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT,
                        help="Thư mục output của run này. Dùng tên khác khi đổi nguồn.")
    parser.add_argument("--limit", type=int, default=0,
                        help="Số ảnh đầu manifest cần xử lý (0 = hết).")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--manifest-version", choices=["v1", "v2"], default="v1",
                        help="Phiên bản manifest của TV1 cần dùng.")
    args = parser.parse_args(argv)

    splits = SPLITS if args.split == "all" else [args.split]
    args.out.mkdir(parents=True, exist_ok=True)

    for s in splits:
        crop_split_multithread(s, args.out, args.limit, args.workers,
                               args.manifest_version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
