"""Read-only validation: pinned checkpoint hash and frozen provenance required."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.training.b1 import validate_checkpoint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_checkpoint(args.checkpoint, args.sha256), indent=2))
    except (ValueError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
