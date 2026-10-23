"""Read-only W4 evidence audit. Never imports an inference or training entry point."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "reports/tv2/w4_evidence"
REFS = {"main": "origin/main", "tv1": "origin/feat/metadata-split",
        "tv2": "origin/feat/baseline", "tv3": "origin/feat/crop-classifier",
        "tv4": "origin/feat/demo"}
REQUIRED = {
    "tv1": ["docs/handoff_tv1_w4.md", "reports/tv1_w4/REPORT.md",
            "reports/tv1_w4/inventory.json", "reports/tv1_w4/quality_checks.json",
            "configs/model_locks/b2_w3.json"],
    "tv3": ["reports/tv3/TV3_W3_CHECKPOINT.md", "reports/tv3/TV3_W4_DECISION.md",
            "reports/tv3/error_analysis_b2.md", "reports/tv3/error_analysis_b3.md",
            "reports/tv3/error_analysis_b2.json", "reports/tv3/error_analysis_b3.json",
            "reports/tv3/validation_comparison.json", "configs/b3_class_weighted.json",
            "scripts/train_b3.py", "scripts/error_analysis.py", "tests/test_tv3_w4.py",
            "outputs/b3_class_weighted/b3_run01/validation_comparison.json",
            "outputs/b3_class_weighted/b3_run01/train_log.jsonl",
            "outputs/b3_class_weighted/b3_run01/best_model.pt"],
    "tv2": [f"reports/tv2/{n}.md" for n in
            ("TV2_W3", "TV2_W3_CHECKPOINT", "TV2_W3_COMPARISON")],
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def audit() -> dict:
    commits = {name: git("rev-parse", ref).decode().strip() for name, ref in REFS.items()}
    result = {"refs": commits, "test_inference_performed": False, "sources": {}}
    for owner, paths in REQUIRED.items():
        ref = commits[owner]
        tree = set(git("ls-tree", "-r", "--name-only", ref).decode().splitlines())
        records = {}
        for path in paths:
            if path not in tree:
                records[path] = {"status": "NOT FOUND", "commit": ref}
                continue
            content = git("show", f"{ref}:{path}")
            records[path] = {"status": "FOUND", "commit": ref,
                             "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
            # Keep exact text/JSON sources locally for review; do not copy source photos or weights.
            dest = ROOT / "outputs/tv2_w4/upstream" / owner / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)
        result["sources"][owner] = records
    result["tv4_w4_paths"] = [p for p in git("ls-tree", "-r", "--name-only", commits["tv4"]).decode().splitlines()
                                  if "w4" in p.lower() or "week4" in p.lower()]
    comp = ROOT / "data/processed/comparison_v1"
    provenance = json.loads((comp / "provenance.json").read_text(encoding="utf-8"))
    result["provenance_sha256"] = sha(comp / "provenance.json")
    result["frozen_hashes"] = {p: {"expected": h, "actual": sha(comp / p), "matches": sha(comp / p) == h}
                               for p, h in provenance["files_sha256"].items()}
    splits = {s: rows(comp / f"{s}.jsonl") for s in ("train", "val", "test")}
    result["splits"] = {}
    for split, parents in splits.items():
        crops = rows(comp / "b2" / f"{split}.jsonl")
        b1 = rows(comp / "b1" / f"{split}.jsonl")
        ids = {r["image_id"] for r in parents}
        counts = Counter(r["class_id"] for r in crops)
        result["splits"][split] = {
            "images": len(parents), "sequences": len({r["seq_id"] for r in parents}),
            "locations": len({r["location"] for r in parents}), "crops": len(crops),
            "parent_counts": dict(sorted(Counter(r["class_id"] for r in parents).items())),
            "crop_counts": dict(sorted(counts.items())),
            "b1_b2_parent_population_matches": ids == {r["image_id"] for r in b1} == {r["image_id"] for r in crops},
            "duplicate_parent_ids": len(parents) - len(ids),
            "local_source_files_present": sum((ROOT / r["quality"]["local_path"]).is_file() for r in parents),
            "source_rasters_decoded": False,
        }
        if split == "train":
            inverse = {i: len(crops) / (8 * counts[i]) for i in range(8)}
            mean = sum(inverse.values()) / 8
            result["splits"][split]["normalized_crop_inverse_frequency_weights"] = {i: inverse[i] / mean for i in range(8)}
    result["cross_split_overlap"] = {}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        result["cross_split_overlap"][f"{a}/{b}"] = {
            field: len({r[field] for r in splits[a]} & {r[field] for r in splits[b]})
            for field in ("image_id", "file_name", "location", "seq_id")}
        result["cross_split_overlap"][f"{a}/{b}"]["file_sha256"] = len(
            {r["quality"]["sha256"] for r in splits[a]} & {r["quality"]["sha256"] for r in splits[b]})
    result["checkpoint_candidates"] = {}
    candidates = ["experiments/B0_run01/checkpoints/best_model.pth", "experiments/B1_run01/checkpoints/best_model.pth",
                  "outputs/b2_crop_classifier/b2_run01/best_model.pt", "outputs/tv3/best_model.pt",
                  "outputs/tv4/models/b2_approved.pth", "outputs/b3_class_weighted/b3_run01/best_model.pt"]
    for name in candidates:
        p = ROOT / name
        result["checkpoint_candidates"][name] = ({"status": "FOUND", "bytes": p.stat().st_size, "sha256": sha(p)}
                                                  if p.is_file() else {"status": "NOT FOUND"})
    write(EVIDENCE / "repository_audit.json", result)
    return result


def snapshot_tv3() -> None:
    """Build an ignored isolated review directory without changing any member branch."""
    dest = ROOT / "outputs/tv2_w4/tv3_review"
    dest.mkdir(parents=True, exist_ok=False)
    content = git("archive", REFS["main"])
    with tarfile.open(fileobj=io.BytesIO(content)) as archive:
        for member in archive.getmembers():
            target = (dest / member.name).resolve()
            if not target.is_relative_to(dest.resolve()) or member.issym() or member.islnk():
                raise ValueError("Unsafe archive member")
            if member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.extractfile(member).read())
    # Only W4 files introduced on TV3; do not overlay the old branch's shared files.
    for path in REQUIRED["tv3"]:
        source = ROOT / "outputs/tv2_w4/upstream/tv3" / path
        if source.is_file():
            target = dest / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-tv3", action="store_true")
    args = parser.parse_args()
    summary = audit()
    if args.snapshot_tv3:
        snapshot_tv3()
    print(json.dumps({"refs": summary["refs"], "splits": summary["splits"],
                      "tv4_w4_paths": summary["tv4_w4_paths"],
                      "checkpoint_candidates": summary["checkpoint_candidates"]}, indent=2))
