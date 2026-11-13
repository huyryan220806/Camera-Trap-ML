"""Supplementary evaluation without changing a future training step's modes/RNG."""
from contextlib import contextmanager

from . import dino_probe as w5


@contextmanager
def preserved_eval(model):
    state = w5.rng_state()
    modes = [(module, module.training) for module in model.modules()]
    try:
        model.eval()
        yield
    finally:
        for module, mode in modes:
            module.training = mode
        w5.restore_rng(state)
