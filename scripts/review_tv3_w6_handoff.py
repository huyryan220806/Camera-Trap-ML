"""Read-only TV2 audit of the TV3 W6 pre-training ZIP and pinned Git objects.

Does not extract files, load checkpoints, or run a model. The output is a small
receipt; the ZIP and producer logs stay at their original location.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile


HANDOFF = "8cd97538390a3f55c66193d79e637dfd73ace770"
SOURCE = "127cac5b64d37fdda630a2f84b006a8e420dc9ed"
ZIP_SHA = "030093e92f07fcbe9a2a7ed39eb60919d66250181cd6c0dd9278106927e21ce7"
DATA_SHA = "d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f"
R0_SHA = "acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8"))


def git_bytes(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def flatten(value: object, prefix: str = "") -> dict[str, object]:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            result.update(flatten(child, f"{prefix}.{key}" if prefix else key))
        return result
    return {prefix: value}


def audit(repo: Path, archive: Path, checksum: Path) -> dict:
    result = dict(archive=str(archive), archive_bytes=archive.stat().st_size,
                  archive_sha256=sha(archive.read_bytes()), expected_sha256=ZIP_SHA,
                  checksum_text=checksum.read_text(encoding="utf-8-sig").strip(),
                  handoff_commit=HANDOFF, source_commit=SOURCE)
    result["archive_sha_matches"] = result["archive_sha256"] == ZIP_SHA
    result["checksum_file_matches"] = result["checksum_text"].split() == [ZIP_SHA, archive.name]
    with zipfile.ZipFile(archive) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        unsafe = [name for name in names if name.startswith(("/", "\\")) or "\\" in name or
                  ":" in name or any(p in ("", ".", "..") for p in PurePosixPath(name).parts)]
        result["entry_count"] = len(names)
        result["duplicate_paths"] = sorted({name for name in names if names.count(name) > 1})
        result["unsafe_paths"] = unsafe
        result["symlink_paths"] = [i.filename for i in infos if (i.external_attr >> 16) & 0o170000 == 0o120000]
        result["bad_crc_member"] = z.testzip()
        manifest = json.loads(z.read("manifest_sha256.json"))
        result["manifest_members_match"] = set(manifest) == set(names) - {"manifest_sha256.json"}
        result["manifest_failures"] = []
        result["git_blob_failures"] = []
        result["members"] = {}
        for name in names:
            data = z.read(name)
            result["members"][name] = dict(bytes=len(data), sha256=sha(data))
            if name in manifest and (manifest[name]["bytes"] != len(data) or manifest[name]["sha256"] != sha(data)):
                result["manifest_failures"].append(name)
            if name.startswith("source/"):
                commit, path = SOURCE, name.removeprefix("source/")
            elif name in ("configs/w6/tv3/R1.frozen.json", "configs/w6/tv3/R2.frozen.json",
                          "experiments/w6/tv3_R1.proposal.json", "experiments/w6/tv3_R1_R2.proposal.json",
                          "reports/tv3/w6/smoke/R1_smoke01.json", "reports/tv3/w6/smoke/R2_smoke01.json"):
                commit, path = HANDOFF, name
            else:
                continue
            try:
                if git_bytes(repo, commit, path) != data:
                    result["git_blob_failures"].append(name)
            except subprocess.CalledProcessError:
                result["git_blob_failures"].append(name)
        result["git_blob_matches_count"] = sum(n.startswith("source/") or n in (
            "configs/w6/tv3/R1.frozen.json", "configs/w6/tv3/R2.frozen.json",
            "experiments/w6/tv3_R1.proposal.json", "experiments/w6/tv3_R1_R2.proposal.json",
            "reports/tv3/w6/smoke/R1_smoke01.json", "reports/tv3/w6/smoke/R2_smoke01.json") for n in names) - len(result["git_blob_failures"])
        summary = json.loads(z.read("handoff_summary.json"))
        result["summary_commit_matches"] = summary["handoff_commit"] == HANDOFF and summary["source_commit"] == SOURCE
        result["runs"] = {}
        for run in ("R1", "R2"):
            candidate_name = f"source/configs/w6/tv3/{run}.candidate.json"
            frozen_name = f"configs/w6/tv3/{run}.frozen.json"
            smoke_name = f"reports/tv3/w6/smoke/{run}_smoke01.json"
            candidate = json.loads(z.read(candidate_name))
            frozen = json.loads(z.read(frozen_name))
            smoke = json.loads(z.read(smoke_name))
            preflight = json.loads(z.read(f"outputs/tv3_w6/preflight_{run}_01.json"))
            proposal = json.loads(z.read("experiments/w6/tv3_R1_R2.proposal.json"))
            row = next(x for x in proposal["runs"] if x["run_id"] == run)
            left, right = flatten(candidate), flatten(frozen)
            diffs = {k: dict(candidate=left.get(k), frozen=right.get(k))
                     for k in sorted(set(left) | set(right)) if left.get(k) != right.get(k)}
            allowed = {"status", "runtime.source_sha", "runtime.runtime_lock",
                       "smoke_evidence.path", "smoke_evidence.sha256"}
            result["runs"][run] = dict(
                candidate_raw_sha256=sha(z.read(candidate_name)), candidate_canonical_sha256=canonical(candidate),
                frozen_raw_sha256=sha(z.read(frozen_name)), frozen_canonical_sha256=canonical(frozen),
                differences=diffs, training_affecting_differences=sorted(set(diffs)-allowed),
                data_pin_matches=candidate["dataset_sha256"] == frozen["dataset_sha256"] == DATA_SHA,
                init_pin_matches=candidate["init_checkpoint_sha256"] == frozen["init_checkpoint_sha256"] == R0_SHA,
                smoke_candidate_hash_matches=smoke["config_sha256"] == canonical(candidate) == preflight["config_sha256"],
                smoke_source_matches=smoke["source_index"]["commit"] == SOURCE,
                smoke_source_file_hashes_match=all(
                    sha(z.read("source/" + path)) == expected
                    for path, expected in smoke["source_index"]["files_sha256"].items()),
                runtime_lock_matches=canonical(smoke["runtime"]) == frozen["runtime"]["runtime_lock"],
                preflight_runtime_matches_smoke=preflight["runtime"] == smoke["runtime"],
                local_manifest_hashes_match=all(
                    sha((repo / "data/processed/comparison_v1" / path).read_bytes()) == expected
                    for path, expected in smoke["data"]["files"].items()),
                smoke_path_hash_matches=frozen["smoke_evidence"] == dict(path=smoke_name, sha256=sha(z.read(smoke_name))),
                proposal_frozen_hash_matches=row["config_sha256"] == canonical(frozen),
                proposal_source_matches=row["source_sha"] == SOURCE,
                preflight_counts=preflight["counts"], smoke_parent_count=smoke["parent_count"],
                smoke_crop_count=smoke["crop_count"], smoke_status=smoke["status"],
                preflight_verified_source_images=preflight["data"]["verified_source_images"],
                smoke_gate_verified_source_images=smoke["data"]["verified_source_images"],
                smoke_checks={key: smoke.get(key) for key in ("official_training", "validation_inference", "test_opened",
                    "frozen_unchanged", "strict_load_exact", "resume_exact", "tail_parent_count", "microbatch",
                    "head_dimension", "peak_allocated_vram", "exit_code")},
                trainable_parameters=[n for n, x in smoke["named_parameters"].items() if x["trainable"]],
                missing_or_nonfinite_gradients=[n for n, x in smoke["gradient_evidence"].items()
                                                if x["present"] != smoke["named_parameters"][n]["trainable"] or
                                                x["present"] and not x["finite"]],
            )
        usage = json.loads(z.read("outputs/tv3_w6/usage.json"))
        result["gpu_usage"] = dict(session_count=len(usage["sessions"]),
                                   sessions=[{k: v for k, v in x.items() if k in ("attempt_id", "kind", "seconds", "status", "booking")}
                                             for x in usage["sessions"]],
                                   measured_total_seconds=sum(x["seconds"] for x in usage["sessions"] if x["seconds"] is not None),
                                   unmeasured_count=sum(x["seconds"] is None for x in usage["sessions"]))
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--zip", type=Path, required=True)
    p.add_argument("--checksum", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    repo = Path(__file__).resolve().parents[1]
    result = audit(repo, args.zip, args.checksum)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("members", "runs")}, indent=2, ensure_ascii=False))
    print("Run summaries:", {k: {n: v[n] for n in ("training_affecting_differences", "smoke_status", "missing_or_nonfinite_gradients")}
                             for k, v in result["runs"].items()})


if __name__ == "__main__":
    main()
