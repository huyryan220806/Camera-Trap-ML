"""Non-destructive B0 provenance probes with synthetic images and an untrained model."""

import argparse
from contextlib import redirect_stdout
import copy
import hashlib
import importlib.util
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch


def write_rows(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve()))
    import torch
    from PIL import Image
    from src.training import b0
    from src.models.b0 import build_b0
    from src.evaluation.metrics import compute_metrics
    spec = importlib.util.spec_from_file_location("review_validate_b0", args.repo / "scripts/validate_b0.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    torch.set_num_threads(2)
    with tempfile.TemporaryDirectory(prefix="tv2-review-") as tmp:
        root = Path(tmp)
        run = root / "experiments/fixture"
        run.mkdir(parents=True)
        names = ["fixture_class_" + str(i) for i in range(8)]
        class_map = root / "class_map.json"
        class_map.write_text(json.dumps(dict(enumerate(names))))
        split_rows = {"train": [], "val": []}
        for split, count in (("train", 1), ("val", 2)):
            for class_id, label in enumerate(names):
                for index in range(count):
                    image_id = f"{split}-{class_id}-{index}"
                    Image.new("RGB", (32, 32), "red").save(root / f"{image_id}.jpg")
                    split_rows[split].append({"image_id": image_id, "split": split, "label": label,
                                              "class_id": class_id, "file_name": f"{image_id}.jpg"})
            write_rows(run / f"selected_{split}.jsonl", split_rows[split])
            write_rows(run / f"used_{split}.jsonl", split_rows[split])
        write_rows(root / "source.jsonl", split_rows["train"] + split_rows["val"])
        config = copy.deepcopy(json.loads((args.repo / "configs/b0.yaml").read_text()))
        config["experiment"]["id"] = "fixture"
        config["data"].update({"source_manifest": "source.jsonl", "image_root": ".", "class_map": "class_map.json",
            "train_manifest": "experiments/fixture/selected_train.jsonl", "validation_manifest": "experiments/fixture/selected_val.jsonl"})
        before = sha(run / "used_val.jsonl")
        (root / "val-0-1.jpg").unlink()
        with patch.object(b0, "ROOT", root):
            used, counts = b0.prepare_data(config, run, names)
        result = {"existing_run_manifest_overwritten": before != sha(run / "used_val.jsonl"),
                  "original_val_count": 16, "val_count_after_missing_image": len(used["val"]), "counts": counts,
                  "note": "prepare_data is called before the smoke branch and before full training; no training was run here."}

        config["dataset"] = {"validation_manifest_sha256": sha(run / "used_val.jsonl")}
        model = build_b0(8, pretrained=False)
        with torch.no_grad():
            model.fc.weight.zero_()
            model.fc.bias.zero_()
        saved_metrics = b0.simple_metrics(compute_metrics([r["class_id"] for r in used["val"]], [0] * len(used["val"]), class_map))
        checkpoint = root / "fixture.pth"
        torch.save({"config": config, "class_to_idx": {name: i for i, name in enumerate(names)},
                    "model_state_dict": model.state_dict(), "epoch": 1, "validation_metrics": saved_metrics}, checkpoint)
        used["val"][0]["image_id"] = "not-in-source-manifest"
        write_rows(run / "used_val.jsonl", used["val"])
        output = StringIO()
        with patch.object(validator, "ROOT", root), patch.object(sys, "argv", ["validate_b0.py", "--checkpoint", str(checkpoint)]), patch.object(torch.cuda, "is_available", return_value=False), redirect_stdout(output):
            validator.main()
        result["validation_hash_mismatch"] = sha(run / "used_val.jsonl") != config["dataset"]["validation_manifest_sha256"]
        result["validator_result_on_changed_image_id"] = json.loads(output.getvalue())
        result["scope"] = "Synthetic fixtures and untrained ResNet18 only; this does not reload or verify TV2's actual checkpoint."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
