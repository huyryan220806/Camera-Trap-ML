"""Non-destructive TV3 bug probes. Synthetic fixtures only; no network calls."""

import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    crop = load("tv3_review_crop", args.repo / "scripts/crop_dataset.py")
    dataset_module = load("tv3_review_dataset", args.repo / "src/data/crop_dataset.py")
    from PIL import Image

    with tempfile.TemporaryDirectory(prefix="tv3-review-") as tmp:
        root = Path(tmp)
        manifest, errors = root / "manifest.jsonl", root / "errors.jsonl"
        manifest.write_text(json.dumps({"image_id": "missing-crop", "file_path": "absent.jpg", "sha256": "bad"}) + "\n")
        errors.write_text(json.dumps({"image_id": "retry-me", "reason": "download_failed"}) + "\n")
        processed = crop.get_processed_ids(manifest, errors)
        result = {"download_failure_marked_processed": "retry-me" in processed,
                  "missing_crop_marked_processed": "missing-crop" in processed}

        source = root / "source"
        source.mkdir()
        (source / "class_map.json").write_text('{"0":"sambar","1":"chinese_serow"}')
        inputs = [{"image_id": name} for name in ("a", "b", "c", "d")]
        out = root / "crops"
        out.mkdir()
        seen = []

        def fake_process(record, *args):
            seen.append(record["image_id"])
            return [record], []

        with patch.object(crop, "MANIFEST_DIR", source), patch.object(crop, "load_manifest", return_value=inputs), patch.object(crop, "process_record", side_effect=fake_process):
            crop.crop_split_multithread("train", out, limit=2, workers=1)
            first = seen.copy()
            seen.clear()
            crop.crop_split_multithread("train", out, limit=2, workers=1)
        result["same_limit_command"] = {"first_run_ids": first, "second_run_ids": seen,
                                        "rows_after_two_runs": len((out / "crop_manifest_train.jsonl").read_text().splitlines())}

        Image.new("RGB", (32, 32), "red").save(root / "fixture.jpg")
        invalid = {"crop_id": "fixture", "image_id": "fixture", "split": "val", "label": "chinese_serow",
                   "class_id": 0, "file_path": "fixture.jpg", "sha256": "not-the-real-hash"}
        (out / "crop_manifest_train.jsonl").write_text(json.dumps(invalid) + "\n")
        ds = dataset_module.CropDataset("train", out, source / "class_map.json", root=root)
        tensor, target = ds[0]
        result["dataset_accepts_invalid_contract"] = {"requested_split": "train", "accepted_split": ds.samples[0]["split"],
            "label": invalid["label"], "expected_class_id": 1, "returned_class_id": target, "bad_hash_accepted": True,
            "tensor_shape": list(tensor.shape)}
        result["scope"] = "Synthetic probes; no source artifacts changed and no network access. True values describe defects, not acceptance tests."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
