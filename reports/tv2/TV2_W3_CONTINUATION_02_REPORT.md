# TV2 W3 – CONTINUATION 02 REPORT

## 1. GitHub

Ngày 18/10/2026. Đọc main trước, fetch toàn bộ refs.
Main `468d81f7272a4497d8b54a53a3651fd13c6dfbc2`.
TV1 `feat/metadata-split`: `7e9b1949f10126fbcfa83fa12baeca488b6aeab3`.
TV2 starting HEAD `1b71b2d9529055911fa2f91f10a5d25eb096b9f2`.
TV3 `d08eba7fffbfb6ecc813de8522fb4d58cd8ed904`; TV4 `f65b936ef36a93ae4cf804e7a65d0ad436ec6171`.
PR4 open/Draft, mergeable=false lúc audit; không tạo mới/merge.
Ending SHA xác định bằng `git log -1 --format=%H -- reports/tv2/TV2_W3_CONTINUATION_02_REPORT.md`;
local/remote SHA và push result trong snapshot `git_verification.json` sau push.

## 2. W3-01 Verification

**W3-01 REMOTE BUNDLE FOUND; W3-01 INTEGRITY VERIFIED (train/validation scope)**.
Path `data/processed/comparison_v1/`, version `comparison_v1`.
Provenance SHA-256 `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`.
Class map SHA-256 `122c3a8c6b297c1d63c3b18db91cf6b3f279a2f979e6b3e77824dbdd086fc58e`.
2.800 train images / 3.125 train crops; 600 validation images / 680 validation crops; 8 classes. Đếm lại từ file thật, không hard-code gate theo các số này.
B1/B2 parent IDs/labels/splits, đủ annotation/boxes, round-half-even/clip/min8/padding0,
weight1/N, source/class map và accepted/excluded accounting PASS; excluded=0.
Train/val: 2.785 chuỗi, 560 địa điểm; overlap ID/path/sequence/location/pixel=0.
3.400/3.400 ảnh train/val khôi phục từ URL SWG TV1, byte/pixel hash và decode/dimensions
PASS; tổng byte nguồn **5.282.909.005**. Không sửa manifest, không chọn lại dữ liệu.
**REAL DATA PREFLIGHT PASS**; evidence `real_preflight.json`, `image_recovery.json`.
Các JSONL test/mixed-split không được mở/copy. All-split leakage dựa trên attestation
TV1 đã commit. Full validator CLI đọc cả test nên không chạy; đã đọc help và chạy
các hàm chính thức select/audit trên train/val, đối chiếu exact views PASS.
Không khẳng định đã kiểm near-duplicates hoặc box review bởi chuyên gia.

## 3. Protocol

**AGREED BY USER FOR TEAM**: người dùng xác nhận “Xác nhận cấu hình trên cho nhóm”.
Evidence: [agreement](W3_PROTOCOL_AGREEMENT_2026-10-18.json), dẫn chiếu đề cương main
và câu xác nhận cụ thể trong chat. Không mạo nhận chữ ký độc lập TV3.
ResNet18 IMAGENET1K_V1, full fine-tune/no-dropout/FP32, seed42; SGD .001/.9/WD.0001;
StepLR10/gamma.1; batch32; max50 epochs/patience7; transforms mục6;
B2 padding0, mean crop CE trong ảnh rồi mean theo ảnh, mean probability cấp ảnh.
Config B1 gắn native handoff: `configs/b1_comparison_v1.pending.yaml`.
B2 thực tế vẫn AdamW .0001/cosine/15/patience5, dropout.2, AMP, batching crop/drop_last;
cần TV3 đồng bộ. Approval protocol không phải code acceptance.
Budget approval: **PENDING**; chưa có duration/window hay booking confirmed.

## 4. Environment

Venv mới độc lập: `outputs/tv2_w3/venv_cuda/`.
Python 3.11.9; PyTorch 2.8.0+cu126; torchvision 0.23.0+cu126; CUDA 12.6.
GPU NVIDIA GeForce RTX 4060 Laptop GPU; VRAM 8585216000 byte.
Forward/backward/optimizer-step trên batch32 ảnh train thật: **PASS**.
Peak allocated: 848898560 byte; probe 2.140 giây.
Đây là hardware probe random-init, không epoch/validation metric/checkpoint chính thức.
pip check PASS; full regression 87/87 PASS trong venv CUDA.
Pinned environment checker **FAIL**: Python3.11.9 khác3.12; NumPy2.4.6 khác2.5.3;
Matplotlib3.10.9 khác3.11.2. Cần chấp nhận/khóa môi trường riêng hoặc chuẩn hóa bộ ghim
trước official run; không sửa requirements chung để tạo PASS.
Môi trường Python3.14/torchCPU cũ giữ nguyên.

## 5. B1 Training

Executed: **NO**. Run ID dự kiến B1_run01 chưa tạo; epochs=0.
Best epoch/runtime/peak GPU memory official: N/A. CUDA probe không tính là training B1.
Code/config được commit để bàn giao; official gate vẫn chặn budget chưa xác nhận.

## 6. B1 Validation

