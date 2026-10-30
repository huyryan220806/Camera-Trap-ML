# TV2 W5 progress — 28–30/10/2026

## Latest status — 30/10/2026, pretrained approval review

Base `163947b5eec79785c89b00dfc5b2b2d618a0d772`, branch `feat/baseline`.
Read all three user-supplied TV3 files in `dino/`; originals unchanged and
byte-exact copies/hashes stored in
`reports/tv2/w5_pretrained_review/2026-10-30/attempt_01/received/`.
SGD0.01/momentum0.9/WD0.0001/cosine50, seed42/max50/patience7/effective32parents,
frozen CLS384+Linear8 and evaluation rules are declared consistently in config,
embedded smoke config and READY. TV2 user explicitly agrees technically with
conditions, confirms no additional sources available and requests DRAFT retained.

| Item | Current result | Evidence / next action |
| --- | --- | --- |
| Train/Val metadata | PASS:7/7 hash matches,2800/3125train,600/680val | pretrained review audit.json; no new raster/Test access |
| Upstream commit/architecture | Official commit/factory confirmed; patch16/embed384/prefix08c60483 | Source links in pretrained review; does not verify full weights SHA |
| GPU/backbone | TV3 reports PASS,32×384features,RTX4060Laptop,CUDA,AMPfalse | No independent replay at TV2; weights/vendor/source missing |
| Config raw hash | **BLOCKED B1**:receivede9303b… vs smoke320718… | JSON identical; CRLF/LF not explanation; TV3 selects canonical bytes/SHA |
| Approval | TV2 **CONDITIONAL** real chat confirmation; TV3 **BLOCKED B2** | READY still awaits confirmation; no invented reviewer/receipt |
| Referenced verification bundle | **BLOCKED B3** | TV3 supplies source SHA852989…/commit,pretrained hash/strict-load and data preflight/sample receipts cited in READY |
| Official registration | **NOT REGISTERED**, protocol **DRAFT** | proposed ID DINOv3_LP_run01 only;experiments=[],canonical config hash=null |

User's follow-up explicitly retains verification gates and asks to finish
independent W5 tasks (TV4 UI/testing/Draft PR) while B1–B3 await TV3. No DINO,
Test W4, B2 checkpoint change or PR merge. Current technical report:
`reports/tv2/TV2_W5_PRETRAINED_REVIEW_2026-10-30.md`.
Checks/UI/Draft PR results for this continuation are appended below after run.

## Continuation checks and UI — 30/10/2026

- Actual updated config JSON valid; statusDRAFT/TV3null/experiments[] preserved;
  DRAFT gate rejects before real model/checkpoint/prediction access.
- Current full software suite409PASS/0FAIL/0SKIP,64.740s; exact TV4head
  suite44PASS/0FAIL/0SKIP,8.393s. Environment and6contract examplesPASS.
  No tests/code altered. Logs/checks.json copied to
  `reports/tv2/w5_pretrained_review/2026-10-30/attempt_01/`.
- Browser review reached correct PR8head fef2511 via loopback server8768 outside
  sandbox; new QA journals only. **15functional UI casesPASS**: realMD+B2,
  responsive1440/390/320/single+multiplebox geometry,maxerror<.011px,
  bidirectional row/box IDs,low-score filter,draft/save/original immutability,
  reload/discard draft,browser JSON download exactmatch,validtrain upload,
  corruptread error,no_detection,syntheticdetector miss/error. NoDINO/TestW4.
- Evidence/screenshots/JSON:
  `reports/tv2/w5_ui_review/2026-10-30/attempt_01/`. Browserconsole empty.
  Original invalidReviewFields1 count included the intentionally small checkbox;
  corrected input/select/textarea audit has no clipped review fields.
- **P2 UI-A11Y-01,ownerTV4**:mobile export icon lacks accessible name(span hidden,
  aria-label/title null). Functional export works; report includes repro/retest.
  App code/TV4 branch not changed; PR8 not APPROVED or merged.
- B2 cold UI request52.27s under startup/regression context is not a benchmark
  or validation result. Previous B2 model metrics unchanged. Historical UI
  BLOCKED entries below remain historical; connection blocker is resolved.
