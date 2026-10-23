"""TV2 W4: fail-closed, immutable, image-level B2 Test evaluation.

Importing this module does not import torch, decode an image, or read Test rows.
Only a committed final selection and a matching committed protocol enable inference.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import time

B2_SHA256 = "8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5"
PREPROCESSING = {"resize_mode": "center_crop", "resize_size": 256, "image_size": 224,
                 "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}
AGGREGATION = "mean_softmax_all_valid_crops_then_argmax"
METRICS = {"labels": list(range(8)), "zero_division": 0, "macro_average": "unweighted_all_8_classes",
           "round_before_average": False, "confusion_matrix": "rows_true_columns_predicted",
           "tie_break": "lowest_class_id", "loss": "not_reported"}
CODE_FILES = ("src/evaluation/w4_test.py", "scripts/evaluate_w4_test.py", "src/evaluation/metrics.py",
              "src/demo/classifier.py", "src/data/b2_dataset.py", "src/models/b2_classifier.py")


class EvaluationBlocked(ValueError):
    """A prerequisite failed before Test inference."""


def require(condition, message):
    if not condition:
        raise EvaluationBlocked(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def protocol_contract_digest(protocol):
    """Bind every protocol field except its reverse full-byte selection hash (no circular hash)."""
    content = {k: v for k, v in protocol.items() if k != "model_selection_lock_sha256"}
    return hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def save_json(path, value):
    """Atomic replacement of this run's state only; never writes a frozen input."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def repository_file(root, name):
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), f"Missing/unsafe repository input: {name}")
    return path


def committed_bytes(root, path):
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    try:
        content = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise EvaluationBlocked(f"Input must be committed before Test: {relative}") from exc
    require(content == path.read_bytes(), f"Uncommitted change to frozen input: {relative}")
    return content


def verify_checkpoint(path, expected_sha256, expected_bytes):
    path = Path(path)
    require(path.is_file(), "Verified B2 checkpoint not available locally")
    require(path.stat().st_size == expected_bytes and digest(path) == expected_sha256,
            "Checkpoint SHA-256/size mismatch")


