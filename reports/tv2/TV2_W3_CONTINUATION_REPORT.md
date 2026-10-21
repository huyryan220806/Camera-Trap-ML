# TV2 W3 CONTINUATION & TEMPORARY HANDOFF REPORT

## 1. Repository

- Current branch: `feat/baseline`.
- Starting commit: `881d143510d23e3862e3748ed2b7cb707aab7dc5` (HEAD=remote lúc bắt đầu).
- Ending commit: commit chứa report này; lấy bằng
  `git log -1 --format=%H -- reports/tv2/TV2_W3_CONTINUATION_REPORT.md`.
  SHA sau push được ghi riêng trong snapshot local `git_verification.json`
  và phản hồi bàn giao để tránh tự tham chiếu hash trong commit.
- Main inspected: `468d81f7272a4497d8b54a53a3651fd13c6dfbc2`.
- TV1 `origin/feat/metadata-split`: cùng SHA main.
- TV3 `origin/feat/crop-classifier`: `d08eba7fffbfb6ecc813de8522fb4d58cd8ed904`.
- Date: 16/10/2026; audit UTC ghi trong evidence.
- Draft PR4 đã tồn tại, open/draft, mergeable=false. Không tạo PR mới/merge PR.

## 2. Completed Tasks

| Task | Evidence | Status |
|---|---|---|
| Read main → TV2 → TV1 → TV3, fetch lại | w3_evidence/continuation_01/remote.json | DONE |
| Đối chiếu full completed-work và review P1 | TV2_W3_COMPLETED_WORK.md; review_TV2_W3_2026-10-16.md của người dùng | DONE |
| Regression P1 và bảo vệ W2 | tests.txt; integrity.json | DONE |
| CPU smoke/reload, CLI và blocked official gate | smoke.txt; train_help.txt; validate_help.txt; official_gate.txt | DONE |
| Audit Python/dependencies/GPU/disk | environment.txt; nvidia_smi.txt; environment_check.txt | DONE; official environment FAIL |
| Bảng Current B1 / Current B2 / Proposed Agreement / Evidence / Status | TV2_W3_PROTOCOL.md | DONE; approval PENDING |
| README bàn giao tạm, 8 mục bắt buộc | README_W3_HANDOFF_TEMP.md | DONE |
| Cập nhật report/review/checkpoint/comparison | Các file TV2_W3*.md và TV2_REVIEW_*_W3.md | DONE |
| Snapshot tiếp theo, copy + hash, không ghi đè cũ | LOCAL_REVIEW_RESULTS/W3/CONTINUATION_01/FILE_MANIFEST.json | Kết quả copy ghi trong manifest sau khi tài liệu hoàn tất |

Không sửa src/tests/config trong continuation này: P1 đã có từ bf9aae4 và
regression vẫn đạt. Root README không đổi để tránh tăng conflict PR hiện có.

## 3. P1 Verification

- B1 gate: **P1 CODE FIX VERIFIED LOCALLY**.
- Regression: 78/78 PASS, 0 failure/error/skip, 29.998 giây.
- Multi-crop: fixture có ảnh hai box; B1 projection được đối chiếu với source;
  B2 phải đủ parent/annotation/box, `bbox_xyxy`, URL và hash ảnh nguồn.
- Provenance: committed receipt/hash vẫn bắt buộc; tests hash/mapping/leakage
  và ảnh nguồn sai đều từ chối. Official gate không bị bypass.
- Không cần JPEG crop, legacy `source_url` hay crop `file_path`.
- Weighting: gate kiểm 1/N; chưa đồng nghĩa TV3 training sampler/compute đã được duyệt.
- Reviewer acceptance: **PENDING INDEPENDENT REVIEW**, không ghi ACCEPTED.
- **REAL COMPARISON_V1 VERIFICATION PENDING**. Literal/schema và padding/rounding
  cần đối chiếu lại bundle TV1 thật trước official run.

## 4. TV1 W3-01

- Official W3 commit available: NO trên refs đã fetch; W2 v2 có trên main.
- Frozen comparison manifest available: NO.
- Official SHA-256 verified: NOT TESTED; không lấy hash snapshot chưa commit làm approval.
- Preflight result: NOT TESTED trên dữ liệu thật; CLI blocked trước model/run.
- Status: **BLOCKED – TV1 W3-01 OFFICIAL HANDOFF MISSING**.

## 5. B1/B2 Protocol

- Agreement evidence: chưa có; config PROPOSED, receipt/hash/ref/budget null.
- Config alignment: chưa thống nhất SGD/StepLR/50/patience7 so với
  AdamW/cosine/15/patience5, dropout, preprocessing, batch cuối và AMP.
- Loss/image weighting: B1 CE một ảnh; B2 weighted CE theo crop, cần chốt
  grouping/normalization và số update để cân bằng ảnh thực sự.
- Validation aggregation: đề xuất B2 mean probability cấp ảnh, kiểm nhãn nhất quán.
- GPU budget: chưa có booking confirmed hoặc budget_reference.
- Status: **PROPOSED – AWAITING TV3 APPROVAL**.

## 6. B1 Training

- Executed: NO official; chỉ synthetic smoke 2 epoch CPU.
- Official dataset / GPU / best epoch / runtime / peak memory: N/A.
- Official epochs: 0. `experiments/B1_run01` chưa tồn tại.
- Hardware: RTX4060 Laptop, 8188MiB VRAM, driver610.78.
- Runtime: Python3.14.3, torch2.13.0+cpu, torchvision0.28.0+cpu;
  `torch.version.cuda=null`, `cuda_available=false`.
