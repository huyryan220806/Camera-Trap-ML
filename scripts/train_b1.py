"""Official B1 entrypoint; --smoke uses generated images in a temporary directory."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.training.b1 import ROOT, smoke, train


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/b1.yaml")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(smoke(args.config) if args.smoke else train(args.config), indent=2))
    except (ValueError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
