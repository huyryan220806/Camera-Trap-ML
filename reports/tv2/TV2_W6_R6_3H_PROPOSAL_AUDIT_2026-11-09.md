# TV2 W6 — Báo Cáo Kiểm Toán Độc Lập Đề Xuất R6 3-Hour & Bản Vá WinError 5

**Tài liệu:** `reports/tv2/TV2_W6_R6_3H_PROPOSAL_AUDIT_2026-11-09.md`  
**Ngày thực hiện:** 2026-11-09  
**Người thực hiện:** TV2 (Baseline & Evaluation)  
**Đối tượng kiểm toán:** Gói đề xuất TV3: `TV3_R6_3h_review_20261109.zip` & `TV3_R6_3h_review_20261109.sha256`  
**Giao thức áp dụng:** `docs/experiment_protocol_w6.md`  
**Phạm vi:** Kiểm toán độc lập, không áp dụng patch, không huấn luyện, không khóa bilateral protocol, không chạy smoke GPU mới.  
**Kết luận thẩm định:** **`READY_FOR_TV2_TECHNICAL_APPROVAL`**

---

## 1. Mục Tiêu & Cơ Sở Thẩm Định

TV3 đệ trình gói đề xuất cấu hình lại cho `R6_attempt01`:
1. Nâng trần thời gian chạy cho riêng `R6_attempt01` từ 2 GPU-giờ lên 3 GPU-giờ (10.800 giây) dựa trên dữ liệu thực nghiệm 14 epoch của R5.
2. Áp dụng bản vá xử lý tranh chấp tệp Windows NTFS (`WinError 5` / `Access is denied`) trong `write_usage()`.
3. Giữ nguyên toàn bộ các giới hạn giao thức: công thức Recipe R2, Seed 43, 20 epoch, tập dữ liệu mở rộng `train_expansion_w6_v1`, trần tổng 12 GPU-giờ toàn W6 và giới hạn tối đa 6 lượt official attempts.

TV2 đã tiến hành kiểm tra độc lập và đối chiếu đa chiều toàn bộ hồ sơ kỹ thuật được cung cấp.

---

## 2. Phần 1 — Xác Minh Tính Toàn Vẹn Của Gói Đề Xuất (Integrity Verification)

- **Đường dẫn tệp nén:** `reports/tv2/w6/tv3/TV3_R6_3h_review_20261109.zip`
- **Kích thước byte:** `66,813` bytes
- **SHA-256 thực tế đo được:**
  `ca6adb28ad773a226a9e3a55f48cbdf0acefd4947796fd338fda33a0e51d7360`
- **SHA-256 trong file `.sha256`:**
  `ca6adb28ad773a226a9e3a55f48cbdf0acefd4947796fd338fda33a0e51d7360`
- **Đối chiếu:** **KHỚP CHÍNH XÁC 100% (PASS)**
- **Bảo toàn bản gốc:** Tệp ZIP và SHA-256 được lưu giữ nguyên trạng tại `reports/tv2/w6/tv3/`. Toàn bộ 24 tệp bên trong đã được giải nén vào thư mục kiểm toán cách ly `reports/tv2/w6_evidence/r6_3h_review_20261109/`.

---

## 3. Phần 2 — Thẩm Định Giới Hạn Ngân Sách & Lịch Sử Sổ Cái (Budget & Ledger Audit)

### 3.1. Phân Tích Sổ Cái Quyết Toán (`usage.settled.snapshot.json`)
- **Số phiên ghi nhận:** 15 phiên (R1–R6 smoke, R1–R5 official).
- **Mục quyết toán R5:** Session `ec15351642b2459996f105e4a3c4d1b3` đã được quyết toán hợp lệ với biên nhận TV2 `906afe96933297cb6130685cd1db2169a6be0a0fdbb6e96e44271fcd97d148b3` ở mức thời gian thực `6405.300349199999` giây.
- **Tổng thời gian GPU TV3 đã sử dụng:**
  $$t_{\text{used}} = 14618.6070 \text{ giây} \approx 4.060724170 \text{ GPU-giờ}$$
- **Ngân sách GPU TV3 còn lại:**
  $$t_{\text{remain}} = 43200 - 14618.6070 = 28581.3930 \text{ giây} \approx 7.939275830 \text{ GPU-giờ}$$
