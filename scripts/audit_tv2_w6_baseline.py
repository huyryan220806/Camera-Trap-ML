"""Read-only W6 D1 audit of frozen W5 bytes and saved Validation predictions.

No model is loaded or replayed; this does not verify all source image bytes.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation import w5_validation as w5
from src.evaluation import w6_validation as w6


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True)
    args=parser.parse_args()
    parents,crops,hashes=w6.load_validation()
    w5.require(w5.sha256(args.checkpoint) == w6.R0_SHA and args.checkpoint.stat().st_size == 86851958,
               'R0 checkpoint bytes mismatch')
    config=ROOT/'configs/dinov3_lp_w5.local.json'
    w5.require(w5.sha256(config) == w6.R0_CONFIG_RAW_SHA, 'W5 config changed')
    protocol=ROOT/'configs/dinov3_lp_w5.local.protocol.json'
    w5.require(w5.sha256(protocol) == 'e47b96f5e576c234e2e48143c7c008df79ca62156cebf6b2bf65c0119a6f133a',
               'W5 protocol changed')
    path=ROOT/'reports/tv2/w5_acceptance/2026-11-02/attempt_01/tv2_predictions.jsonl'
    predictions=w5.read_jsonl(path)
    result=w5.audit_predictions(predictions,parents,crops,'DINOv3_LP_run01',w6.R0_SHA)
    w5.require(result['metrics']['accuracy'] == .845 and result['metrics']['macro_f1'] == .8444008279545706,
               'R0 saved metrics changed')
    result.update(status='PASS',checkpoint_sha256=w6.R0_SHA,checkpoint_bytes=86851958,
                  manifest_sha256=hashes,config_raw_sha256=w5.sha256(config),protocol_raw_sha256=w5.sha256(protocol),
                  predictions_sha256=w5.sha256(path),source_training_commit=w6.R0_SOURCE,
                  scope='local checkpoint bytes and saved Validation artifacts; no fresh model replay',
                  model_loaded=False,official_training_performed=False,test_opened=False,
                  all_old_image_pixels_verified=False)
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
