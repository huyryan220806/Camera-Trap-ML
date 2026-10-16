# TV2 Cross-review TV4 W2

## Review metadata

- Reviewer: **TV2**
- TV4 branch (read-only): `origin/codex/tv4-week2-demo-detector`
- TV4 commit: `f61ca6d3180971c4d7725c7d3cab1046be44134a`
- Acceptance source: `docs/handoff_tv4_w2.md` at that commit
- Review date: **2026-10-11**
- Isolation: the TV4 commit was exported to an ignored temporary snapshot. No checkout, edit, commit or push was made on the TV4 branch.

## Environment

- OS: Windows 11 `10.0.26200`
- Python: `3.12.14`
- PyTorch: `2.8.0+cpu`; torchvision: `0.23.0+cpu`; CUDA unavailable
- MegaDetector package: `10.0.25`
- Model: `md_v5a.0.1.pt`, CPU, image size 1280
- Model MD5: `60f8e7ec1308554df258ed1f4040bc4f`
- Model SHA-256: `fe3e90e4b1955821ab7c1f88b446dc0c8cb25e109fdd1872916a55305294a5ef`
- Inputs: eight locally available **train-v2-only** images, verified against each manifest `quality.sha256`. No validation or test image was used.
- Runtime: loopback demo at `127.0.0.1:8766`; desktop viewport and 390×844 responsive viewport checked in the Codex in-app browser.

## Required command checks

| Check | Status | Evidence |
|---|---|---|
| Complete unittest suite | PASS | 91 tests ran in 10.584 s, 0 failed: [final_handoff/tv4_tests.txt](final_handoff/tv4_tests.txt). |
| Dependency consistency (`pip check`) | PASS | `No broken requirements found`: [final_handoff/tv4_pip_check.txt](final_handoff/tv4_pip_check.txt). |
| Fresh real detector smoke | PASS | The pre-existing smoke report was removed from the temporary snapshot before execution. The new run detected one animal at score 0.891 in a train-v2 image and recorded package/model/hash: [final_handoff/tv4_detector_smoke.json](final_handoff/tv4_detector_smoke.json). |

## Checklist from `docs/handoff_tv4_w2.md`

| Item | Status | Independent evidence |
|---|---|---|
| Load an image, show preview, run mock and distinguish it from real inference | PASS | Uploaded a train-v2 JPEG through the UI. Preview rendered; mock badge stated `GIẢ LẬP · KHÔNG PHẢI SUY LUẬN`, then MegaDetector mode displayed `MEGADETECTOR · MDv5a.0.1`. Mock JSON used `pipeline.mode=mock`; real JSON used `pipeline.mode=megadetector`. |
| Run MD, inspect box, and compare JSON/version/threshold/hash | PASS | Real UI inference detected one animal box at 0.891. Exported JSON reports MDv5a.0.1, package 10.0.25, threshold 0.2 and the exact weights SHA-256: [final_handoff/tv4_exported_result.json](final_handoff/tv4_exported_result.json). Desktop visual evidence: [final_handoff/tv4_desktop.jpg](final_handoff/tv4_desktop.jpg). |
| Test no detection, corrupt file and detector failure; no implicit mock fallback | PASS | A real run at threshold 1.0 returned `no_detection` and stated this does not mean an empty image. Uploading a corrupt JPEG returned a read-stage error. Mock error was explicitly labelled. The actual adapter was also invoked with an intentionally missing weights path and returned detect-stage `error`, retained `pipeline.mode=megadetector`, empty detections and no mock fallback: [final_handoff/tv4_edge_results.json](final_handoff/tv4_edge_results.json). |
| Change image/mode/threshold and ensure stale results are cleared | PASS | Independently changed each control after a result. JSON reset to `{}`, export was disabled and box count became zero before the next run. |
| Export JSON and inspect SWG warning and classifier-unavailable disclosure | PASS | Export download succeeded. The page always displayed the SWG training-overlap banner. JSON has `training_overlap_swg=true`, the limitation text, `classifier_id=null` and `species=null`; the UI labels the value `Điểm detector`, not a calibrated probability. |
| Open on a small screen; ensure boxes align and no horizontal overflow | PASS | At viewport 390×844, document `scrollWidth=clientWidth=375`. The image occupied x=18..357.2 and the box x=139.86..262.68, inside the displayed image. Overlay position matched JSON percentage coordinates and toggle hide/show worked. Evidence: [final_handoff/tv4_mobile.jpg](final_handoff/tv4_mobile.jpg). |

Checklist totals: **PASS 6, FAIL 0, NOT TESTED 0, BLOCKED 0**.

The structured UI observation summary is [final_handoff/tv4_ui_checks.json](final_handoff/tv4_ui_checks.json).

## Commands executed

From the isolated TV4 snapshot with its dedicated Python 3.12 environment:

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 -m pip check
python -X utf8 scripts/prepare_tv4_demo.py --smoke
python -X utf8 scripts/run_demo.py --port 8766
```

Additional independent checks exercised the real adapter with a missing model path and verified a two-box coordinate-conversion fixture. UI tests used browser controls rather than TV4's own report as evidence.

## Issues found

None found in the tested scope.

## Not tested

None from the required six-item handoff checklist.

## Blocked

None.

## Final conclusion

**PASS.** All six required checklist items and all three required command checks passed independently. The result approves the tested TV4 W2 handoff at the commit above; it does not claim independent MegaDetector accuracy on SWG and does not add a species classifier. TV2 did not modify the TV4 source branch.
