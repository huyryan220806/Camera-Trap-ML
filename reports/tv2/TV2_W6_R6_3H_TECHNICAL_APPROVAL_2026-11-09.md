# CameraTrapML — TV2 W6 Technical Approval (R6 3-Hour Amendment)

**Date:** 2026-11-09 (Asia/Ho_Chi_Minh)  
**Role:** TV2 — Baseline & Evaluation  
**Decision:** **APPROVE_R6_3H** (Technical Approval for Protocol Amendment & R6 3H Allowance)  
**Status:** TV2 technical approval receipt prepared and committed; TV3 bilateral co-signature PENDING; official R6 training NOT AUTHORIZED until bilateral protocol lock.

---

## 1. Decision Statement

> *"Tôi, TV2 (Baseline & Evaluation), chấp thuận về mặt kỹ thuật proposal điều chỉnh thời gian R6 lên tối đa 3,0 GPU-giờ (R6 3-Hour Amendment) và cấu hình frozen R6 của TV3, với quyết định chính thức `APPROVE_R6_3H` theo hợp đồng kiểm định `verify_r6_amendment_evidence()`."*

Bản phê duyệt kỹ thuật này xác nhận:
1. Cấu hình đóng băng `configs/w6/tv3/R6.3h.frozen.json` cùng metadata đề xuất `experiments/w6/tv3_R6_3h.frozen.proposal.json`.
2. Bằng chứng train-only smoke `reports/tv3/w6/smoke/R6_3h_smoke01.json` và preflight `reports/tv3/w6/r6_3h_freeze_evidence/preflight.json`.
3. Bản vá I/O retry giới hạn xử lý tranh chấp Windows NTFS `WinError 5` trên file `usage.json`.
4. Sổ kế toán GPU đã kết toán đầy đủ sự cố R5_attempt01 (6.405,3 s, FAILED, epoch 14), bảo toàn 5/6 official attempts và trần tổng TV3 12,0 GPU-giờ.

Bản chấp thuận này **không** thay thế cho phê duyệt độc lập từ TV3 và **không** cấp quyền chạy huấn luyện chính thức (official training). Run R6 và amendment duy trì trạng thái **`PENDING`** trong registry cho đến khi TV3 nộp biên nhận phê duyệt riêng và hoàn tất thủ tục bilateral protocol lock.

---

## 2. Evidence & Scope Binding

| Thuộc tính | Giá trị / Đường dẫn |
|---|---|
| **TV3 Source Binding Commit** | `3b4b106c01e64901f213f6eebfdd10ffa55a7eb7` (chứa source patch, tests, candidate config) |
| **TV3 Handoff Commit** | `24251096c47b867c257bc62feae403459bd50d42` (chứa frozen config, proposal, smoke, preflight, usage) |
| **Recipe & Seed** | `R2`, Seed `43` |
| **Dataset Release** | `train_expansion_w6_v1` |
| **Dataset Release SHA-256** | `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5` |
| **Runtime Lock Canonical SHA-256** | `7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a` |
| **Frozen Config Path** | `configs/w6/tv3/R6.3h.frozen.json` |
| **Frozen Config Canonical SHA-256** | `08a01874ccc2cf0f21e652ed082893bfc666e4489c01e7b5cb36404bebe67a70` |
| **Frozen Config Raw Byte SHA-256** | `6d32d3b5525053e8ab43eadc190f70da649f0ce7d9ff48889bbb210694f682c4` |
| **Smoke Evidence Path** | `reports/tv3/w6/smoke/R6_3h_smoke01.json` |
| **Smoke Evidence SHA-256** | `4ef74db223ac7ab45e88cd11de78e878c9c0253c2e2a0a95b473b6a25bae287d` |
| **TV2 Approval Receipt Path** | `reports/tv2/w6_evidence/r6_3h_approval/TV2_R6_3H_APPROVAL.json` |
| **TV2 Approval Receipt SHA-256** | `8781ad4ef026e591987c00bfdce2a9fb576dfbc21690923f7c6334912b9c8f73` |
| **Protocol Amendment Ref** | `docs/experiment_protocol_w6.md#protocol-amendment-r6-3-hour-allowance-2026-11-09` |

