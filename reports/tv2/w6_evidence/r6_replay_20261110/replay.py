import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PKG = OUT / 'received'
VENDOR = PROJECT / 'outputs/tv2_w6/independent_replay_20261106/vendor/dinov3'
sys.path.insert(0, str(PKG))
from src.training import dino_probe as w5
from src.training import dino_w6 as w6
import torch
import torchvision
import PIL
import numpy
import sklearn

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

cfg_path = PROJECT / 'configs/w6/tv3/R6.3h.frozen.json'
config = read(cfg_path)
hand = read(PKG / 'handoff.json')
binding = read(PKG / 'binding.json')
source = read(PKG / 'source_index.json')
assert all(sha(PKG / name) == digest for name, digest in source['files_sha256'].items())
assert source == binding['source_index']
assert source['commit'] == hand['source_sha'] == '3b4b106c01e64901f213f6eebfdd10ffa55a7eb7'
assert sha(cfg_path) == sha(PKG / 'config.json') == hand['config_raw_sha256']
assert canonical(config) == hand['config_sha256'] == binding['config_sha256']
assert config == read(PKG / 'config.json')
assert config['preprocessing'] == read(PKG / 'preprocessing.json')['validation']
assert read(PKG / 'class_map.json') == binding['class_map']
assert hand['class_order'] == list(binding['class_map'].values())
assert sha(PKG / 'best_model.pt') == hand['checkpoint_sha256']
assert w5.git_revision(VENDOR) == config['vendor_commit'] == hand['vendor_commit']

assert sys.version_info[:3] == (3, 12, 10)
assert torch.__version__ == '2.6.0+cu124'
assert torchvision.__version__ == '0.21.0+cu124'
assert PIL.__version__ == '12.2.0'
assert numpy.__version__ == '2.5.3'
assert sklearn.__version__ == '1.9.0'
assert torch.version.cuda == '12.4' and torch.backends.cudnn.version() == 90100
assert torch.cuda.is_available() and torch.cuda.get_device_name(0) == 'NVIDIA GeForce RTX 4060 Laptop GPU'
for field, actual in [('torch',torch.__version__),('torchvision',torchvision.__version__),('pillow',PIL.__version__),('numpy',numpy.__version__),('sklearn',sklearn.__version__),('cuda',torch.version.cuda),('cudnn',torch.backends.cudnn.version()),('gpu',torch.cuda.get_device_name(0))]:
    assert binding['runtime'][field] == actual, field

w5.ROOT = PROJECT
w6.ROOT = PROJECT
rows, cmap, gate = w5.read_release(PROJECT, verify_images=False)
assert len(rows['val']) == 680 and len({r['image_id'] for r in rows['val']}) == 600
assert cmap == binding['class_map']
assert sha(PROJECT / 'data/processed/comparison_v1/provenance.json') == w5.PROVENANCE
assert w6.verify_pixels(rows['val'], PROJECT) == 600

payload = torch.load(PKG / 'best_model.pt', map_location='cpu', weights_only=True)
assert payload['config'] == config and payload['binding'] == binding
configured_runtime = w6.configure_runtime(config)
assert torch.are_deterministic_algorithms_enabled()
assert torch.get_num_threads() == torch.get_num_interop_threads() == 10
assert not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32

torch.cuda.synchronize()
start = time.perf_counter()
model, transform, loaded = w6.load_package(PKG / 'best_model.pt', hand['checkpoint_sha256'], VENDOR, 'cuda')
assert loaded['binding'] == binding
assert not model.training
logits = w6.validation_logits(model, config, rows['val'], 'cuda', root=PROJECT)
torch.cuda.synchronize()
evaluation = w5.evaluate_logits(logits, rows['val'], cmap)
torch.cuda.synchronize()
seconds = time.perf_counter() - start

replay = {'created_utc':datetime.now(timezone.utc).isoformat(), 'pid':os.getpid(),
          'python':sys.version, 'torch':torch.__version__, 'torchvision':torchvision.__version__,
          'pillow':PIL.__version__, 'numpy':numpy.__version__, 'sklearn':sklearn.__version__,
          'cuda':torch.version.cuda, 'cudnn':torch.backends.cudnn.version(),
          'gpu':torch.cuda.get_device_name(0), 'runtime':configured_runtime,
          'checkpoint_sha256':sha(PKG / 'best_model.pt'), 'config_sha256':canonical(config),
          'source_commit':source['commit'], 'vendor_commit':w5.git_revision(VENDOR),
          'validation_images':600, 'validation_crops':680, 'inference_wall_seconds':seconds,
          'gpu_hours':seconds / 3600, 'strict_state_load':True,
          'training_performed':False, 'test_opened':False, 'evaluation':evaluation}
(OUT / 'replay.json').write_text(json.dumps(replay, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
print(json.dumps({'metrics':evaluation['metrics'], 'seconds':seconds, 'gpu_hours':seconds/3600,
                  'replay_sha256':sha(OUT / 'replay.json')}, ensure_ascii=False))