- **Số lượt official attempts đã dùng:** **5 / 6** (`R1_attempt01`, `R2_attempt01`, `R3_attempt01`, `R4_attempt01`, `R5_attempt01`).
- **Số lượt official attempts còn lại:** **1 lượt duy nhất** (dành cho R6).
- **Trạng thái R6 trong sổ cái:** Không có phiên chạy hay attempt R6 nào được tạo trước khi phê duyệt (`attempts: []`).

### 3.2. Dự Toán GPU Cho R6 (`gpu_estimate.json`)
- Dựa trên nhật ký thực tế 14 epoch của R5 (`train_log.json`):
  - Thời gian trung bình 1 epoch: `449.08` s (~7.48 phút).
  - Epoch chậm nhất (Epoch 3): `579.26` s (~9.65 phút).
  - Dự toán 20 epoch theo mức trung bình: $20 \times 449.08\text{s} = 8.981.60\text{s}$ (~2.495 GPU-giờ).
  - Khoảng đệm an toàn (headroom) với trần 3 giờ (10.800 s): $10.800 - 8.981.6 = 1.818.4$ s (~30.3 phút).
  - Khi R6 tiêu thụ tối đa 3 GPU-giờ, tổng GPU TV3 lũy kế là:
    $$4.0607 + 3.0000 = 7.0607 \text{ GPU-giờ} < 12.0000 \text{ GPU-giờ (vẫn còn dư ~4.939 giờ)}$$
- **Kết luận:** Đề xuất 3 GPU-giờ cho R6 có căn cứ thực nghiệm vững chắc, khả thi về mặt kỹ thuật và hoàn toàn nằm trong trần ngân sách 12 giờ của TV3.

---

## 4. Phần 3 — Kiểm Tra Bản Vá `WinError 5` (File Lock Patch Audit)

TV2 đã rà soát chi tiết mã nguồn `write_usage()` trong `src/training/dino_w6_control.py`:

```python
def write_usage(path, usage, refresh=None):
    delays = (0.05, 0.1, 0.2, 0.4, 0.8)
    for attempt in range(len(delays) + 1):
        try:
            if refresh is not None:
                refresh()
            w5.atomic_json(path, usage)
            return
        except PermissionError as exc:
            if getattr(exc, 'winerror', None) != 5 or attempt == len(delays):
                raise
            time.sleep(delays[attempt])
```

| Tiêu chí an toàn | Kết quả thẩm định | Chi tiết kiểm chứng |
| :--- | :---: | :--- |
| **Giới hạn số lần retry** | **PASS** | Tối đa 5 lần thử lại (tổng cộng 6 lần gọi ghi); tổng thời gian backoff tối đa cố định là $0.05 + 0.1 + 0.2 + 0.4 + 0.8 = 1.55$ giây. |
| **Phạm vi lỗi được retry** | **PASS** | Chỉ retry duy nhất khi `isinstance(exc, PermissionError)` và `exc.winerror == 5`. Mọi mã lỗi khác hoặc `PermissionError` không phải WinError 5 đều bị ném ra ngay lập tức (`raise`). |
| **Không nuốt ngoại lệ** | **PASS** | Khi vượt quá 5 lần retry, hàm re-raise nguyên vẹn `PermissionError`. Không có khối `except ...: pass` hay nuốt lỗi. |
| **Bảo toàn dữ liệu & bằng chứng** | **PASS** | `w5.atomic_json` ghi ra tệp `.tmp` trước khi `os.replace`. Khi `os.replace` thất bại kéo dài, tệp `.tmp` chứa dữ liệu mới nhất được giữ nguyên làm bằng chứng; tệp gốc không bị xóa hay hỏng. |
| **Thời gian retry tính vào GPU** | **PASS** | Hàm `refresh_final_measurement` được truyền vào `refresh` parameter, cập nhật lại `session['seconds'] = time.perf_counter() - started` trước mỗi lần retry. Toàn bộ thời gian `time.sleep` đều được tính vào thời gian sử dụng GPU. |
| **Xử lý vượt ngân sách khi retry** | **PASS** | Nếu trong quá trình retry mà thời gian vượt quá `allowance`, trạng thái tự động chuyển thành `STOPPED` với lỗi `'Budget exceeded during ledger finalization'` và ném `BudgetExceeded`. |
| **Cô lập tác động (Scope Isolation)**| **PASS** | Hàm `w5.atomic_json` trong `src/training/dino_probe.py` được giữ **nguyên vẹn 100%**, đảm bảo tương thích ngược W5. Chỉ có sổ cái W6 (`dino_w6_control.py`) sử dụng lớp bọc `write_usage()`. |