---

## 3. GPU Accounting & Invariant Verification

Đối chiếu số liệu kế toán tại `reports/tv3/w6/r6_3h_freeze_evidence/usage.json`:

| Hạng mục | Số phiên | Thời gian (giây) | Thời gian (giờ) | Ghi chú |
|---|:---:|:---:|:---:|---|
| **Official Attempts (R1–R4)** | 4 | 8.046,8267 | 2,2352296 | R1: 217,5s; R2: 2948,2s; R3: 2409,6s; R4: 2471,6s |
| **Official Attempt R5 (Settled)** | 1 | 6.405,3003 | 1,7792501 | FAILED tại epoch 14, đối soát song phương TV2/TV3 khớp 100% |
| **Tổng Official Attempts (R1–R5)** | **5** | **14.452,1270** | **4,0144797** | **5 / 6 official attempts đã sử dụng** |
| **Reload Sessions (R1–R4)** | 4 | 155,5781 | 0,0432161 | Xác minh reload sau mỗi completed attempt |
| **Train-only Smoke (R1–R6, R6_3h)** | 7 | 47,0056 | 0,0130571 | Khởi tạo cấu hình và thiết bị |
| **Lũy kế TV3 hiện tại** | **16** | **14.630,4108** | **4,0640030** | Khớp chính xác với `c.usage_totals()` |
| **Trần tối đa TV3 toàn chiến dịch** | - | 43.200,0000 | 12,0000000 | Bất biến theo protocol |
| **Ngân sách TV3 còn lại** | - | 28.569,5892 | 7,9359970 | Dư dồi dào |
| **Dự toán R6_attempt01 (tối đa 3h)** | 1 | $\le 10.800,0000$ | $\le 3,0000000$ | Lượt chạy thứ 6/6 (cuối cùng) |
| **Tổng lũy kế dự kiến sau R6** | **17** | **$\le 25.430,4108$** | **$\le 7,0640030$** | **Còn dư $\ge 4,936$ giờ GPU dưới trần 12h** |

---

## 4. Kiểm định Bản vá Lỗi I/O `WinError 5`

- **Nguyên nhân gốc:** Tranh chấp tệp trên Windows NTFS (`MoveFileExW`) khi `os.replace` trên `usage.json` trong lúc tiến trình nền hoặc anti-virus quét tệp.
- **Giải pháp TV3:** Bổ sung hàm `write_usage(path, usage, refresh=None)` tại `src/training/dino_w6_control.py` với tối đa 5 lần retry (thời gian chờ: 0.05s, 0.1s, 0.2s, 0.4s, 0.8s, tổng 1.55s). Chỉ bắt và retry duy nhất lỗi `PermissionError` có `winerror == 5`. Mọi lỗi khác hoặc lỗi vĩnh viễn đều ném ngoại lệ ngay lập tức và bảo toàn tệp `.tmp`.
- **Kiểm thử độc lập:** Toàn bộ 18 test cases trong `tests/test_r6_amendment.py` đạt **PASS** 100%.

---

## 5. Các Ràng buộc & Điều kiện trước Lượt chạy Official R6

1. **Ràng buộc song phương:** TV3 phải xuất bản receipt approval độc lập (`role: TV3`, `decision: APPROVE_R6_3H`, binding khớp 100%) và hai bên thực hiện bilateral protocol lock trước khi kích hoạt huấn luyện.
2. **Khóa phạm vi:** Chỉ duy nhất `R6_attempt01` được phép chạy tối đa 3,0 GPU-giờ. Mọi attempt khác giữ nguyên giới hạn 2,0 GPU-giờ.
3. **Niêm phong Official Test W4:** Tuyệt đối không đọc, mở raster ảnh hoặc suy luận trên tập dữ liệu Test W4.
4. **Không phục hồi R5:** Lượt chạy R5 giữ nguyên trạng thái `FAILED`, checkpoint epoch 14 được lưu trữ làm bằng chứng kiểm toán, không khởi động lại hoặc resume R5.
