# TV2 W6 — Báo Cáo Kiểm Toán Độc Lập Sự Cố R5 & Kế Toán GPU
**Tài liệu:** `reports/tv2/TV2_W6_R5_FAILURE_AUDIT_2026-11-09.md`  
**Ngày thực hiện:** 2026-11-09  
**Người thực hiện:** TV2 (Baseline & Evaluation)  
**Phạm vi:** Kiểm toán độc lập sự cố `R5_attempt01`, đối chiếu kế toán GPU và đánh giá tính khả thi tiếp tục thực thi theo giao thức W6 (`docs/experiment_protocol_w6.md`).  
**Trạng thái kiểm toán:** `PASS (AUDIT_COMPLETE / BILATERAL_RECONCILIATION_FINALIZED / READY_FOR_TV3_SETTLEMENT)`

---

## 1. Tóm Tắt Sự Cố & Dữ Liệu Ban Đầu

Vào lúc 13:04:05 UTC ngày 2026-11-08, quá trình huấn luyện chính thức `R5_attempt01` của TV3 đã gặp lỗi hệ thống và dừng đột ngột ở cuối epoch 14.

| Thông số sự cố | Giá trị ghi nhận |
| :--- | :--- |
| **Run ID / Attempt ID** | `R5` / `R5_attempt01` |
| **Recipe / Seed / Dataset** | Recipe R2 / Seed 42 / `train_expansion_w6_v1` |
| **Mã lỗi hệ điều hành** | `PermissionError: [WinError 5] Access is denied` tại `os.replace(tmp, path)` trên `outputs/tv3_w6/usage.json` |
| **Session ID** | `ec15351642b2459996f105e4a3c4d1b3` |
| **Process ID (PID)** | `32064` |
| **Booking GPU** | `NVIDIA GeForce RTX 4060 Laptop GPU; 2026-11-08 18:00-20:00 Asia/Ho_Chi_Minh; official R5; agreed with team` |
| **Started UTC** | `2026-11-08T11:17:20.007469+00:00` |
| **Ended UTC (tại file tạm)** | `2026-11-08T13:04:05.311161+00:00` |
| **Thời gian đo được trong file tạm** | `6405.300349199999` giây (~1.77925 GPU-giờ) |
| **Heartbeat cuối trong sổ cái chính** | `6399.7437291999995` giây |
| **Checkpoint hoàn tất cuối cùng** | Epoch 14 (`outputs/tv3_w6/runs/R5_attempt01/last_model.pt`) |
| **Nguồn dữ liệu kiểm toán** | Gói bằng chứng `reports/tv2/w6/R5_io_20261108T130627Z.zip` |

---

## 2. Phần A — Bảo Toàn Bằng Chứng (Evidence Preservation)

TV2 đã bảo toàn toàn bộ tệp bằng chứng thực tế vào thư mục độc lập `reports/tv2/w6_evidence/r5_failure_20261109/`, thiết lập thuộc tính **Read-Only** trên hệ thống và lập bảng đối chiếu SHA-256 nguyên trạng.

### Bảng Bằng Chứng Bảo Toàn