def verify_gate(root, selection_path, protocol_path, checkpoint):
    """Check locks, code, checkpoint bytes and frozen metadata BEFORE decoding Test."""
    root, checkpoint = Path(root).resolve(), Path(checkpoint)
    selection_path, protocol_path = Path(selection_path), Path(protocol_path)
    selection, protocol = load_json(selection_path), load_json(protocol_path)
    require(selection.get("status") in ("LOCKED", "FINAL MODEL LOCKED – B2") and selection.get("final_selection_closed") is True
            and selection.get("blockers") == [], "FINAL MODEL LOCK PENDING: " + str(selection.get("blockers")))
    require(protocol.get("status") == "LOCKED", "Evaluation protocol is not LOCKED")
    require(selection.get("model") == "B2" and selection.get("run_id") == "b2_run01", "Unexpected final model/run")
    require(selection.get("evaluation_models") == protocol.get("evaluation_models") == ["B2"], "Only preregistered B2 permitted")
    require(selection.get("checkpoint_sha256") == protocol.get("checkpoint_sha256") == B2_SHA256, "Unapproved checkpoint hash")
    require(selection.get("selection_split") == "val" and selection.get("test_used_for_selection") is False,
            "Model must be selected on Validation only")
    require(selection.get("review_status") in ("PASS", "PASS WITH LIMITATIONS"), "Selection evidence review pending")
    require(all(selection.get("evidence_verified", {}).get(k) is True for k in
                ("b2_checkpoint_metadata", "b2_independent_reload", "decision_before_test")), "Required B2 selection evidence missing")
    require(isinstance(selection.get("locked_utc"), str) and selection["locked_utc"], "Lock timestamp missing")
    require(protocol.get("model_selection_lock_sha256") == digest(selection_path), "Selection/protocol hash mismatch")
    require(protocol.get("evaluation_unit") == "source_image" and protocol.get("aggregation") == AGGREGATION,
            "Image aggregation policy differs")
    require(protocol.get("metrics") == METRICS, "Metric contract differs")
    require(protocol.get("preprocessing") == selection.get("preprocessing") == PREPROCESSING, "Preprocessing differs")
    require(protocol.get("threshold_policy") == {"status": "NOT_SELECTED", "value": None,
                "classification": "argmax_all_images", "calibrated": False}, "Unvalidated threshold policy")
    require(protocol.get("run_id") == "W4_test_eval01", "Official run ID differs from frozen plan")
    require(protocol.get("execution") == {"device": "cpu", "crop_batch_size": 32, "num_threads": 4, "seed": 42},
            "Execution differs from frozen plan")
    require(protocol.get("code_sha256") and set(protocol["code_sha256"]) == set(CODE_FILES), "Incomplete evaluator code hashes")
    for file in (selection_path, protocol_path):
        require(file.resolve().is_relative_to(root), "Lock/protocol must be inside repository")
        committed_bytes(root, file)
    for name, expected in protocol["code_sha256"].items():
        path = repository_file(root, name)
        require(digest(path) == expected, f"Evaluation code changed: {name}")
        committed_bytes(root, path)
    for name, expected in selection.get("decision_evidence_sha256", {}).items():
        path = repository_file(root, name)
        require(digest(path) == expected, f"Decision evidence changed: {name}")
        committed_bytes(root, path)
    require(selection.get("decision_evidence_sha256"), "Decision evidence files missing")
    verify_selection_policy(root, selection)
    comp = root / "data/processed/comparison_v1"
    provenance = load_json(comp / "provenance.json")
    require(provenance.get("dataset_version") == "comparison_v1", "Wrong dataset version")
    require(digest(comp / "provenance.json") == selection.get("provenance_sha256") == protocol.get("provenance_sha256"),
            "Frozen data provenance changed")
    for name, expected in provenance["files_sha256"].items():
        require(digest(repository_file(comp, name)) == expected, f"Frozen dataset changed: {name}")
    require(digest(root / "configs/b2_crop_classifier.json") == selection.get("config_sha256"), "B2 config changed")
    require(protocol.get("test_manifest_sha256") == digest(comp / "test.jsonl") and
            protocol.get("b2_test_manifest_sha256") == digest(comp / "b2/test.jsonl"), "Test manifest hash differs")
    class_map = load_json(comp / "class_map.json")
    require(set(class_map) == {str(i) for i in range(8)} and len(set(class_map.values())) == 8, "Invalid class order")
    require(selection.get("class_map") == protocol.get("class_map") == class_map, "Class mapping changed")
    require(selection.get("checkpoint_bytes") == 89548866, "Unapproved checkpoint size")
    require(selection.get("protocol_contract_sha256") == protocol_contract_digest(protocol),
            "Protocol changed after selection lock")
    verify_checkpoint(checkpoint, B2_SHA256, 89548866)
    return selection, protocol


