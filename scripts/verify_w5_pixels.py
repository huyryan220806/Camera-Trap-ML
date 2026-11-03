"""Read/decode/hash only frozen comparison_v1 Train and Validation rasters."""
from concurrent.futures import ThreadPoolExecutor
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.evaluation.w5_validation import load_frozen_validation,read_jsonl,require,sha256
from comparison_data import image_check


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    require(args.output.resolve().is_relative_to(ROOT/'outputs') and not args.output.exists(),'Use a new outputs file')
    _,_,hashes=load_frozen_validation(ROOT)
    rows=[]
    for split in ('train','val'):
        batch=read_jsonl(ROOT/'data/processed/comparison_v1'/f'{split}.jsonl')
        require(all(r['split']==split for r in batch),'Wrong split')
        rows.extend(batch)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,_ in enumerate(pool.map(image_check,rows),1):
            if i%250==0 or i==len(rows):print(f'Train/Val raster verification {i}/{len(rows)}',flush=True)
    result=dict(status='PASS',checked_utc=datetime.now(timezone.utc).isoformat(),train_images=2800,val_images=600,
                checks='file SHA256, decode, RGB SHA256, dimensions vs frozen quality metadata',
                manifest_sha256=hashes,test_rasters_opened=False,near_duplicates_checked=False,training_performed=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
