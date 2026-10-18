"""Shared, deterministic comparison-manifest rules; no sampling or split assignment."""
from collections import Counter, defaultdict
import math
from pathlib import Path

from download_subset import ROOT, SPLITS, inspect_image, load_json, read_rows, sha256
from split_swg import audit_records
from validate_manifest_v2 import validate as validate_v2

DEFAULT_CONFIG = ROOT / 'configs/comparison_v1.json'
DEFAULT_OUTPUT = ROOT / 'data/processed/comparison_v1'
DEFAULT_STATE = ROOT / 'data/interim/comparison_v1'
DEFAULT_REPORT = ROOT / 'reports/tv1_w3/verification.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def repo_path(value):
    path = (ROOT / value).resolve()
    require(path.is_relative_to(ROOT), 'Path must stay within repository')
    return path


def config_rules(config):
    require(config['dataset_version'] and isinstance(config['dataset_version'], str), 'Missing version')
    require(type(config['min_crop_side']) is int and config['min_crop_side'] >= 1, 'Invalid minimum side')
    # A changed geometry policy needs its own implementation and tests, not a silent flag.
    supported = {
        'padding_fraction': 0, 'rounding': 'python_round_half_even_then_clip',
        'bad_box_policy': 'exclude_entire_image_from_both_models',
        'multi_box_policy': 'all_boxes_same_species',
        'b2_train_weight': '1 / number_of_crops_in_parent_image',
        'evaluation_unit': 'image_id',
        'b2_evaluation_aggregation': 'mean_class_probabilities_over_all_parent_crops',
        'within_split_exact_duplicates': 'retain_and_report',
        'test_policy': 'integrity_checks_only_no_model_selection',
    }
    require(all(config.get(k) == v for k, v in supported.items()), 'Unsupported comparison policy')


def load_inputs(config_path):
    config = load_json(config_path)
    config_rules(config)
    source = repo_path(config['source_dir'])
    validate_v2(source, check_images=False)
    provenance = load_json(source / 'provenance.json')
    require(config['source_seed'] == provenance['source_seed'], 'Source seed changed')
    rows = read_rows(source / 'manifest_v2.jsonl')
    cmap = load_json(source / 'class_map.json')
    require(set(cmap) == {str(i) for i in range(len(cmap))}, 'Class IDs must be contiguous')
    require(len(set(cmap.values())) == len(cmap), 'Duplicate class names')
    return config, source, rows, cmap


def source_fingerprint(source):
    provenance = load_json(source / 'provenance.json')
    return {name: sha256(source / name) for name in sorted(set(provenance['files_sha256']) | {'provenance.json'})}


def geometry(box, width, height, minimum):
    coords = box.get('bbox_xywh')
    if not isinstance(coords, list) or len(coords) != 4:
        return None, 'missing_or_invalid_bbox'
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in coords):
        return None, 'nonfinite_or_nonnumeric_bbox'
    x, y, w, h = coords
    if not (w > 0 and h > 0 and 0 <= x < x + w <= width + 1e-6
            and 0 <= y < y + h <= height + 1e-6):
        return None, 'bbox_outside_image'
    xyxy = [max(0, round(x)), max(0, round(y)), min(width, round(x + w)), min(height, round(y + h))]
    if xyxy[2] - xyxy[0] < minimum or xyxy[3] - xyxy[1] < minimum:
        return None, 'crop_below_min_side'
    return xyxy, None


def eligible_crops(row, cmap, config):
    issues, crops = [], []
    label = row.get('label')
    if not isinstance(label, str) or label not in cmap.values():
        issues.append({'reason': 'unknown_or_ambiguous_image_label'})
    if type(row.get('class_id')) is not int or cmap.get(str(row.get('class_id'))) != label:
        issues.append({'reason': 'class_id_label_mismatch'})
    if any(type(row.get(k)) is not int or row[k] <= 0 for k in ('width', 'height')):
        return [], issues + [{'reason': 'invalid_image_dimensions'}]
    boxes = row.get('boxes')
    if not isinstance(boxes, list) or not boxes:
        return [], issues + [{'reason': 'no_boxes'}]
    seen = set()
    for box in boxes:
        if not isinstance(box, dict):
            issues.append({'reason': 'invalid_box_record'})
            continue
        annotation = box.get('annotation_id')
        context = {'annotation_id': annotation}
        if not isinstance(annotation, str) or not annotation:
            issues.append({**context, 'reason': 'missing_annotation_id'})
        elif annotation in seen:
            issues.append({**context, 'reason': 'duplicate_annotation_id'})
        else:
            seen.add(annotation)
        if box.get('label') != label:
            issues.append({**context, 'reason': 'box_label_disagrees_with_image'})
        xyxy, reason = geometry(box, row['width'], row['height'], config['min_crop_side'])
        if reason:
            issues.append({**context, 'reason': reason})
        else:
            crops.append({'annotation_id': annotation, 'bbox_xywh_original': box['bbox_xywh'],
                          'bbox_xyxy': xyxy, 'crop_w': xyxy[2] - xyxy[0], 'crop_h': xyxy[3] - xyxy[1]})
    return ([], issues) if issues else (crops, [])


