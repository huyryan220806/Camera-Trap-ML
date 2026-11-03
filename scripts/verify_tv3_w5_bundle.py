"""Reproduce B1/B3 evidence without model inference, training or Test access.

With --local-assets, additionally rehash the downloaded weights, verify the
vendor checkout, and rehash the 32 train crops' source images. This is a
current verification, not a replay of the historical GPU smoke.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CONFIG = 'configs/dinov3_lp_w5.local.json'
SMOKE = 'reports/tv3/pretrained_2026-10-29/backbone_smoke_2026-10-29.json'
PREFLIGHT = 'reports/tv3/w5_evidence/preflight.json'
SOURCE = 'src/training/dino_probe.py'


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def canonical(c):
    # EXACT dino_probe.digest recipe: default separators (', ', ': '), no LF.
    return json.dumps(c, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(local_assets=False):
    c, smoke, preflight = read(CONFIG), read(SMOKE), read(PREFLIGHT)
    raw_sha, canonical_sha = sha(ROOT / CONFIG), sha_bytes(canonical(c))
    require(raw_sha == 'e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce', 'Canonical file bytes changed')
    require(c == smoke['config'] and canonical_sha == smoke['config_sha256'], 'Smoke config mismatch')
    require(sha(ROOT / SOURCE) == smoke['source_code_sha256'], 'Smoke source mismatch')
    source = (ROOT / SOURCE).read_text(encoding='utf-8')
    require('model.load_state_dict(state_dict, strict=True)' in source, 'Strict-load call missing')
    old = read('configs/dinov3_lp_w5.json')
    require(sha_bytes(canonical(old)) == preflight['config_sha256'], 'Preflight template changed')
    differences = {key: {'preflight': old['model'][key], 'pinned': c['model'][key]}
                   for key in old['model'] if old['model'][key] != c['model'][key]}
    require(set(differences) == {'repo_commit', 'weights_sha256', 'weights_source'}, 'Unexpected preflight config change')
    unpinned = json.loads(json.dumps(c))
    unpinned['model'] = old['model']
    require(unpinned == old, 'Non-model parameters changed since preflight')
    folder = ROOT / c['data']['directory']
    require(sha(folder / 'provenance.json') == c['data']['provenance_sha256'] == smoke['data']['provenance_sha256'] == preflight['data']['provenance_sha256'], 'Data provenance mismatch')
    for name, expected in smoke['data']['files'].items():
        require(sha(folder / name) == expected, 'Manifest mismatch: ' + name)
    for name, expected in preflight['data']['files'].items():
        require(smoke['data']['files'][name] == expected, 'Historical data mismatch: ' + name)
    rows = [json.loads(line) for line in (folder / 'b2/train.jsonl').read_text(encoding='utf-8').splitlines()]
    samples = []
    for index, row in enumerate(rows[:32]):
        q = row['quality']
        sample = dict(index=index, crop_id=row['crop_id'], image_id=row['image_id'], split=row['split'],
                      bbox_xyxy=row['bbox_xyxy'], class_id=row['class_id'], source_path=q['local_path'],
                      expected_source_sha256=q['sha256'], expected_rgb_sha256=q['pixel_sha256'])
        require(row['split'] == 'train', 'Smoke samples must be train only')
        if local_assets:
            path = (ROOT / q['local_path']).resolve()
            require(path.is_relative_to((ROOT / 'data/images').resolve()), 'Source path outside data/images')
            sample['observed_source_sha256'] = sha(path)
            require(sample['observed_source_sha256'] == q['sha256'], 'Sample byte mismatch')
        samples.append(sample)
    report = dict(status='PASS', config_path=CONFIG, config_file_sha256=raw_sha,
                  config_canonical_sha256=canonical_sha,
                  serialization="json.dumps(config, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8'); default separators ', ' and ': '; no trailing newline",
                  smoke_path=SMOKE, smoke_file_sha256=sha(ROOT / SMOKE), embedded_config_equal=True,
                  source_path=SOURCE, source_sha256=sha(ROOT / SOURCE),
                  strict_load_evidence={'kind': 'historical smoke PASS linked to exact source containing strict=True; no new load',
                                        'historical_missing_unexpected_keys_log': 'not separately captured'},
                  preflight_path=PREFLIGHT, preflight_sha256=sha(ROOT / PREFLIGHT),
                  preflight_config_differences=differences, manifest_sha256=smoke['data']['files'],
                  data_scope='Historical 28/10 full 3400-image decode/byte/RGB check; current metadata hashes; optional current sample byte checks. No full pixel recheck today.',
                  smoke_sample_scope='Reconstructed from the executed smoke recipe rows[train][:32], not a contemporaneous sample receipt; no smoke rerun.',
                  sample_unique_images=len({s['image_id'] for s in samples}), samples=samples,
                  model_inference_performed=False, training_performed=False, test_accessed=False,
                  local_assets_verified=local_assets)
    if local_assets:
        weights = ROOT / c['model']['weights_path']
        require(sha(weights) == c['model']['weights_sha256'], 'Pretrained SHA mismatch')
        repo = ROOT / c['model']['repo_dir']
        commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        status = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=normal'], text=True)
        require(commit == c['model']['repo_commit'] and not status.strip(), 'Vendor commit/cleanliness mismatch')
        report['pretrained_verification'] = dict(path=c['model']['weights_path'], sha256=sha(weights), bytes=weights.stat().st_size,
                                                architecture_commit=commit, checkout_clean=True,
                                                upstream_factory_sha256=sha(repo / 'dinov3/hub/backbones.py'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-assets', action='store_true')
    parser.add_argument('--output', type=Path, help='New JSON report path; never overwrites evidence')
    args = parser.parse_args()
    if args.output:
        require(not args.output.exists(), 'Output already exists')
    report = verify(args.local_assets)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write('\n')
    print(json.dumps({key: report[key] for key in ('status', 'config_file_sha256', 'config_canonical_sha256', 'local_assets_verified', 'model_inference_performed')}, indent=2))


if __name__ == '__main__':
    main()
