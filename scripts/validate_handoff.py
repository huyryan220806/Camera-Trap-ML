"""Check saved handoff files independently of split creation."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from prepare_swg import ROOT, items, valid_bbox


def load_lines(path):
    with path.open(encoding='utf-8') as f: return [json.loads(line) for line in f]


def main():
    p=ROOT/'data/processed/v1'
    rows=load_lines(p/'manifest_v1.jsonl')
    assert len(rows)==len({r['image_id'] for r in rows})
    labels=json.loads((p/'class_map.json').read_text())
    groups={s:[r for r in rows if r['split']==s] for s in ['train','val','test']}
    for s in groups: assert load_lines(p/(s+'.jsonl'))==groups[s]
    for row in rows:
        assert row['file_name'].startswith('public/')
        assert labels[str(row['class_id'])]==row['label']
        assert row['boxes']
        for b in row['boxes']:
            x,y,w,h=b['bbox_xywh']
            assert w>0 and h>0 and 0<=x<x+w<=row['width']+1e-6 and 0<=y<y+h<=row['height']+1e-6
            assert b['label']==row['label']
    for field in ['image_id','file_name','seq_id','location']:
        sets=[{r[field] for r in groups[s]} for s in groups]
        assert not (sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2])
    pilots=load_lines(p/'pilot_v1.jsonl')
    by_id={r['image_id']:r for r in rows}
    assert all(by_id[r['image_id']]==r for r in pilots)
    hashes={}
    for name in ['manifest_v1.jsonl','pilot_v1.jsonl','location_split.json']:
        original=(p/name).read_bytes()
        reproduced=(ROOT/'data/processed/repro_check'/name).read_bytes()
        assert original==reproduced
        hashes[name]=hashlib.sha256(original).hexdigest()
    # Revalidate the source boxes after boundary-rule tests, without rewriting the frozen manifest.
    archive='swg_camera_traps.bounding_boxes.with_species.zip'
    images={im['id']:im for im in items(archive,'images')}
    counts=Counter(valid_bbox(a,images.get(a['image_id']))[1] for a in items(archive,'annotations'))
    summary=json.loads((ROOT/'reports/eda/summary.json').read_text())
    assert dict(counts)==summary['box_validation']
    notebook=json.loads((ROOT/'notebooks/01_metadata_eda.ipynb').read_text(encoding='utf-8'))
    for cell in notebook['cells']:
        if cell['cell_type']=='code': compile(''.join(cell['source']),cell['id'],'exec')
    result={'passed':True,'manifest_rows':len(rows),'pilot_rows':len(pilots),'split_rows':{s:len(v) for s,v in groups.items()},
            'same_seed_reproduces_identical_bytes':True,'sha256':hashes,'source_box_revalidation':dict(counts),
            'notebook_code_syntax_valid':True,'notebook_executed_in_jupyter':False,
            'image_content_hashes_checked':False}
    (ROOT/'reports/eda/verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
