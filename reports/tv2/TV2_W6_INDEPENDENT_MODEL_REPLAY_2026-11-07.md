# TV2 W6 — Independent Model Replay R3/R4 and Multi-Seed Evaluation

**Date:** 2026-11-07
**Branch:** `feat/baseline`
**Protocol lock:** `056ee897dbd9929844787a65ab705c09ecfbf846`
**TV3 result commit:** `61498e7ffc6831b1988cc2d1296457c1fe613373`
**TV3 source commit:** `95652c2d770cac464633eef0149bd27f4d859ece`
**Vendor commit:** `6876159a11b4df116f30f667f8c9888617df0751`

---

## 1. Quyết định TV2 (Decisions)

- **ARTIFACT_VERIFIED: PASS** — File ZIP `R3_attempt01.zip` và `R4_attempt01.zip` khớp hoàn toàn SHA-256 đã công bố, pass CRC check (`testzip() is None`), package index khớp từng file payload về SHA-256 và kích thước byte. Checkpoint best/last khớp SHA với handoff. Frozen config canonical và raw SHA khớp 100% với protocol lock TV2.
- **MODEL_REPLAY: PASS** — Tái lập thành công môi trường CUDA 12.4 + PyTorch 2.6.0+cu124 trên GPU NVIDIA GeForce RTX 4060 Laptop. Chạy fresh-process inference độc lập từ `best_model.pt` của R3 và R4 trên toàn bộ 600 ảnh / 680 GT crops thực tế của Validation set (`comparison_v1`). So sánh element-by-element với producer `validation.json`: 0 sai lệch trên crop logits (5,440/5,440), crop probabilities (5,440/5,440), image probabilities (4,800/4,800), predicted classes (0 mismatches) và metrics (exact match, max absolute delta = 0.0).
- **REGRESSION_REVIEW: PASS** — So sánh cặp trực tiếp trên đúng 600 image IDs với R0 (W5 reference) và R2 (seed 42). Không có lớp nào bị mất $\ge 4$ ảnh đúng so với R0 ở cả R3 và R4.
- **MULTI_SEED_SUMMARY: COMPLETED (Recipe R2 trên seeds 42, 43, 44)** — Tổng hợp kết quả thống kê trung bình và độ lệch chuẩn mẫu (sample SD, ddof=1) cho Recipe R2:
  - Accuracy: $0.848889 \pm 0.004811$ (Mean: 509.33 / 600 ảnh đúng)
  - Macro-F1: $0.848017 \pm 0.004556$
  - Toàn bộ các seed (42, 43, 44) và giá trị trung bình đều **nằm dưới ngưỡng mục tiêu 88.0%** (528/600). Tuyệt đối không chọn riêng seed tốt nhất (seed 42 hay 44) làm đại diện.
- **TV2_ACCEPTANCE: PASS** — Nghiệm thu kỹ thuật độc lập hai official runs R3/R4 của TV3. Demo mặc định giữ nguyên (không đổi). TV4 adapter review vẫn hoàn toàn độc lập. R5/R6 tiếp tục bị khóa chờ TV1 data review.

---

## 2. Thông tin môi trường Replay và Định danh đầu vào

- **Môi trường:** Isolated Python venv tại `outputs/tv2_w6/independent_replay_20261106/.venv/`.
  - Python: 3.12.10 (MSC v.1943 64 bit)
  - PyTorch: `2.6.0+cu124`
  - Torchvision: `0.21.0+cu124`
  - CUDA: `12.4`, cuDNN: `90100`
  - GPU: `NVIDIA GeForce RTX 4060 Laptop GPU` (8,188 MB VRAM)
  - Thư viện: Pillow `12.2.0`, NumPy `2.5.3`, scikit-learn `1.9.0`
  - Cấu hình runtime: FP32, AMP=False, TF32=False, `torch.are_deterministic_algorithms_enabled()=True`, `cudnn.deterministic=True`, `cudnn.benchmark=False`, intra/inter-op threads = 10.
- **Dữ liệu kiểm tra:** Tập Validation `comparison_v1` (600 ảnh, 680 GT crops, provenance SHA-256 `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`). Toàn bộ 600 ảnh đã được verify bytes và RGB pixels. Tuyệt đối không mở tập Train hay tập Official Test W4.

### Bảng định danh artifact đầu vào R3 / R4