---

## 5. Phần 4 — Thẩm Định Mã Nguồn & Giới Hạn Ngoại Lệ (Amendment Scope Audit)

### 5.1. Khóa Chặt Ngoại Lệ Chỉ Cho `R6_attempt01`
Trong `src/evaluation/w6_validation.py`:
```python
def attempt_budget_hours(registry, run_id, attempt_id, require_approved=True):
    amendment = r6_amendment(registry or {})
    if not amendment or run_id != 'R6':
        return 2
    w5.require(attempt_id == 'R6_attempt01', 'Only R6_attempt01 receives amendment')
    if require_approved:
        w5.require(amendment['status'] == 'APPROVED', 'BLOCKED: R6 amendment pending')
    return 3
```
- **R1–R5:** Luôn luôn trả về `2` GPU-giờ. Không run nào khác có thể mượn ngoại lệ.
- **Lượt R6 khác:** Nếu xuất hiện `R6_attempt02`, hàm lập tức ném `ValueError('Only R6_attempt01 receives amendment')`.
- **Trạng thái phê duyệt:** Khi amendment chưa đạt `APPROVED`, hàm ném `ValueError('BLOCKED: R6 amendment pending')`.

### 5.2. Ràng Buộc Schema Cấp Hệ Thống (`contracts/w6_registry.schema.json`)
Schema JSON được cập nhật với các ràng buộc hằng số (constants) bất biến:
- `"run_id": {"const": "R6"}`
- `"attempt_id": {"const": "R6_attempt01"}`
- `"max_gpu_hours": {"const": 3}`
- `"additionalProperties": false`
- `"approvals": {"required": ["TV2", "TV3"]}`
- Schema từ chối bất kỳ registry nào cố tình áp dụng 3 giờ cho run khác hoặc attempt khác.

---

## 6. Phần 5 — Kiểm Toán Độc Lập Các Bài Test (Independent Test Replay)

### 6.1. Đối Chiếu Nhật Ký Kiểm Thử TV3 (116 Tests)
TV2 đã kiểm tra 4 tệp nhật ký kiểm thử nguyên bản của TV3:
1. `test_dino_w6.log`: 15 tests — **OK** (4.759s).
2. `test_w5_validation.log`: 32 tests — **OK** (2.816s).
3. `test_w6_validation.log`: 51 tests — **OK** (2.168s).
4. `test_r6_amendment.log`: 18 tests — **OK** (1.307s).
- **Tổng cộng:** 116 tests, 0 failures, 0 errors.

### 6.2. Kiểm Thử Tái Lập Độc Lập Của TV2 (Independent Replay)
TV2 đã thiết lập một môi trường overlay cách ly (isolated temporary overlay) trên CPU độc lập, kết hợp mã nguồn repo và các tệp đề xuất, chạy kiểm thử thực tế đối với bộ 18 test đặc thù `tests/test_r6_amendment.py`:

```
test_amendment_approval_and_binding_rejections ... ok
test_evidence_content_and_hash_must_match ... ok
test_exclusive_writer_prevents_second_session ... ok
test_explicit_policy_required_for_three_hours ... ok
test_final_retry_time_is_accounted ... ok
test_full_approved_validator_and_config_cap_binding ... ok
test_only_r6_config_accepts_three ... ok
test_other_errors_not_retried ... ok
test_other_runs_and_attempt_ids_cannot_borrow_exception ... ok
test_permanent_replace_error_retains_old_and_tmp ... ok
test_proposal_retains_history_and_blocks_official ... ok
test_reload_revalidates_amendment_before_inference ... ok
test_reload_shares_attempt_budget ... ok
test_session_stops_with_reserve_and_saves_actual_usage ... ok
test_settlement_is_exactly_once_and_does_not_discard_time ... ok
test_total_twelve_and_six_attempts_remain ... ok
test_transient_replace_retries_preserve_content ... ok
test_unknown_and_duplicate_reconciliation_block ... ok

Ran 18 tests in 1.104s — OK (Returncode 0)
```
- **Xác nhận:** Toàn bộ các ca kiểm thử then chốt (thành công sau lỗi tạm thời, giữ nguyên old/tmp khi lỗi kéo dài, không nuốt lỗi khác, tính thời gian retry vào GPU, chặn đứng việc mượn giờ của run khác) đều đã chạy thật và **PASS 100%**.

