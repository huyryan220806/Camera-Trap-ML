"""Read-only validation of frozen B0 metadata, before loader/model creation."""

import json
from pathlib import Path

from src.data.b0_dataset import image_path, inspect_images, read_rows, verify_image_hash
from src.evaluation.metrics import load_class_map
from src.training.run_artifacts import file_sha256


def verify_manifest_hash(path: Path, expected: str | None, description: str) -> None:
    if not expected:
        raise ValueError(f"Missing frozen {description.lower()} hash; cannot verify provenance")
    if file_sha256(path) != expected:
        raise ValueError(f"{description} hash mismatch: {path}")


def verify_source_membership(rows: list[dict], source_path: Path) -> None:
    source = {}
    with source_path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if row["image_id"] in source:
                    raise ValueError("Duplicate image_id in frozen source manifest")
                source[row["image_id"]] = row
    for row in rows:
        # Exact row equality includes ID, split, class, file path and quality hash.
        if source.get(row["image_id"]) != row:
            raise ValueError(f"Validation row provenance mismatch: {row['image_id']}")


def verify_validation_provenance(checkpoint: dict, root: Path) -> tuple[list[dict], list[str], Path, dict]:
    config = checkpoint["config"]
    if config["data"]["test_used_for_selection"] is not False:
        raise ValueError("Checkpoint config violates test isolation")
    if checkpoint["model_name"] != "resnet18" or checkpoint["freeze_backbone"] is not True:
        raise ValueError("Checkpoint is not frozen B0 ResNet18")
    frozen = config.get("dataset", {})
    source = root / config["data"]["source_manifest"]
    verify_manifest_hash(source, frozen.get("source_manifest_sha256"), "Source manifest")
    class_map = root / config["data"]["class_map"]
    # Old checkpoints without a class-map byte hash must still match both maps.
    if frozen.get("class_map_sha256"):
        verify_manifest_hash(class_map, frozen["class_map_sha256"], "Class map")
    labels, names = load_class_map(class_map)
    if (labels != list(range(len(names))) or len(set(names)) != len(names)
            or checkpoint["class_to_idx"] != {name: i for i, name in enumerate(names)}
            or checkpoint["idx_to_class"] != {i: name for i, name in enumerate(names)}
            or checkpoint["num_classes"] != len(names)
            or config["model"]["num_classes"] != len(names)):
        raise ValueError("Checkpoint class map mismatch")
    run_dir = root / "experiments" / config["experiment"]["id"]
    validation = run_dir / "used_val.jsonl"
    verify_manifest_hash(validation, frozen.get("validation_manifest_sha256"), "Validation manifest")
    rows = read_rows(validation, "val", names)
    verify_source_membership(rows, source)
    image_root = root / config["data"]["image_root"]
    hashed = sum(verify_image_hash(image_path(image_root, row, project_root=root), row) for row in rows)
    _, errors = inspect_images(rows, image_root, project_root=root)
    if errors:
        raise ValueError(f"Validation image verification failed: {errors}")
    return rows, names, class_map, {
        "status": "PASS", "source_manifest_hash": "PASS", "validation_manifest_hash": "PASS",
        "class_map": "PASS", "class_map_hash": "PASS" if frozen.get("class_map_sha256") else "NOT AVAILABLE: exact bidirectional mapping verified",
        "source_membership": "PASS", "image_sha256_verified": hashed,
        "images_without_frozen_sha256": len(rows) - hashed,
    }
