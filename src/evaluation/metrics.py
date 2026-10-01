#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
CameraTrapML – Module Đánh giá Thống nhất (Evaluation Metrics)
==============================================================================
Mã công việc : W1-02  (Tuần 1 – TV2)
Mô tả        : Cung cấp các hàm tính metric chuẩn hóa dùng xuyên suốt đồ án.
                Hỗ trợ đầu vào là PyTorch Tensor lẫn NumPy array.

Metric chính (dùng chọn checkpoint):
    ► Macro-F1

Metric phụ:
    ► Macro-Precision, Macro-Recall, Accuracy
    ► Per-class Precision / Recall / F1
    ► Confusion Matrix (số liệu + hình trực quan)

Sử dụng:
    from src.evaluation.metrics import compute_metrics, compute_confusion_matrix

    results = compute_metrics(y_true, y_pred, class_names)
    cm_dict = compute_confusion_matrix(y_true, y_pred, class_names,
                                       save_path="confusion_matrix.png")
==============================================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import matplotlib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix as sk_confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# ---------------------------------------------------------------------------
# Kiểu dữ liệu linh hoạt: chấp nhận cả Tensor và ndarray
# ---------------------------------------------------------------------------
ArrayLike = Union[np.ndarray, "torch.Tensor", List[int], Sequence[int]]


# ---------------------------------------------------------------------------
# Tiện ích nội bộ
# ---------------------------------------------------------------------------
def _to_numpy(arr: ArrayLike) -> np.ndarray:
    """Chuyển đổi input về numpy 1-D array.

    Hỗ trợ: list, numpy array, PyTorch Tensor (CPU hoặc GPU).
    """
    # Kiểm tra xem có phải PyTorch Tensor không (tránh import nếu không cần)
    try:
        import torch
        if isinstance(arr, torch.Tensor):
            return arr.detach().cpu().numpy()
    except ImportError:
        pass

    return np.asarray(arr).ravel()


# ---------------------------------------------------------------------------
# 1. Compute Metrics – Hàm chính
# ---------------------------------------------------------------------------
def compute_metrics(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    class_names: Optional[List[str]] = None,
    *,
    zero_division: int = 0,
) -> Dict:
    """Tính toán toàn bộ metric đánh giá cho bài toán phân loại.

    Args:
        y_true: Nhãn thật (ground-truth labels). Shape ``(N,)``.
        y_pred: Nhãn dự đoán. Shape ``(N,)``.
        class_names: Danh sách tên các lớp theo thứ tự index.
                     Nếu ``None``, sẽ tự sinh dạng ``['class_0', 'class_1', ...]``.
        zero_division: Giá trị trả về khi chia cho 0
                       (mặc định ``0`` – an toàn cho lớp không có mẫu).

    Returns:
        dict chứa:
            - ``macro_f1``        : float – **Metric chính chọn checkpoint**
            - ``macro_precision`` : float
            - ``macro_recall``    : float
            - ``accuracy``        : float
            - ``per_class``       : dict[str, dict] –
                Mỗi lớp có ``precision``, ``recall``, ``f1``, ``support``.
            - ``classification_report_str`` : str –
                Bảng tóm tắt dạng text (tiện cho logging).
    """
    y_true_np = _to_numpy(y_true)
    y_pred_np = _to_numpy(y_pred)

    # Xác định danh sách lớp
    unique_labels = np.unique(np.concatenate([y_true_np, y_pred_np]))
    num_classes = len(unique_labels)
    if class_names is None:
        class_names = [f"class_{i}" for i in range(num_classes)]

    # --- Macro metrics ---
    macro_f1 = f1_score(
        y_true_np, y_pred_np,
        average="macro", zero_division=zero_division,
    )
    macro_precision = precision_score(
        y_true_np, y_pred_np,
        average="macro", zero_division=zero_division,
    )
    macro_recall = recall_score(
        y_true_np, y_pred_np,
        average="macro", zero_division=zero_division,
    )
    accuracy = accuracy_score(y_true_np, y_pred_np)

    # --- Per-class metrics ---
    per_class_precision = precision_score(
        y_true_np, y_pred_np,
        average=None, zero_division=zero_division,
    )
    per_class_recall = recall_score(
        y_true_np, y_pred_np,
        average=None, zero_division=zero_division,
    )
    per_class_f1 = f1_score(
        y_true_np, y_pred_np,
        average=None, zero_division=zero_division,
    )

    # Đếm số mẫu thực (support) cho từng lớp
    support = np.array([
        np.sum(y_true_np == label) for label in unique_labels
    ])

    per_class: Dict[str, Dict[str, float]] = {}
    for idx, name in enumerate(class_names):
        per_class[name] = {
            "precision": float(per_class_precision[idx]),
            "recall":    float(per_class_recall[idx]),
            "f1":        float(per_class_f1[idx]),
            "support":   int(support[idx]),
        }

    # --- Classification report dạng text ---
    report_str = classification_report(
        y_true_np, y_pred_np,
        target_names=class_names,
        zero_division=zero_division,
    )

    return {
        "macro_f1":        float(macro_f1),
        "macro_precision": float(macro_precision),
        "macro_recall":    float(macro_recall),
        "accuracy":        float(accuracy),
        "per_class":       per_class,
        "classification_report_str": report_str,
    }


