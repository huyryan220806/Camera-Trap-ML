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
            "comparison_unit": "all_valid_boxes_mean_probability_per_source_image"}


def official_gate(config: dict, root: Path) -> tuple[dict, dict]:
    validate_config(config)
    data = config["data"]
    if data.get("tv1_handoff"):
        from src.training.tv1_handoff import load_handoff
        receipt = load_handoff(data["tv1_handoff"], root)
        freeze_digest = receipt["provenance_sha256"]
    elif not all(data.get(k) for k in ("freeze_receipt", "freeze_sha256", "freeze_git_ref")):
        raise GateError("BLOCKED - W3-01 MANIFEST NOT FROZEN")
    else:
        receipt = committed_receipt(root, data["freeze_receipt"], data["freeze_sha256"], data["freeze_git_ref"])
        if receipt.get("status") != "FROZEN" or receipt.get("owner") != "TV1" or receipt.get("task") != "W3-01" or not receipt.get("dataset_version"):
            raise GateError("BLOCKED - W3-01 MANIFEST NOT FROZEN")
        freeze_digest = data["freeze_sha256"]
    protocol = config["protocol"]
    if protocol.get("status") != "AGREED":
        raise GateError("BLOCKED - B1/B2 PROTOCOL NOT AGREED")
    agreement = committed_receipt(root, protocol["receipt"], protocol["sha256"], protocol["git_ref"])
    approval = agreement.get("approval", {})
    group_confirmation = (approval.get("kind") == "user_confirmed_team_agreement"
                          and set(approval.get("confirmed_for", [])) == {"TV2", "TV3"}
                          and isinstance(approval.get("source"), str) and bool(approval["source"].strip())
                          and isinstance(approval.get("quote"), str) and bool(approval["quote"].strip()))
    if (agreement.get("status") != "AGREED" or not (set(agreement.get("approved_by", [])) == {"TV2", "TV3"} or group_confirmation)
            or agreement.get("freeze_sha256") != freeze_digest
            or agreement.get("settings") != protocol_settings(config)):
        raise GateError("B1/B2 agreement differs from requested experiment")
    if not config["runtime"].get("budget_reference") or agreement.get("budget_reference") != config["runtime"]["budget_reference"]:
        raise GateError("BLOCKED - GPU BUDGET NOT CONFIRMED")
    return receipt, agreement


def read_b1_view(path: Path, expected_split: str, class_names: list[str]) -> list[dict]:
    """Read TV1's B1 projection without requiring full source-manifest fields."""
    rows = []
    image_ids, sample_ids = set(), set()
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            class_id = row.get("class_id")
            image_id = row.get("image_id")
            sample_id = row.get("sample_id")
            weight = row.get("sample_weight")
            if row.get("split") != expected_split:
                raise GateError(f"{path}:{line_number} has invalid split")
            if type(class_id) is not int or not 0 <= class_id < len(class_names):
                raise GateError(f"{path}:{line_number} has invalid class_id")
            if row.get("label") != class_names[class_id]:
                raise GateError(f"{path}:{line_number} has inconsistent label")
            if not image_id or image_id in image_ids or not sample_id or sample_id in sample_ids:
                raise GateError(f"{path}:{line_number} has missing/duplicate sample identity")
            if row.get("input_type") != "full_image" or "boxes" in row:
                raise GateError(f"{path}:{line_number} is not a B1 full-image projection")
            if type(weight) not in (int, float) or not math.isfinite(weight) or not math.isclose(weight, 1.0):
                raise GateError(f"{path}:{line_number} has invalid sample_weight")
            image_ids.add(image_id)
            sample_ids.add(sample_id)
            rows.append(row)
    if not rows:
        raise GateError(f"No {expected_split} B1 rows in {path}")
    return rows


def projection_matches_source(view: dict, source: dict) -> bool:
    """Compare stable provenance fields while allowing the B1 view to be a projection."""
    required = ("image_id", "split", "class_id", "label")
    if any(view.get(key) != source.get(key) for key in required):
        return False
    for key in ("file_name", "url", "seq_id", "sequence_id", "location", "width", "height"):
        if key in view and view[key] != source.get(key):
            return False
    if "quality" in view:
        quality = view.get("quality")
        source_quality = source.get("quality") or {}
        if not isinstance(quality, dict) or any(value != source_quality.get(key) for key, value in quality.items()):
            return False
    return True


