"""TV3 - Tuần 4: Phân tích lỗi (Error Analysis) cho B2/B3 trên tập validation.

Phân tích chi tiết các dự đoán sai trên tập validation để:
1. Xác định các cặp lớp hay bị nhầm lẫn nhất (confused class pairs).
2. Liệt kê tất cả ảnh bị phân loại sai kèm xác suất từng lớp.
3. Tính tỷ lệ lỗi và mục tiêu nhầm phổ biến nhất theo từng lớp.
4. Xuất báo cáo JSON (cấu trúc) và Markdown (đọc được) phục vụ tài liệu Week 4.
5. Bảo vệ chống ghi đè bằng chứng gốc (anti-overwrite protection).
6. Ghi nhận SHA-256 của checkpoint, manifest, provenance và runtime môi trường.

Đánh giá cấp ảnh: trung bình softmax probabilities của các crop cùng image_id rồi argmax
(theo đúng protocol B2 đã thống nhất với TV1).

KHÔNG BAO GIỜ dùng tập test để phân tích — chỉ dùng tập validation.

Sử dụng:
    # Phân tích B2:
    python scripts/error_analysis.py --checkpoint outputs/b2_crop_classifier/b2_run01/best_model.pt

    # Phân tích B3 với mã attempt riêng (không ghi đè bản gốc):
    python scripts/error_analysis.py --checkpoint outputs/b3_class_weighted/b3_run01/best_model.pt --attempt attempt02

    # Tuỳ chọn thêm:
    python scripts/error_analysis.py --checkpoint ... --top-n 15 --output-dir reports/tv3 --preflight-hash-check
"""

import argparse
import hashlib
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models.b2_classifier import B2CropClassifier, load_checkpoint
from src.data.b2_dataset import B2ComparisonDataset, b2_collate_fn, make_b2_loaders
from src.evaluation.b2_evaluator import evaluate_b2_model, aggregate_image_predictions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("error_analysis")
from src.evaluation.reproducibility import verify_validation_inputs, runtime_metadata


def sha256_file(path: Path) -> str:
    """Tính hash SHA-256 của file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Tiện ích phân tích lỗi
# ---------------------------------------------------------------------------

def _derive_model_name(checkpoint_path: Path) -> str:
    """Suy ra tên mô hình từ đường dẫn checkpoint (ví dụ: 'b2' hoặc 'b3').

    Ưu tiên lấy từ tên thư mục cha chứa checkpoint.
    Nếu không nhận diện được, dùng tên file checkpoint (bỏ phần mở rộng).
    """
    parts = checkpoint_path.parts
    for part in parts:
        part_lower = part.lower()
        if "b3" in part_lower:
            return "b3"
        if "b2" in part_lower:
            return "b2"
    return checkpoint_path.stem


def _build_confusion_matrix(
    y_true: list[int],
    y_pred: list[int],
    num_classes: int,
) -> list[list[int]]:
    """Xây dựng confusion matrix dạng nested list [true][pred]."""
    cm = [[0] * num_classes for _ in range(num_classes)]
    for t, p in zip(y_true, y_pred):
        if 0 <= t < num_classes and 0 <= p < num_classes:
            cm[t][p] += 1
    return cm


def _top_confused_pairs(
    cm: list[list[int]],
    id_to_label: dict[int, str],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Trích xuất top-N cặp lớp bị nhầm lẫn nhiều nhất (off-diagonal).

    Trả về danh sách đã sắp xếp giảm dần theo số lần nhầm,
    mỗi phần tử chứa true_label, predicted_label, count, và direction mô tả.
    """
    num_classes = len(cm)
    pairs: list[tuple[int, int, int]] = []
    for t in range(num_classes):
        for p in range(num_classes):
            if t != p and cm[t][p] > 0:
                pairs.append((t, p, cm[t][p]))

    pairs.sort(key=lambda x: x[2], reverse=True)

    result: list[dict[str, Any]] = []
    for t, p, count in pairs[:top_n]:
        true_name = id_to_label.get(t, str(t))
        pred_name = id_to_label.get(p, str(p))
        result.append({
            "true_label": true_name,
            "predicted_label": pred_name,
            "true_class_id": t,
            "predicted_class_id": p,
            "count": count,
            "direction": f"{true_name} → {pred_name}",
        })
    return result


