"""Shared evaluation helpers for CameraTrapML experiments."""

from importlib import import_module

__all__ = [
    "compute_metrics",
    "load_class_map",
    "plot_confusion_matrix",
    "compute_classification_metrics",
    "aggregate_image_predictions",
    "evaluate_b2_model",
    "format_validation_markdown_table",
]


def __getattr__(name):
    # Keep TV2 metrics usable without importing the optional TV3 torch runtime.
    if name not in __all__:
        raise AttributeError(name)
    module = ".metrics" if name in __all__[:3] else ".b2_evaluator"
    return getattr(import_module(module, __name__), name)
