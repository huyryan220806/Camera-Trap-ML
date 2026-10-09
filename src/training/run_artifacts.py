"""Reserve new runs and publish complete artifact files without overwriting history."""

import hashlib
import os
from pathlib import Path
import tempfile


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def protect_run_directory(run_dir: Path, *, preparing: bool = False) -> None:
    # Only downloaded/selected inputs may exist before the first training call.
    allowed = set() if preparing else {"selected_train.jsonl", "selected_val.jsonl", "download_report.json"}
    if run_dir.exists() and (not run_dir.is_dir() or any(p.name not in allowed for p in run_dir.iterdir())):
        raise FileExistsError(f"Run ID already exists: {run_dir.name}. Use a new run ID. Resume is not supported.")


def reserve_run(run_dir: Path) -> None:
    protect_run_directory(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also rejects concurrent writers. Keep the marker after
    # success/failure: a partially attempted run must never be restarted in place.
    try:
        with (run_dir / ".training_started").open("x", encoding="utf-8") as marker:
            marker.write("Resume is not supported. Use a new run ID.\n")
            marker.flush()
            os.fsync(marker.fileno())
    except FileExistsError as exc:
        raise FileExistsError(f"Run ID already exists: {run_dir.name}. Use a new run ID.") from exc


def atomic_write_files(payloads: dict[Path, bytes]) -> None:
    """Stage/fsync every file before publication; roll back on a write exception.

    os.replace is atomic per file, not across the group. New runs stay reserved
    after interruption; no completed run is ever a legal write destination.
    """
    staged, previous, published = {}, {}, []
    try:
        for path, content in payloads.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            previous[path] = path.read_bytes() if path.exists() else None
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".b0-", delete=False) as target:
                staged[path] = Path(target.name)
                target.write(content)
                target.flush()
                os.fsync(target.fileno())
        for path, temporary in staged.items():
            os.replace(temporary, path)
            published.append(path)
    except BaseException:
        for path in reversed(published):
            old = previous[path]
            if old is None:
                path.unlink(missing_ok=True)
            else:
                with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".b0-rollback-", delete=False) as target:
                    backup = Path(target.name)
                    target.write(old)
                    target.flush()
                    os.fsync(target.fileno())
                try:
                    os.replace(backup, path)
                finally:
                    backup.unlink(missing_ok=True)
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_files({path: text.encode("utf-8")})
