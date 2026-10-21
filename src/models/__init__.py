"""Model definitions for TV2 and TV3 experiments."""

from importlib import import_module

__all__ = ["B2CropClassifier", "save_checkpoint", "load_checkpoint"]


def __getattr__(name):
    if name not in __all__:
        raise AttributeError(name)
    return getattr(import_module(".b2_classifier", __name__), name)
