"""Train and verify B0 using only TV1's fixed train and validation splits."""

import csv
import gc
import hashlib
import json
import platform
from pathlib import Path
import random
import subprocess

import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision
from torch import nn
from torch.utils.data import DataLoader

from src.data.b0_dataset import FullImageDataset, inspect_images, make_transform, read_rows
from src.evaluation.metrics import compute_metrics, load_class_map, plot_confusion_matrix
from src.models.b0 import build_b0, parameter_counts

ROOT = Path(__file__).resolve().parents[2]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def paths_from_config(config: dict) -> tuple[Path, Path, Path]:
    run_dir = ROOT / "experiments" / config["experiment"]["id"]
    return run_dir, ROOT / config["data"]["class_map"], ROOT / config["data"]["image_root"]


def prepare_data(config: dict, run_dir: Path, class_names: list[str]) -> tuple[dict, dict]:
    image_root = ROOT / config["data"]["image_root"]
    all_rows, valid_rows, errors = {}, {}, []
    source_rows = {}
    with (ROOT / config["data"]["source_manifest"]).open(encoding="utf-8") as source:
        for line in source:
            if line.strip():
                row = json.loads(line)
                if row.get("split") in ("train", "val"):
                    if row["image_id"] in source_rows:
                        raise ValueError(f"Duplicate image_id in source pilot: {row['image_id']}")
                    source_rows[row["image_id"]] = row
    for split in ("train", "val"):
        source = ROOT / config["data"].get("train_manifest" if split == "train" else "validation_manifest", str((run_dir / f"selected_{split}.jsonl").relative_to(ROOT)))
        rows = read_rows(source, split, class_names)
        if any(source_rows.get(row["image_id"]) != row for row in rows):
            raise ValueError(f"Selected {split} manifest differs from TV1 pilot")
        all_rows[split] = rows
        valid_rows[split], split_errors = inspect_images(rows, image_root)
        errors.extend(split_errors)
        if {row["class_id"] for row in valid_rows[split]} != set(range(len(class_names))):
            raise ValueError(f"Missing an entire class in usable {split} images")
        (run_dir / f"used_{split}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in valid_rows[split]), encoding="utf-8")
    if {row["image_id"] for row in all_rows["train"]} & {row["image_id"] for row in all_rows["val"]}:
        raise ValueError("Selected train and validation image IDs overlap")
    (run_dir / "image_errors.json").write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8")
    counts = {split: {"selected": len(all_rows[split]), "usable": len(valid_rows[split]), "excluded": len(all_rows[split]) - len(valid_rows[split])} for split in ("train", "val")}
    return valid_rows, counts


def make_loaders(config: dict, rows: dict, *, seed: int) -> tuple[DataLoader, DataLoader]:
    image_root = ROOT / config["data"]["image_root"]
    data_cfg = config["data"]
    generator = torch.Generator().manual_seed(seed)
    train = DataLoader(FullImageDataset(rows["train"], image_root, make_transform(config, True)), batch_size=data_cfg["batch_size"], shuffle=True, num_workers=data_cfg["num_workers"], generator=generator)
    val = DataLoader(FullImageDataset(rows["val"], image_root, make_transform(config, False)), batch_size=data_cfg["batch_size"], shuffle=False, num_workers=data_cfg["num_workers"])
    return train, val


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, class_map: Path) -> tuple[dict, list[int], list[int], float]:
    model.eval()
    actual, predicted = [], []
    loss_sum = 0.0
    criterion = nn.CrossEntropyLoss()
    with torch.inference_mode():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            loss_sum += criterion(logits, labels).item() * labels.numel()
            actual.extend(labels.cpu().tolist())
            predicted.extend(logits.argmax(dim=1).cpu().tolist())
    metrics = compute_metrics(actual, predicted, class_map)
    return metrics, actual, predicted, loss_sum / len(actual)


def simple_metrics(metrics: dict) -> dict:
    return {key: metrics[key] for key in ("macro_f1", "macro_precision", "macro_recall", "accuracy")}


