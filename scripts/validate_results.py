"""Validate per-image outputs using JSON Schema plus class-map and geometry checks."""
import argparse
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    def reject_constant(value):
        raise ValueError(f'Non-JSON numeric constant: {value}')
    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject_constant,
                      object_pairs_hook=reject_duplicate_keys)


def validate_result(result):
    schema = load_json(ROOT / 'contracts/inference_result.schema.json')
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = [f'{".".join(map(str, e.absolute_path)) or "root"}: {e.message}'
              for e in validator.iter_errors(result)]
    if errors:
        return errors

    def check_finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            errors.append('Numeric values must be finite')
        elif isinstance(value, dict):
            for v in value.values(): check_finite(v)
        elif isinstance(value, list):
            for v in value: check_finite(v)
    check_finite(result)
    classes = load_json(ROOT / 'data/processed/v1/class_map.json')
    width, height = result['image']['width'], result['image']['height']
    if (width is None) != (height is None):
        errors.append('Image dimensions must both be known or both null')
    if result['status'] == 'error':
        error = result['error']
        allowed = {'read': {'FILE_NOT_FOUND', 'IMAGE_DECODE_ERROR', 'UNSUPPORTED_FORMAT'},
                   'detect': {'DETECTOR_FAILED'}, 'classify': {'CLASSIFIER_FAILED'}}
        if error['code'] not in allowed[error['stage']]:
            errors.append('Error code does not match its stage')
        if error['stage'] == 'read' and (width is not None or height is not None):
            errors.append('Read errors must use null image dimensions')
        if error['stage'] != 'read' and (width is None or height is None):
            errors.append('Model errors require the decoded image dimensions')
        return errors

    ids = set()
    has_low_score = False
    for detection in result['detections']:
        if detection['detection_id'] in ids:
            errors.append('Duplicate detection_id within image')
        ids.add(detection['detection_id'])
        x, y, w, h = detection['bbox_xywh']
        if x + w > width or y + h > height:
            errors.append('Bounding box extends outside the original image')
        if detection['detector_score'] < result['pipeline']['detector_threshold']:
            errors.append('Detection is below the configured detector threshold')
        top = detection['top_k']
        if len({p['class_id'] for p in top}) != len(top):
            errors.append('Repeated class in top_k')
        if any(classes.get(str(p['class_id'])) != p['label'] for p in top):
            errors.append('Prediction class_id/label does not match class_map v1')
        if any(a['score'] < b['score'] for a, b in zip(top, top[1:])):
            errors.append('top_k must be ordered by descending score')
        has_low_score |= top[0]['score'] < result['pipeline']['review_threshold']
    if result['detections']:
        expected = 'needs_review' if has_low_score else 'ok'
        if result['status'] != expected:
            errors.append(f'Status must be {expected} for these scores and thresholds')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*', help='JSON files; defaults to all tracked examples')
    args = parser.parse_args()
    paths = [Path(p) for p in args.paths] if args.paths else sorted((ROOT / 'examples/results').glob('*.json'))
    if not paths:
        parser.error('No result files found')
    failed = False
    for path in paths:
        try:
            errors = validate_result(load_json(path))
        except (ValueError, OSError) as exc:
            errors = [str(exc)]
        print(f'{"FAIL" if errors else "OK"}: {path.name}')
        for error in errors:
            print(f'  {error}')
        failed |= bool(errors)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