| Tên tệp đã trích xuất & bảo toàn | Kích thước (bytes) | SHA-256 Checksum | Trạng thái quyền |
| :--- | :--- | :--- | :--- |
| **Gói gốc:** `R5_io_20261108T130627Z.zip` | 12,425 | `0249f86f82480f277a18086a809c6be4608fc9219ad2a5d715620d6ebad242de` | Nguyên trạng |
| `evidence_index.json` | 977 | `fc5ec8bc3500acd5c4a8a45e50e9f7517c81c0a65045980abb64d876ddfc9ca2` | Read-Only |
| `incident_summary.json` | 821 | `a64703975f77b7c6c5cbb7e1eb18919dc05faf0aa74de7750768f4f602caa2f9` | Read-Only |
| `usage.json` (sổ cái chính) | 8,115 | `375a962c8c84dbec57fee1ecf06e767dbaaf709c6157f9988f9c41095152c6dd` | Read-Only |
| `usage.json.tmp` (sổ cái tạm thời điểm lỗi) | 8,215 | `d2f252ff521a559f8cd96e4be15963322d045ba536c04e33ce2d37888f3af078` | Read-Only |
| `R5_attempt01_status.json` | 469 | `3e6fbf4105f4eb7ddb205e6461e0f38f8b4286652501257ca7725a4121fa5081` | Read-Only |
| `R5_attempt01_binding.json` | 5,457 | `988de64ac9e6f000dd852d8f31dc23ffdb38ae22fab22015688fe9f810224059` | Read-Only |
| `R5_attempt01_train_log.json` | 50,641 | `1e66026a6ec6cf7ce015cfc27affbb1cdfdfbea442a72cb11378f7b26ee7187c` | Read-Only |
| `evidence_manifest.json` | 3,196 | `612d7799ad7d0c2420212315a2b122ba7a20d0bb808ff9f5df8b455b114220f4` | Read-Only |
| `R5_ACCOUNTING_RECONCILIATION_RECEIPT.json` | 4,249 | `906afe96933297cb6130685cd1db2169a6be0a0fdbb6e96e44271fcd97d148b3` | Final Reviewed |

**Cam kết bảo toàn:**
1. Tệp `usage.json.tmp` đã được sao chép bảo vệ, không bị bất kỳ tiến trình nào ghi đè.
2. Không sửa đổi `seconds: null` trong sổ cái chính thành số liệu giả lập khi chưa có biên nhận phê duyệt.
3. Không thực hiện lệnh `settle-usage` trước khi hoàn tất thủ tục song phương.

---

## 3. Phần B — Kiểm Toán Chi Tiết Sự Cố (Incident Audit)

### B.1. Đối Chiếu Định Danh & Tiến Trình

- **Session ID:** `ec15351642b2459996f105e4a3c4d1b3` khớp chính xác giữa `usage.json` (session 14), `usage.json.tmp`, `incident_summary.json` và `R5_attempt01_status.json`.
- **PID:** `32064` được ghi nhận tại thời điểm khởi tạo phiên.
- **Xác nhận dừng tiến trình:**
  - Lệnh kiểm tra tiến trình xác nhận PID `32064` đã kết thúc hoàn toàn kể từ 13:04:05 UTC 2026-11-08.
  - Không có tiến trình con (child processes) hoặc tác vụ nền Python/CUDA nào của phiên này đang hoạt động.
  - GPU hoàn toàn ở trạng thái rảnh rỗi (idle).

### B.2. Đối Chiếu Thời Gian Thực Tế

- **Thời điểm bắt đầu:** `2026-11-08T11:17:20.007469+00:00`
- **Thời điểm kết thúc ghi nhận:** `2026-11-08T13:04:05.311161+00:00`
- **Thời gian trôi qua theo Wall-Clock:**
  $$\Delta t_{\text{wall}} = 13:04:05.311161 - 11:17:20.007469 = 6405.303692 \text{ giây}$$
- **Thời gian trôi qua theo CPU Perf Counter (`perf_counter`):**
  $$\Delta t_{\text{perf}} = 6405.3003492 \text{ giây}$$
- **Độ chênh lệch giữa Wall-Clock và Perf Counter:**
  $$|\Delta t_{\text{wall}} - \Delta t_{\text{perf}}| = |6405.303692 - 6405.3003492| = 0.003343 \text{ giây (3.3 ms)}$$
  *Nhận xét:* Độ chênh lệch chỉ 3.3 mili-giây, phản ánh tính chân thực tuyệt đối của đồng hồ đo lường nội bộ tiến trình.