def bbox_xyxy(box: dict) -> list[float]:
    bbox = box.get("bbox_xywh", [])
    if len(bbox) != 4:
        raise GateError("Invalid source bbox")
    x, y, width, height = bbox
    return [x, y, x + width, y + height]


def same_bbox(left: object, right: object) -> bool:
    if not isinstance(left, list) or len(left) != 4 or not isinstance(right, list) or len(right) != 4:
        return False
    if any(type(value) not in (int, float) or not math.isfinite(value) for value in left + right):
        return False
    return all(math.isclose(a, b, rel_tol=0.0, abs_tol=1e-6) for a, b in zip(left, right))


def verify_data(receipt: dict, root: Path, image_root: Path, num_classes: int, *, inspect: bool = True) -> tuple[dict, list[str], Path, dict]:
    native = receipt.get("format") == "tv1_comparison_v1"
    if native:
        from src.training.tv1_handoff import load_handoff
        if load_handoff(receipt["binding"], root) != receipt:
            raise GateError("TV1 adapter evidence changed")
    files = receipt["files"]
    required = ("train", "val", "source_train", "source_val", "crop_train", "crop_val", "class_map", "excluded", "quality_audit")
    paths = {k: hashed_file(root, files[k]) for k in required}
    labels, names = load_class_map(paths["class_map"])
    if labels != list(range(num_classes)) or len(set(names)) != num_classes:
        raise GateError("Class mapping mismatch")
    quality = json.loads(paths["quality_audit"].read_text(encoding="utf-8"))
    # TV1 audits ALL splits; TV2 only consumes this attestation, never test rows.
    if not native and any(quality.get(k) is not True for k in ("all_split_location_disjoint", "all_split_sequence_disjoint", "all_split_content_disjoint", "source_membership_verified", "box_review_passed")):
        raise GateError("TV1 quality/leakage attestation incomplete")
    rows, stats = {}, {}
    identities = {key: {} for key in ("image_id", "file_name", "local_path", "sha256", "pixel_sha256", "location", "seq_id")}
    for split in ("train", "val"):
        b1_rows = read_b1_view(paths[split], split, names)
        source = {r["image_id"]: r for r in read_rows(paths[f"source_{split}"], split, names)}
        for view in b1_rows:
            if view["image_id"] not in source or not projection_matches_source(view, source[view["image_id"]]):
                raise GateError(f"Source provenance mismatch: {view['image_id']}")
            if native:
                source_row = source[view["image_id"]]
                keys = ("image_id", "split", "label", "class_id", "seq_id", "sequence_id", "location", "file_name", "url", "width", "height", "quality")
                expected_view = {**{k: source_row[k] for k in keys}, "sample_id": source_row["image_id"], "input_type": "full_image", "sample_weight": 1.0}
                if view != expected_view:
                    raise GateError("Native B1 projection mismatch")
        rows[split] = [source[view["image_id"]] for view in b1_rows]
        for row in rows[split]:
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
                tolerance = 1e-6 if native else 0
                if x < 0 or y < 0 or bw <= 0 or bh <= 0 or x+bw > w + tolerance or y+bh > h + tolerance:
                    raise GateError("Box outside source image")
            if inspect:
                path = image_path(image_root, row, project_root=root)
                try:
                    verify_image_hash(path, row)
                    with Image.open(path) as im:
                        im.verify()
                    with Image.open(path) as im:
                        if native and (path.stat().st_size != quality_row.get("bytes") or im.format != quality_row.get("image_format") or im.mode != quality_row.get("image_mode")):
                            raise GateError("Native image size/format/mode differs")
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
        expected = {(row["image_id"], box["annotation_id"]): bbox_xyxy(box)
                    for row in rows[split] for box in row["boxes"]}
        if native:
            for (image_id, annotation), coords in expected.items():
                row = by_id[image_id]
                coords[:] = [max(0, round(coords[0])), max(0, round(coords[1])), min(row["width"], round(coords[2])), min(row["height"], round(coords[3]))]
                if coords[2] - coords[0] < 8 or coords[3] - coords[1] < 8:
                    raise GateError("Native crop below minimum side")
        seen_pairs, seen_crop_ids, seen_annotation_ids = set(), set(), set()
        crop_counts = {}
        for crop in crops:
            image_id = crop.get("image_id")
            crop_id = crop.get("crop_id")
            annotation_id = crop.get("annotation_id")
            if image_id not in by_id or not crop_id or crop_id in seen_crop_ids:
                raise GateError("Invalid or duplicate crop identity")
            if not annotation_id or annotation_id in seen_annotation_ids:
                raise GateError("Invalid or duplicate annotation identity")
            pair = (image_id, annotation_id)
            if pair in seen_pairs or pair not in expected:
                raise GateError("Crop/source/box mapping mismatch")
            row = by_id[image_id]
            quality = crop.get("quality")
            source_quality = row.get("quality") or {}
            if (crop.get("input_type") != ("ground_truth_crop" if native else "bbox_crop")
                    or any(crop.get(k) != row[k] for k in ("split", "label", "class_id"))
                    or not same_bbox(crop.get("bbox_xyxy"), expected[pair])
                    or crop.get("url") != row.get("url")
                    or not isinstance(quality, dict)
                    or quality.get("local_path") != source_quality.get("local_path")
                    or quality.get("sha256") != source_quality.get("sha256")):
                raise GateError("Crop/source/box mapping mismatch")
            if native:
                box = next(b for b in row["boxes"] if b["annotation_id"] == annotation_id)
                coords = expected[pair]
                keys = ("image_id", "split", "label", "class_id", "seq_id", "sequence_id", "location", "file_name", "url", "width", "height", "quality")
                expected_crop = {**{k: row[k] for k in keys}, "annotation_id": annotation_id,
                                 "bbox_xywh_original": box["bbox_xywh"], "bbox_xyxy": coords,
                                 "crop_w": coords[2]-coords[0], "crop_h": coords[3]-coords[1],
                                 "crop_id": image_id + "_" + annotation_id, "input_type": "ground_truth_crop",
                                 "parent_crop_count": len(row["boxes"]), "sample_weight": 1.0 / len(row["boxes"])}
                if crop != expected_crop:
                    raise GateError("Native crop projection mismatch")
            seen_pairs.add(pair)
            seen_crop_ids.add(crop_id)
            seen_annotation_ids.add(annotation_id)
            crop_counts[image_id] = crop_counts.get(image_id, 0) + 1
        if seen_pairs != set(expected) or {image_id for image_id, _ in seen_pairs} != set(by_id):
            raise GateError("B1/B2 eligible source images or valid boxes differ")
        for crop in crops:
            weight = crop.get("sample_weight")
            expected_weight = 1.0 / crop_counts[crop["image_id"]]
            if type(weight) not in (int, float) or not math.isfinite(weight) or not math.isclose(weight, expected_weight, rel_tol=0.0, abs_tol=1e-12):
                raise GateError("Invalid B2 image-balanced sample_weight")
        stats[split] = {"images": len(rows[split]), "crops": len(crops), "sequences": len({r["seq_id"] for r in rows[split]}), "per_class": {name: {"images": sum(r["label"] == name for r in rows[split]), "sequences": len({r["seq_id"] for r in rows[split] if r["label"] == name})} for name in names}}
        if native:
            declared = [s for s in receipt["summary"]["by_split"] if s["split"] == split]
            if len(declared) != 1 or any(declared[0].get(k) != value for k, value in {
                "requested": len(source), "retained": len(rows[split]), "b1_samples": len(b1_rows), "b2_crops": len(crops),
                "excluded": 0, "sequences": stats[split]["sequences"], "locations": len({r["location"] for r in rows[split]})}.items()):
                raise GateError("TV1 summary differs from actual rows")
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
    return rows, names, paths["class_map"], {"status": "PASS" if inspect else "METADATA PASS - IMAGES NOT CHECKED", "counts": stats, "excluded": len(excluded), "files": files, "test_rows_opened": False, "crop_bytes_verified": False, "source_images_verified": inspect}
