# TV2 W6 — Independent Acceptance R1/R2

**Ngày:** 06/11/2026

**Branch kiểm tra:** `feat/baseline`

**Protocol lock:** `18c8ec3a6a58c47b04dbe8606217478145baed6c`

**TV3 result commit:** `076a640a263c3d7f0c1406d741468dca504f352c`

**TV3 source commit:** `127cac5b64d37fdda630a2f84b006a8e420dc9ed`


## Quyết định TV2

- **ARTIFACT_VERIFIED: PASS** — hai ZIP, package index, CRC, checkpoint, frozen config, source/data/runtime bindings và producer registry artifacts được kiểm tra.
- **REGRESSION_REVIEW: PASS ở mức saved predictions** — tính lại trên 600 cặp image ID chung; R1/R2 không dùng Test.
- **MODEL_REPLAY: `MODEL_REPLAY_PENDING`** — chưa chạy replay. Python/Torch CUDA đã khóa không có sẵn; không dùng kết quả reload của TV3 thay independent replay và không nới tolerance.
- **RECIPE_SELECTION: `PENDING_MODEL_REPLAY`** — R2 là ứng viên theo metric hiện có, chưa được TV2 chọn recipe chính thức.
- **TV2 outcome: `PENDING`** — chưa đề nghị đổi demo mặc định. TV4 adapter gate cũng còn chờ. Không cấp approval R3–R6.

## Git và nguồn

HEAD trên `feat/baseline` là protocol lock `18c8ec3a6a58c47b04dbe8606217478145baed6c`. Không merge nhánh TV3; frozen config, source TV3, W1–W5 và protocol lock không bị sửa. GitHub xác nhận TV3 result commit `076a640a263c3d7f0c1406d741468dca504f352c` (“docs(tv3): publish W6 R1 R2 producer results and audits”) và source commit `127cac5b64d37fdda630a2f84b006a8e420dc9ed` tồn tại ở `feat/crop-classifier`.

