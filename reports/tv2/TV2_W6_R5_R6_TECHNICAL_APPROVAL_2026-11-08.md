# CameraTrapML — TV2 W6 Technical Approval (R5/R6)

**Date:** 2026-11-08 (Asia/Ho_Chi_Minh)
**Role:** TV2 — Baseline & Evaluation
**Decision:** **TECHNICALLY_APPROVED_BY_TV2_FOR_PROTOCOL_LOCK**
**Status:** TV2 technical approval recorded; TV3 approval receipt PENDING; official R5/R6 training NOT AUTHORIZED until bilateral protocol lock.

---

## 1. Decision Statement

> *"Tôi, TV2 (Baseline & Evaluation), chấp thuận về mặt kỹ thuật proposal R5 và R6 của TV3, với phạm vi TECHNICALLY_APPROVED_BY_TV2_FOR_PROTOCOL_LOCK."*

Bản phê duyệt kỹ thuật này xác nhận các cấu hình `R5.frozen.json` và `R6.frozen.json`, metadata đề xuất, smoke bindings, tính toán ngân sách GPU và cam kết mã nguồn của TV3 đã thỏa mãn toàn bộ các điều kiện tiên quyết của protocol W6 (`docs/experiment_protocol_w6.md`).

Bản chấp thuận này **không** thay thế cho phê duyệt độc lập từ TV3 và **không** cấp quyền chạy huấn luyện chính thức (official training). Cả hai lượt chạy R5 và R6 duy trì trạng thái **`CONDITIONAL`** trong registry cho đến khi TV3 nộp biên nhận phê duyệt riêng và hoàn tất thủ tục bilateral protocol lock.

---

## 2. Evidence & Scope Binding

| Thuộc tính | Giá trị / Đường dẫn |
|---|---|
| **TV3 Proposal Commit** | `a6bfffb5391866001b83298983aed90e7a2d29ce` (nhánh `origin/feat/crop-classifier`) |
| **TV3 Proposal File** | `experiments/w6/tv3_R5_R6.proposal.json` |
| **Recipe Selection** | `R2` (Linear probe + Fine-tune backbone, chọn từ kết quả độc lập `reports/tv2/TV2_W6_INDEPENDENT_MODEL_REPLAY_2026-11-06.md`) |
| **Dataset Release** | `train_expansion_w6_v1` |
| **Dataset Release SHA-256** | `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5` |
| **TV2 Data Expansion Sign-off** | Commit `def28ef14605d5615e5b05a479f03aaad6376224`, biên nhận `reports/tv2/TV2_W6_DATA_EXPANSION_APPROVAL_RECEIPT.json` |
| **Source Commit Binding** | `947fbb85aacec9417f248f5f1e1f08c2da75de09` (0 byte diff trong cây `src/` so với commit mã nguồn R3/R4 `95652c2d770cac464633eef0149bd27f4d859ece`) |
| **Runtime Lock Canonical SHA-256** | `7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a` |
| **TV2 Evidence JSON** | `reports/tv2/w6_evidence/lock_20261108/TV2_R5_R6_TECHNICAL_APPROVAL.json` |

---

## 3. Frozen Runs Specification & Hash Table

| Run | Recipe | Seed | Dataset | Frozen Config Path | Canonical SHA-256 | Raw File SHA-256 | Smoke Report Path | Smoke Raw SHA-256 | Trạng thái |
|:---:|:---:|:---:|:---|:---|:---:|:---:|:---|:---:|:---:|
| **R5** | R2 | 42 | `train_expansion_w6_v1` | `configs/w6/tv3/R5.frozen.json` | `5c698bbc4e1d1e232ff8326eb7e4036265a77be317a39472f2fd92d7c9804b03` | `fd80bab2db8656e7265cb7325c498dd363434f83421f7835213539ccbb454413` | `reports/tv3/w6/smoke/R5_smoke01.json` | `dc7f44eb36ac4211b659c52b3ebcdaecd154d609dc5a6ac2cc5506e41b55282d` | `CONDITIONAL` |
| **R6** | R2 | 43 | `train_expansion_w6_v1` | `configs/w6/tv3/R6.frozen.json` | `b33a1c6a8445f8d1d784c30533894f47da7bd64081575ece0d9d18fa9a7d3723` | `0721f394b2e0cfb7575616c2197ee4db19126ee20b642627b2e5b79b6ac4c75b` | `reports/tv3/w6/smoke/R6_smoke01.json` | `85872af6807ac76c5a4d9734bd7bc0b9fe0cac71e3310c726c65242b0f79bf94` | `CONDITIONAL` |

