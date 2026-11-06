import argparse, hashlib, json, os, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
p=argparse.ArgumentParser(); p.add_argument('--run', choices=['R1','R2'], required=True); args=p.parse_args()
PROJECT=Path(__file__).resolve().parents[3]; E=PROJECT/'outputs/tv2_w6/independent_replay_20261106'; PKG=PROJECT/'outputs/tv2_w6/independent_acceptance_20261106/received'/args.run/(args.run+'_attempt01'); SRC=E/'remote_source'; VENDOR=E/'vendor/dinov3'
sys.path.insert(0,str(SRC))
from src.training import dino_probe as w5
from src.training import dino_w6 as w6
import torch

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def canon(o): return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
root=PROJECT; w5.ROOT=root; w6.ROOT=root
cfgpath=root/f'configs/w6/tv3/{args.run}.frozen.json'; config=json.loads(cfgpath.read_text(encoding='utf-8')); ckpt=PKG/'best_model.pt'; hand=json.loads((PKG/'handoff.json').read_text(encoding='utf-8'))
assert sha(ckpt)==hand['checkpoint_sha256']; assert sys.version_info[:3]==(3,12,10),sys.version; assert torch.__version__=='2.6.0+cu124',torch.__version__
import torchvision, PIL, numpy, sklearn
assert torchvision.__version__=='0.21.0+cu124',torchvision.__version__; assert PIL.__version__=='12.2.0' and numpy.__version__=='2.5.3' and sklearn.__version__=='1.9.0'; assert torch.cuda.is_available(); assert torch.version.cuda=='12.4' and torch.backends.cudnn.version()==90100; assert torch.get_default_dtype()==torch.float32
rows,cmap,gate=w5.read_release(root,verify_images=False); assert len(rows['val'])==680 and len({r['image_id'] for r in rows['val']})==600; assert w6.verify_pixels(rows['val'],root)==600
payload=torch.load(ckpt,map_location='cpu',weights_only=True); assert payload['config']==config and canon(config)==hand['config_sha256']; w6.configure_runtime(config); assert torch.are_deterministic_algorithms_enabled(); assert torch.get_num_threads()==10 and torch.get_num_interop_threads()==10; assert not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32; runtime=w5.runtime(); gpu=torch.cuda.get_device_name(0); assert gpu=='NVIDIA GeForce RTX 4060 Laptop GPU',gpu
torch.cuda.synchronize(); t0=time.perf_counter(); model,transform,payload=w6.load_package(ckpt,hand['checkpoint_sha256'],VENDOR,'cuda'); logits=w6.validation_logits(model,config,rows['val'],'cuda',root=root); torch.cuda.synchronize(); result=w5.evaluate_logits(logits,rows['val'],cmap); torch.cuda.synchronize(); elapsed=time.perf_counter()-t0
image_ids=sorted({r['image_id'] for r in rows['val']})
output={'run_id':args.run,'created_utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),'argv':sys.argv,'python_executable':sys.executable,'python_version':sys.version,'platform':platform.platform(),'torch':torch.__version__,'torchvision':torchvision.__version__,'pillow':PIL.__version__,'numpy':numpy.__version__,'sklearn':sklearn.__version__,'cuda':torch.version.cuda,'cudnn':torch.backends.cudnn.version(),'gpu':gpu,'vram_bytes':torch.cuda.get_device_properties(0).total_memory,'runtime':runtime,'deterministic_algorithms':torch.are_deterministic_algorithms_enabled(),'cudnn_deterministic':torch.backends.cudnn.deterministic,'cudnn_benchmark':torch.backends.cudnn.benchmark,'tf32_matmul':torch.backends.cuda.matmul.allow_tf32,'tf32_cudnn':torch.backends.cudnn.allow_tf32,'amp_enabled':False,'zip_sha256':sha(root/f'reports/tv3/w6/{args.run}_attempt01.zip'),'checkpoint_sha256':sha(ckpt),'config_raw_sha256':sha(cfgpath),'config_canonical_sha256':canon(config),'source_commit':hand['source_sha'],'vendor_commit':w5.git_revision(VENDOR),'provenance_sha256':sha(root/'data/processed/comparison_v1/provenance.json'),'val_manifest_sha256':sha(root/'data/processed/comparison_v1/b2/val.jsonl'),'image_manifest_sha256':sha(root/'data/processed/comparison_v1/b1/val.jsonl'),'validation_images':600,'validation_crops':680,'image_ids':image_ids,'crop_ids':[r['crop_id'] for r in rows['val']],'logits':logits.tolist(),'evaluation':result,'inference_wall_seconds':elapsed,'gpu_hours':elapsed/3600,'test_or_train_images_opened':False,'training_performed':False}
out=E/f'replay_{args.run}.json'; out.write_text(json.dumps(output,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8'); print(json.dumps({k:output[k] for k in ('run_id','pid','python_version','torch','torchvision','pillow','numpy','sklearn','cuda','cudnn','gpu','validation_images','validation_crops','inference_wall_seconds','gpu_hours')},indent=2,ensure_ascii=False)); print(json.dumps({'metrics':result['metrics'],'output':str(out),'output_sha256':sha(out)},indent=2,ensure_ascii=False))
