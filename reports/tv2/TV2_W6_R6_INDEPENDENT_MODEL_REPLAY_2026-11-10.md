# TV2 W6 — Independent R6 model replay and acceptance

**Ngày:** 10/11/2026

**TV3 result commit:** [`450f15bde6899faffac3c9389156d04c15196568`](https://github.com/huyryan220806/Camera-Trap-ML/commit/450f15bde6899faffac3c9389156d04c15196568) (đã xác nhận trên GitHub)

**Kết luận:** `TV2_MODEL_REPLAY_ACCEPTED`

## 1. Tiếp nhận và toàn vẹn artifact

- SHA-256 tính trực tiếp từ `reports/tv3/w6/w6_2/R6_attempt01.zip`: `fcb6118cd89c1a825d02e6d1c0a7bd19b983bac7bebaf863b959c0dd8854144e`, khớp giá trị yêu cầu; kích thước 267.959.559 byte.
- Trước giải nén đã kiểm tra duplicate, path traversal/absolute path, symlink, mã hóa, giới hạn số lượng và kích thước entry, và CRC toàn bộ ZIP: **PASS**.
- Có 38 entry; **36/36** payload liệt kê trong `package_index.json` khớp SHA-256 và số byte. Hai entry không tự liệt kê là `package_index.json` (SHA-256 `d2f149a5041049d0eee7ef460a3c8a5e479fb7cb37904358ed20e7c845b0f071`) và `registry.delivery.json` (SHA-256 `0b150263271c5932cd685868b1c6304d8739df82831316842154115a148554c9`, byte-identical với `registry.result.json`).
- `best_model.pt`: `24e3f51418dd7492a7537dff629794547c4540e8929bfe3e566105a6486581ef` (86.851.190 byte), khớp index và handoff. `last_model.pt`: `ffcf48c86abfd8ea96f225739b0a77e32912981ca858b17ff52094279d4918fc`.

## 2. Replay thực thi độc lập

TV2 dùng source trong gói đã đối chiếu từng file với `source_index.json` (source commit `3b4b106c01e64901f213f6eebfdd10ffa55a7eb7`), vendor DINOv3 commit `6876159a11b4df116f30f667f8c9888617df0751`, `configs/w6/tv3/R6.3h.frozen.json`, class map và preprocessing đã khóa. Config raw SHA-256 `6d32d3b5525053e8ab43eadc190f70da649f0ce7d9ff48889bbb210694f682c4`; canonical SHA-256 `08a01874ccc2cf0f21e652ed082893bfc666e4489c01e7b5cb36404bebe67a70`.

Trong process riêng, dùng đúng `src.training.dino_w6.load_package` (`torch.load(weights_only=True)`, `load_state_dict(..., strict=True)`), `eval()`, `inference_mode()`, FP32, deterministic, AMP/TF32 tắt. Runtime: Python 3.12.10; PyTorch 2.6.0+cu124; torchvision 0.21.0+cu124; Pillow 12.2.0; NumPy 2.5.3; scikit-learn 1.9.0; CUDA 12.4/cuDNN 90100; **NVIDIA GeForce RTX 4060 Laptop GPU**. Toàn bộ 600 ảnh Validation được kiểm byte và RGB, sau đó suy luận trên 680 GT crop. Prediction TV3 chỉ được đọc sau khi TV2 đã suy luận và lưu kết quả độc lập.

Chuỗi `sys.version` khác nhau ở metadata build: TV2 ghi `3.12.10 (main, May 30 2025, 05:39:07)`, TV3 ghi `3.12.10 (tags/v3.12.10:0cc8128, Apr 8 2025, 12:21:36)`; cả hai cùng `MSC v.1943 64 bit (AMD64)`. Các phiên bản thư viện và cấu hình tính toán đã đối chiếu như trên, nhưng không khẳng định hai runtime giống hệt mọi metadata.

**Chính sách khóa:** equality tuyệt đối từng phần tử trên runtime đã pin (`atol=0`, `rtol=0`) cho logits, probabilities, nhãn và metrics. Artifact-level dùng mean crop scores `atol=1e-10`, tổng probability `atol=1e-5`, số học metric `atol=1e-10` đúng protocol; không nới tolerance.

| So sánh TV2 với TV3 | Số phần tử | Sai khác | Max abs delta |
|---|---:|---:|---:|
| Crop logits | 5.440 | 0 | 0 |
| Crop probabilities | 5.440 | 0 | 0 |
| Image probabilities | 4.800 | 0 | 0 |
| Crop/image predicted labels | 680 / 600 | 0 / 0 | — |
| Image truth, ID/order và metrics | 600, toàn bộ | 0 | 0 |

Kết quả TV2: **519/600 đúng, accuracy 0,865; macro-F1 0,8641867348386344**. Handoff, Validation TV3 và kết quả suy luận TV2 khớp. Replay model mất 125,4353894 giây = **0,034843164 GPU-giờ**. SHA-256 replay JSON: `2ff62bc044f44e2123c241526ab20c5699a2f3551df27fdd14913e658518db9e`.

Lũy kế TV2 replay theo receipt trước (0,1408824127 GPU-giờ) và lượt này: **0,1757255764 / 2 GPU-giờ**.

## 3. Training, reload và ledger

- `train_log.json` có đúng epoch 1–18; macro-F1 cao nhất ở **epoch 13**. `last_model.pt` ghi epoch 18, best epoch 13 và bad epochs 5; `best_model.pt` ghi epoch 13.
- `reload01.json` báo fresh process `PASS`, exact predictions/metrics và max logit delta 0; `reload01.predictions.json` khớp hash `0371900a5a743daf755b254d3b2b3e08ffd78d7160fb6b25b7322094bd228226`.
- R6 official: 8.117,3099281 giây = 2,254808313 GPU-giờ, dưới trần riêng 3 giờ. Reload: 44,013371 giây; official + reload = 2,267034250 GPU-giờ. Cả hai trong booking RTX 4060, 10/11/2026 12:30–16:00 Asia/Ho_Chi_Minh. Sáu trên sáu official attempts đã dùng. Toàn bộ TV3 gồm sessions và R5 reconciliation: **6,331037238 / 12 GPU-giờ**.
- Dòng R5 lịch sử trong `usage.json` còn `RUNNING`, `seconds=null`; reconciliation kèm ledger xác nhận 6.405,3003492 giây và `FAILED_NO_RESUME`. `registry.result.json` ghi R5 `FAILED`, `metrics=null`. **R5 không được tính là seed hoàn thành.**

## 4. Artifact-level và so sánh cặp với R0

Xác suất ảnh lưu khớp mean xác suất crop; argmax, confusion matrix 8×8, accuracy và macro-F1 được tính lại độc lập từ payload. R0 dùng `tv2_predictions.jsonl` có SHA-256 `9be94d303882476202a653bbd9b1d89d8bfa48c4f7114ccd193c84f5de1ef3b7`, cùng 600 image IDs và nhãn thật.

| Kết quả paired | Số ảnh |
|---|---:|
| R0 đúng, R6 sai | 7 |
| R0 sai, R6 đúng | 19 |
| Cả hai đúng | 500 |
| Cả hai sai | 74 |

R0 đúng 507/600 (accuracy 0,845; macro-F1 0,8444008279545706); R6 tăng **12 ảnh đúng**, accuracy +0,020 và macro-F1 +0,0197859068840638. Chênh số ảnh đúng theo class ID 0–7 là `[0, +1, +5, +1, +1, +1, 0, +3]`; không có lớp mất ≥4 ảnh đúng. Accuracy R6 **86,50% vẫn chưa đạt KPI 88%** (còn thiếu 9 ảnh đúng trên 600). Đây là so sánh mô tả trên cùng Validation; R0 và R6 dùng tập train khác nhau. R5 không được đưa vào multi-seed. Quyết định demo và TV4 adapter là gate riêng.

## 5. Receipt và giới hạn

- [Receipt TV2](TV2_W6_R6_MODEL_REPLAY_RECEIPT_2026-11-10.json), SHA-256 `84466f8f12b40c4927c8383293670a6273b434dcecdf9418c4cc201c3570c470`.
- [Artifact audit](w6_evidence/r6_replay_20261110/artifact_audit.json), [replay output](w6_evidence/r6_replay_20261110/replay.json), [exact comparison](w6_evidence/r6_replay_20261110/exact_comparison.json). Đây là bản sao byte-identical từ `outputs/tv2_w6/r6_replay_20261110/`; script kiểm tra gốc cũng được lưu cùng thư mục bằng chứng. `outputs/` bị `.gitignore`, còn checkpoint và dữ liệu ảnh không được đưa vào commit TV2.
- Không huấn luyện lại, không sửa checkpoint hoặc dữ liệu khóa, không mở Official Test W4. Kết luận chỉ áp dụng cho **TV2 independent model replay**; TV4 adapter và quyết định demo chưa được nghiệm thu ở đây.

**Kết luận cuối:** `TV2_MODEL_REPLAY_ACCEPTED`.
