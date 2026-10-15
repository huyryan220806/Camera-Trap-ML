"""B1 training with explicit official gates and isolated synthetic smoke runs."""

import copy
import csv
import gc
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import random
import subprocess
import tempfile
import time

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.utils.data import DataLoader
import torchvision

from src.data.b0_dataset import FullImageDataset, make_transform
from src.evaluation.metrics import plot_confusion_matrix
from src.models.b0 import parameter_counts
from src.models.b1 import build_b1
from src.training.b0 import evaluate, plot_learning_curves, set_seed, simple_metrics
from src.training.b1_gate import GateError, official_gate, relative_path, validate_config, verify_data
from src.training.run_artifacts import atomic_write_files, atomic_write_text, file_sha256, reserve_run

ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, value: dict) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def seed_worker(_worker_id: int) -> None:
    seed = torch.initial_seed() % 2**32
    random.seed(seed)
    np.random.seed(seed)


def make_loaders(config: dict, rows: dict, root: Path) -> tuple[DataLoader, DataLoader]:
    data = config["data"]
    loaders = []
    for split in ("train", "val"):
        generator = torch.Generator().manual_seed(config["experiment"]["seed"])
        dataset = FullImageDataset(rows[split], root / data["image_root"], make_transform(config, split == "train"), project_root=root)
        loaders.append(DataLoader(dataset, batch_size=data["batch_size"], shuffle=split == "train",
                                  num_workers=data["num_workers"], worker_init_fn=seed_worker,
                                  generator=generator, drop_last=False))
    return tuple(loaders)


def environment() -> dict:
    cuda = torch.cuda.is_available()
    return {"python": platform.python_version(), "torch": str(torch.__version__),
            "torchvision": str(torchvision.__version__), "cuda_available": cuda,
            "cuda_version": torch.version.cuda, "gpu_name": torch.cuda.get_device_name(0) if cuda else None,
            "platform": platform.platform()}