- Workspace free disk tại audit: 380165210112 byte (~354GiB).
- Ảnh nguồn swg_pilot_v2 và bundle comparison_v1 chưa tồn tại local.
- Status: **BLOCKED**, có phần cứng nhưng chưa có runtime/budget/data/protocol hợp lệ.

## 7. B1 Validation

Macro-F1, Macro-Precision, Macro-Recall, Accuracy, per-class metrics,
confusion matrix: **N/A cho official B1**. Status: **NOT TESTED**.
Synthetic metric/logit delta0 chỉ kiểm khả năng reload, không là chất lượng B1.

## 8. Checkpoint

Path, size, SHA-256, download URL: **N/A** cho official B1.
Official reload: NOT TESTED. Status: **B1 CHECKPOINT: NOT AVAILABLE – TRAINING BLOCKED**.
Không upload fixture, không tạo URL giả. Synthetic checkpoint đã xóa sau smoke.

## 9. TV3 Cross-review

- TV3 commit vẫn `d08eba7`, chưa có commit sửa mới sau review.
- Tests: 9/9 snapshot PASS ở lượt trước; không chạy lại trong continuation này.
- Đã đọc lại config/model/training/evaluator hiện tại. Lỗi path/preflight,
  patience chưa thi hành, best_epoch, last weights gắn best metrics, run
  protection, provenance/reload và dữ liệu còn nguyên.
- Bổ sung lưu ý train epoch loss averaging và ảnh nhiều crop trong batching.
- Status: **PENDING TV3 FIX / REVIEW**; acceptance vẫn BLOCKED/CODE REVIEW FAIL.

## 10. Remaining Blockers

| Blocker | Owner | Evidence | Required action | Unblock condition |
|---|---|---|---|---|
| 01 TV1 data | TV1 | remote.json không có comparison_v1 | Push W3 SHA, bundle, hashes/freeze/QA, source images | TV2 real preflight PASS |
| 02 Protocol | TV2 + TV3 | Hai config khác nhau, receipt null | Duyệt settings/sampling/loss/compute và freeze | Approval thật và configs khớp |
| 03 Environment | TV2 + chủ GPU | CPU torch, checker FAIL, booking trống | Environment riêng phù hợp, CUDA smoke và duyệt budget | Runtime/data GPU smoke PASS |
| 04 B1 train | TV2 | Gate exit1, run chưa tạo | Train khi 01–03 được gỡ | Tất cả training gates PASS |
| 05 Validation/checkpoint | TV2 | Artifact official chưa có | Validate/reload, hash/size/upload kiểm độc lập | Run thật thành công |
| 06 B2 cross-review | TV3 sửa, TV2 review | d08eba7 không đổi | Sửa lỗi và bàn giao evidence/code/model thật | Acceptance criteria đủ |
| 07 Comparison | TV2 + TV3 | Chưa metric thật | So cùng parent IDs, val/classes/protocol | B1+B2 thật, tái lập được |
| 08 Review/merge | Reviewer + người tích hợp | PR4 draft, mergeable=false | Review độc lập và xử lý conflict khi được phép | Approval; không tự nghiệm thu |

## 11. Temporary README

Path: `reports/tv2/README_W3_HANDOFF_TEMP.md`.
Created: YES. Missing tasks/owners/unblock conditions: YES. Resume instructions:
YES, dùng CLI/API hiện có; không có `--preflight`/`--resume` giả.
Status: READY FOR TEAM HANDOFF, không phải nghiệm thu W3-02.

## 12. Local Review Package

Path: `LOCAL_REVIEW_RESULTS/W3/CONTINUATION_01/`.
Copy manifest ghi từng source/copy path, size, SHA trước/sau và hash bản sao.
Không ảnh hàng loạt/checkpoint lớn; copy config/reports/evidence và checkpoint
metadata. Snapshot cũ không bị ghi đè. Số copy và kết quả cuối ghi trong
FILE_MANIFEST.json và phản hồi bàn giao sau copy. File nguồn không thay bởi copy.
Git tracked: NO. Git staged/pushed: NO. `.git/info/exclude` đã có quy tắc ignore.

## 13. Tests

- Previous: 78/78 PASS.
- Current total: **78**; passed **78**; failed **0**; errors **0**; skipped **0**.
- Runtime: 29.998s; command `python -X utf8 -m unittest discover -s tests -v`.
- CPU smoke/reload PASS; official gate expected BLOCKED exit1.
- pip check PASS; result contracts 6/6 PASS; GPU schedule validator PASS với
  **0 booking**, không phải confirmation tài nguyên.
- Pinned environment checker **FAIL** (Python3.14.3≠3.12,
  NumPy2.4.4≠2.5.3, matplotlib3.10.9≠3.11.2); torch/torchvision cũng khác pins.
- Log mới trong `w3_evidence/continuation_01/`; không xóa log cũ.

## 14. W2 Integrity

53 file được hash trước/sau; danh sách thay đổi rỗng.
B0_run01 modified: NO. B0 checkpoint modified: NO. W2 metrics modified: NO.
Checkpoint B0: 44837567 byte,
`d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680`.
Status: PASS. Evidence: `w3_evidence/continuation_01/integrity.json`.

## 15. Git

Chỉ commit/push `feat/baseline`; message
`docs(tv2): update W3 temporary handoff and blockers`.
SHA và kết quả push được ghi sau khi lệnh hoàn tất, trong final handoff và
snapshot local `git_verification.json`. HEAD/origin phải trùng; nếu divergence
thì dừng, không force. Other branches modified: NO. Force push: NO.
Không stage root README, src/tests/config, weights/images/local review hay tài
liệu cá nhân. PR4 được cập nhật tự động qua push; không merge hoặc đổi trạng thái draft.

## 16. Final Status

**W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**.
