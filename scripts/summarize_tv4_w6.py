"""Publish benchmark measurements/evidence without changing raw worker logs."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    raw=json.loads((args.input/'benchmark.json').read_text())
    assert raw['status']=='COMPLETE'
    registry=json.loads((ROOT/'configs/demo_w6.json').read_text())
    fixture=ROOT/'outputs/tv4/w6/benchmark_fixture/images.json'
    fixture_sha=hashlib.sha256(fixture.read_bytes()).hexdigest()
    for model in raw['models']:
        assert model['fixture_sha256']==fixture_sha and model['requests']==48 and model['unique_images']==24
        name=model['model_id']
        if name=='DINOv3_LP_run01':
            model['checkpoint_sha256']='acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3'
            model['model_version']='DINOv3_LP_run01'; model['feature_dim']=384
        else:
            entry=registry['models'][name]
            model['checkpoint_sha256']=entry['checkpoint_sha256']
            model['config_sha256']=entry['config_sha256']; model['feature_dim']=entry['feature_dim']
            model['model_version']=entry['run_id']+'_attempt01'
        model['dataset_version']='comparison_v1'
        model['runtime_helper_default_classifier_image_size']=model['runtime']['classifier_image_size']
        model['runtime']['classifier_image_size']=model['classifier_resolution']
        model['runtime_metadata_note']='Generic runtime_info defaults to legacy224; actual transform256 is recorded by classifier_resolution and envelope preprocessing. Raw worker JSON kept unchanged.'
        shutil.copy2(args.input/(name+'.jsonl'),args.output/(name+'.jsonl'))
        shutil.copy2(args.input/(name+'.json'),args.output/(name+'.raw.json'))
    (args.output/'benchmark.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
    shutil.copy2(fixture,args.output/'benchmark_images.json')
    configuration={'registry':registry,'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        for name in ('src/demo/dino_w6.py','src/demo/dino.py','src/training/dino_w6.py',
                     'src/training/dino_probe.py','src/demo/detector.py','src/demo/inference.py',
                     'scripts/benchmark_tv4_w6.py','configs/demo_w6.json')},
        'note':'Hashes of the exact CPU inference implementation used in this benchmark; native vendor locked separately.'}
    (args.output/'configuration.json').write_text(json.dumps(configuration,indent=2),encoding='utf-8')
    index={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
           for p in sorted(args.output.iterdir()) if p.is_file()}
    (args.output/'benchmark_index.json').write_text(json.dumps(index,indent=2),encoding='utf-8')
    print('Published benchmark evidence',args.output)


if __name__=='__main__': main()
