"""CLI for B0 training and its prerequisite smoke test."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.training.b0 import train  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "b0.yaml")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    train(args.config, smoke=args.smoke)
