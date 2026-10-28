"""Freeze auditable W5 metadata candidates without changing any previous split.

Default invocation is restartable. Existing releases are recomputed and verified,
never overwritten. New image bytes and model predictions are not read here.
"""
import argparse
from collections import Counter, defaultdict, deque
import hashlib
import json
import os
from pathlib import Path

from comparison_data import eligible_crops, require, repo_path
from download_subset import ROOT, atomic_json, load_json, read_rows, sha256, utc_now
from split_swg import audit_records
from task_lock import state_lock
from validate_comparison import validate as validate_comparison

DEFAULT_CONFIG = ROOT / 'configs/data_w5_candidates_v1.json'


def stable_key(seed, kind, value):
    return hashlib.sha256(f'{seed}|{kind}|{value}'.encode()).hexdigest()


def validate_identities(rows):
    for row in rows:
        for key in ('image_id', 'file_name', 'seq_id', 'sequence_id', 'location'):
            require(isinstance(row.get(key), str) and row[key].strip(), 'Missing identity: ' + key)
        require(row['split'] in ('train', 'val', 'test'), 'Unknown source split')
        require(row['seq_id'] == row['sequence_id'], 'Sequence aliases disagree')
    audit = audit_records(rows)
    require(audit['metadata_leakage_check_passed'], 'Source identity/split leakage')
    locations = defaultdict(set)
    for row in rows:
        locations[row['seq_id']].add(row['location'])
    require(all(len(v) == 1 for v in locations.values()), 'Sequence spans locations')
    return audit


def diversified_selection(rows, existing_sequences, seed, cap):
    """At most one image from each sequence absent from the baseline train."""
    require(type(cap) is int and cap > 0, 'Invalid additional train cap')
    by_sequence = defaultdict(list)
    for row in rows:
        if row['seq_id'] not in existing_sequences:
            by_sequence[row['seq_id']].append(row)
    locations = defaultdict(list)
    for seq, group in by_sequence.items():
        representative = min(group, key=lambda r: stable_key(seed, 'image', r['image_id']))
        locations[representative['location']].append(representative)
    queues = {
        loc: deque(sorted(group, key=lambda r: stable_key(seed, 'sequence', r['seq_id'])))
        for loc, group in locations.items()
    }
    order = sorted(queues, key=lambda loc: stable_key(seed, 'location', loc))
    selected = []
    while len(selected) < cap:
        added = False
        for loc in order:
            if queues[loc] and len(selected) < cap:
                selected.append(queues[loc].popleft())
                added = True
        if not added:
            break
    return sorted(selected, key=lambda r: r['image_id'])


def counts(rows):
    return {'images': len(rows), 'sequences': len({r['seq_id'] for r in rows}),
            'locations': len({r['location'] for r in rows}),
            'boxes': sum(len(r['boxes']) for r in rows)}


