# TV4 W3 continuation - 2026-10-20

## Completed - 2026-10-21

- TV1 W3 re-audit PASS; TV4 W3 now supports actual B0/B1/B2 checkpoints.
- Final root test suite: 199/199 PASS (20.543s), reports/tv4_w3_continuation/tests.txt.
- Fresh server browser QA Oct 21 PASS for all three models / 3 viewports;
  all exported envelopes validate. Screenshot desktop and narrow mobile reviewed.
- B2 validation and smoke evidence retained, including the original loss-only
  exact-comparison failure and documented tolerance. No test model inference.
- TV1 W4 data inventory complete in feat/metadata-split worktree (path below):
  600 valid / 495 sequences / 98 locations / 680 crops; 12 metadata-selected
  quality examples. Final suite 178/178 PASS. B3 remains train/val only.
- Delivery docs: reports/tv4_w3_continuation/REPORT.md and, in TV1 worktree,
  docs/handoff_tv1_w4.md + reports/tv1_w4/REPORT.md.
- Saving local commits on the two fixed branches. No push/main merge; no
  checkpoint/image added to Git. Existing unrelated untracked files untouched.
- Demo running at http://127.0.0.1:8765 (started hidden Oct 21, launcher PID 2812).
  If stopped, run scripts/run_demo.py --port 8765 after checking the port.
- All required run sessions completed. Resume does not require re-training,
  re-downloading, or redoing validation unless source/weights/code change.

## Earlier resume checkpoint - 2026-10-21

- B2 independent validation PASS on 600 val images / 680 crops; 3400 train/val
  source hashes checked. Adapter/native logits delta 0. Exact classification
  matrices and metrics match. Weighted loss differs 0.8177 vs 0.8178; accepted
  with explicit one-unit four-decimal tolerance, not proof of identical loss.
  Original strict-comparison failure is preserved in outputs/tv4/w3_continuation.
- B2 installed and enabled. Actual MD+B2 train-image cold/warm smoke PASS.
  Browser B0/B1/B2 PASS, JSON exports and 3 viewports; report timestamps Oct 20.
- Root feat/demo still has uncommitted implementation; no push/main merge.
- TV1 W4 work is in the REUSED worktree:
  C:/Users/loval/.codex/worktrees/review-tv2-week2/CameraTrapML,
  now on feat/metadata-split, not TV2. Initial lock + inventory script written;
  inventory NOT YET RUN and tests/docs not yet complete at resume.
- Model lock freezes B2; allows data-quality inventory only. No test model
  inference or B3 tuning from test examples. B3 remains a W4 train/val task.
- Next: test inventory/resume, run it on root data with --data-root, produce
  TV1 report/examples, finish TV4 report/docs, run both suites, save results.
- Python: D:/VLU/261/ML/CameraTrapML/.venv/Scripts/python.exe.
  Old server/process sessions ended overnight. Start demo hidden when finished.

## Earlier notes (superseded where noted above)

User request: check TV3 completion, finish TV1/TV4 W3, then do TV1 W4 only
after all W3 work and model locking are complete. Do not merge main.

Starting refs:
- TV1 feat/metadata-split: 7e9b194.
- TV2 feat/baseline: 8a7c99c.
- TV3 feat/crop-classifier: 7cc87e8 (new training handoff).
- TV4 feat/demo: f65b936. Work stays on this fixed branch.
- main: 468d81f.

Initial review:
- TV3 now reports b2_run01, 28 epochs, best epoch 21. Image-level validation
  macro-F1 0.7455 on 600 images; recomputation from the published confusion
  matrix agrees within four-decimal rounding. Crop metrics also agree.
- B2 checkpoint claim: 89548866 bytes, SHA-256
  8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5.
  No download link found in the Git handoff, and no B2 weights on this machine.
  Asked the user for a URL/local path. Do not fabricate a URL or claim reload.
- TV3 metadata is now native class_map/id_to_label/is_official/preprocessing,
  not the older TV4 proposed metadata. Adapt strictly without modifying weights.
- TV3 run config still has preflight_hash_check=false; reload in training is
  same-process metadata + random-tensor forward, not independent validation.
- No committed final model lock found. Test analysis W4 must wait; do not
  inspect test images, run test inference, or select examples from test yet.

Plan:
1. Finish review/tests of the latest TV3 handoff without modifying that branch.
2. Install pinned B1 from the existing TV2 handoff; enable and smoke/browser test.
3. Support the native TV3 B2 adapter with synthetic regression tests. Keep B2
   disabled until actual checkpoint bytes and real inference are verified.
4. Recheck TV1 frozen metadata; record exact remaining dependencies before W4.

Keep unrelated untracked reports/notebooks, data, weights and backup stash.
Record outcomes here before stopping. No main merge, no automatic model lock.

Update during execution:
- User supplied outputs/tv3/best_model.pt. SHA/size match TV3 handoff exactly;
  weights_only=True load and native adapter metadata/remapping PASS, epoch21.
- B1 real setup and MD+B1 cold/warm smoke PASS. Browser B0/B1 PASS at
  1440x1100, 390x844, 320x740; screenshots viewed. B1 JSON export validates.
- TV3 full suite 93/93 PASS (16.736s). TV4 suite after five new tests:
  196/196 PASS (33.060s). Latest files are local edits, not committed/pushed.
- B2 independent full validation is next: scripts/verify_tv4_b2_handoff.py
  --source outputs/tv3/best_model.pt --tv3-root
  C:/Users/loval/.codex/worktrees/review-tv3-week2/CameraTrapML.
- User clarified: lock B2, but B3 will still be tried in W4. This authorizes
  freezing the B2 checkpoint baseline, NOT claiming B3 is waived or a final
  model-selection decision. Keep test inference/error inspection gated while
  B3 selection is pending. Separate data inventory from test model errors.
