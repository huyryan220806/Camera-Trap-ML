# TV2 W5 progress — 28–29/10/2026

Scope: W5 only (28/10–03/11 proposed schedule, not an official deadline).
Branch: `feat/baseline`. Initial HEAD: `5fe9083367a78de8bf3ed652a6b58eb26a171e47`.
Fetched and fast-forwarded to `60516f5` (also `origin/main`); no merge conflict.
Four pre-existing untracked user documents are preserved and excluded from staging.
No AGENTS.md found in the repository inventory. PR #7 merged; PR #8 open at
`fef2511b571b23be3d4e2cf6c1ccedd659097b6f` (GitHub API checked this session).

| Task | State | Input / next action | Evidence |
| --- | --- | --- | --- |
| W5-01 | VERIFIED DATA / DRAFT PROTOCOL | comparison_v1 hashes/3400 Train-Val rasters PASS; TV1 W5 verify-only PASS at9abc9c5; approval pending TV3/TV1 | reports/tv2/W5_PROTOCOL.md; w5_evidence/attempt_01/comparison.json,candidates.json,train_val_pixels.json |
| W5-02 | B2 PASS / DINO BLOCKED | B2_W5_reference_attempt01, SHA8787ffaf…2127e5, val600images/680crops; accuracy.7466666667,macro-F1.7454765175; no DINO handoff | w5_evidence/attempt_01/validation_02/b2_predictions.jsonl,b2_metrics.json,experiment_comparison.json |
| W5-03 | API PASS / BROWSER BLOCKED | Exact PR8 fef2511;15API assertions and44unit tests PASS; responsive/click/export not observed; no screenshots | TV2_W5_TV4_REVIEW.md; w5_evidence/attempt_01/ui_api_03 |
| W5-04 | B2 RELOAD PASS / DINO BLOCKED | Fresh-process B2, strict load/class map/preprocess, all680crop native/adapter max logit delta0; original training provenance incomplete | w5_evidence/attempt_01/b2_validation/verification.json |
| W5-05 | REPORTS / TESTS COMPLETE; REVIEW PENDING |409testsPASS/0FAIL/0SKIP,32newW5tests; environment/contractsPASS; report/chapter/handoff produced | TV2_W5.md; W5_EXPERIMENT_CHAPTER.md; w5_evidence/attempt_01/checks_summary.json |

Executed: `git status --short --branch`, `git remote -v`, `git fetch origin`,
`git branch -avv`, `git log -5 --oneline`, `git merge --ff-only origin/feat/baseline`.
The first sandboxed fetch could not write FETCH_HEAD; authorized retry succeeded.
No training or Test inference has been started. W4 results remain historical.
W5 seed/budget/tie approval is pending TV3; no official candidate run is authorized
by this progress file. Continue with independent CPU/data/software verification.

## Execution ledger

All commands used the existing Python3.12.14 venv
`outputs/w2_final_handoff/tv4_env/Scripts/python.exe`; root `.venv` absent.
No environment installation/change. Every attempt uses a fresh directory/file.
Code/data base SHA60516f5; source hashes and command timestamps are in the evidence.
Public evidence mirrors selected local `outputs/tv2_w5/attempt_01` artifacts in
`reports/tv2/w5_evidence/attempt_01`; snapshots/models/images stay ignored local.

- W5-01: `scripts/validate_comparison.py --metadata-only --report <attempt>/comparison.json` PASS;
  TV1 snapshot `scripts/prepare_tv1_w5.py --verify-only --report <snapshot>/outputs/tv2_w5/candidates.json` PASS;
  `scripts/verify_w5_pixels.py --output <attempt>/train_val_pixels.json`3400PASS.
  Dataset comparison_v1 provenance d9fd5461…0a5f; W5 candidates provenance37db148e…cd07.
  Expanded data remains training_ready=false,holdout_ready=false. OwnerTV1 for future release.
- W5-02/W5-04: `scripts/verify_w4_checkpoints.py --model B2 --checkpoint experiments/B2_run01/checkpoints/best_model.pt --output <attempt>/b2_validation --device cpu` PASS;
  `scripts/report_w5_b2.py --verification-dir <attempt>/b2_validation --output <attempt>/validation_02` PASS.
  No B2 training or official Test. DINO experimentID/config/checkpoint/predictions=N/A,ownerTV3.
  `evaluate_w5_validation.py` with draft protocol exits1 as expected; no candidate output created.
- W5-03: `scripts/review_tv4_w5.py --snapshot <attempt>/upstream/tv4 --commit fef2511b571b23be3d4e2cf6c1ccedd659097b6f --url http://127.0.0.1:8767 --output <attempt>/ui_api_03` PASS15API assertions;
  exact-head `-m unittest discover -s tests -p 'test_tv4*.py' -v`44PASS.
  Browser IAB localhost timeout and Edge app approval timeout; ownerTV2/environment for UI retest.
  Sample0train only,cold11.713562s,warm2.038520s,CPU4threads,actual1crop; no general performance claim.
- W5-05: `scripts/check_environment.py`PASS; `scripts/validate_results.py`6fixturesPASS;
  `-m unittest discover -s tests -v`409PASS,0FAIL,0SKIP,48.218s unittest(53.600s runner).
  TV1 isolated W5 subset12PASS. Final suite TEMP is outside repository in the writable visualization root.
  Initial socket/TEMP failures preserved; no tests altered to conceal failures.

## Deviations and blockers

Full-snapshot raster integrity validator was mistakenly launched then interrupted
(last progress750/4000; exact decoded count/IDs unknown; scope includes Test).
No model forward/metrics/selection used Test. No PASS receipt. Log is retained;
Train/Val-only replacement subsequently verified3400rasters. Do not claim no
Test raster access across the whole session. See deviations.json for full audit.

W5 remains PARTIAL. TV3 must confirm protocol seed/tie/budget and hand over real
DINO artifacts; TV1 must review data; TV2 must finish browser responsive/click/
export review with screenshots. No product bug has been demonstrated in PR8 API.
B2 remains demo fallback. Approval/reviewer/merge states are not inferred.

## Resume

First inspect Git/processes/local evidence, do not restart reference/model jobs
merely because chat was interrupted. B2 validation and pixel audit are finished.
Read docs/handoff_tv2_w5.md for exact contracts/commands with a new attempt path.
When TV3 handoff arrives, verify external approval provenance and dataset/hash,
then run candidate audit and architecture-specific clean reload. No Test rerun.
Git publication/PR/reviewer notifications are recorded in
`reports/tv2/w5_evidence/attempt_01/publication.json` after delivery.

## Git delivery outcome

Implementation commit `0f43b5e`, report/evidence commit `0f002c9` pushed to
`origin/feat/baseline`; no other branch pushed. Final publication receipt and
raw-evidence attributes are in a following delivery commit, verified after push.
GitHub connector rejected PR creation **and** PR8 review comment with HTTP403
`Resource not accessible by integration`. No W5 PR/review request/comment was
sent; no reviewer approval/merge. PR body and unsent TV4 comment are saved in
`w5_evidence/attempt_01/pr_draft.md` and `tv4_review_comment.md`.
Manual compare: https://github.com/huyryan220806/Camera-Trap-ML/compare/main...feat/baseline?expand=1
Reviewers still need notification when PR can be created. Do not mark W5 COMPLETE.