def build_candidates(source, baseline, cmap, geometry_policy, exposure_ids, config):
    source_audit = validate_identities(source)
    validate_identities(baseline)
    parent = {r['image_id']: r for r in source}
    require(set(exposure_ids) <= set(parent), 'Historical exposure has unknown image IDs')
    for row in baseline:
        original = parent.get(row['image_id'])
        require(original is not None and all(row.get(k) == v for k, v in original.items()),
                'Baseline differs from frozen source: ' + row['image_id'])
    baseline_ids = {r['image_id'] for r in baseline}
    baseline_sequences = {r['seq_id'] for r in baseline}
    known_ids = set(exposure_ids) | baseline_ids
    seen_locations = {parent[i]['location'] for i in known_ids}
    pool, holdout, decisions, invalid = [], [], [], []
    for row in sorted(source, key=lambda r: r['image_id']):
        _, issues = eligible_crops(row, cmap, geometry_policy)
        if row['image_id'] in baseline_ids:
            require(not issues, 'A baseline image no longer meets geometry policy')
            decision = 'baseline_retained'
        elif issues:
            decision = 'excluded_geometry_or_label'
            invalid.append({'source': row, 'issues': issues})
        elif row['split'] == 'train':
            decision = 'train_candidate'
            pool.append(row)
        elif row['split'] == 'val':
            decision = 'reserved_validation'
        elif row['location'] in seen_locations:
            decision = 'reserved_test_exposed_location'
        else:
            decision = 'holdout_candidate_unexposed_location'
            holdout.append(row)
        decisions.append({
            'image_id': row['image_id'], 'label': row['label'], 'source_split': row['split'],
            'sequence_id': row['seq_id'], 'location': row['location'], 'decision': decision,
            'reasons': sorted({i['reason'] for i in issues}),
        })
    selected, per_class = [], []
    for label in cmap.values():
        extra = [r for r in pool if r['label'] == label]
        chosen = diversified_selection(extra, baseline_sequences, config['seed'],
                                       config['additional_train_per_class_cap'])
        selected.extend(chosen)
        fresh = [r for r in extra if r['seq_id'] not in baseline_sequences]
        hstats = counts([r for r in holdout if r['label'] == label])
        failures = [k for k in ('images', 'sequences', 'locations')
                    if hstats[k] < config[f'holdout_min_{k}_per_class']]
        per_class.append({
            'label': label,
            'baseline_train': counts([r for r in baseline if r['label'] == label and r['split'] == 'train']),
            'train_pool': counts(extra), 'new_sequence_pool': counts(fresh),
            'selected_additional_train': counts(chosen),
            'proposed_train_images_if_all_pass_quality':
                sum(r['label'] == label and r['split'] == 'train' for r in baseline) + len(chosen),
            'holdout_candidate': hstats, 'holdout_failed_support_checks': failures,
        })
    selected.sort(key=lambda r: r['image_id'])
    selected_ids = {r['image_id'] for r in selected}
    for item in decisions:
        if item['decision'] == 'train_candidate':
            item['selection_state'] = ('selected' if item['image_id'] in selected_ids else
                'baseline_sequence_not_selected' if item['sequence_id'] in baseline_sequences else
                'not_selected_sequence_representative_or_cap')
    require(len({r['seq_id'] for r in selected}) == len(selected), 'Repeated selected sequence')
    require(not ({r['seq_id'] for r in selected} & baseline_sequences), 'Selected baseline sequence')
    require(all(r['split'] == 'train' for r in selected), 'Non-train extension')
    require(all(r['split'] == 'test' and r['location'] not in seen_locations for r in holdout),
            'Holdout location exposure')
    combined = baseline + selected + [{**r, 'split': 'holdout_candidate'} for r in holdout]
    audit = audit_records(combined)
    require(audit['metadata_leakage_check_passed'], 'Combined identity/split leakage')
    support_ok = all(not r['holdout_failed_support_checks'] for r in per_class)
    summary = {
        'dataset_version': config['dataset_version'], 'seed': config['seed'],
        'source': counts(source), 'source_by_split': {s: counts([r for r in source if r['split'] == s]) for s in ('train', 'val', 'test')},
        'baseline': counts(baseline), 'train_pool': counts(pool),
        'selected_additional_train': counts(selected), 'holdout_candidates': counts(holdout),
        'excluded_invalid': counts([r['source'] for r in invalid]),
        'decision_counts': dict(sorted(Counter(r['decision'] for r in decisions).items())),
        'selection_counts': dict(sorted(Counter(r['selection_state'] for r in decisions if 'selection_state' in r).items())),
        'per_class': per_class, 'source_split_changes': 0, 'training_ready': False,
        'new_image_content_checked': False, 'new_image_near_duplicates_checked': False,
        'holdout_support_sufficient': support_ok, 'holdout_ready': False,
        'holdout_status': 'PENDING_QUALITY_AND_EXPOSURE_REVIEW' if support_ok else 'NOT_READY_INSUFFICIENT_SUPPORT',
        'recommended_evaluation': 'Keep comparison_v1 validation for development; preserve published B2 Test. No new independent 8-class claim from this candidate pool.',
        'support_floor': {k: config[f'holdout_min_{k}_per_class'] for k in ('images', 'sequences', 'locations')},
        'scope': config['scope'],
    }
    audit.update(source_audit=source_audit, protected_baseline_unchanged=True,
                 source_split_changes=0, historical_exposure_unique_images=len(known_ids),
                 historical_exposure_locations=len(seen_locations),
                 selected_vs_baseline_sequence_overlap=0,
                 holdout_vs_historical_location_overlap=0,
                 content_audit_scope='Existing comparison_v1 evidence only; new candidate image bytes not checked')
    return {
        'decisions.jsonl': decisions, 'train_extension_candidates.jsonl': selected,
        'holdout_candidates.jsonl': holdout, 'excluded_invalid.jsonl': invalid,
        'summary.json': summary, 'audit.json': audit, 'class_map.json': cmap,
        'policy.json': config,
    }