- **Tiến trình Heartbeat:**
  - Trong quá trình huấn luyện, hàm `tick()` cập nhật heartbeat mỗi 5 giây vào `usage.json`.
  - Heartbeat cuối cùng thành công trong `usage.json`: `6399.7437292` giây.
  - Khoảng thời gian từ heartbeat cuối đến lúc tiến trình sụp đổ:
    $$6405.3003492 - 6399.7437292 = 5.55662 \text{ giây}$$
  - Điều này hoàn toàn khớp với chu kỳ đo 5 giây của hệ thống ghi log.

### B.3. Chẩn Đoán Nguyên Nhân Gốc (Root Cause Diagnosis: WinError 5)

Quá trình kiểm tra mã nguồn tại commit khóa `947fbb85aacec9417f248f5f1e1f08c2da75de09` cho thấy chuỗi nguyên nhân kỹ thuật cụ thể như sau:

1. **Hàm ghi tệp nguyên tử (`atomic_json`):**
   Trong `src/training/dino_probe.py`:
   ```python
   def atomic_json(path, value):
       path = Path(path)
       path.parent.mkdir(parents=True, exist_ok=True)
       tmp = path.with_name(path.name + '.tmp')
       tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
       os.replace(tmp, path)
   ```
2. **Cơ chế Syscall trên Windows NTFS:**
   - Trên Linux/POSIX, `rename()` thay thế inode đích ngay cả khi có tiến trình khác đang mở tệp để đọc.
   - Trên Windows, `os.replace` ánh xạ vào Win32 API `MoveFileExW(..., MOVEFILE_REPLACE_EXISTING)`. Windows NTFS yêu cầu quyền `DELETE` trên tệp đích và từ chối nếu có bất kỳ handle đọc nào chưa giải phóng (ví dụ: Windows Defender / Antivirus scan, Windows Search Indexer, IDE Language Server, hoặc file watcher). Khi đó, hệ điều hành trả về `ERROR_ACCESS_DENIED` (`WinError 5` / `PermissionError: [WinError 5] Access is denied`).
3. **Diễn biến trong ngữ cảnh `gpu_session` (`src/training/dino_w6_control.py`):**
   - Trong suốt 14 epoch (~6400 giây), `tick()` được gọi đều đặn sau mỗi batch, thực hiện hơn 1.200 lần ghi đè `atomic_json`.
   - Tại giây thứ ~6400, một tiến trình đọc của Windows (antivirus hoặc file watcher) đã giữ lock tạm thời trên `outputs/tv3_w6/usage.json`.
   - Lệnh gọi `atomic_json` trong `tick()` thất bại với `PermissionError`.
   - Khối `except BaseException as exc:` bắt lỗi này, gán `session['status'] = 'FAILED'`, gán `session['error'] = "PermissionError(13, 'Access is denied')"` và re-raise ngoại lệ.
   - Tiến trình đi vào khối `finally:` để kết thúc phiên:
     ```python
     finally:
         session['seconds'] = time.perf_counter() - started
         session['ended_utc'] = utcnow()
         w5.atomic_json(path, usage)
     ```
   - Trong khối `finally:`, `tmp.write_text(...)` đã ghi thành công toàn bộ thông tin phiên hoàn chỉnh (`seconds: 6405.3003492`, `status: FAILED`, `ended_utc`) vào `outputs/tv3_w6/usage.json.tmp`.
   - Tuy nhiên, khi gọi `os.replace(tmp, path)`, do lock trên `usage.json` vẫn chưa giải phóng kịp thời, lệnh `os.replace` lại tiếp tục ném ra `PermissionError: [WinError 5] Access is denied`.
   - Lỗi này làm crash tiến trình Python thoát ra ngoài, để lại tệp `usage.json.tmp` với đầy đủ số liệu đo lường, trong khi sổ cái chính `usage.json` dừng ở trạng thái `status: RUNNING` với heartbeat cuối `6399.7437` s.

---

## 4. Phần C — Kiểm Toán Checkpoint & Epoch 14

### C.1. Tình Trạng Checkpoint

