"""Per-box classification; v1 result remains unchanged inside a provenance envelope."""
import json
import logging
import math
import time

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from scripts.validate_results import validate_result
from .classifier import CLASS_MAP_PATH, MAX_BOXES
from .detector import ROOT, TRAINING_SOURCE, analyze, decode_image

SCORE_WARNING = 'Softmax class scores are not calibrated probabilities; review threshold is a demo setting.'
SWG_WARNING = 'MegaDetector MDv5a used SWG in training; SWG demo is not an independent end-to-end evaluation.'
CROP_WARNING = 'B0/B1 trained on full images; detector-crop input is a distribution shift, not a crop-model benchmark.'


def validate_envelope(envelope):
    schema = json.loads((ROOT / 'contracts/classifier_demo.schema.json').read_text(encoding='utf-8'))
    legacy = json.loads((ROOT / 'contracts/inference_result.schema.json').read_text(encoding='utf-8'))
    registry = Registry().with_resource('https://cameratrap.local/contracts/inference_result.schema.json',
                                        Resource.from_contents(legacy))
    Draft202012Validator(schema, registry=registry).validate(envelope)
    errors = validate_result(envelope['result'])
    if errors:
        raise ValueError('; '.join(errors))


def analyze_classified(data, file_name, *, classifier='B0', cache=None,
                       mode='megadetector', threshold=0.2, review_threshold=0.7,
                       scenario='animal', adapter=None):
    if classifier not in ('B0', 'B1', 'B2'):
        raise ValueError('Unknown classifier')
    if type(review_threshold) not in (int, float) or not math.isfinite(review_threshold) or not 0 <= review_threshold <= 1:
        raise ValueError('Review threshold must be finite in [0, 1]')
    start = time.perf_counter()
    detected = analyze(data, file_name, mode, threshold, scenario, adapter)
    result = {'schema_version': '1.0.0', 'request_id': detected['request_id'],
              'image': {'image_id': None, **detected['image']},
              'pipeline': {'mode': 'mock' if mode == 'mock' else 'inference',
                           'detector_id': detected['pipeline']['detector_id'],
                           'classifier_id': 'mock-scores-v1' if mode == 'mock' else classifier,
                           'class_map_version': 'swg-v1', 'detector_threshold': threshold,
                           'review_threshold': review_threshold},
              'status': detected['status'] if detected['status'] != 'detected' else 'needs_review',
              'needs_review': True, 'detections': [], 'error': detected['error'], 'elapsed_ms': 0}
    proof = {'requested_classifier': classifier, 'classifier': None,
             'detector': detected['pipeline'], 'ignored_non_animals': detected['ignored_non_animals'],
             'score_kind': 'softmax_class_score', 'scores_calibrated': False,
             'crop_policy': 'round_clip_min8_padding0', 'max_boxes': MAX_BOXES,
             'training_overlap_swg': True, 'training_source': TRAINING_SOURCE,
             'warnings': [SCORE_WARNING, SWG_WARNING]}
    if mode == 'mock':
        proof['warnings'].append('Both boxes and class scores are synthetic; no model inference was performed.')
    elif classifier in ('B0', 'B1'):
        proof['warnings'].append(CROP_WARNING)
    if detected['status'] == 'detected':
        try:
            if len(detected['detections']) > MAX_BOXES:
                raise ValueError('More than 64 animal boxes; no partial result returned')
            if mode == 'mock':
                names = json.loads((ROOT / CLASS_MAP_PATH).read_text(encoding='utf-8'))
                predictions = [[{'class_id': (j + n) % 8, 'label': names[str((j + n) % 8)], 'score': score}
                                for j, score in enumerate((0.58, 0.24, 0.08))]
                               for n in range(len(detected['detections']))]
            else:
                if cache is None:
                    raise RuntimeError('Classifier cache is not configured')
                predictions, proof['classifier'] = cache.predict(decode_image(data), detected['detections'], classifier)
            if len(predictions) != len(detected['detections']):
                raise ValueError('Missing classifier output for one or more boxes')
            result['detections'] = [
                {'detection_id': box['detection_id'], 'bbox_xywh': box['bbox_xywh'],
                 'detector_score': box['score'], 'top_k': top}
                for box, top in zip(detected['detections'], predictions)]
            result['needs_review'] = any(top[0]['score'] < review_threshold for top in predictions)
            result['status'] = 'needs_review' if result['needs_review'] else 'ok'
            errors = validate_result(result)
            if errors:
                raise ValueError('; '.join(errors))
        except Exception:
            logging.exception('Classifier failed (%s); no fallback or partial predictions', classifier)
            result.update(status='error', needs_review=True, detections=[], error={
                'stage': 'classify', 'code': 'CLASSIFIER_FAILED',
                'message': 'Khong phan loai duoc. Kiem tra checkpoint, SHA, class map va kich thuoc crop; khong tu doi model.'})
    result['elapsed_ms'] = round((time.perf_counter() - start) * 1000, 2)
    envelope = {'schema_version': 'classifier-demo-1.0', 'result': result, 'provenance': proof}
    validate_envelope(envelope)
    return envelope
