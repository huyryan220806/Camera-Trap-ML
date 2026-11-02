"""Real CPU native/adapter equivalence on synthetic RGB/grayscale crops, never Test."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    import torch
    from PIL import Image
    from src.demo.classifier import ClassifierCache
    from src.demo.dino import DinoCache, CHECKPOINT_SHA
    from src.demo.review import runtime_info
    from src.training import dino_probe as native
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    cache = DinoCache(ClassifierCache(), args.package, args.repo)
    index = json.loads((args.package / 'artifact_index.json').read_text())
    for entry in index['files']:
        path = (args.package / entry['path']).resolve()
        assert path.is_relative_to(args.package.resolve())
        assert path.stat().st_size == entry['bytes']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
    crops = [Image.new('RGB', (193, 77), (25, 90, 46)), Image.new('L', (61, 205), 128),
             Image.new('RGB', (8, 8), (230, 110, 11))]
    started = time.perf_counter()
    actual, metadata = cache.logits(crops)
    cold = time.perf_counter() - started
    # Independent load from native interface, same crops/batch/device/runtime.
    backbone, head, transform, _ = native.load_package(args.package / 'best_model.pt', CHECKPOINT_SHA, 'cpu', args.repo)
    expected = native.predict_crops(backbone, head, transform, crops, 'cpu')
    delta = (actual - expected).abs().max().item()
    assert torch.equal(actual, expected), f'Native/adapter differ: {delta}; no tolerance relaxed'
    singles = []
    for crop in crops:
        one, _ = cache.logits([crop])
        reference = native.predict_crops(backbone, head, transform, [crop], 'cpu')
        assert torch.equal(one, reference)
        singles.append(one.tolist())
    nine = crops * 3
    bounded, _ = cache.logits(nine)
    bounded_native = torch.cat([native.predict_crops(backbone, head, transform, nine[i:i+8], 'cpu')
                                for i in range(0, len(nine), 8)])
    assert torch.equal(bounded, bounded_native)
    raster = Image.new('RGB', (100, 240), (40, 70, 100))
    detections = [{'detection_id': 'one', 'bbox_xywh': [1, 2, 30, 60]},
                  {'detection_id': 'two', 'bbox_xywh': [20, 90, 70, 130]}]
    predictions, _ = cache.predict(raster, detections, 'DINOv3_LP_run01')
    assert len(predictions) == 2 and all(len(top) == 3 for top in predictions)
    warm = []
    for _ in range(5):
        started = time.perf_counter(); cache.logits(crops); warm.append(time.perf_counter() - started)
    # Failure gates run after a warm load too.
    original_package, original_repo = cache.package, cache.repo
    cache.package = args.output / 'missing'
    try:
        cache.logits(crops)
        raise AssertionError('Missing package silently accepted')
    except FileNotFoundError:
        pass
    cache.package = original_package
    cache.package = args.output / 'invalid'
    cache.package.mkdir()
    (cache.package / 'best_model.pt').write_bytes(b'QA invalid checkpoint')
    try:
        cache.logits(crops)
        raise AssertionError('Bad checkpoint size silently accepted')
    except ValueError:
        pass
    cache.package = original_package
    cache.repo = ROOT
    try:
        cache.logits(crops)
        raise AssertionError('Wrong architecture silently accepted')
    except ValueError:
        pass
    cache.repo = original_repo
    report = {'status': 'PASS', 'scope': 'CPU synthetic-crop integration, not validation accuracy or GPU replay',
        'artifact_payload_files': len(index['files']), 'checkpoint_sha256': CHECKPOINT_SHA,
        'runtime': {**runtime_info(), 'classifier_image_size': 256},
        'process_memory_bytes': __import__('psutil').Process().memory_info()._asdict(),
        'device': 'cpu', 'precision': 'FP32', 'amp': False, 'tf32': False,
        'crops': [{'mode': im.mode, 'size': im.size} for im in crops], 'crop_batch': 3,
        'max_crop_batch': 8, 'bounded_batches_tested': [8, 1], 'portrait_per_box_top3': predictions,
        'max_abs_logit_delta': delta, 'predictions_changed': 0,
        'adapter_logits': actual.tolist(), 'native_logits': expected.tolist(), 'single_logits': singles,
        'metadata': metadata, 'cold_seconds': cold, 'warm_seconds': warm,
        'warm_mean_seconds': statistics.mean(warm), 'warm_p50_seconds': statistics.median(warm),
        'timing_scope': 'checksum + source/vendor gates + load when cold + crop transforms + forward; excludes HTTP/detector/UI',
        'limitations': ['CPU environment differs from TV2 GPU replay', 'Synthetic fixtures; no accuracy measurement',
                         '5 warm calls insufficient for robust p95 estimate']}
    (args.output / 'equivalence.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'max_abs_logit_delta', 'cold_seconds', 'warm_mean_seconds')}))


if __name__ == '__main__':
    main()