| Run | Seed | ZIP SHA-256 | Best Checkpoint SHA-256 | Config Raw SHA-256 | Config Canonical SHA-256 |
|---|---:|---|---|---|---|
| R3 | 43 | `a6f4d51c0f84f959c0ecf44c62eee819fc82844d38e63bbff50abe573920df4a` | `2494551fa40e9d663ecb368d7c92d007c7404e92207503b432573ae55c7c4a6f` | `4c52a6521a083a62122924e080716015310560f2a6544085ab7aef9acf2e8078` | `dec76442a22f55043ccf1f1784cd303d0d944fd37e433271966642f181c5234d` |
| R4 | 44 | `cbe27ed2cd243e9783743eb8028b8d6b1f600fb28299735276d6d13b31114c0b` | `7eaa034773ebed9f513493eca6dda3c9e8f0bcc6d2c814ad357026e6a9656ce8` | `8e1ee676431166082cf9f0efa4d25b41424517f443282b7b8c13b614a67fe53d` | `839061f577cc374a8e105c5e41312b1919ea4efffd3c0e0c9b9c6a93a3ac3ff5` |

---

## 3. Kết quả Independent Replay (Exact Comparison)

Chính sách so sánh là **bình đẳng tuyệt đối từng phần tử (exact element equality, tolerance = 0.0)** giữa kết quả suy luận độc lập của TV2 và file `validation.json` của TV3 trong gói nộp.

| Run | Crop Logits | Crop Probs | Image Probs | Predicted Classes | Truth Matches | Metric Diff Count | Max Abs Delta | Replay Status |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| R3 | 0 / 5,440 | 0 / 5,440 | 0 / 4,800 | 0 / 600 | 600 / 600 | 0 | 0.0 | **PASS** |
| R4 | 0 / 5,440 | 0 / 5,440 | 0 / 4,800 | 0 / 600 | 600 / 600 | 0 | 0.0 | **PASS** |

Trình tự `image_id` và `crop_id` khớp tuyệt đối 100%. Chi tiết so sánh máy đọc được lưu tại [`outputs/tv2_w6/independent_replay_20261107/exact_comparison.json`](../../outputs/tv2_w6/independent_replay_20261107/exact_comparison.json).

---

## 4. Tổng hợp Multi-Seed Recipe R2 (Seeds 42, 43, 44)

Recipe R2 sử dụng kiến trúc DINOv2 linear probe cải tiến với 2 blocks trainable, augmentations và LR schedule đã phê chuẩn.

| Run | Recipe | Seed | Correct | Accuracy | Macro-Precision | Macro-Recall | Macro-F1 | Δ Correct vs R0 | Δ Macro-F1 vs R0 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **R0** | R0 | 42 | 507/600 | 0.845000 | 0.847957 | 0.845000 | 0.844401 | 0 | 0.000000 |
| **R1** | R1 | 42 | 501/600 | 0.835000 | 0.835766 | 0.835000 | 0.833864 | -6 | -0.010537 |
| **R2** | R2 | 42 | 511/600 | 0.851667 | 0.853158 | 0.851667 | 0.850651 | +4 | +0.006250 |
| **R3** | R2 | 43 | 506/600 | 0.843333 | 0.845788 | 0.843333 | 0.842757 | -1 | -0.001644 |
| **R4** | R2 | 44 | 511/600 | 0.851667 | 0.854455 | 0.851667 | 0.850645 | +4 | +0.006244 |

### Thống kê đa seed Recipe R2:
- **Accuracy:** Mean = **0.848889** (84.89%), Sample SD (ddof=1) = **0.004811** (0.48%)
- **Macro-F1:** Mean = **0.848017** (84.80%), Sample SD (ddof=1) = **0.004556** (0.46%)
- **Số ảnh đúng:** Mean = **509.33 / 600** $\pm$ **2.89**
- **Khoảng cách tới mục tiêu 88% (528 ảnh đúng):** Thiếu trung bình **18.67 ảnh đúng**. Cả 3 seed đều không đạt 88% (seed 42 thiếu 17 ảnh, seed 43 thiếu 22 ảnh, seed 44 thiếu 17 ảnh).

> **Ghi chú thận trọng từ TV2:**
> Kết quả R3 (seed 43) cho thấy hiệu năng thực tế của Recipe R2 có thể dao động xuống dưới baseline R0 (506 so với 507 ảnh đúng). Việc báo cáo trung bình $\pm$ sample SD là bắt buộc để tránh thiên kiến chọn seed tốt nhất (seed 42 hay seed 44). Mọi kết luận đều giới hạn trên một tập Validation cố định (600 ảnh) và chưa phản ánh phân phối tự nhiên hay khả năng tổng quát hóa đa địa điểm.

---

## 5. Phân tích Paired Regression và Nhóm nhầm lẫn

