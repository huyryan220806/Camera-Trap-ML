"""Read-only audit of the three week-2 handoffs; no images are downloaded."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tip(root):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    for member in ("tv1", "tv2", "tv3"):
        parser.add_argument(f"--{member}", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pilot = {r["image_id"]: r for r in rows(args.tv1 / "data/processed/v1/pilot_v1.jsonl")}
    v2 = {r["image_id"]: r for r in rows(args.tv1 / "data/processed/v2/manifest_v2.jsonl")}
    class_map = json.loads((args.tv1 / "data/processed/v1/class_map.json").read_text())
    result = {"review_date": "2026-10-09", "tv2_commit": tip(args.tv2), "tv3_commit": tip(args.tv3)}
    run = args.tv2 / "experiments/B0_run01"
    config = json.loads((run / "config.yaml").read_text())
    b0 = {}
    selected_ids = {}
    for split in ("train", "val"):
        used = rows(run / f"used_{split}.jsonl")
        selected = rows(run / f"selected_{split}.jsonl")
        selected_ids[split] = {r["image_id"] for r in used}
        hash_key = "train_manifest_sha256" if split == "train" else "validation_manifest_sha256"
        b0[split] = {
            "selected": len(selected), "used": len(used), "selected_equals_used": selected == used,
            "exact_pilot_rows": sum(pilot.get(r["image_id"]) == r for r in used),
            "also_in_v2": sum(r["image_id"] in v2 for r in used),
            "class_counts": dict(Counter(r["label"] for r in used)),
            "manifest_hash_matches_config": sha(run / f"used_{split}.jsonl") == config["dataset"][hash_key],
        }
    b0["split_id_overlap"] = len(selected_ids["train"] & selected_ids["val"])
    b0["source_hash_matches"] = sha(args.tv1 / "data/processed/v1/pilot_v1.jsonl") == config["dataset"]["source_manifest_sha256"]
    b0["checkpoint_available_in_checkout"] = (run / "checkpoints/best_model.pth").is_file()
    metric = json.loads((run / "results/val_metrics.json").read_text())
    matrix = metric["confusion_matrix"]
    support = sum(map(sum, matrix))
    precision, recall, f1 = [], [], []
    for c in range(len(matrix)):
        tp, predicted, actual = matrix[c][c], sum(row[c] for row in matrix), sum(matrix[c])
        p, r = (tp / predicted if predicted else 0), (tp / actual if actual else 0)
        precision.append(p)
        recall.append(r)
        f1.append(2 * p * r / (p + r) if p + r else 0)
    recomputed = {"macro_precision": sum(precision) / len(matrix), "macro_recall": sum(recall) / len(matrix),
                  "macro_f1": sum(f1) / len(matrix), "accuracy": sum(matrix[i][i] for i in range(len(matrix))) / support}
    b0["metrics_recomputed_from_committed_confusion_matrix"] = recomputed
    b0["metrics_match_matrix"] = all(abs(metric[k] - v) < 1e-12 for k, v in recomputed.items())
    b0["support"] = support
    result["tv2"] = b0
    crop_result, parents = {}, {}
    for split in ("train", "val"):
        source = {r["image_id"]: r for r in rows(args.tv3 / f"data/processed/v1/{split}.jsonl")}
        crops = rows(args.tv3 / f"data/crops/crop_manifest_{split}.jsonl")
        errors = rows(args.tv3 / f"data/crops/crop_errors_{split}.jsonl")
        ids = {r["image_id"] for r in crops}
        parents[split] = ids
        mismatches = []
        for crop in crops:
            parent = source.get(crop["image_id"])
            boxes = [] if not parent else [b for b in parent["boxes"] if b["annotation_id"] == crop["annotation_id"]]
            if (not parent or len(boxes) != 1 or boxes[0]["label"] != crop["label"]
                    or boxes[0]["bbox_xywh"] != crop["bbox_xywh_original"]
                    or class_map.get(str(crop["class_id"])) != crop["label"] or crop["split"] != split):
                mismatches.append(crop["crop_id"])
        crop_result[split] = {
            "crop_rows": len(crops), "unique_parent_images": len(ids),
            "duplicate_crop_ids": len(crops) - len({r["crop_id"] for r in crops}),
            "annotation_or_mapping_mismatches": mismatches,
            "parent_images_in_v2": len(ids & set(v2)), "parent_images_outside_v2": len(ids - set(v2)),
            "v2_split_images": sum(r["split"] == split for r in v2.values()),
            "v2_split_images_without_crop": len({r["image_id"] for r in v2.values() if r["split"] == split} - ids),
            "crop_class_counts": dict(Counter(r["label"] for r in crops)),
            "parent_class_counts": dict(Counter(source[i]["label"] for i in ids)),
            "crop_files_present_in_fresh_checkout": sum((args.tv3 / r["file_path"]).is_file() for r in crops),
            "error_reasons": dict(Counter(r["reason"] for r in errors)),
        }
    crop_result["train_val_parent_overlap"] = len(parents["train"] & parents["val"])
    result["tv3"] = crop_result
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
