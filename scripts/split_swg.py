"""Deterministic location-held-out split, using labels only, never model scores."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import sqlite3

import numpy as np

from prepare_swg import DB, ROOT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose_location_split(records, classes, seed, attempts=2000, min_sequences=10, min_locations=2):
    locations = sorted({r['location'] for r in records})
    li = {v:i for i,v in enumerate(locations)}
    ci = {v:i for i,v in enumerate(classes)}
    counts = np.zeros((len(locations),len(classes)),dtype=np.int64)
    seqs = defaultdict(set)
    for r in records:
        counts[li[r['location']],ci[r['label']]] += 1
        seqs[(r['location'],r['label'])].add(r['seq_id'])
    sequence_counts = np.zeros_like(counts)
    for (loc,label), ids in seqs.items(): sequence_counts[li[loc],ci[label]]=len(ids)
    if np.any(counts.sum(axis=0)==0): raise ValueError('A selected class has no eligible images')
    ntrain = round(.7*len(locations)); nval=round(.15*len(locations))
    if min(ntrain,nval,len(locations)-ntrain-nval)<min_locations:
        raise ValueError('Not enough locations for three disjoint splits')
    rng = np.random.default_rng(seed)
    targets=np.array([.7,.15,.15])[:,None]
    best=None
    for attempt in range(attempts):
        shuffled=rng.permutation(len(locations))
        groups=[shuffled[:ntrain],shuffled[ntrain:ntrain+nval],shuffled[ntrain+nval:]]
        ic=np.array([counts[g].sum(axis=0) for g in groups])
        sc=np.array([sequence_counts[g].sum(axis=0) for g in groups])
        lc=np.array([(counts[g]>0).sum(axis=0) for g in groups])
        if np.any(sc < min_sequences) or np.any(lc < min_locations): continue
        score=float(np.mean((ic/counts.sum(axis=0)-targets)**2)+np.mean((sc/sequence_counts.sum(axis=0)-targets)**2))
        if best is None or score<best[0]: best=(score,attempt,groups)
    if best is None: raise ValueError('No feasible split. Review classes or sample support; do not silently relax constraints.')
    score,attempt,groups=best
    mapping={locations[int(i)]:split for split,group in zip(['train','val','test'],groups) for i in group}
    return mapping,{'objective':score,'chosen_attempt_zero_based':attempt,'attempts':attempts,'seed':seed,
                    'algorithm':'seeded PCG64 permutation search over locations; minimize squared per-class image and sequence ratio deviation',
                    'target_ratios':[.7,.15,.15],'min_sequences_per_class_per_split':min_sequences,'min_locations_per_class_per_split':min_locations}


def audit_records(records):
    overlap={key:{} for key in ['image_id','file_name','seq_id','location']}
    duplicate_ids=[]; seen=set()
    for r in records:
        if r['image_id'] in seen: duplicate_ids.append(r['image_id'])
        seen.add(r['image_id'])
        for key in overlap:
            overlap[key].setdefault(r[key],set()).add(r['split'])
    leaked={key:[v for v,splits in entries.items() if len(splits)>1] for key,entries in overlap.items()}
    duplicates=len(records)-len({r['file_name'] for r in records})
    return {'rows':len(records),'duplicate_image_ids':len(duplicate_ids),'duplicate_file_paths':duplicates,
            'cross_split_overlap':{k:len(v) for k,v in leaked.items()},
            'metadata_leakage_check_passed':not duplicate_ids and duplicates==0 and all(not v for v in leaked.values()),
            'image_content_duplicates_checked':False,
            'image_content_note':'Images have not been downloaded. Pixel hashes and perceptual duplicates are NOT checked.'}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--config',default='configs/split_v1.json'); parser.add_argument('--output',default='data/processed/v1')
    args=parser.parse_args(); config=json.loads((ROOT/args.config).read_text(encoding='utf-8'))
    output=ROOT/args.output
    if (output/'manifest_v1.jsonl').exists(): raise SystemExit('Existing manifest is frozen. Choose a new --output directory for a new version or reproducibility check.')
    conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row
    for k in ['box_image_metadata_mismatches','box_images_missing_main']:
        v=json.loads(conn.execute('SELECT value FROM metadata WHERE key=?',(k,)).fetchone()[0])
        if v: raise ValueError(f'Unresolved source mismatch: {k}={v}')
    classes=config['classes']; placeholders=','.join('?' for _ in classes)
    records=[dict(r) for r in conn.execute(f'SELECT * FROM boxed_eligible WHERE label IN ({placeholders}) ORDER BY id',classes)]
    if not records: raise ValueError('No records')
    # A sequence spanning locations would defeat a location-only split.
    seq_locations=defaultdict(set)
    for r in records: seq_locations[r['seq_id']].add(r['location'])
    if any(len(v)>1 for v in seq_locations.values()): raise ValueError('A sequence spans locations; resolve it before splitting')
    mapping,details=choose_location_split(records,classes,config['seed'],config['attempts'],config['min_sequences'],config['min_locations'])
    boxes=defaultdict(list)
    for b in conn.execute('SELECT * FROM boxes WHERE status="valid" ORDER BY id'):
        boxes[b['image_id']].append({'annotation_id':b['id'],'label':b['category_name'],'bbox_xywh':json.loads(b['bbox'])})
    clean=[]
    for r in records:
        clean.append({'image_id':r['id'],'file_name':r['file_name'],'sequence_id':r['seq_id'],'seq_id':r['seq_id'],
                      'location':r['location'],'country':r['country'],'datetime':r['datetime'],'width':r['width'],'height':r['height'],
                      'label':r['label'],'class_id':classes.index(r['label']),'split':mapping[r['location']],
                      'image_annotation_sequence_level':bool(r['sequence_level']),'boxes':boxes[r['id']],
                      'url':'https://storage.googleapis.com/public-datasets-lila/swg-camera-traps/'+r['file_name']})
    audit=audit_records(clean)
    if not audit['metadata_leakage_check_passed']: raise ValueError(audit)
    output.mkdir(parents=True,exist_ok=True)
    def write_json(name,obj): (output/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
    def write_lines(name,rows):
        with (output/name).open('w',encoding='utf-8',newline='\n') as f:
            for r in rows: f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
    write_lines('manifest_v1.jsonl',clean)
    for split in ['train','val','test']: write_lines(split+'.jsonl',[r for r in clean if r['split']==split])
    # The pilot is for pipeline smoke tests only; its class balance is intentionally artificial.
    pilot=[]; rng=random.Random(config['seed'])
    for label in classes:
        for split,ratio in [('train',.7),('val',.15),('test',.15)]:
            pool=[r for r in clean if r['label']==label and r['split']==split]
            rng.shuffle(pool); pilot.extend(pool[:round(config['pilot_images_per_class']*ratio)])
    pilot.sort(key=lambda r:r['image_id']); write_lines('pilot_v1.jsonl',pilot)
    summary=[]
    for label in classes:
        for split in ['train','val','test']:
            group=[r for r in clean if r['label']==label and r['split']==split]
            summary.append({'label':label,'split':split,'images':len(group),'sequences':len({r['seq_id'] for r in group}),
                            'locations':len({r['location'] for r in group}),'boxes':sum(len(r['boxes']) for r in group)})
    write_json('class_map.json',{str(i):label for i,label in enumerate(classes)})
    write_json('location_split.json',dict(sorted(mapping.items())))
    write_json('split_statistics.json',summary)
    audit['pilot']=audit_records(pilot); write_json('audit.json',audit)
    sources=json.loads((ROOT/'data/raw/sources.json').read_text())
    write_json('provenance.json',{'config':config,'split_search':details,'sources':sources,
       'manifest_sha256':digest(output/'manifest_v1.jsonl'),'pilot_sha256':digest(output/'pilot_v1.jsonl'),
       'script_sha256':digest(Path(__file__)),'numpy_version':np.__version__,
       'scope':'public images with exactly one candidate image label and all valid boxes agreeing with that label; no image bytes inspected'})
    print(json.dumps({'audit':audit,'split_images':dict(Counter(r['split'] for r in clean)),'pilot_images':len(pilot),'classes':classes},indent=2))


if __name__=='__main__': main()
