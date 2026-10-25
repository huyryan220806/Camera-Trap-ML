# TV4 W4 progress - 2026-10-25

User authorized TV3 fixes first, then TV4 review screen and inference timing.
TV3 fixes are in feat/crop-classifier worktree; B2/B3 validation diagnostics
and regression tests done. B3 reference remains UNRESOLVED, excluded from Test.

Root feat/demo fast-forwarded to already published main c6aee9f (TV2 W4).
No main modification, push, or merging TV3 W4 into main. Preserve user files.

TV4 implemented so far: separate immutable inference snapshots and append-only
human review events with revisions, explicit unresolved/empty/detector-miss
states, runtime and batch logging. No input photos stored by the review API.

TV3 saved locally on feat/crop-classifier as a692a10, full 109 tests PASS.
TV4 UI implemented and browser QA PASS for 1440x1100, 390x844, 320x740.
Initial browser assertion mistakenly included the 13px checkbox in a 40px
text-field-width rule; corrected the selector, retained initial failure log.
Final full regression: 356/356 tests PASS in 72.621 seconds.
Final browser QA PASS after restarting the server: real MD+B2, corrections,
save/reload/export, low scores, missing detections, corrupt image, three widths.
Server launcher PID 12300 / child PID 22380 on 127.0.0.1:8765 (latest backend).

Initial benchmark_20261025 overlapped the first unit test run: keep as diagnostic,
do not use as primary speed measurement. It had 8 metadata-selected train images,
no unmatched GT boxes at IoU .5. Final benchmark adds 4 separately reported tiny-box
train probes (metadata-only choice) and excludes those probes from primary timing.

Isolated final benchmark COMPLETE in outputs/tv4/w4/benchmark_final_20261025;
no tests or browser inference ran concurrently. If interrupted, inspect
config.json and inference.jsonl, then run the SAME command with --resume:

    .venv/Scripts/python.exe -X utf8 scripts/benchmark_tv4_w4.py --output outputs/tv4/w4/benchmark_final_20261025 --resume

Completed jobs are flushed to disk and skipped on resume. Code/config changes
require a NEW output directory; never overwrite the earlier evidence.

Final benchmark: 21 requests (17 ok, 3 needs_review, 1 no_detection). Primary
16 warm requests: mean 5547.205 ms, p50 5999.543 ms, p95 6239.496 ms; cold
18078.914 ms. Four tiny-box probes excluded from primary timing. All four have
unmatched GT candidates; one has no detections; last has 12 boxes, crop batches
[8, 4]. Do not call this independent detector evaluation or adjudicated misses.
Completed-run resume PASS: journal 21 -> 21, identical SHA, zero new jobs.

Handoff: docs/handoff_tv4_w4.md. Report: reports/tv4_w4/REPORT.md.
Evidence packaged in reports/tv4_w4/evidence. Final SHA audit: B2
8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5,
B3 93ae48dd4b42fa6062daed3a9a1869d620bd7ba9e7ae2aa274085b061f76300b,
comparison provenance d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f,
all unchanged. Frozen inputs and original evaluation/inference/model code have
no diff from origin/main on the demo branch. User's unrelated untracked files
are preserved. All required command sessions completed; only the local demo
server remains available for the user.

Implementation and verification COMPLETE; saved on feat/demo with commit title
"feat(tv4): add durable review workflow and measured inference logs" (git log -1).
TV3 remains saved as a692a10 on feat/crop-classifier, with B3 UNRESOLVED.
No push/main merge. Next session should read this file and the latest user request
before doing anything; do not repeat the completed benchmark or official Test.
