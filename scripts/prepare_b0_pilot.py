"""Select and download a fixed train/validation subset of TV1's pilot manifest.

No test row is selected, downloaded or written to experiment manifests.
"""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlparse
from urllib.request import urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.b0_dataset import image_path, inspect_images  # noqa: E402
from src.evaluation.metrics import load_class_map  # noqa: E402


def select_rows(manifest: Path, class_names: list[str], seed: int, per_class: dict[str, int]) -> dict[str, list[dict]]:
    groups = defaultdict(list)
    with manifest.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            split = row.get("split")
            if split in ("train", "val"):
                class_id = row.get("class_id")
                if type(class_id) is not int or not 0 <= class_id < len(class_names) or row.get("label") != class_names[class_id]:
                    raise ValueError(f"Invalid label in pilot: {row.get('image_id')}")
                groups[(split, class_id)].append(row)
    selected = {}
    for split, limit in per_class.items():
        items = []
        for class_id in range(len(class_names)):
            candidates = groups[(split, class_id)]
            if len(candidates) < limit:
                raise ValueError(f"Too few pilot {split} images for class {class_id}: {len(candidates)}")
            candidates.sort(key=lambda row: hashlib.sha256(f"{seed}:{row['image_id']}".encode()).digest())
            items.extend(candidates[:limit])
        selected[split] = sorted(items, key=lambda row: row["image_id"])
    if {r["image_id"] for r in selected["train"]} & {r["image_id"] for r in selected["val"]}:
        raise ValueError("Train/validation image IDs overlap")
    return selected


def download_one(row: dict, image_root: Path) -> dict:
    path = image_path(image_root, row)
    url = row["url"]
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "storage.googleapis.com" or not parsed.path.startswith("/public-datasets-lila/swg-camera-traps/"):
        raise ValueError(f"Unexpected source URL for {row['image_id']}")
    if path.exists():
        good, errors = inspect_images([row], image_root)
        if good:
            return {"image_id": row["image_id"], "split": row["split"], "status": "existing", "bytes": path.stat().st_size}
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".download")
    try:
        with urlopen(url, timeout=40) as response, temp_path.open("wb") as destination:
            while chunk := response.read(1024 * 1024):
                destination.write(chunk)
        with Image.open(temp_path) as image:
            image.verify()
        with Image.open(temp_path) as image:
            image.convert("RGB").load()
        temp_path.replace(path)
        return {"image_id": row["image_id"], "split": row["split"], "status": "downloaded", "bytes": path.stat().st_size}
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        return {"image_id": row["image_id"], "split": row["split"], "status": "failed", "error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/b0.yaml")
    parser.add_argument("--select-only", action="store_true")
    args = parser.parse_args()
    config = json.loads((ROOT / args.config).read_text(encoding="utf-8"))
    labels, class_names = load_class_map(ROOT / config["data"]["class_map"])
    if labels != list(range(len(labels))):
        raise ValueError("Class IDs must be contiguous from zero")
    selected = select_rows(ROOT / config["data"]["source_manifest"], class_names, config["experiment"]["seed"], {"train": config["data"]["train_per_class"], "val": config["data"]["val_per_class"]})
    run_dir = ROOT / "experiments" / config["experiment"]["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in selected.items():
        (run_dir / f"selected_{split}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(f"Selected {len(selected['train'])} train, {len(selected['val'])} validation images from TV1 pilot; no test images")
    if args.select_only:
        return
    image_root = ROOT / config["data"]["image_root"]
    outcomes = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(download_one, row, image_root) for rows in selected.values() for row in rows]
        for future in as_completed(futures):
            outcomes.append(future.result())
            if len(outcomes) % 25 == 0:
                print(f"Checked {len(outcomes)}/{len(futures)} images", flush=True)
    outcomes.sort(key=lambda item: item["image_id"])
    status = dict(Counter(item["status"] for item in outcomes))
    report = {"source_manifest": config["data"]["source_manifest"], "seed": config["experiment"]["seed"], "selected_counts": {key: len(rows) for key, rows in selected.items()}, "status_counts": status, "images": outcomes}
    (run_dir / "download_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Download status: {status}")
    if status.get("failed", 0):
        raise SystemExit(f"{status['failed']} selected images failed; see download_report.json")


if __name__ == "__main__":
    main()
