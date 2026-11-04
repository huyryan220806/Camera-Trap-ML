"""TV2 read-only metadata/package review of the pinned TV1 W6 snapshot.

No Test manifest/raster is opened. Test preservation uses Git object IDs only.
Optional image checks decode only the 1446 retained new TRAIN images in the ZIP.
This partial review cannot approve the expansion release.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.evaluation import w5_validation as w5
from src.evaluation.w6_validation import EXPANSION_SHA

REF = '11e451071f58146522df20e1890cc6fe6e488eb0'
BASE = 'cfcf00615847d52fba73ee3e44fe0e6076bb840c'
PREFIX = 'data/processed/train_expansion_w6_v1/'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def blob(path, ref=REF):
    return git('show',ref+':'+path)


def parse_rows(data):
    return [json.loads(line) for line in data.decode('utf-8').splitlines() if line.strip()]


def check_geometry(parents, crops):
    by_id = w5.unique(parents,'image_id')
    crop_ids = w5.unique(crops,'crop_id')
    counts = Counter(r['image_id'] for r in crops)
    w5.require(set(counts) == set(by_id), 'Crop parent coverage mismatch')
    expected = {}
    for parent in parents:
        w5.require(parent['split'] == 'train', 'Expansion must be train-only')
        w5.class_id(parent['class_id'])
        w5.require(parent['label'] == w5.CLASSES[parent['class_id']], 'Class map mismatch')
        for box in parent['boxes']:
            w5.require(box['label'] == parent['label'], 'Box label inconsistent with parent')
            x,y,width,height = box['bbox_xywh']
            bounds = [max(0,min(parent['width'],round(x))),max(0,min(parent['height'],round(y))),
                      max(0,min(parent['width'],round(x+width))),max(0,min(parent['height'],round(y+height)))]
            if bounds[2]-bounds[0] < 8 or bounds[3]-bounds[1] < 8:
                continue
            expected[(parent['image_id'],box['annotation_id'])] = bounds
    actual = {}
    for row in crops:
        parent = by_id[row['image_id']]
        key = (row['image_id'],row['annotation_id'])
        w5.require(key not in actual, 'Duplicate annotation crop')
        actual[key] = row['bbox_xyxy']
        w5.require(row['split'] == 'train' and row['class_id'] == parent['class_id'] and
                   row['label'] == parent['label'] and row['quality'] == parent['quality'], 'Crop/parent identity mismatch')
        for field in ('file_name','seq_id','location','width','height','url'):
            w5.require(row.get(field) == parent.get(field), 'Crop source field mismatch: '+field)
        w5.require(all(type(v) is int for v in row['bbox_xyxy']), 'Integer geometry required')
        w5.require(row['parent_crop_count'] == counts[row['image_id']] and
                   abs(row['sample_weight']-1/counts[row['image_id']]) <= 1e-12, 'Parent weighting mismatch')
    w5.require(actual == expected, 'Crop geometry/annotation coverage mismatch')
    return dict(parents=len(by_id),crops=len(crop_ids),per_class_images=dict(Counter(r['class_id'] for r in parents)),
                per_class_crops=dict(Counter(r['class_id'] for r in crops)))


def review_metadata():
    provenance_bytes = blob(PREFIX+'provenance.json')
    w5.require(hashlib.sha256(provenance_bytes).hexdigest() == EXPANSION_SHA, 'Release SHA mismatch')
    provenance = json.loads(provenance_bytes)
    snapshot = {name:blob(PREFIX+name) for name in provenance['files_sha256']}
    for name,data in snapshot.items():
        w5.require(hashlib.sha256(data).hexdigest() == provenance['files_sha256'][name], 'Snapshot checksum: '+name)
    def rows(name):return parse_rows(snapshot[name])
    def doc(name):return json.loads(snapshot[name])
    train,additional,excluded,crops = (rows(name) for name in ('train.jsonl','additional_train.jsonl','excluded.jsonl','b2/train.jsonl'))
    old_train = parse_rows(blob('data/processed/comparison_v1/train.jsonl',BASE))
    val = parse_rows(blob('data/processed/comparison_v1/val.jsonl',BASE))
    candidates = parse_rows(blob('data/processed/w5_candidates_v1/train_extension_candidates.jsonl'))
    holdout = parse_rows(blob('data/processed/w5_candidates_v1/holdout_candidates.jsonl'))
    w5.require([len(r) for r in (train,additional,excluded,crops,candidates)] == [4246,1446,219,4729,1665], 'Unexpected counts')
    original = w5.unique(old_train,'image_id');combined = w5.unique(train,'image_id')
    new = w5.unique(additional,'image_id');removed = w5.unique(excluded,'image_id');pool=w5.unique(candidates,'image_id')
    w5.require(not (set(new)&set(removed)) and set(new)|set(removed) == set(pool), 'Candidate partition mismatch')
    w5.require(set(combined) == set(original)|set(new) and all(combined[k] == v for k,v in original.items()), 'Old train changed')
    w5.require(all(combined[k] == v for k,v in new.items()), 'Additional train differs from combined')
    for iid,row in {**new,**removed}.items():
        w5.require(all(row.get(k) == v for k,v in pool[iid].items()), 'Source label/split/box changed: '+iid)
    w5.require(doc('class_map.json') == {str(i):v for i,v in enumerate(w5.CLASSES)}, 'Class map changed')
    result = check_geometry(train,crops)
    w5.require(set(w5.unique(rows('b1/train.jsonl'),'image_id')) == set(combined), 'B1/B2 population mismatch')
    decisions = w5.unique(rows('decisions.jsonl'),'image_id')
    w5.require(set(decisions) == set(pool), 'Decision coverage mismatch')
    reasons = Counter(r['exclusion']['reason'] for r in excluded)
    w5.require(reasons['near_duplicate_pending_review'] == 191 and
               sum(v for k,v in reasons.items() if k.startswith('exact_duplicate')) == 5 and
               sum(v for k,v in reasons.items() if k not in ('near_duplicate_pending_review',) and not k.startswith('exact_duplicate')) == 23,
               'Quarantine reason counts mismatch')
    for field in ('image_id','file_name','seq_id','location'):
        w5.require(not ({r[field] for r in train}&{r[field] for r in val+holdout}), 'Val/holdout leakage: '+field)
    features = w5.unique(rows('features.jsonl'),'image_id')
    for field in ('image_id','seq_id','location'):
        w5.require(not ({r[field] for r in train}&{r[field] for r in features.values() if r['split'] != 'train'}),
                   'Protected-split fingerprint metadata leakage: '+field)
    for row in additional:
        feature=features[row['image_id']]
        w5.require(all(feature[k] == row[k] for k in ('image_id','seq_id','location','label','split')) and
                   all(feature[k] == row['quality'][k] for k in ('sha256','pixel_sha256')),
                   'Retained image/fingerprint identity mismatch')
    # Compare metadata fingerprints for all protected splits, without opening their images/manifests.
    protected = [r for r in features.values() if r['image_id'] not in new]
    for key in ('sha256','pixel_sha256'):
        values = {r[key] for r in protected}
        w5.require(not ({r['quality'][key] for r in additional}&values), 'New retained exact content leakage: '+key)
        w5.require(len({r['quality'][key] for r in additional}) == len(additional), 'Duplicate within retained new images')
    near = doc('near_duplicates.json')
    w5.require(len(near) == 347, 'Near-duplicate pair count mismatch')
    flagged=set()
    for pair in near:
        a,b = [features[i] for i in pair['image_ids']]
        ph=(int(a['phash64'],16)^int(b['phash64'],16)).bit_count()
        dh=(int(a['dhash128'],16)^int(b['dhash128'],16)).bit_count()
        w5.require(ph == pair['phash_distance'] <= 4 and dh == pair['dhash_distance'] <= 8, 'Near-distance mismatch')
        w5.require(pair['splits'] == ['train','train'] and pair['model_used'] is False, 'Unexpected duplicate screening scope')
        flagged.update(pair['new_ids_quarantined'])
    w5.require(flagged <= set(removed) and not (flagged&set(new)), 'Flagged images retained')
    visual = doc('visual_review.json')
    w5.require(len(visual['items']) == 80 and visual['quarantined_count'] == 23 and visual['retained_count'] == 57, 'Visual sample accounting')
    preservation={}
    for split in ('val','test'):
        for view in ('','b1/','b2/'):
            path='data/processed/comparison_v1/'+view+split+'.jsonl'
            preservation[view+split] = git('rev-parse',BASE+':'+path).strip() == git('rev-parse',REF+':'+path).strip()
    w5.require(all(preservation.values()), 'Val/Test Git blob changed')
    result.update(status='PENDING REVIEW',release_commit=REF,release_sha256=EXPANSION_SHA,
                  snapshot_files_verified=len(snapshot)+1,candidates=1665,retained=1446,quarantined=219,
                  quarantine_reasons=dict(reasons),near_pairs_checked=len(near),near_flagged_ids=len(flagged),
                  val_test_git_blob_preserved=preservation,quality_ready=provenance['quality_ready'],
                  producer_peer_review_status=provenance['peer_review_status'],
                  test_manifest_opened=False,test_raster_opened=False,test_model_inference=False,
                  source_fingerprint_scope='Git metadata + producer features, not independent Test image rehash',
                  test_id_sequence_location_fingerprint_metadata='PASS',
                  test_path_leakage_independently_rechecked=False,
                  missing=['Quarantined 219 image bytes and visual review package',
                           'Independent full old Train/Val and holdout byte/RGB recheck',
                           'Independent visual/specialist review; source fingerprints are producer evidence'],
                  r5_r6_permitted=False)
    return result,snapshot,provenance_bytes,additional


def check_package(path,snapshot,provenance_bytes,additional):
    from PIL import Image
    import PIL
    expected_sha='a88bfbf99aa25ac70637f35dca6056851e4c300dd89c3906185f943b13b3f659'
    w5.require(path.stat().st_size == 2246204406 and w5.sha256(path) == expected_sha, 'Image ZIP identity mismatch')
    expected={PREFIX+name:data for name,data in snapshot.items()}
    expected[PREFIX+'provenance.json']=provenance_bytes
    images={row['quality']['local_path']:row for row in additional}
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        w5.require(len(names) == len(set(n.casefold() for n in names)), 'ZIP duplicate/case collision')
        w5.require(set(names) == set(expected)|set(images), 'ZIP membership mismatch')
        for info in infos:
            name=info.filename
            w5.require(not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts and
                       '\\' not in name and ':' not in name and not info.flag_bits&1 and
                       (info.external_attr >> 16)&0o170000 != 0o120000, 'Unsafe ZIP entry')
            data=archive.read(info)  # also validates CRC
            if name in expected:
                w5.require(data == expected[name], 'ZIP metadata differs from Git')
                continue
            row=images[name];quality=row['quality']
            w5.require(len(data) == quality['bytes'] and hashlib.sha256(data).hexdigest() == quality['sha256'], 'Image byte mismatch')
            with Image.open(io.BytesIO(data)) as image:
                rgb=image.convert('RGB');rgb.load()
                w5.require(rgb.size == (row['width'],row['height']), 'Image dimensions mismatch')
                sha=hashlib.sha256(('RGB:%d:%d:' % rgb.size).encode()+rgb.tobytes()).hexdigest()
                w5.require(sha == quality['pixel_sha256'], 'RGB mismatch')
        return dict(status='PASS',zip_sha256=expected_sha,zip_bytes=path.stat().st_size,
                    entries=len(names),new_train_images_byte_rgb_decoded=len(images),snapshot_files=len(expected),
                    pillow=PIL.__version__,test_images_decoded=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image-zip',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    out=args.output.resolve()
    w5.require(out.is_relative_to((ROOT/'outputs').resolve()) and not out.exists(), 'Use new outputs attempt')
    result,snapshot,provenance,additional=review_metadata()
    result['environment']=dict(python=platform.python_version(),platform=platform.platform())
    result['image_package']=check_package(args.image_zip,snapshot,provenance,additional) if args.image_zip else {'status':'NOT RUN'}
    out.mkdir(parents=True,exist_ok=False)
    with (out/'review.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))


if __name__=='__main__':main()
