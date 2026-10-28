"""Validation-only artifact audit for W5; never trains, loads models or opens Test.

Scores are mean per-crop softmax vectors in the frozen numeric class order.
An artifact audit is not reviewer approval or proof of fresh-process inference.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

DATASET = "comparison_v1"
PROVENANCE = "d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f"
B2_SHA256 = "8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5"
CLASSES = ["large_antlered_muntjac", "annamite_striped_rabbit", "sambar", "chinese_serow",
           "common_palm_civet", "masked_palm_civet", "silver_pheasant", "eurasian_wild_pig"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def class_id(value):
    require(type(value) is int and 0 <= value < 8, "Class ID must be integer 0..7")
    return value


def vector(values):
    require(isinstance(values, list) and len(values) == 8, "Need all eight class scores")
    require(all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in values),
            "Nonfinite/out-of-range class scores")
    require(math.isclose(sum(values), 1., rel_tol=0, abs_tol=1e-5), "Scores must sum to one")
    return values


def softmax(logits):
    require(isinstance(logits, list) and len(logits) == 8 and
            all(type(v) in (int, float) and math.isfinite(v) for v in logits), "Invalid eight-class logits")
    shifted = [math.exp(v - max(logits)) for v in logits]
    return [v / sum(shifted) for v in shifted]


def unique(rows, key):
    require(rows, "Empty population")
    require(all(isinstance(r.get(key), str) and r[key].strip() for r in rows), "Missing identity: " + key)
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), "Duplicate identity: " + key)
    return result


def validate_population(parents, crops):
    population = unique(parents, "image_id")
    specs = unique(crops, "crop_id")
    require(all(r.get("split") == "val" for r in parents + crops), "Validation only; Test/train rejected")
    require({r["image_id"] for r in crops} == set(population), "Missing/extra parent in crop manifest")
    for row in parents:
        class_id(row["class_id"])
    for row in crops:
        require(row["class_id"] == population[row["image_id"]]["class_id"], "Crop/parent label mismatch")
        class_id(row["class_id"])
    return population, specs


def load_frozen_validation(root):
    """Only fixed Train/Val paths are opened. Test is not a configurable input."""
    folder = Path(root) / "data/processed/comparison_v1"
    require(sha256(folder / "provenance.json") == PROVENANCE, "Frozen provenance hash mismatch")
    provenance = read_json(folder / "provenance.json")
    names = ("class_map.json", "train.jsonl", "val.jsonl", "b2/train.jsonl", "b2/val.jsonl")
    hashes = {name: sha256(folder / name) for name in names}
    require(all(value == provenance["files_sha256"][name] for name, value in hashes.items()),
            "Frozen Train/Val manifest hash mismatch")
    require(read_json(folder / "class_map.json") == {str(i): c for i, c in enumerate(CLASSES)}, "Class order mismatch")
    train, val, crops = (read_jsonl(folder / name) for name in ("train.jsonl", "val.jsonl", "b2/val.jsonl"))
    validate_population(val, crops)
    unique(train, "image_id")
    require(all(r.get("split") == "train" for r in train), "Train split mismatch")
    for field in ("image_id", "file_name", "seq_id", "location"):
        require(not ({r[field] for r in train} & {r[field] for r in val}), "Train/Val leakage: " + field)
    return val, crops, hashes


def aggregate(crop_predictions, parents, crops, experiment_id, checkpoint_sha256):
    population, expected = validate_population(parents, crops)
    require(isinstance(experiment_id, str) and experiment_id.strip(), "Missing experiment ID")
    require(isinstance(checkpoint_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", checkpoint_sha256), "Invalid checkpoint hash")
    actual = unique(crop_predictions, "crop_id")
    require(set(actual) == set(expected), "Missing/extra crop prediction")
    groups = defaultdict(list)
    for cid, row in actual.items():
        ref = expected[cid]
        require(row.get("image_id") == ref["image_id"] and row.get("ground_truth") == ref["class_id"],
                "Crop identity/ground truth mismatch")
        class_id(row["ground_truth"])
        require(("logits" in row) != ("class_scores" in row), "Provide exactly logits or softmax scores")
        groups[row["image_id"]].append(softmax(row["logits"]) if "logits" in row else vector(row["class_scores"]))
    result = []
    for iid, scores in sorted(groups.items()):
        mean = [sum(p[i] for p in scores) / len(scores) for i in range(8)]
        result.append(dict(image_id=iid, ground_truth=population[iid]["class_id"],
                           predicted_class=max(range(8), key=mean.__getitem__), class_scores=mean,
                           crop_count=len(scores), experiment_id=experiment_id, checkpoint_sha256=checkpoint_sha256))
    return result


def audit_predictions(predictions, parents, crops, experiment_id, checkpoint_sha256):
    population, _ = validate_population(parents, crops)
    actual = unique(predictions, "image_id")
    require(set(actual) == set(population), "Missing/extra image prediction")
    counts = defaultdict(int)
    for row in crops:
        counts[row["image_id"]] += 1
    for iid, row in actual.items():
        require(class_id(row["ground_truth"]) == population[iid]["class_id"], "Ground truth mismatch")
        scores = vector(row["class_scores"])
        require(class_id(row["predicted_class"]) == max(range(8), key=scores.__getitem__), "Argmax/tie mismatch")
        require(type(row["crop_count"]) is int and row["crop_count"] == counts[iid], "Crop count mismatch")
        require(row["experiment_id"] == experiment_id and row["checkpoint_sha256"] == checkpoint_sha256,
                "Experiment/checkpoint mismatch")
    # Independent confusion-matrix arithmetic; all 8 classes, zero_division=0.
    cm = [[0] * 8 for _ in range(8)]
    for row in predictions:
        cm[row["ground_truth"]][row["predicted_class"]] += 1
    per_class = []
    for i, name in enumerate(CLASSES):
        support, guessed, tp = sum(cm[i]), sum(r[i] for r in cm), cm[i][i]
        per_class.append(dict(class_id=i, label=name, precision=tp/guessed if guessed else 0.,
                              recall=tp/support if support else 0., f1=2*tp/(support+guessed) if support+guessed else 0.,
                              support=support))
    metrics = {"accuracy": sum(cm[i][i] for i in range(8)) / len(predictions)}
    metrics.update({"macro_" + key: sum(r[key] for r in per_class) / 8 for key in ("precision", "recall", "f1")})
    return dict(metrics=metrics, per_class=per_class, confusion_matrix=cm, images=len(predictions), crops=len(crops))


def verify_handoff(handoff, checkpoint, hashes, protocol, artifact_root=None):
    """Fail closed before accepting candidate artifacts; approval is external input.

    The receipt records reviewer names but cannot authenticate their authorship.
    TV2 must verify its Git/PR provenance in the handoff report.
    """
    require(protocol.get("status") == "APPROVED" and protocol.get("reviewers", {}).get("TV3"),
            "BLOCKED: W5 protocol needs TV3 approval")
    require(protocol.get("selection_metric") == "image_macro_f1" and
            protocol.get("checkpoint_tie_rule") == "earliest_epoch" and
            protocol.get("prediction_tie_rule") == "lowest_class_id", "Unsupported/unregistered tie policy")
    budget = protocol.get("max_candidate_runs")
    require(type(budget) is int and budget > 0 and handoff.get("experiment_id") in protocol.get("experiments", []),
            "BLOCKED: candidate budget/registration missing")
    require(len(protocol["experiments"]) == len(set(protocol["experiments"])) <= budget, "Invalid experiment budget")
    require(type(handoff.get("seed")) is int and handoff["seed"] in protocol.get("seeds", []), "Unregistered seed")
    require(handoff.get("evaluation_split") == "val" and handoff.get("dataset_version") == DATASET,
            "Only frozen comparison_v1 Validation is accepted")
    require(handoff.get("class_order") == CLASSES, "Class order mismatch")
    require(handoff.get("provenance_sha256") == PROVENANCE and handoff.get("manifest_sha256") == hashes,
            "Dataset/manifest hash mismatch")
    require(handoff.get("aggregation") == "mean_crop_softmax_then_argmax", "Aggregation mismatch")
    for key in ("experiment_id", "model_name", "architecture", "pretrained_source", "model_version",
                "training_log", "training_commit", "device", "train_dataset_version", "val_dataset_version"):
        require(isinstance(handoff.get(key), str) and handoff[key].strip(), "Missing handoff field: " + key)
    require(handoff["train_dataset_version"] == handoff["val_dataset_version"] == DATASET,
            "Expanded-data experiment needs a separate protocol")
    require(handoff.get("training_status") == "complete" and isinstance(handoff.get("preprocessing"), dict)
            and handoff["preprocessing"], "Incomplete training/preprocessing handoff")
    require(handoff.get("fresh_process_reload", {}).get("status") == "PASS" and
            handoff["fresh_process_reload"].get("evidence"), "Missing fresh-process reload evidence")
    require(handoff.get("checkpoint_sha256") == sha256(checkpoint), "Checkpoint hash mismatch")
    require(type(handoff.get("checkpoint_bytes")) is int and handoff["checkpoint_bytes"] == Path(checkpoint).stat().st_size,
            "Checkpoint size mismatch")
    # A bare PASS string is insufficient: require actual config, log and reload artifacts.
    artifacts = handoff.get("artifacts", {})
    for name in ("training_config", "training_log", "reload_report"):
        entry = artifacts.get(name, {})
        require(isinstance(entry.get("path"), str) and entry["path"].strip(), "Missing artifact: " + name)
        path = Path(artifact_root or ".") / entry["path"]
        require(path.is_file() and entry.get("sha256") == sha256(path), "Artifact missing/hash mismatch: " + name)
    reload_path = Path(artifact_root or ".") / artifacts["reload_report"]["path"]
    reload_report = read_json(reload_path)
    require(reload_report.get("status") == "PASS" and reload_report.get("fresh_process") is True and
            reload_report.get("checkpoint_sha256") == handoff["checkpoint_sha256"] and
            reload_report.get("evaluation_split") == "val" and reload_report.get("manifest_sha256") == hashes and
            reload_report.get("test_inference_performed") is False, "Reload report does not verify this Validation checkpoint")


def compare_predictions(reference, candidate):
    """Inputs must already have passed audit_predictions against the same manifest."""
    left, right = unique(reference, "image_id"), unique(candidate, "image_id")
    require(set(left) == set(right), "Comparison population mismatch")
    changes = {"b2_correct_candidate_wrong": [], "b2_wrong_candidate_correct": [],
               "both_wrong": [], "both_correct": []}
    for iid in sorted(left):
        a, b = left[iid], right[iid]
        require(a["ground_truth"] == b["ground_truth"], "Comparison ground truth mismatch")
        good_a, good_b = a["predicted_class"] == a["ground_truth"], b["predicted_class"] == b["ground_truth"]
        key = ("both_correct" if good_a and good_b else "both_wrong" if not good_a and not good_b
               else "b2_correct_candidate_wrong" if good_a else "b2_wrong_candidate_correct")
        changes[key].append(iid)
    return changes
