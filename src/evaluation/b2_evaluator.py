"""TV3 - Tuần 3: B2 Evaluator & Image-level Aggregation.

Theo hướng dẫn của TV1 trong handoff_tv1_w3.md:
1. B1/B2 cùng tập image ID, nhưng B2 có thể có nhiều crop cho mỗi ảnh (nhiều cá thể).
2. Khi đánh giá so sánh với B1:
   - Lấy trung bình vector xác suất lớp (softmax) của tất cả crop cùng image_id:
     p_img = mean_{crop in image}(softmax(logits_crop))
   - Dự đoán nhãn cấp ảnh: y_pred = argmax(p_img).
   - So sánh trực tiếp metric cấp ảnh (Image-level Accuracy & Macro F1) với B1.
   - Không so metric B1 cấp ảnh với metric B2 cấp crop!
"""

from collections import defaultdict
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader


def compute_classification_metrics(
    y_true: list[int] | np.ndarray,
    y_pred: list[int] | np.ndarray,
    num_classes: int,
    id_to_label: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Tính các chỉ số phân loại: Accuracy, Macro Precision, Macro Recall, Macro F1, Per-class metrics."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    total_samples = len(y_true)
    if total_samples == 0:
        return {"accuracy": 0.0, "macro_f1": 0.0, "macro_precision": 0.0, "macro_recall": 0.0, "total": 0}

    accuracy = float(np.mean(y_true == y_pred))

    # Confusion matrix & Per-class stats
    confusion = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < num_classes and 0 <= p < num_classes:
            confusion[t, p] += 1

    per_class: dict[str, dict[str, float]] = {}
    precisions = []
    recalls = []
    f1s = []

    for c in range(num_classes):
        tp = int(confusion[c, c])
        fp = int(np.sum(confusion[:, c]) - tp)
        fn = int(np.sum(confusion[c, :]) - tp)
        support = int(np.sum(confusion[c, :]))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

        label_name = id_to_label.get(c, str(c)) if id_to_label else str(c)
        per_class[label_name] = {
            "class_id": c,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }

    macro_precision = float(np.mean(precisions))
    macro_recall = float(np.mean(recalls))
    macro_f1 = float(np.mean(f1s))

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "total_samples": total_samples,
        "per_class": per_class,
        "confusion_matrix": confusion.tolist(),
    }


