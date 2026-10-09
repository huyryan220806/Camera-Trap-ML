# TV2 W2 review fixes

Review base: `8a48b86c7dfde00beba0fe21aea8394260cf9e56`. Date: 2026-10-09. Branch: `feat/baseline` only.
Acceptance source: `review_TV2_W2_2026-10-09.md`, also available on TV4 handoff branch at `reports/review_TV2_W2_2026-10-09.md`.

## P2 #1 – Run immutability: FIXED

Root cause: `prepare_data()` published manifests before the smoke branch and normal training reused existing run directories.

- Smoke now executes inside `TemporaryDirectory`; all used manifests, errors and temporary checkpoint are discarded on exit. Real source/selected manifests are read only.
- Normal training allows an initial directory containing only selected inputs/download report. Existing config/log/results/checkpoint/used files or other state reject the run before preparation. Exclusive `.training_started` creation blocks concurrent/repeated training. Failed runs also require a new ID; resume is unsupported.
- Preparation CLI also refuses an existing prepared/completed directory, so it cannot overwrite B0_run01 selected manifests or trigger downloads for that historical run.
- Validate both splits before writing either used manifest. Stage and fsync all payloads before `os.replace`; roll back published files on exceptions. Config uses the same atomic file writer.
- Atomic replacement is per file. Group rollback covers Python-visible exceptions; this is not a multi-file filesystem transaction under power loss. An abruptly interrupted new run remains reserved and cannot be mistaken for a resumable/completed run. Existing completed artifacts are never permitted write targets.

Tests cover unchanged bytes/SHA after smoke, missing validation image, smoke error, existing run rejection, prepare error after the train split, injected failure on the second `os.replace`, each existing-run marker, preparation CLI, and a new tiny fixture run that can train/save/verify exactly once. No B0 retraining occurred; the one-epoch test uses synthetic images and an 11-parameter fixture model in a temporary directory.

## P2 #2 – Validation provenance: FIXED

The checkpoint config is the frozen authority. Before loader/model creation, verify source SHA, class-map SHA and both mapping directions, used-validation SHA, exact row membership (including ID/split/label/path/quality), image SHA when frozen metadata exists, and decoding. Hash or membership mismatch raises an error before inference; aggregate metric equality cannot bypass these checks. Training's final checkpoint verification uses this gate too.

Pilot v1 remains compatible. Its checkpoint already contains all three manifest/map hashes. For older metadata missing only the class-map hash, exact bidirectional mapping remains mandatory. Missing source/validation frozen hashes fail closed. No historical metadata was generated or injected into B0_run01.

TV1 v2 schema was read from `origin/codex/tv1-week2-download-quality` at `b9a92b95edcc377aafcbe1efc4161bb7520f2090`. Future rows with `quality.local_path` use that repository-relative path, confined to the configured image root, and require `quality.sha256`. Frozen image bytes are verified before inference. Positive v2 fixture and changed-but-decodable image tests pass. B0_run01 has **64/64 validation images without a frozen image SHA**; historical byte identity is not claimed, and no migration to v2 was performed.

## Execution evidence

Full suite: **52 total, 52 passed, 0 failed** (29 existing + 23 new), 5.369 seconds. Runtime: Python 3.14.3, torch 2.13.0+cpu, torchvision 0.28.0+cpu. Test names, all per-file before/after hashes and real validation output: [W2_review_fix_verification.json](W2_review_fix_verification.json).

Commands from repository root, using the above installed Python interpreter:

```powershell
py -m unittest discover -s tests -v
py scripts/train_b0.py --smoke
py scripts/validate_b0.py --checkpoint experiments/B0_run01/checkpoints/best_model.pth
```

This machine invoked `AppData/Local/Python/pythoncore-3.14-64/python.exe` explicitly and added the existing `data/images/local_deps` to `PYTHONPATH`. TEMP/TMP pointed into ignored `outputs/w2_review_fix/tmp`; `MPLBACKEND=Agg`. Validation used `OMP_NUM_THREADS=4` and `MKL_NUM_THREADS=4`. No environment/version changes were made.

Real smoke: **PASS**, one training batch and validation batch, temporary save/load. Parameter counts remain 11,180,616 total / 4,104 trainable / 11,176,512 frozen.

Real checkpoint: 44,837,567 bytes; actual and review SHA-256 both `d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680`. Provenance and reload **PASS**, epoch 4, 64 validation images:

| Metric | Reloaded | Absolute difference |
|---|---:|---:|
| Macro-F1 | 0.3616866793337382 | 0 |
| Macro-Precision | 0.46773504273504274 | 0 |
| Macro-Recall | 0.375 | 0 |
| Accuracy | 0.375 | 0 |

All **15 files** under B0_run01, including weights, were snapshotted before changes and checked after tests, real smoke and validation. No additions/deletions/byte-size/hash changes. The SHA-256 of the sorted ledger `path<TAB>bytes<TAB>sha256<LF>` is:

- Before: `2a87714ef5c185ec320c877482c85decd5ffad90f4a67de58d6c52d41cfb3c17`
- After: `2a87714ef5c185ec320c877482c85decd5ffad90f4a67de58d6c52d41cfb3c17`
- **B0_run01 BEFORE/AFTER: UNCHANGED**.

## Remaining handoff items

- **Checkpoint shared URL: PENDING USER UPLOAD.** [Handoff document](TV2_W2_CHECKPOINT.md) provides verified hash/size and validation instructions. No URL was fabricated, no weights or dataset images were committed.
- **TV4 cross-review: PENDING.** Checklist read from `origin/codex/tv4-week2-demo-detector` at `f61ca6d3180971c4d7725c7d3cab1046be44134a`; independent demo execution not performed. [Checklist status](TV2_REVIEW_TV4_W2.md).
- **W3 comparison dataset: pending team agreement.** TV1/TV2/TV3 must freeze a common evaluation image list before comparing B0/B1/B2. No B1/B2 implementation or dataset expansion was performed.

Code verification is complete; full checkpoint handoff acceptance remains pending until a real shared URL is supplied.
