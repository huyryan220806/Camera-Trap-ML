"""Provenance, TV2 approval and cumulative GPU accounting for W6 commands."""
from __future__ import annotations

from contextlib import contextmanager
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import uuid

import torch

from . import dino_probe as w5
from . import dino_w6 as w6

SOURCE_FILES = (
    'src/__init__.py', 'src/training/__init__.py', 'src/evaluation/__init__.py',
    'src/training/dino_probe.py', 'src/training/dino_handoff.py',
    'src/training/dino_w6.py', 'src/training/dino_w6_control.py',
    'src/training/dino_w6_delivery.py', 'scripts/dino_w6.py',
    'src/evaluation/w5_validation.py', 'src/evaluation/w6_validation.py',
    'contracts/w6_registry.schema.json',
)


def tv2():
    try:
        from src.evaluation import w6_validation
    except ImportError as exc:
        raise ValueError('Merge TV2 W6 source first; see docs/handoff_tv3_w6.md') from exc
    return w6_validation


def committed_file(path, commit, root=w5.ROOT):
    relative = Path(path).resolve().relative_to(root.resolve()).as_posix()
    expected = subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=root)
    w5.require(w5.sha(path) == hashlib.sha256(expected).hexdigest(), 'Uncommitted/changed file: ' + relative)


def source_index(commit=None, root=w5.ROOT):
    commit = commit or w5.git_revision(root)
    result = dict(commit=commit, files_sha256={})
    for relative in SOURCE_FILES:
        path = root / relative
        committed_file(path, commit, root)
        result['files_sha256'][relative] = w5.sha(path)
    return result


def settings_digest(c):
    c = copy.deepcopy(c)
    c.pop('smoke_evidence', None)
    c['status'] = 'DRAFT'
    c['runtime'].update(source_sha=None, runtime_lock=None)
    return w6.digest(c)


def approved_gate(c, config_path, registry_path, runtime, root=w5.ROOT):
    v = tv2()
    registry = w5.read_json(registry_path)
    v.validate_registry(registry, root)
    run = next(r for r in registry['runs'] if r['run_id'] == c['run_id'])
    v.official_gate(registry, run)
    w5.require(c['status'] == 'FROZEN' and w6.digest(c) == run['config_sha256'] and
               c['recipe'] == run['recipe'] and c['runtime']['source_sha'] == run['source_sha'], 'Config not frozen to registry')
    w5.require(Path(config_path).resolve() == (root / run['config_path']).resolve(), 'Use registered config file')
    w5.require(w6.digest(runtime) == c['runtime']['runtime_lock'], 'Runtime changed: stop and report to TV2')
    # Freeze/approval must exist in committed Git history before official validation.
    head = w5.git_revision(root)
    committed_file(config_path, head, root)
    committed_file(registry_path, head, root)
    sources = source_index(run['source_sha'], root)
    evidence = c['smoke_evidence']
    path = v.confined(root, evidence['path'])
    committed_file(path, head, root)
    w5.require(w5.sha(path) == evidence['sha256'], 'Smoke evidence changed')
    smoke = w5.read_json(path)
    w5.require(smoke['status'] == 'PASS' and smoke['official_training'] is False and smoke['validation_inference'] is False and
               smoke['settings_sha256'] == settings_digest(c) and smoke['source_index'] == sources and
               smoke['runtime'] == runtime, 'Smoke/config/source/runtime binding mismatch')
    usage = load_usage(root)
    usage_totals(usage)
    known = {s['attempt_id'] for s in usage['sessions']}
    registered = {p['attempt_id'] for p in registry['tv3_preparation_attempts']}
    registered.update(a['attempt_id'] for r in registry['runs'] for a in r['attempts'])
    w5.require(registered <= known, 'Missing GPU history; restore usage.json before changing execution machine')
    # Approvals are peer evidence, not signatures inferred by this program.
    return registry, run, sources


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class BudgetExceeded(RuntimeError):
    pass


