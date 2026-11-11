"""Package only retained additional train images plus the frozen W6 manifests.

The existing 4,000-image pilot is a separate prerequisite. No model weights,
quarantined image or holdout image is included. ZIP and receipt remain in outputs/.
"""
import hashlib
from pathlib import Path
import zipfile

import prepare_tv1_w6 as w
from download_subset import atomic_json, load_json, read_rows, sha256, utc_now
from task_lock import state_lock


def package():
    config, binding = w.fingerprint(w.CONFIG)
    validation = w.verify_release(config, binding)
    release = w.repo_path(config['output_dir'])
    out = w.ROOT / 'outputs/tv1_w6'
    destination = out / 'swg_train_expansion_w6_v1_additional.zip'
    receipt_path = out / 'image_package.json'
    with state_lock(w.ROOT / 'data/interim/package_train_expansion_w6_v1'):
        sources = {p.relative_to(w.ROOT).as_posix(): p for p in release.rglob('*') if p.is_file()}
        rows = read_rows(release / 'additional_train.jsonl')
        expected_hashes = {name: sha256(p) for name, p in sources.items()}
        for row in rows:
            name = row['quality']['local_path']
            sources[name] = w.repo_path(name)
            expected_hashes[name] = row['quality']['sha256']
        if receipt_path.exists():
            receipt = load_json(receipt_path)
            w.require(receipt['provenance_sha256'] == validation['provenance_sha256'], 'Archive belongs to a different release')
            w.require(destination.exists() and sha256(destination) == receipt['sha256'], 'Existing archive changed or missing; preserve receipt and inspect')
            print('Verified existing image package:', destination)
            return receipt
        if not destination.exists():
            partial = destination.with_suffix('.zip.part')
            if partial.exists():
                # Preserve interrupted output instead of silently deleting it.
                backup = partial.with_name(partial.name + '.interrupted-' + str(partial.stat().st_mtime_ns))
                partial.rename(backup)
            with zipfile.ZipFile(partial, 'w', compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
                for index, (name, p) in enumerate(sorted(sources.items()), 1):
                    w.require(p.is_file() and sha256(p) == expected_hashes[name], 'Package input changed: ' + name)
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_STORED
                    with p.open('rb') as src, archive.open(info, 'w', force_zip64=True) as dst:
                        for block in iter(lambda: src.read(1024 * 1024), b''):
                            dst.write(block)
                    if index % 250 == 0 or index == len(sources):
                        print(f'Package {index}/{len(sources)}', flush=True)
            partial.replace(destination)
        with zipfile.ZipFile(destination) as archive:
            w.require(len(archive.namelist()) == len(sources) and set(archive.namelist()) == set(sources), 'Archive membership mismatch')
            for name, expected in expected_hashes.items():
                digest = hashlib.sha256()
                with archive.open(name) as entry:
                    for block in iter(lambda: entry.read(1024 * 1024), b''):
                        digest.update(block)
                w.require(digest.hexdigest() == expected, 'Archive bytes differ: ' + name)
        receipt = {'created_utc': utc_now(), 'path': destination.relative_to(w.ROOT).as_posix(),
                   'bytes': destination.stat().st_size, 'sha256': sha256(destination),
                   'provenance_sha256': validation['provenance_sha256'],
                   'additional_train_images': len(rows), 'archive_entries': len(sources),
                   'contents': 'retained additional images + release manifests; requires original swg_pilot_v2 separately',
                   'holdout_images_included': False, 'quarantined_images_included': False,
                   'entry_sha256_verified': True, 'script_sha256': sha256(Path(__file__))}
        atomic_json(receipt_path, receipt)
        print(destination)
        return receipt


if __name__ == '__main__':
    package()
