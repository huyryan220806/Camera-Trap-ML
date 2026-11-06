# TV2 W6 — Independent Model Replay and Recipe Decision

**Date:** 2026-11-06
**Branch:** `feat/baseline`
**HEAD before report changes:** `4696a6ef2dd8a3e61013be297e2aeaafe55fb060`
**Protocol lock:** `18c8ec3a6a58c47b04dbe8606217478145baed6c`
**TV3 result commit:** `076a640a263c3d7f0c1406d741468dca504f352c`
**TV3 source commit:** `127cac5b64d37fdda630a2f84b006a8e420dc9ed`

## Decision

- **ARTIFACT_VERIFIED: PASS** — ZIP integrity, package indexes, frozen configs, checkpoints, source/vendor pins and Validation data passed the independent preflight.
- **REGRESSION_REVIEW: PASS** — paired results were recalculated on the 600 shared Validation image IDs, using the TV2 W5 R0 reference.
- **MODEL_REPLAY: PASS** — fresh TV2 Python processes independently loaded each best checkpoint and inferred all 680 GT crops from the 600 real Validation images. Exact comparison passed for both runs.
- **RECIPE_SELECTION: R2** — TV2 selects R2 for seed 42 under macro-F1 → accuracy → inference cost when needed. No tie required a cost comparison.
- **Demo default: unchanged** — TV4 adapter review remains pending. This decision does not approve R3/R4 execution automatically. R5/R6 remain conditional on TV1 data acceptance, which is still pending.

## Runtime and input identity

The isolated TV2 replay environment used Python 3.12.10, torch 2.6.0+cu124, torchvision 0.21.0+cu124, Pillow 12.2.0, NumPy 2.5.3, scikit-learn 1.9.0, CUDA 12.4, cuDNN 90100, Windows 11, and an NVIDIA RTX 4060 Laptop GPU. Runtime settings were FP32, AMP off, TF32 off, deterministic algorithms on, cuDNN deterministic on, cuDNN benchmark off, and 10 intra/inter-op threads.

The captured CPython build string differs from TV3's build string (`main, May 30 2025` versus `tags/v3.12.10:0cc8128, Apr 8 2025`); both report Python 3.12.10 and MSC v.1943. Windows reports build 26200 in the TV2 replay environment and 26100 in the producer receipt. All specified Python/package versions, GPU model and precision/determinism settings matched, and the independent outputs matched the producer exactly. Both build differences are retained in the environment receipt.

The preflight verified both requested ZIP SHA-256 values and CRCs, every indexed package file hash and byte count, best/last checkpoint hashes, raw and canonical frozen config hashes, source snapshot files against TV3 source commit `127cac5b64d37fdda630a2f84b006a8e420dc9ed`, clean vendor commit `6876159a11b4df116f30f667f8c9888617df0751`, dataset provenance and Validation manifest hashes, plus bytes, dimensions and RGB pixel hashes for each of the 600 Validation images. The 680 Validation crop IDs were unique and present. No train or Test image was opened by the replay.

| Run | ZIP SHA-256 | Best checkpoint SHA-256 | Frozen config canonical SHA-256 |
|---|---|---|---|
| R1 | `998901556b51789a52fc7a650eac504a4f6e23a1118af00450c7a18aeb9bb2fe` | `86b1c7460b300f27b2f8d5efe426def51750478e2bf195ffa61df1213f646f79` | `2ab03b7e13d798b8aace5e4b3542a189389c43c7630f4132303b9200fced63bf` |
| R2 | `30f380cab3aa89f5b63c54507f7b7b63d2479e73f52710283e4f557e27fda223` | `022786bda189478b9098a32299e9a290f9c37f01681ac3784b1782ce24b6b8bc` | `55dea8ab328e43581642deb964631d391a5b88596feb191a5fa5911a7a94acb7` |

## Exact independent replay comparison

Comparison policy was exact element equality; no tolerance was introduced. Replay predictions were produced by fresh Python processes from `best_model.pt`, using the pinned source snapshot and verified image bytes/pixels. Results below compare against each package's producer `validation.json`.