def aggregate_image_predictions(
    crop_records: list[dict[str, Any]],
    num_classes: int,
    id_to_label: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Gom xác suất các crop cùng image_id, tính trung bình vector xác suất rồi argmax.

    Mỗi crop_record gồm:
      - 'image_id': str
      - 'class_id': int (nhãn ground-truth của ảnh)
      - 'probabilities': list[float] (softmax vector kích thước num_classes)
    """
    image_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in crop_records:
        image_groups[record["image_id"]].append(record)

    image_ids = []
    y_true_img = []
    y_pred_img = []
    image_aggregated_probs = []

    for img_id, crops in image_groups.items():
        # Lấy nhãn ground-truth (mọi crop trong 1 ảnh có cùng nhãn)
        gt_class = crops[0]["class_id"]

        # Trung bình vector xác suất của tất cả crop trong ảnh
        prob_matrix = np.array([c["probabilities"] for c in crops], dtype=float)
        mean_prob = np.mean(prob_matrix, axis=0)

        pred_class = int(np.argmax(mean_prob))

        image_ids.append(img_id)
        y_true_img.append(gt_class)
        y_pred_img.append(pred_class)
        image_aggregated_probs.append(mean_prob.tolist())

    metrics = compute_classification_metrics(
        y_true=y_true_img,
        y_pred=y_pred_img,
        num_classes=num_classes,
        id_to_label=id_to_label,
    )
    metrics["total_unique_images"] = len(image_ids)
    return metrics


@torch.no_grad()
def evaluate_b2_model(
    model: nn.Module,
    data_loader: DataLoader,
    device: torch.device,
    num_classes: int = 8,
    id_to_label: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Chạy đánh giá mô hình B2 trên toàn bộ DataLoader và trả về cả 2 cấp độ:

    1. Crop-level metrics
    2. Image-level aggregated metrics (chuẩn so sánh B1)
    """
    model.eval()

    all_crop_y_true = []
    all_crop_y_pred = []
    crop_records = []
    total_loss = 0.0
    total_weight = 0.0
    criterion = nn.CrossEntropyLoss(reduction="none")

    for batch in data_loader:
        images = batch["images"].to(device)
        class_ids = batch["class_ids"].to(device)
        weights = batch["sample_weights"].to(device)
        image_ids = batch["image_ids"]

        logits = model(images)
        loss_elements = criterion(logits, class_ids)
        weighted_loss = torch.sum(loss_elements * weights)

        total_loss += float(weighted_loss.item())
        total_weight += float(torch.sum(weights).item())

        probs = torch.softmax(logits, dim=-1).cpu().numpy()
        preds = torch.argmax(logits, dim=-1).cpu().numpy()
        targets = class_ids.cpu().numpy()

        for i in range(len(image_ids)):
            all_crop_y_true.append(int(targets[i]))
            all_crop_y_pred.append(int(preds[i]))
            crop_records.append({
                "image_id": image_ids[i],
                "class_id": int(targets[i]),
                "probabilities": probs[i].tolist(),
            })

    avg_loss = total_loss / total_weight if total_weight > 0 else 0.0

    # 1. Metric cấp crop
    crop_metrics = compute_classification_metrics(
        y_true=all_crop_y_true,
        y_pred=all_crop_y_pred,
        num_classes=num_classes,
        id_to_label=id_to_label,
    )
    crop_metrics["weighted_val_loss"] = round(avg_loss, 4)

    # 2. Metric cấp ảnh (Chuẩn so sánh B1)
    image_metrics = aggregate_image_predictions(
        crop_records=crop_records,
        num_classes=num_classes,
        id_to_label=id_to_label,
    )

    return {
        "val_loss": round(avg_loss, 4),
        "crop_level": crop_metrics,
        "image_level": image_metrics,
    }


def format_validation_markdown_table(
    image_metrics: dict[str, Any],
    crop_metrics: dict[str, Any],
    b1_baseline_metrics: dict[str, Any] | None = None,
) -> str:
    """Tạo bảng Markdown so sánh validation giữa B2 (cấp ảnh) và B1."""
    md = []
    md.append("## Bảng so sánh Validation B1 (Toàn ảnh) vs B2 (Vùng cắt)")
    md.append("")
    md.append("| Chỉ số | B1 (Toàn ảnh) | B2 Crop (Cấp Crop) | B2 Crop (Tổng hợp Cấp Ảnh) |")
    md.append("| :--- | :---: | :---: | :---: |")

    b1_acc = f"{b1_baseline_metrics.get('accuracy', 'N/A') * 100:.2f}%" if b1_baseline_metrics and "accuracy" in b1_baseline_metrics else "Chờ B1"
    b1_f1 = f"{b1_baseline_metrics.get('macro_f1', 'N/A') * 100:.2f}%" if b1_baseline_metrics and "macro_f1" in b1_baseline_metrics else "Chờ B1"
    b1_prec = f"{b1_baseline_metrics.get('macro_precision', 'N/A') * 100:.2f}%" if b1_baseline_metrics and "macro_precision" in b1_baseline_metrics else "Chờ B1"
    b1_rec = f"{b1_baseline_metrics.get('macro_recall', 'N/A') * 100:.2f}%" if b1_baseline_metrics and "macro_recall" in b1_baseline_metrics else "Chờ B1"

    crop_acc = f"{crop_metrics['accuracy'] * 100:.2f}%"
    crop_f1 = f"{crop_metrics['macro_f1'] * 100:.2f}%"
    crop_prec = f"{crop_metrics['macro_precision'] * 100:.2f}%"
    crop_rec = f"{crop_metrics['macro_recall'] * 100:.2f}%"

    img_acc = f"{image_metrics['accuracy'] * 100:.2f}%"
    img_f1 = f"{image_metrics['macro_f1'] * 100:.2f}%"
    img_prec = f"{image_metrics['macro_precision'] * 100:.2f}%"
    img_rec = f"{image_metrics['macro_recall'] * 100:.2f}%"

    md.append(f"| **Độ chính xác (Accuracy)** | {b1_acc} | {crop_acc} | **{img_acc}** |")
    md.append(f"| **Macro F1-Score** | {b1_f1} | {crop_f1} | **{img_f1}** |")
    md.append(f"| **Macro Precision** | {b1_prec} | {crop_prec} | **{img_prec}** |")
    md.append(f"| **Macro Recall** | {b1_rec} | {crop_rec} | **{img_rec}** |")
    md.append(f"| **Số lượng mẫu** | {image_metrics['total_unique_images']} ảnh | {crop_metrics['total_samples']} crops | **{image_metrics['total_unique_images']} ảnh** |")
    md.append("")
    md.append("> **Ghi chú đánh giá công bằng:** Chỉ số **B2 Crop (Tổng hợp Cấp Ảnh)** được tính bằng cách lấy trung bình vector xác suất của các crop trong cùng một ảnh rồi chọn argmax theo đúng khuyến nghị của TV1 tại `handoff_tv1_w3.md`.")
    return "\n".join(md)
