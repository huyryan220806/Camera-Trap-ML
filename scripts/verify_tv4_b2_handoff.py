"""Fresh-process B2 validation on frozen train/val sources; never open test."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.demo.classifier import ClassifierCache, checkpoint_model
from src.demo.detector import digest
from download_subset import atomic_json, utc_now
from task_lock import state_lock

TV3_COMMIT = '7cc87e86a8ad2cb7ca034c59a8e03b708050c3f1'
MODULES = ['src/data/b2_dataset.py', 'src/models/b2_classifier.py', 'src/evaluation/b2_evaluator.py']


def metrics_match(actual, expected, *, crop=False):
    """Require exact classification results; allow one rounded loss unit."""
    actual, expected = dict(actual), dict(expected)
    if crop:
        a, b = actual.pop('weighted_val_loss', None), expected.pop('weighted_val_loss', None)
        if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (a, b)):
            return False
        # Loss is serialized to 4 decimals and can differ across CPU/GPU runtimes.
        if abs(a - b) > 0.0001 + 1e-12:
            return False
    return actual == expected


def load_module(root, path):
    spec = importlib.util.spec_from_file_location('review_' + Path(path).stem, root / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(source, tv3_root, output):
    import torch
    torch.set_num_threads(4)
    tv3_root = Path(tv3_root).resolve()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=tv3_root, text=True).strip()
    if head != TV3_COMMIT:
        raise ValueError('TV3 checkout must be at the pinned handoff commit')
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--', *MODULES], cwd=tv3_root, check=True)
    cache = ClassifierCache()
    entry = cache.registry()['B2']
    source = Path(source).resolve()
    if source.stat().st_size != entry['checkpoint_bytes'] or digest(source) != entry['sha256']:
        raise ValueError('B2 checkpoint SHA/size mismatch')
    comp = ROOT / 'data/processed/comparison_v1'
    if digest(comp / 'provenance.json') != entry['provenance_sha256']:
        raise ValueError('Frozen provenance mismatch')
    provenance = json.loads((comp / 'provenance.json').read_text(encoding='utf-8'))
    for path in ('class_map.json', 'b1/train.jsonl', 'b1/val.jsonl', 'b2/train.jsonl', 'b2/val.jsonl'):
        if digest(comp / path) != provenance['files_sha256'][path]:
            raise ValueError('Changed frozen view: ' + path)
    report_bytes = subprocess.check_output(
        ['git', 'show', TV3_COMMIT + ':reports/tv3/validation_comparison.json'], cwd=ROOT)
    reference = json.loads(report_bytes)
    report = {'status': 'running', 'checked_utc': utc_now(), 'tv3_commit': head,
              'checkpoint_sha256': digest(source), 'checkpoint_bytes': source.stat().st_size,
              'reference_report_sha256': hashlib.sha256(report_bytes).hexdigest(),
              'provenance_sha256': entry['provenance_sha256'],
              'device': 'cpu', 'test_opened': False, 'training_performed': False}
    state = output.parent / 'b2_validation_state'
    with state_lock(state):
        atomic_json(output, report)
        try:
            ck = torch.load(source, map_location='cpu', weights_only=True)
            model, transform = checkpoint_model(ck, 'B2', entry, cache.names())
            dataset_module = load_module(tv3_root, MODULES[0])
            model_module = load_module(tv3_root, MODULES[1])
            evaluator = load_module(tv3_root, MODULES[2])
            datasets = {}
            for split in ('train', 'val'):
                datasets[split] = dataset_module.B2ComparisonDataset(
                    split, manifest_path=comp / 'b2' / (split + '.jsonl'),
                    class_map_path=comp / 'class_map.json', root=ROOT, preflight_hash_check=True)
                b1_ids = {json.loads(line)['image_id'] for line in
                          (comp / 'b1' / (split + '.jsonl')).read_text(encoding='utf-8').splitlines()}
                if set(datasets[split].get_image_ids()) != b1_ids:
                    raise ValueError('B1/B2 parent image mismatch')
            report.update(source_images_verified=sum(len(ds.get_image_ids()) for ds in datasets.values()),
                          source_image_hash_check=True, phase='validation')
            atomic_json(output, report)
            native = model_module.B2CropClassifier(8, 'resnet18', pretrained=False, dropout_p=0)
            native.load_state_dict(ck['model_state_dict'], strict=True)
            native.eval()
            from PIL import Image
            first = datasets['val'].samples[0]
            with Image.open(ROOT / first['quality']['local_path']) as image:
                tensor = transform(image.convert('RGB').crop(tuple(first['bbox_xyxy'])))
            if not torch.equal(tensor, datasets['val'][0]['image']):
                raise ValueError('TV4 and TV3 validation preprocessing differ')
            with torch.inference_mode():
                a, b = model(tensor[None]), native(tensor[None])
            delta = float((a - b).abs().max())
            if not torch.allclose(a, b, atol=1e-6, rtol=1e-5):
                raise ValueError('TV4 adapter differs from native TV3 wrapper')
            loader = torch.utils.data.DataLoader(datasets['val'], batch_size=16, shuffle=False,
                                                  num_workers=0, collate_fn=dataset_module.b2_collate_fn)
            metrics = evaluator.evaluate_b2_model(model, loader, torch.device('cpu'), 8, dict(enumerate(cache.names())))
            report.update(metrics=metrics, adapter_native_max_logit_delta=delta,
                          best_epoch=ck['epoch'], val_images=len(datasets['val'].get_image_ids()),
                          val_crops=len(datasets['val']), checkpoint_metrics=ck['val_metrics'])
            mismatches = []
            for actual_key, reference_key in (('image_level', 'image_level_metrics'), ('crop_level', 'crop_level_metrics')):
                if not metrics_match(metrics[actual_key], reference[reference_key], crop=actual_key == 'crop_level'):
                    mismatches.append('published_' + actual_key)
                if not metrics_match(metrics[actual_key], ck['val_metrics'][actual_key], crop=actual_key == 'crop_level'):
                    mismatches.append('checkpoint_' + actual_key)
            if ck['epoch'] != reference['best_epoch']:
                mismatches.append('epoch')
            report['mismatches'] = mismatches
            report['comparison_policy'] = {
                'classification_metrics': 'exact, including confusion matrices and per-class results',
                'weighted_val_loss_absolute_tolerance': 0.0001,
                'actual_loss': metrics['crop_level']['weighted_val_loss'],
                'published_loss': reference['crop_level_metrics']['weighted_val_loss'],
                'note': 'One unit at 4-decimal serialization; cause of cross-runtime loss difference not proven.',
            }
            if mismatches:
                raise ValueError('Fresh validation disagrees with handoff: ' + ', '.join(mismatches))
            report.update(status='PASS', phase='complete', checked_utc=utc_now())
        except BaseException as exc:
            report.update(status='FAILED', error=str(exc), checked_utc=utc_now())
            raise
        finally:
            atomic_json(output, report)
        print(json.dumps({k: v for k, v in report.items() if k not in ('metrics', 'checkpoint_metrics')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--tv3-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/tv4/w3_continuation/b2_validation.json')
    args = parser.parse_args()
    verify(args.source, args.tv3_root, args.output)
