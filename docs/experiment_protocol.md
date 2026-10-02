# Đề cương Thí nghiệm – CameraTrapML

> **Dự án:** Ứng dụng học máy hỗ trợ nhận dạng một số loài động vật ưu tiên bảo tồn tại Trường Sơn từ ảnh bẫy camera  
> **Mã công việc:** W1-02 (Tuần 1 – TV2)  
> **Phiên bản:** 1.0 – Ngày lập: 01/10/2026  
> **Tác giả:** Thành viên 2 – Phụ trách Baseline & Evaluation

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Thiết kế các mô hình Baseline](#2-thiết-kế-các-mô-hình-baseline)
3. [Quy tắc kiểm soát & tái lập (Reproducibility)](#3-quy-tắc-kiểm-soát--tái-lập-reproducibility)
4. [Chiến lược chia dữ liệu & bảo vệ tập Test](#4-chiến-lược-chia-dữ-liệu--bảo-vệ-tập-test)
5. [Chiến lược chọn Checkpoint & Early Stopping](#5-chiến-lược-chọn-checkpoint--early-stopping)
6. [Augmentation & Tiền xử lý](#6-augmentation--tiền-xử-lý)
7. [Metric đánh giá](#7-metric-đánh-giá)
8. [Lịch trình thực nghiệm](#8-lịch-trình-thực-nghiệm)
9. [Cấu trúc lưu trữ thí nghiệm](#9-cấu-trúc-lưu-trữ-thí-nghiệm)

---

## 1. Tổng quan

### 1.1. Mục tiêu

Xây dựng và đánh giá hệ thống các mô hình baseline phân loại ảnh bẫy camera (*camera trap*) nhằm nhận dạng một số loài động vật ưu tiên bảo tồn tại vùng Trường Sơn, Việt Nam. Các mô hình được thiết kế theo mức độ phức tạp tăng dần (B0 → B1 → B2 → B3) để đo lường tác động của từng kỹ thuật lên hiệu suất phân loại.

### 1.2. Backbone thống nhất

Tất cả các baseline sử dụng chung kiến trúc **ResNet-18** (pretrained trên ImageNet-1K) nhằm:
- Đảm bảo tính **so sánh công bằng** giữa các phương án.
- Phù hợp với tài nguyên GPU hạn chế (< 8 GB VRAM).
- Đơn giản hóa quá trình debug và tái lập.

### 1.3. Bài toán

| Thuộc tính | Giá trị |
|---|---|
| Loại bài toán | Phân loại đa lớp (Multi-class Classification) |
| Đầu vào | Ảnh RGB từ bẫy camera |
| Đầu ra | Nhãn loài (species label) |
| Loss function | CrossEntropyLoss (mặc định) / CrossEntropyLoss + class weights (B3) |

> **Lưu ý quan trọng về bối cảnh đánh giá (MegaDetector):** MegaDetector được sử dụng trong pipeline thực tế (và demo end-to-end) vốn đã chứa dữ liệu SWG trong tập huấn luyện. Do đó, phải tách biệt rõ ràng giữa "Đánh giá phân loại trên Bounding Box chuẩn (Ground-truth Bbox)" với "Đánh giá demo toàn luồng (End-to-end)". Không dùng điểm số của mô hình phân loại (B0-B3) làm căn cứ duy nhất để khẳng định khả năng phát hiện động vật của toàn hệ thống MegaDetector.

---

## 2. Thiết kế các mô hình Baseline

### 2.1. B0 – Baseline khởi động (Frozen Backbone)

| Thuộc tính | Chi tiết |
|---|---|
| **Tuần triển khai** | Tuần 2 |
| **Mục tiêu** | Thiết lập mức hiệu suất sàn (*lower bound*) khi chỉ dùng đặc trưng ImageNet sẵn có |
| **Backbone** | ResNet-18, pretrained ImageNet-1K |
| **Chiến lược huấn luyện** | **Đóng băng toàn bộ backbone** (`requires_grad = False` cho tất cả layer trừ FC cuối) |
| **Lớp phân loại** | Thay thế `fc` gốc bằng `nn.Linear(512, num_classes)` |
| **Input** | Toàn ảnh (full-image), resize về `224 × 224` |
| **Optimizer** | Adam, `lr = 1e-3` |
| **Epochs** | 30 (có Early Stopping) |
| **Batch size** | 32 |

**Lý do thiết kế:** B0 đóng vai trò *sanity check* – nếu mô hình không học được gì có nghĩa (F1 ≈ random), cần xem lại pipeline dữ liệu trước khi tiến xa hơn.

---

### 2.2. B1 – Full-image Fine-tuning

| Thuộc tính | Chi tiết |
|---|---|
| **Tuần triển khai** | Tuần 3 |
| **Mục tiêu** | Đo lường mức cải thiện khi fine-tune toàn bộ mạng trên domain camera trap |
| **Backbone** | ResNet-18, pretrained ImageNet-1K |
| **Chiến lược huấn luyện** | **Mở toàn bộ tham số** (hoặc unfreeze dần – *gradual unfreezing*) |
| **Input** | Toàn ảnh (full-image), resize về `224 × 224` |
| **Optimizer** | SGD + Momentum (0.9), `lr = 1e-3`, hoặc Adam `lr = 1e-4` |
| **LR Scheduler** | StepLR (giảm `lr × 0.1` mỗi 10 epoch) hoặc CosineAnnealingLR |
| **Epochs** | 50 (có Early Stopping) |
| **Batch size** | 32 |

**So sánh với B0:** Cùng input (full-image) nhưng khác ở chiến lược huấn luyện → cho phép đo riêng tác động của fine-tuning.
> **Quy tắc công bằng dữ liệu:** B1 và B2 bắt buộc phải sử dụng **chung một tập danh sách ảnh đủ điều kiện**. Nếu một ảnh bị loại bỏ ở B2 (do lỗi bounding box), ảnh đó cũng phải bị loại khỏi tập huấn luyện của B1.

---

### 2.3. B2 – Cropped-box Fine-tuning

| Thuộc tính | Chi tiết |
|---|---|
| **Tuần triển khai** | Tuần 3 |
| **Mục tiêu** | Đánh giá tác động của việc loại bỏ nền (*background removal*) bằng cách chỉ dùng vùng cắt chứa động vật |
| **Backbone** | ResNet-18, pretrained ImageNet-1K |
| **Chiến lược huấn luyện** | Fine-tune toàn bộ (giống B1) |
| **Input** | **Vùng cắt (bounding box)** từ metadata/SWG annotation, resize về `224 × 224` |
| **Tiền xử lý bổ sung** | Mở rộng bbox thêm 10-15% padding để tránh cắt mất phần cơ thể |
| **Optimizer** | Giống B1 |
| **Epochs** | 50 (có Early Stopping) |
| **Batch size** | 32 |

**So sánh với B1:** Cùng chiến lược fine-tune nhưng khác ở input (cropped vs. full-image) → cho phép đo riêng tác động của cropping.
> **Quy tắc công bằng dữ liệu:** Dùng chung danh sách ảnh huấn luyện đã lọc kỹ bounding box với B1.

---

### 2.4. B3 – Class-Weighted Loss (Tùy chọn mở rộng)

| Thuộc tính | Chi tiết |
|---|---|
| **Tuần triển khai** | Tuần 3–4 (nếu có thời gian) |
| **Mục tiêu** | Xử lý **mất cân bằng lớp** (class imbalance) – phổ biến trong dữ liệu camera trap |
| **Dựa trên** | B1 hoặc B2 (chọn mô hình có F1 tốt hơn) |
| **Thay đổi** | Thêm `weight` vào `CrossEntropyLoss` |
| **Cách tính weight** | Nghịch đảo tần suất: $w_c = \frac{N_{\text{total}}}{C \times N_c}$ trong đó $N_c$ là số mẫu lớp $c$, $C$ là tổng số lớp |
| **Mọi cấu hình khác** | Giữ nguyên so với mô hình gốc (B1/B2) |

**Lý do:** Dữ liệu camera trap thường có phân bố rất lệch – một vài loài phổ biến chiếm đa số mẫu. Class weights giúp mô hình chú ý hơn đến lớp thiểu số.

---

### 2.5. Bảng tổng hợp so sánh

> **LƯU Ý - FAIR COMPARISON:** B1 (toàn ảnh) và B2 (vùng cắt) **bắt buộc phải sử dụng chung một tập danh sách ảnh đủ điều kiện** (có 1 loài xác định, bounding box hợp lệ). Nếu ảnh nào bị TV3 loại bỏ do box lỗi/hỏng, ảnh đó cũng phải loại khỏi tập huấn luyện của B1 để đảm bảo tính so sánh công bằng.

| Baseline | Input | Backbone | Trainable Params | Loss | Tuần |
|---|---|---|---|---|---|
| **B0** | Full-image | ResNet-18 frozen | FC only (~`512 × C`) | CE | 2 |
| **B1** | Full-image | ResNet-18 unfrozen | All (~11.2M) | CE | 3 |
| **B2** | Cropped bbox | ResNet-18 unfrozen | All (~11.2M) | CE | 3 |
| **B3** | Best of B1/B2 | ResNet-18 unfrozen | All (~11.2M) | Weighted CE | 3–4 |

---

## 3. Quy tắc Kiểm soát & Tái lập (Reproducibility)

### 3.1. Cố định Random Seed

Mọi thí nghiệm **bắt buộc** gọi hàm seed trước khi huấn luyện:

```python
import random
import numpy as np
import torch

def set_seed(seed: int = 42) -> None:
    """Cố định toàn bộ random seed để đảm bảo tái lập."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

> **Lưu ý:** `cudnn.deterministic = True` có thể làm chậm huấn luyện 10–20%. Chấp nhận đánh đổi này để đảm bảo tính tái lập.

### 3.2. Lưu trữ metadata thí nghiệm

Mỗi lần chạy thí nghiệm **phải** lưu đầy đủ:

| Thành phần | Mô tả | Vị trí lưu |
|---|---|---|
| `config.yaml` | Toàn bộ hyperparameters (lr, batch_size, epochs, seed, ...) | `experiments/<exp_id>/config.yaml` |
| `git_commit` | Hash commit hiện tại | Ghi trong `config.yaml` |
| `best_model.pth` | Weights của best checkpoint | `experiments/<exp_id>/checkpoints/` |
| `train_log.csv` | Loss, metric mỗi epoch (train & val) | `experiments/<exp_id>/logs/` |
| `final_metrics.json` | Metric tổng kết trên tập Validation | `experiments/<exp_id>/results/` |

### 3.3. Ví dụ cấu trúc `config.yaml`

```yaml
experiment:
  name: "B0_frozen_resnet18"
  id: "B0_run01"
  seed: 42
  git_commit: "abc1234"

model:
  backbone: "resnet18"
  pretrained: true
  freeze_backbone: true  # B0: true, B1/B2: false
  num_classes: 8          # Theo data/processed/v1/class_map.json của nhóm

data:
  input_type: "full_image"  # full_image | cropped_bbox
  image_size: 224
  batch_size: 32
  num_workers: 4

training:
  optimizer: "adam"
  lr: 0.001
  weight_decay: 0.0001
  epochs: 30
  early_stopping_patience: 7
  checkpoint_metric: "macro_f1"  # Metric chọn best checkpoint
  checkpoint_mode: "max"

loss:
  type: "cross_entropy"
  class_weights: null  # B3: sử dụng inverse frequency
```

---

## 4. Chiến lược Chia dữ liệu & Bảo vệ tập Test

### 4.1. Phân chia dữ liệu

Dữ liệu được chia theo tỉ lệ:

| Tập | Tỉ lệ | Mục đích |
|---|---|---|
| **Train** | ~70% | Huấn luyện mô hình |
| **Validation** | ~15% | Điều chỉnh hyperparameters, Early Stopping, chọn checkpoint |
| **Test** | ~15% | Đánh giá cuối cùng (chỉ dùng 1 lần) |

> **Quan trọng - Quy tắc phân chia:** Phân chia theo **địa điểm trạm bẫy ảnh (Site-level / Location-based split)** kết hợp cân đối tỷ lệ lớp (stratified group split).
> - Tất cả các ảnh thuộc cùng một trạm camera (station/location) và cùng một chuỗi (sequence) **bắt buộc** phải nằm trọn trong cùng một tập (Train, Val hoặc Test).
> - Tuyệt đối **không** chia ngẫu nhiên trên toàn ảnh (random split) để tránh rò rỉ dữ liệu (data leakage) do trùng phông nền môi trường.
> - TV1 phụ trách cung cấp manifest chia tập này.

### 4.2. Nguyên tắc khóa tập Test (Test Set Isolation)

> [!CAUTION]
> **QUY TẮC TUYỆT ĐỐI: Tập Test chỉ được nạp và đánh giá MỘT LẦN DUY NHẤT vào Tuần 4, sau khi đã chọn xong best checkpoint.**

Chi tiết quy tắc:

| # | Quy tắc | Mô tả |
|---|---|---|
| 1 | **Không xem trước** | Không được phân tích, thống kê hay trực quan hóa tập Test trong quá trình phát triển |
| 2 | **Không dùng để chọn mô hình** | Mọi quyết định chọn hyperparameter, architecture, checkpoint đều dựa trên Validation |
| 3 | **Đánh giá một lần** | Chạy inference trên Test **đúng 1 lần** với mô hình đã khóa (locked model) |
| 4 | **Không quay lại** | Sau khi đánh giá trên Test, **không được** quay lại điều chỉnh mô hình dựa trên kết quả Test |
| 5 | **Ghi nhận trung thực** | Kết quả Test (dù tốt hay xấu) được báo cáo nguyên trạng |

**Quy trình bảo vệ:**

```
Tuần 2-3: Train/Val loop → chọn best checkpoint (theo Val Macro-F1)
              ↓
Tuần 4:   Khóa mô hình → Nạp tập Test → Đánh giá 1 lần → Báo cáo
```

### 4.3. Phòng chống Data Leakage

- **Chia theo Location (Site-level split):** Đã đề cập ở Mục 4.1, đảm bảo tuyệt đối không có ảnh của cùng một trạm/chuỗi xuất hiện ở cả Train và Test/Val.
- **Augmentation chỉ áp dụng trên Train:** Xem chi tiết mục 6.

---

## 5. Chiến lược Chọn Checkpoint & Early Stopping

### 5.1. Metric chọn checkpoint

| Metric | Vai trò |
|---|---|
| **Macro-F1** | ✅ **Metric chính** – dùng để chọn best checkpoint và Early Stopping |
| Accuracy | Metric tham khảo (dễ bị chi phối bởi lớp đa số) |
| Macro-Precision, Macro-Recall | Metric phụ – dùng để phân tích |

**Lý do chọn Macro-F1:** Dữ liệu camera trap thường mất cân bằng lớp nghiêm trọng. Macro-F1 đối xử công bằng với mọi lớp (kể cả lớp hiếm), trong khi Accuracy dễ đạt cao chỉ nhờ dự đoán đúng lớp phổ biến.

### 5.2. Early Stopping

```
Theo dõi: Val Macro-F1
Patience: 7 epochs (B0: 5 epochs do mô hình đơn giản hơn)
Mode    : max (dừng khi F1 không tăng thêm)
```

**Logic:**
1. Sau mỗi epoch, đánh giá trên tập Validation.
2. Nếu `val_macro_f1` đạt giá trị cao nhất → lưu checkpoint (`best_model.pth`).
3. Nếu `val_macro_f1` không cải thiện trong `patience` epoch liên tiếp → dừng huấn luyện.
4. Tải lại `best_model.pth` để dùng cho đánh giá cuối.

### 5.3. Lưu checkpoint

```python
# Pseudocode
if val_macro_f1 > best_macro_f1:
    best_macro_f1 = val_macro_f1
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "val_macro_f1": val_macro_f1,
        "val_loss": val_loss,
        "config": config,
    }, "best_model.pth")
    patience_counter = 0
else:
    patience_counter += 1
    if patience_counter >= patience:
        print("Early Stopping triggered.")
        break
```

---

## 6. Augmentation & Tiền xử lý

### 6.1. Nguyên tắc chung

| Tập | Augmentation | Normalize |
|---|---|---|
| **Train** | ✅ Có (xem bảng dưới) | ✅ ImageNet mean/std |
| **Validation** | ❌ Không | ✅ ImageNet mean/std |
| **Test** | ❌ Không | ✅ ImageNet mean/std |

> **Quy tắc:** Validation và Test chỉ áp dụng resize + center crop + normalize. **Không** augment để đảm bảo đánh giá trên phân phối gốc.

### 6.2. Augmentation trên tập Train

```python
import torchvision.transforms as T

train_transform = T.Compose([
    T.Resize(256),
    T.RandomCrop(224),
    T.RandomHorizontalFlip(p=0.5),
    T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.05),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],   # ImageNet
                std=[0.229, 0.224, 0.225]),
])

val_test_transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]),
])
```

### 6.3. Giải thích lựa chọn Augmentation

| Kỹ thuật | Lý do |
|---|---|
| `RandomHorizontalFlip` | Động vật có thể xuất hiện từ trái/phải; tăng đa dạng hướng nhìn |
| `ColorJitter` | Ảnh camera trap có điều kiện ánh sáng rất khác nhau (ngày/đêm, mưa/nắng) |
| `RandomCrop` | Mô phỏng sự khác biệt về vị trí động vật trong khung hình |
| **Không dùng** `RandomVerticalFlip` | Động vật hiếm khi xuất hiện lộn ngược → tạo mẫu phi thực tế |

---

## 7. Metric đánh giá

### 7.1. Bộ metric chuẩn

Khung metric Tuần 1 nằm trong `notebooks/TV2_baseline_evaluation.ipynb`. Trước khi đánh giá dữ liệu thật, đọc `data/processed/v1/class_map.json` của nhóm; notebook chỉ dùng danh sách lớp mẫu để chạy demo khi file này chưa có trên nhánh TV2.

| Metric | Công thức | Vai trò |
|---|---|---|
| **Macro-F1** | $\text{Macro-F1} = \frac{1}{C} \sum_{c=1}^{C} F1_c$ | **Metric chính** (chọn checkpoint) |
| Macro-Precision | $\frac{1}{C} \sum_{c=1}^{C} \text{Precision}_c$ | Phân tích bổ sung |
| Macro-Recall | $\frac{1}{C} \sum_{c=1}^{C} \text{Recall}_c$ | Phân tích bổ sung |
| Accuracy | $\frac{\text{Số dự đoán đúng}}{N}$ | Tham khảo (nhạy cảm với class imbalance) |
| Per-class F1 | $F1_c = \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$ | Đánh giá chi tiết từng loài |
| Confusion Matrix | Ma trận $C \times C$ | Trực quan hóa lỗi phân loại |

Với class map v1, $C = 8$. Macro-Precision, Macro-Recall và Macro-F1 dùng đủ 8 ID lớp theo thứ tự số, kể cả lớp không có mẫu trong tập đang đánh giá. Lớp vắng mặt nhận điểm 0 theo `zero_division=0`; ví dụ chỉ dự đoán đúng lớp 0 thì Accuracy bằng 1 nhưng Macro-F1 bằng $1/8$. Confusion matrix luôn có kích thước $8 \times 8$.

### 7.2. Xử lý zero-division

Khi một lớp không có mẫu trong tập dự đoán hoặc ground-truth, metric có thể gặp phép chia cho 0. Thống nhất sử dụng `zero_division=0` (sklearn convention) để trả về `0.0` thay vì `NaN`.

### 7.3. Báo cáo kết quả

Mỗi thí nghiệm phải báo cáo đầy đủ:

1. **Bảng Macro metrics** (F1, Precision, Recall, Accuracy) trên Validation.
2. **Bảng Per-class metrics** cho từng loài.
3. **Confusion Matrix** (heatmap chuẩn hóa theo True Label).
4. **Learning curves** (Train Loss, Val Loss, Val Macro-F1 theo epoch).

---

## 8. Lịch trình Thực nghiệm

| Tuần | Công việc | Sản phẩm |
|---|---|---|
| **Tuần 1** | Xây khung đánh giá, cấu hình môi trường | `notebooks/TV2_baseline_evaluation.ipynb`, report trong `reports/`, tài liệu này |
| **Tuần 2** | Huấn luyện B0 (frozen backbone) | `best_model_B0.pth`, `train_log_B0.csv`, báo cáo Val metrics |
| **Tuần 3** | Huấn luyện B1 (full-image FT) & B2 (cropped FT) | Weights + logs + so sánh Val metrics B0/B1/B2 |
| **Tuần 3–4** | *(Tùy chọn)* B3 (class weights) | Weights + logs |
| **Tuần 4** | **Đánh giá cuối trên Test** (1 lần duy nhất) | Bảng Test metrics, Confusion Matrix, báo cáo so sánh |
| **Tuần 5–6** | Phân tích lỗi, hoàn thiện báo cáo | Error analysis, tài liệu cuối |

---

## 9. Cấu trúc Lưu trữ Thí nghiệm

```
Do_an/
├── requirements.txt
├── notebooks/
│   └── TV2_baseline_evaluation.ipynb
├── reports/
│   ├── gpu_env_report.txt
│   └── demo_confusion_matrix.png
├── docs/
│   └── experiment_protocol.md   ← Tài liệu này
└── experiments/         # Dự kiến từ Tuần 2, chưa tạo trong W1
    ├── B0_run01/
    │   ├── config.yaml
    │   ├── checkpoints/
    │   │   └── best_model.pth
    │   ├── logs/
    │   │   └── train_log.csv
    │   └── results/
    │       ├── val_metrics.json
    │       ├── test_metrics.json       # Tuần 4
    │       └── confusion_matrix.png
    ├── B1_run01/
    ├── B2_run01/
    └── B3_run01/        # (Tùy chọn)
