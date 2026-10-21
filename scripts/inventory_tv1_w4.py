"""Read-only test data inventory after B2 lock; no model inference or relabeling."""
import argparse
from collections import Counter, defaultdict
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from download_subset import atomic_json, inspect_image, load_json, read_rows, sha256, utc_now
from task_lock import state_lock
from validate_comparison import validate


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_image(root, local_path):
    path = (root / local_path).resolve()
    require(path.is_relative_to((root / 'data/images').resolve()), 'Image path outside data/images')
    return path


def distribution(rows, crops, labels):
    require(len({r['image_id'] for r in rows}) == len(rows), 'Duplicate image IDs')
    parents = {r['image_id']: r for r in rows}
    require(set(parents) == {c['image_id'] for c in crops}, 'B1/B2 parent mismatch')
    for crop in crops:
        parent = parents[crop['image_id']]
        require(all(crop[k] == parent[k] for k in ('label', 'class_id', 'split', 'sequence_id', 'location')),
                'Crop/parent metadata mismatch')
    def count(group, selected_crops):
        return {'images': len(group), 'sequences': len({r['sequence_id'] for r in group}),
                'locations': len({r['location'] for r in group}), 'crops': len(selected_crops),
                'unique_rgb': len({r['quality']['pixel_sha256'] for r in group})}
    result = {'total': count(rows, crops), 'per_class': {}}
    for label in labels:
        group = [r for r in rows if r['label'] == label]
        result['per_class'][label] = count(group, [c for c in crops if c['label'] == label])
    require(sum(v['images'] for v in result['per_class'].values()) == len(rows), 'Unknown class')
    return result


def select_examples(rows, crops):
    """Fixed metadata rules, independent of predictions, with deterministic IDs."""
    groups, flags, by_id = defaultdict(list), defaultdict(set), {r['image_id']: r for r in rows}
    for row in rows:
        groups[row['quality']['pixel_sha256']].append(row['image_id'])
    duplicates = sorted(sorted(ids) for ids in groups.values() if len(ids) > 1)
    for group in duplicates:
        for image_id in group:
            flags[image_id].add('confirmed_exact_rgb_duplicate')
    counts = Counter(c['image_id'] for c in crops)
    small, border = set(), set()
    for crop in crops:
        x1, y1, x2, y2 = crop['bbox_xyxy']
        require(0 <= x1 < x2 <= crop['width'] and 0 <= y1 < y2 <= crop['height'], 'Invalid crop geometry')
        if (x2 - x1) * (y2 - y1) / (crop['width'] * crop['height']) < 0.01:
            small.add(crop['image_id'])
        if x1 <= 1 or y1 <= 1 or x2 >= crop['width'] - 1 or y2 >= crop['height'] - 1:
            border.add(crop['image_id'])
    multi = {i for i, n in counts.items() if n > 1}
    # At most four examples per candidate condition; duplicate witnesses always retained.
    for name, ids in (('candidate_small_box_under_1pct', small),
                      ('candidate_box_touches_border', border), ('multiple_boxes_not_an_error', multi)):
        for image_id in sorted(ids)[:4]:
            flags[image_id].add(name)
    examples = []
    for image_id in sorted(flags):
        row = by_id[image_id]
        examples.append({'image_id': image_id, 'label': row['label'], 'split': 'test',
                         'sequence_id': row['sequence_id'], 'location': row['location'],
                         'local_path': row['quality']['local_path'], 'url': row['url'],
                         'sha256': row['quality']['sha256'], 'pixel_sha256': row['quality']['pixel_sha256'],
                         'width': row['width'], 'height': row['height'],
                         'bbox_xyxy': sorted(c['bbox_xyxy'] for c in crops if c['image_id'] == image_id),
                         'flags': sorted(flags[image_id]), 'action': 'retain_unchanged',
                         'label_error_confirmed': False, 'model_prediction_used': False})
    return {'rules_version': 'metadata-rules-v1', 'duplicate_groups': duplicates,
            'counts': {'small_box_images': len(small), 'border_box_images': len(border),
                       'multiple_box_images': len(multi), 'duplicate_images': sum(map(len, duplicates))},
            'examples': examples}