### Kiểm định Candidate và Smoke Bindings
- **R5 Candidate:** Canonical digest `3a0f9f0b45e354090d3c3b264a021cb3765c7c43036a7e93f618fd3d977c2f1a`, Raw SHA `d0a46afd1aed0a9f40a1a9a4562ffe6d4105fee5b6344588f315ca54c6b4c818` (khớp hoàn toàn với `config_sha256` và `config_raw_sha256` trong `R5_smoke01.json`).
- **R6 Candidate:** Canonical digest `4e6e51bf7509199e070fb97f1dc7323eabfe976be074a8ab1d361e9a62de66c5`, Raw SHA `68bfd1b427d9a8463f47234d6b3967ae33c2d81dbaba9e86e3fd168b415f90bc` (khớp hoàn toàn với `config_sha256` và `config_raw_sha256` trong `R6_smoke01.json`).
- **Smoke Results:** Cả hai smoke runs đều ghi nhận `status: PASS`, `exit_code: 0`, `official_training: false`, `validation_inference: false`, `test_opened: false`.
- **Cấu hình Frozen:** `w6.validate_recipe_config` đạt `PASS` cho cả hai cấu hình; điểm khác biệt duy nhất giữa R5 và R6 là `seed` (42 vs 43), `run_id` và bằng chứng smoke liên kết.

---

## 4. GPU Budget & Accounting

Đối chiếu với giới hạn của `docs/experiment_protocol_w6.md`:
- **Số lượt official attempts đã dùng:** 4 lượt (R1: 0.071201h, R2: 0.829476h, R3: 0.680165h, R4: 0.686542h). Tổng GPU official: **2.267384 giờ**.
- **Số lượt smoke preparation đã dùng:** 6 lượt (R1_smoke01 đến R6_smoke01). Tổng GPU smoke: **0.014090 giờ**.
- **Tổng thời gian GPU TV3 đã tiêu thụ:** **2.281474 giờ** (khớp chính xác tuyệt đối với sổ kế toán).
- **Hạn mức GPU tối đa của TV3:** 12.0 giờ → Ngân sách còn lại: **9.718526 giờ** (đủ dồi dào cho R5 và R6).
- **Số lượt official attempts còn lại:** 6 - 4 = **2** lượt (vừa vặn cho R5 và R6 nếu không có sự cố crash/re-attempt).
- **Giới hạn mỗi lượt official attempt:** $\le 2.0$ giờ GPU.

---

## 5. Ràng buộc & Điều kiện trước Official Training

1. **Chờ phê duyệt riêng của TV3:** TV3 phải xuất bản biên nhận phê duyệt riêng (receipt file) đối với cùng cấu hình frozen, commit mã nguồn, runtime và dataset này. TV2 không ký thay hoặc đại diện cho TV3.
2. **Khóa Protocol song phương (Bilateral Protocol Lock):** Trước khi TV3 kích hoạt huấn luyện R5/R6, TV2 và TV3 phải đồng bộ và cập nhật trạng thái của R5 và R6 trong `experiments/w6/registry.json` sang `REGISTERED`, gắn kèm đầy đủ bằng chứng approval của cả hai bên.
3. **Tuyệt đối không xâm phạm Official Test W4:** Mọi quá trình training, validation intermediate, hyperparameter tuning hoặc model selection không được đọc hoặc suy luận trên tập Test W4.
4. **Bảo toàn môi trường runtime:** Môi trường GPU, phiên bản thư viện và cấu hình PyTorch phải tuân thủ nghiêm ngặt canonical runtime lock `7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a`.
5. **Không có kết quả huấn luyện nào được tuyên bố:** Tài liệu này thuần túy là phê duyệt kỹ thuật trước huấn luyện. Mọi chỉ số đánh giá sẽ chỉ được TV2 độc lập replay và nghiệm thu sau khi TV3 hoàn thành huấn luyện chính thức.
