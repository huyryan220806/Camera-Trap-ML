"""Fail-closed W3 gate. Reads train/val only; never repairs or filters a split.

Receipt formats are a TV2 proposal, documented in TV2_W3_PROTOCOL.md. TV1/TV3
must supply real committed evidence before these gates can authorize a run.
"""

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from PIL import Image

from src.data.b0_dataset import image_path, read_rows, verify_image_hash
from src.evaluation.metrics import load_class_map
from src.training.run_artifacts import file_sha256


class GateError(ValueError):
    pass


def relative_path(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise GateError("Expected a repository-relative path")
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise GateError("Path escapes repository")
    return path


def hashed_file(root: Path, entry: dict) -> Path:
    path = relative_path(root, entry["path"])
    expected = entry.get("sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise GateError("Missing or invalid frozen SHA-256")
    if not path.is_file() or file_sha256(path) != expected:
        raise GateError(f"SHA-256 mismatch or missing file: {entry['path']}")
    return path


def committed_receipt(root: Path, path: str, digest: str, ref: str) -> dict:
    local = hashed_file(root, {"path": path, "sha256": digest})
    if not isinstance(ref, str) or not re.fullmatch(r"[0-9a-f]{40}:.+", ref):
        raise GateError("Receipt requires an immutable <40-char commit>:<path> reference")
    try:
        content = subprocess.check_output(["git", "show", ref], cwd=root, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise GateError("Cannot verify receipt against its Git commit") from exc
    if hashlib.sha256(content).hexdigest() != digest:
        raise GateError("Receipt differs from committed handoff evidence")
    return json.loads(local.read_text(encoding="utf-8"))


def validate_config(config: dict) -> None:
    try:
        exp, model, data, training = (config[k] for k in ("experiment", "model", "data", "training"))
        if not re.fullmatch(r"B1_[A-Za-z0-9_-]+", exp["id"]):
            raise GateError("Run ID must start B1_ and contain no path separators")
        if type(exp["seed"]) is not int or not 0 <= exp["seed"] < 2**32:
            raise GateError("Invalid seed")
        expected_model = {"backbone": "resnet18", "weights": "ResNet18_Weights.IMAGENET1K_V1", "initialization": "imagenet_direct", "fine_tune": "all", "batch_norm": "update_train_only"}
        if any(model[k] != v for k, v in expected_model.items()):
            raise GateError("Unsupported B1 model/initialization/fine-tuning strategy")
        for container, key, minimum in [(model, "num_classes", 2), (data, "batch_size", 2), (data, "image_size", 32), (data, "resize_size", 32), (data, "num_workers", 0), (training, "epochs", 1), (training, "early_stopping_patience", 1), (training, "step_size", 1)]:
            if type(container[key]) is not int or container[key] < minimum:
                raise GateError(f"Invalid {key}")
        if data["resize_size"] < data["image_size"]:
            raise GateError("resize_size must cover image_size")
        if data["input_type"] != "full_image" or data["test_used_for_selection"] is not False:
            raise GateError("B1 requires full images and test isolation")
        if (training["optimizer"], training["scheduler"], training["checkpoint_metric"], training["checkpoint_mode"]) != ("sgd", "step_lr", "macro_f1", "max"):
            raise GateError("Unsupported optimizer/scheduler/checkpoint selection")
        for key in ("lr", "momentum", "weight_decay", "gamma"):
            value = training[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise GateError(f"Invalid {key}")
        if training["lr"] == 0 or not 0 < training["gamma"] <= 1 or training["momentum"] >= 1:
            raise GateError("Invalid learning rate, gamma or momentum")
        if config["preprocessing"] != {"train": "resize_random_crop_flip_jitter", "validation": "resize_center_crop", "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}:
            raise GateError("Unsupported preprocessing")
        relative_path(Path.cwd(), data["image_root"])
        if config["runtime"]["device"] != "cuda":
            raise GateError("Official B1 requires agreed CUDA budget; CPU is smoke only")
    except (KeyError, TypeError) as exc:
        raise GateError(f"Incomplete B1 config: {exc}") from exc


def protocol_settings(config: dict) -> dict:
    return {"seed": config["experiment"]["seed"], "model": config["model"],
            "training": config["training"], "preprocessing": config["preprocessing"],
            "data": {k: config["data"][k] for k in ("image_size", "resize_size", "batch_size", "num_workers")},
            "loss": "unweighted_cross_entropy", "drop_last": False,
            "comparison_unit": "one_selected_box_per_source_image"}


def official_gate(config: dict, root: Path) -> tuple[dict, dict]:
    validate_config(config)
    data = config["data"]
    if not all(data.get(k) for k in ("freeze_receipt", "freeze_sha256", "freeze_git_ref")):
        raise GateError("BLOCKED - W3-01 MANIFEST NOT FROZEN")
    receipt = committed_receipt(root, data["freeze_receipt"], data["freeze_sha256"], data["freeze_git_ref"])
    if receipt.get("status") != "FROZEN" or receipt.get("owner") != "TV1" or receipt.get("task") != "W3-01" or not receipt.get("dataset_version"):
        raise GateError("BLOCKED - W3-01 MANIFEST NOT FROZEN")
    protocol = config["protocol"]
    if protocol.get("status") != "AGREED":
        raise GateError("BLOCKED - B1/B2 PROTOCOL NOT AGREED")
    agreement = committed_receipt(root, protocol["receipt"], protocol["sha256"], protocol["git_ref"])
    if (agreement.get("status") != "AGREED" or set(agreement.get("approved_by", [])) != {"TV2", "TV3"}
            or agreement.get("freeze_sha256") != data["freeze_sha256"]
            or agreement.get("settings") != protocol_settings(config)):
        raise GateError("B1/B2 agreement differs from requested experiment")
    if not config["runtime"].get("budget_reference") or agreement.get("budget_reference") != config["runtime"]["budget_reference"]:
        raise GateError("BLOCKED - GPU BUDGET NOT CONFIRMED")
    return receipt, agreement


def verify_data(receipt: dict, root: Path, image_root: Path, num_classes: int, *, inspect: bool = True) -> tuple[dict, list[str], Path, dict]:
    files = receipt["files"]
    required = ("train", "val", "source_train", "source_val", "crop_train", "crop_val", "class_map", "excluded", "quality_audit")
    paths = {k: hashed_file(root, files[k]) for k in required}
    labels, names = load_class_map(paths["class_map"])
    if labels != list(range(num_classes)) or len(set(names)) != num_classes:
        raise GateError("Class mapping mismatch")
    quality = json.loads(paths["quality_audit"].read_text(encoding="utf-8"))
    # TV1 audits ALL splits; TV2 only consumes this attestation, never test rows.
    if any(quality.get(k) is not True for k in ("all_split_location_disjoint", "all_split_sequence_disjoint", "all_split_content_disjoint", "source_membership_verified", "box_review_passed")):
        raise GateError("TV1 quality/leakage attestation incomplete")
    rows, stats = {}, {}
    identities = {key: {} for key in ("image_id", "file_name", "local_path", "sha256", "pixel_sha256", "location", "seq_id")}
    for split in ("train", "val"):
        rows[split] = read_rows(paths[split], split, names)
        source = {r["image_id"]: r for r in read_rows(paths[f"source_{split}"], split, names)}
        for row in rows[split]:
            if row != source.get(row["image_id"]):
                raise GateError(f"Source provenance mismatch: {row['image_id']}")
            if row.get("sequence_id", row.get("seq_id")) != row.get("seq_id"):
                raise GateError("Sequence alias mismatch")
            quality_row = row.get("quality", {})
            for key, seen in identities.items():
                value = quality_row.get(key) if key in ("local_path", "sha256", "pixel_sha256") else row.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise GateError(f"Missing {key}: {row['image_id']}")
                if key in ("sha256", "pixel_sha256") and not re.fullmatch(r"[0-9a-f]{64}", value):
                    raise GateError(f"Invalid {key}")
                identity = (split, row["class_id"]) if key in ("sha256", "pixel_sha256") else split
                if value in seen and (key in ("image_id", "file_name", "local_path") or seen[value] != identity):
                    raise GateError(f"Duplicate or cross-split leakage: {key}")
                seen[value] = identity
            w, h = row.get("width"), row.get("height")
            if type(w) not in (int, float) or type(h) not in (int, float) or not (math.isfinite(w) and math.isfinite(h) and w > 0 and h > 0):
                raise GateError("Invalid source dimensions")
            boxes = row.get("boxes", [])
            annotation_ids = set()
            if not boxes or not row.get("url"):
                raise GateError("Missing box/source URL")
            for box in boxes:
                bbox = box.get("bbox_xywh", [])
                annotation = box.get("annotation_id")
                if not annotation or annotation in annotation_ids or box.get("label") != row["label"] or len(bbox) != 4:
                    raise GateError("Invalid box identity or label")
                annotation_ids.add(annotation)
                if any(type(v) not in (int, float) or not math.isfinite(v) for v in bbox):
                    raise GateError("Invalid box coordinates")
                x, y, bw, bh = bbox
                if x < 0 or y < 0 or bw <= 0 or bh <= 0 or x+bw > w or y+bh > h:
                    raise GateError("Box outside source image")
            if inspect:
                path = image_path(image_root, row, project_root=root)
                try:
                    verify_image_hash(path, row)
                    with Image.open(path) as im:
                        im.verify()
                    with Image.open(path) as im:
                        rgb = im.convert("RGB")
                        rgb.load()
                        if rgb.size != (w, h):
                            raise GateError("Decoded source dimensions differ")
                        pixel_hash = hashlib.sha256(f"RGB:{rgb.width}:{rgb.height}:".encode() + rgb.tobytes()).hexdigest()
                        if pixel_hash != quality_row["pixel_sha256"]:
                            raise GateError("Decoded pixel SHA-256 mismatch")
                except (OSError, ValueError) as exc:
                    raise GateError(f"Image invalid {row['image_id']}: {exc}") from exc
        if {r["class_id"] for r in rows[split]} != set(labels):
            raise GateError(f"Missing class in {split}")
        with paths[f"crop_{split}"].open(encoding="utf-8") as stream:
            crops = [json.loads(line) for line in stream if line.strip()]
        by_id = {r["image_id"]: r for r in rows[split]}
        seen_crops = set()
        for crop in crops:
            image_id = crop.get("image_id")
            if image_id not in by_id or image_id in seen_crops:
                raise GateError("Require exactly one selected crop per eligible source image")
            seen_crops.add(image_id)
            row = by_id[image_id]
            box = next((b for b in row["boxes"] if b["annotation_id"] == crop.get("annotation_id")), None)
            if (box is None or any(crop.get(k) != row[k] for k in ("split", "label", "class_id"))
                    or crop.get("bbox_xywh_original") != box["bbox_xywh"] or crop.get("source_url") != row["url"]):
                raise GateError("Crop/source/box mapping mismatch")
            if not re.fullmatch(r"[0-9a-f]{64}", crop.get("sha256", "")) or not crop.get("file_path"):
                raise GateError("Missing crop artifact identity")
        if seen_crops != set(by_id):
            raise GateError("B1/B2 eligible source image sets differ")
        stats[split] = {"images": len(rows[split]), "sequences": len({r["seq_id"] for r in rows[split]}), "per_class": {name: {"images": sum(r["label"] == name for r in rows[split]), "sequences": len({r["seq_id"] for r in rows[split] if r["label"] == name})} for name in names}}
    excluded = [json.loads(line) for line in paths["excluded"].read_text(encoding="utf-8").splitlines() if line.strip()]
    excluded_ids = set()
    sources = {r["image_id"] for split in ("train", "val") for r in read_rows(paths[f"source_{split}"], split, names)}
    accepted = {r["image_id"] for split in rows.values() for r in split}
    for row in excluded:
        if row.get("split") not in ("train", "val") or not row.get("reason") or row.get("image_id") in excluded_ids:
            raise GateError("Invalid exclusion ledger")
        excluded_ids.add(row["image_id"])
    if accepted & excluded_ids or accepted | excluded_ids != sources:
        raise GateError("Accepted/excluded accounting differs from source")
    return rows, names, paths["class_map"], {"status": "PASS", "counts": stats, "excluded": len(excluded), "files": files, "test_rows_opened": False, "crop_bytes_verified": False}