# ---------------------------------------------------------------------------
# 2. Confusion Matrix
# ---------------------------------------------------------------------------
def compute_confusion_matrix(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    class_names: Optional[List[str]] = None,
) -> Dict:
    """Tính Confusion Matrix và trả về dict số liệu.

    Args:
        y_true: Nhãn thật.
        y_pred: Nhãn dự đoán.
        class_names: Tên các lớp.

    Returns:
        dict chứa:
            - ``matrix``      : np.ndarray shape ``(C, C)``
            - ``class_names`` : list[str]
            - ``per_class_accuracy`` : dict[str, float]
    """
    y_true_np = _to_numpy(y_true)
    y_pred_np = _to_numpy(y_pred)

    unique_labels = np.unique(np.concatenate([y_true_np, y_pred_np]))
    num_classes = len(unique_labels)
    if class_names is None:
        class_names = [f"class_{i}" for i in range(num_classes)]

    cm = sk_confusion_matrix(y_true_np, y_pred_np)

    # Accuracy theo từng lớp (đường chéo / tổng hàng)
    row_sums = cm.sum(axis=1)
    per_class_acc = {}
    for idx, name in enumerate(class_names):
        if row_sums[idx] > 0:
            per_class_acc[name] = float(cm[idx, idx] / row_sums[idx])
        else:
            per_class_acc[name] = 0.0

    return {
        "matrix":             cm,
        "class_names":        class_names,
        "per_class_accuracy": per_class_acc,
    }


