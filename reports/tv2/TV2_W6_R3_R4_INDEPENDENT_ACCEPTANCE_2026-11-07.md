# TV2 W6 — Independent Acceptance R3/R4 & Multi-Seed Evaluation

**Ngày thẩm định:** 07/11/2026
**Nhánh làm việc:** `feat/baseline`
**Protocol lock:** `056ee897dbd9929844787a65ab705c09ecfbf846`
**TV3 result commit:** `61498e7ffc6831b1988cc2d1296457c1fe613373`
**TV3 source commit:** `95652c2d770cac464633eef0149bd27f4d859ece`
**TV2 baseline HEAD:** `056ee897dbd9929844787a65ab705c09ecfbf846`

---

## 1. Quyết định TV2 (Decisions)

1. **ARTIFACT_VERIFIED: PASS**
   Đã thẩm định độc lập 2 gói `R3_attempt01.zip` và `R4_attempt01.zip`, file `.sha256.json`, CRC toàn bộ archive (`testzip() is None`), 38/38 file payload khớp hoàn toàn hash SHA-256 và kích thước byte trong `package_index.json`. Frozen config raw/canonical SHA và checkpoint best/last SHA khớp chính xác với protocol lock.
2. **MODEL_REPLAY: PASS**
   Tái lập thành công môi trường CUDA TV2 (Python 3.12.10, PyTorch 2.6.0+cu124, NVIDIA GeForce RTX 4060 Laptop GPU). Chạy fresh-process inference độc lập từ `best_model.pt` của R3 và R4 trên 600 ảnh / 680 GT crops thực tế của Validation set. So sánh element-by-element với kết quả producer: **0 sai lệch** trên toàn bộ 5,440 crop logits, 5,440 crop probabilities, 4,800 image probabilities, 600 predicted classes và toàn bộ metrics (max absolute delta = 0.0).
3. **REGRESSION_REVIEW: PASS**
   Phân tích paired outcomes trên đúng 600 image IDs chung so với R0 và R2. Không có bất kỳ lớp nào bị mất $\ge 4$ ảnh đúng so với R0 ở cả hai run R3 và R4.
4. **MULTI_SEED_SUMMARY: COMPLETED (Recipe R2 trên seeds 42, 43, 44)**
   Tổng hợp kết quả thống kê trung bình và độ lệch chuẩn mẫu (sample SD, ddof=1):
   - **Accuracy:** $0.848889 \pm 0.004811$ ($84.89\% \pm 0.48\%$)
   - **Macro-F1:** $0.848017 \pm 0.004556$ ($84.80\% \pm 0.46\%$)
   - **Số ảnh đúng:** $509.33 \pm 2.89$ / 600 ảnh
   - **Cảnh báo quan trọng:** Toàn bộ 3 seed và giá trị trung bình đều **nằm dưới ngưỡng mục tiêu 88.0% (528/600)**. Không được lấy riêng seed tốt nhất (seed 42 hay 44) làm kết quả đại diện.
5. **TV2_ACCEPTANCE: PASS**
   Nghiệm thu chính thức kết quả thực thi của R3 và R4. Demo mặc định giữ nguyên (không đổi). TV4 adapter gate vẫn độc lập. R5/R6 tiếp tục bị khóa chờ TV1 data review.

---

## 2. Thông tin Artifact Audit và Định danh

- **R3 ZIP:** `reports/tv3/w6/w6/R3_attempt01.zip`
  - SHA-256: `a6f4d51c0f84f959c0ecf44c62eee819fc82844d38e63bbff50abe573920df4a` (Khớp)
  - Kích thước: 267,930,042 bytes | CRC: PASS
  - Best checkpoint SHA-256: `2494551fa40e9d663ecb368d7c92d007c7404e92207503b432573ae55c7c4a6f`
  - Raw config SHA-256: `4c52a6521a083a62122924e080716015310560f2a6544085ab7aef9acf2e8078`
  - Canonical config SHA-256: `dec76442a22f55043ccf1f1784cd303d0d944fd37e433271966642f181c5234d`
- **R4 ZIP:** `reports/tv3/w6/w6/R4_attempt01.zip`
  - SHA-256: `cbe27ed2cd243e9783743eb8028b8d6b1f600fb28299735276d6d13b31114c0b` (Khớp)
  - Kích thước: 267,934,803 bytes | CRC: PASS
  - Best checkpoint SHA-256: `7eaa034773ebed9f513493eca6dda3c9e8f0bcc6d2c814ad357026e6a9656ce8`
  - Raw config SHA-256: `8e1ee676431166082cf9f0efa4d25b41424517f443282b7b8c13b614a67fe53d`
  - Canonical config SHA-256: `839061f577cc374a8e105c5e41312b1919ea4efffd3c0e0c9b9c6a93a3ac3ff5`

