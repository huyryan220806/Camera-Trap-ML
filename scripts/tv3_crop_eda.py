"""TV3 week-one EDA helpers: metadata box scan and train-only visual sampling.

The box rule is imported from ``prepare_swg.valid_bbox`` (TV1) so that the
notebook never keeps a diverging copy. Sampling only reads the train manifest.
"""
from collections import Counter, defaultdict
import hashlib
from io import BytesIO
import json
from pathlib import Path
import random
import subprocess
import sys
from zipfile import ZipFile

import ijson

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_swg import valid_bbox  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TRAIN_MANIFEST = ROOT / 'data/processed/v1/train.jsonl'
BOX_ZIP = ROOT / 'data/raw/swg_camera_traps.bounding_boxes.with_species.zip'
REPORT_DIR = ROOT / 'reports'
SEED = 42
TARGET_SPECIES = [
    'large_antlered_muntjac', 'annamite_striped_rabbit', 'sambar', 'chinese_serow',
    'common_palm_civet', 'masked_palm_civet', 'silver_pheasant', 'eurasian_wild_pig',
]
GEOMETRY_ERRORS = {'outside_or_nonpositive_bbox', 'nonfinite_bbox', 'invalid_image_size'}


# ---------------------------------------------------------------- metadata scan
def iter_items(fileobj, key):
    """Stream COCO items; use_float=True so decimals are float, not Decimal."""
    yield from ijson.items(fileobj, key + '.item', use_float=True)


def scan_box_annotations(images, annotations):
    """Apply the shared valid_bbox rule to every annotation of the box file."""
    images = {im['id']: im for im in images}
    status = Counter(valid_bbox(ann, images.get(ann.get('image_id')))[1] for ann in annotations)
    corrupt = sum(1 for im in images.values() if im.get('corrupt'))
    return {
        'scope': 'all box annotations in the raw box metadata file',
        'images': len(images),
        'corrupt_images': corrupt,
        'annotations': sum(status.values()),
        'valid_boxes': status.get('valid', 0),
        'missing_bbox_records': status.get('no_bbox', 0),
        'geometry_errors': sum(v for k, v in status.items() if k in GEOMETRY_ERRORS),
        'status_counts': dict(sorted(status.items())),
    }


def scan_box_zip(zip_path=BOX_ZIP):
    with ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.endswith('.json')]
        if len(names) != 1:
            raise ValueError('Expected one JSON member in ' + str(zip_path))
        with z.open(names[0]) as f:
            images = list(iter_items(f, 'images'))
        with z.open(names[0]) as f:
            return scan_box_annotations(images, iter_items(f, 'annotations'))


# ---------------------------------------------------------------- sampling
def load_manifest(path=TRAIN_MANIFEST):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def git_commit_of(path):
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%H', '--', str(path)], cwd=ROOT,
                             capture_output=True, text=True, check=True)
        return out.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def sample_species(records, species, n=10, seed=SEED):
    """Pick up to n train images of one species, round-robin over shuffled locations.

    Only records with split == 'train' and at least one cleaned box are used.
    If fewer than n exist, the real number is returned (never filled from val/test).
    """
    rng = random.Random(f'{seed}:{species}')
    by_loc = defaultdict(list)
    for r in records:
        if r.get('split') == 'train' and r.get('label') == species and r.get('boxes'):
            by_loc[r['location']].append(r)
    locations = sorted(by_loc)
    rng.shuffle(locations)
    for loc in locations:
        by_loc[loc].sort(key=lambda r: r['image_id'])
        rng.shuffle(by_loc[loc])
    picked = []
    while len(picked) < n and any(by_loc[loc] for loc in locations):
        for loc in locations:
            if by_loc[loc] and len(picked) < n:
                picked.append(by_loc[loc].pop())
    return picked


def ids_not_in_train(audit_rows, train_records):
    train_ids = {r['image_id'] for r in train_records if r.get('split') == 'train'}
    return [row['image_id'] for row in audit_rows if row['image_id'] not in train_ids]


