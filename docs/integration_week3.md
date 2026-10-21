# Week-three integration - 2026-10-21

User confirmed testing the demo and authorized publishing TV1 W4 and merging W3.

## Scope

- TV1 W4 `4bcf85c` pushed to feat/metadata-split; EXCLUDED from main here.
- TV1 W3 `7e9b194` included through the demo branch ancestry.
- TV4 W3 `254b40e`, TV2 W3 `8a7c99c`, TV3 W3 `7cc87e8` selected.
- Permanent member branches retained; no codex branches or force-push.
- PR #5 covers TV1/TV4 W3, existing PR #4 TV2, existing PR #3 TV3.

## Integration verification

Local main in reused worktree:
`C:/Users/loval/.codex/worktrees/review-tv2-week2/CameraTrapML`.
Root checkout remains feat/demo, running user demo is unaffected.
After publication, restore reused worktree to feat/metadata-split.

Merged TV1/TV4, TV2 and TV3 locally. Conflicts resolved by preserving both
README sections and both shared evaluation/model APIs. Lazy exports avoid
making the metrics-only path depend on torch. Added three integration tests.
No model/dataset/experiment artifact changed to resolve conflicts.

Metadata re-audit PASS: same 4000 parents, no cross-split sequence/location
overlap, provenance d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f.
Environment and six result-contract fixtures PASS. Full suite **263/263 PASS**
(91.062s), including three shared-API regressions. Real MegaDetector plus
B0/B1/B2 using the MERGED code PASS on the same hashed train image: top 3,
identical cold/warm predictions, cache reuse, JSON schema/semantic validation.
No test inference, no training, no changed model/data hashes.

Evidence in `reports/integration_w3/`: tests.txt, comparison.json,
merged_smoke.json, b3_weight_audit.json. Local runner/extra evidence remains
in root `outputs/integration_w3_2026-10-21/`. App and demo code are byte-for-byte
the same as validated TV4 254b40e; only shared package exports needed combining.
TV2/TV3 training modules, logs, configs and checkpoints are preserved.

PR4 marked ready after review. User explicitly authorized integrating W3;
merge commits retain the member histories (no squash or force push).
Publication: push local main only after these checks; verify all selected W3
tips are ancestors of origin/main and W4 4bcf85c is NOT an ancestor. Restore
this temporary integration worktree to feat/metadata-split after publication.

To rerun checks from a prepared main checkout:

```powershell
python -m unittest discover -s tests -v
python scripts/check_environment.py
python scripts/validate_results.py
python scripts/validate_comparison.py --metadata-only
python scripts/verify_tv4_classifier.py --model B0
python scripts/verify_tv4_classifier.py --model B1
python scripts/verify_tv4_classifier.py --model B2
```

Real smoke requires local weights plus train images; see TV4 setup docs.

## B3 caution for week four

The current experiment protocol defines B3 as inverse-frequency class-weighted
CE, all other settings unchanged. comparison_v1 TRAIN has 350 parent images
per class, so N/(C*Nc) = 2800/(8*350) = 1 for every class. B2 already applies
1/n_crops per parent; summed effective sample weights are also 350/class
(up to floating-point rounding). Thus parent-based B3 weights do not change
the loss. This is a train-only audit, not test-based model selection.

Do not assume B3 is stronger just because its number is higher. TV3 should
record weight values before launching a run. If the team wants a different
improvement, agree on one controlled change using train/val, keep the same
frozen parents and compare IMAGE-level validation macro-F1/per-class recall.
Do not use raw crop counts as independent parent frequencies, test examples
to tune, or extend B2 training under the same run ID. B2 remains the fixed
reference (image val F1 0.7455); no B3 result or superiority is claimed here.

Original TV3 train_log.jsonl CRLF and report trailing-whitespace warnings are
inherited. Preserve report/log bytes; do not reformat experiment evidence.