def sync(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def validate_checkpoint(checkpoint_path: Path, expected_sha256: str, *, root: Path = ROOT,
                        device: torch.device | None = None, expected_kind: str = "OFFICIAL") -> dict:
    if not expected_sha256 or file_sha256(checkpoint_path) != expected_sha256:
        raise GateError("Checkpoint SHA-256 mismatch")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint.get("kind") != expected_kind or checkpoint.get("model_name") != "resnet18" or checkpoint.get("freeze_backbone") is not False:
        raise GateError("Checkpoint is not the expected B1 experiment kind")
    config = checkpoint["config"]
    validate_config(config)
    receipt = checkpoint["freeze_receipt"]
    if expected_kind == "OFFICIAL":
        verified, _ = official_gate(config, root)
        if verified != receipt:
            raise GateError("Checkpoint freeze evidence differs")
    rows, names, class_map, proof = verify_data(receipt, root, root / config["data"]["image_root"], config["model"]["num_classes"])
    if (checkpoint["class_to_idx"] != {name: i for i, name in enumerate(names)}
            or checkpoint["idx_to_class"] != {i: name for i, name in enumerate(names)}
            or checkpoint["num_classes"] != len(names) or checkpoint["provenance"] != proof):
        raise GateError("Checkpoint class mapping/provenance mismatch")
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _, loader = make_loaders(config, rows, root)
    model = build_b1(len(names), pretrained=False).to(device)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    metrics, actual, predicted, loss = evaluate(model, loader, device, class_map)
    differences = {key: abs(metrics[key] - checkpoint["validation_metrics"][key]) for key in simple_metrics(metrics)}
    loss_delta = abs(loss - checkpoint["val_loss"])
    if (any(delta > 1e-9 for delta in differences.values()) or not math.isfinite(loss_delta)
            or loss_delta > 1e-6 or predicted != checkpoint["validation_predictions"]):
        raise GateError("Reloaded validation metrics, loss or predictions differ")
    batch, _ = next(iter(loader))
    with torch.inference_mode():
        logits = model(batch.to(device)).cpu()
    logit_delta = float((logits - checkpoint["validation_probe_logits"]).abs().max())
    if not torch.allclose(logits, checkpoint["validation_probe_logits"], atol=1e-6, rtol=1e-5):
        raise GateError("Reloaded logits differ")
    if file_sha256(checkpoint_path) != expected_sha256:
        raise GateError("Checkpoint changed during validation")
    return {"reload": "PASS", "kind": expected_kind, "checkpoint_sha256": expected_sha256,
            "checkpoint_bytes": checkpoint_path.stat().st_size, "best_epoch": checkpoint["epoch"],
            "metric_absolute_differences": differences, "val_loss_absolute_difference": loss_delta,
            "logits_max_absolute_difference": logit_delta, "validation_metrics": simple_metrics(metrics),
            "validation_samples": len(actual), "provenance": proof}


def _execute(config: dict, receipt: dict, root: Path, run: Path, device: torch.device, *, synthetic: bool) -> dict:
    started = time.perf_counter()
    kind = "SYNTHETIC_SMOKE" if synthetic else "OFFICIAL"
    write_json(run / "status.json", {"status": "RUNNING", "kind": kind})
    try:
        result = _fit(config, receipt, root, run, device, synthetic=synthetic)
    except BaseException as exc:
        write_json(run / "status.json", {"status": "INTERRUPTED" if isinstance(exc, KeyboardInterrupt) else "FAILED", "kind": kind, "error": str(exc), "resume_supported": False})
        raise
    result["total_seconds"] = time.perf_counter() - started
    write_json(run / "status.json", {"status": "COMPLETED", "kind": kind, **result})
    return result


def _fit(config: dict, receipt: dict, root: Path, run: Path, device: torch.device, *, synthetic: bool) -> dict:
    config = copy.deepcopy(config)
    rows, names, class_map, proof = verify_data(receipt, root, root / config["data"]["image_root"], config["model"]["num_classes"])
    set_seed(config["experiment"]["seed"])
    torch.set_num_threads(min(4, torch.get_num_threads()))
    train_loader, val_loader = make_loaders(config, rows, root)
    model = build_b1(len(names), pretrained=not synthetic).to(device)
    counts = parameter_counts(model)
    if counts["frozen"] != 0 or counts["trainable"] <= sum(p.numel() for p in model.fc.parameters()):
        raise RuntimeError("B1 must fine-tune the backbone")
    training = config["training"]
    optimizer = torch.optim.SGD([p for p in model.parameters() if p.requires_grad], lr=training["lr"], momentum=training["momentum"], weight_decay=training["weight_decay"])
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=training["step_size"], gamma=training["gamma"])
    criterion = nn.CrossEntropyLoss()
    config["environment"] = {**environment(), "actual_device": str(device)}
    config["parameter_counts"] = counts
    write_json(run / "config.yaml", config)  # JSON is a YAML subset, as in B0.
    write_json(run / "data_gate.json", proof)
    log = run / "logs/train_log.csv"
    log.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path = run / "checkpoints/best_model.pth"
    results = run / "results"
    results.mkdir()
    best, stale, best_epoch = -1.0, 0, 0
    training_seconds = validation_seconds = 0.0
    gradient_checked = False
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    fields = ["epoch", "train_loss", "val_loss", "val_macro_f1", "val_macro_precision", "val_macro_recall", "val_accuracy", "learning_rate", "train_seconds", "validation_seconds", "epoch_seconds", "peak_gpu_memory_bytes", "samples_seen", "batch_size", "last_batch_size"]
    with log.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for epoch in range(1, training["epochs"] + 1):
            sync(device)
            epoch_start = time.perf_counter()
            model.train()  # Fine-tuned BatchNorm affine params AND running stats.
            loss_sum, seen = 0.0, 0
            for images, targets in train_loader:
                images, targets = images.to(device), targets.to(device)
                optimizer.zero_grad(set_to_none=True)
                logits = model(images)
                if logits.shape != (len(targets), len(names)):
                    raise RuntimeError("Incorrect model output shape")
                loss = criterion(logits, targets)
                if not torch.isfinite(loss):
                    raise RuntimeError("Non-finite training loss")
                loss.backward()
                for name, parameter in model.named_parameters():
                    if parameter.requires_grad and (parameter.grad is None or not torch.isfinite(parameter.grad).all()):
                        raise RuntimeError(f"Missing/non-finite fine-tuning gradient: {name}")
                gradient_checked = True
                optimizer.step()
                loss_sum += loss.item() * targets.numel()
                seen += targets.numel()
                last_batch = targets.numel()
            sync(device)
            train_seconds = time.perf_counter() - epoch_start
            val_start = time.perf_counter()
            metrics, actual, predicted, val_loss = evaluate(model, val_loader, device, class_map)
            sync(device)
            val_seconds = time.perf_counter() - val_start
            if not math.isfinite(val_loss):
                raise RuntimeError("Non-finite validation loss")
            training_seconds += train_seconds
            validation_seconds += val_seconds
            peak = torch.cuda.max_memory_allocated(device) if device.type == "cuda" else None
            row = {"epoch": epoch, "train_loss": loss_sum / seen, "val_loss": val_loss,
                   **{f"val_{k}": v for k, v in simple_metrics(metrics).items()},
                   "learning_rate": optimizer.param_groups[0]["lr"], "train_seconds": train_seconds,
                   "validation_seconds": val_seconds, "epoch_seconds": train_seconds + val_seconds,
                   "peak_gpu_memory_bytes": peak, "samples_seen": seen,
                   "batch_size": config["data"]["batch_size"], "last_batch_size": last_batch}
            writer.writerow(row)
            stream.flush()
            if metrics["macro_f1"] > best:
                best, stale, best_epoch = metrics["macro_f1"], 0, epoch
                batch, _ = next(iter(val_loader))
                with torch.inference_mode():
                    probe = model(batch.to(device)).cpu()
                checkpoint = {"kind": "SYNTHETIC_SMOKE" if synthetic else "OFFICIAL", "model_name": "resnet18", "freeze_backbone": False,
                              "model_state_dict": model.state_dict(), "epoch": epoch, "best_val_macro_f1": best,
                              "validation_metrics": simple_metrics(metrics), "val_loss": val_loss,
                              "validation_predictions": predicted, "validation_probe_logits": probe,
                              "class_to_idx": {name: i for i, name in enumerate(names)}, "idx_to_class": dict(enumerate(names)),
                              "num_classes": len(names), "config": config, "freeze_receipt": receipt, "provenance": proof,
                              "pretrained_source": "NONE - synthetic fixture" if synthetic else "https://download.pytorch.org/models/resnet18-f37072fd.pth"}
                buffer = io.BytesIO()
                torch.save(checkpoint, buffer)
                atomic_write_files({checkpoint_path: buffer.getvalue()})
                del checkpoint, buffer
                payload = {**simple_metrics(metrics), "best_epoch": epoch, "val_loss": val_loss, "support": len(actual), "per_class": {name: metrics["classification_report"][name] for name in names}, "confusion_matrix": metrics["confusion_matrix"].tolist()}
                write_json(results / "val_metrics.json", payload)
                with (results / "per_class_metrics.csv").open("w", newline="", encoding="utf-8") as csvfile:
                    per_class = csv.DictWriter(csvfile, fieldnames=["label", "precision", "recall", "f1-score", "support"])
                    per_class.writeheader()
                    for name in names:
                        per_class.writerow({"label": name, **payload["per_class"][name]})
                figure, _ = plot_confusion_matrix(actual, predicted, results / "confusion_matrix.png", class_map, "B1 validation" if not synthetic else "SYNTHETIC smoke - not B1 results")
                plt.close(figure)
            else:
                stale += 1
            scheduler.step()
            if stale >= training["early_stopping_patience"]:
                break
    # Optimizer retains references: release it too before constructing the fresh model.
    del optimizer, scheduler, model, logits, loss
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
    digest = file_sha256(checkpoint_path)
    reloaded = validate_checkpoint(checkpoint_path, digest, root=root, device=device, expected_kind="SYNTHETIC_SMOKE" if synthetic else "OFFICIAL")
    write_json(results / "reload_validation.json", reloaded)
    plot_learning_curves(run)
    return {"epochs_completed": epoch, "best_epoch": best_epoch, "gradient_checked": gradient_checked,
            "training_seconds": training_seconds, "validation_seconds": validation_seconds,
            "peak_gpu_memory_bytes": peak, "parameter_counts": counts,
            "checkpoint_sha256": digest, "checkpoint_bytes": checkpoint_path.stat().st_size,
            "reload": reloaded["reload"], "metric_absolute_differences": reloaded["metric_absolute_differences"],
            "logits_max_absolute_difference": reloaded["logits_max_absolute_difference"]}


