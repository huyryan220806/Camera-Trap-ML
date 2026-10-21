# TV4 week 3 verification - 2026-10-18

## Results

- Full unit suite: **191/191 PASS**, no failures/errors/skips, 34.103 seconds.
- New classifier tests: 18 PASS. Synthetic B0/B1/B2 checkpoints, strict map
  and transform checks, wrong hash/size/shape/kind, non-finite weights,
  missing/disabled model, bounded LRU, invalidation, concurrent first load,
  multiple crops, empty/decode/detector/classifier failure, HTTP export contract.
  Different box pixels produce independent scores; invalid logits and review
  thresholds are rejected. B0 preprocessing matches the original validation transform.
- Real MegaDetector MDv5a + handed-off B0: PASS on one **train v2** image.
  B0 checkpoint SHA d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680.
  One accepted animal box; repeated predictions identical, classifier loaded
  once, second request cache hit. No training or test inference.
- Browser QA: desktop 1440x1100, mobile 390x844 and 320x740. Actual MD+B0,
  export preserving provenance, mock multiple boxes with 3 scores each,
  empty/read/detector errors, detector-only compatibility, stale result
  clearing and disabled B1/B2. No page errors or page overflow; box geometry
  stays on the image and class names do not overlap scores.
- Screenshots inspected locally in `outputs/tv4/w3/browser/`; not source
  images or model weights committed to Git.
- Repeated B0 setup reuses verified checkpoint bytes. `pip check` PASS.
- Frozen data and historical B0 run artifacts remain unchanged.

## Evidence

- `tests.json` and `tests.txt`: complete integrated suite, including synthetic
  negative cases whose expected errors appear in the log.
- `smoke.json`: cold/warm real train-only inference and provenance.
- `browser_verification.json`: browser checks against the local server.
- `example_export.json`: real JSON envelope exported through the browser.

## Scope and limits

B1/B2 have adapter fixtures but no approved real checkpoint. B0 learned full
images, so crop inference is a distribution shift. This is integration
verification, not evidence of classifier accuracy on detector crops. Mock
multiple-box checks are explicitly synthetic. No independent TV2 acceptance
is implied. MDv5a training includes SWG. Softmax scores are **not calibrated
probabilities**; detector/review thresholds are demo defaults, not optimized.

See [handoff](../../docs/handoff_tv4_w3.md) for setup, checkpoint requirements,
the v1 result/provenance envelope, errors, cache and restart procedure.