- [TV3 result commit](https://github.com/huyryan220806/Camera-Trap-ML/commit/076a640a263c3d7f0c1406d741468dca504f352c)
- [TV3 source commit](https://github.com/huyryan220806/Camera-Trap-ML/commit/127cac5b64d37fdda630a2f84b006a8e420dc9ed)
- R1 ZIP SHA-256: `998901556b51789a52fc7a650eac504a4f6e23a1118af00450c7a18aeb9bb2fe`
- R2 ZIP SHA-256: `30f380cab3aa89f5b63c54507f7b7b63d2479e73f52710283e4f557e27fda223`

Cả hai SHA ZIP khớp. CRC toàn bộ archive PASS; 39 file R1 và 38 file R2 có đúng membership so với `package_index.json` (index bao phủ 37/36 payload files; `package_index.json` và `registry.delivery.json` là metadata ngoài index). Hash và byte length của mọi payload được index bao phủ đều khớp. SHA của best/last checkpoint khớp handoff và index. Producer `registry.result.json` ghi đúng hai official attempts: R1 và R2 đều `COMPLETED`; mỗi attempt chỉ có một lượt. Producer status/reload ghi `fresh_process_reload=PASS`, nhưng `tv2_model_replay=PENDING` và `tv4_adapter=PENDING`.

Dataset là `comparison_v1`, provenance SHA-256 `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`; prediction artifacts ghi Validation, 600 ảnh/680 GT crops. Cả hai run pin source `127cac5b64d37fdda630a2f84b006a8e420dc9ed`, runtime lock và class order như protocol. Raw/canonical frozen-config hashes cùng checkpoint best/last hashes được khớp độc lập với package handoff.

| Run | Frozen config canonical SHA-256 | Config raw SHA-256 | Best checkpoint SHA-256 | Last checkpoint SHA-256 |
|---|---|---|---|---|
| R1 | `2ab03b7e13d798b8aace5e4b3542a189389c43c7630f4132303b9200fced63bf` | `92bf5966fe2b4e228fb52b0ae975c8e5044ca1c35b6a4d06ab79f5733cef507c` | `86b1c7460b300f27b2f8d5efe426def51750478e2bf195ffa61df1213f646f79` | `c3a39e22f10f483a2885610ecbf8a00a552ffbd7472a215497732d09f9554250` |
| R2 | `55dea8ab328e43581642deb964631d391a5b88596feb191a5fa5911a7a94acb7` | `a649fe30c436fee538d9a58a904685a558aebd77a1df3af91409f55f1a86f36c` | `022786bda189478b9098a32299e9a290f9c37f01681ac3784b1782ce24b6b8bc` | `b220b65ef64cc03263afd848f00c20762b2948d6639db17da4a1636cfe648c57` |

## Recomputed Validation metrics

Metrics below were recomputed from saved image predictions, using all eight classes and image-level aggregation. R0 predictions are the TV2 W5 locked reference; crop probabilities were separately averaged by `image_id` and compared with saved image scores.

| Run | Correct | Accuracy | Macro-P | Macro-R | Macro-F1 | Δ correct vs R0 | Δ Macro-F1 vs R0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| R0 | 507/600 | 0.845000 | 0.847957 | 0.845000 | 0.8444008279545706 | — | — |
| R1 | 501/600 | 0.835000 | 0.835766 | 0.835000 | 0.8338641693401927 | -6 | -0.0105366586143779 |
| R2 | 511/600 | 0.851667 | 0.853158 | 0.851667 | 0.8506508530416190 | +4 | +0.0062500250870484 |

R2 changes optimizer and augmentation together; this is a comparison of recipes and does not isolate the causal effect of its two trainable backbone blocks. R2 improves on R0 by 4 images (0.67 percentage points accuracy) and 0.625 percentage points macro-F1. It remains 17 correct images below the 528/600 (88%) target. R1 is worse than R0 on both accuracy and macro-F1.

No run reaches 88% accuracy. The metric increase is small and comes from one seed on the same balanced Validation set; it is not evidence of statistical significance or generalization to natural class prevalence, other sites, or detector end-to-end use.

## Per-class metrics and paired regressions

Each class has support 75. Cell values are `precision / recall / F1`; rightmost columns show change in correctly classified images versus R0.

| Class | R0 P / R / F1 | R1 P / R / F1 | R2 P / R / F1 | R1 Δ correct | R2 Δ correct |
|---|---|---|---|---:|---:|
| large_antlered_muntjac | 0.870968 / 0.720000 / 0.788321 | 0.771429 / 0.720000 / 0.744828 | 0.883333 / 0.706667 / 0.785185 | 0 | -1 |
| annamite_striped_rabbit | 0.845238 / 0.946667 / 0.893082 | 0.851852 / 0.920000 / 0.884615 | 0.887500 / 0.946667 / 0.916129 | -2 | 0 |
| sambar | 0.786667 / 0.786667 / 0.786667 | 0.797101 / 0.733333 / 0.763889 | 0.818182 / 0.840000 / 0.828947 | **-4** | +4 |
| chinese_serow | 0.918919 / 0.906667 / 0.912752 | 0.883117 / 0.906667 / 0.894737 | 0.907895 / 0.920000 / 0.913907 | 0 | +1 |
| common_palm_civet | 0.820513 / 0.853333 / 0.836601 | 0.750000 / 0.880000 / 0.809816 | 0.861111 / 0.826667 / 0.843537 | +2 | -2 |
| masked_palm_civet | 0.835821 / 0.746667 / 0.788732 | 0.848485 / 0.746667 / 0.794326 | 0.770270 / 0.760000 / 0.765101 | 0 | +1 |
| silver_pheasant | 0.972973 / 0.960000 / 0.966443 | 0.973333 / 0.973333 / 0.973333 | 0.935065 / 0.960000 / 0.947368 | +1 | 0 |
| eurasian_wild_pig | 0.732558 / 0.840000 / 0.782609 | 0.810811 / 0.800000 / 0.805369 | 0.761905 / 0.853333 / 0.805031 | -3 | +1 |

Paired by exact image IDs:

- **R1:** 8 wrong→correct and 14 correct→wrong; 39 predictions changed. Sambar loses 4 correct images, and R1 macro-F1 is below R0. This fails the protocol’s recipe-winner criterion.
- **R2:** 12 wrong→correct and 8 correct→wrong; 34 predictions changed. Net is +4 correct. No class loses 4 or more correct images, though muntjac loses 1 and common palm civet loses 2. The change is not uniformly beneficial.
- Common↔masked civet confusion counts (both directions summed): R0 13, R1 16, R2 15. For muntjac↔sambar: R0 12, R1 16, R2 13. R2 reduces the second pair’s combined errors by one but increases civet-pair errors by two.

Full 8×8 confusion matrices, per-class values at full precision, paired image IDs, package inventory, and calculations are in [the machine-readable acceptance evidence](../../outputs/tv2_w6/independent_acceptance_20261106/acceptance_evidence.json) and [artifact audit](../../outputs/tv2_w6/independent_acceptance_20261106/artifact_audit.json).

## Runtime replay and usage

Producer runtime is Python 3.12.10, torch 2.6.0+cu124, torchvision 0.21.0+cu124, Windows 11, RTX 4060 Laptop GPU, FP32, AMP=false, TF32=false, deterministic algorithms enabled. This workspace exposes Python 3.14.3 and torch 2.13.0+cpu; `torch.cuda.is_available()` is false (although `nvidia-smi` sees an RTX 4060 Laptop GPU). It does not have the pinned Python/Torch CUDA environment. Therefore no checkpoint inference was run, no cross-device or numerical tolerance was introduced, and **TV2 replay GPU usage remains 0.0/2.0 hours**. TV3’s producer reload is not independent TV2 replay.

Producer accounting records two official attempts: R1 0.0712013161 GPU-hours; R2 0.8294758375 GPU-hours. Preparation/smoke is 0.0050373665 hours. Total TV3 measured use is 0.9057145201/12 hours, leaving 11.0942854799 hours. Both individual attempts are within the two-hour limit. Reload sessions are listed separately in the usage evidence.

## Checks and next step

- Registry/schema validator: `VALID`, protocol `APPROVED`; this locked local registry remains the protocol snapshot with zero recorded official attempts. The result package’s registry records the two completed producer attempts. Recipe selection remains pending and no result was inserted into the frozen protocol registry in this acceptance review.
- TV2 W6 unit tests: **51 PASS / 0 FAIL**.
- W5 focused regression suites: **70 PASS / 0 FAIL** (32 + 9 + 13 + 11 + 5).
- `git diff --check`: PASS at review time.
- No training, official Test opening, or Test inference was performed. Frozen configs, TV3 source, protocol lock, and W1–W5 remain unchanged.
- Next: TV3/TV2 must make the pinned Python 3.12.10 + torch 2.6.0+cu124 CUDA runtime available for a fresh-process independent TV2 replay of R1 and R2. Compare logits, crop scores, image scores, predictions and metrics exactly. Then record TV2 recipe selection only after replay and regression gates are complete. TV4 adapter verification remains a separate requirement before any demo-default change.

Evidence directory: `outputs/tv2_w6/independent_acceptance_20261106/`. Machine-readable summary SHA-256: `7afede0afc9e1319aa9216bab1f11e38a85be289a21c4efdfc2879f6762427ad`.

## Addendum — independent replay completed (2026-11-06)

This addendum supersedes the earlier `MODEL_REPLAY_PENDING` and `PENDING_MODEL_REPLAY` entries above. TV2 reconstructed the requested Python 3.12.10 / torch 2.6.0+cu124 CUDA runtime in an isolated environment, verified Validation image bytes and RGB pixels, then independently replayed R1 and R2 in new Python processes. The interpreter build string differed from TV3's build tag/date; the pinned Python/package versions, hardware, deterministic/precision settings matched, and the exact comparisons passed.

**MODEL_REPLAY: PASS** — R1 and R2 each matched producer crop logits (5,440 values), crop probabilities (5,440), image probabilities (4,800), predicted classes and metrics exactly; mismatch counts and maximum absolute deltas were zero. TV2 replay usage, including a first successful R1 execution whose console encoding failed only after inference and a clean-log R1 rerun, totals 0.1177512729/2 GPU-hours.

**RECIPE_SELECTION: R2** — R2 scored 0.850650853041619 macro-F1 and 511/600 accuracy-correct images, ahead of R0 and R1 on the selection criteria. Its gain is modest (+4 correct images; +0.0062500251 macro-F1) and remains 17 correct images below the 88% target. Per-class and paired regressions are documented in [the replay decision report](TV2_W6_INDEPENDENT_MODEL_REPLAY_2026-11-06.md). The report records R2 as the seed-42 choice; it does not change the demo default. TV4 adapter review remains pending, R3/R4 are not automatically approved, and R5/R6 remain conditional while TV1 data review is pending.

The dynamic registry fields `replay_attempts` and `recipe_selection` now point to this evidence. Protocol approvals, frozen config/source bindings, W1–W5 and Official Test status were not changed. The registry validator is `VALID / APPROVED`, measured TV2 replay usage is 0.1177512729 hours, W6 tests are 51/51 PASS, and W5 focused regression tests are 70/70 PASS.
