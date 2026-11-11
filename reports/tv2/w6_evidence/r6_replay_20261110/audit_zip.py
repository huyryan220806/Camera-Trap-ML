import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
ZIP = ROOT / 'reports/tv3/w6/w6_2/R6_attempt01.zip'
OUT = Path(__file__).resolve().parent
DEST = OUT / 'received'
EXPECTED = 'fcb6118cd89c1a825d02e6d1c0a7bd19b983bac7bebaf863b959c0dd8854144e'

def sha_stream(stream):
    h = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        h.update(block)
        size += len(block)
    return h.hexdigest(), size

with ZIP.open('rb') as stream:
    zip_sha, zip_bytes = sha_stream(stream)
assert zip_sha == EXPECTED, 'ZIP SHA mismatch'
with zipfile.ZipFile(ZIP) as archive:
    infos = archive.infolist()
    names = [i.filename for i in infos]
    assert len(names) == len(set(names)) and len(names) <= 100, 'duplicate or excessive entries'
    assert sum(i.file_size for i in infos) <= 350_000_000, 'excessive uncompressed size'
    for info in infos:
        p = PurePosixPath(info.filename)
        assert p.parts and p.parts[0] == 'R6_attempt01', 'wrong root'
        assert not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename and ':' not in info.filename, 'unsafe path'
        assert not info.is_dir() and not info.flag_bits & 1, 'directory/encrypted entry'
        mode = info.external_attr >> 16
        assert not stat.S_ISLNK(mode), 'symlink entry'
        assert info.file_size <= 210_000_000, 'oversized entry'
    assert archive.testzip() is None, 'CRC failure'
    index = json.loads(archive.read('R6_attempt01/package_index.json'))
    listed = index
    actual = {n.removeprefix('R6_attempt01/') for n in names}
    assert set(listed) == actual - {'package_index.json', 'registry.delivery.json'}, sorted(actual - set(listed))
    checks = {}
    for info in infos:
        rel = info.filename.removeprefix('R6_attempt01/')
        with archive.open(info) as stream:
            digest, size = sha_stream(stream)
        checks[rel] = {'sha256': digest, 'bytes': size}
        if rel in listed:
            assert checks[rel] == listed[rel], f'index mismatch: {rel}'
        target = DEST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(info) as source, target.open('wb') as sink:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                sink.write(block)
    assert checks['best_model.pt']['sha256'] == '24e3f51418dd7492a7537dff629794547c4540e8929bfe3e566105a6486581ef'
report = {'zip_sha256': zip_sha, 'zip_bytes': zip_bytes, 'safe_paths': True, 'crc': 'PASS', 'indexed_files': len(listed), 'entries': len(infos), 'checks': checks}
(OUT / 'artifact_audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({k: report[k] for k in ('zip_sha256','zip_bytes','safe_paths','crc','indexed_files','entries')}, indent=2))