---

## 7. Phần 6 — So Sánh Cấu Hình Candidate & Proposal Registry

### 7.1. Cấu Hình Ứng Viên (`configs/w6/tv3/R6.3h.candidate.json`)
Đối chiếu từng trường với cấu hình đã khóa trước đây (`R6.frozen.json`):

| Trường thông số | Giá trị Candidate R6.3h | Giá trị Frozen trước | Đánh giá |
| :--- | :--- | :--- | :---: |
| `recipe` | `R2` | `R2` | Giữ nguyên |
| `seed` | `43` | `43` | Giữ nguyên |
| `dataset` | `train_expansion_w6_v1` | `train_expansion_w6_v1` | Giữ nguyên |
| `dataset_sha256` | `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5` | `a6ac6933062b...` | Giữ nguyên |
| `backbone` | `dinov3_vits16` | `dinov3_vits16` | Giữ nguyên |
| `pretrained_sha256` | `08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d` | `08c60483bc63...` | Giữ nguyên |
| `init_checkpoint_sha256` | `acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3` | `acbe32252af4...` | Giữ nguyên |
| `epochs` / `patience` | `20` / `5` | `20` / `5` | Giữ nguyên |
| `parent_batch` / `crop_microbatch` | `16` / `8` | `16` / `8` | Giữ nguyên |
| `drop_last` | `false` | `false` | Giữ nguyên |
| `loss` / `pooling` | `mean_parent_mean_crop_ce_once` / `x_norm_clstoken` | Giữ nguyên | Giữ nguyên |
| `optimizer` / `lr` | AdamW, backbone `1e-5`, head `1e-4`, weight_decay `0.01` | Giữ nguyên | Giữ nguyên |
| `runtime` settings | FP32, amp: false, tf32: false, deterministic: true, threads: 10/10 | Giữ nguyên | Giữ nguyên |
| **`max_gpu_hours`** | **`3`** | `2` | **Được điều chỉnh có chủ đích** |
| `status` | `DRAFT` | `FROZEN` | Đúng chuẩn (chờ smoke) |
| `smoke_evidence` | `null` | cũ | Đúng chuẩn (chờ smoke mới) |

- **Mã băm Canonical Digest:** `06840272beac00bbdb5cb9cf90eb1c71d5a30dbf3e43631f45fea26ff182ec46`
- **Mã băm Raw File SHA-256:** `3ec1926c89d86bd5ec3638cd932f3dd267456808f1e62c9385c77eae0b17e42a`
- Khớp 100% với định danh trong `experiments/w6/tv3_R6_3h.proposal.json`.

### 7.2. Nguyên Tắc Cập Nhật Smoke Evidence & Khóa Protocol
- Gói đề xuất đặt `source_sha: null` và `smoke_evidence: null` trong candidate config và proposal registry.
- **TV3 không tái sử dụng bằng chứng smoke cũ (`R6_smoke01.json`)** vì mã nguồn đã được sửa đổi và config đã đổi từ 2h sang 3h.
- Quy trình yêu cầu:
  1. Commit mã nguồn đã sửa đổi lên Git để xác định `source_sha`.
  2. TV3 chạy một phiên `train_only_smoke` mới trên mã nguồn đã commit, ghi nhận thời gian vào sổ cái GPU.
  3. Đóng băng cấu hình thành `R6.3h.frozen.json` gắn kết với smoke mới, `source_sha` và `runtime_lock`.
  4. Hai bên TV2 và TV3 ký duyệt biên nhận riêng rẽ trước khi kích hoạt `protocol_status: APPROVED` và `amendment.status = APPROVED`.