def train(config_path: Path, *, root: Path = ROOT) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    receipt, _ = official_gate(config, root)
    if not torch.cuda.is_available():
        raise GateError("BLOCKED - CUDA UNAVAILABLE; use --smoke on CPU")
    # Require committed code so git_commit actually identifies the executed pipeline.
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=all", "--", "src", "scripts", "configs", "requirements.txt", "requirements-tv2.txt"], cwd=root)
    if dirty.strip():
        raise GateError("Commit training code/config before official execution")
    config["code_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    verify_data(receipt, root, relative_path(root, config["data"]["image_root"]), config["model"]["num_classes"])
    smoke_result = smoke(config_path)  # mandatory fresh synthetic preflight
    config["smoke_preflight"] = smoke_result
    run = root / "experiments" / config["experiment"]["id"]
    if run.exists():
        raise FileExistsError("Run ID already exists. Use a new run ID; resume is not supported")
    reserve_run(run)
    return _execute(config, receipt, root, run, torch.device("cuda"), synthetic=False)


def create_fixture(root: Path, config: dict) -> dict:
    """Only generated images; never reads project manifests or historical runs."""
    (root / "images").mkdir()
    names = ["fixture_a", "fixture_b"]
    files = {}
    def save(name, value, *, lines=False):
        path = root / (name + (".jsonl" if lines else ".json"))
        path.write_text("".join(json.dumps(row) + "\n" for row in value) if lines else json.dumps(value), encoding="utf-8")
        files[name] = {"path": path.name, "sha256": file_sha256(path)}
    save("class_map", dict(enumerate(names)))
    for split in ("train", "val"):
        rows, crops = [], []
        for label in range(2):
            for index in range(2):
                image_id = f"{split}_{label}_{index}"
                rng = np.random.default_rng(100 * (split == "val") + 10*label + index)
                pixels = rng.integers(0, 255, (64, 64, 3), dtype=np.uint8)
                path = root / "images" / f"{image_id}.png"
                Image.fromarray(pixels).save(path)
                row = {"image_id": image_id, "file_name": path.name, "url": f"fixture://{image_id}", "seq_id": image_id, "location": f"{split}_{label}", "split": split, "class_id": label, "label": names[label], "width": 64, "height": 64,
                       "boxes": [{"annotation_id": image_id, "label": names[label], "bbox_xywh": [0, 0, 64, 64]}],
                       "quality": {"local_path": f"images/{path.name}", "sha256": file_sha256(path), "pixel_sha256": hashlib.sha256(b"RGB:64:64:" + pixels.tobytes()).hexdigest()}}
                rows.append(row)
                crops.append({"image_id": image_id, "annotation_id": image_id, "split": split, "class_id": label, "label": names[label], "bbox_xywh_original": [0, 0, 64, 64], "source_url": row["url"], "file_path": f"images/{path.name}", "sha256": file_sha256(path)})
        save(split, rows, lines=True)
        save(f"source_{split}", rows, lines=True)
        save(f"crop_{split}", crops, lines=True)
    save("excluded", [], lines=True)
    save("quality_audit", dict.fromkeys(["all_split_location_disjoint", "all_split_sequence_disjoint", "all_split_content_disjoint", "source_membership_verified", "box_review_passed"], True))
    return {"status": "SYNTHETIC_ONLY", "dataset_version": "synthetic_fixture", "files": files}


def smoke(config_path: Path) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(config)
    config["experiment"]["id"] = "B1_synthetic_smoke"
    config["model"]["num_classes"] = 2
    config["data"].update(image_root="images", batch_size=2, image_size=32, resize_size=40, num_workers=0)
    config["training"].update(epochs=2, early_stopping_patience=2)
    with tempfile.TemporaryDirectory(prefix="B1_synthetic_") as directory:
        root = Path(directory)
        receipt = create_fixture(root, config)
        run = root / "run"
        reserve_run(run)
        result = _execute(config, receipt, root, run, torch.device("cpu"), synthetic=True)
    return {"status": "PASS", "kind": "SYNTHETIC_SMOKE", "device": "cpu", "pretrained_weights": False,
            "temporary_artifacts_removed": True, "official_training": False, **result}