def write_validation_results(run_dir: Path, metrics: dict, actual: list[int], predicted: list[int], best_epoch: int, train_loss: float, val_loss: float, class_map: Path) -> None:
    results = run_dir / "results"
    results.mkdir(parents=True, exist_ok=True)
    payload = {**simple_metrics(metrics), "best_epoch": best_epoch, "train_loss": train_loss, "val_loss": val_loss, "per_class": metrics["classification_report"], "confusion_matrix": metrics["confusion_matrix"].tolist(), "support": len(actual)}
    (results / "val_metrics.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with (results / "val_metrics.csv").open("w", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination)
        writer.writerow(["metric", "value"])
        for key, value in simple_metrics(metrics).items():
            writer.writerow([key, value])
    figure, _ = plot_confusion_matrix(actual, predicted, results / "confusion_matrix.png", class_map, "B0 validation confusion matrix")
    plt.close(figure)


def plot_learning_curves(run_dir: Path) -> None:
    with (run_dir / "logs" / "train_log.csv").open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    epochs = [int(row["epoch"]) for row in rows]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(epochs, [float(row["train_loss"]) for row in rows], label="Train loss")
    axes[0].plot(epochs, [float(row["val_loss"]) for row in rows], label="Validation loss")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()
    axes[1].plot(epochs, [float(row["val_macro_f1"]) for row in rows], label="Validation macro-F1")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylim(0, 1)
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(run_dir / "results" / "learning_curves.png", dpi=160)
    plt.close(figure)


def verify_checkpoint(checkpoint_path: Path, config: dict, rows: list[dict], class_names: list[str], saved_metrics: dict, device: torch.device, class_map: Path) -> dict:
    if not checkpoint_path.is_file() or checkpoint_path.stat().st_size <= 0:
        raise RuntimeError("Best B0 checkpoint missing or empty")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    expected_mapping = {name: index for index, name in enumerate(class_names)}
    if checkpoint["class_to_idx"] != expected_mapping or checkpoint["idx_to_class"] != {index: name for index, name in enumerate(class_names)}:
        raise RuntimeError("Checkpoint class map differs from project class map")
    if checkpoint["model_name"] != "resnet18" or not checkpoint["freeze_backbone"]:
        raise RuntimeError("Checkpoint is not a frozen B0 ResNet18")
    reloaded = build_b0(len(class_names), pretrained=False).to(device)
    reloaded.load_state_dict(checkpoint["model_state_dict"], strict=True)
    val_loader = DataLoader(FullImageDataset(rows, ROOT / config["data"]["image_root"], make_transform(config, False)), batch_size=config["data"]["batch_size"], shuffle=False, num_workers=config["data"]["num_workers"])
    reloaded_metrics, actual, predicted, val_loss = evaluate(reloaded, val_loader, device, class_map)
    del reloaded
    gc.collect()
    difference = {key: abs(reloaded_metrics[key] - saved_metrics[key]) for key in simple_metrics(saved_metrics)}
    if any(delta > 1e-9 for delta in difference.values()):
        raise RuntimeError(f"Reloaded validation metrics differ from saved metrics: {difference}")
    result = {"checkpoint_path": str(checkpoint_path), "checkpoint_bytes": checkpoint_path.stat().st_size, "checkpoint_sha256": file_sha256(checkpoint_path), "checkpoint_epoch": checkpoint["epoch"], "reload_successful": True, "metric_absolute_differences": difference, "validation_metrics": simple_metrics(reloaded_metrics), "val_loss": val_loss, "support": len(actual)}
    return result


def train(config_path: Path, *, smoke: bool = False) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["data"]["test_used_for_selection"] is not False or config["model"]["freeze_backbone"] is not True:
        raise ValueError("B0 must freeze backbone and exclude test")
    if config["training"]["checkpoint_metric"] != "macro_f1":
        raise ValueError("B0 must select by validation macro-F1")
    run_dir, class_map, _ = paths_from_config(config)
    run_dir.mkdir(parents=True, exist_ok=True)
    labels, class_names = load_class_map(class_map)
    if labels != list(range(len(labels))) or len(labels) != config["model"]["num_classes"]:
        raise ValueError("B0 config does not match class map")
    set_seed(config["experiment"]["seed"])
    torch.set_num_threads(min(4, torch.get_num_threads()))
    torch.hub.set_dir(str(ROOT / "data" / "images" / "torch" / "hub"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows, counts = prepare_data(config, run_dir, class_names)
    train_loader, val_loader = make_loaders(config, rows, seed=config["experiment"]["seed"])
    model = build_b0(len(class_names), pretrained=True).to(device)
    counts_params = parameter_counts(model)
    print(f"B0 parameters: {counts_params}; device={device}; samples={counts}", flush=True)
    optimizer = torch.optim.Adam(model.fc.parameters(), lr=config["training"]["lr"], weight_decay=config["training"]["weight_decay"])
    criterion = nn.CrossEntropyLoss()
    checkpoint_path = run_dir / "checkpoints" / "best_model.pth"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    if smoke:
        model.eval()  # Frozen backbone and BatchNorm running statistics stay fixed.
        images, labels_batch = next(iter(train_loader))
        optimizer.zero_grad(set_to_none=True)
        loss = criterion(model(images.to(device)), labels_batch.to(device))
        loss.backward()
        if model.fc.weight.grad is None or any(p.grad is not None for name, p in model.named_parameters() if not name.startswith("fc.")):
            raise RuntimeError("Smoke backward violated frozen-backbone policy")
        optimizer.step()
        val_images, _ = next(iter(val_loader))
        with torch.inference_mode():
            model(val_images.to(device))
        smoke_path = checkpoint_path.parent / "smoke_temp.pth"
        torch.save({"model_state_dict": model.state_dict()}, smoke_path)
        fresh = build_b0(len(class_names), pretrained=False)
        fresh.load_state_dict(torch.load(smoke_path, map_location="cpu", weights_only=True)["model_state_dict"])
        smoke_path.unlink()
        (run_dir / "smoke_result.json").write_text(json.dumps({"status": "PASS", "train_batch": len(labels_batch), "validation_batch": len(val_images), "forward_backward": True, "checkpoint_save_load": True, "parameter_counts": counts_params, "device": str(device), "samples": counts}, indent=2), encoding="utf-8")
        print("B0 smoke test PASS", flush=True)
        return
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    config["experiment"]["git_commit"] = commit
    config["environment"] = {"python": platform.python_version(), "torch": str(torch.__version__), "torchvision": str(torchvision.__version__), "cuda_version": torch.version.cuda, "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "device": str(device)}
    config["dataset"] = {"samples": counts, "source_manifest_sha256": file_sha256(ROOT / config["data"]["source_manifest"]), "train_manifest_sha256": file_sha256(run_dir / "used_train.jsonl"), "validation_manifest_sha256": file_sha256(run_dir / "used_val.jsonl"), "class_map_sha256": file_sha256(class_map)}
    config["model"]["parameter_counts"] = counts_params
    (run_dir / "config.yaml").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    log_path = run_dir / "logs" / "train_log.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    best = -1.0
    best_metrics = None
    best_actual = best_predicted = None
    best_epoch = 0
    best_train_loss = best_val_loss = None
    stale = 0
    with log_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=["epoch", "train_loss", "val_loss", "val_macro_f1", "val_macro_precision", "val_macro_recall", "val_accuracy", "learning_rate"])
        writer.writeheader()
        for epoch in range(1, config["training"]["epochs"] + 1):
            model.eval()  # Keep BatchNorm running state frozen along with backbone weights.
            total_loss = 0.0
            total_samples = 0
            for images, targets in train_loader:
                images, targets = images.to(device), targets.to(device)
                optimizer.zero_grad(set_to_none=True)
                outputs = model(images)
                loss = criterion(outputs, targets)
                loss.backward()
                optimizer.step()
                total_loss += loss.item() * targets.numel()
                total_samples += targets.numel()
            train_loss = total_loss / total_samples
            metrics, actual, predicted, val_loss = evaluate(model, val_loader, device, class_map)
            row = {"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss, "val_macro_f1": metrics["macro_f1"], "val_macro_precision": metrics["macro_precision"], "val_macro_recall": metrics["macro_recall"], "val_accuracy": metrics["accuracy"], "learning_rate": optimizer.param_groups[0]["lr"]}
            writer.writerow(row)
            destination.flush()
            print(json.dumps(row), flush=True)
            if metrics["macro_f1"] > best:
                best = metrics["macro_f1"]
                best_epoch = epoch
                best_metrics, best_actual, best_predicted = metrics, actual, predicted
                best_train_loss, best_val_loss = train_loss, val_loss
                stale = 0
                torch.save({"model_state_dict": model.state_dict(), "optimizer_state_dict": optimizer.state_dict(), "epoch": epoch, "best_val_macro_f1": best, "validation_metrics": simple_metrics(metrics), "class_to_idx": {name: index for index, name in enumerate(class_names)}, "idx_to_class": {index: name for index, name in enumerate(class_names)}, "num_classes": len(class_names), "model_name": "resnet18", "pretrained": "ImageNet-1K", "freeze_backbone": True, "seed": config["experiment"]["seed"], "config": config}, checkpoint_path)
            else:
                stale += 1
                if stale >= config["training"]["early_stopping_patience"]:
                    print(f"Early stopping at epoch {epoch}", flush=True)
                    break
    del model
    gc.collect()
    write_validation_results(run_dir, best_metrics, best_actual, best_predicted, best_epoch, best_train_loss, best_val_loss, class_map)
    plot_learning_curves(run_dir)
    reload_result = verify_checkpoint(checkpoint_path, config, rows["val"], class_names, best_metrics, device, class_map)
    (run_dir / "results" / "reload_validation.json").write_text(json.dumps(reload_result, indent=2), encoding="utf-8")
    print(json.dumps({"best_epoch": best_epoch, "best_macro_f1": best, "checkpoint": str(checkpoint_path), "reload": "PASS", "checkpoint_bytes": reload_result["checkpoint_bytes"]}), flush=True)