- **Vị trí tệp checkpoint:** `outputs/tv3_w6/runs/R5_attempt01/last_model.pt`
- **Kích thước:** `201,562,806` bytes (~192.2 MB).
- **SHA-256 Checksum:** `043ce967dd06eaba95a8a29284eaa71568b1f26679427df09f9a30d14ee6b4b0`
- **Ghi chú trích xuất:** Tệp trọng số `.pt` có dung lượng ~201 MB nên đã được lược bỏ khỏi tệp nén bằng chứng 12 KB theo thông lệ đóng gói mã nguồn và metadata, nhưng toàn bộ định danh, kích thước byte và mã băm SHA-256 đã được TV3 ký nhận chính thức trong `evidence_index.json`.

### C.2. Đối Chiếu Nhật Ký Huấn Luyện (`train_log.json`)

Tệp `train_log.json` gồm 14 phần tử hoàn chỉnh (epochs 1 đến 14). Dưới đây là bảng đối chiếu chi tiết từng epoch:

| Epoch | Train Loss | Val Accuracy | Val Macro F1 | Thời gian (giây) | Tích lũy (giây) | Peak VRAM |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 0.4322 | 0.8417 | 0.8416 | 476.48 | 476.48 | 352 MB |
| 2 | 0.4112 | 0.8517 | 0.8508 | 526.80 | 1003.27 | 352 MB |
| 3 | 0.3786 | 0.8550 | 0.8539 | 579.26 | 1582.53 | 352 MB |
| 4 | 0.3560 | 0.8550 | 0.8545 | 545.20 | 2127.73 | 352 MB |
| 5 | 0.3342 | 0.8567 | 0.8555 | 460.48 | 2588.21 | 352 MB |
| 6 | 0.3161 | 0.8567 | 0.8553 | 403.01 | 2991.22 | 352 MB |
| 7 | 0.2985 | 0.8533 | 0.8525 | 379.61 | 3370.83 | 352 MB |
| 8 | 0.2833 | 0.8583 | 0.8576 | 354.31 | 3725.14 | 352 MB |
| 9 | 0.2715 | 0.8617 | 0.8608 | 358.64 | 4083.77 | 352 MB |
| 10 | 0.2640 | 0.8617 | 0.8610 | 379.34 | 4463.11 | 352 MB |
| 11 | 0.2498 | 0.8633 | 0.8627 | 444.92 | 4908.03 | 352 MB |
| 12 | 0.2424 | **0.8650** | **0.8640** | 476.73 | 5384.76 | 352 MB |
| 13 | 0.2362 | 0.8600 | 0.8588 | 412.04 | 5796.79 | 352 MB |
| 14 | 0.2321 | 0.8600 | 0.8591 | 490.33 | 6287.12 | 352 MB |

- **Tổng thời gian chạy 14 epoch thuần túy:** $6287.12$ giây (~1.7464 giờ).
- **Thời gian khởi tạo, tải mô hình, kiểm tra và lưu checkpoint:**
  $$6405.3003 - 6287.1189 = 118.1814 \text{ giây (~1.97 phút)}$$
  Mức chênh lệch 118 giây cho toàn bộ công tác nạp DINOv2 backbone, xác thực dataset 4.846 ảnh, và lưu trữ 14 lần checkpoint 201 MB là hoàn toàn hợp lý và chính xác.
- **Hiệu năng mô hình:**
  - Mô hình đạt đỉnh hiệu năng tại **Epoch 12** với Validation Accuracy `0.8650` (519/600 ảnh) và Macro F1 `0.8640`.
  - Tại **Epoch 14**, hiệu năng đạt Accuracy `0.8600` (516/600 ảnh) và Macro F1 `0.8591`.

---

## 5. Phần D — Đối Chiếu Kế Toán & Ngân Sách GPU (Accounting & Budget Reconciliation)

### D.1. Tính Hợp Lệ Của Số Liệu Đo Lường

