# TV2 W3 – TEMPORARY HANDOFF README

## 1. General Information

Camera-Trap-ML; TV2 phụ trách B1 full-image fine-tuning, validation, checkpoint và review B2.
Ngày cập nhật: **18/10/2026 – CONTINUATION_02**. Branch: `feat/baseline`.
Trạng thái: **W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**.
Commit đầu lượt: `1b71b2d9529055911fa2f91f10a5d25eb096b9f2`.
Commit chứa bản bàn giao này: `git log -1 --format=%H -- reports/tv2/README_W3_HANDOFF_TEMP.md`.
SHA cuối và push verification ghi trong snapshot local `git_verification.json`.
Main: `468d81f7272a4497d8b54a53a3651fd13c6dfbc2`; TV1: `7e9b1949f10126fbcfa83fa12baeca488b6aeab3`;
TV3: `d08eba7fffbfb6ecc813de8522fb4d58cd8ed904`.
[PR4](https://github.com/huyryan220806/Camera-Trap-ML/pull/4) vẫn Draft; không tạo PR mới/merge.

## 2. Completed Work

| Task | Status | Evidence | Notes |
|---|---|---|---|
| TV1 remote bundle và integrity train/val | PASS | metadata_preflight.json; snapshot.json; tv1_scoped_validator.json | Đúng SHA, không còn blocker “TV1 chưa push” |
| Provenance/class map/nguồn/B1/B2, đủ box, rounding, parent IDs, leakage/accounting | PASS | Adapter + scoped validator chính thức TV1 | 2.800 train images / 3.125 train crops; 600 validation images / 680 validation crops; 8 classes |
| Khôi phục cache ảnh và full preflight | PASS | image_recovery.json; real_preflight.json | 3.400/3.400 ảnh, byte/pixel hash, decode/dimensions/format/mode đạt; không test |
| Adapter native provenance | DONE | src/training/tv1_handoff.py; b1_gate.py | Không tạo status=FROZEN hoặc box_review_passed giả; giữ fail-closed |
| Protocol nhóm | AGREED BY USER FOR TEAM | W3_PROTOCOL_AGREEMENT_2026-10-18.json | Người dùng xác nhận thông số cụ thể; không mạo nhận chữ ký/review riêng TV3 |
| Regression | PASS | tests_cuda_env.txt | 87/87; 86/86 trước bổ sung test xác nhận nhóm; logs cũ giữ nguyên |
| Synthetic smoke/reload | PASS | smoke.txt; tests_cuda_env.txt | Không là metric/checkpoint B1 chính thức |
| CUDA hardware/model smoke | PASS | cuda_readiness.json | Batch32 ảnh train thật, forward/backward/step, không pretrained/epoch/checkpoint |
| B0/W2 và dữ liệu TV1 | PASS | integrity_final.json | Hash 53 file được bảo vệ + snapshot TV1 không đổi |

Evidence mới: `reports/tv2/w3_evidence/continuation_02/`.
Provenance SHA-256: `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`.
Snapshot dữ liệu/code TV1 local: `outputs/tv2_w3/tv1_7e9b194/`; byte-identical với Git.
Không copy JSONL test hoặc manifest chứa cả test. Full validator CLI TV1 đọc mọi split,
nên chỉ đọc `--help`, chạy `select`/`audit` chính thức trên train/val và kiểm độc lập
bằng preflight TV2. Leakage với test dựa trên **attestation tổng hợp đã commit của TV1**,
không tuyên bố tự kiểm lại test. Near-duplicate/perceptual hash chưa được kiểm.

## 3. Pending and Blocked Tasks

| Task | Status | Reason | Owner | Evidence | Required next step |
|---|---|---|---|---|---|
| GPU budget | PENDING | Chưa có thời lượng/khung giờ được người dùng xác nhận; booking trống | Người dùng/chủ GPU + TV2 | agreement budget_reference=null; gpu_schedule.txt | Xác nhận thời lượng/khung giờ; ghi budget thật vào agreement/config trước train |
| Official environment freeze | PENDING | Venv CUDA chạy được nhưng khác Python/common pins cũ | TV2 + nhóm | cuda_readiness.json; cuda_pinned_environment_check.txt; cuda_pip_freeze.txt | Chấp nhận/khóa environment CUDA đã test hoặc chuẩn hóa môi trường đích; không coi checker ghim là PASS |
| B1 official training | BLOCKED | Budget/environment freeze chưa hoàn tất | TV2 | official_gate_after_agreement.txt; B1_run01 chưa tồn tại | Kiểm lại toàn bộ gate, commit code/config, run ID mới, rồi train |
| B1 validation/checkpoint/URL | NOT TESTED / NOT AVAILABLE | Chưa có official training | TV2 | Không có official run/artifact | Validate fresh model/process, hash/size, reload, chia sẻ URL thật sau run |
| B2 implementation alignment | PENDING TV3 FIX / REVIEW | TV3 vẫn d08eba7, code/config chưa theo protocol đã xác nhận | TV3 sửa; TV2 review | TV2_REVIEW_TV3_W3.md | Đồng bộ SGD/StepLR/50/patience7/transforms/no-dropout/FP32, sampling theo ảnh; sửa path/provenance/run/reload |
| B1/B2 comparison | PENDING | Chưa có hai kết quả thật/tái lập | TV2 + TV3 | TV2_W3_COMPARISON.md | Cùng parent IDs/val/class map, settings/compute đã kiểm soát, aggregation cấp ảnh |
| Review/merge | PENDING | Chưa có review độc lập; PR4 Draft, mergeable=false lúc audit | Reviewer/người tích hợp | PR4 | Review artifact thật; không tự nghiệm thu hoặc merge |

TV1 đã được xác minh; ảnh train/val đã đầy đủ. Protocol hiện không còn thiếu lựa chọn
optimizer/scheduler: người dùng đã xác nhận SGD/StepLR như chi tiết trong agreement.
TV3 cần triển khai đúng quyết định đó; xác nhận protocol không phải nghiệm thu code B2.

## 4. Official Training Gate

- [x] Native schema/provenance/commit và actual train/val hashes verified.
- [x] 3.400 source images, full preflight PASS.
- [x] Regression tests và synthetic reload PASS.
- [x] Protocol cụ thể được người dùng xác nhận cho nhóm; evidence đã lưu.
- [x] CUDA forward/backward batch32 PASS trong venv riêng.
- [ ] Training budget/window confirmed.
- [ ] Official environment accepted/frozen; pinned checker hiện FAIL.
- [ ] Final config/budget binding committed và gate chung PASS.
- [x] B1_run01 chưa tồn tại lúc audit; phải kiểm lại ngay trước chạy.

Thiếu điều kiện bắt buộc: không train. Không tự đổi batch/LR/epochs khi OOM hoặc thiếu thời gian.

## 5. Resume Instructions

Venv CUDA local: `outputs/tv2_w3/venv_cuda/Scripts/python.exe`, Python 3.11.9,
torch 2.8.0+cu126, torchvision 0.23.0+cu126, CUDA 12.6.
Environment cũ giữ nguyên. Exact installed packages: `cuda_pip_freeze.txt`.
Nguồn cài cặp torch/torchvision: [PyTorch official versions](https://pytorch.org/get-started/previous-versions/#v280).
Venv này là candidate đã test; khác Python3.12/NumPy2.5.3/Matplotlib3.11.2 trong bộ ghim cũ.

```powershell
$py = 'outputs/tv2_w3/venv_cuda/Scripts/python.exe'
$env:MPLBACKEND = 'Agg'
# Chỉ tạo snapshot trên máy mới hoặc khi chưa có đường dẫn này; không ghi đè:
& $py -B -X utf8 scripts/prepare_tv1_snapshot.py --commit 7e9b1949f10126fbcfa83fa12baeca488b6aeab3 --output outputs/tv2_w3/tv1_7e9b194
& $py -B -X utf8 scripts/preflight_b1.py --help
& $py -B -X utf8 scripts/preflight_b1.py --config configs/b1_comparison_v1.pending.yaml --report outputs/tv2_w3/preflight_next.json
& $py -B -X utf8 -m unittest discover -s tests -v
& $py -B -X utf8 scripts/train_b1.py --help
& $py -B -X utf8 scripts/validate_b1.py --help
# Chỉ sau tất cả gate PASS và code/config được commit:
& $py -B -X utf8 scripts/train_b1.py --config configs/b1_comparison_v1.pending.yaml
```

`preflight_next.json` phải là file mới. Lệnh prepare snapshot từ chối ghi đè; trên máy
hiện tại **bỏ qua bước prepare** vì snapshot đã có. Máy mới cần khôi phục đúng ảnh
train/val theo `quality.local_path`, URL SWG và hashes; không chạy trình khôi phục mọi
split nếu nó mở test. Bản local hiện tại có đủ ảnh, không cần tải lại.
Config `.pending.yaml` chứa protocol đã xác nhận nhưng còn chờ budget/environment freeze.
`configs/b1.yaml` giữ nguyên bản đề xuất lịch sử, không dùng nhầm cho dữ liệu mới.
Trước train, ghi approval/budget thật, cập nhật immutable receipt SHA/ref rồi commit;
không điền booking hoặc chữ ký giả. Pipeline chưa hỗ trợ resume epoch: run lỗi phải giữ
nguyên, lần sau dùng ID mới.

Sau run thật, dùng `validate_b1.py --checkpoint <best_model.pth> --sha256 <hash-thật>`;
ghi reload report mới ngoài run, kiểm predictions/logits/metrics bằng model/process mới.
Chỉ công bố URL checkpoint sau khi tải kiểm hash độc lập; không commit weights.

## 6. Important Files

- [Protocol đã xác nhận](W3_PROTOCOL_AGREEMENT_2026-10-18.json).
- [Protocol và các khác biệt B2](TV2_W3_PROTOCOL.md).
- [Báo cáo continuation 02](TV2_W3_CONTINUATION_02_REPORT.md).
- [Review TV1](TV2_REVIEW_TV1_W3.md), [review TV3](TV2_REVIEW_TV3_W3.md).
- `configs/b1_comparison_v1.pending.yaml`; `src/training/tv1_handoff.py`; `src/training/b1_gate.py`.
- `scripts/prepare_tv1_snapshot.py`; `scripts/preflight_b1.py`; `scripts/train_b1.py`; `scripts/validate_b1.py`.
- `tests/test_tv1_handoff.py`; `tests/test_b1.py`.
- Local copy: `LOCAL_REVIEW_RESULTS/W3/CONTINUATION_02/FILE_MANIFEST.json` (không lên Git).

## 7. What Must Not Be Changed

B0_run01/checkpoint/W2 metrics, split/class IDs/byte manifest TV1, test isolation,
nhánh thành viên khác, run cũ, snapshot cũ và file nguồn khi copy. Không merge/rebase,
reset, force push; không push ảnh/weights/local review.

## 8. Final Temporary Status

**W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**.
**B1 CHECKPOINT: NOT AVAILABLE – TRAINING BLOCKED**.
**B1/B2 COMPARISON PENDING – TV3**. Chưa có nghiệm thu độc lập W3-02.
