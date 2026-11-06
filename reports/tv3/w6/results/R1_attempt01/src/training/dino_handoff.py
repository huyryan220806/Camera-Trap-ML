"""TV3 exports compatible with TV2 W5 at 3f76643; never grants approval."""
from pathlib import Path
import json
import os

from src.training import dino_probe as d

MANIFEST_NAMES = ('class_map.json', 'train.jsonl', 'val.jsonl', 'b2/train.jsonl', 'b2/val.jsonl')
METRICS = ('accuracy', 'macro_f1', 'macro_precision', 'macro_recall')


def manifest_hashes(gate):
    return {name: gate['files'][name] for name in MANIFEST_NAMES}


def protocol_draft(c):
    return dict(status='DRAFT', dataset_version='comparison_v1', evaluation_split='val',
                selection_metric='image_macro_f1', prediction_tie_rule='lowest_class_id',
                checkpoint_tie_rule='earliest_epoch', proposed_seeds=[c['training']['seed']],
                seeds=[], max_candidate_runs=None, experiments=[],
                reviewers={'TV2': None, 'TV3': None, 'TV1': None}, approval_evidence=None,
                config_sha256=d.digest(c), budget_reference=None,
                proposal={'experiment_id': c['experiment_id'], 'max_candidate_runs': 1,
                          'training': c['training'], 'runtime': c['runtime']},
                note='Proposal only. Record real TV2/TV3 agreement before APPROVED; TV1 review remains separate.')


def validate_protocol(c, receipt):
    d.require(receipt.get('status') == 'APPROVED' and
              all(receipt.get('reviewers', {}).get(who) for who in ('TV2', 'TV3')),
              'W5 protocol needs actual TV2/TV3 agreement (APPROVED receipt)')
    d.require(receipt.get('config_sha256') == d.digest(c), 'Agreement does not bind this configuration')
    d.require(receipt.get('approval_evidence') and receipt.get('budget_reference'), 'Missing agreement evidence/budget')
    for key, value in dict(dataset_version='comparison_v1', evaluation_split='val',
                           selection_metric='image_macro_f1', prediction_tie_rule='lowest_class_id',
                           checkpoint_tie_rule='earliest_epoch').items():
        d.require(receipt.get(key) == value, 'Unregistered policy: ' + key)
    seeds, experiments, budget = (receipt.get(k) for k in ('seeds', 'experiments', 'max_candidate_runs'))
    d.require(isinstance(seeds, list) and all(type(s) is int for s in seeds) and
              c['training']['seed'] in seeds, 'Unregistered seed')
    d.require(type(budget) is int and budget > 0 and isinstance(experiments, list) and
              all(isinstance(e, str) for e in experiments) and
              len(experiments) == len(set(experiments)) <= budget and c['experiment_id'] in experiments,
              'Missing/invalid experiment registration or budget')


def preprocessing(c):
    v3 = c['model']['name'] == 'dinov3_vits16'
    return dict(id=c['preprocessing'], color='RGB', exif_transpose=False, padding=0,
                bbox='frozen integer bbox_xyxy; right/bottom exclusive',
                steps=(['ToImage uint8', 'Resize square 256x256 bilinear antialias',
                        'ToDtype float32 scale=True', 'Normalize'] if v3 else
                       ['PIL Resize short edge 256 bicubic antialias', 'CenterCrop 224x224',
                        'ToTensor float32 /255', 'Normalize']),
                mean=d.MEAN, std=d.STD, random_augmentation=False)


def write_jsonl(path, rows):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
    os.replace(tmp, path)


def export_predictions(run, result, experiment_id, checkpoint_sha):
    # Export the actual softmax vectors: recomputing FP32 logits with Python's
    # FP64 exp in the receiving evaluator can change near-tied predictions.
    crops = [dict(crop_id=p['crop_id'], image_id=p['image_id'], ground_truth=p['y_true'],
                  class_scores=p['probabilities']) for p in result['crop_predictions']]
    images = [dict(image_id=p['image_id'], ground_truth=p['y_true'], predicted_class=p['y_pred'],
                   class_scores=p['probabilities'], crop_count=p['crop_count'],
                   experiment_id=experiment_id, checkpoint_sha256=checkpoint_sha)
              for p in result['image_predictions']]
    write_jsonl(run / 'val_crops.jsonl', crops)
    write_jsonl(run / 'val_images.jsonl', images)


def artifact(run, path):
    path = Path(path).resolve()
    return {'path': path.relative_to(run.resolve()).as_posix(), 'sha256': d.sha(path)}


def build_handoff(run, checkpoint, c, binding, result):
    sha = d.sha(checkpoint)
    export_predictions(run, result, c['experiment_id'], sha)
    d.atomic_json(run / 'class_map.json', binding['class_map'])
    d.atomic_json(run / 'preprocessing.json', preprocessing(c))
    return dict(experiment_id=c['experiment_id'], model_name=c['model']['name'],
                architecture=c['model']['name'] + ' frozen CLS384 + Linear(384,8,bias=True)',
                model_version=c['model']['repo_commit'],
                pretrained_source=c['model']['weights_source'] + '; sha256=' + str(c['model']['weights_sha256']),
                checkpoint_sha256=sha, checkpoint_bytes=checkpoint.stat().st_size,
                checkpoint_path=checkpoint.name, seed=c['training']['seed'],
                dataset_version='comparison_v1', train_dataset_version='comparison_v1',
                val_dataset_version='comparison_v1', evaluation_split='val', provenance_sha256=d.PROVENANCE,
                manifest_sha256=manifest_hashes(binding['data']),
                class_order=[binding['class_map'][str(i)] for i in range(8)],
                aggregation='mean_crop_softmax_then_argmax', preprocessing=preprocessing(c),
                training_status='complete', training_commit=binding['code_commit'],
                training_log='train_log.json', device=c['runtime']['device'], runtime=binding['runtime'],
                training_budget=c['training'], cache=c['cache'],
                architecture_repo=c['model']['repo_dir'], architecture_commit=c['model']['repo_commit'],
                download_url=None, adapter='src.training.dino_probe.load_package / predict_crops',
                fresh_process_reload={'status': 'PENDING', 'evidence': None},
                validation_metrics={key: result['metrics'][key] for key in METRICS},
                artifacts={key: artifact(run, run / name) for key, name in
                           [('training_config', 'config.json'), ('training_log', 'train_log.json'),
                            ('crop_predictions', 'val_crops.jsonl'), ('image_predictions', 'val_images.jsonl'),
                            ('class_mapping', 'class_map.json'), ('preprocessing', 'preprocessing.json'),
                            ('binding', 'binding.json')]})


def finish_handoff(run, report_path, process_ok):
    handoff = d.read_json(run / 'handoff.json')
    report = d.read_json(report_path) if report_path.is_file() else {}
    passed = bool(process_ok and report.get('passed') is True and report.get('status') == 'PASS' and
                  report.get('fresh_process') is True and report.get('evaluation_split') == 'val' and
                  report.get('test_inference_performed') is False and
                  report.get('checkpoint_sha256') == handoff['checkpoint_sha256'] and
                  report.get('manifest_sha256') == handoff['manifest_sha256'])
    evidence = report_path.relative_to(run).as_posix()
    handoff['fresh_process_reload'] = dict(status='PASS' if passed else 'FAIL', evidence=evidence)
    if report_path.is_file():
        handoff['artifacts']['reload_report'] = artifact(run, report_path)
    d.atomic_json(run / 'handoff.json', handoff)
    return passed