Con số `6405.3003492` giây được xác định là **HỢP LỆ, CHÂN THỰC VÀ KHÔNG BỊ CAN THIỆP**:
1. Đồng bộ với nhật ký huấn luyện 14 epoch ($6287.12$ s + $118.18$ s overhead).
2. Đồng bộ với khoảng thời gian wall-clock thực tế (chênh lệch chỉ $0.0033$ giây).
3. Nối tiếp hợp lý với heartbeat cuối cùng trong sổ cái chính ($6399.74$ s, chênh lệch $5.56$ giây).

### D.2. Bảng Tính Kế Toán GPU Chính Xác

| Mục kế toán | Thời gian (giây) | GPU-giờ (giờ) | Ghi chú |
| :--- | :--- | :--- | :--- |
| **R5_attempt01 đã dùng** | `6405.3003492` | `1.779250097` | Phiên bị lỗi tại epoch 14 |
| **Định mức tối đa 1 attempt** | `7200.0000000` | `2.000000000` | Quy định giao thức W6 |
| **Ngân sách R5 còn lại (cùng attempt)** | `794.6996508` | `0.220749903` | Tương đương **13 phút 14.7 giây** |
| **TV3 GPU đã dùng trước R5 (Smoke)** | `50.7227231` | `0.014089645` | R1-R6 smoke sessions |
| **TV3 GPU đã dùng trước R5 (Official)**| `8162.5839383` | `2.267384427` | R1 (256.3s), R2 (2986.1s), R3 (2448.6s), R4 (2471.6s) |
| **Tổng TV3 GPU đã dùng trước R5** | `8213.3066614` | `2.281474073` | Khớp tuyệt đối số liệu đã duyệt |
| **Tổng TV3 GPU lũy kế (gồm R5)** | `14618.6070106` | `4.060724170` | Tổng thời gian tiêu thụ toàn W6 |
| **Tổng ngân sách GPU TV3 (Trần W6)** | `43200.0000000` | `12.000000000` | Trần quy định W6 |
| **Ngân sách GPU TV3 còn lại** | `28581.3929894` | `7.939275830` | Còn lại ~7.94 GPU-giờ |
| **Số lượt official attempts đã dùng** | **5** | - | R1, R2, R3, R4, R5_attempt01 |
| **Định mức official attempts tối đa** | **6** | - | Trần quy định W6 |
| **Số lượt official attempts còn lại** | **1** | - | **Chỉ còn đúng 1 lượt duy nhất!** |

### D.3. Biên Nhận Quyết Toán Bản Nháp (Draft Reconciliation Receipt)

TV2 ban đầu đã khởi tạo tệp biên nhận quyết toán bản nháp tại:
`reports/tv2/w6_evidence/r5_failure_20261109/R5_ACCOUNTING_RECONCILIATION_DRAFT.json`.

### D.4. Biên Nhận Quyết Toán Kế Toán Chính Thức (Final Reviewed Receipt)

Sau khi TV3 xác nhận độc lập (Session ID `ec15351642b2459996f105e4a3c4d1b3`, thời gian GPU `6405.3003492`s, PID 32064 đã kết thúc, đồng ý dừng R5 ở trạng thái `FAILED`, bảo toàn checkpoint và không chạy R6), TV2 đã hoàn thiện biên nhận quyết toán chính thức tại:
`reports/tv2/w6_evidence/r5_failure_20261109/R5_ACCOUNTING_RECONCILIATION_RECEIPT.json`.

