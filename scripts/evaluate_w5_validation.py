"""Audit a registered TV3 W5 crop-prediction handoff on frozen Validation only.

No inference/training is performed. This verifies submitted artifacts, not their
scientific provenance or reviewer approval. See reports/tv2/W5_PROTOCOL.md.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation.w5_validation import (B2_SHA256, aggregate, audit_predictions, compare_predictions,
    load_frozen_validation, read_json, read_jsonl, require, sha256, verify_handoff)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True, help='Externally approved registration receipt')
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--crop-predictions', type=Path, required=True, help='JSONL; schema in contracts/w5_*')
    parser.add_argument('--b2-predictions', type=Path, help='Audited W5 image-prediction JSONL')
    parser.add_argument('--output', type=Path, required=True, help='A new directory under outputs/')
    args = parser.parse_args()
    out = args.output.resolve()
    require(out.is_relative_to(ROOT / 'outputs') and not out.exists(), 'Use a new outputs attempt; never overwrite')
    parents, crops, hashes = load_frozen_validation(ROOT)
    handoff, protocol = read_json(args.handoff), read_json(args.protocol)
    verify_handoff(handoff, args.checkpoint, hashes, protocol, args.handoff.resolve().parent)
    checkpoint_hash = handoff['checkpoint_sha256']
    predictions = aggregate(read_jsonl(args.crop_predictions), parents, crops, handoff['experiment_id'], checkpoint_hash)
    result = audit_predictions(predictions, parents, crops, handoff['experiment_id'], checkpoint_hash)
    require(sha256(args.checkpoint) == checkpoint_hash, 'Checkpoint changed during audit')
    published = handoff.get('validation_metrics', {})
    require(set(published) == set(result['metrics']), 'Need all four published image metrics')
    import math
    require(all(type(published[k]) in (int, float) and math.isfinite(published[k]) and
                math.isclose(published[k], v, rel_tol=0, abs_tol=1e-10) for k, v in result['metrics'].items()),
            'Published vs independently recomputed metrics differ')
    result.update(status='ARTIFACT_VERIFIED', experiment_id=handoff['experiment_id'],
                  checkpoint_sha256=checkpoint_hash, dataset_version='comparison_v1',
                  test_inference_performed=False, training_performed=False, model_loaded=False,
                  approval_authorship_verified_by_code=False,
                  input_sha256={k: sha256(getattr(args, k)) for k in ('handoff','protocol','crop_predictions')})
    if args.b2_predictions:
        reference = read_jsonl(args.b2_predictions)
        require(reference and reference[0]['checkpoint_sha256'] == B2_SHA256, 'Comparison requires pinned B2 checkpoint')
        ref = audit_predictions(reference, parents, crops, reference[0]['experiment_id'], reference[0]['checkpoint_sha256'])
        result['paired_outcomes'] = compare_predictions(reference, predictions)
        result['metric_delta_candidate_minus_b2'] = {k: v - ref['metrics'][k] for k,v in result['metrics'].items()}
        result['input_sha256']['b2_predictions'] = sha256(args.b2_predictions)
    out.mkdir(parents=True, exist_ok=False)
    with (out / 'predictions.jsonl').open('x',encoding='utf-8') as f:
        for row in predictions:
            f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    with (out / 'audit.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,allow_nan=False,indent=2)
        f.write('\n')
    print(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2))


if __name__ == '__main__':
    main()
