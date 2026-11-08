import hashlib, json, platform, sys
from pathlib import Path

root = Path.cwd()
e = root / 'outputs/tv2_w6/independent_replay_20261107'
prev_e = root / 'outputs/tv2_w6/independent_replay_20261106'

def load(n, base=e):
    return json.loads((base / n).read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

r3 = load('replay_R3.json')
r4 = load('replay_R4.json')
comp = load('exact_comparison.json')

producer_runtime = json.loads((root / 'outputs/tv2_w6/independent_acceptance_20261107/received/R3/R3_attempt01/runtime.json').read_text(encoding='utf-8'))

# TV2 replay attempts: 3 historical (R1, R1 retry, R2) + 2 new (R3, R4)
replays = [
    {
        'run_id': 'R1',
        'process_id': 12860,
        'result': 'INFERENCE_COMPLETED; initial console rendering raised cp1258 UnicodeEncodeError after replay JSON write',
        'gpu_hours': 0.03687700852777602,
        'wall_seconds': 132.75723069999367
    },
    {
        'run_id': 'R1',
        'process_id': 13580,
        'result': 'COMPLETED; clean UTF-8 log retained',
        'gpu_hours': 0.04432501094444888,
        'wall_seconds': 159.5700394000014
    },
    {
        'run_id': 'R2',
        'process_id': 10564,
        'result': 'COMPLETED; clean UTF-8 log retained',
        'gpu_hours': 0.03654925344443958,
        'wall_seconds': 131.57731239998247
    },
    {
        'run_id': 'R3',
        'process_id': r3['pid'],
        'result': 'COMPLETED; clean UTF-8 log retained',
        'gpu_hours': r3['gpu_hours'],
        'wall_seconds': r3['inference_wall_seconds']
    },
    {
        'run_id': 'R4',
        'process_id': r4['pid'],
        'result': 'COMPLETED; clean UTF-8 log retained',
        'gpu_hours': r4['gpu_hours'],
        'wall_seconds': r4['inference_wall_seconds']
    }
]

total_gpu_hours = sum(x['gpu_hours'] for x in replays)

receipt = {
    'receipt_id': 'TV2_W6_INDEPENDENT_MODEL_REPLAY_2026-11-07',
    'branch': 'feat/baseline',
    'head_before_report_commit': '056ee897dbd9929844787a65ab705c09ecfbf846',
    'protocol_lock_commit': '056ee897dbd9929844787a65ab705c09ecfbf846',
    'tv3_result_commit': '61498e7ffc6831b1988cc2d1296457c1fe613373',
    'tv3_source_commit': '95652c2d770cac464633eef0149bd27f4d859ece',
    'status': comp['model_replay_status'],
    'exact_comparison': {
        'path': 'outputs/tv2_w6/independent_replay_20261107/exact_comparison.json',
        'sha256': sha(e / 'exact_comparison.json'),
        'comparison_policy': comp['comparison_policy'],
        'all_runs_exact': all(x['exact_all_required'] for x in comp['runs'])
    },
    'runtime': {
        'producer': producer_runtime,
        'tv2_replay': {
            'python': r3['python_version'],
            'python_executable': r3['python_executable'],
            'platform': r3['platform'],
            'torch': r3['torch'],
            'torchvision': r3['torchvision'],
            'pillow': r3['pillow'],
            'numpy': r3['numpy'],
            'sklearn': r3['sklearn'],
            'cuda': r3['cuda'],
            'cudnn': r3['cudnn'],
            'gpu': r3['gpu'],
            'vram_bytes': r3['vram_bytes'],
            'runtime': r3['runtime'],
            'deterministic_algorithms': r3['deterministic_algorithms'],
            'cudnn_deterministic': r3['cudnn_deterministic'],
            'cudnn_benchmark': r3['cudnn_benchmark'],
            'tf32_matmul': r3['tf32_matmul'],
            'tf32_cudnn': r3['tf32_cudnn'],
            'amp_enabled': r3['amp_enabled']
        },
        'producer_python_build_differs': r3['python_version'] != producer_runtime.get('python')
    },
    'inputs': {
        'zip_sha256': {
            'R3': r3['zip_sha256'],
            'R4': r4['zip_sha256']
        },
        'best_checkpoint_sha256': {
            'R3': r3['checkpoint_sha256'],
            'R4': r4['checkpoint_sha256']
        },
        'config_raw_sha256': {
            'R3': r3['config_raw_sha256'],
            'R4': r4['config_raw_sha256']
        },
        'config_canonical_sha256': {
            'R3': r3['config_canonical_sha256'],
            'R4': r4['config_canonical_sha256']
        },
        'source_commit': '95652c2d770cac464633eef0149bd27f4d859ece',
        'vendor_commit': r3['vendor_commit'],
        'dataset_provenance_sha256': r3['provenance_sha256'],
        'validation_image_manifest_sha256': r3['image_manifest_sha256'],
        'validation_crop_manifest_sha256': r3['val_manifest_sha256'],
        'validation_images': 600,
        'validation_crops': 680,
        'raw_bytes_and_rgb_pixels_verified': True
    },
    'gpu_accounting': {
        'budget_gpu_hours': 2.0,
        'replays': replays,
        'total_gpu_hours': total_gpu_hours,
        'remaining_gpu_hours': 2.0 - total_gpu_hours,
        'calculation': 'sum of wall seconds from checkpoint/model load through CUDA-synchronized inference and metric evaluation, divided by 3600; conservative accounting',
        'training_or_test_inference': False
    },
    'artifacts': {
        run: {
            'path': f'outputs/tv2_w6/independent_replay_20261107/replay_{run}.json',
            'sha256': sha(e / f'replay_{run}.json'),
            'log_path': f'outputs/tv2_w6/independent_replay_20261107/replay_{run}.log',
            'log_sha256': sha(e / f'replay_{run}.log')
        } for run in ('R3', 'R4')
    },
    'multi_seed_evaluation': {
        'recipe': 'R2',
        'seeds': [42, 43, 44],
        'individual_accuracy': {'42': 0.8516666666666667, '43': 0.8433333333333334, '44': 0.8516666666666667},
        'individual_macro_f1': {'42': 0.850650853041619, '43': 0.8427567876976385, '44': 0.850644765168246},
        'mean_accuracy': 0.8488888888888889,
        'sample_sd_accuracy': 0.004811252243246881,
        'mean_macro_f1': 0.8480174686358345,
        'sample_sd_macro_f1': 0.004555883907153724,
        'below_88_percent_target_by_correct_images': 18.67,
        'all_seeds_below_target': True,
        'target_correct': 528
    }
}

out_receipt = e / 'environment_receipt.json'
out_receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
print(json.dumps({
    'receipt': str(out_receipt),
    'sha256': sha(out_receipt),
    'model_replay': receipt['status'],
    'gpu_hours': total_gpu_hours,
    'remaining': 2.0 - total_gpu_hours
}, indent=2, ensure_ascii=False))
