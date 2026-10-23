"""Official TV2 W4 evaluation; default is a read-only fail-closed preflight."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation.w4_test import EvaluationBlocked, evaluate, verify_gate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "outputs/b2_crop_classifier/b2_run01/best_model.pt")
    parser.add_argument("--execute", action="store_true", help="Execute exactly the committed plan after all gates pass")
    args = parser.parse_args()
    selection = ROOT / "reports/tv2/TV2_W4_MODEL_SELECTION_LOCK.json"
    protocol = ROOT / "reports/tv2/TV2_W4_EVALUATION_PROTOCOL.json"
    try:
        if args.execute:
            run = evaluate(ROOT, selection, protocol, args.checkpoint)
            print(json.dumps({"status": "COMPLETE", "run": str(run)}))
        else:
            verify_gate(ROOT, selection, protocol, args.checkpoint)
            print(json.dumps({"status": "GATE PASS", "test_inference_performed": False}))
        return 0
    except (EvaluationBlocked, FileNotFoundError, KeyError, TypeError, json.JSONDecodeError) as exc:
        marker = ROOT / "outputs/tv2_w4/OFFICIAL_TEST_STARTED.json"
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "test_inference_performed": None if marker.exists() else False,
                          "official_run_reserved": marker.exists()}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