---

## 8. Phần 7 — Bảng Tổng Hợp Tiêu Chí Kiểm Định (PASS / FAIL / PENDING)

| Hạng mục kiểm toán | Kết quả | Chi tiết thẩm định |
| :--- | :---: | :--- |
| **1. Toàn vẹn gói ZIP & SHA-256** | **PASS** | SHA-256 khớp tuyệt đối `ca6adb28...`; lưu trữ bảo toàn bản gốc. |
| **2. Đọc & thẩm định source diff** | **PASS** | Kiểm tra chi tiết 8 tệp trong patch; logic chặt chẽ, tối thiểu hóa thay đổi. |
| **3. Giới hạn ngân sách R6 3h** | **PASS** | Ngoại lệ 3h chỉ gán duy nhất cho `R6_attempt01`; R1–R5 giữ 2h. |
| **4. Ngân sách TV3 & Attempt limit** | **PASS** | Trần 12h giữ nguyên; TV3 còn 7.94h (dư 4.94h sau R6); còn đúng 1 attempt (5/6 đã dùng). |
| **5. Trạng thái R5 trong sổ cái** | **PASS** | Sổ cái đã settle khớp receipt TV2 `906afe96...`; R5 giữ `FAILED`, không resume. |
| **6. Cơ chế bản vá WinError 5** | **PASS** | Chỉ retry lỗi WinError 5; tối đa 5 lần (1.55s); không nuốt lỗi; tính thời gian retry vào GPU. |
| **7. Rà soát phạm vi atomic_json** | **PASS** | `w5.atomic_json` gốc giữ nguyên; chỉ bọc `write_usage` cho ledger W6. |
| **8. Kiểm thử độc lập (Test Replay)** | **PASS** | 116 tests của TV3 hợp lệ; TV2 tái lập độc lập 18/18 test amendment đạt 100% PASS. |
| **9. Ràng buộc Config & Registry** | **PASS** | Recipe R2, Seed 43, 20 epoch, dataset, weights, runtime giữ nguyên; chỉ đổi max_gpu_hours = 3. |
| **10. Tính toàn vẹn Binding & Smoke** | **PASS** | Không tái sử dụng smoke cũ; yêu cầu commit source và chạy smoke mới trước khi freeze. |

---

## 9. Kết Luận & Khuyến Nghị Tiếp Theo

### KẾT LUẬN THẨM ĐỊNH: **`READY_FOR_TV2_TECHNICAL_APPROVAL`**

Gói đề xuất `TV3_R6_3h_review_20261109.zip` đáp ứng đầy đủ và nghiêm ngặt mọi tiêu chuẩn kỹ thuật, kế toán ngân sách và an toàn dữ liệu của giao thức W6. Bản vá `WinError 5` xử lý triệt để nguyên nhân gốc gây ra sự cố của R5 mà không tạo ra bất kỳ tác dụng phụ ngoài ý muốn nào.

### Các Bước Kế Tiếp (Theo Quy Trình Giao Thức):
1. **Áp dụng patch mã nguồn:** Cam kết (commit) 5 tệp mã nguồn (`dino_w6.py`, `dino_w6_control.py`, `w6_validation.py`, `scripts/dino_w6.py`, `w6_registry.schema.json`) và test vào nhánh Git để cố định `source_sha`.
2. **Khởi tạo candidate:** Đưa `configs/w6/tv3/R6.3h.candidate.json` và `experiments/w6/tv3_R6_3h.proposal.json` vào nhánh.
3. **Chạy train-only smoke mới:** TV3 thực thi một lượt smoke ngắn trên GPU chính thức với mã nguồn mới, ghi nhận vào `usage.json`.
4. **Đóng băng cấu hình (Freeze):** Tạo `configs/w6/tv3/R6.3h.frozen.json` gắn kết với kết quả smoke mới, `source_sha` và `runtime_lock`.
5. **Ký duyệt kỹ thuật TV2 & TV3:** Lập các biên nhận phê duyệt độc lập (Technical Approval Receipts) cho bản sửa đổi R6 3-hour.
6. **Bilateral Lock:** Hoàn tất khóa giao thức song phương trước khi cấp phép chạy huấn luyện chính thức `R6_attempt01`.