def inputs(config_path):
    config = load_json(config_path)
    require(config['dataset_version'] == 'w5_candidates_v1', 'Use a separately reviewed builder for another version')
    require(config['source_manifest'] == 'data/processed/v1/manifest_v1.jsonl', 'Unexpected source')
    require(config['comparison_dir'] == 'data/processed/comparison_v1', 'Unexpected baseline')
    require(config['selection'] == 'one_image_per_new_sequence_then_round_robin_locations_sha256_seeded', 'Unsupported selection')
    require(config['holdout_source_split'] == 'test', 'Only original test locations may be holdout candidates')
    require(type(config['seed']) is int, 'Invalid seed')
    for k in ('images', 'sequences', 'locations'):
        require(type(config[f'holdout_min_{k}_per_class']) is int and config[f'holdout_min_{k}_per_class'] > 0, 'Invalid support floor')
    validate_comparison(ROOT / config['comparison_dir'], check_images=False)
    v1 = ROOT / 'data/processed/v1'
    original = load_json(v1 / 'provenance.json')
    require(sha256(v1 / 'manifest_v1.jsonl') == original['manifest_sha256'], 'Frozen v1 changed')
    require(sha256(v1 / 'pilot_v1.jsonl') == original['pilot_sha256'], 'Frozen pilot changed')
    source = read_rows(ROOT / config['source_manifest'])
    parent = {r['image_id']: r for r in source}
    cmap = load_json(ROOT / config['comparison_dir'] / 'class_map.json')
    require(cmap == load_json(v1 / 'class_map.json'), 'Class maps differ')
    location_map = load_json(v1 / 'location_split.json')
    require(all(location_map.get(r['location']) == r['split'] for r in source), 'Source/location map mismatch')
    history = set()
    for pattern in config['historical_exposure_globs']:
        matches = {p for p in ROOT.glob(pattern) if p.is_file()}
        require(bool(matches), 'Missing historical exposure evidence: ' + pattern)
        history |= matches
    exposure_ids, history_summary = set(), []
    for p in sorted(history):
        rows = read_rows(p)
        ids = {r['image_id'] for r in rows}
        require(ids <= set(parent), 'Unknown exposure IDs in ' + str(p))
        require(all(r.get('split') == parent[r['image_id']]['split'] for r in rows), 'Historical source split mismatch')
        exposure_ids |= ids
        history_summary.append({'path': p.relative_to(ROOT).as_posix(), 'rows': len(rows), 'unique_images': len(ids)})
    protected = set(history) | {config_path.resolve(), ROOT / 'configs/comparison_v1.json'}
    for directory in (v1, ROOT / 'data/processed/v2', ROOT / config['comparison_dir']):
        protected |= {p for p in directory.rglob('*') if p.is_file()}
    fingerprint = {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(protected)}
    baseline = read_rows(ROOT / config['comparison_dir'] / 'manifest.jsonl')
    objects = build_candidates(source, baseline, cmap, load_json(ROOT / 'configs/comparison_v1.json'), exposure_ids, config)
    objects['historical_exposure.json'] = {'sources': history_summary, 'scope': 'Conservative evidence from available B0/crop manifests, including attempted downloads; plus all baseline locations. Not a guarantee about unrecorded experiments or foundation-model pretraining.'}
    objects['baseline_references.json'] = {
        'dataset_version': 'comparison_v1', 'training_release': 'Use existing baseline for the first DINO experiment',
        'manifest': 'data/processed/comparison_v1/manifest.jsonl',
        'b2_train': 'data/processed/comparison_v1/b2/train.jsonl',
        'b2_val': 'data/processed/comparison_v1/b2/val.jsonl',
        'class_map': 'data/processed/comparison_v1/class_map.json',
        'provenance_sha256': sha256(ROOT / config['comparison_dir'] / 'provenance.json'),
        'counts': {'train_images': sum(r['split'] == 'train' for r in baseline), 'val_images': sum(r['split'] == 'val' for r in baseline), 'old_test_images': sum(r['split'] == 'test' for r in baseline)},
        'old_test_policy': 'Published B2 result only; do not use to tune new models',
    }
    return config, objects, fingerprint


