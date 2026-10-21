# Progress TV4 W3 - 2026-10-18

Task: integrate classifiers, inference flow and model cache. Start with real
B0; allow replacement by approved B1/B2 checkpoints. Multiple boxes, top 3,
prediction scores must not be described as calibrated probabilities.

- TV1 W3 published and remote SHA verified: 7e9b1949f10126fbcfa83fa12baeca488b6aeab3
  on feat/metadata-split. 173 tests PASS; comparison_v1 metadata PASS, unchanged.
- Working branch: feat/demo, fast-forwarded to TV1 handoff. No new branch.
- Existing B0: outputs/review_w2_round3/best_model.pth, SHA
  d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680,
  44837567 bytes. Use verified copy; no retraining or validation/test inference.
- Existing MD: outputs/tv4/models/md_v5a.0.1.pt. Keep SWG training-overlap warning.
- Do not stage unrelated untracked reports/notebooks. Keep the TV1 backup stash.

Plan: explicit registry and strict checkpoint adapter, bounded thread-safe CPU
model cache, per-box inference and legacy v1 results plus provenance envelope,
backward-compatible detector-only API, UI classifier selector/top 3, setup and
resume script, focused regressions, real train-only smoke and browser QA.

Limits: B0/B1 learned full images; detector crops are a distribution change.
Demo does not establish scientific B1/B2 comparison performance. B1/B2 have
no accepted real checkpoint yet; adapter fixtures must be labelled synthetic.

Implemented: verified model registry/cache, B0/B1/B2 ResNet18 adapters,
per-box inference envelope, server/UI top 3 + classifier selector, setup and
real smoke scripts. B1/B2 are disabled without accepted real checkpoints.
18 focused tests PASS, including B1/B2 synthetic checkpoint adapters and
concurrent cache, checksum changes, errors and HTTP contract.
Real MD+B0 cold/warm smoke PASS on one train v2 image; model loaded once,
identical predictions. Evidence: outputs/tv4/w3/smoke.json.

Complete: full suite 191/191 PASS, 0 failures/errors/skips, 34.103 seconds.
Real browser QA PASS at 1440x1100, 390x844 and 320x740; screenshots inspected.
Exported envelope independently validated. pip check PASS. B0 setup rerun
successfully reused cached weights. Frozen data and historical B0 artifacts
are unchanged. Evidence copied to reports/tv4_w3; handoff in docs/handoff_tv4_w3.md.

TV1 is already pushed. TV4 implementation commit
ddce6fb6863bc8d8f65a767ff94ff95c2152eece was successfully pushed to origin/feat/demo
on 2026-10-18 with user authorization. It includes TV1 W3 ancestor 7e9b194.
Do not merge into main until all members finish and the user authorizes integration.
No branch codex/* was created. No code on TV2/TV3 branches was changed.

Demo launched at http://127.0.0.1:8765 (local process); logs are under
outputs/tv4/w3/server.*.log. After a restart, run scripts/run_demo.py again.
Read this file and git status before resuming; do not recreate the frozen
snapshot, remove cached weights, drop the TV1 backup stash, or stage unrelated
untracked reports/notebooks. Unit/real smoke processes completed; only the
requested demo server is left running. Further TV4 pushes should target feat/demo,
not main, and retain the TV1 W3 ancestor 7e9b194.
