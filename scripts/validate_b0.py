"""Reload saved B0 checkpoint and rerun validation without touching test."""

import argparse
import json
from pathlib import Path
import sys

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.b0_dataset import FullImageDataset, make_transform, read_rows  # noqa: E402
from src.evaluation.metrics import load_class_map  # noqa: E402
from src.models.b0 import build_b0  # noqa: E402
from src.training.b0 import evaluate, simple_metrics  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "experiments" / "B0_run01" / "checkpoints" / "best_model.pth")
    args = parser.parse_args()
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    config = checkpoint["config"]
    if config["data"]["test_used_for_selection"] is not False:
        raise ValueError("Checkpoint config violates test isolation")
    run_dir = ROOT / "experiments" / config["experiment"]["id"]
    class_map = ROOT / config["data"]["class_map"]
    labels, names = load_class_map(class_map)
    if labels != list(range(len(names))) or checkpoint["class_to_idx"] != {name: index for index, name in enumerate(names)}:
        raise ValueError("Checkpoint class map mismatch")
    rows = read_rows(run_dir / "used_val.jsonl", "val", names)
    model = build_b0(len(names), pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    loader = DataLoader(FullImageDataset(rows, ROOT / config["data"]["image_root"], make_transform(config, False)), batch_size=config["data"]["batch_size"], shuffle=False, num_workers=config["data"]["num_workers"])
    metrics, actual, _, loss = evaluate(model, loader, device, class_map)
    saved = checkpoint["validation_metrics"]
    differences = {key: abs(metrics[key] - saved[key]) for key in saved}
    if any(value > 1e-9 for value in differences.values()):
        raise RuntimeError(f"Reload mismatch: {differences}")
    print(json.dumps({"reload": "PASS", "epoch": checkpoint["epoch"], "samples": len(actual), "metrics": simple_metrics(metrics), "val_loss": loss, "metric_absolute_differences": differences}, indent=2))


if __name__ == "__main__":
    main()
