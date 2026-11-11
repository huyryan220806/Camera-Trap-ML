"""Validate W6 registry or audit a completed W6 package (Validation only).

Does not run models or grant approval. Output must be a new outputs/ attempt.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation import w5_validation as w5
from src.evaluation import w6_validation as w6


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=ROOT/'experiments/w6/registry.json')
    parser.add_argument('--handoff', type=Path)
    parser.add_argument('--run-id', choices=['R%d' % i for i in range(1,7)])
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    registry = w5.read_json(args.registry)
    result = w6.validate_registry(registry)
    if args.handoff is None:
        w5.require(not any((args.run_id,args.checkpoint,args.output)), 'Package arguments require --handoff')
        print(json.dumps(result, indent=2, allow_nan=False))
        return
    w5.require(all((args.run_id,args.checkpoint,args.output)), 'Need run ID, checkpoint and output')
    out = args.output.resolve()
    w5.require(out.is_relative_to((ROOT/'outputs').resolve()) and not out.exists(), 'Use new outputs attempt')
    handoff = w5.read_json(args.handoff)
    package = args.handoff.resolve().parent
    run, parents, crops = w6.verify_submission(registry,args.run_id,handoff,package,args.checkpoint)
    artifacts = handoff['artifacts']
    crop_path = w6.confined(package,artifacts['crop_predictions']['path'])
    image_path = w6.confined(package,artifacts['image_predictions']['path'])
    predictions = w5.read_jsonl(image_path)
    result = w6.evaluate(w5.read_jsonl(crop_path),predictions,parents,crops,args.run_id,run['checkpoint_sha256'])
    for key,value in result['metrics'].items():
        w5.require(w6.finite(handoff.get('validation_metrics',{}).get(key)) and
                   abs(handoff['validation_metrics'][key]-value) <= 1e-10, 'Published metric mismatch: '+key)
    for key in ('accuracy','macro_f1'):
        w5.require(abs(run['metrics'][key]-result['metrics'][key]) <= 1e-10, 'Registry metric mismatch')
    reference_path = ROOT/'reports/tv2/w5_acceptance/2026-11-02/attempt_01/tv2_predictions.jsonl'
    # Pin reference bytes to the immutable integrated W5 Git blob, not a claimed checkpoint field.
    import subprocess
    expected = subprocess.check_output(['git','show','cfcf00615847d52fba73ee3e44fe0e6076bb840c:'+reference_path.relative_to(ROOT).as_posix()],cwd=ROOT)
    import hashlib
    w5.require(w5.sha256(reference_path) == hashlib.sha256(expected).hexdigest(), 'R0 reference predictions changed')
    result['r0_comparison'] = w6.paired_report(w5.read_jsonl(reference_path),predictions,parents,crops,args.run_id,run['checkpoint_sha256'])
    # Recheck package bytes after reading, before publishing the new audit.
    for entry in artifacts.values():
        w5.require(w5.sha256(w6.confined(package,entry['path'])) == entry['sha256'], 'Artifact changed during audit')
    w5.require(w5.sha256(args.checkpoint) == run['checkpoint_sha256'], 'Checkpoint changed during audit')
    result.update(status='ARTIFACT_VERIFIED',run_id=args.run_id,model_replay='NOT RUN',
                  model_loaded=False,training_performed=False,test_inference_performed=False,
                  approval_authorship_verified=False,
                  inputs_sha256={'registry':w5.sha256(args.registry),'handoff':w5.sha256(args.handoff),
                                 'r0_predictions':w5.sha256(reference_path)})
    out.mkdir(parents=True,exist_ok=False)
    with (out/'audit.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__ == '__main__':
    main()
