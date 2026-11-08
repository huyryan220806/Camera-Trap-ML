"""Verify supplied W6 ZIPs against pinned producer receipts; no training/Test."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PINS = {
 'R1': ('998901556b51789a52fc7a650eac504a4f6e23a1118af00450c7a18aeb9bb2fe', '86b1c7460b300f27b2f8d5efe426def51750478e2bf195ffa61df1213f646f79'),
 'R2': ('30f380cab3aa89f5b63c54507f7b7b63d2479e73f52710283e4f557e27fda223', '022786bda189478b9098a32299e9a290f9c37f01681ac3784b1782ce24b6b8bc'),
 'R3': ('a6f4d51c0f84f959c0ecf44c62eee819fc82844d38e63bbff50abe573920df4a', '2494551fa40e9d663ecb368d7c92d007c7404e92207503b432573ae55c7c4a6f'),
 'R4': ('cbe27ed2cd243e9783743eb8028b8d6b1f600fb28299735276d6d13b31114c0b', '7eaa034773ebed9f513493eca6dda3c9e8f0bcc6d2c814ad357026e6a9656ce8')}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desktop', type=Path, required=True)
    parser.add_argument('--downloads', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/tv4/w6/intake')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {}
    for run, (zip_sha, checkpoint_sha) in PINS.items():
        archive_path = (args.downloads if run == 'R3' else args.desktop) / f'{run}_attempt01.zip'
        receipt = json.loads((args.downloads / f'{run}_attempt01.sha256.json').read_text(encoding='utf-8-sig'))
        assert receipt['zip_sha256'] == zip_sha == sha(archive_path)
        assert receipt['checkpoint_sha256'] == checkpoint_sha
        assert archive_path.stat().st_size == receipt['bytes']
        with zipfile.ZipFile(archive_path) as archive:
            seen = set()
            for entry in archive.infolist():
                name = entry.filename
                assert not ('\\' in name or ':' in name or name.startswith('/') or '..' in Path(name).parts)
                assert (entry.external_attr >> 16) & 0o170000 != 0o120000
                assert not entry.flag_bits & 1
                assert name.casefold() not in seen
                seen.add(name.casefold())
                assert (args.output / name).resolve().is_relative_to(args.output.resolve())
            assert archive.testzip() is None
            archive.extractall(args.output)
        folder = args.output / f'{run}_attempt01'
        for name, spec in receipt['files'].items():
            path = (folder / name).resolve()
            assert path.is_relative_to(folder.resolve())
            assert path.stat().st_size == spec['bytes'] and sha(path) == spec['sha256'], name
        h = json.loads((folder / 'handoff.json').read_text())
        report[run] = {'status': 'PASS', 'zip_sha256': zip_sha, 'zip_bytes': receipt['bytes'],
            'payload_files': len(receipt['files']), 'checkpoint_sha256': checkpoint_sha,
            'checkpoint_bytes': (folder / 'best_model.pt').stat().st_size,
            'config_sha256': h['config_sha256'], 'source_sha': h['source_sha'],
            'feature_dim': h['feature_dim'], 'pooling': h['pooling'],
            'source_index_sha256': sha(folder / 'source_index.json'),
            'handoff_sha256': sha(folder / 'handoff.json'), 'config_raw_sha256': sha(folder / 'config.json'),
            'preprocessing_sha256': sha(folder / 'preprocessing.json'), 'class_map_sha256': sha(folder / 'class_map.json')}
        print(run, 'payload verification PASS', flush=True)
    (args.output / 'intake.json').write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