def verify_selection_policy(root, selection):
    """Team selection closes B2; it does not turn unselected B3 diagnostics into PASS."""
    evidence = selection["decision_evidence_sha256"]
    decision_path = selection.get("team_decision_record")
    require(decision_path in evidence, "Committed B2 team decision missing")
    decision = load_json(repository_file(root, decision_path))
    require(decision.get("source_kind") == "user_reported_team_decision" and
            decision.get("final_model_selection") == "B2 SELECTED BY TEAM" and
            decision.get("run_id") == "b2_run01" and decision.get("selection_split") == "val" and
            decision.get("test_used_for_selection") is False and decision.get("evaluation_models") == ["B2"],
            "Explicit Validation-only B2 team decision missing")
    require(decision.get("b3_limitation_accepted_for_model_selection") is True and
            decision.get("b3_selected_for_test") is False and
            decision.get("b3_reference_reproducibility") == "FAIL / UNRESOLVED",
            "B3 limitation acceptance missing or technical FAIL concealed")
    try:
        recorded = datetime.fromisoformat(decision["recorded_utc"])
        locked = datetime.fromisoformat(selection["locked_utc"])
        require(recorded.utcoffset() == locked.utcoffset() == timezone.utc.utcoffset(None)
                and recorded <= locked <= datetime.now(timezone.utc), "Decision/lock chronology invalid")
    except (KeyError, TypeError, ValueError) as exc:
        raise EvaluationBlocked("Decision/lock chronology invalid") from exc
    b2_path = selection.get("b2_validation_evidence")
    require(b2_path in evidence, "Independent B2 Validation evidence missing")
    b2 = load_json(repository_file(root, b2_path))
    require(b2.get("status") == "PASS" and b2.get("model") == "B2" and
            b2.get("checkpoint_sha256") == B2_SHA256 and
            b2.get("provenance_sha256") == selection.get("provenance_sha256") and
            b2.get("preprocessing") == selection.get("preprocessing") and
            b2.get("class_map") == selection.get("class_map"), "Independent B2 Validation not verified")
    b3 = selection.get("b3_reproducibility", {})
    require(b3.get("status") == "UNRESOLVED / LIMITATION ACCEPTED" and
            b3.get("reference_reproduced") is False and b3.get("selected_for_test") is False,
            "B3 reproducibility FAIL must remain disclosed and excluded from Test")
    require(set(b3.get("diagnostic_evidence", {})) == {"CPU", "CUDA"}, "B3 diagnostic evidence missing")
    for name in b3["diagnostic_evidence"].values():
        require(name in evidence, "B3 FAIL evidence must be pinned")
        diagnostic = load_json(repository_file(root, name))
        require(diagnostic.get("status") == "FAIL" and diagnostic.get("model") == "B3",
                "B3 historical technical FAIL must not become PASS")


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_population(splits, crops, class_map):
    """Validate every source/crop association and leakage dimension without reading pixels."""
    require(set(splits) == {"train", "val", "test"}, "Need all split manifests for leakage audit")
    for split, rows in splits.items():
        require(rows, f"Empty {split} split")
        require(len({r["image_id"] for r in rows}) == len(rows), f"Duplicate image ID in {split}")
        require(len({r["file_name"] for r in rows}) == len(rows), f"Duplicate source path in {split}")
        for row in rows:
            require(row.get("split") == split and type(row.get("class_id")) is int and
                    str(row["class_id"]) in class_map and class_map[str(row["class_id"])] == row.get("label"),
                    "Source split/class mismatch")
            require(all(row.get(k) for k in ("image_id", "file_name", "location", "seq_id")) and
                    row.get("quality", {}).get("sha256"), "Incomplete leakage metadata")
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        for field in ("image_id", "file_name", "location", "seq_id"):
            require(not ({r[field] for r in splits[a]} & {r[field] for r in splits[b]}), f"Leakage: {a}/{b} {field}")
        require(not ({r["quality"]["sha256"] for r in splits[a]} & {r["quality"]["sha256"] for r in splits[b]}),
                f"Leakage: {a}/{b} file_sha256")
    parents = {r["image_id"]: r for r in splits["test"]}
    require(crops and len({r["crop_id"] for r in crops}) == len(crops), "Empty/duplicate crops")
    groups = defaultdict(list)
    for crop in crops:
        require(crop["image_id"] in parents, "Crop references an unknown Test parent")
        parent = parents[crop["image_id"]]
        require(all(crop.get(k) == parent.get(k) for k in ("class_id", "label", "split", "file_name", "quality", "location", "seq_id")),
                "Crop/parent metadata differs")
        box = crop.get("bbox_xyxy")
        require(isinstance(box, list) and len(box) == 4 and all(type(v) is int for v in box), "Invalid integer crop")
        l, t, r, b = box
        require(0 <= l < r <= parent["width"] and 0 <= t < b <= parent["height"], "Crop outside source raster")
        groups[crop["image_id"]].append(crop)
    require(set(groups) == set(parents), "Missing Test parent crops")
    for group in groups.values():
        require(all(r.get("parent_crop_count") == len(group) and
                    math.isclose(r.get("sample_weight", -1), 1 / len(group), abs_tol=1e-12) for r in group),
                "Crop count/weight differs")
    return parents, groups


def aggregate_predictions(crop_rows, expected_crops):
    """One mean softmax vector per source image; no per-crop or majority-vote metric."""
    expected = {r["crop_id"]: r for r in expected_crops}
    require(len(expected) == len(expected_crops) and expected, "Expected crops must be nonempty and unique")
    seen, groups = set(), defaultdict(list)
    for row in crop_rows:
        cid = row["crop_id"]
        require(cid in expected and cid not in seen, "Unexpected/duplicate crop prediction")
        seen.add(cid)
        ref = expected[cid]
        require(row["image_id"] == ref["image_id"] and row["class_id"] == ref["class_id"], "Prediction/label association differs")
        p = row["probabilities"]
        require(len(p) == 8 and all(math.isfinite(v) and 0 <= v <= 1 for v in p)
                and math.isclose(sum(p), 1, abs_tol=1e-5), "Invalid softmax vector")
        groups[row["image_id"]].append(row)
    require(seen == set(expected), "Missing crop predictions")
    output = []
    for image_id, rows in sorted(groups.items()):
        require(len({r["class_id"] for r in rows}) == 1, "Inconsistent parent labels")
        p = [sum(r["probabilities"][c] for r in rows) / len(rows) for c in range(8)]
        predicted = max(range(8), key=p.__getitem__)  # first / lowest ID wins exact ties
        output.append({"image_id": image_id, "true_class_id": rows[0]["class_id"], "predicted_class_id": predicted,
                       "confidence": p[predicted], "probabilities": p, "num_crops": len(rows)})
    return output


