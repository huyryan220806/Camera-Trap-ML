# TV2 W6 D1 — audit và phần chuẩn bị đánh giá

Ngày04/11/2026, nhánh duy nhất `feat/baseline`. **D1 implementation COMPLETED
ở trạng thái DRAFT; protocol approval PENDING REVIEW; model RESULT PENDING.**
Không đồng nghĩa hoàn tất toàn W6 hoặc được phép chạy official GPU.

## Git và inventory trước sửa

HEAD ban đầu `df31029c2dfa3b87e4efd1b1f210babd89c60cbd`, tracked diff/index
rỗng. Origin `https://github.com/huyryan220806/Camera-Trap-ML.git`.
Local branch chưa có upstream tracking được cấu hình. Fetch lần đầu bị
sandbox chặn `.git/FETCH_HEAD`; fetch có escalation hợp lệ sau đó PASS.
Remote main/baseline/crop-classifier/demo cùng
`cfcf00615847d52fba73ee3e44fe0e6076bb840c`; metadata-split
`11e451071f58146522df20e1890cc6fe6e488eb0` (nội dung W6 tại `c1d2789`).

Đã xem status/HEAD/remote/branch tracking/graph/diff và danh mục code/docs.
Không có AGENTS.md trong repository hoặc các thư mục tổ tiên đã kiểm.
Không tồn tại protocol, registry hoặc code W6 TV2 trước lượt này.
Các file cá nhân, `dino/`, ZIP ảnh mở rộng và cây ảnh giải nén chưa tracked
được giữ nguyên, không stage. Không sửa code TV3/TV4 hay snapshot TV1.

Người dùng đã cho phép riêng fast-forward thuần túy. Đã chạy
`git merge --ff-only origin/feat/baseline`: HEAD→`cfcf006`, không merge commit.
Chênh lệch lịch sử W5 do cập nhật này tách khỏi thay đổi W6; không gọi phần
TV1/TV3/TV4 đã tích hợp là implementation mới của TV2. Publication cuối nằm
trong phản hồi và receipt sau commit, không tự ghi SHA của commit chứa tài liệu.

## Tài liệu đã đọc đầy đủ

Các tài liệu W1–W5 đọc từ `origin/feat/baseline` tại cfcf006 (git show), các
plan/handoff/release W6 đọc từ snapshot TV1 tại11e4510, không checkout nhánh TV1.

| Đường dẫn | Quyết định bắt buộc |
| --- | --- |
| docs/handoff_tv2_w1.md | Macro đủ8 lớp; val chọn checkpoint; Test chỉ sau lock |
| reports/tv2/TV2_W2.md | B0 run cũ bất biến; không so khác population |
| reports/tv2/TV2_W2_REVIEW_FIX.md | Write-once; fail closed provenance trước inference |
| reports/tv2/TV2_W2_CHECKPOINT.md | Hash/size/reload thật; giới hạn lịch sử pixel v1 |
| reports/tv2/TV2_W3.md | Phân biệt snapshot lịch sử PENDING với completion sau đó |
| reports/tv2/TV2_W3_PROTOCOL.md | Parent-image loss; mean crop softmax; seed/protocol freeze |
| reports/tv2/TV2_W3_COMPLETED_WORK.md | B1 đã train/replay; không lặp lại |
| reports/tv2/TV2_W4.md | B2 khóa bằng val; B3 exact reproduction UNRESOLVED |
| reports/tv2/TV2_W4_TEST_EVALUATION.md | Official Test đã chạy; không rerun hoặc dùng tuning |
| reports/tv2/TV2_W4_MODEL_SELECTION_LOCK.json | Không đổi lock/checkpoint hoặc kết luận B3 |
| reports/tv2/TV2_W5.md | Đọc cập nhật tích hợp trước các mục PENDING lịch sử |
| reports/tv2/W5_PROTOCOL.md | APPROVED riêng W5; preprocessing DINO square256 |
| reports/tv2/TV2_W5_DINO_ACCEPTANCE_2026-11-02.md | R0 độc lập PASS; exact replay lịch sử; per-class regression |
| docs/integration_week3.md | Shared metric APIs; GT-crop metric khác demo detector |
| docs/integration_week4.md | Không sửa bằng chứng/log chỉ để làm sạch whitespace |
| docs/integration_week5.md | W5 đã tích hợp, B2 mặc định/DINO opt-in |
| reports/review_w5_2026-11-02/REPORT.md | Review model/adapter/UI đạt; không cần train lại |
| docs/progress_integration_w5_2026-11-03.md | Publication đã xong; gia hạn chưa có hạn mới |
| docs/plans/TV1_W6.md | Train-only expansion; cách ly nghi trùng, quality≠peer review |
| docs/plans/TV2_W6.md | R0–R6, budget, recipe/seed selection, replay |
| docs/plans/TV3_W6.md | CLS+patch và FT2 recipes; TV3 viết trainer W6 riêng |
| docs/plans/TV4_W6.md | Adapter riêng; benchmark train, chỉ đổi model sau gate |
| docs/handoff_tv1_w6.md | ZIP chỉ ảnh giữ; cần pilot cũ và peer review riêng |
| reports/tv1_w6/REPORT.md | 1446giữ/219cách ly; trạng thái pending_TV2 |

Đã đọc code metric W1, evaluator/CLI/contracts/tests W5, các phần DINO liên
quan transform/data gate/cache identity/loss/aggregation/reload/handoff và
tests DINO; inventory source/config/contracts/validators. Tái dùng W5 đúng
ngữ nghĩa, không sửa các module W5 hoặc trainer/adapter đã khóa source hash.

