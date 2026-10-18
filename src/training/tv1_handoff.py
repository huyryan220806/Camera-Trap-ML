"""Authenticate TV1's native provenance, without inventing a freeze receipt.

Only train/validation JSONL is consumed. Test isolation relies on TV1's
committed aggregate audit, not on reopening test rows in the TV2 process.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess


FORMAT = "tv1_comparison_v1"
BUNDLE = "data/processed/comparison_v1"
PROVENANCE = BUNDLE + "/provenance.json"


def load_handoff(binding: dict, root: Path) -> dict:
    from src.training.b1_gate import GateError, hashed_file, relative_path

    def require(condition, message):
        if not condition:
            raise GateError(message)

    commit = binding.get("commit", "")
    require(isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit), "TV1 requires immutable commit")
    snapshot = relative_path(root, binding["snapshot"])
    require(snapshot.is_dir(), "TV1 snapshot missing")

    def git_bytes(name):
        try:
            return subprocess.check_output(["git", "show", commit + ":" + name], cwd=root, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as exc:
            raise GateError("Cannot authenticate TV1 Git evidence: " + name) from exc

    def checked(name, digest):
        path = hashed_file(snapshot, {"path": name, "sha256": digest})
        return path

    raw = git_bytes(PROVENANCE)
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == binding.get("provenance_sha256"), "TV1 provenance differs from pinned Git hash")
    provenance = json.loads(checked(PROVENANCE, digest).read_text(encoding="utf-8"))
    require(provenance.get("dataset_version") == "comparison_v1", "Unexpected TV1 dataset version")
    require(provenance.get("source_dir") == "data/processed/v2", "Unexpected TV1 source")
    require(provenance.get("config_path") == "configs/comparison_v1.json", "Unexpected TV1 config path")
    verification_path = "reports/tv1_w3/verification.json"
    verification_raw = git_bytes(verification_path)
    verification = json.loads(checked(verification_path, hashlib.sha256(verification_raw).hexdigest()).read_text(encoding="utf-8"))
    require(verification.get("passed") is True and verification.get("dataset_version") == "comparison_v1"
            and verification.get("provenance_sha256") == digest, "TV1 verification does not authenticate provenance")
    require(verification.get("local_images_redecoded") is True
            and verification.get("b1_b2_same_parent_ids") is True
            and verification.get("b1_b2_same_labels_and_splits") is True
            and verification.get("split_changes") == 0, "TV1 verification attestation incomplete")
    policy_path = checked(provenance["config_path"], provenance["config_sha256"])
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    required_policy = {
        "dataset_version": "comparison_v1", "source_dir": "data/processed/v2", "source_seed": 42,
        "min_crop_side": 8, "padding_fraction": 0, "rounding": "python_round_half_even_then_clip",
        "bad_box_policy": "exclude_entire_image_from_both_models", "multi_box_policy": "all_boxes_same_species",
        "b2_train_weight": "1 / number_of_crops_in_parent_image", "evaluation_unit": "image_id",
        "b2_evaluation_aggregation": "mean_class_probabilities_over_all_parent_crops",
        "within_split_exact_duplicates": "retain_and_report", "test_policy": "integrity_checks_only_no_model_selection"}
    require(policy == required_policy, "Unsupported TV1 geometry/data policy")
    files = provenance["files_sha256"]
    expected_names = {"audit.json", "class_map.json", "duplicates.json", "excluded.jsonl", "manifest.jsonl", "policy.json", "summary.json"}
    expected_names.update(prefix + split + ".jsonl" for prefix in ("", "b1/", "b2/") for split in ("train", "val", "test"))
    require(set(files) == expected_names, "TV1 file inventory incomplete")
    for name, value in files.items():
        require(re.fullmatch(r"[0-9a-f]{64}", value), "Invalid TV1 file hash")
        if name == "manifest.jsonl" or name.endswith("test.jsonl"):
            continue
        checked(BUNDLE + "/" + name, value)
    for name in ("train.jsonl", "val.jsonl", "class_map.json", "provenance.json", "audit.json", "summary.json", "excluded_v2.jsonl", "duplicates.json"):
        checked("data/processed/v2/" + name, provenance["source_files_sha256"][name])
    for name in ("comparison_data.py", "freeze_comparison.py", "validate_comparison.py"):
        checked("scripts/" + name, provenance["script_sha256"][name])
    require(json.loads((snapshot / BUNDLE / "policy.json").read_text(encoding="utf-8")) == policy, "Bundle policy differs")
    for split in ("train", "val"):
        # Current release retains all source images. Other selection policies
        # need explicit accounting support, never silently drop source rows.
        require(files[split + ".jsonl"] == provenance["source_files_sha256"][split + ".jsonl"], "TV1 source membership changed; review exclusion adapter")
    require((snapshot / BUNDLE / "excluded.jsonl").stat().st_size == 0, "Nonempty exclusion ledger needs scoped review")
    cmap = json.loads((snapshot / BUNDLE / "class_map.json").read_text(encoding="utf-8"))
    require(cmap == json.loads((snapshot / "data/processed/v2/class_map.json").read_text(encoding="utf-8")), "Source class mapping changed")
    audit = json.loads((snapshot / BUNDLE / "audit.json").read_text(encoding="utf-8"))
    for scope in (audit, audit.get("source_audit", {}), verification):
        require(scope.get("cross_split_overlap") == dict.fromkeys(("image_id", "file_name", "seq_id", "location"), 0), "TV1 all-split leakage attestation failed")
    for scope in (audit, audit["source_audit"]):
        require(scope.get("metadata_leakage_check_passed") is True and scope.get("image_content_duplicates_checked") is True
                and scope.get("duplicate_image_ids") == 0 and scope.get("duplicate_file_paths") == 0, "TV1 audit incomplete")
    require(audit.get("b1_b2_same_parent_ids") is True and audit.get("b1_b2_same_labels_and_splits") is True, "TV1 view attestation failed")
    summary = json.loads((snapshot / BUNDLE / "summary.json").read_text(encoding="utf-8"))
    require(summary.get("split_changes") == 0 and summary.get("excluded") == 0
            and summary.get("requested") == summary.get("retained") == verification.get("retained") == audit.get("rows")
            and verification.get("requested") == summary["requested"] and verification.get("excluded") == 0, "TV1 accounting differs")
    mapping = {"train": "b1/train.jsonl", "val": "b1/val.jsonl", "source_train": "train.jsonl", "source_val": "val.jsonl",
               "crop_train": "b2/train.jsonl", "crop_val": "b2/val.jsonl", "class_map": "class_map.json",
               "excluded": "excluded.jsonl", "quality_audit": "audit.json"}
    mapped = {key: {"path": (snapshot / BUNDLE / name).relative_to(root.resolve()).as_posix(), "sha256": files[name]} for key, name in mapping.items()}
    return {"format": FORMAT, "dataset_version": "comparison_v1", "binding": dict(binding), "files": mapped,
            "provenance_sha256": digest, "policy": policy, "summary": summary,
            "test_verification_scope": "TV1 committed aggregate attestation only; test rows/pixels never opened"}