Tất cả các file payload (best_model.pt, last_model.pt, handoff.json, validation.json, reload01.predictions.json, ...) đều đã được kiểm tra tính toàn vẹn 100% đối chiếu với `package_index.json`.

---

## 3. Bảng tổng hợp R0 / R1 / R2 / R3 / R4

| Run | Recipe | Seed | Dataset | Status | Correct | Accuracy | Macro-Precision | Macro-Recall | Macro-F1 | Δ Correct vs R0 | Δ Macro-F1 vs R0 |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| **R0** | R0 | 42 | comparison_v1 | REFERENCE | 507/600 | 0.845000 | 0.847957 | 0.845000 | 0.844401 | 0 | 0.000000 |
| **R1** | R1 | 42 | comparison_v1 | COMPLETED | 501/600 | 0.835000 | 0.835766 | 0.835000 | 0.833864 | -6 | -0.010537 |
| **R2** | R2 | 42 | comparison_v1 | COMPLETED | 511/600 | 0.851667 | 0.853158 | 0.851667 | 0.850651 | +4 | +0.006250 |
| **R3** | R2 | 43 | comparison_v1 | COMPLETED | 506/600 | 0.843333 | 0.845788 | 0.843333 | 0.842757 | -1 | -0.001644 |
| **R4** | R2 | 44 | comparison_v1 | COMPLETED | 511/600 | 0.851667 | 0.854455 | 0.851667 | 0.850645 | +4 | +0.006244 |

### Thống kê Multi-Seed Recipe R2 (seeds 42, 43, 44):
- **Accuracy trung bình:** $0.848889 \pm 0.004811$
- **Macro-F1 trung bình:** $0.848017 \pm 0.004556$
- **Số ảnh đúng trung bình:** $509.33 \pm 2.89$ / 600 ảnh
- **Khoảng cách tới mục tiêu 88.0% (528 ảnh đúng):** Còn thiếu trung bình **18.67 ảnh đúng**.
- **Đánh giá suy luận:** R3 đạt 506 ảnh đúng (thấp hơn R0 1 ảnh). R2 và R4 đạt 511 ảnh đúng. Sự biến thiên giữa các seed cho thấy hiệu quả của Recipe R2 chưa đủ cách biệt an toàn so với baseline R0, và không có căn cứ để chọn riêng seed cao nhất làm metric đại diện.

---

## 4. Per-Class Regression & Phân tích nhóm nhầm lẫn

Mỗi lớp gồm đúng 75 ảnh trong tập cân bằng Validation.

| Lớp (Class) | R0 P / R / F1 | R2 P / R / F1 | R3 P / R / F1 | R4 P / R / F1 | R2 Δ | R3 Δ | R4 Δ |
|---|---|---|---|---|---:|---:|---:|
| **large_antlered_muntjac** | 0.8710 / 0.7200 / 0.7883 | 0.8833 / 0.7067 / 0.7852 | 0.8814 / 0.6933 / 0.7761 | 0.8966 / 0.6933 / 0.7820 | -1 | -2 | -2 |
| **annamite_striped_rabbit** | 0.8452 / 0.9467 / 0.8931 | 0.8875 / 0.9467 / 0.9161 | 0.8974 / 0.9333 / 0.9150 | 0.8987 / 0.9467 / 0.9221 | 0 | -1 | 0 |
| **sambar** | 0.7867 / 0.7867 / 0.7867 | 0.8182 / 0.8400 / 0.8289 | 0.7821 / 0.8133 / 0.7974 | 0.8289 / 0.8400 / 0.8344 | **+4** | **+2** | **+4** |
| **chinese_serow** | 0.9189 / 0.9067 / 0.9128 | 0.9079 / 0.9200 / 0.9139 | 0.9067 / 0.9067 / 0.9067 | 0.9079 / 0.9200 / 0.9139 | +1 | 0 | +1 |
| **common_palm_civet** | 0.8205 / 0.8533 / 0.8366 | 0.8611 / 0.8267 / 0.8435 | 0.8400 / 0.8400 / 0.8400 | 0.8205 / 0.8533 / 0.8366 | -2 | -1 | 0 |
| **masked_palm_civet** | 0.8358 / 0.7467 / 0.7887 | 0.7703 / 0.7600 / 0.7651 | 0.7733 / 0.7733 / 0.7733 | 0.8000 / 0.7467 / 0.7724 | +1 | +2 | 0 |
| **silver_pheasant** | 0.9730 / 0.9600 / 0.9664 | 0.9351 / 0.9600 / 0.9474 | 0.9474 / 0.9600 / 0.9536 | 0.9474 / 0.9600 / 0.9536 | 0 | 0 | 0 |
| **eurasian_wild_pig** | 0.7326 / 0.8400 / 0.7826 | 0.7619 / 0.8533 / 0.8050 | 0.7381 / 0.8267 / 0.7799 | 0.7356 / 0.8533 / 0.7901 | +1 | -1 | +1 |

