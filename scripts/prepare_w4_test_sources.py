"""Restore only missing original Test bytes; no model import, labels/splits unchanged."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.download_subset import safe_image_path, inspect_image
from src.evaluation.w4_test import digest


def restore_one(row):
    import requests
    images = ROOT / "data/images/swg_pilot_v2"
    path = safe_image_path(images, row)
    expected = row["quality"]
    # Compare lexically: resolving a missing leaf while parallel workers create
    # parents can produce inconsistent transient normalization on Windows.
    if path != ROOT / expected["local_path"]:
        raise ValueError("Frozen image path mismatch")
    if path.exists():
        if digest(path) != expected["sha256"]:
            raise ValueError("Existing source differs; preserve it and stop")
        return {"image_id": row["image_id"], "status": "verified_existing", "sha256": expected["sha256"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for _ in range(2):
        part = None
        try:
            with tempfile.NamedTemporaryFile(prefix=".tv2-w4-", suffix=".part", dir=path.parent, delete=False) as handle:
                part = Path(handle.name)
                size = 0
                with requests.get(row["url"], stream=True, timeout=(15, 60), allow_redirects=False,
                                  headers={"Accept-Encoding": "identity"}) as response:
                    if response.status_code != 200:
                        raise ValueError(f"Unexpected HTTP {response.status_code}")
                    for chunk in response.iter_content(256 * 1024):
                        size += len(chunk)
                        if size > expected["bytes"]:
                            raise ValueError("Download exceeds frozen byte size")
                        handle.write(chunk)
            if part.stat().st_size != expected["bytes"] or digest(part) != expected["sha256"]:
                raise ValueError("Original source checksum/size mismatch; no replacement permitted")
            # Only after exact byte match, verify raster shape and pixel hash from the frozen quality record.
            quality = inspect_image(part, row)
            pixels = quality["pixel_sha256"]
            if pixels != expected["pixel_sha256"]:
                raise ValueError("Frozen RGB checksum mismatch")
            if path.exists():
                raise ValueError("Destination appeared concurrently; preserve both and stop")
            # Windows rename refuses to overwrite an existing destination.
            part.rename(path)
            return {"image_id": row["image_id"], "status": "restored_verified", "sha256": expected["sha256"],
                    "bytes": expected["bytes"], "pixel_sha256": pixels}
        except Exception as exc:
            last_error = repr(exc)
        finally:
            if part is not None and part.is_file():
                part.unlink()  # only this call's disposable partial file
    return {"image_id": row["image_id"], "status": "FAILED", "error": last_error}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restore-missing", action="store_true", help="Download missing original files after checksum binding")
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=6)
    args = parser.parse_args()
    comp = ROOT / "data/processed/comparison_v1"
    if digest(comp / "provenance.json") != "d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f":
        raise ValueError("Unapproved data provenance")
    provenance = json.loads((comp / "provenance.json").read_text(encoding="utf-8"))
    if digest(comp / "test.jsonl") != provenance["files_sha256"]["test.jsonl"]:
        raise ValueError("Frozen Test manifest changed")
    rows = [json.loads(line) for line in (comp / "test.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    output = ROOT / "outputs/tv2_w4/source_restore"
    output.mkdir(parents=True, exist_ok=True)
    if not args.restore_missing:
        print(json.dumps({"source_images": len(rows), "missing": sum(not (ROOT / r["quality"]["local_path"]).is_file() for r in rows),
                          "model_inference_performed": False}))
        return 0
    # Independent receipts allow retrying missing downloads without changing a frozen manifest.
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(restore_one, row): row for row in rows}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
            except Exception as exc:
                result = {"image_id": futures[future]["image_id"], "status": "FAILED", "error": repr(exc)}
            results.append(result)
            (output / (result["image_id"] + ".json")).write_text(json.dumps(result) + "\n", encoding="utf-8")
            if i % 50 == 0:
                print(f"Source restoration {i}/{len(rows)}; failures={sum(r['status'] == 'FAILED' for r in results)}", flush=True)
    report = {"source_images": len(rows), "verified": sum(r["status"] != "FAILED" for r in results),
              "restored": sum(r["status"] == "restored_verified" for r in results),
              "failures": [r for r in results if r["status"] == "FAILED"], "model_inference_performed": False,
              "frozen_manifest_sha256": digest(comp / "test.jsonl"), "labels_or_splits_changed": False}
    (ROOT / "reports/tv2/w4_evidence/test_source_restoration.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "failures"}))
    return 0 if not report["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