## Bảng đối chiếu quyết định / code / việc W6 / phụ thuộc / bằng chứng

| Quyết định đã khóa | Code đang có | Cần làm W6 | Phụ thuộc | Bằng chứng |
| --- | --- | --- | --- | --- |
| Classmap/split/comparison_v1 | w5_validation.load_frozen_validation | Wrapper W6 kiểm600/680/75lớp | Không đổi TV1 freeze | evidence/r0_audit.json |
| Mean vector softmax, image metric | w5.aggregate/audit_predictions | Saved vector cross-check, paired R0, regression | Predictions thật TV3 | w6_validation + 50tests |
| W5 APPROVED, R0 reference | W5 protocol/checkpoint/predictions | Hash local, không rerun | Không | r0_audit.json |
| B2 default, DINO W5 opt-in | Adapter/UI W5 đã tích hợp | Đề nghị demo sau W6 gates | TV3 model, TV4 adapter | integration_week5.md |
| W4 lock/Test, B3 UNRESOLVED | Code và evidence W4 | Giữ nguyên; không dùng chọn W6 | Không | Git diff so cfcf006 |
| W6 R1/R2 recipes | Chỉ plan; TV3 remote chưa code W6 | DRAFT configs + validator + smoke checklist | Implementation/smoke/source/runtime TV3 | protocol và configs/w6 |
| Max6 attempts, TV3≤12h, TV2≤2h | Chưa registry W6 | Schema/semantic budget/failure accounting | Logs GPU thực sau bàn giao | registry VALID,0attempt |
| Expansion quality≠TV2 acceptance | Snapshot TV1, chưa trên baseline | Read-only metadata/package review riêng | Ảnh cách ly/holdout/visual package | TV2_W6_TV1_DATA_REVIEW.md |

## Đối chiếu cấu hình R1/R2 với plan TV3

| Tham số | R1 proposal | R2 proposal | Kết luận |
| --- | --- | --- | --- |
| Feature/head | CLS384+mean patch384→768→8; không registers | CLS384→8 | MATCH plan |
| Trainable | chỉ head, frozen/eval backbone | last2blocks+final norm+head | MATCH; gradient smoke NOT RUN |
| Init | W5 backbone, head768 mới | W5 backbone+head | Head768 mới là hệ quả shape; chờ TV3 xác nhận init implementation |
| Optimizer | SGD.01/.9/WD.0001 | AdamW1e-5/1e-4/WD.01, no-decay bias/norm | MATCH các giá trị plan |
| Schedule | cosine50/patience7 | warmup2+cosine20/patience5 | MATCH phần đã nêu; warmup endpoints/AdamW betas/eps chưa được plan chỉ rõ |
| Batch/loss | 32parent, crop extraction32/shard128 | 16parent, crop≤8; final denominator actual | MATCH; accumulation/last-batch smoke NOT RUN |
| Augmentation | không, như W5 | horizontal.5; không vertical/random crop | MATCH |
| Cache | 768 riêng đủ identity | disabled | MATCH; code cache/mask chưa có |
| Validation preprocess | square256 bilinear uint8 antialias, RGB/ImageNet | như R1 | MATCH; không dùng B2 CenterCrop224 |
| Runtime/source | FP32, AMP/TF32false; actual versions/source null | như R1 | NOT VERIFIED; cần freeze trước official |

Không phát hiện giá trị cụ thể mâu thuẫn plan; không suy ra implementation
TV3 đã khớp khi mới chỉ có plan. Các khoảng trống trên giữ DRAFT, không tự
điền source commit, smoke, runtime pin hoặc approval của TV3.

## Bằng chứng thực và giới hạn

Local bytes checkpoint R0 khớp SHA/86.851.958byte, protocol W5 khớp
`e47b96f5e576c234e2e48143c7c008df79ca62156cebf6b2bf65c0119a6f133a`;
Train/Val classmap/manifest hashes và counts khớp. Tính lại từ saved W5 image
predictions: accuracy.845, macro-F1.8444008279545706. Đây là artifact re-audit,
không model load/forward/replay mới. Không xác minh lại toàn bộ ảnh cũ trong D1.
Evidence fresh-process replay W5 đọc như bằng chứng lịch sử, không nhận là lượt mới.

W6 tests50PASS; focused regression W5/metrics/contracts/DINO70PASS,0skip.
Synthetic CPU head/gradient/resume tests không phải official model training.
`regression_01.json` có trường `training_performed=false` mang nghĩa không
official training; xem correction trong evidence, không dùng nó phủ nhận CPU
fixture train loops. W6 lần tests_02 lỗi TEMP sandbox, tests_03/04 PASS sau
chuyển TEMP/TMP; không sửa/skip assertions để vượt lỗi môi trường.
Model R1–R6 predictions/checkpoints/metrics: **RESULT PENDING / NOT RUN**.

Nhật ký/lệnh/raw outputs bắt đầu tại
`outputs/tv2_w6/d1_20261104_01/`; phần nhỏ dùng review được lưu ở
`reports/tv2/w6_evidence/d1_20261104_01/`. SHA index và integrity cuối bổ sung
sau các kiểm tra; giữ nguyên mọi log lỗi. Không commit ZIP/weights/ảnh/cache.
Không tạo `TV2_W6.md` như báo cáo kết quả cuối khi chưa có kết quả thật.