def encoded(objects):
    result = {}
    for name, value in objects.items():
        if name.endswith('.jsonl'):
            text = ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n' for r in value)
        else:
            text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        result[name] = text.encode('utf-8')
    return result


def verify_files(folder, files):
    require({p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()} == set(files), 'Release file set changed')
    for name, content in files.items():
        require((folder / name).read_bytes() == content, 'Release modified: ' + name)


def write_bytes(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('wb') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def publish(folder, staging, files, verify_only=False):
    if folder.exists():
        verify_files(folder, files)
        return 'verified_existing'
    require(not verify_only, 'Release not built yet')
    staging.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        p = staging / name
        if p.exists():
            require(p.read_bytes() == content, 'Staging changed; preserve and inspect: ' + name)
        else:
            write_bytes(p, content)
    # Only this writer's interrupted temporary files can remain in staging.
    extras = {p.name for p in staging.iterdir()} - set(files)
    require(not extras, 'Unexpected staging files: ' + str(sorted(extras)))
    verify_files(staging, files)
    folder.parent.mkdir(parents=True, exist_ok=True)
    staging.rename(folder)
    return 'published'


def run(config_path=DEFAULT_CONFIG, verify_only=False, report=None):
    config_path = Path(config_path).resolve()
    initial = load_json(config_path)
    require(initial['output_dir'] == 'data/processed/w5_candidates_v1', 'Unsafe output directory')
    require(initial['state_dir'] == 'data/interim/w5_candidates_v1', 'Unsafe state directory')
    state, output = repo_path(initial['state_dir']), repo_path(initial['output_dir'])
    report = Path(report) if report else ROOT / 'outputs/tv1_w5/verification.json'
    require(report.resolve().is_relative_to(ROOT / 'outputs'), 'Runtime report must be under outputs/')
    with state_lock(state):
        print('Verifying frozen sources and historical exposure...', flush=True)
        config, objects, fingerprint = inputs(config_path)
        files = encoded(objects)
        provenance = {
            'dataset_version': config['dataset_version'], 'schema_version': 1,
            'source_files_sha256': fingerprint,
            'builder_sha256': {p.name: sha256(p) for p in [Path(__file__), ROOT / 'scripts/comparison_data.py', ROOT / 'scripts/split_swg.py']},
            'files_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
            'training_ready': False, 'holdout_ready': False,
        }
        files.update(encoded({'provenance.json': provenance}))
        receipt = state / 'source_receipt.json'
        if receipt.exists():
            require(load_json(receipt) == provenance, 'Inputs/builder changed since work started; preserve this version')
        elif not verify_only:
            atomic_json(receipt, provenance)
        require(all(sha256(ROOT / p) == digest for p, digest in fingerprint.items()), 'Input changed during inventory')
        action = publish(output, state / 'staging', files, verify_only)
        result = {'passed': True, 'checked_utc': utc_now(), 'action': action,
                  'dataset_version': config['dataset_version'], 'source_files_unchanged': True,
                  'release_sha256': sha256(output / 'provenance.json'),
                  'source_images': objects['summary.json']['source']['images'],
                  'additional_train_candidates': objects['summary.json']['selected_additional_train']['images'],
                  'holdout_status': objects['summary.json']['holdout_status'],
                  'new_images_downloaded': 0, 'model_inference_run': False, 'source_split_changes': 0}
        atomic_json(report, result)
        if not verify_only:
            atomic_json(state / 'task_state.json', result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.config, args.verify_only, args.report), indent=2))


if __name__ == '__main__':
    main()