# ---------------------------------------------------------------- download / save
def fetch_image(url, timeout=15):
    import requests
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def draw_boxes(img, boxes, ax, linewidth=2, label=True):
    import matplotlib.patches as patches
    ax.imshow(img)
    for b in boxes:
        x, y, w, h = b['bbox_xywh']  # cleaned pixel boxes from the manifest
        ax.add_patch(patches.Rectangle((x, y), w, h, linewidth=linewidth, edgecolor='red', facecolor='none'))
        if label:
            ax.text(x, max(0, y - 8), b['label'], color='red', fontsize=9, backgroundcolor='white')
    ax.axis('off')


def process_species(species, records, out_dir, fetch=fetch_image, seen_hashes=None, n=10, seed=SEED):
    """Download, save raw + bbox images and a grid. Returns (audit_rows, errors, counts)."""
    import matplotlib
    import matplotlib.pyplot as plt
    from PIL import Image, UnidentifiedImageError

    seen_hashes = {} if seen_hashes is None else seen_hashes
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sample = sample_species(records, species, n=n, seed=seed)
    audit, errors = [], []
    counts = Counter(selected=len(sample), saved=0, failed=0)
    fig, axes = plt.subplots(2, 5, figsize=(22, 8))
    axes = axes.flatten()
    for ax in axes:
        ax.axis('off')
    for i, r in enumerate(sample):
        row = {'species': species, 'image_id': r['image_id'], 'split': r['split'],
               'location': r.get('location'), 'sequence_id': r.get('sequence_id') or r.get('seq_id'),
               'url': r['url'], 'n_boxes': len(r['boxes']), 'status': None, 'files': {}}
        audit.append(row)
        try:
            data = fetch(r['url'])
        except Exception as e:  # network / HTTP error
            row['status'] = 'download_failed'
            errors.append({'type': 'download_failed', 'image_id': r['image_id'], 'error': str(e)})
            continue
        digest = hashlib.sha256(data).hexdigest()
        row['sha256'] = digest
        if digest in seen_hashes:
            errors.append({'type': 'duplicate_bytes_in_sample', 'image_id': r['image_id'],
                           'same_as': seen_hashes[digest], 'sha256': digest})
        seen_hashes.setdefault(digest, r['image_id'])
        try:
            img = Image.open(BytesIO(data)).convert('RGB')
        except (UnidentifiedImageError, OSError) as e:
            row['status'] = 'decode_failed'
            errors.append({'type': 'decode_failed', 'image_id': r['image_id'], 'error': str(e)})
            continue
        stem = f'{i + 1:02d}_{r["image_id"][:8]}'
        raw_path = out_dir / f'{stem}_raw.jpg'
        img.save(raw_path)
        f1, a1 = plt.subplots(1, figsize=(8, 6))
        draw_boxes(img, r['boxes'], a1)
        a1.set_title(f'{species} | {r.get("location")}', fontsize=9)
        bbox_path = out_dir / f'{stem}_bbox.jpg'
        f1.savefig(bbox_path, bbox_inches='tight', dpi=100)
        plt.close(f1)
        draw_boxes(img, r['boxes'], axes[i], linewidth=1.5, label=False)
        axes[i].set_title(f'{r.get("location")} | {row["sequence_id"][-4:]}', fontsize=8)
        row['status'] = 'saved'
        row['files'] = {'raw': raw_path.relative_to(ROOT).as_posix(), 'bbox': bbox_path.relative_to(ROOT).as_posix()}
        counts['saved'] += 1
    fig.suptitle(species.replace('_', ' ').title(), fontsize=14, fontweight='bold')
    fig.tight_layout()
    grid_path = out_dir / f'grid_{species}.png'
    fig.savefig(grid_path, bbox_inches='tight', dpi=100)
    plt.close(fig)
    counts['failed'] = counts['selected'] - counts['saved']
    return audit, errors, dict(counts)