def audit(rows):
    for row in rows:
        require(row.get('split') in SPLITS, 'Unknown split')
        for key in ('image_id', 'file_name', 'seq_id', 'sequence_id', 'location'):
            require(isinstance(row.get(key), str) and row[key].strip(), 'Missing identity: ' + key)
        require(row['seq_id'] == row['sequence_id'], 'Sequence aliases disagree')
    result = audit_records(rows)
    require(result['metadata_leakage_check_passed'], 'Image/path/sequence/location leakage detected')
    seq_locations = defaultdict(set)
    groups = defaultdict(list)
    for row in rows:
        seq_locations[row['seq_id']].add(row['location'])
        pixel = row.get('quality', {}).get('pixel_sha256')
        require(isinstance(pixel, str) and len(pixel) == 64, 'Missing pixel checksum')
        groups[pixel].append(row)
    require(all(len(v) == 1 for v in seq_locations.values()), 'Sequence spans locations')
    duplicates = []
    for pixel, group in groups.items():
        if len(group) < 2:
            continue
        require(len({r['split'] for r in group}) == 1, 'Exact pixel duplicate crosses splits')
        require(len({r['label'] for r in group}) == 1, 'Exact duplicate has conflicting labels')
        duplicates.append({'pixel_sha256': pixel, 'image_ids': [r['image_id'] for r in group],
                           'split': group[0]['split'], 'label': group[0]['label'], 'action': 'retain_and_report'})
    result.update(image_content_duplicates_checked=True,
                  image_content_note='Exact decoded RGB hashes only; near duplicates NOT checked.',
                  unique_sequences=len(seq_locations), unique_locations=len({r['location'] for r in rows}),
                  exact_duplicate_groups=len(duplicates), unique_pixel_contents=len(groups))
    return result, duplicates


def select(rows, cmap, config):
    audit(rows)  # Never hide source leakage by filtering away its witnesses.
    accepted, excluded, b1, b2 = [], [], [], []
    for row in rows:
        crops, issues = eligible_crops(row, cmap, config)
        if issues:
            excluded.append({**row, 'exclusion': {'reason': issues[0]['reason'], 'issues': issues}})
            continue
        accepted.append(row)
        common = {k: row[k] for k in ('image_id', 'split', 'label', 'class_id', 'seq_id', 'sequence_id',
                                      'location', 'file_name', 'url', 'width', 'height', 'quality')}
        b1.append({**common, 'sample_id': row['image_id'], 'input_type': 'full_image', 'sample_weight': 1.0})
        for crop in crops:
            b2.append({**common, **crop, 'crop_id': row['image_id'] + '_' + crop['annotation_id'],
                       'input_type': 'ground_truth_crop', 'parent_crop_count': len(crops),
                       'sample_weight': 1.0 / len(crops)})
    require(accepted, 'No eligible images; refusing to publish an empty dataset')
    require(len({r['crop_id'] for r in b2}) == len(b2), 'Duplicate crop identity')
    return accepted, excluded, b1, b2


def summarize(rows, accepted, excluded, b2, cmap):
    def measure(split, label=None):
        match = lambda r: r['split'] == split and (label is None or r['label'] == label)
        source, kept, dropped = ([r for r in group if match(r)] for group in (rows, accepted, excluded))
        return {'split': split, 'label': label, 'requested': len(source), 'retained': len(kept),
                'excluded': len(dropped), 'b1_samples': len(kept), 'b2_crops': sum(match(r) for r in b2),
                'source_boxes': sum(len(r['boxes']) for r in source),
                'excluded_boxes': sum(len(r['boxes']) for r in dropped),
                'sequences': len({r['seq_id'] for r in kept}), 'locations': len({r['location'] for r in kept}),
                'exclusion_reasons': dict(sorted(Counter(r['exclusion']['reason'] for r in dropped).items()))}
    return {'requested': len(rows), 'retained': len(accepted), 'excluded': len(excluded),
            'b1_samples': len(accepted), 'b2_crops': len(b2), 'split_changes': 0,
            'by_split': [measure(s) for s in SPLITS],
            'by_class_split': [measure(s, label) for label in cmap.values() for s in SPLITS],
            'exclusion_reasons': dict(sorted(Counter(r['exclusion']['reason'] for r in excluded).items()))}


def image_check(row):
    quality = row['quality']
    path = repo_path(quality['local_path'])
    require(path.is_relative_to(ROOT / 'data/images'), 'Image must be within data/images')
    actual = inspect_image(path, row)
    for key in ('sha256', 'pixel_sha256', 'bytes', 'image_format', 'image_mode'):
        require(actual[key] == quality[key], f'Image changed: {row["image_id"]}/{key}')
    return actual


def bundle_files(rows, cmap, config):
    accepted, excluded, b1, b2 = select(rows, cmap, config)
    accepted_audit, duplicates = audit(accepted)
    source_audit, _ = audit(rows)
    common_ids = {r['image_id'] for r in accepted}
    require(common_ids == {r['image_id'] for r in b1} == {r['image_id'] for r in b2}, 'B1/B2 IDs differ')
    accepted_audit.update(source_audit=source_audit, b1_b2_same_parent_ids=True,
                          b1_b2_same_labels_and_splits=True)
    files = {'manifest.jsonl': accepted, 'excluded.jsonl': excluded}
    for split in SPLITS:
        files[split + '.jsonl'] = [r for r in accepted if r['split'] == split]
        files[f'b1/{split}.jsonl'] = [r for r in b1 if r['split'] == split]
        files[f'b2/{split}.jsonl'] = [r for r in b2 if r['split'] == split]
    objects = {'class_map.json': cmap, 'policy.json': config, 'audit.json': accepted_audit,
               'duplicates.json': duplicates, 'summary.json': summarize(rows, accepted, excluded, b2, cmap)}
    return files, objects
