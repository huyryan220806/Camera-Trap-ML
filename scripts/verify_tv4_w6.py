"""Real checkpoint/native comparison for R1-R4, including a real train crop."""
import argparse
import gc
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repo',type=Path,default=ROOT/'outputs/tv4/w5/dinov3_architecture')
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    import torch
    from PIL import Image
    from src.demo.classifier import ClassifierCache, crop_coordinates
    from src.demo.dino import DinoCache
    from src.demo.dino_w6 import W6Cache, MODEL_IDS
    from src.demo.review import runtime_info
    from src.training import dino_w6 as native
    torch.set_num_threads(4); torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    cache=W6Cache(DinoCache(ClassifierCache()),args.repo)
    row=json.loads((ROOT/'outputs/tv4/w6/benchmark_fixture/images.json').read_text())['images'][0]
    image=Image.open(ROOT/row['quality']['local_path']).convert('RGB')
    real=image.crop(crop_coordinates(row['boxes'][0]['bbox_xywh'],image.size))
    crops=[real,Image.new('L',(67,193),128),Image.new('RGB',(193,67),(23,68,112))]*3
    report={'runtime':{**runtime_info(),'classifier_image_size':256},'device':'cpu','precision':'FP32','amp':False,'tf32':False,
        'test_opened':False,'scope':'same-device/same-batch native equivalence, not validation metric replay',
        'real_train_image_id':row['image_id'],'crop_batches':[8,1],'models':{}}
    for kind in ('DINO_W6_R2','DINO_W6_R1','DINO_W6_R3','DINO_W6_R4'):
        logits,metadata=cache.logits(crops,kind)
        _,folder,config,entry,_=cache.validate(kind)
        model,transform,payload=native.load_package(folder/'best_model.pt',entry['checkpoint_sha256'],args.repo,'cpu')
        reference=torch.cat([native.predict_crops(model,transform,crops[i:i+8],'cpu') for i in range(0,9,8)])
        assert torch.equal(logits,reference), f'{kind}: logit mismatch, no tolerance relaxed'
        assert torch.equal(logits.softmax(-1),reference.softmax(-1))
        one,_=cache.logits([real],kind)
        assert torch.equal(one,native.predict_crops(model,transform,[real],'cpu'))
        detections=[{'detection_id':'a','bbox_xywh':[0,0,30,60]}, {'detection_id':'b','bbox_xywh':[10,80,50,100]}]
        tops,_=cache.predict(Image.new('RGB',(100,240)),detections,kind)
        assert len(tops)==2 and all(len(t)==3 for t in tops)
        _,warm=cache.logits([real],kind); assert warm['cache_hit']
        report['models'][kind]={'status':'PASS','max_abs_logit_delta':(logits-reference).abs().max().item(),
            'max_abs_score_delta':0,'adapter_logits':logits.tolist(),'native_logits':reference.tolist(),
            'top3_portrait':tops,'metadata':metadata,'warm_metadata':warm,'feature_dim':config['feature_dim']}
        print(kind,'native/adapter exact PASS',flush=True)
        del model,transform,payload; gc.collect()
    # Capacity1 cache must reload after swapping away from R2 and back.
    _,reloaded=cache.logits([real],'DINO_W6_R2'); assert not reloaded['cache_hit']
    report['cache_swap_reload']=reloaded
    report['status']='PASS'
    (args.output/'equivalence.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__': main()
