"""Convert a successful fresh-process B2 verification into W5 comparison artifacts."""
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation.w5_validation import (B2_SHA256, audit_predictions, load_frozen_validation,
    read_json, require, sha256)
from src.demo.review import runtime_info


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    out=args.output.resolve()
    require(out.is_relative_to(ROOT/'outputs') and not out.exists(),'Use a new outputs directory')
    folder=args.verification_dir
    source=read_json(folder/'verification.json')
    require(source['status']=='PASS' and source['fresh_process'] and source['checkpoint_sha256']==B2_SHA256,
            'Need verified pinned B2 fresh-process positive control')
    require(source['test_inference_performed'] is False and source['test_manifest_opened'] is False,
            'B2 verification must be Validation only')
    checkpoint=Path(source['checkpoint_path'])
    require(sha256(checkpoint)==B2_SHA256,'B2 checkpoint changed')
    parents,crops,hashes=load_frozen_validation(ROOT)
    experiment='B2_W5_reference_attempt01'
    predictions=[dict(image_id=r['image_id'],ground_truth=r['true_class_id'],predicted_class=r['predicted_class_id'],
                      class_scores=r['probabilities'],crop_count=r['num_crops'],experiment_id=experiment,
                      checkpoint_sha256=B2_SHA256) for r in read_json(folder/'validation_predictions.json')]
    result=audit_predictions(predictions,parents,crops,experiment,B2_SHA256)
    require(all(abs(value-source['image_level_metrics'][key])<1e-12 for key,value in result['metrics'].items()),
            'Independent metrics differ from fresh-process verifier')
    result.update(experiment_id=experiment,verification='PASS',dataset_version='comparison_v1',
                  manifest_sha256=hashes,checkpoint_sha256=B2_SHA256,
                  input_sha256={p.name:sha256(p) for p in folder.iterdir() if p.is_file()})
    hardware=runtime_info()
    environment={key:hardware[key] for key in ('cpu','logical_cpus','ram_gib','os','python','versions')}
    environment.update(source['environment'],crop_batch=32,workers=0)
    table=[dict(experiment_id=experiment,model='B2',architecture='ResNet18, FC8, dropout0',
                pretrained='torchvision ResNet18_Weights.IMAGENET1K_V1',dataset_version='comparison_v1',
                checkpoint_sha256=B2_SHA256,seed=42,train_images=2800,train_crops=3125,
                val_images=600,val_crops=680,**result['metrics'],
                validation_wall_seconds=source['validation_wall_seconds'],
                runtime_scope='Validation: native AND adapter forwards; excludes raster/hash preflight, includes metric/report preparation',
                environment=environment,
                verification='PASS',best_epoch=source['best_epoch'],training_performed=False),
           dict(experiment_id=None,model='DINO candidate (architecture not delivered)',architecture=None,pretrained=None,
                dataset_version='comparison_v1 (required)',checkpoint_sha256=None,seed=None,train_images=None,train_crops=None,
                val_images=None,val_crops=None,accuracy=None,macro_f1=None,macro_precision=None,macro_recall=None,
                validation_wall_seconds=None,environment=None,verification='BLOCKED',
                reason='No TV3 checkpoint/config/log/predictions/reload handoff; W5 protocol unapproved')]
    out.mkdir(parents=True,exist_ok=False)
    def dump(name,value):
        with (out/name).open('x',encoding='utf-8') as f:
            json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    dump('b2_metrics.json',result);dump('experiment_comparison.json',table)
    with (out/'b2_predictions.jsonl').open('x',encoding='utf-8') as f:
        for row in predictions:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    with (out/'b2_per_class.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(result['per_class'][0]));writer.writeheader();writer.writerows(result['per_class'])
    with (out/'b2_confusion_matrix.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['true/pred']+list(range(8)))
        writer.writerows([[i]+row for i,row in enumerate(result['confusion_matrix'])])
    # Validate the published row contract as well as semantic checks above.
    from jsonschema import Draft202012Validator
    schema=Draft202012Validator(read_json(ROOT/'contracts/w5_image_prediction.schema.json'))
    for row in predictions:schema.validate(row)
    print(json.dumps(dict(status='PASS',images=len(predictions),metrics=result['metrics'],output=str(out)),indent=2))


if __name__=='__main__':main()