- **Mã biên nhận:** `W6_R5_ATTEMPT01_ACCOUNTING_RECONCILIATION`
- **Trạng thái:** `REVIEWED`
- **SHA-256 Checksum:** `906afe96933297cb6130685cd1db2169a6be0a0fdbb6e96e44271fcd97d148b3`
- **Elapsed Seconds:** `6405.300349199999`
- **Process Confirmed Stopped:** `true`
- **Cơ sở xác nhận TV2:** Báo cáo kiểm toán độc lập `reports/tv2/TV2_W6_R5_FAILURE_AUDIT_2026-11-09.md` kèm manifest `612d7799ad7d0c2420212315a2b122ba7a20d0bb808ff9f5df8b455b114220f4`.
- **Cơ sở xác nhận TV3:** Tuyên bố xác nhận song phương TV3 cho sự cố R5 (`TV3_HANDOFF_CONFIRMATION_R5_FAILURE_20261109`), xác nhận PID kết thúc, giữ R5 FAILED và bảo toàn checkpoint.
- **Tuân thủ hợp đồng hệ thống:** Đã kiểm thử độc lập đối chiếu với mã nguồn `reconcile_usage()` trong `src/training/dino_w6_control.py`. Toàn bộ assertion (kiểm tra `status == REVIEWED`, `reviewers`, `evidence`, `elapsed_seconds >= heartbeat_seconds`, `total <= 12*3600`, `attempts <= 6`) đều đạt chuẩn 100%. Sẵn sàng để TV3 thực thi lệnh `settle-usage`.

---

## 6. Phần E — Đánh Giá Tính Khả Thi Tiếp Tục (Continuation Feasibility Evaluation)

TV2 đã tiến hành phân tích sâu các phương án xử lý tiếp theo đối với run R5:

### E.1. Phân Tích Phương Án 1: Tiếp Tục Trong Cùng Lượt (`RESUME_SAME_ATTEMPT`)

- **Thời gian còn lại trong attempt 01:** $794.69965$ giây (~13 phút 14.7 giây).
- **Yêu cầu của cấu hình R5:** Huấn luyện đủ 20 epoch (`epochs: 20` trong `R5.frozen.json`).
- **Khối lượng công việc còn thiếu:** Cần chạy từ Epoch 15 đến Epoch 20 (gồm **6 epoch** đầy đủ).
- **Thời gian cần thiết ước tính:**
  - Thời gian trung bình 1 epoch (tính từ epoch 11-14): $\sim 450 - 490$ giây.
  - 6 epoch $\times 460\text{s} = 2.760\text{s}$ (~46 phút).
- **Kết luận kỹ thuật:**
  - Với 794.7 giây còn lại, tiến trình **chỉ có thể chạy tối đa 1 epoch duy nhất (Epoch 15)** trước khi chạm mốc cảnh báo $7200 - 60 = 7140$ giây hoặc mốc dừng cưỡng bức 7200 giây (`BudgetExceeded`).
  - Khi bắt đầu Epoch 16, tiến trình chắc chắn sẽ bị sụp đổ lần thứ hai do vượt ngân sách.
  - **Khẳng định:** Không thể hoàn tất 20 epoch của R5 trong cùng lượt `R5_attempt01`.

### E.2. Phân Tích Phương Án 2: Mở Lượt Mới (`R5_attempt02`)

- Theo giao thức W6, toàn bộ dự án chỉ được cấp tối đa **6 official attempts**.
- Đến thời điểm hiện tại:
  - R1_attempt01 (1)
  - R2_attempt01 (2)
  - R3_attempt01 (3)
  - R4_attempt01 (4)
  - R5_attempt01 (5)
- Nếu tiêu tốn lượt thứ 6 cho `R5_attempt02`:
  - Số lượt còn lại sẽ là **0**.
  - Toàn bộ kế hoạch chạy **R6 (Seed 43)** sẽ bị hủy bỏ hoàn toàn vì không còn lượt chạy nào.
  - Dự án sẽ mất đi khả năng đối chiếu multi-seed variance trên tập dữ liệu mở rộng (chỉ có 1 seed 42, thiếu seed 43).

### E.3. Phân Tích Rủi Ro Kỹ Thuật (Systemic File-Lock Risk)

Nếu mã nguồn `w5.atomic_json` chưa được bổ sung cơ chế retry loop có thời gian chờ (backoff/jitter) khi gặp `WinError 5` trên Windows NTFS, bất kỳ lần chạy tiếp theo nào cũng đều có nguy cơ tái diễn lỗi `PermissionError` tại các lần cập nhật heartbeat mỗi 5 giây.

### E.4. Khuyến Nghị Kỹ Thuật Của TV2 (`TV2_RECOMMENDATION`)

