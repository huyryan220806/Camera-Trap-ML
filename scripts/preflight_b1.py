"""Validate TV1 native train/validation handoff independently of training approval."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.training.b1_gate import validate_config, verify_data
from src.training.tv1_handoff import load_handoff


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/b1_comparison_v1.pending.yaml")
    parser.add_argument("--metadata-only", action="store_true", help="Do not claim image preflight PASS")
    parser.add_argument("--report", type=Path, help="New report path; existing files are never overwritten")
    args = parser.parse_args()
    if args.report and args.report.exists():
        parser.error("Report exists; choose a new evidence path")
    result = {"official_training_authorized": False, "test_rows_opened": False}
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        validate_config(config)
        receipt = load_handoff(config["data"]["tv1_handoff"], ROOT)
        _, _, _, proof = verify_data(receipt, ROOT, ROOT / config["data"]["image_root"], config["model"]["num_classes"], inspect=not args.metadata_only)
        result.update(status="METADATA PASS - IMAGES NOT CHECKED" if args.metadata_only else "REAL DATA PREFLIGHT PASS",
                      source_commit=receipt["binding"]["commit"], provenance_sha256=receipt["provenance_sha256"], proof=proof)
    except Exception as exc:
        result.update(status="FAIL", error=f"{type(exc).__name__}: {exc}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result["status"] == "FAIL")


if __name__ == "__main__":
    raise SystemExit(main())
