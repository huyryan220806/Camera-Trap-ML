"""Run the pinned, unmodified TV2 artifact auditor without merging branches.

Requires the TV2 commit to exist locally (git fetch origin). This script does
not train, download weights, approve a protocol, or perform model inference.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TV2_COMMIT = '3f76643d1bc395098d90105e67a9cf29c8fe3256'
B2_PREDICTIONS = 'reports/tv2/w5_evidence/attempt_01/validation_02/b2_predictions.jsonl'
FILES = ['scripts/evaluate_w5_validation.py', 'src/evaluation/w5_validation.py',
         'contracts/w5_crop_prediction.schema.json', 'contracts/w5_image_prediction.schema.json',
         'configs/tv2_w5_protocol.draft.json', B2_PREDICTIONS] + [
             'data/processed/comparison_v1/' + name for name in
             ('provenance.json', 'class_map.json', 'train.jsonl', 'val.jsonl', 'b2/train.jsonl', 'b2/val.jsonl')]


def prepare_reference(destination, source_repo=ROOT):
    destination = Path(destination)
    hashes = {}
    for name in FILES:
        blob = subprocess.check_output(['git', '-C', str(source_repo), 'show', TV2_COMMIT + ':' + name])
        path = destination / name
        if path.exists():
            if path.read_bytes() != blob:
                raise ValueError('TV2 snapshot modified: ' + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as f:
                f.write(blob)
        hashes[name] = hashlib.sha256(blob).hexdigest()
    receipt = {'source_commit': TV2_COMMIT, 'files_sha256': hashes,
               'scope': 'Unmodified TV2 audit code, frozen train/val metadata and published B2 predictions. No model inference.'}
    (destination / 'snapshot.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return destination


def audit_command(snapshot, run, protocol, output):
    return [sys.executable, '-X', 'utf8', str(snapshot / 'scripts/evaluate_w5_validation.py'),
            '--protocol', str(Path(protocol).resolve()), '--handoff', str(run / 'handoff.json'),
            '--checkpoint', str(run / 'best_model.pt'), '--crop-predictions', str(run / 'val_crops.jsonl'),
            '--b2-predictions', str(snapshot / B2_PREDICTIONS), '--output', str(output)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--run', type=Path)
    parser.add_argument('--protocol', type=Path)
    parser.add_argument('--attempt', default='attempt_01', help='New audit directory name; never overwrite')
    args = parser.parse_args()
    snapshot = ROOT / 'outputs/tv3_w5/tv2_reference' / TV2_COMMIT
    snapshot = prepare_reference(snapshot)
    if args.prepare_only:
        print(snapshot)
        return
    if args.run is None or args.protocol is None:
        parser.error('--run and --protocol are required unless --prepare-only')
    if not args.attempt or args.attempt in ('.', '..') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in args.attempt):
        parser.error('--attempt must be a simple new directory name')
    out = snapshot / 'outputs' / args.attempt
    if out.exists():
        parser.error('Attempt already exists; select a new name')
    command = audit_command(snapshot, args.run.resolve(), args.protocol, out)
    completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    # Keep failed attempts too, without claiming an audit or a real inference PASS.
    out.mkdir(parents=True, exist_ok=True)
    (out / 'auditor.log').write_text(completed.stdout + completed.stderr, encoding='utf-8')
    (out / 'invocation.json').write_text(json.dumps(dict(command=command, returncode=completed.returncode,
                                                      source_commit=TV2_COMMIT), indent=2) + '\n', encoding='utf-8')
    print(f'TV2 artifact audit exit={completed.returncode}; evidence: {out}')
    raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