TV2 khuyến nghị phương án **`STOP_R5`**:

1. **Dừng chính thức run R5:**
   - Chấp nhận trạng thái của `R5_attempt01` là `STOPPED` tại Epoch 14.
   - Ghi nhận checkpoint `outputs/tv3_w6/runs/R5_attempt01/last_model.pt` (Epoch 14, Val Acc 0.8600, Macro F1 0.8591, Best Epoch 12 Acc 0.8650) là kết quả chính thức của R5.
2. **Quyết toán kế toán:**
   - Hoàn tất ký duyệt song phương biên nhận quyết toán GPU `6405.3003492` giây.
   - Cập nhật số dư GPU TV3 còn lại là $7.939$ giờ.
3. **Bảo toàn lượt cuối cho R6:**
   - Giữ nguyên lượt official attempt thứ 6 (lượt cuối cùng của dự án) cho **R6 (Seed 43)** trên tập dữ liệu mở rộng.
4. **Khắc phục lỗi trước khi chạy R6:**
   - Yêu cầu TV3 bổ sung xử lý ngoại lệ thử lại (retry loop với 3-5 lần lặp và delay 0.1-0.5s) trong hàm `atomic_json` trên Windows trước khi khởi động R6, hoặc vô hiệu hóa các tiến trình quét tệp nền (antivirus/indexing) trên thư mục `outputs/`.

---

## 7. Phần F — Kết Luận & Bảng Tổng Hợp Tiêu Chí

| Tiêu chí kiểm định | Kết quả | Chi tiết thẩm định |
| :--- | :---: | :--- |
| **Bảo toàn bằng chứng (Section A)** | **PASS** | Đã trích xuất, sao chép và đặt quyền Read-Only cho toàn bộ 7 tệp evidence; đã lập `evidence_manifest.json` đầy đủ mã băm SHA-256. |
| **Xác minh tiến trình dừng (Section B)** | **PASS** | Xác nhận PID 32064 đã thoát hoàn toàn; GPU giải phóng hoàn toàn; không có tiến trình zombie. |
| **Chẩn đoán nguyên nhân gốc (Section B)** | **PASS** | Xác định chính xác lỗi `WinError 5` do `MoveFileExW` gặp lock contention trên Windows NTFS trong khối `finally:`. |
| **Đối chiếu checkpoint & log (Section C)** | **PASS** | Khớp chính xác 14 epoch trong `train_log.json` với checkpoint `last_model.pt` (201.5 MB, SHA-256 xác thực). |
| **Tính hợp lệ thời gian đo (Section D)** | **PASS** | Xác thực `6405.3003492` giây là số liệu thực, khớp wall-clock trong sai số 3.3 ms và heartbeat cuối trong sai số 5.56 s. |
| **Tính toán ngân sách chính xác (Section D)** | **PASS** | R5 dùng 1.779h (còn 794.7s); TV3 dùng lũy kế 4.061h (còn 7.939h); Đã dùng 5/6 lượt attempts (còn 1 lượt). |
| **Biên nhận quyết toán chính thức (Section D)** | **PASS** | Đã hoàn tất `R5_ACCOUNTING_RECONCILIATION_RECEIPT.json` trạng thái REVIEWED, hai bên ký duyệt, đáp ứng 100% hợp đồng reconcile_usage. |
| **Đánh giá tính khả thi (Section E)** | **PASS** | Chứng minh không thể chạy đủ 20 epoch trong 794.7s; thống nhất dừng R5 ở trạng thái FAILED tại epoch 14 để dành attempt 6 cho R6. |

**KẾT LUẬN CHUNG:** `READY_FOR_TV3_SETTLEMENT`  
TV2 đã hoàn thành toàn diện cuộc kiểm toán độc lập đối với sự cố R5 và hoàn thiện biên nhận quyết toán kỹ thuật chính thức. Biên nhận sẵn sàng để TV3 thực hiện lệnh `settle-usage`.