def verify_lock(lock_path):
    lock = load_json(lock_path)
    require(lock.get('data_inventory_allowed') is True, 'Data inventory not authorized')
    proof_path = (ROOT / lock['validation_report']).resolve()
    require(proof_path.is_relative_to(ROOT), 'Validation proof outside repository')
    require(sha256(proof_path) == lock['validation_report_sha256'], 'Changed validation proof')
    proof = load_json(proof_path)
    require(proof['status'] == 'PASS' and not proof['test_opened'], 'Invalid pre-test validation proof')
    for key in ('checkpoint_sha256', 'checkpoint_bytes', 'provenance_sha256', 'best_epoch'):
        require(proof[key] == lock[key], 'Lock/proof mismatch: ' + key)
    return lock


def inventory(data_root, output, lock_path):
    data_root, output, lock_path = Path(data_root).resolve(), Path(output).resolve(), Path(lock_path).resolve()
    comp = ROOT / 'data/processed/comparison_v1'
    require(output.is_relative_to(ROOT / 'outputs') or output.is_relative_to(data_root / 'outputs'),
            'Outputs must stay in outputs/, not source data')
    lock = verify_lock(lock_path)
    require(sha256(comp / 'provenance.json') == lock['provenance_sha256'], 'Changed frozen data')
    with state_lock(output / 'state'):
        audit = validate(comp, check_images=False)
        rows, crops = read_rows(comp / 'test.jsonl'), read_rows(comp / 'b2/test.jsonl')
        cmap = load_json(comp / 'class_map.json')
        labels = [v for k, v in sorted(cmap.items(), key=lambda pair: int(pair[0]))]
        summary = distribution(rows, crops, labels)
        frozen = load_json(comp / 'summary.json')
        for item in frozen['by_class_split']:
            if item['split'] == 'test':
                measured = summary['per_class'][item['label']]
                require(all(measured[a] == item[b] for a, b in
                            (('images', 'retained'), ('sequences', 'sequences'), ('locations', 'locations'), ('crops', 'b2_crops'))),
                        'Counts disagree with frozen summary')
        checks, reused = [], 0
        for index, row in enumerate(rows, 1):
            path = safe_image(data_root, row['quality']['local_path'])
            cached = output / 'state' / (row['image_id'] + '.json')
            result = None
            if path.is_file() and cached.exists():
                prior = load_json(cached)
                # Rehash bytes on resume; only skip expensive decode of exactly verified content.
                if (prior.get('valid') is True and prior.get('image_id') == row['image_id']
                        and prior.get('sha256') == sha256(path) == row['quality']['sha256']
                        and all(prior.get(k) == row['quality'][k] for k in ('pixel_sha256', 'bytes', 'image_format', 'image_mode'))
                        and (prior.get('width'), prior.get('height')) == (row['width'], row['height'])):
                    result = prior
                    reused += 1
            if result is None:
                try:
                    actual = inspect_image(path, row)
                    require(all(actual[k] == row['quality'][k] for k in
                                ('sha256', 'pixel_sha256', 'bytes', 'image_format', 'image_mode')), 'Image differs from frozen quality')
                    result = {'image_id': row['image_id'], 'valid': True, **actual}
                except Exception as exc:
                    result = {'image_id': row['image_id'], 'valid': False, 'error': str(exc), 'checked_utc': utc_now()}
                atomic_json(cached, result)
            checks.append(result)
            if index % 100 == 0:
                atomic_json(output / 'progress.json', {'phase': 'image_checks', 'done': index,
                            'total': len(rows), 'reused_decodes': reused, 'updated_utc': utc_now()})
                print(f'Test data checks {index}/{len(rows)}; no inference', flush=True)
        examples = select_examples(rows, crops)
        summary.update(schema_version='1.0', checked_utc=utc_now(), lock_id=lock['lock_id'],
                       model_lock_sha256=sha256(lock_path), provenance_sha256=lock['provenance_sha256'],
                       test_model_inference_performed=False, label_changes=0, split_changes=0, exclusions=0,
                       valid_images=sum(c['valid'] for c in checks), invalid_images=sum(not c['valid'] for c in checks),
                       reused_decodes=reused, metadata_audit=audit, example_counts=examples['counts'])
        # Check the frozen bundle again after I/O; never silently publish stale counts.
        validate(comp, check_images=False)
        atomic_json(output / 'inventory.json', summary)
        atomic_json(output / 'quality_checks.json', checks)
        atomic_json(output / 'examples.json', examples)
        lines = ['# TV1 W4 - Test Data Quality Examples', '',
                 'No predictions were used. No labels/splits were changed. Keep all samples.',
                 'Only exact RGB duplicates are confirmed issues. Small/border boxes are review candidates, not label errors.',
                 'Do not use these test examples to tune B3. Multiple boxes alone are not an error.', '']
        cards = []
        for item in examples['examples']:
            lines.extend([f"## {item['image_id']}", f"- Class: `{item['label']}`",
                          '- Flags: ' + ', '.join(item['flags']),
                          f"- Image: `{item['local_path']}`",
                          f"- Boxes (xyxy): `{item['bbox_xyxy']}`", '- Action: retain unchanged.', ''])
            path = safe_image(data_root, item['local_path'])
            overlays = []
            for x1, y1, x2, y2 in item['bbox_xyxy']:
                overlays.append(f'<div class="bbox" style="left:{100*x1/item["width"]:.5f}%;'
                                f'top:{100*y1/item["height"]:.5f}%;width:{100*(x2-x1)/item["width"]:.5f}%;'
                                f'height:{100*(y2-y1)/item["height"]:.5f}%"></div>')
            cards.append('<section><h2>' + html.escape(item['image_id']) + '</h2><p>' +
                         html.escape(item['label'] + ': ' + ', '.join(item['flags'])) +
                         '</p><figure><img loading="lazy" src="' + html.escape(path.as_uri(), quote=True) +
                         '" alt="Test data quality example">' + ''.join(overlays) + '</figure><pre>' +
                         html.escape(str(item['bbox_xyxy'])) + '</pre></section>')
        (output / 'examples.md').write_text('\n'.join(lines), encoding='utf-8')
        (output / 'examples.local.html').write_text(
            '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>TV1 W4 quality review</title><style>body{font:16px system-ui;max-width:960px;margin:24px auto;padding:16px}'
            'img{display:block;width:100%;height:auto}figure{position:relative;margin:0}.bbox{position:absolute;border:2px solid #e03131;box-sizing:border-box}'
            'h2,pre,p{overflow-wrap:anywhere;white-space:pre-wrap}section{border-top:1px solid #aaa;margin-top:24px}</style>'
            '<h1>Test data quality examples</h1><p>No model predictions. Retain all labels and splits. Do not tune B3 with these examples.</p>' +
            ''.join(cards) + '</html>', encoding='utf-8')
        atomic_json(output / 'progress.json', {'phase': 'failed' if summary['invalid_images'] else 'complete', 'total': len(rows),
                    'valid': summary['valid_images'], 'invalid': summary['invalid_images'], 'updated_utc': utc_now()})
        print(json.dumps(summary, indent=2))
        require(not summary['invalid_images'], 'Missing/changed/corrupt images recorded; restore original bytes and rerun')
        return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/tv1/w4')
    parser.add_argument('--lock', type=Path, default=ROOT / 'configs/model_locks/b2_w3.json')
    args = parser.parse_args()
    inventory(args.data_root, args.output, args.lock)