def plot_confusion_matrix(
    y_true: ArrayLike,
    y_pred: ArrayLike,
    class_names: Optional[List[str]] = None,
    *,
    normalize: bool = True,
    figsize: tuple = (10, 8),
    cmap: str = "Blues",
    title: str = "Confusion Matrix",
    save_path: Optional[Union[str, Path]] = None,
    show: bool = False,
) -> "matplotlib.figure.Figure":
    """Vẽ Confusion Matrix trực quan bằng Seaborn heatmap.

    Args:
        y_true: Nhãn thật.
        y_pred: Nhãn dự đoán.
        class_names: Tên các lớp.
        normalize: Nếu ``True``, chuẩn hóa theo hàng (True-label) → tỉ lệ %.
        figsize: Kích thước figure ``(width, height)`` inch.
        cmap: Bảng màu Matplotlib.
        title: Tiêu đề hình.
        save_path: Đường dẫn lưu hình (``*.png``). ``None`` = không lưu.
        show: Nếu ``True``, gọi ``plt.show()`` (dùng khi chạy interactive).

    Returns:
        ``matplotlib.figure.Figure`` – đối tượng figure để tiếp tục tùy chỉnh.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    cm_dict = compute_confusion_matrix(y_true, y_pred, class_names)
    cm = cm_dict["matrix"]
    class_names = cm_dict["class_names"]

    if normalize:
        # Chuẩn hóa theo hàng, tránh chia cho 0
        row_sums = cm.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1, row_sums)  # tránh /0
        cm_display = cm.astype(float) / row_sums
        fmt = ".2%"
        subtitle = "(Normalized by True Label)"
    else:
        cm_display = cm
        fmt = "d"
        subtitle = "(Raw Counts)"

    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        cm_display,
        annot=True,
        fmt=fmt,
        cmap=cmap,
        xticklabels=class_names,
        yticklabels=class_names,
        linewidths=0.5,
        linecolor="gray",
        ax=ax,
    )
    ax.set_xlabel("Predicted Label", fontsize=12)
    ax.set_ylabel("True Label", fontsize=12)
    ax.set_title(f"{title}\n{subtitle}", fontsize=14)

    # Xoay nhãn cho dễ đọc
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[INFO] Confusion matrix saved → {save_path}")

    if show:
        plt.show()

    return fig


# ---------------------------------------------------------------------------
# 3. Tiện ích bổ sung
# ---------------------------------------------------------------------------
def print_metrics_summary(metrics: Dict) -> None:
    """In tóm tắt metric ra console (dùng cho logging nhanh).

    Args:
        metrics: dict trả về từ ``compute_metrics()``.
    """
    print("=" * 60)
    print("  EVALUATION METRICS SUMMARY")
    print("=" * 60)
    print(f"  Macro-F1  (checkpoint) : {metrics['macro_f1']:.4f}")
    print(f"  Macro-Precision        : {metrics['macro_precision']:.4f}")
    print(f"  Macro-Recall           : {metrics['macro_recall']:.4f}")
    print(f"  Accuracy               : {metrics['accuracy']:.4f}")
    print("-" * 60)
    print(metrics["classification_report_str"])
    print("=" * 60)


# ---------------------------------------------------------------------------
# Demo / Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    """Chạy demo nhanh với dữ liệu giả để kiểm tra module."""
    print("[DEMO] Kiểm tra module evaluation/metrics.py\n")

    # Tạo dữ liệu mẫu (5 lớp, 30 mẫu)
    np.random.seed(42)
    num_samples = 30
    num_classes = 5
    class_names = [
        "Saola", "Mang_lon", "Mang_Truong_Son",
        "Tho_van", "Ga_loi_lam",
    ]

    y_true = np.random.randint(0, num_classes, size=num_samples)
    y_pred = y_true.copy()
    # Gây nhiễu: sai 20% dự đoán
    noise_idx = np.random.choice(num_samples, size=6, replace=False)
    y_pred[noise_idx] = np.random.randint(0, num_classes, size=len(noise_idx))

    # --- Test compute_metrics ---
    results = compute_metrics(y_true, y_pred, class_names)
    print_metrics_summary(results)

    # --- Test với PyTorch Tensor (nếu có) ---
    try:
        import torch
        y_true_t = torch.tensor(y_true)
        y_pred_t = torch.tensor(y_pred)
        results_t = compute_metrics(y_true_t, y_pred_t, class_names)
        print("[OK] Hoạt động với PyTorch Tensor ✓")
    except ImportError:
        print("[SKIP] PyTorch không khả dụng – bỏ qua test Tensor.")

    # --- Test confusion matrix ---
    cm_dict = compute_confusion_matrix(y_true, y_pred, class_names)
    print(f"\nConfusion Matrix shape: {cm_dict['matrix'].shape}")
    print(f"Per-class accuracy   : {cm_dict['per_class_accuracy']}")

    # --- Test plot (lưu file, không show) ---
    fig = plot_confusion_matrix(
        y_true, y_pred, class_names,
        save_path="demo_confusion_matrix.png",
        show=False,
    )
    print("\n[DEMO] Hoàn tất kiểm tra module metrics ✓")