| Run | Crop logits | Crop probabilities | Image probabilities | Predicted classes | Metrics | Max absolute delta |
|---|---:|---:|---:|---:|---:|---:|
| R1 | 0 / 5,440 mismatches | 0 / 5,440 | 0 / 4,800 | 0 / 1,280 class mismatches | exact | 0.0 |
| R2 | 0 / 5,440 mismatches | 0 / 5,440 | 0 / 4,800 | 0 / 1,280 class mismatches | exact | 0.0 |

Crop and image IDs, order and labels also matched exactly. Each replay covered all 600 images and all 680 crops. Full mismatch counts, metric comparisons and artifact SHA-256 values are in [exact_comparison.json](../../outputs/tv2_w6/independent_replay_20261106/exact_comparison.json).

## Validation results and paired review

| Run | Correct | Accuracy | Macro-F1 | Δ correct vs R0 | Δ Macro-F1 vs R0 |
|---|---:|---:|---:|---:|---:|
| R0 | 507/600 | 0.845000 | 0.8444008279545706 | — | — |
| R1 | 501/600 | 0.835000 | 0.8338641693401928 | -6 | -0.0105366586143778 |
| R2 | 511/600 | 0.851667 | 0.8506508530416190 | +4 | +0.0062500250870484 |

R1 changes 39 image predictions: 8 wrong-to-correct and 14 correct-to-wrong. Sambar loses 4 correct images, and R1 is below R0 on both accuracy and macro-F1.

R2 changes 34 image predictions: 12 wrong-to-correct and 8 correct-to-wrong. It gains 4 correct images overall and no class loses 4 or more correct images. The class-level changes versus R0 are: muntjac −1, rabbit 0, sambar +4, serow +1, common palm civet −2, masked palm civet +1, silver pheasant 0, and wild pig +1. Common/masked civet confusion rises from 13 to 15; muntjac/sambar confusion rises from 12 to 13. These regressions remain visible despite the aggregate gain.

R2's gain is small: +0.67 percentage points accuracy and +0.625 percentage points macro-F1 on one seed and one balanced Validation set. At 511/600 correct, R2 remains 17 correct images short of the 528/600 (88%) target. This comparison does not establish statistical significance, natural-prevalence performance, cross-site generalization, or end-to-end detector performance.

R2 is selected because it has the highest macro-F1 and accuracy among R0/R1/R2; inference cost is a tie-breaker only and was not needed. This records the seed-42 recipe choice, not a claim that R2 meets the target or a request to change the demo default.

## GPU accounting

The replay budget is 2.0 GPU-hours. Timing conservatively covers model/checkpoint loading through CUDA-synchronized inference and metric evaluation. R1 was first replayed successfully, but its console report hit a Windows cp1258 Unicode encoding error after writing results; it was rerun in a fresh process with UTF-8 output to retain a clean log. Both inference executions are included in usage.

| Process | Run | GPU hours |
|---|---|---:|
| Initial R1 inference; post-inference console encoding error | R1 | 0.0368770085 |
| Clean-log R1 replay | R1 | 0.0443250109 |
| R2 replay | R2 | 0.0365492534 |
| **Total** |  | **0.1177512729 / 2.0** |

Remaining replay budget: **1.8822487271 GPU-hours**. No training or Official Test inference was run. Machine-readable accounting and process identities are in [environment_receipt.json](../../outputs/tv2_w6/independent_replay_20261106/environment_receipt.json); per-run logs are `replay_R1.log` and `replay_R2.log` in the same evidence directory.

## Validation and next gates

- Registry/schema validator: `VALID`, protocol remains `APPROVED`.
- W6 validation tests: **51 PASS / 0 FAIL**.
- W5 focused regression tests: **70 PASS / 0 FAIL**.
- `git diff --check`: required before commit.
- The protocol's approvals, frozen configs/source bindings and smoke evidence were not changed. Registry updates are limited to replay accounting and the R2 recipe-selection evidence. R3/R4 remain conditional and unapproved; R5/R6 remain conditional while TV1 data review is pending.
- TV3 may use the R2 selection evidence when proposing the next seed-repeat step; separate approval and remaining-budget gates still apply. TV4 adapter review must pass before considering any demo-default change.

Prior artifact and paired-review details: [TV2 W6 independent acceptance](TV2_W6_R1_R2_INDEPENDENT_ACCEPTANCE_2026-11-06.md).
Environment receipt SHA-256: `ac435b6737b0acdfcd0a2571e305197c7fc691e46f482b7f5044e34361813fee`.
