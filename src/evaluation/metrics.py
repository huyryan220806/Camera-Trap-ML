"""Classification metrics that always use the complete project class map."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLASS_MAP = ROOT / "data" / "processed" / "v1" / "class_map.json"


def load_class_map(class_map_path: str | Path = DEFAULT_CLASS_MAP) -> tuple[list[int], list[str]]:
    """Return class IDs and names sorted by numeric class ID.

    The project currently stores ``{"0": "class_name"}``, while this parser
    also accepts ``{"class_name": 0}`` to keep evaluation code independent of
    JSON orientation.
    """
    path = Path(class_map_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Class map not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Class map is not valid JSON: {path}") from exc

    if not isinstance(raw, dict) or not raw:
        raise ValueError("Class map must be a non-empty JSON object.")

    entries: list[tuple[int, str]] = []
    if all(_is_integer_like(key) and isinstance(value, str) for key, value in raw.items()):
        entries = [(int(key), value) for key, value in raw.items()]
    elif all(isinstance(key, str) and _is_integer_like(value) for key, value in raw.items()):
        entries = [(int(value), key) for key, value in raw.items()]
    else:
        raise ValueError(
            "Class map must map numeric IDs to names or class names to numeric IDs."
        )

    entries.sort(key=lambda item: item[0])
    labels = [class_id for class_id, _ in entries]
    target_names = [class_name for _, class_name in entries]
    if len(labels) != len(set(labels)):
        raise ValueError("Class map contains duplicate class IDs.")
    if any(not name.strip() for name in target_names):
        raise ValueError("Class map contains an empty class name.")
    return labels, target_names


def _is_integer_like(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        return int(value) == float(value)
    except (TypeError, ValueError, OverflowError):
        return False


def _as_label_array(values: Iterable[int], input_name: str) -> np.ndarray:
    if hasattr(values, "detach"):
        values = values.detach().cpu().numpy()
    array = np.asarray(values)
    if array.ndim != 1:
        raise ValueError(f"{input_name} must be a one-dimensional sequence of class IDs.")
    if array.size == 0:
        return array.astype(np.int64)
    if not np.all([_is_integer_like(value) for value in array.tolist()]):
        raise ValueError(f"{input_name} must contain only integer class IDs.")
    return array.astype(np.int64)


def _validated_inputs(
    y_true: Iterable[int],
    y_pred: Iterable[int],
    labels: list[int],
) -> tuple[np.ndarray, np.ndarray]:
    true_array = _as_label_array(y_true, "y_true")
    pred_array = _as_label_array(y_pred, "y_pred")
    if true_array.size == 0 or pred_array.size == 0:
        raise ValueError("y_true and y_pred must not be empty.")
    if true_array.size != pred_array.size:
        raise ValueError(
            f"y_true and y_pred must have the same length; got "
            f"{true_array.size} and {pred_array.size}."
        )

    valid_labels = set(labels)
    unknown = sorted((set(true_array.tolist()) | set(pred_array.tolist())) - valid_labels)
    if unknown:
        raise ValueError(f"Unknown class ID(s): {unknown}. Valid class IDs: {labels}.")
    return true_array, pred_array


def compute_metrics(
    y_true: Iterable[int],
    y_pred: Iterable[int],
    class_map_path: str | Path = DEFAULT_CLASS_MAP,
) -> dict[str, Any]:
    """Compute classification metrics over every class in the class map."""
    labels, target_names = load_class_map(class_map_path)
    true_array, pred_array = _validated_inputs(y_true, y_pred, labels)

    report = classification_report(
        true_array,
        pred_array,
        labels=labels,
        target_names=target_names,
        zero_division=0,
        output_dict=True,
    )
    report_text = classification_report(
        true_array,
        pred_array,
        labels=labels,
        target_names=target_names,
        zero_division=0,
    )
    matrix = confusion_matrix(true_array, pred_array, labels=labels)

    return {
        "accuracy": float(accuracy_score(true_array, pred_array)),
        "macro_precision": float(
            precision_score(
                true_array,
                pred_array,
                labels=labels,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_recall": float(
            recall_score(
                true_array,
                pred_array,
                labels=labels,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_f1": float(
            f1_score(
                true_array,
                pred_array,
                labels=labels,
                average="macro",
                zero_division=0,
            )
        ),
        "classification_report": report,
        "classification_report_str": report_text,
        "confusion_matrix": matrix,
        "labels": labels,
        "target_names": target_names,
    }


def plot_confusion_matrix(
    y_true: Iterable[int],
    y_pred: Iterable[int],
    output_path: str | Path | None = None,
    class_map_path: str | Path = DEFAULT_CLASS_MAP,
    title: str = "Confusion Matrix (normalized by true label)",
) -> tuple[plt.Figure, np.ndarray]:
    """Plot a row-normalized confusion matrix with all project classes."""
    labels, target_names = load_class_map(class_map_path)
    true_array, pred_array = _validated_inputs(y_true, y_pred, labels)
    matrix = confusion_matrix(true_array, pred_array, labels=labels)

    row_sums = matrix.sum(axis=1, keepdims=True)
    normalized = np.divide(
        matrix.astype(float),
        row_sums,
        out=np.zeros_like(matrix, dtype=float),
        where=row_sums != 0,
    )

    figure_width = max(10, len(labels) * 1.25)
    fig, ax = plt.subplots(figsize=(figure_width, 8))
    sns.heatmap(
        normalized,
        annot=True,
        fmt=".2f",
        cmap="Blues",
        vmin=0,
        vmax=1,
        xticklabels=target_names,
        yticklabels=target_names,
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Row-normalized proportion"},
        ax=ax,
    )
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=160, bbox_inches="tight")
    return fig, matrix