def load_usage(root=w5.ROOT):
    path = root / 'outputs/tv3_w6/usage.json'
    return w5.read_json(path) if path.exists() else dict(version=1, sessions=[], reconciliations=[])


def effective_seconds(usage, session):
    if session['seconds'] is not None:
        return session['seconds']
    matches = [r for r in usage['reconciliations'] if r['session_id'] == session['session_id']]
    w5.require(len(matches) == 1, 'Unmeasured interrupted GPU session: settle with reviewed accounting receipt first')
    return matches[0]['seconds']


def usage_totals(usage):
    sessions = usage['sessions']
    seconds = [effective_seconds(usage, s) for s in sessions]
    w5.require(all(type(x) in (int, float) and math.isfinite(x) and x >= 0 for x in seconds), 'Invalid GPU accounting')
    total = sum(seconds)
    attempts = {s['attempt_id'] for s in sessions if s['kind'] != 'train_only_smoke'}
    by_attempt = {a: sum(effective_seconds(usage, s) for s in sessions if s['attempt_id'] == a) for a in attempts}
    w5.require(len(attempts) <= 6 and total <= 12 * 3600 and all(x <= 7200 for x in by_attempt.values()),
               'Recorded budget exceeded; stop and report, never trim recorded time')
    return total, by_attempt


@contextmanager
def gpu_session(attempt_id, run_id, kind, booking, resume=False, root=w5.ROOT):
    """One shared lock, real wall time including extraction; failures keep their slot.

    Each GPU operation calls tick. The 60-second reserve allows a batch and
    checkpoint finalization; an actual overrun is reported, never capped in logs.
    Hard kills leave unknown usage, blocking further work until reviewed settlement.
    """
    w5.require(booking and booking.strip(), 'Record an actual GPU booking/device/time agreement')
    folder = root / 'outputs/tv3_w6'
    with w5.writer_lock(folder / 'gpu_lock'):
        usage = load_usage(root)
        total, attempts = usage_totals(usage)
        previous = [s for s in usage['sessions'] if s['attempt_id'] == attempt_id]
        if kind == 'train_only_smoke':
            w5.require(not previous and not resume, 'Smoke attempt ID already used')
            allowance = min(600, 43200 - total)
        else:
            w5.require(all(s['run_id'] == run_id for s in previous), 'Attempt ID belongs to another run')
            if resume:
                w5.require(previous and any(s['kind'] == 'official' for s in previous), 'No official attempt to resume/reload')
            else:
                w5.require(not previous and len(attempts) < 6, 'Duplicate attempt or six-attempt limit')
            allowance = min(7200 - attempts.get(attempt_id, 0), 43200 - total)
        w5.require(allowance > 60, 'No GPU budget left')
        session = dict(session_id=uuid.uuid4().hex, attempt_id=attempt_id, run_id=run_id, kind=kind,
                       started_utc=utcnow(), ended_utc=None, seconds=None, heartbeat_seconds=0,
                       pid=os.getpid(), booking=booking, status='RUNNING')
        usage['sessions'].append(session)
        path = folder / 'usage.json'
        w5.atomic_json(path, usage)
        started = time.perf_counter()
        last_heartbeat = 0.0

        def tick():
            nonlocal last_heartbeat
            elapsed = time.perf_counter() - started
            if elapsed - last_heartbeat >= 5:
                session['heartbeat_seconds'] = elapsed
                w5.atomic_json(path, usage)
                last_heartbeat = elapsed
            if elapsed >= allowance - 60:
                raise BudgetExceeded('GPU budget reached; keep this attempt and last checkpoint')

        try:
            yield tick, session
            if time.perf_counter() - started > allowance:
                raise BudgetExceeded('Actual GPU session exceeded budget; retain measured overrun and report')
            session['status'] = 'COMPLETED'
        except BaseException as exc:
            session['status'] = ('OOM' if isinstance(exc, torch.cuda.OutOfMemoryError) else
                                 'STOPPED' if isinstance(exc, (KeyboardInterrupt, BudgetExceeded)) else 'FAILED')
            session['error'] = repr(exc)
            raise
        finally:
            session['seconds'] = time.perf_counter() - started
            session['ended_utc'] = utcnow()
            w5.atomic_json(path, usage)
            # Deliberately retain elapsed > limits; no false compliant receipt.


