"""Evaluate the delivered R6 epoch-13 checkpoint on the locked Train and Val splits."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json_once(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("package", "data-root", "vendor", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--check-only", action="store_true", help="Check inputs on CPU without model inference.")
    parser.add_argument("--booking", help="Confirmed GPU booking/device/time reference for inference.")
    args = parser.parse_args()
    if not args.check_only and not (args.booking or "").strip():
        parser.error("--booking is required for the GPU evaluation")
    package, root, vendor, output = (p.resolve() for p in (args.package, args.data_root, args.vendor, args.output))
    require(not output.exists(), "Use a fresh output directory")
    require(not output.is_relative_to(package) and not output.is_relative_to(root / "data"),
            "Place the output outside the package and data directories")

    repo = Path(__file__).resolve().parents[3]
    cfg_path = repo / "configs/w6/tv3/R6.3h.frozen.json"
    config = read_json(cfg_path)
    source = read_json(package / "source_index.json")
    binding = read_json(package / "binding.json")
    handoff = read_json(package / "handoff.json")
    val_path = package / "validation.json"
    checkpoint = package / "best_model.pt"
    checkpoint_sha = "24e3f51418dd7492a7537dff629794547c4540e8929bfe3e566105a6486581ef"
    require(config["run_id"] == handoff["run_id"] == "R6" and config["seed"] == handoff["seed"] == 43,
            "Wrong run or seed")
    require(sha256(checkpoint) == handoff["checkpoint_sha256"] == checkpoint_sha and handoff["best_epoch"] == 13,
            "Wrong R6 checkpoint")
    require(sha256(cfg_path) == sha256(package / "config.json") == handoff["config_raw_sha256"]
            == binding["config_file_raw_sha256"], "Frozen config bytes differ")
    require(sha256(val_path) == "0371900a5a743daf755b254d3b2b3e08ffd78d7160fb6b25b7322094bd228226",
            "Historical Validation changed")
    require(source == binding["source_index"] and source["commit"] == handoff["source_sha"]
            == config["runtime"]["source_sha"], "Source index differs")
    for name, expected in source["files_sha256"].items():
        path = (package / name).resolve()
        require(path.is_relative_to(package) and sha256(path) == expected, f"Source differs: {name}")

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(package))
    import torch
    from src.training import dino_probe as w5
    from src.training import dino_w6 as w6

    require(Path(w6.__file__).resolve() == package / "src/training/dino_w6.py"
            and Path(w5.__file__).resolve() == package / "src/training/dino_probe.py", "Wrong imported source")
    w6.validate_config(config)
    require(w6.digest(config) == handoff["config_sha256"] == binding["config_sha256"], "Canonical config differs")
    require(w5.git_revision(vendor) == config["vendor_commit"] == handoff["vendor_commit"], "Vendor revision differs")
    require(not subprocess.check_output(
        ["git", "-C", str(vendor), "status", "--porcelain", "--untracked-files=all"], text=True
    ).strip(), "Vendor checkout is dirty")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
    require(payload["epoch"] == 13 and payload["config"] == config and payload["binding"] == binding,
            "Checkpoint metadata differs")
    require(payload["class_map"] == binding["class_map"] == read_json(package / "class_map.json")
            and list(payload["class_map"].values()) == handoff["class_order"], "Class order differs")
    del payload

    rows, class_map, gate = w6.read_data(config, read_json(package / "registry.approved.json"), root=root)
    require(set(rows) == {"train", "val"} and class_map == binding["class_map"], "Unexpected population/class map")
    require(gate["files"] == binding["data"]["files"] and gate["expansion"] == binding["data"]["expansion"],
            "Manifest hashes differ")
    counts = {"train": (4246, 4729), "val": (600, 680)}
    populations = {}
    for split, crops in rows.items():
        image_ids = list(dict.fromkeys(row["image_id"] for row in crops))
        require((len(image_ids), len(crops)) == counts[split], f"Wrong population for {split}")
        require(w6.verify_pixels(crops, root) == len(image_ids), f"Pixel verification incomplete: {split}")
        manifest = ("data/processed/train_expansion_w6_v1/b2/train.jsonl" if split == "train"
                    else "data/processed/comparison_v1/b2/val.jsonl")
        populations[split] = {
            "n_images": len(image_ids), "n_crops": len(crops), "manifest": manifest,
            "manifest_sha256": sha256(root / manifest),
            "image_id_order_sha256": w6.digest(image_ids),
            "crop_id_order_sha256": w6.digest([row["crop_id"] for row in crops]),
        }
        print(f"{split}: verified {len(image_ids)} images and {len(crops)} crops", flush=True)

    output.mkdir(parents=True, exist_ok=False)
    evidence = {
        "checkpoint_sha256": checkpoint_sha, "epoch": 13, "seed": config["seed"],
        "config_raw_sha256": sha256(cfg_path), "config_sha256": w6.digest(config),
        "source_index_sha256": sha256(package / "source_index.json"), "source": source,
        "vendor_commit": config["vendor_commit"], "populations": populations, "test_opened": False,
    }
    if args.check_only:
        write_json_once(output / "input_preflight.json", {
            **evidence, "verified_utc": datetime.now(timezone.utc).isoformat(),
            "measurement_mode": "input_preflight_no_inference",
        })
        return

    runtime = w6.configure_runtime(config)
    require(sys.version_info[:3] == (3, 12, 10), "Expected Python 3.12.10")
    for key in ("torch", "torchvision", "pillow", "numpy", "sklearn", "cuda", "cudnn", "gpu",
                "num_threads", "num_interop_threads", "amp", "tf32", "deterministic_algorithms"):
        require(runtime[key] == binding["runtime"][key], f"Frozen runtime differs: {key}")
    require(torch.are_deterministic_algorithms_enabled() and not torch.backends.cuda.matmul.allow_tf32
            and not torch.backends.cudnn.allow_tf32, "Unexpected PyTorch compute settings")

    torch.cuda.synchronize()
    started_utc = datetime.now(timezone.utc).isoformat()
    start = perf_counter()
    print(f"GPU session started at {started_utc}", flush=True)
    model, _, loaded = w6.load_package(checkpoint, checkpoint_sha, vendor, "cuda")
    require(loaded["epoch"] == 13 and loaded["binding"] == binding, "Loaded checkpoint binding differs")
    del loaded
    require(not any(module.training for module in model.modules()), "A module remains in training mode")
    before = w6.cpu_state(model)
    results = {}
    for split in ("train", "val"):
        crops = rows[split]
        torch.cuda.synchronize()
        split_started = datetime.now(timezone.utc).isoformat()
        split_start = perf_counter()
        logits = w6.validation_logits(model, config, crops, "cuda", root=root)
        torch.cuda.synchronize()
        evaluation = w5.evaluate_logits(logits, crops, class_map)
        results[split] = {
            "started_utc": split_started, "ended_utc": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": perf_counter() - split_start, "metrics": evaluation["metrics"],
        }
        write_json_once(output / f"{split}_predictions.json", evaluation)
    after = w6.cpu_state(model)
    require(all(torch.equal(before[name], after[name]) for name in before), "Model parameters or buffers changed")
    torch.cuda.synchronize()
    seconds, ended_utc = perf_counter() - start, datetime.now(timezone.utc).isoformat()
    require(sha256(checkpoint) == checkpoint_sha, "Checkpoint file changed")

    frozen_val = read_json(val_path)
    fresh_val = read_json(output / "val_predictions.json")
    write_json_once(output / "checkpoint_eval.json", {
        **evidence, "measurement_mode": "fixed_checkpoint_eval_no_augmentation",
        "booking": args.booking, "started_utc": started_utc, "ended_utc": ended_utc,
        "session_seconds": seconds, "gpu_hours": seconds / 3600, "runtime": runtime,
        "runtime_sha256": w6.digest(runtime), "training_performed": False, "state_unchanged": True,
        "val_exact_vs_tv3": fresh_val == frozen_val,
        "splits": {
            split: {**result, "predictions_sha256": sha256(output / f"{split}_predictions.json")}
            for split, result in results.items()
        },
    })


if __name__ == "__main__":
    main()