def _per_class_error_breakdown(
    y_true: list[int],
    y_pred: list[int],
    num_classes: int,
    id_to_label: dict[int, str],
) -> dict[str, dict[str, Any]]:
    """Tính tỷ lệ lỗi và mục tiêu nhầm phổ biến nhất theo từng lớp."""
    class_errors: dict[int, Counter] = defaultdict(Counter)
    class_totals: Counter = Counter()

    for t, p in zip(y_true, y_pred):
        class_totals[t] += 1
        if t != p:
            class_errors[t][p] += 1

    breakdown: dict[str, dict[str, Any]] = {}
    for c in range(num_classes):
        label = id_to_label.get(c, str(c))
        total = class_totals.get(c, 0)
        errors = sum(class_errors[c].values())
        error_rate = errors / total if total > 0 else 0.0

        mistake_counter = class_errors[c]
        if mistake_counter:
            most_common_id, most_common_count = mistake_counter.most_common(1)[0]
            most_common_label = id_to_label.get(most_common_id, str(most_common_id))
        else:
            most_common_label = None
            most_common_count = 0

        mistake_detail: dict[str, int] = {}
        for mid, mcount in mistake_counter.most_common():
            mistake_detail[id_to_label.get(mid, str(mid))] = mcount

        breakdown[label] = {
            "class_id": c,
            "total": total,
            "errors": errors,
            "error_rate": round(error_rate, 4),
            "most_common_mistake": most_common_label,
            "most_common_mistake_count": most_common_count,
            "mistake_counts": mistake_detail,
        }

    return breakdown