def reconcile_usage(receipt_path, root=w5.ROOT):
    receipt = w5.read_json(receipt_path)
    with w5.writer_lock(root / 'outputs/tv3_w6/gpu_lock'):
        usage = load_usage(root)
        item = next(s for s in usage['sessions'] if s['session_id'] == receipt['session_id'])
        w5.require(item['seconds'] is None and not any(r['session_id'] == item['session_id'] for r in usage['reconciliations']),
                   'Session already measured/settled')
        w5.require(receipt.get('status') == 'REVIEWED' and receipt.get('reviewers', {}).get('TV2') and
                   receipt.get('reviewers', {}).get('TV3') and receipt.get('evidence') and
                   receipt.get('process_confirmed_stopped') is True, 'Need actual reviewed accounting and stopped-process evidence')
        seconds = receipt['elapsed_seconds']
        w5.require(type(seconds) in (float, int) and math.isfinite(seconds) and
                   seconds >= item['heartbeat_seconds'], 'Cannot erase measured GPU usage')
        usage['reconciliations'].append(dict(session_id=item['session_id'], seconds=seconds,
                                             receipt_sha256=w5.sha(receipt_path), receipt=receipt, recorded_utc=utcnow()))
        w5.atomic_json(root / 'outputs/tv3_w6/usage.json', usage)
    return usage_totals(usage)


def registry_with_usage(registry, root=w5.ROOT):
    """Merge producer facts into a COPY; never write approval or overwrite TV2 registry."""
    result = copy.deepcopy(registry)
    usage = load_usage(root)
    usage_totals(usage)
    for session in usage['sessions']:
        if session['kind'] != 'train_only_smoke':
            continue
        entry = dict(attempt_id=session['attempt_id'], kind='train_only_smoke',
                     gpu_hours=effective_seconds(usage, session) / 3600,
                     evidence_path=f"outputs/tv3_w6/smoke/{session['attempt_id']}/receipt.json")
        matches = [p for p in result['tv3_preparation_attempts'] if p['attempt_id'] == entry['attempt_id']]
        if matches:
            w5.require(matches == [entry], 'Preparation accounting conflicts with registry')
        else:
            result['tv3_preparation_attempts'].append(entry)
    attempt_ids = {s['attempt_id'] for s in usage['sessions'] if s['kind'] != 'train_only_smoke'}
    for aid in sorted(attempt_ids):
        sessions = [s for s in usage['sessions'] if s['attempt_id'] == aid]
        run = next(r for r in result['runs'] if r['run_id'] == sessions[0]['run_id'])
        folder = root / 'outputs/tv3_w6/runs' / aid
        status = w5.read_json(folder / 'status.json') if (folder / 'status.json').exists() else {'status': sessions[-1]['status']}
        actual = status['status']
        entry = dict(attempt_id=aid, status=actual, gpu_hours=sum(effective_seconds(usage, s) for s in sessions) / 3600,
                     evidence_path=folder.relative_to(root).as_posix() + '/status.json')
        run['attempts'] = [a for a in run['attempts'] if a['attempt_id'] != aid] + [entry]
        run.update(status=actual, checkpoint_sha256=None, metrics=None)
        if actual == 'COMPLETED':
            h = w5.read_json(folder / 'handoff.json')
            run.update(checkpoint_sha256=h['checkpoint_sha256'],
                       metrics={k: h['validation_metrics'][k] for k in ('accuracy', 'macro_f1')},
                       evidence_paths=[folder.relative_to(root).as_posix() + '/handoff.json'])
    return result
