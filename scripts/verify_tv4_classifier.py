"""Real detector/classifier integration smoke on train only, with cache reuse."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.demo.classifier import ClassifierCache
from src.demo.detector import MegaDetectorAdapter, digest
from src.demo.inference import analyze_classified, validate_envelope
from prepare_tv4_demo import sample_rows
from download_subset import atomic_json, utc_now
from task_lock import state_lock


def verify(output, model='B0'):
    rows = sample_rows()
    if not rows or rows[0]['split'] != 'train':
        raise ValueError('A locally downloaded train v2 sample is required; never substitute test')
    row = rows[0]
    path = ROOT / row['quality']['local_path']
    if digest(path) != row['quality']['sha256']:
        raise ValueError('Train sample checksum mismatch')
    cache, detector = ClassifierCache(), MegaDetectorAdapter()
    report = {'status': 'running', 'date': utc_now()[:10], 'checked_utc': utc_now(),
              'sample_id': row['image_id'], 'sample_split': 'train', 'image_sha256': digest(path),
              'retrained': False, 'test_inference_used': False, 'device': 'cpu', 'model': model}
    with state_lock(ROOT / 'outputs/tv4/w3/smoke_state' / model):
        atomic_json(output, report)
        try:
            cold = analyze_classified(path.read_bytes(), path.name, cache=cache, adapter=detector, classifier=model)
            validate_envelope(cold)
            if cold['result']['status'] not in ('ok', 'needs_review'):
                raise RuntimeError('Expected a classified animal in the chosen train smoke image')
            report['cold'] = cold
            atomic_json(output, report)
            warm = analyze_classified(path.read_bytes(), path.name, cache=cache, adapter=detector, classifier=model)
            validate_envelope(warm)
            if warm['result']['detections'] != cold['result']['detections']:
                raise RuntimeError('Warm cache changed predictions')
            if cold['provenance']['classifier']['cache_hit'] or not warm['provenance']['classifier']['cache_hit'] or cache.load_count != 1:
                raise RuntimeError('Model was not cached once')
            report.update(status='PASS', warm=warm, model_load_count=cache.load_count,
                          identical_predictions=True, checked_utc=utc_now())
            print(json.dumps({k: v for k, v in report.items() if k not in ('cold', 'warm')}, indent=2))
        except BaseException as exc:
            report.update(status='FAILED', error=str(exc))
            raise
        finally:
            atomic_json(output, report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--model', choices=('B0', 'B1', 'B2'), default='B0')
    args = parser.parse_args()
    output = args.output or ROOT / ('outputs/tv4/w3/smoke.json' if args.model == 'B0'
                                   else f'outputs/tv4/w3/{args.model.lower()}_smoke.json')
    verify(output, args.model)
