# Báo Cáo Bàn Giao Checkpoint B2 (TV3 Tuần 3)
**Mô hình phân loại động vật trên vùng cắt (B2 Crop Classifier)**

---

## 1. Thông Tin Checkpoint Chính Thức

| Thuộc tính | Chi tiết |
| :--- | :--- |
| **Mã thí nghiệm (Run ID)** | `b2_run01` |
| **File Checkpoint tốt nhất** | `outputs/b2_crop_classifier/b2_run01/best_model.pt` |
| **Kích thước file (bytes)** | `89,548,866 bytes` (~85.4 MB) |
| **SHA-256 Checksum** | `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5` |
| **Epoch tốt nhất (Best Epoch)** | **Epoch 21** (Early stopping tại epoch 28 / ngân sách 50 epochs) |
| **Tổng thời gian huấn luyện** | 2,652.16 giây (~44.2 phút trên GPU RTX) |
| **Trạng thái kiểm định reload** | **PASS** (Tải lại và forward pass kiểm tra metadata thành công 100%) |
| **Dấu kiểm định** | `is_official = True` |

---

## 2. Tuân Thủ Tiêu Chí Hoàn Thành & Protocol Đối Sánh

Toàn bộ quá trình huấn luyện tuân thủ nghiêm ngặt 3 tiêu chí của đề cương và thỏa thuận `reports/tv2/W3_PROTOCOL_AGREEMENT_2026-10-18.json`:

1. **Khóa dữ liệu W3-01:**
   - Chạy trên dữ liệu đóng băng `data/processed/comparison_v1` (TV1 commit `7e9b194`).
   - Gate xác thực SHA-256 đối chiếu chéo thành công:
     - `provenance.json`: `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`
     - `b2/train.jsonl`: `023c3cbf31c42e6e35547a5d928fa93cc00a31a0657879d5e775b4a9d37ce3d3`
     - `b2/val.jsonl`: `7a4c1b2edf1712e675b5b84c581733f3112b950d2318d4f9ae51d33dd366067e`
     - `class_map.json`: `122c3a8c6b297c1d63c3b18db91cf6b3f279a2f979e6b3e77824dbdd086fc58e`
2. **Cùng tập ảnh và ngân sách với baseline B1 của TV2:**
   - Tập huấn luyện: 2.800 ảnh nguồn / 3.125 crops.
   - Tập validation: 600 ảnh nguồn / 680 crops.
   - 8 lớp động vật, seed = 42, FP32, không dropout.
   - Optimizer: SGD lr=0.001, momentum=0.9, weight_decay=0.0001.
   - Scheduler: StepLR (step_size=10, gamma=0.1).
3. **Loss và gom nhóm theo ảnh:**
   - Sử dụng `ImageGroupedBatchSampler` giữ trọn vẹn toàn bộ crop của cùng parent image trong 1 batch duy nhất.
   - Loss cấp ảnh: trung bình CE các crop trong ảnh, rồi trung bình qua các ảnh trong batch (`compute_image_grouped_loss`).
   - Đánh giá cấp ảnh: trung bình vector xác suất softmax của tất cả crop trong ảnh rồi chọn argmax.

---

## 3. Bảng So Sánh Đối Sánh Chính Thức: B1 (Toàn Ảnh) vs B2 (Vùng Cắt)

| Chỉ số | B1 Baseline (Toàn ảnh - TV2) | B2 (Cấp Crop) | B2 (Cấp Ảnh Tổng Hợp - TV3) | Chênh lệch (B2 vs B1) |
| :--- | :---: | :---: | :---: | :---: |
| **Độ chính xác (Accuracy)** | 56.50% | 72.94% | **74.67%** | <span style="color:green">**+18.17%**</span> |
| **Macro F1-Score** | 56.24% | 72.54% | **74.55%** | <span style="color:green">**+18.31%**</span> |
| **Macro Precision** | 56.88% | 72.71% | **74.84%** | <span style="color:green">**+17.96%**</span> |
| **Macro Recall** | 56.50% | 73.02% | **74.67%** | <span style="color:green">**+18.17%**</span> |
| **Số lượng mẫu đánh giá** | 600 ảnh | 680 crops | **600 ảnh** | — |

> **Nhận xét kết quả:** 
> - Mô hình B2 trên vùng cắt vượt trội hoàn toàn so với mô hình B1 trên toàn ảnh (+18.31% Macro F1).
> - Lý do: Động vật trong ảnh camera trap chiếm tỷ lệ diện tích nhỏ trên khung hình 3264x2448. Việc crop trúng vùng phát hiện giúp mô hình loại bỏ hoàn toàn nhiễu từ bối cảnh rừng rậm, cành lá và ánh sáng phức tạp, tập trung tối đa vào đặc trưng hình thái của loài.

---

## 4. Chi Tiết Hiệu Năng Từng Lớp (Per-class Metrics - Cấp Ảnh)

| Lớp (Species) | Class ID | Số mẫu (Support) | Precision | Recall | **F1-Score** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `silver_pheasant` (Gà lôi trắng) | 6 | 75 | 98.55% | 90.67% | **94.44%** |
| `annamite_striped_rabbit` (Thỏ vằn) | 1 | 75 | 73.12% | 90.67% | **80.95%** |
| `common_palm_civet` (Cầy vòi đốm) | 4 | 75 | 81.43% | 76.00% | **78.62%** |
| `chinese_serow` (Sơn dương) | 3 | 75 | 79.45% | 77.33% | **78.38%** |
| `masked_palm_civet` (Cầy vòi mốc) | 5 | 75 | 69.88% | 77.33% | **73.42%** |
| `eurasian_wild_pig` (Lợn rừng) | 7 | 75 | 70.67% | 70.67% | **70.67%** |
| `sambar` (Nai) | 2 | 75 | 69.12% | 62.67% | **65.73%** |
| `large_antlered_muntjac` (Mang lớn) | 0 | 75 | 56.52% | 52.00% | **54.17%** |

---

## 5. Hướng Dẫn Bàn Giao & Tích Hợp Cho TV4 (Adapter & Demo)

Checkpoint `outputs/b2_crop_classifier/b2_run01/best_model.pt` đã đóng gói sẵn toàn bộ siêu dữ liệu để TV4 nạp trực tiếp mà không cần cấu hình thủ công:

```python
import torch
from torchvision import models
import torch.nn as nn

# 1. Nạp checkpoint
ckpt = torch.load("outputs/b2_crop_classifier/b2_run01/best_model.pt", map_location="cpu", weights_only=False)

# 2. Đọc metadata cấu hình tự động
class_map = ckpt["class_map"]       # {"large_antlered_muntjac": 0, ...}
id_to_label = ckpt["id_to_label"]   # {0: "large_antlered_muntjac", ...}
preprocessing = ckpt["preprocessing"]
# preprocessing: {'resize': 256, 'crop_size': 224, 'mean': [0.485, 0.456, 0.406], 'std': [0.229, 0.224, 0.225]}

# 3. Khởi tạo kiến trúc mô hình ResNet-18
model = models.resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, ckpt["num_classes"])
model.load_state_dict(ckpt["model_state_dict"])
model.eval()
```