def _build_misclassified_list(
    image_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Lọc danh sách ảnh bị phân loại sai, sắp xếp theo confidence tăng dần."""
    misclassified: list[dict[str, Any]] = []
    for rec in image_records:
        if rec["true_class_id"] != rec["predicted_class_id"]:
            misclassified.append(rec)

    misclassified.sort(key=lambda x: x["confidence"])
    return misclassified


def _summary_statistics(
    y_true: list[int],
    y_pred: list[int],
    per_class_breakdown: dict[str, dict[str, Any]],
    top_confused: list[dict[str, Any]],
) -> dict[str, Any]:
    """Tổng hợp thống kê lỗi tổng quan."""
    total = len(y_true)
    total_misclassified = sum(1 for t, p in zip(y_true, y_pred) if t != p)
    overall_error_rate = total_misclassified / total if total > 0 else 0.0
    overall_accuracy = 1.0 - overall_error_rate

    sorted_classes = sorted(
        per_class_breakdown.items(),
        key=lambda x: x[1]["error_rate"],
        reverse=True,
    )
    worst_classes = [
        {
            "class": name,
            "error_rate": round(info["error_rate"], 4),
            "errors": info["errors"],
            "total": info["total"],
            "most_confused_with": info["most_common_mistake"],
        }
        for name, info in sorted_classes
        if info["error_rate"] > 0
    ]

    bidirectional: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for pair in top_confused:
        a = pair["true_label"]
        b = pair["predicted_label"]
        key = tuple(sorted([a, b]))
        if key not in seen_pairs:
            seen_pairs.add(key)
            reverse_count = 0
            for p2 in top_confused:
                if p2["true_label"] == b and p2["predicted_label"] == a:
                    reverse_count = p2["count"]
                    break
            bidirectional.append({
                "class_a": a,
                "class_b": b,
                "a_to_b": pair["count"],
                "b_to_a": reverse_count,
                "total_confusion": pair["count"] + reverse_count,
            })

    bidirectional.sort(key=lambda x: x["total_confusion"], reverse=True)

    return {
        "total_images": total,
        "total_misclassified": total_misclassified,
        "overall_accuracy": round(overall_accuracy, 4),
        "overall_error_rate": round(overall_error_rate, 4),
        "worst_performing_classes": worst_classes,
        "most_confused_pairs_bidirectional": bidirectional,
    }


def _generate_markdown_report(
    model_name: str,
    checkpoint_path: str,
    summary: dict[str, Any],
    top_confused: list[dict[str, Any]],
    per_class_breakdown: dict[str, dict[str, Any]],
    misclassified: list[dict[str, Any]],
    confusion_matrix: list[list[int]],
    id_to_label: dict[int, str],
    num_classes: int,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Tạo báo cáo Markdown chi tiết phục vụ tài liệu Week 4."""
    meta = metadata or {}
    lines: list[str] = []

    lines.append(f"# Báo cáo Phân tích Lỗi — Mô hình {model_name.upper()}")
    lines.append("")
    lines.append(f"> **Checkpoint:** `{checkpoint_path}`")
    if "checkpoint_sha256" in meta:
        lines.append(f"> **Checkpoint SHA-256:** `{meta['checkpoint_sha256']}`")
    if "manifest_sha256" in meta and meta["manifest_sha256"]:
        lines.append(f"> **Validation Manifest SHA-256:** `{meta['manifest_sha256']}`")
    if "runtime" in meta:
        rt = meta["runtime"]
        lines.append(f"> **Thiết bị chạy:** `{rt.get('device_name', rt.get('device', 'N/A'))}` | **PyTorch:** `{rt.get('torch', 'N/A')}`")
    lines.append(f"> **Thời gian tạo:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"> **Tập đánh giá:** Validation (KHÔNG dùng test set)")
    lines.append("")

    # --- 1. Tổng quan ---
    lines.append("## 1. Tổng quan")
    lines.append("")
    lines.append("| Chỉ số | Giá trị |")
    lines.append("| :--- | :---: |")
    lines.append(f"| Tổng số ảnh | {summary['total_images']} |")
    lines.append(f"| Số ảnh phân loại sai | {summary['total_misclassified']} |")
    lines.append(f"| Độ chính xác tổng thể (Image-level) | {summary['overall_accuracy'] * 100:.2f}% |")
    lines.append(f"| Tỷ lệ lỗi tổng thể | {summary['overall_error_rate'] * 100:.2f}% |")
    lines.append("")

    # --- 2. Top cặp lớp nhầm lẫn ---
    lines.append(f"## 2. Top-{len(top_confused)} cặp lớp bị nhầm lẫn nhiều nhất")
    lines.append("")
    lines.append("| # | Lớp thật | Dự đoán sai thành | Số lần | Hướng |")
    lines.append("| :---: | :--- | :--- | :---: | :--- |")
    for i, pair in enumerate(top_confused, 1):
        lines.append(
            f"| {i} | {pair['true_label']} | {pair['predicted_label']} "
            f"| {pair['count']} | {pair['direction']} |"
        )
    lines.append("")

    # --- 3. Nhầm lẫn hai chiều ---
    bidirectional = summary.get("most_confused_pairs_bidirectional", [])
    if bidirectional:
        lines.append("## 3. Các cặp lớp nhầm lẫn hai chiều (A ↔ B)")
        lines.append("")
        lines.append("| Lớp A | Lớp B | A→B | B→A | Tổng nhầm |")
        lines.append("| :--- | :--- | :---: | :---: | :---: |")
        for bp in bidirectional:
            lines.append(
                f"| {bp['class_a']} | {bp['class_b']} "
                f"| {bp['a_to_b']} | {bp['b_to_a']} | {bp['total_confusion']} |"
            )
        lines.append("")

    # --- 4. Phân tích lỗi theo lớp ---
    lines.append("## 4. Phân tích lỗi theo từng lớp")
    lines.append("")
    lines.append("| Lớp | Tổng ảnh | Số lỗi | Tỷ lệ lỗi | Nhầm nhiều nhất sang |")
    lines.append("| :--- | :---: | :---: | :---: | :--- |")
    sorted_breakdown = sorted(
        per_class_breakdown.items(),
        key=lambda x: x[1]["error_rate"],
        reverse=True,
    )
    for label, info in sorted_breakdown:
        mistake = info["most_common_mistake"] or "—"
        if info["most_common_mistake"]:
            mistake += f" ({info['most_common_mistake_count']})"
        lines.append(
            f"| {label} | {info['total']} | {info['errors']} "
            f"| {info['error_rate'] * 100:.2f}% | {mistake} |"
        )
    lines.append("")

    # --- 5. Các lớp có hiệu suất kém nhất ---
    worst = summary.get("worst_performing_classes", [])
    if worst:
        lines.append("## 5. Các lớp có hiệu suất kém nhất")
        lines.append("")
        for i, w in enumerate(worst[:5], 1):
            confused_with = w['most_confused_with'] or 'N/A'
            lines.append(
                f"{i}. **{w['class']}** — Tỷ lệ lỗi: {w['error_rate'] * 100:.2f}% "
                f"({w['errors']}/{w['total']} ảnh sai), "
                f"hay nhầm với: *{confused_with}*"
            )
        lines.append("")

    # --- 6. Confusion Matrix ---
    lines.append("## 6. Confusion Matrix")
    lines.append("")
    sorted_labels = [id_to_label.get(c, str(c)) for c in range(num_classes)]
    short_labels = [lbl[:12] for lbl in sorted_labels]
    header = "| True \\ Pred | " + " | ".join(short_labels) + " |"
    separator = "| :--- |" + " :---: |" * num_classes
    lines.append(header)
    lines.append(separator)
    for t in range(num_classes):
        row_vals = []
        for p in range(num_classes):
            val = confusion_matrix[t][p]
            if t == p:
                row_vals.append(f"**{val}**")
            elif val > 0:
                row_vals.append(f"_{val}_")
            else:
                row_vals.append("0")
        lines.append(f"| {short_labels[t]} | " + " | ".join(row_vals) + " |")
    lines.append("")
    lines.append("> **Ghi chú:** Số in đậm = phân loại đúng (diagonal). Số in nghiêng = phân loại sai.")
    lines.append("")

    # --- 7. Danh sách ảnh bị phân loại sai ---
    lines.append("## 7. Ảnh bị phân loại sai (sắp xếp theo confidence tăng dần)")
    lines.append("")
    lines.append(f"Tổng: **{len(misclassified)}** ảnh bị phân loại sai.")
    lines.append("")
    show_count = min(30, len(misclassified))
    if show_count > 0:
        lines.append(f"Hiển thị top {show_count} ảnh uncertain nhất:")
        lines.append("")
        lines.append("| # | Image ID | Nhãn thật | Dự đoán | Confidence |")
        lines.append("| :---: | :--- | :--- | :--- | :---: |")
        for i, mis in enumerate(misclassified[:show_count], 1):
            lines.append(
                f"| {i} | `{mis['image_id']}` | {mis['true_label']} "
                f"| {mis['predicted_label']} | {mis['confidence'] * 100:.1f}% |"
            )
        lines.append("")
    else:
        lines.append("Không có ảnh nào bị phân loại sai trên tập validation! 🎉")
        lines.append("")

    lines.append("---")
    lines.append(f"*Báo cáo được tạo tự động bởi `scripts/error_analysis.py` — TV3*")

    return "\n".join(lines)


@torch.no_grad()
def run_error_analysis(
    checkpoint_path: Path,
    top_n: int = 10,
    output_dir: Path = ROOT / "reports" / "tv3",
    attempt: str | None = None,
    overwrite: bool = False,
    preflight_hash_check: bool = True,
    data_root: Path | None = None,
) -> dict[str, Any]:
    """Chạy phân tích lỗi trên tập validation và xuất báo cáo JSON + Markdown.

    Tính năng bảo vệ:
    - Nạp an toàn bằng weights_only=True.
    - Từ chối ghi đè; bắt buộc xác minh bản khóa và SHA ảnh nguồn.
    - Ghi nhận SHA-256 của Checkpoint, Manifest, Provenance và Runtime môi trường.
    """
    logger.info("Nạp checkpoint từ: %s", checkpoint_path)
    if overwrite or not preflight_hash_check:
        raise ValueError('Immutable reports and source hash verification are mandatory')
    if attempt is not None and not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', attempt):
        raise ValueError('Invalid attempt ID')
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Không tìm thấy checkpoint: {checkpoint_path}")

    model_name = _derive_model_name(checkpoint_path)
    file_suffix = f"_{attempt}" if attempt else ""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"error_analysis_{model_name}{file_suffix}.json"
    md_path = output_dir / f"error_analysis_{model_name}{file_suffix}.md"

    # Cơ chế bảo vệ chống ghi đè bằng chứng cũ
    if json_path.exists() or md_path.exists():
        msg = (
            f"\n{'=' * 70}\n"
            f"[LỖI BẢO VỆ BẰNG CHỨNG GỐC - ANTI-OVERWRITE]\n"
            f"File báo cáo '{json_path.name}' hoặc '{md_path.name}' đã tồn tại trong '{output_dir}'!\n"
            f"Để tránh ghi đè làm mất bằng chứng gốc, hệ thống từ chối ghi đè.\n"
            f"Hãy truyền tham số --attempt (ví dụ: --attempt attempt02) để lưu bản mới.\n"
            f"{'=' * 70}"
        )
        logger.error(msg)
        raise FileExistsError(msg)

    # Tính SHA-256 của checkpoint
    ckpt_sha = sha256_file(checkpoint_path)
    logger.info("Checkpoint SHA-256: %s", ckpt_sha)

    # Nạp an toàn với weights_only=True
    checkpoint_data = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    input_root = Path(data_root) if data_root is not None else ROOT
    comp_dir, ckpt_sha, verified_model = verify_validation_inputs(input_root, checkpoint_path, checkpoint_data)
    num_classes = checkpoint_data.get("num_classes", 8)
    backbone_name = checkpoint_data.get("backbone_name", "resnet18")
    id_to_label_raw = checkpoint_data.get("id_to_label", {})
    id_to_label: dict[int, str] = {int(k): v for k, v in id_to_label_raw.items()}

    if not id_to_label:
        class_map_raw = checkpoint_data.get("class_map", {})
        if class_map_raw:
            id_to_label = {v: k for k, v in class_map_raw.items()}
            if isinstance(list(id_to_label.keys())[0], str):
                id_to_label = {int(k): v for k, v in id_to_label.items()}
        else:
            default_class_map = ROOT / "data" / "processed" / "comparison_v1" / "class_map.json"
            if default_class_map.exists():
                raw = json.loads(default_class_map.read_text(encoding="utf-8"))
                id_to_label = {int(k): v for k, v in raw.items()}
                logger.warning("Checkpoint thiếu id_to_label, đã đọc từ: %s", default_class_map)
            else:
                id_to_label = {i: str(i) for i in range(num_classes)}
                logger.warning("Không tìm được class_map, dùng nhãn số thay thế.")

    logger.info(
        "Cấu hình mô hình: backbone=%s, num_classes=%d, classes=%s",
        backbone_name, num_classes, list(id_to_label.values()),
    )

    model = B2CropClassifier(
        num_classes=num_classes,
        backbone_name=backbone_name,
        pretrained=False,
    )
    model.load_state_dict(checkpoint_data['model_state_dict'])
    model.eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    logger.info("Sử dụng thiết bị: %s", device)

    # Xác minh dữ liệu và tính SHA manifest/provenance
    config = checkpoint_data.get("config", {})
    data_cfg = config.get("data", {})

    val_manifest = comp_dir / "b2" / "val.jsonl"
    manifest_sha = sha256_file(val_manifest) if val_manifest.exists() else None

    prov_file = comp_dir / "provenance.json"
    prov_sha = sha256_file(prov_file) if prov_file.exists() else None

    logger.info("Tạo DataLoader cho tập validation (preflight_hash_check=%s)...", preflight_hash_check)
    loaders = make_b2_loaders(
        comparison_dir=comp_dir,
        batch_size=32,
        num_workers=0,
        splits=["val"],
        root=input_root,
        preflight_hash_check=True,
    )
    val_loader = loaders["val"]
    logger.info("Đã tạo val loader: %d batches", len(val_loader))

    logger.info("Chạy inference trên tập validation...")
    crop_records: list[dict[str, Any]] = []

    for batch in val_loader:
        images = batch["images"].to(device, non_blocking=True)
        class_ids = batch["class_ids"]
        image_ids = batch["image_ids"]

        logits = model(images)
        probs = torch.softmax(logits, dim=-1).cpu().numpy()

        for i in range(len(image_ids)):
            crop_records.append({
                "image_id": image_ids[i],
                "class_id": int(class_ids[i]),
                "probabilities": probs[i].tolist(),
            })

    logger.info("Thu thập xong: %d crop records", len(crop_records))

    logger.info("Tổng hợp dự đoán cấp ảnh (trung bình softmax → argmax)...")

    image_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in crop_records:
        image_groups[rec["image_id"]].append(rec)

    image_records: list[dict[str, Any]] = []
    y_true_all: list[int] = []
    y_pred_all: list[int] = []

    for img_id, crops in image_groups.items():
        gt_class = crops[0]["class_id"]

        prob_matrix = np.array([c["probabilities"] for c in crops], dtype=float)
        mean_prob = np.mean(prob_matrix, axis=0)
        pred_class = int(np.argmax(mean_prob))
        confidence = float(mean_prob[pred_class])

        y_true_all.append(gt_class)
        y_pred_all.append(pred_class)

        image_records.append({
            "image_id": img_id,
            "true_class_id": gt_class,
            "true_label": id_to_label.get(gt_class, str(gt_class)),
            "predicted_class_id": pred_class,
            "predicted_label": id_to_label.get(pred_class, str(pred_class)),
            "confidence": confidence,
            "all_probabilities": {
                id_to_label.get(c, str(c)): float(mean_prob[c])
                for c in range(num_classes)
            },
            "num_crops": len(crops),
        })

    total_images = len(image_records)
    logger.info("Tổng hợp xong: %d ảnh duy nhất", total_images)

    logger.info("Xây dựng confusion matrix và phân tích lỗi...")

    confusion_matrix = _build_confusion_matrix(y_true_all, y_pred_all, num_classes)
    top_confused = _top_confused_pairs(confusion_matrix, id_to_label, top_n=top_n)
    misclassified = _build_misclassified_list(image_records)
    per_class_breakdown = _per_class_error_breakdown(
        y_true_all, y_pred_all, num_classes, id_to_label,
    )
    summary = _summary_statistics(
        y_true_all, y_pred_all, per_class_breakdown, top_confused,
    )

    logger.info("Mô hình: %s | Tổng lỗi: %d/%d (%.2f%%)",
                model_name, summary["total_misclassified"], summary["total_images"],
                summary["overall_error_rate"] * 100)

    runtime_meta = runtime_metadata(device)
    if sha256_file(checkpoint_path) != ckpt_sha:
        raise ValueError('Checkpoint changed during analysis')

    metadata = {
        "model_name": model_name,
        "attempt": attempt,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": ckpt_sha,
        "manifest_path": str(val_manifest) if val_manifest.exists() else None,
        "manifest_sha256": manifest_sha,
        "provenance_sha256": prov_sha,
        "preflight_hash_check": preflight_hash_check,
        "backbone": backbone_name,
        "num_classes": num_classes,
        "evaluation_split": "val",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "runtime": runtime_meta,
        "author": "TV3",
        "verified_checkpoint_model": verified_model,
        "scope": "Validation diagnostic; not an overwrite or acceptance of historical B3 reference",
    }

    json_payload = {
        "metadata": metadata,
        "summary": summary,
        "confusion_matrix": {
            "matrix": confusion_matrix,
            "labels": [id_to_label.get(c, str(c)) for c in range(num_classes)],
        },
        "top_confused_pairs": top_confused,
        "per_class_breakdown": per_class_breakdown,
        "misclassified_images": misclassified,
        "all_image_predictions": image_records,
    }

    with open(json_path, "x", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2, ensure_ascii=False)
    logger.info("Đã xuất báo cáo JSON: %s", json_path)

    md_content = _generate_markdown_report(
        model_name=model_name,
        checkpoint_path=str(checkpoint_path),
        summary=summary,
        top_confused=top_confused,
        per_class_breakdown=per_class_breakdown,
        misclassified=misclassified,
        confusion_matrix=confusion_matrix,
        id_to_label=id_to_label,
        num_classes=num_classes,
        metadata=metadata,
    )
    with md_path.open('x', encoding='utf-8') as handle:
        handle.write(md_content)
    logger.info("Đã xuất báo cáo Markdown: %s", md_path)

    logger.info("Phân tích lỗi hoàn tất cho mô hình %s!", model_name.upper())
    return json_payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phân tích lỗi B2/B3 trên tập validation (TV3 Tuần 4).",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Đường dẫn tới file checkpoint (.pt) của B2 hoặc B3.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Số cặp lớp nhầm lẫn hàng đầu cần hiển thị (mặc định: 10).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/tv3",
        help="Thư mục lưu báo cáo (mặc định: reports/tv3).",
    )
    parser.add_argument(
        "--attempt",
        type=str,
        default=None,
        help="Mã lượt chạy (ví dụ: attempt02) để không ghi đè báo cáo gốc.",
    )
    parser.add_argument(
        "--preflight-hash-check",
        action="store_true",
        default=True,
        help="Xác thực SHA-256 của ảnh nguồn trước khi suy luận.",
    )
    parser.add_argument('--data-root', type=Path, default=ROOT)
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.is_absolute():
        checkpoint_path = ROOT / checkpoint_path

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir

    run_error_analysis(
        checkpoint_path=checkpoint_path,
        top_n=args.top_n,
        output_dir=output_dir,
        attempt=args.attempt,
        preflight_hash_check=args.preflight_hash_check,
        data_root=args.data_root,
    )


if __name__ == "__main__":
    main()
