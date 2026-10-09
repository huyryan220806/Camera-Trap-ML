"""Reload saved B0 checkpoint and rerun validation without touching test."""

import argparse
import json
from pathlib import Path
import sys

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.b0_dataset import FullImageDataset, make_transform  # noqa: E402
from src.models.b0 import build_b0  # noqa: E402
from src.training.b0 import evaluate, simple_metrics  # noqa: E402
from src.training.provenance import verify_validation_provenance  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "experiments" / "B0_run01" / "checkpoints" / "best_model.pth")
    args = parser.parse_args()
    result = validate_checkpoint(args.checkpoint)
    print(json.dumps(result, indent=2))


def validate_checkpoint(checkpoint_path: Path, *, root: Path = ROOT) -> dict:
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    config = checkpoint["config"]
    rows, names, class_map, provenance = verify_validation_provenance(checkpoint, root)
    model = build_b0(len(names), pretrained=False)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    loader = DataLoader(FullImageDataset(rows, root / config["data"]["image_root"], make_transform(config, False), project_root=root), batch_size=config["data"]["batch_size"], shuffle=False, num_workers=config["data"]["num_workers"])
    metrics, actual, _, loss = evaluate(model, loader, device, class_map)
    saved = simple_metrics(checkpoint["validation_metrics"])
    differences = {key: abs(metrics[key] - saved[key]) for key in saved}
    if any(value > 1e-9 for value in differences.values()):
        raise RuntimeError(f"Reload mismatch: {differences}")
    return {"provenance": provenance, "reload": "PASS", "epoch": checkpoint["epoch"], "samples": len(actual), "metrics": simple_metrics(metrics), "val_loss": loss, "metric_absolute_differences": differences}


if __name__ == "__main__":
    main()
