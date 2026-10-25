"""Validation-only integrity and exact prediction replay checks."""
import hashlib
import json
import platform
from pathlib import Path

PROVENANCE = 'd9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f'
CHECKPOINTS = {
    '8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5': 'B2',
    '93ae48dd4b42fa6062daed3a9a1869d620bd7ba9e7ae2aa274085b061f76300b': 'B3',
}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def runtime_metadata(device, batch_size=32):
    import torch
    import torchvision
    import PIL
    return {'python': platform.python_version(), 'torch': torch.__version__,
            'torchvision': torchvision.__version__, 'pillow': PIL.__version__,
            'device': str(device), 'device_name': torch.cuda.get_device_name(device) if device.type == 'cuda' else platform.processor(),
            'cuda': torch.version.cuda, 'cudnn': torch.backends.cudnn.version(),
            'cudnn_deterministic': torch.backends.cudnn.deterministic,
            'cudnn_benchmark': torch.backends.cudnn.benchmark,
            'cudnn_allow_tf32': torch.backends.cudnn.allow_tf32,
            'matmul_allow_tf32': torch.backends.cuda.matmul.allow_tf32,
            'deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
            'threads': torch.get_num_threads(), 'crop_batch_size': batch_size}


def verify_validation_inputs(root, checkpoint_path, checkpoint):
    root = Path(root)
    sha = digest(checkpoint_path)
    if sha not in CHECKPOINTS:
        raise ValueError('Checkpoint is not a pinned delivered B2/B3 artifact')
    comp = root / 'data/processed/comparison_v1'
    if digest(comp / 'provenance.json') != PROVENANCE:
        raise ValueError('Frozen provenance SHA mismatch')
    provenance = json.loads((comp / 'provenance.json').read_text(encoding='utf-8'))
    for name in ('class_map.json', 'train.jsonl', 'val.jsonl', 'b2/train.jsonl', 'b2/val.jsonl'):
        if digest(comp / name) != provenance['files_sha256'][name]:
            raise ValueError('Frozen validation input changed: ' + name)
    cmap = json.loads((comp / 'class_map.json').read_text(encoding='utf-8'))
    names = {int(k): v for k, v in cmap.items()}
    if (checkpoint.get('provenance_sha256') != PROVENANCE or checkpoint.get('is_official') is not True
            or checkpoint.get('id_to_label') != names
            or checkpoint.get('class_map') != {v: k for k, v in names.items()}
            or checkpoint.get('num_classes') != 8 or checkpoint.get('backbone_name') != 'resnet18'):
        raise ValueError('Checkpoint metadata does not match frozen data')
    return comp, sha, CHECKPOINTS[sha]


def compare_replay(expected, actual):
    """A close scalar metric cannot override a changed prediction or matrix."""
    def index(records):
        result = {p['image_id']: (p['true_class_id'], p['predicted_class_id']) for p in records}
        if not records or len(result) != len(records):
            raise ValueError('Replay requires unique nonempty image predictions')
        return result
    before, after = index(expected['predictions']), index(actual['predictions'])
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    cm_match = expected['image_level']['confusion_matrix'] == actual['image_level']['confusion_matrix']
    metrics_match = all(expected['image_level'].get(k) == actual['image_level'].get(k)
                        for k in ('macro_f1', 'macro_precision', 'macro_recall', 'accuracy'))
    metrics_match = metrics_match and expected.get('unrounded_metrics') == actual.get('unrounded_metrics')
    return {'status': 'PASS' if not changed and cm_match and metrics_match else 'FAIL',
            'classification_metrics_match': metrics_match,
            'prediction_ids_and_labels_match': not changed, 'confusion_matrix_matches': cm_match,
            'changed_image_ids': changed, 'expected': expected, 'reloaded': actual,
            'policy': 'Exact image IDs, true/predicted labels and confusion matrix; no scalar-F1 tolerance.'}