### Kết quả Paired vs R0 (600 ảnh)
- **R3 vs R0:** 6 wrong $\to$ correct, 7 correct $\to$ wrong (net = -1, tổng 21 ảnh đổi nhãn).
- **R4 vs R0:** 10 wrong $\to$ correct, 6 correct $\to$ wrong (net = +4, tổng 26 ảnh đổi nhãn).

### Kết quả Paired vs R2 (seed 42)
- **R3 vs R2:** 2 wrong $\to$ correct, 7 correct $\to$ wrong (net = -5, tổng 17 ảnh đổi nhãn).
- **R4 vs R2:** 2 wrong $\to$ correct, 2 correct $\to$ wrong (net = 0, tổng 11 ảnh đổi nhãn).

### Nhóm loài dễ nhầm lẫn:
1. **Common palm civet vs Masked palm civet (classes 4 & 5):**
   - R0: $5 + 8 = 13$ lỗi nhầm lẫn
   - R2: $8 + 7 = 15$ lỗi nhầm lẫn
   - R3: $7 + 7 = 14$ lỗi nhầm lẫn
   - R4: $6 + 8 = 14$ lỗi nhầm lẫn
   $\to$ Cả ba seed của R2 đều có số ca nhầm lẫn giữa 2 loài cầy cao hơn baseline R0.
2. **Large-antlered muntjac vs Sambar (classes 0 & 2):**
   - R0: $8 + 4 = 12$ lỗi nhầm lẫn
   - R2: $10 + 3 = 13$ lỗi nhầm lẫn
   - R3: $10 + 3 = 13$ lỗi nhầm lẫn
   - R4: $10 + 2 = 12$ lỗi nhầm lẫn
   $\to$ Sambar cải thiện độ nhạy (Recall tăng từ 78.7% lên 81.3%–84.0%), nhưng Muntjac bị giảm độ nhạy (Recall giảm từ 72.0% xuống 69.3% ở R3/R4, mất 2 ảnh đúng so với R0, chủ yếu bị dự đoán nhầm thành Sambar).

---

## 6. Hạch toán GPU (GPU Accounting)

### TV2 Replay Budget (Hạn mức 2.0 GPU-giờ)
| Tiến trình / Lần chạy | Run | GPU Giờ | Thời gian (giây) | Ghi chú |
|---|---|---:|---:|---|
| R1_replay01 | R1 | 0.0368770085 | 132.76 | Replay thành công, console log cp1258 |
| R1_replay02 | R1 | 0.0443250109 | 159.57 | Rerun clean UTF-8 log |
| R2_replay01 | R2 | 0.0365492534 | 131.58 | Replay thành công |
| R3_replay01 | R3 | 0.0117644758 | 42.35 | Replay độc lập exact PASS |
| R4_replay01 | R4 | 0.0113666640 | 40.92 | Replay độc lập exact PASS |
| **Tổng cộng TV2** | | **0.1408824127** | | **Còn lại: 1.8591175873 GPU-giờ / 2.0** |

### TV3 Producer Budget (Hạn mức 12.0 GPU-giờ, tối đa 6 attempts)
- Official attempts: 4 / 6 attempts đã sử dụng (R1: 0.0712h, R2: 0.8295h, R3: 0.6802h, R4: 0.6865h; tổng official = 2.267384h).
- Preparation / smoke: 4 sessions (R1, R2, R3, R4 smoke; tổng prep = 0.009595h).
- Tổng thời gian TV3 sử dụng: **2.276979 GPU-giờ / 12.0 GPU-giờ** (Còn lại: **9.723021 GPU-giờ**). Mọi attempt đơn lẻ đều $\le 2.0$ GPU-giờ.

---

## 7. Bằng chứng và Artifacts

- Receipt file: [`outputs/tv2_w6/independent_replay_20261107/environment_receipt.json`](../../outputs/tv2_w6/independent_replay_20261107/environment_receipt.json) (SHA-256: `63b4edb764a1a35d3ad7f6581bcf82c1d147040933d89eee3e57a1f9ff55a3e2`)
- Exact comparison: [`outputs/tv2_w6/independent_replay_20261107/exact_comparison.json`](../../outputs/tv2_w6/independent_replay_20261107/exact_comparison.json)
- Acceptance evidence: [`outputs/tv2_w6/independent_acceptance_20261107/acceptance_evidence.json`](../../outputs/tv2_w6/independent_acceptance_20261107/acceptance_evidence.json)
- Artifact audit: [`outputs/tv2_w6/independent_acceptance_20261107/artifact_audit.json`](../../outputs/tv2_w6/independent_acceptance_20261107/artifact_audit.json)