```

---

## Phụ lục A: Checklist trước khi chạy thí nghiệm

- [ ] Cell môi trường trong notebook đã chạy; ghi đúng trạng thái CPU/GPU thực tế
- [ ] Random seed đã được cố định (`set_seed(42)`)
- [ ] `config.yaml` đã được tạo và ghi nhận git commit hash
- [ ] Data splits đã được tạo (stratified) và lưu file CSV
- [ ] Augmentation chỉ áp dụng trên Train
- [ ] Tập Test **chưa** được nạp/xem xét
- [ ] Cell metric trong notebook đã chạy test cho lớp vắng mặt và đầu vào sai
- [ ] Đường dẫn lưu checkpoint + log đã tồn tại

---

## Phụ lục B: Bảng ký hiệu

| Ký hiệu | Ý nghĩa |
|---|---|
| $C$ | Số lớp (number of classes) |
| $N$ | Tổng số mẫu |
| $N_c$ | Số mẫu của lớp $c$ |
| $P_c$ | Precision của lớp $c$ |
| $R_c$ | Recall của lớp $c$ |
| $F1_c$ | F1-score của lớp $c$ |
| CE | CrossEntropyLoss |
| FT | Fine-tuning |
| FC | Fully Connected layer |
| LR | Learning Rate |

---

*Tài liệu này là sản phẩm bàn giao của Tuần 1 (W1-02) và sẽ được cập nhật khi có thay đổi thiết kế trong quá trình thực nghiệm.*