- Draft PR preparation/publication result is recorded after final push; no
  protocol APPROVED or official DINO registration while B1–B3 persist.
  Body: `reports/tv2/W5_DRAFT_PR_2026-10-30.md`; receipt:
  `reports/tv2/w5_pretrained_review/2026-10-30/attempt_01/publication.json`.
  Delivery commit can be located by `git log -1 -- reports/tv2/TV2_W5_PRETRAINED_REVIEW_2026-10-30.md`.

**Historical update — 29/10/2026:** protocol/config/handoff only, base commit
`3f76643d1bc395098d90105e67a9cf29c8fe3256`, branch `feat/baseline`.
User-supplied configuration recorded: frozen DINOv3 ViT-S/16 + linear8;
conditional DINOv2 ViT-S/14 fallback registered before the official run;
comparison_v1 Train2800parents/3125GTcrops, Val600parents/680GTcrops;
seed42, max1candidate training run, max50epochs/patience7, image_macro_f1,
earliest_epoch checkpoint tie, lowest_class_id prediction tie, mean crop
softmax vectors per image, effective32parent batch, crop microbatch preserving
per-image weights, planned RTX4060Laptop8GB/FP32. GPU availability is unverified.

Source: current user instruction dated29/10 plus
`feat/metadata-split@9abc9c572a9191e8a43a5abef05ebaf846b8356f:docs/plans/TV3_W5_W6.md`
(Git content SHA2567708c9683b0938b728276302f88c15df5e9bac99edb0944a79e3fa0118f5d88a).
The TV1-authored plan is not a separate TV3 reviewer confirmation. **DRAFT is
retained**, all reviewers/approval_evidence remain null, selected_model=null,
experiments=[]. Seed/budget fields now describe the requested configuration,
not an approval receipt. Historical entries below describe the earlier attempt.

Before official run, TV2/TV3 must provide actual approval evidence; TV3 must
select/register the model and verify learning rate, optimizer, scheduler,
pooling, pretrained source/version/SHA, model-specific preprocessing and actual
device/microbatch/accumulation in the training config. Existing validation gate
blocks DRAFT but does not validate all new training fields; code/gate unchanged.
No training, Test inference, checkpoint change or W6 work in this update.
Current check/commit/push results are appended in the protocol update ledger.

## Protocol update ledger — 29/10/2026

- Task: W5 protocol/config alignment only. Config SHA-256:
  `7614281a0eb89f79160331f93b26594665775fbbcc8737adbc176121480edbc2`.
  Dataset remains comparison_v1; no experiment registered or executed.
- Source read: `git fetch origin`, then
  `git show 9abc9c572a9191e8a43a5abef05ebaf846b8356f:docs/plans/TV3_W5_W6.md`.
  User decision and source commit/content hash recorded in config/protocol.
- JSON parse and declared configuration assertions PASS. Existing gate accepts
  the field names/policies; actual DRAFT rejected with
  `BLOCKED: W5 protocol needs TV3 approval` before checkpoint/prediction access.
  Gate implementation/tests unchanged; it does not enforce every training field.
- Related tests: existing Python3.12.14 venv,
  `-X utf8 -m unittest discover -s tests -p test_w5_validation.py -v`:
  **32 PASS, 0 FAIL, 0 SKIP**, 25.387s (runner26.304s). No training/Test inference.
  Log: `outputs/tv2_w5/protocol_update_20261029_01/related_tests.log`, SHA-256
  `a7f6b99e0d6d481ce51a1c8ac2ea015583da5cf6d6ff942729c8fff72f886caa`.
  JSON/gate summary: same folder `checks.json`; earlier attempts retained.
- `git diff --check` PASS; tracked scope is exactly config, protocol, handoff
  and this progress file. Four original untracked user documents remain excluded.
- Approval: **DRAFT**. TV2/TV3 real confirmation still required; no signatures,
  approval receipt, official experiment or model-registration values invented.
  LR/optimizer/scheduler/pooling/pretrained SHA/preprocessing and actual
  microbatch/device remain pending TV3's verified training config.
- Delivery: base/parent `3f76643d1bc395098d90105e67a9cf29c8fe3256`;
  identify this update commit with `git log -1 -- configs/tv2_w5_protocol.draft.json`.
  Push only to `origin/feat/baseline`; final handoff records local/remote SHA.
  Next action is TV2/TV3 review of the missing config/approval, not a training run.

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
