"""Stream SWG metadata into SQLite and produce auditable class statistics."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sqlite3
from zipfile import ZipFile

import ijson

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
DB = ROOT / 'data/interim/swg.sqlite'
REPORT = ROOT / 'reports/eda'


def items(archive, key):
    with ZipFile(RAW / archive) as z:
        names = [n for n in z.namelist() if n.endswith('.json')]
        if len(names) != 1:
            raise ValueError('Expected one JSON member')
        with z.open(names[0]) as f:
            yield from ijson.items(f, key + '.item', use_float=True)


def normalize(name):
    return re.sub(r'[\s_]+', '_', name.strip().lower())


def label_policy(name):
    if name in {'vehicle', 'domestic_dog'}:
        return 'exclude_outside_wildlife_scope'
    if name in {'empty', 'ignore', 'problem', 'blurred', 'human'}:
        return 'exclude_quality_empty_or_human'
    if name.startswith('unidentified') or name in {'insect', 'invertebrate'}:
        return 'exclude_unresolved_taxonomy'
    if name.endswith('_group') or name.endswith('_sp') or '_or_' in name or name in {
        'pangolin', 'ferret_badger', 'chevrotain', 'macaque_not_stump_tailed',
        'flying_squirrel', 'bamboo_rat', 'gibbon', 'forktail_sp', 'laughingthrush'
    }:
        return 'review_taxonomy'
    return 'candidate'


def valid_bbox(ann, image):
    if not image:
        return None, 'missing_image'
    if ann.get('sequence_level_annotation'):
        return None, 'sequence_level_box'
    if 'bbox' in ann and 'bbox_relative' in ann:
        return None, 'ambiguous_coordinate_system'
    box = ann.get('bbox', ann.get('bbox_relative'))
    if not isinstance(box, list) or len(box) != 4:
        return None, 'no_bbox'
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in box):
        return None, 'nonfinite_bbox'
    w, h = image.get('width', 0), image.get('height', 0)
    if w <= 0 or h <= 0:
        return None, 'invalid_image_size'
    x, y, bw, bh = box
    if 'bbox_relative' in ann:
        x, y, bw, bh = x*w, y*h, bw*w, bh*h
    if min(x, y) < 0 or x >= w or y >= h or min(bw, bh) <= 0 or x+bw > w+1 or y+bh > h+1:
        return None, 'outside_or_nonpositive_bbox'
    return [x, y, min(bw, w-x), min(bh, h-y)], 'valid'


def bulk(conn, sql, rows, label):
    batch = []
    count = 0
    for row in rows:
        batch.append(row)
        if len(batch) == 20000:
            conn.executemany(sql, batch); conn.commit()
            count += len(batch); batch = []
            if count % 200000 == 0:
                print(f'{label}: {count:,}', flush=True)
    conn.executemany(sql, batch); conn.commit()
    print(f'{label}: {count+len(batch):,}', flush=True)


def ingest():
    if DB.exists():
        raise SystemExit(f'Database already exists: {DB}. Use --stats to reuse it.')
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.executescript('''
      PRAGMA journal_mode=WAL;
      CREATE TABLE categories(id INTEGER PRIMARY KEY, raw_name TEXT, name TEXT, policy TEXT);
      CREATE TABLE images(id TEXT PRIMARY KEY, file_name TEXT, seq_id TEXT, location TEXT,
        country TEXT, datetime TEXT, width INTEGER, height INTEGER, corrupt INTEGER, is_public INTEGER);
      CREATE TABLE annotations(id TEXT PRIMARY KEY, image_id TEXT, category_id INTEGER, sequence_level INTEGER);
      CREATE TABLE boxes(id TEXT PRIMARY KEY, image_id TEXT, category_name TEXT, bbox TEXT, status TEXT);
      CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT);
    ''')
    main = 'swg_camera_traps.zip'
    cats = list(items(main, 'categories'))
    conn.executemany('INSERT INTO categories VALUES(?,?,?,?)', [(c['id'], c['name'], normalize(c['name']), label_policy(normalize(c['name']))) for c in cats])
    def image_rows():
        for im in items(main, 'images'):
            parts = im['file_name'].split('/')
            yield (im['id'], im['file_name'], im.get('seq_id'), im.get('location'), parts[1] if len(parts)>1 else None,
                   im.get('datetime'), im.get('width'), im.get('height'), int(bool(im.get('corrupt', False))), int(parts[0]=='public'))
    bulk(conn, 'INSERT INTO images VALUES(?,?,?,?,?,?,?,?,?,?)', image_rows(), 'images')
    def ann_rows():
        for a in items(main, 'annotations'):
            yield (a['id'], a['image_id'], a['category_id'], int(bool(a.get('sequence_level_annotation', False))))
    bulk(conn, 'INSERT INTO annotations VALUES(?,?,?,?)', ann_rows(), 'annotations')
    bfile = 'swg_camera_traps.bounding_boxes.with_species.zip'
    bimages = {im['id']: im for im in items(bfile, 'images')}
    bcats = {c['id']: normalize(c['name']) for c in items(bfile, 'categories')}
    status_counts = Counter()
    def box_rows():
        for a in items(bfile, 'annotations'):
            box, status = valid_bbox(a, bimages.get(a['image_id']))
            name = bcats.get(a['category_id'])
            if name is None:
                status = 'unknown_category'
            status_counts[status] += 1
            yield (a['id'], a['image_id'], name, json.dumps(box) if box else None, status)
    bulk(conn, 'INSERT INTO boxes VALUES(?,?,?,?,?)', box_rows(), 'box_annotations')
    mismatch = 0
    missing = 0
    for image_id, im in bimages.items():
        row = conn.execute('SELECT file_name,seq_id,location,width,height FROM images WHERE id=?',(image_id,)).fetchone()
        if row is None:
            missing += 1
        elif tuple(row) != tuple(im.get(k) for k in ['file_name','seq_id','location','width','height']):
            mismatch += 1
    conn.executemany('INSERT INTO metadata VALUES(?,?)', [
        ('box_source_images',json.dumps(len(bimages))),('box_validation',json.dumps(status_counts)),
        ('box_image_metadata_mismatches',json.dumps(mismatch)),('box_images_missing_main',json.dumps(missing))])
    print('Creating indexes and eligible-image view', flush=True)
    conn.executescript('''
      CREATE INDEX ann_image ON annotations(image_id);
      CREATE INDEX ann_cat ON annotations(category_id);
      CREATE INDEX image_sequence ON images(seq_id);
      CREATE INDEX image_location ON images(location);
      CREATE INDEX box_image ON boxes(image_id);
      CREATE INDEX box_class ON boxes(category_name);
      CREATE INDEX box_image_class_status ON boxes(image_id,category_name,status);
      CREATE TABLE image_labels AS
        SELECT a.image_id, COUNT(DISTINCT c.name) AS nlabels, MIN(c.name) AS label,
          MAX(a.sequence_level) AS sequence_level
        FROM annotations a JOIN categories c ON c.id=a.category_id GROUP BY a.image_id;
      CREATE UNIQUE INDEX label_image ON image_labels(image_id);
      CREATE VIEW eligible AS SELECT i.*,l.label,l.sequence_level
        FROM images i JOIN image_labels l ON i.id=l.image_id
        WHERE i.is_public=1 AND i.corrupt=0 AND i.seq_id IS NOT NULL AND i.seq_id!=''
          AND i.location IS NOT NULL AND i.location!='' AND i.width>0 AND i.height>0
          AND l.nlabels=1 AND l.label IN (SELECT name FROM categories WHERE policy='candidate');
      CREATE VIEW boxed_eligible AS SELECT e.* FROM eligible e
        WHERE EXISTS(SELECT 1 FROM boxes b WHERE b.image_id=e.id AND b.status='valid' AND b.category_name=e.label)
        AND NOT EXISTS(SELECT 1 FROM boxes b WHERE b.image_id=e.id AND (b.status!='valid' OR b.category_name!=e.label));
      INSERT INTO metadata VALUES('ingest_complete','true');
    ''')
    conn.commit(); conn.close()


def stats():
    REPORT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    assert conn.execute("SELECT value FROM metadata WHERE key='ingest_complete'").fetchone(), 'Incomplete ingest'
    conn.execute('PRAGMA cache_size=-131072')
    conn.execute('CREATE INDEX IF NOT EXISTS box_image_class_status ON boxes(image_id,category_name,status)')
    for row in conn.execute('SELECT id,name FROM categories').fetchall():
        conn.execute('UPDATE categories SET policy=? WHERE id=?', (label_policy(row['name']), row['id']))
    conn.commit()
    def scalar(q): return conn.execute(q).fetchone()[0]
    summary = {k:scalar(q) for k,q in {
        'images_metadata':'SELECT COUNT(*) FROM images',
        'sequences_metadata':'SELECT COUNT(DISTINCT seq_id) FROM images',
        'locations_metadata':'SELECT COUNT(DISTINCT location) FROM images',
        'categories_raw':'SELECT COUNT(*) FROM categories',
        'categories_normalized':'SELECT COUNT(DISTINCT name) FROM categories',
        'annotations':'SELECT COUNT(*) FROM annotations',
        'public_images':'SELECT COUNT(*) FROM images WHERE is_public=1',
        'private_images':'SELECT COUNT(*) FROM images WHERE is_public=0',
        'corrupt_images':'SELECT COUNT(*) FROM images WHERE corrupt=1',
        'public_usable_candidate_images':'SELECT COUNT(*) FROM eligible',
        'public_usable_boxed_candidate_images':'SELECT COUNT(*) FROM boxed_eligible',
        'box_annotations':'SELECT COUNT(*) FROM boxes',
        'valid_boxes':'SELECT COUNT(*) FROM boxes WHERE status="valid"',
        'valid_box_images':'SELECT COUNT(DISTINCT image_id) FROM boxes WHERE status="valid"',
        'duplicate_file_paths':'SELECT COUNT(*) FROM (SELECT file_name FROM images GROUP BY file_name HAVING COUNT(*)>1)',
        'sequences_spanning_locations':'SELECT COUNT(*) FROM (SELECT seq_id FROM images GROUP BY seq_id HAVING COUNT(DISTINCT location)>1)',
        'annotations_missing_image':'SELECT COUNT(*) FROM annotations a LEFT JOIN images i ON i.id=a.image_id WHERE i.id IS NULL',
        'annotations_unknown_category':'SELECT COUNT(*) FROM annotations a LEFT JOIN categories c ON c.id=a.category_id WHERE c.id IS NULL',
        'images_without_label':'SELECT COUNT(*) FROM images i LEFT JOIN image_labels l ON l.image_id=i.id WHERE l.image_id IS NULL',
        'multi_label_images':'SELECT COUNT(*) FROM image_labels WHERE nlabels>1',
        'sequence_level_annotations':'SELECT COUNT(*) FROM annotations WHERE sequence_level=1',
    }.items()}
    summary.update({r['key']:json.loads(r['value']) for r in conn.execute('SELECT * FROM metadata')})
    summary['country_counts'] = [dict(r) for r in conn.execute('SELECT country,is_public,COUNT(*) images,COUNT(DISTINCT location) locations FROM images GROUP BY country,is_public')]
    summary['year_counts'] = [dict(r) for r in conn.execute('SELECT substr(datetime,1,4) year,COUNT(*) images FROM images GROUP BY year')]
    classes = [dict(r) for r in conn.execute('''SELECT c.name,c.policy,GROUP_CONCAT(DISTINCT c.raw_name) raw_names,
       COUNT(DISTINCT i.id) images, COUNT(DISTINCT i.seq_id) sequences,COUNT(DISTINCT i.location) locations,
       COUNT(DISTINCT CASE WHEN i.is_public=1 THEN i.id END) public_images
       FROM categories c LEFT JOIN annotations a ON c.id=a.category_id LEFT JOIN images i ON i.id=a.image_id
       GROUP BY c.name ORDER BY images DESC''')]
    for source,prefix in [('eligible','eligible'),('boxed_eligible','boxed')]:
        counts={r['label']:dict(r) for r in conn.execute(f'SELECT label,COUNT(*) images,COUNT(DISTINCT seq_id) sequences,COUNT(DISTINCT location) locations FROM {source} GROUP BY label')}
        for c in classes:
            for metric in ['images','sequences','locations']:
                c[f'{prefix}_{metric}']=counts.get(c['name'],{}).get(metric,0)
    boxes={r['category_name']:r['n'] for r in conn.execute('SELECT category_name,COUNT(*) n FROM boxes WHERE status="valid" GROUP BY category_name')}
    for c in classes: c['valid_boxes_all_scopes']=boxes.get(c['name'],0)
    for name,obj in [('summary.json',summary),('class_statistics.json',classes)]:
        (REPORT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)
    print('TOP BOXED CLASSES',json.dumps([(c['name'],c['boxed_images'],c['boxed_sequences'],c['boxed_locations']) for c in classes if c['boxed_images']>0],indent=2),flush=True)
    conn.close()


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--stats',action='store_true'); args=p.parse_args()
    if not args.stats: ingest()
    stats()
