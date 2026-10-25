"""Resumable train-only MD+B2 timing; GT overlap checks are not Test metrics."""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from task_lock import state_lock
from src.demo.classifier import ClassifierCache
from src.demo.detector import MegaDetectorAdapter, digest
from src.demo.inference import analyze_classified
from src.demo.review import runtime_info, utc_now


def unmatched_gt(gt_boxes, detections, threshold=.5):
    pairs = []
    for i, (a, b, c, d) in enumerate(gt_boxes):
        for j, det in enumerate(detections):
            x, y, w, h = det['bbox_xywh']
            intersection = max(0, min(c, x + w) - max(a, x)) * max(0, min(d, y + h) - max(b, y))
            union = (c - a) * (d - b) + w * h - intersection
            iou = intersection / union if union else 0
            if iou >= threshold:
                pairs.append((iou, i, j))
    matched_gt, matched_det = set(), set()
    for _, i, j in sorted(pairs, reverse=True):
        if i not in matched_gt and j not in matched_det:
            matched_gt.add(i)
            matched_det.add(j)
    return [i for i in range(len(gt_boxes)) if i not in matched_gt]


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def run(output, repeats=2, resume=False):
    import torch
    torch.set_num_threads(4)
    comp = ROOT / 'data/processed/comparison_v1'
    if digest(comp / 'provenance.json') != 'd9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f':
        raise ValueError('Frozen provenance mismatch')
    provenance = json.loads((comp / 'provenance.json').read_text(encoding='utf-8'))
    for name in ('train.jsonl', 'b2/train.jsonl'):
        if digest(comp / name) != provenance['files_sha256'][name]:
            raise ValueError('Frozen train manifest changed')
    source = read_rows(comp / 'train.jsonl')
    selected = [min((r for r in source if r['class_id'] == c), key=lambda r: r['image_id']) for c in range(8)]
    crops = read_rows(comp / 'b2/train.jsonl')
    by_id = {r['image_id']: r for r in source}
    ordered_crops = sorted(crops, key=lambda c: (
        (c['bbox_xyxy'][2] - c['bbox_xyxy'][0]) * (c['bbox_xyxy'][3] - c['bbox_xyxy'][1])
        / (by_id[c['image_id']]['width'] * by_id[c['image_id']]['height']), c['crop_id']))
    stress = []
    seen = {r['image_id'] for r in selected}
    for crop in ordered_crops:
        if crop['image_id'] not in seen:
            stress.append(by_id[crop['image_id']])
            seen.add(crop['image_id'])
        if len(stress) == 4:
            break
    if any(r['split'] != 'train' for r in selected + crops):
        raise ValueError('Benchmark only accepts train')
    fingerprint = {'runtime': runtime_info(), 'repeats': repeats, 'classifier': 'B2',
                   'detector_threshold': .2, 'review_threshold': .7, 'gt_matching_iou': .5,
                   'selection': 'lowest image_id per class in frozen train; not selected by predictions',
                   'image_ids': [r['image_id'] for r in selected], 'provenance_sha256': digest(comp / 'provenance.json'),
                   'stress_selection': 'Four extra train parents with smallest normalized GT box area; excluded from primary timing summary',
                   'stress_image_ids': [r['image_id'] for r in stress],
                   'code_sha256': {p: digest(ROOT / p) for p in ('scripts/benchmark_tv4_w4.py',
                        'src/demo/inference.py', 'src/demo/classifier.py', 'src/demo/detector.py',
                        'src/demo/review.py', 'configs/demo_classifiers.json')},
                   'limitations': ['Train-only convenience sample, not independent detector evaluation; MD trained on SWG.',
                                   'GT unmatched at IoU 0.5 is a missed/localization candidate, not adjudicated wildlife ground truth.',
                                   'Timing excludes file read, GT matching, journaling, upload/preview/browser and human review.']}
    output = Path(output)
    if output.exists():
        if not resume or json.loads((output / 'config.json').read_text(encoding='utf-8')) != fingerprint:
            raise ValueError('Existing output needs --resume with identical configuration and code')
    else:
        output.mkdir(parents=True)
        with (output / 'config.json').open('x', encoding='utf-8') as handle:
            json.dump(fingerprint, handle, indent=2, ensure_ascii=False)
    # Reuse the repository's OS-released lock and stopped-process recovery.
    with state_lock(output):
        journal = output / 'inference.jsonl'
        records = read_rows(journal) if journal.exists() else []
        done = {r['job_id'] for r in records}
        if len(done) != len(records):
            raise ValueError('Duplicate benchmark job in journal')
        adapter, cache = MegaDetectorAdapter(), ClassifierCache()
        jobs = [('cold', selected[0])] + [(f'warm-{repeat}-{i}', row) for repeat in range(repeats) for i, row in enumerate(selected)]
        jobs += [(f'small-box-{i}', row) for i, row in enumerate(stress)]
        if not done.issubset({job for job, _ in jobs}):
            raise ValueError('Unexpected benchmark job in journal')
        for job, row in jobs:
            if job in done:
                continue
            path = (ROOT / row['quality']['local_path']).resolve()
            if not path.is_relative_to(ROOT / 'data/images') or digest(path) != row['quality']['sha256']:
                raise ValueError('Source path/SHA mismatch')
            data = path.read_bytes()
            detector_cold = adapter.model is None
            start = time.perf_counter()
            envelope = analyze_classified(data, path.name, classifier='B2', cache=cache, adapter=adapter,
                                          mode='megadetector', threshold=.2, review_threshold=.7)
            wall_ms = (time.perf_counter() - start) * 1000
            result = envelope['result']
            classifier = envelope['provenance']['classifier']
            phase = 'cold' if detector_cold else 'classifier_cold' if classifier and not classifier['cache_hit'] else 'warm'
            gt = [c['bbox_xyxy'] for c in crops if c['image_id'] == row['image_id']]
            missed = None if result['status'] == 'error' else unmatched_gt(gt, result['detections'])
            record = {'job_id': job, 'created_utc': utc_now(), 'phase': phase, 'image_id': row['image_id'],
                      'source_sha256': row['quality']['sha256'], 'split': 'train', 'wall_ms': wall_ms,
                      'gt_boxes_xyxy': gt, 'gt_unmatched_indices_iou_0_5': missed,
                      'zero_detections_with_gt': result['status'] == 'no_detection' and bool(gt),
                      'status': result['status'], 'envelope': envelope}
            count = len(result['detections']) if classifier else 0
            record['classifier_actual_crop_batches'] = [min(8, count - offset) for offset in range(0, count, 8)]
            if result.get('error') and result['error']['stage'] == 'classify':
                record['classifier_actual_crop_batches'] = None
            with journal.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
                handle.flush()
                os.fsync(handle.fileno())
            records.append(record)
            print(json.dumps({k: record[k] for k in ('job_id', 'phase', 'wall_ms', 'status', 'gt_unmatched_indices_iou_0_5')}), flush=True)
        warm = [r['wall_ms'] for r in records if r['phase'] == 'warm' and r['status'] != 'error' and r['job_id'].startswith('warm-')]
        summary = {'status': 'COMPLETE', 'config': fingerprint, 'requests': len(records),
                   'statuses': dict(Counter(r['status'] for r in records)), 'warm_success_requests': len(warm),
                   'warm_mean_ms': statistics.mean(warm) if warm else None,
                   'warm_p50_ms': statistics.median(warm) if warm else None,
                   'warm_p95_nearest_rank_ms': sorted(warm)[math.ceil(.95 * len(warm)) - 1] if warm else None,
                   'warm_images_per_second': len(warm) * 1000 / sum(warm) if warm else None,
                   'cold_ms': [r['wall_ms'] for r in records if r['phase'] != 'warm'],
                   'miss_candidate_image_ids': sorted({r['image_id'] for r in records if r['gt_unmatched_indices_iou_0_5']}),
                   'zero_detection_image_ids': sorted({r['image_id'] for r in records if r['zero_detections_with_gt']}),
                   'official_test_inference': False}
        temp = output / 'summary.tmp'
        temp.write_text(json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
        temp.replace(output / 'summary.json')
        return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=2)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.repeats <= 20:
        parser.error('repeats must be in 1..20')
    print(json.dumps(run(args.output, args.repeats, args.resume), indent=2, ensure_ascii=False))
