"""TV2: verify a delivered B2/B3 checkpoint on frozen Train/Validation only.

No Test manifest or Test raster is opened by this entry point. Each CLI invocation
loads one checkpoint in a fresh process and writes a new, non-overwritable report.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation.w4_test import B2_SHA256, PREPROCESSING, aggregate_predictions, digest, metrics_and_integrity, read_rows

PROVENANCE = "d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f"
TV3_COMMIT = "65b99b9def6a147abe6a4d436c18a067f3f37dc4"
DELIVERED_B3_SHA256 = "93ae48dd4b42fa6062daed3a9a1869d620bd7ba9e7ae2aa274085b061f76300b"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                                     allow_nan=False).encode("utf-8")).hexdigest()


def crop_class_weights(samples):
    """The reviewed TV3 crop-frequency definition, normalized to arithmetic mean 1."""
    counts = Counter(row["class_id"] for row in samples)
    require(set(counts) == set(range(8)), "Train must contain all eight classes")
    raw = [len(samples) / (8 * counts[c]) for c in range(8)]
    mean = sum(raw) / 8
    return [weight / mean for weight in raw]


def verify_metadata(checkpoint, expected_config, mapping, model_name):
    require(checkpoint.get("is_official") is True, "Checkpoint is not marked official")
    require(checkpoint.get("backbone_name") == "resnet18" and checkpoint.get("num_classes") == 8,
            "Wrong architecture/class count")
    require(checkpoint.get("epoch") == {"B2": 21, "B3": 14}[model_name], "Best epoch differs from handoff")
    require(checkpoint.get("provenance_sha256") == PROVENANCE, "Wrong frozen provenance")
    require(checkpoint.get("class_map") == {label: int(i) for i, label in mapping.items()}, "Class map mismatch")
    require({str(k): v for k, v in checkpoint.get("id_to_label", {}).items()} == mapping, "ID mapping mismatch")
    require(checkpoint.get("config") == expected_config, "Embedded config differs from the pinned TV3 config")
    prep = checkpoint.get("preprocessing", {})
    require(prep.get("resize") == 256 and prep.get("crop_size") == 224 and
            prep.get("mean") == PREPROCESSING["mean"] and prep.get("std") == PREPROCESSING["std"] and
            prep.get("val_transforms") == "Resize(256) -> CenterCrop(224) -> ToTensor() -> Normalize()",
            "Unsupported preprocessing")


def validation_reference_checks(metrics, cm, stored, published, actual_errors):
    """Keep exact CM/error identity checks even when rounded macro scores agree."""
    return {
        "checkpoint_cm_matches": cm == stored["confusion_matrix"],
        "checkpoint_rounded_metrics_match": all(round(value, 4) == stored[key] for key, value in metrics.items()),
        "published_cm_matches": cm == published["confusion_matrix"]["matrix"],
        "published_error_ids_and_labels_match": actual_errors == {
            r["image_id"]: (r["true_class_id"], r["predicted_class_id"]) for r in published["misclassified_images"]},
    }


def verify(model_name, checkpoint_path, output, device_name="cpu"):
    import torch
    from torch.utils.data import DataLoader
    from src.data.b2_dataset import B2ComparisonDataset, b2_collate_fn
    from src.models.b2_classifier import B2CropClassifier
    from src.demo.classifier import checkpoint_model
    require(device_name in ("cpu", "cuda"), "Unsupported Validation device")
    require(device_name != "cuda" or torch.cuda.is_available(), "Requested CUDA runtime is unavailable; no fallback")
    device = torch.device(device_name)

    require(not output.exists(), "Never overwrite a checkpoint verification report")
    require(checkpoint_path.is_file(), "Delivered checkpoint missing")
    before = digest(checkpoint_path)
    expected_sha = B2_SHA256 if model_name == "B2" else DELIVERED_B3_SHA256
    require(before == expected_sha, "Delivered checkpoint checksum differs")
    require(checkpoint_path.stat().st_size == (89548866 if model_name == "B2" else 89548994), "Checkpoint size differs")
    comp = ROOT / "data/processed/comparison_v1"
    require(digest(comp / "provenance.json") == PROVENANCE, "Frozen provenance changed")
    provenance = json.loads((comp / "provenance.json").read_text(encoding="utf-8"))
    # Deliberately do not open or hash Test manifests here: only Train/Validation views.
    for name in ("train.jsonl", "val.jsonl", "b1/train.jsonl", "b1/val.jsonl", "b2/train.jsonl", "b2/val.jsonl", "class_map.json"):
        require(digest(comp / name) == provenance["files_sha256"][name], "Frozen Train/Val input changed: " + name)
    mapping = json.loads((comp / "class_map.json").read_text(encoding="utf-8"))
    require(set(mapping) == {str(i) for i in range(8)}, "Expected fixed class IDs 0-7")
    config_name = "b2_crop_classifier.json" if model_name == "B2" else "b3_class_weighted.json"
    config_bytes = subprocess.check_output(["git", "show", f"{TV3_COMMIT}:configs/{config_name}"], cwd=ROOT)
    expected_config = json.loads(config_bytes)
    torch.set_num_threads(4)
    torch.manual_seed(42)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    started = time.perf_counter()
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    verify_metadata(checkpoint, expected_config, mapping, model_name)
    require(all(torch.is_tensor(t) and torch.isfinite(t).all().item() for t in checkpoint["model_state_dict"].values()),
            "Invalid checkpoint tensors")
    native = B2CropClassifier(8, "resnet18", pretrained=False, dropout_p=0).eval().requires_grad_(False)
    native.load_state_dict(checkpoint["model_state_dict"], strict=True)
    entry = {"checkpoint_format": "tv3-native-v1", "training_input": "crop", "preprocessing": PREPROCESSING,
             "provenance_sha256": PROVENANCE}
    adapter, transform = checkpoint_model(checkpoint, "B2", entry, [mapping[str(i)] for i in range(8)])
    native.to(device)
    adapter.to(device)
    load_seconds = time.perf_counter() - started
    datasets = {split: B2ComparisonDataset(split, comp / "b2" / f"{split}.jsonl", comp / "class_map.json",
                                           root=ROOT, preflight_hash_check=True) for split in ("train", "val")}
    for split, dataset in datasets.items():
        parents = read_rows(comp / f"{split}.jsonl")
        b1 = read_rows(comp / "b1" / f"{split}.jsonl")
        require({row["image_id"]: row["class_id"] for row in parents} ==
                {row["image_id"]: row["class_id"] for row in dataset.samples} ==
                {row["image_id"]: row["class_id"] for row in b1}, "Parent population mismatch")
    require(Counter(row["class_id"] for row in read_rows(comp / "train.jsonl")) == dict.fromkeys(range(8), 350),
            "Train parent-image balance differs")
    first = datasets["val"].samples[0]
    from PIL import Image
    with Image.open(ROOT / first["quality"]["local_path"]) as im:
        adapter_tensor = transform(im.convert("RGB").crop(tuple(first["bbox_xyxy"])))
    require(torch.equal(adapter_tensor, datasets["val"][0]["image"]), "Native/adapter transform differs")
    loader = DataLoader(datasets["val"], batch_size=32, shuffle=False, drop_last=False, num_workers=0, collate_fn=b2_collate_fn)
    crop_records, max_logit_delta = [], 0.
    loss_sum, weight_sum = 0., 0.
    inference_start = time.perf_counter()
    with torch.inference_mode():
        for batch in loader:
            images = batch["images"].to(device)
            logits = native(images)
            adapter_logits = adapter(images)
            max_logit_delta = max(max_logit_delta, float((logits - adapter_logits).abs().max().item()))
            require(logits.shape == (len(batch["images"]), 8) and torch.isfinite(logits).all().item(), "Invalid Validation logits")
            weights = batch["sample_weights"].to(device)
            ce = torch.nn.functional.cross_entropy(logits, batch["class_ids"].to(device), reduction="none")
            loss_sum += float((ce * weights).sum().item())
            weight_sum += float(weights.sum().item())
            probs = logits.softmax(dim=1).cpu().tolist()
            for cid, iid, cls, p in zip(batch["crop_ids"], batch["image_ids"], batch["class_ids"].tolist(), probs):
                crop_records.append({"crop_id": cid, "image_id": iid, "class_id": cls, "probabilities": p})
    require(max_logit_delta <= 1e-6, "Native and inference adapter logits differ")
    predictions = aggregate_predictions(crop_records, datasets["val"].samples)
    parents = {row["image_id"]: row for row in read_rows(comp / "val.jsonl")}
    metrics, cm, per_class = metrics_and_integrity(predictions, parents, comp / "class_map.json")
    stored = checkpoint["val_metrics"]["image_level"]
    error_analysis_bytes = subprocess.check_output(["git", "show", f"{TV3_COMMIT}:reports/tv3/error_analysis_{model_name.lower()}.json"], cwd=ROOT)
    published = json.loads(error_analysis_bytes)
    require(published["metadata"]["evaluation_split"] == "val", "TV3 analysis not labelled Validation")
    published_errors = {r["image_id"]: (r["true_class_id"], r["predicted_class_id"]) for r in published["misclassified_images"]}
    actual_errors = {r["image_id"]: (r["true_class_id"], r["predicted_class_id"]) for r in predictions
                     if r["true_class_id"] != r["predicted_class_id"]}
    require(digest(checkpoint_path) == before, "Checkpoint changed during verification")
    validation_checks = validation_reference_checks(metrics, cm, stored, published, actual_errors)
    passed = all(validation_checks.values())
    summary = {"status": "PASS" if passed else "FAIL", "model": model_name, "checked_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint_path": str(checkpoint_path.resolve()), "checkpoint_sha256": before, "checkpoint_bytes": checkpoint_path.stat().st_size,
        "best_epoch": checkpoint["epoch"], "provenance_sha256": PROVENANCE, "config_source_commit": TV3_COMMIT,
        "config_source_path": f"configs/{config_name}", "config_source_file_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "embedded_config_canonical_sha256": canonical_hash(checkpoint["config"]),
        "class_map": mapping, "preprocessing": PREPROCESSING,
        "train_images_sha_verified": len(datasets["train"].get_image_ids()), "val_images_sha_verified": len(parents),
        "validation_population_sha256": digest(comp / "val.jsonl"), "validation_crop_manifest_sha256": digest(comp / "b2/val.jsonl"),
        "validation_image_ids_sha256": canonical_hash(sorted(parents)), "validation_images": len(parents), "validation_crops": len(crop_records),
        "image_level_metrics": metrics, "confusion_matrix": cm, "per_class_metrics": per_class,
        "validation_checks": validation_checks,
        "stored_image_level_metrics_match": validation_checks["checkpoint_rounded_metrics_match"] and validation_checks["checkpoint_cm_matches"],
        "published_validation_cm_and_error_ids_match": validation_checks["published_cm_matches"] and validation_checks["published_error_ids_and_labels_match"],
        "checkpoint_image_level_metrics": {key: stored[key] for key in metrics},
        "checkpoint_confusion_matrix": stored["confusion_matrix"],
        "cm_difference_from_checkpoint": [[cm[i][j] - stored["confusion_matrix"][i][j] for j in range(8)] for i in range(8)],
        "error_records_only_in_published": sorted(set(published_errors) - set(actual_errors)),
        "error_records_only_in_reloaded": sorted(set(actual_errors) - set(published_errors)),
        "error_records_with_changed_labels": {iid: {"published": published_errors[iid], "reloaded": actual_errors[iid]}
            for iid in published_errors.keys() & actual_errors.keys() if published_errors[iid] != actual_errors[iid]},
        "unweighted_parent_mean_crop_validation_CE": loss_sum / weight_sum,
        "checkpoint_reported_validation_CE": checkpoint["val_metrics"]["val_loss"],
        "validation_loss_definition": "Mean unweighted crop CE within parent, then mean parents; this is NOT B3's weighted training loss",
        "crop_frequency_class_weights_reconstructed_from_frozen_train": crop_class_weights(datasets["train"].samples),
        "parent_inverse_frequency_weights": [1.] * 8,
        "native_adapter_max_logit_delta_all_val_crops": max_logit_delta, "checkpoint_unchanged": True,
        "fresh_process": True, "weights_only_safe_load": True,
        "run_id_embedded": checkpoint.get("run_id"), "training_commit_embedded": checkpoint.get("git_commit"),
        "original_training_log_available": False, "reported_final_training_epoch": 28 if model_name == "B2" else 21,
        "reported_final_training_epoch_independently_verified": False,
        "environment": {"python": platform.python_version(), "torch": torch.__version__, "device": device_name, "num_threads": 4,
            "cuda_build": torch.version.cuda, "gpu": torch.cuda.get_device_name(0) if device_name == "cuda" else None,
            "cudnn_deterministic": torch.backends.cudnn.deterministic, "cudnn_benchmark": torch.backends.cudnn.benchmark,
            "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32, "matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32},
        "model_load_seconds": load_seconds, "validation_wall_seconds": time.perf_counter() - inference_start,
        "test_manifest_opened": False, "test_inference_performed": False, "training_performed": False}
    output.mkdir(parents=True, exist_ok=False)
    for filename, data in (("verification.json", summary), ("validation_predictions.json", predictions),
                           ("checkpoint_validation_metrics.json", checkpoint["val_metrics"]), ("embedded_config.json", checkpoint["config"])):
        with (output / filename).open("x", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
    print(json.dumps({key: summary[key] for key in ("status", "model", "best_epoch", "checkpoint_sha256", "image_level_metrics",
                     "validation_images", "validation_crops", "native_adapter_max_logit_delta_all_val_crops", "test_inference_performed")}, indent=2))
    require(passed, "Reloaded Validation differs; FAIL evidence saved, no final model lock or Test inference permitted")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("B2", "B3"), required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu",
                        help="Validation verification only; official Test remains bound to its frozen CPU protocol")
    args = parser.parse_args()
    verify(args.model, args.checkpoint.resolve(), args.output.resolve(), args.device)


if __name__ == "__main__":
    main()
