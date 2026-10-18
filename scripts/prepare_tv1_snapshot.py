"""Copy a pinned TV1 train/val snapshot and validator code without merging branches."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def prepare(commit, output):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Use a full immutable commit SHA")
    output = output.resolve()
    if not output.is_relative_to(ROOT / "outputs") or output.exists():
        raise ValueError("Use a new directory within ignored outputs/; never overwrite snapshots")
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", commit], cwd=ROOT, text=True).splitlines()
    prefixes = ("scripts/", "src/", "configs/", "docs/", "reports/tv1_w3/", "data/processed/v2/", "data/processed/comparison_v1/")
    selected = []
    omitted = []
    for name in names:
        if not (name.startswith(prefixes) or name in ("requirements.txt", "requirements-tv2.txt")):
            continue
        if name.endswith(".jsonl") and Path(name).name not in ("train.jsonl", "val.jsonl", "excluded.jsonl", "excluded_v2.jsonl"):
            omitted.append(name)
            continue
        destination = (output / name).resolve()
        if not destination.is_relative_to(output):
            raise ValueError("Unsafe Git path")
        selected.append((name, destination))
    if not any(name == "data/processed/comparison_v1/provenance.json" for name, _ in selected):
        raise ValueError("TV1 comparison provenance missing")
    output.mkdir(parents=True, exist_ok=False)
    files = []
    for name, path in selected:
        data = subprocess.check_output(["git", "show", commit + ":" + name], cwd=ROOT)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
        files.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    report = {"commit": commit, "files": files, "omitted_test_or_mixed_jsonl": omitted,
              "scope": "Train/validation plus validator code and aggregate QA. Do not run all-split validator."}
    with (output / "SNAPSHOT_MANIFEST.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    return {"commit": commit, "output": str(output), "files_copied": len(files), "omitted": len(omitted)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.commit, args.output), indent=2))


if __name__ == "__main__":
    main()