def metrics_and_integrity(predictions, parents, class_map_path):
    from src.evaluation.metrics import compute_metrics
    require(predictions and len({p["image_id"] for p in predictions}) == len(predictions)
            and {p["image_id"] for p in predictions} == set(parents), "Need exactly one prediction per Test image")
    require(all(p["true_class_id"] == parents[p["image_id"]]["class_id"] for p in predictions), "Ground truth differs")
    result = compute_metrics([p["true_class_id"] for p in predictions],
                             [p["predicted_class_id"] for p in predictions], class_map_path)
    cm = result["confusion_matrix"].tolist()
    require(result["labels"] == list(range(8)) and len(cm) == 8 and all(len(r) == 8 for r in cm), "Need fixed 8x8 matrix")
    require(sum(map(sum, cm)) == len(parents), "Confusion matrix population mismatch")
    per_class = []
    for c, name in enumerate(result["target_names"]):
        support, predicted = sum(cm[c]), sum(row[c] for row in cm)
        tp = cm[c][c]
        precision, recall = tp / predicted if predicted else 0., tp / support if support else 0.
        f1 = 2 * tp / (support + predicted) if support + predicted else 0.
        original = result["classification_report"][name]
        require(original["support"] == support and all(math.isclose(original[k], v, abs_tol=1e-12)
                for k, v in (("precision", precision), ("recall", recall), ("f1-score", f1))), "Per-class metrics/CM mismatch")
        per_class.append({"class_id": c, "label": name, "precision": precision, "recall": recall,
                          "f1": f1, "support": support, "errors": support - tp})
    require(math.isclose(result["accuracy"], sum(cm[i][i] for i in range(8)) / len(parents), abs_tol=1e-12), "Accuracy mismatch")
    for key, column in (("macro_f1", "f1"), ("macro_precision", "precision"), ("macro_recall", "recall")):
        require(math.isclose(result[key], sum(row[column] for row in per_class) / 8, abs_tol=1e-12), "Macro metric mismatch")
    return {key: result[key] for key in ("macro_f1", "macro_precision", "macro_recall", "accuracy")}, cm, per_class


def reserve_run(root, run_id):
    """One official run per repository, including interrupted runs. No unsafe resume."""
    require(run_id == "W4_test_eval01", "Run ID not preregistered")
    parent = Path(root) / "outputs/tv2_w4"
    parent.mkdir(parents=True, exist_ok=True)
    marker = parent / "OFFICIAL_TEST_STARTED.json"
    try:
        with marker.open("x", encoding="utf-8") as handle:
            json.dump({"run_id": run_id, "resume_supported": False,
                       "reserved_utc": datetime.now(timezone.utc).isoformat()}, handle)
    except FileExistsError as exc:
        raise EvaluationBlocked("An official evaluation was already reserved; inspect state, do not rerun") from exc
    run = parent / run_id
    run.mkdir(exist_ok=False)
    return run


