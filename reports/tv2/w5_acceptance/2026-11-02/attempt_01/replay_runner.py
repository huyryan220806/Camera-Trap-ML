"""TV2 independent validation-only replay of a pinned TV3 DINO package.

Run in a fresh process. Does not train, modify source artifacts or read Test.
Exact reproduction is required: no numerical tolerance is introduced here.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, time

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(Path(path).read_bytes())

def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(value,handle,indent=2,ensure_ascii=False,allow_nan=False)
        handle.write('\n')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--vendor',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    root,source,run,vendor,out=[p.resolve() for p in (args.root,args.source,args.run,args.vendor,args.output)]
    assert not out.exists() and out.is_relative_to(root/'outputs')
    c=load(run/'config.json');receipt=load(run/'protocol.approved.json')
    checkpoint=run/'best_model.pt'
    assert sha(checkpoint)=='acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3'
    source_hashes={rel:sha(source/rel) for rel in receipt['source_lock']['files_sha256']}
    assert source_hashes==receipt['source_lock']['files_sha256']
    assert subprocess.check_output(['git','-C',str(vendor),'rev-parse','HEAD'],text=True).strip()==c['model']['repo_commit']
    assert not subprocess.check_output(['git','-C',str(vendor),'status','--porcelain'],text=True).strip()
    spec=importlib.util.spec_from_file_location('tv2_validation',root/'src/evaluation/w5_validation.py')
    w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
    parents,rows,hashes=w.load_frozen_validation(root)
    assert len(parents)==600 and len(rows)==680 and all(r['split']=='val' for r in rows)
    sys.path.insert(0,str(source))
    import torch
    from PIL import Image
    from src.training import dino_probe as d, dino_handoff as h
    assert torch.__version__=='2.6.0+cu124' and torch.cuda.is_available()
    torch.set_num_threads(10);torch.set_num_interop_threads(10)
    d.seed_all(42);d.validate_config(c);h.validate_protocol(c,receipt)
    reference=load(run/'validation.json')
    start=time.perf_counter();checked=set()
    for r in rows:
        if r['image_id'] in checked:continue
        path=(root/r['quality']['local_path']).resolve()
        assert path.is_relative_to(root/'data/images')
        assert sha(path)==r['quality']['sha256']
        with Image.open(path) as im:
            rgb=im.convert('RGB');assert rgb.size==(r['width'],r['height'])
            assert hashlib.sha256(f'RGB:{rgb.width}:{rgb.height}:'.encode()+rgb.tobytes()).hexdigest()==r['quality']['pixel_sha256']
        checked.add(r['image_id'])
        if len(checked)%100==0:print('TV2 validation pixel checks',len(checked),'/600',flush=True)
    assert len(checked)==600
    device='cuda';torch.cuda.reset_peak_memory_stats()
    backbone,head,transform,payload=d.load_package(checkpoint,sha(checkpoint),device=device,repo_dir=vendor)
    assert payload['config']==c and payload['binding']==load(run/'binding.json')
    assert payload['class_map']==load(run/'class_map.json')=={str(i):name for i,name in enumerate(w.CLASSES)}
    assert not backbone.training and not head.training
    assert all(not p.requires_grad for p in backbone.parameters())
    assert head.in_features==384 and head.out_features==8
    assert all(p.dtype==torch.float32 for p in list(backbone.parameters())+list(head.parameters()))
    assert h.preprocessing(c)==load(run/'preprocessing.json')
    print('Strict architecture load PASS, frozen CLS384 + Linear8; CUDA FP32',flush=True)
    features=[]
    extraction_start=time.perf_counter()
    with torch.inference_mode():
        for offset in range(0,len(rows),c['cache']['batch_size']):
            batch=rows[offset:offset+c['cache']['batch_size']]
            x=torch.stack([d.crop_tensor(r,transform,root) for r in batch]).to(device)
            features.append(d.extract(backbone,x).float().cpu())
            print('TV2 fresh features',offset+len(batch),'/680',flush=True)
        # Match registered reference evaluation shape: all680 features in one
        # linear-head call. This is not a feature-cache read or training batch.
        logits=head(torch.cat(features).to(device)).cpu()
    torch.cuda.synchronize()
    extraction_seconds=time.perf_counter()-extraction_start
    actual=d.evaluate_logits(logits,rows,payload['class_map'])
    comparison=d.compare_predictions(reference,actual)
    crop_prob_delta=max(abs(x-y) for a,b in zip(reference['crop_predictions'],actual['crop_predictions'])
                        for x,y in zip(a['probabilities'],b['probabilities']))
    image_prob_delta=max(abs(x-y) for a,b in zip(reference['image_predictions'],actual['image_predictions'])
                         for x,y in zip(a['probabilities'],b['probabilities']))
    out.mkdir(parents=True,exist_ok=False)
    predictions=out/'predictions.json';save(predictions,actual)
    report=dict(comparison,status='PASS' if comparison['passed'] else 'FAIL',fresh_process=True,
        independent_actor='TV2',comparison_policy='Exact Python object equality and zero logit difference; no relaxed tolerance',
        checkpoint_sha256=sha(checkpoint),checkpoint_bytes=checkpoint.stat().st_size,
        config_sha256=d.digest(c),protocol_sha256=sha(run/'protocol.approved.json'),
        source_hashes=source_hashes,vendor_commit=c['model']['repo_commit'],vendor_factory_sha256=sha(vendor/'dinov3/hub/backbones.py'),
        runtime=d.runtime(),device=device,preprocessing=h.preprocessing(c),
        validation_images=600,validation_crops=680,validation_source_byte_rgb_checks=600,manifest_sha256=hashes,
        frozen_backbone=True,head_shape=[384,8],precision='FP32',feature_cache_used=False,
        extraction_batch_crops=32,linear_evaluation_batch_crops=680,
        extraction_and_head_seconds=extraction_seconds,total_seconds=time.perf_counter()-start,
        peak_allocated_vram_bytes=torch.cuda.max_memory_allocated(),peak_reserved_vram_bytes=torch.cuda.max_memory_reserved(),
        max_abs_crop_probability_delta=crop_prob_delta,max_abs_image_probability_delta=image_prob_delta,
        reference_metrics=reference['metrics'],replayed_metrics=actual['metrics'],
        predictions_sha256=sha(predictions),predictions_path=str(predictions),
        training_performed=False,test_opened=False,test_inference_performed=False)
    save(out/'report.json',report)
    print(json.dumps({k:report[k] for k in ['status','max_abs_logit_delta','image_prediction_changes','total_seconds']},indent=2),flush=True)
    assert comparison['passed'],'Exact replay mismatch; retained FAIL evidence without tolerance relaxation'

if __name__=='__main__':main()