Macro-F1/Macro-Precision/Macro-Recall/Accuracy/per-class/confusion matrix/curves:
**N/A — NOT TESTED on an official B1 run**. Không dùng synthetic smoke làm kết quả.

## 7. Checkpoint

Path/size/SHA-256/download URL official: N/A. Official reload: NOT TESTED.
Synthetic checkpoint save/load: PASS, artifacts tạm đã xóa.
**B1 CHECKPOINT: NOT AVAILABLE – TRAINING BLOCKED**.

## 8. TV3 Cross-review

Commit vẫn d08eba7; không có fix commit mới. Đã đọc lại config/loader/training.
Loader hỗ trợ bbox_xyxy/quality.local_path nhưng script ghép ROOT/comparison_v1 sai;
hash check mặc định false; freeze checks chưa chặt; early stopping config chưa thi hành;
best_epoch reporting sai; last weights gắn best_metrics; chưa run immutability/fresh
reload/provenance/GPU evidence đủ. Sampling/loss/drop_last cần khớp protocol nhóm.
9/9 tests là kết quả lịch sử, không chạy lại TV3 khi commit không đổi.
**PENDING TV3 FIX / REVIEW**; không sửa code/nhánh TV3.

## 9. B1/B2 Comparison

Dữ liệu chung đã xác minh; quyết định protocol đã có, implementation B2 chưa khớp.
Chưa có metric/checkpoint validation thật của hai run. **B1/B2 COMPARISON PENDING – TV3**.
Không so B0 pilot khác membership như cùng thí nghiệm; không tạo số liệu B2.

## 10. Temporary Handoff README

Đã cập nhật [README hiện tại](README_W3_HANDOFF_TEMP.md), xóa blocker TV1 chưa push và
cache thiếu khỏi trạng thái mới. Có owner/evidence/required next step và lệnh tiếp tục.

| Task | Status | Reason | Owner | Evidence | Required next step |
|---|---|---|---|---|---|
| GPU budget | PENDING | Chưa có thời lượng/khung giờ được người dùng xác nhận; booking trống | Người dùng/chủ GPU + TV2 | agreement budget_reference=null; gpu_schedule.txt | Xác nhận thời lượng/khung giờ; ghi budget thật vào agreement/config trước train |
| Official environment freeze | PENDING | Venv CUDA chạy được nhưng khác Python/common pins cũ | TV2 + nhóm | cuda_readiness.json; cuda_pinned_environment_check.txt; cuda_pip_freeze.txt | Chấp nhận/khóa environment CUDA đã test hoặc chuẩn hóa môi trường đích; không coi checker ghim là PASS |
| B1 official training | BLOCKED | Budget/environment freeze chưa hoàn tất | TV2 | official_gate_after_agreement.txt; B1_run01 chưa tồn tại | Kiểm lại toàn bộ gate, commit code/config, run ID mới, rồi train |
| B1 validation/checkpoint/URL | NOT TESTED / NOT AVAILABLE | Chưa có official training | TV2 | Không có official run/artifact | Validate fresh model/process, hash/size, reload, chia sẻ URL thật sau run |
| B2 implementation alignment | PENDING TV3 FIX / REVIEW | TV3 vẫn d08eba7, code/config chưa theo protocol đã xác nhận | TV3 sửa; TV2 review | TV2_REVIEW_TV3_W3.md | Đồng bộ SGD/StepLR/50/patience7/transforms/no-dropout/FP32, sampling theo ảnh; sửa path/provenance/run/reload |
| B1/B2 comparison | PENDING | Chưa có hai kết quả thật/tái lập | TV2 + TV3 | TV2_W3_COMPARISON.md | Cùng parent IDs/val/class map, settings/compute đã kiểm soát, aggregation cấp ảnh |
| Review/merge | PENDING | Chưa có review độc lập; PR4 Draft, mergeable=false lúc audit | Reviewer/người tích hợp | PR4 | Review artifact thật; không tự nghiệm thu hoặc merge |

## 11. Local Results

Snapshot mới: `LOCAL_REVIEW_RESULTS/W3/CONTINUATION_02/`.
Chỉ copy, SHA-256/size từng cặp trong FILE_MANIFEST.json; số copy và kết quả cuối ở
manifest và phản hồi bàn giao. File nguồn/snapshot cũ không bị sửa bởi thao tác copy.
Không copy toàn bộ ảnh/weights. **Committed: NO; Pushed: NO**.

## 12. Git and Regression

Branch duy nhất sửa/commit/push: feat/baseline. Không merge/rebase/force push.
87/87 tests PASS trong venv CUDA; 86/86 PASS trước thêm test approval budget.
53 protected files giữ nguyên SHA/size, gồm checkpoint B0 44.837.567 byte,
SHA `d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680`.
Source TV1 snapshot giữ nguyên; file cá nhân không stage. B0 modified: NO.
Other branches modified: NO. Exact commit/push evidence ghi sau push trong local
snapshot git_verification.json để tránh tự tham chiếu hash commit.

## 13. Final Status

**W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**.
Data và CUDA đã tiến triển thật; còn budget/environment freeze, B2 fixes và artifact
training/validation/review. Không tuyên bố nghiệm thu W3-02.