def evaluate(root, selection_path, protocol_path, checkpoint):
    """The gate is deliberately the first operation; no Test inference before it."""
    root = Path(root).resolve()
    selection, protocol = verify_gate(root, selection_path, protocol_path, checkpoint)
    comp = root / "data/processed/comparison_v1"
    splits = {s: read_rows(comp / f"{s}.jsonl") for s in ("train", "val", "test")}
    crops = read_rows(comp / "b2/test.jsonl")
    parents, groups = validate_population(splits, crops, protocol["class_map"])
    actual_population = {"images": len(parents), "crops": len(crops),
                         "sequences": len({r["seq_id"] for r in parents.values()}),
                         "locations": len({r["location"] for r in parents.values()}),
                         "per_class_support": dict(sorted(Counter(str(r["class_id"]) for r in parents.values()).items()))}
    require(actual_population == protocol["expected_population"], "Test population differs from frozen plan")
    # All source hashes and full RGB decode are required before reserving the one official run.
    from PIL import Image
    for row in parents.values():
        path = repository_file(root, row["quality"]["local_path"])
        require(digest(path) == row["quality"]["sha256"], "Source image SHA mismatch: " + row["image_id"])
        with Image.open(path) as image:
            image.load()
            require(image.size == (row["width"], row["height"]), "Source raster dimensions differ")
    import torch
    from src.demo.classifier import checkpoint_model
    torch.manual_seed(42)
    torch.set_num_threads(4)
    load_start = time.perf_counter()
    ck = torch.load(checkpoint, map_location="cpu", weights_only=True)
    require(ck.get("epoch") == selection["best_epoch"] == 21, "Checkpoint epoch mismatch")
    entry = {"checkpoint_format": "tv3-native-v1", "training_input": "crop", "preprocessing": PREPROCESSING,
             "provenance_sha256": selection["provenance_sha256"]}
    names = [protocol["class_map"][str(i)] for i in range(8)]
    model, transform = checkpoint_model(ck, "B2", entry, names)
    load_seconds = time.perf_counter() - load_start
    require(digest(checkpoint) == B2_SHA256, "Checkpoint changed during load")
    # Recheck committed locks and bytes immediately before the irreversible first Test forward.
    verify_gate(root, selection_path, protocol_path, checkpoint)
    run = reserve_run(root, protocol["run_id"])
    save_json(run / "evaluation_config.json", protocol)
    import platform
    save_json(run / "environment.json", {"python": platform.python_version(), "torch": torch.__version__,
              "cuda_build": torch.version.cuda, "cuda_available": torch.cuda.is_available(),
              "evaluation_device": "cpu", "cpu": platform.processor(), "threads": torch.get_num_threads()})
    save_json(run / "checkpoint_verification.json", {"sha256": digest(checkpoint), "bytes": Path(checkpoint).stat().st_size,
                                                     "epoch": ck["epoch"], "metadata": "PASS"})
    state = {"status": "RUNNING", "test_images_forwarded": 0, "resume_supported": False,
             "started_utc": datetime.now(timezone.utc).isoformat()}
    save_json(run / "state.json", state)
    predictions, forward_seconds = [], 0.
    start = time.perf_counter()
    try:
        with (run / "progress.jsonl").open("x", encoding="utf-8") as journal, torch.inference_mode():
            for image_id, group in sorted(groups.items()):
                row = parents[image_id]
                path = repository_file(root, row["quality"]["local_path"])
                require(digest(path) == row["quality"]["sha256"], "Source changed before inference")
                with Image.open(path) as source:
                    rgb = source.convert("RGB")
                    tensors = [transform(rgb.crop(tuple(c["bbox_xyxy"]))) for c in group]
                output = []
                for offset in range(0, len(tensors), 32):
                    batch = torch.stack(tensors[offset:offset + 32])
                    tick = time.perf_counter()
                    logits = model(batch)
                    require(logits.shape == (len(batch), 8) and torch.isfinite(logits).all().item(), "Invalid logits")
                    probs = logits.softmax(dim=1).tolist()
                    forward_seconds += time.perf_counter() - tick
                    for crop, p in zip(group[offset:offset + 32], probs):
                        output.append({**{k: crop[k] for k in ("crop_id", "image_id", "class_id")}, "probabilities": p})
                prediction = aggregate_predictions(output, group)[0]
                predictions.append(prediction)
                journal.write(json.dumps(prediction, allow_nan=False) + "\n")
                journal.flush()
                state["test_images_forwarded"] = len(predictions)
                save_json(run / "state.json", state)
        total_seconds = time.perf_counter() - start
        metrics, cm, per_class = metrics_and_integrity(predictions, parents, comp / "class_map.json")
        save_json(run / "test_metrics.json", {**metrics, "support": len(parents), "correct": sum(cm[i][i] for i in range(8)),
                  "device": "cpu", "model_load_seconds": load_seconds, "forward_softmax_seconds": forward_seconds,
                  "source_hash_decode_preprocess_inference_journal_seconds": total_seconds,
                  "images_per_second_excluding_load": len(parents) / total_seconds})
        for name, values in (("per_class_metrics.csv", per_class), ("test_predictions.csv", [
                {k: p[k] for k in ("image_id", "true_class_id", "predicted_class_id", "confidence", "num_crops")} for p in predictions])):
            with (run / name).open("x", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(values[0]))
                writer.writeheader()
                writer.writerows(values)
        with (run / "confusion_matrix.csv").open("x", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["true_class_id/predicted_class_id", *range(8)])
            writer.writerows([[i, *row] for i, row in enumerate(cm)])
        from src.evaluation.metrics import plot_confusion_matrix
        import matplotlib.pyplot as plt
        fig, _ = plot_confusion_matrix([p["true_class_id"] for p in predictions], [p["predicted_class_id"] for p in predictions],
                                       run / "confusion_matrix.png", comp / "class_map.json", title="B2 Test — source images")
        plt.close(fig)
        lines = ["# Official B2 Test errors", "", "All predictions retained. No model/threshold changes permitted.", "",
                 "| Class | Precision | Recall | Errors / support |", "|---|---:|---:|---:|"]
        lines += [f"| {r['label']} | {r['precision']:.6f} | {r['recall']:.6f} | {r['errors']} / {r['support']} |" for r in per_class]
        lines += ["", "## Directed confusion pairs", ""]
        pairs = sorted(((cm[a][b], a, b) for a in range(8) for b in range(8) if a != b and cm[a][b]), reverse=True)
        lines += [f"- {names[a]} → {names[b]}: {n}" for n, a, b in pairs]
        lines += ["", "## Manifest geometry subgroups", "",
                  "Flags use frozen integer pixel crop boxes; groups may overlap. No samples excluded.", "",
                  "| Subgroup | Images | Errors | Error rate |", "|---|---:|---:|---:|"]
        for label, condition in (
            ("multiple_crops", lambda p, g: len(g) > 1),
            ("box_area_below_1_percent", lambda p, g: any(
                (c["bbox_xyxy"][2] - c["bbox_xyxy"][0]) * (c["bbox_xyxy"][3] - c["bbox_xyxy"][1])
                / (p["width"] * p["height"]) < .01 for c in g)),
            ("box_within_1_pixel_of_edge", lambda p, g: any(
                min(c["bbox_xyxy"][0], c["bbox_xyxy"][1], p["width"] - c["bbox_xyxy"][2],
                    p["height"] - c["bbox_xyxy"][3]) <= 1 for c in g))):
            subgroup = [p for p in predictions if condition(parents[p["image_id"]], groups[p["image_id"]])]
            errors = sum(p["true_class_id"] != p["predicted_class_id"] for p in subgroup)
            rate = f"{errors / len(subgroup):.8f}" if subgroup else "N/A (no images)"
            lines.append(f"| {label} | {len(subgroup)} | {errors} | {rate} |")
        lines += ["", "## Verifiable error examples", ""]
        for p in predictions:
            if p["true_class_id"] != p["predicted_class_id"]:
                lines.append(f"- {p['image_id']}: true={names[p['true_class_id']]}, predicted={names[p['predicted_class_id']]}, "
                             f"softmax_score={p['confidence']:.8f}, crops={p['num_crops']}; source=frozen manifest; raster not visually adjudicated.")
        lines += ["", "No night/visibility or detector-miss claim follows from this closed-set ground-truth-box evaluation.",
                  "Images share sequences/locations; class-balanced sample is not natural prevalence; one known within-Test RGB duplicate pair retained.",
                  "Softmax is uncalibrated; image counts do not estimate animal individuals. MegaDetector demo is a separate evaluation."]
        (run / "error_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        (run / "evaluation_log.txt").write_text("B2 eval/inference_mode. One forward per crop. No training. All 8 labels. Integrity checks PASS.\n", encoding="utf-8")
        (run / "test_evaluation_log.txt").write_bytes((run / "evaluation_log.txt").read_bytes())
        state.update(status="COMPLETE", artifact_integrity="PASS", completed_utc=datetime.now(timezone.utc).isoformat())
        save_json(run / "state.json", state)
        save_json(run / "evaluation_manifest.json", {"protocol_sha256": digest(protocol_path),
                  "selection_sha256": digest(selection_path), "files_sha256": {p.name: digest(p) for p in run.iterdir() if p.is_file()}})
    except BaseException as exc:
        state.update(status="INTERRUPTED_REQUIRES_REVIEW", error=repr(exc))
        save_json(run / "state.json", state)
        raise
    return run