*Cột $\Delta$: Số lượng ảnh phân loại đúng tăng/giảm so với baseline R0 (Support = 75).*

### Đánh giá ngưỡng suy giảm (Cảnh báo mất $\ge 4$ ảnh đúng):
- **R1:** Lớp `sambar` mất 4 ảnh đúng (59 $\to$ 55).
- **R2:** Không có lớp nào mất $\ge 4$ ảnh đúng.
- **R3:** Không có lớp nào mất $\ge 4$ ảnh đúng (mất nhiều nhất là `large_antlered_muntjac` mất 2 ảnh).
- **R4:** Không có lớp nào mất $\ge 4$ ảnh đúng (mất nhiều nhất là `large_antlered_muntjac` mất 2 ảnh).

### Phân tích cặp loài dễ nhầm lẫn (Confusable Pairs):
1. **Common palm civet $\leftrightarrow$ Masked palm civet (classes 4 và 5):**
   - R0: 13 lỗi (5 + 8)
   - R2: 15 lỗi (8 + 7)
   - R3: 14 lỗi (7 + 7)
   - R4: 14 lỗi (6 + 8)
   $\to$ Hiện tượng nhầm lẫn giữa hai loài cầy vẫn là điểm yếu cố hữu của Recipe R2 qua cả 3 seed, cao hơn R0 từ 1–2 ca nhầm lẫn.
2. **Large-antlered muntjac $\leftrightarrow$ Sambar (classes 0 và 2):**
   - R0: 12 lỗi (8 + 4)
   - R2: 13 lỗi (10 + 3)
   - R3: 13 lỗi (10 + 3)
   - R4: 12 lỗi (10 + 2)
   $\to$ Độ nhạy của Sambar tăng rõ rệt (+2 đến +4 ảnh đúng), nhưng số ảnh Muntjac bị nhầm thành Sambar tăng từ 8 (ở R0) lên 10 (ở cả R2, R3, R4).

---

## 5. Kết quả Replay và Hạch toán GPU

### Bảng kết quả Exact Replay (TV2 Replay vs Producer)
| Run | Seed | Logits Mismatches | Probs Mismatches | Pred Class Mismatches | Metric Diff | Max Delta | Kết luận Replay |
|---|---:|---:|---:|---:|---:|---:|:---:|
| R3 | 43 | 0 / 5,440 | 0 / 5,440 | 0 / 600 | 0 | 0.0 | **PASS** |
| R4 | 44 | 0 / 5,440 | 0 / 5,440 | 0 / 600 | 0 | 0.0 | **PASS** |

### Hạch toán GPU Replay TV2 (Ngân sách: 2.0 GPU-giờ)
- Replay R1 lần 1 + 2: 0.081202 GPU-giờ
- Replay R2: 0.036549 GPU-giờ
- Replay R3: 0.011764 GPU-giờ (42.35 giây)
- Replay R4: 0.011367 GPU-giờ (40.92 giây)
- **Tổng cộng TV2 Replay:** **0.140882 GPU-giờ / 2.0 GPU-giờ** (Còn lại: **1.859118 GPU-giờ**).

### Hạch toán GPU TV3 (Ngân sách: 12.0 GPU-giờ, tối đa 6 attempts)
- Official attempts: 4 / 6 attempts (R1: 0.0712h, R2: 0.8295h, R3: 0.6802h, R4: 0.6865h; tổng = 2.267384h).
- Preparation (4 smokes): 0.009595h.
- **Tổng cộng TV3:** **2.276979 GPU-giờ / 12.0 GPU-giờ** (Còn lại: **9.723021 GPU-giờ**).

---

## 6. Kiểm tra Verification Gates

- **Registry Validator:** `scripts/evaluate_w6_validation.py` trả về `VALID / APPROVED` cho cả `experiments/w6/registry.json` và `experiments/w6/tv3_R3_R4.approved.json`.
- **W6 Validation Tests:** `51 PASS / 0 FAIL`.
- **W5 Regression Suites:** `70 PASS / 0 FAIL` (test_w5_validation: 32, test_evaluation: 9, test_contracts: 13, test_dino_w5: 11, test_dino_tv2_compat: 5).
- **Git diff --check:** PASS.
- Không sửa source/config frozen, không sửa W1–W5, không mở Official Test W4.

---

## 7. Kết luận và Bàn giao TV2

1. TV2 chính thức nghiệm thu kỹ thuật hai official runs R3 (seed 43) và R4 (seed 44) của TV3.
2. Recipe R2 đạt kết quả multi-seed trung bình là **84.89% Accuracy** và **0.8480 Macro-F1**, vẫn thấp hơn mục tiêu 88.0%.
3. Quyết định demo mặc định **không thay đổi**. TV4 adapter review vẫn là điều kiện tiên quyết độc lập trước khi cân nhắc bất kỳ thay đổi nào về demo.
4. R5/R6 vẫn tiếp tục bị khóa cho đến khi TV1 hoàn tất data review.
