# Báo Cáo Quyết Định Mô Hình Phân Loại Tuần 4 (TV3 - W4-03)
**Lựa chọn chính thức giữa B3 (Class-Weighted Crop Classifier) và B2 (Crop Classifier Baseline)**

---

## 1. Mục Tiêu & Tiêu Chí Nghiệm Thu Tuần 4

Theo đề cương và thỏa thuận kỹ thuật tuần 4:
- **Nhiệm vụ:** Thử nghiệm trọng số lớp (B3) và chốt bộ phân loại cuối cùng cho pipeline CameraTrapML.
- **Quy tắc nghiệm thu:**
  1. Mô hình B3 là **tùy chọn** (thăm dò kỹ thuật - exploratory variant).
  2. Quyết định lựa chọn phải được thực hiện chậm nhất vào **Ngày 3 của Tuần 4**.
  3. **Quy tắc ngăn chặn rò rỉ dữ liệu (No Data Leakage):** Tuyệt đối **KHÔNG** mở hoặc dùng tập Test để chọn mô hình. Quyết định hoàn toàn dựa trên tập Validation (600 ảnh / 680 crops). Tập Test chỉ được TV2 mở một lần duy nhất sau khi bộ phân loại đã chốt và đóng băng.
  4. Nếu B3 không vượt trội hơn B2 trên tập validation, bảo lưu mô hình B2 và dành toàn bộ thời lượng còn lại cho **Phân tích lỗi (Error Analysis)** chuyên sâu.
  5. Đóng gói checkpoint chính thức cùng siêu dữ liệu đầy đủ bàn giao cho TV4 tích hợp adapter.

> [!IMPORTANT]
> **Công bố giới hạn tái lập B3 (Reproduction Disclaimer):**
> `B3 reference reproduction UNRESOLVED; exploratory only; excluded from Test.`
> Kiểm định CPU ghi nhận 2 ảnh dự đoán khác báo cáo gốc, dù tổng đúng vẫn 446/600. Macro-F1 tham chiếu là 0.7410465262846234; CPU kiểm định là 0.7410527051783586. Khác biệt runtime/số thực là một giả thuyết, chưa chứng minh được nguyên nhân gốc; chẩn đoán CUDA của TV2 cũng chưa tái lập hoàn toàn tham chiếu. Chưa có đầy đủ log B3, runtime, training commit và dự đoán chưa làm tròn của lần chạy gốc. Không suy đoán thông tin bị thiếu. Giữ B3 ngoài Test và giữ lựa chọn B2 theo bằng chứng validation hiện có, không khẳng định ưu thế thống kê hoặc ưu thế trong mọi điều kiện.
>
> Bằng chứng lịch sử: nhánh TV2 commit `5fe9083`, `reports/tv2/w4_evidence/continuation_01/b3_validation_diagnostic/verification.json` và `b3_validation_cuda_diagnostic/verification.json`. Kiểm định CPU độc lập ngày 23/10 của TV1 có cùng sai lệch hai ảnh. Các kết quả tham chiếu dưới đây được giữ nguyên, không thay bằng điểm chạy lại.

---

## 2. Bảng So Sánh Đối Sánh Thực Nghiệm Chính Thức: B2 vs B3

Cả hai mô hình đều được huấn luyện trên cùng tập ảnh đóng băng `comparison_v1` (TV1 commit `7e9b194`), cùng kiến trúc ResNet-18, cùng SGD optimizer (lr=0.001, momentum=0.9), cùng cơ chế gom nhóm ảnh `ImageGroupedBatchSampler` và cùng tập Validation 600 ảnh:

| Chỉ số (Cấp Ảnh - Image Level) | B1 Baseline (TV2) | B2 Baseline (TV3) | B3 Trọng số lớp (TV3) | Chênh lệch (B3 vs B2) | Kết luận tiêu chí |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Macro F1-Score** | 56.24% | **74.55%** | 74.10% | <span style="color:red">**-0.45 điểm % (pp)**</span> | **B3 không đạt $\ge +0.5$ pp** |
| **Độ chính xác (Accuracy)** | 56.50% | **74.67%** | 74.33% | <span style="color:red">**-0.34 điểm % (pp)**</span> | Giảm nhẹ |
| **Macro Precision** | 57.49% | **74.84%** | 74.06% | <span style="color:red">**-0.78 điểm % (pp)**</span> | Giảm |
| **Macro Recall** | 56.50% | **74.67%** | 74.33% | <span style="color:red">**-0.34 điểm % (pp)**</span> | Giảm |
| **Số ảnh đoán sai (Errors)** | — | **152 / 600** | 154 / 600 | +2 ảnh sai | B2 ổn định hơn |
| **Epoch tốt nhất (Best Epoch)** | — | Epoch 21 (dừng ở 28) | Epoch 14 (dừng ở 21) | — | B3 dừng sớm hơn |
| **Thời gian huấn luyện** | — | 2,652s (~44.2 phút) | 1,660s (~27.7 phút) | — | Cùng môi trường GPU |

*(Ghi chú số liệu B1: Căn cứ kết quả chính thức từ `experiments/B1_run01/results/val_metrics.json` tại commit `5fe9083` của TV2: Accuracy = 56.50%, Macro F1 = 56.24%, Macro Precision = 57.49%, Macro Recall = 56.50%).*

---

## 3. So Sánh Hiệu Suất Từng Loài (Per-Class F1 Score)

| Class ID | Loài động vật (Species) | Trọng số $w_c$ (B3) | B2 F1-Score | B3 F1-Score | Biến thiên ($\Delta$) | Nhận xét thực nghiệm |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `annamite_striped_rabbit` (Thỏ vằn) | 1.1002 | 80.95% | **86.96%** | <span style="color:green">**+6.01 pp**</span> | Tăng mạnh do được ưu tiên trọng số |
| 0 | `large_antlered_muntjac` (Mang lớn) | 1.0726 | 54.17% | **57.75%** | <span style="color:green">**+3.58 pp**</span> | Cải thiện nhẹ |
| 5 | `masked_palm_civet` (Cầy vòi mốc) | 1.0909 | 73.42% | **73.68%** | +0.26 pp | Ổn định |
| 6 | `silver_pheasant` (Gà lôi trắng) | 0.8557 | **94.44%** | 93.88% | -0.56 pp | Ổn định ở mức rất cao |
| 3 | `chinese_serow` (Sơn dương) | 1.0697 | **78.38%** | 77.33% | -1.05 pp | Giảm nhẹ |
| 4 | `common_palm_civet` (Cầy vòi đốm) | 1.0940 | **78.62%** | 77.12% | -1.50 pp | Giảm nhẹ |
| 2 | `sambar` (Nai) | 0.9147 | **65.73%** | 62.67% | <span style="color:red">**-3.06 pp**</span> | **Suy giảm** khi bị hạ trọng số ($w < 1$) |
| 7 | `eurasian_wild_pig` (Lợn rừng) | 0.8022 | **70.67%** | 63.45% | <span style="color:red">**-7.22 pp**</span> | **Suy giảm mạnh** khi chịu trọng số thấp nhất |

---

## 4. Phân Tích Kỹ Thuật & Giả Thuyết Thực Nghiệm

1. **Phân bổ tập huấn luyện ở cấp ảnh vốn đã cân bằng:**
   - Tập huấn luyện gốc gồm đúng 350 ảnh cho mỗi loài (2.800 ảnh / 8 loài = 350 ảnh/loài). Do đó, ở cấp ảnh không tồn tại hiện tượng mất cân bằng số lượng mẫu thu thập.
   - Thử nghiệm B3 sử dụng tần suất nghịch đảo theo crop (inverse crop frequency) để thăm dò việc bù trừ số lượng bounding box, không phải để sửa mất cân bằng ở cấp ảnh. Sự chênh lệch số crop (từ 350 đến 480 crops) chủ yếu phản ánh tập tính bầy đàn (Lợn rừng và Gà lôi thường xuất hiện theo nhóm nhiều cá thể trong một ảnh).
2. **Hệ quả quan sát được từ việc phân bổ trọng số crop:**
   - Trong lần chạy B3, việc gán trọng số thấp cho Lợn rừng ($w_7 = 0.8022$) và Nai ($w_2 = 0.9147$) đi kèm với sự sụt giảm F1 ở hai loài này (Lợn rừng -7.22 pp, Nai -3.06 pp). Giả thuyết kỹ thuật hợp lý là gradient của hàm mất mát giảm sự chú ý vào các trường hợp khó của các loài này.
3. **Bản chất nhầm lẫn hình thái học giữa các loài gần nhau:**
   - Quan sát trên ma trận nhầm lẫn cho thấy lỗi tập trung lớn nhất ở cặp **Mang lớn $\leftrightarrow$ Nai** (25 ảnh nhầm hai chiều ở B2, 22 ảnh ở B3). Cả hai loài đều thuộc họ Hươu nai với hình thái tương đồng, đặc biệt khó phân biệt khi góc chụp che khuất gạc hoặc trong ảnh hồng ngoại ban đêm. Việc điều chỉnh trọng số lớp không thể giải quyết triệt để sự thiếu hụt đặc trưng hình thái này.

---

## 5. Quyết Định Chính Thức Của Nhóm TV3

Căn cứ vào tiêu chí hoàn thành đã cam kết trong đề cương:
> *"B3 là tùy chọn; quyết định chậm nhất ngày 3 bằng validation; lưu lý do, checkpoint và giới hạn. Nếu bỏ B3, dành giờ cho phân tích lỗi."*

Nhóm TV3 đưa ra quyết định chính thức:

### 🏆 **CHÍNH THỨC GIỮ MÔ HÌNH B2 LÀM BỘ PHÂN LOẠI CHÍNH THỨC CỦA DỰ ÁN**

- **Lý do lựa chọn B2:**
  - Macro F1 của B2 cao hơn B3 (**74.55% vs 74.10%**).
  - B2 có độ ổn định đồng đều hơn trên các lớp đông crop như Lợn rừng (+7.22 pp F1) và Nai (+3.06 pp F1).
  - B3 không đạt ngưỡng cải thiện tối thiểu $\ge +0.5$ pp trên tập validation.
- **Tình trạng của B3:** Đã bàn giao mã nguồn, báo cáo và checkpoint; nhật ký huấn luyện B3 gốc chưa có trong hồ sơ nhận được. `reports/tv3/train_log.jsonl` là log B2, không dùng thay cho B3. Giữ giới hạn này công khai; không train lại để thay thế lịch sử sau khi đã mở Test.

---

## 6. Hướng Dẫn Bàn Giao Checkpoint Cho TV4 (Tích Hợp Adapter)

Mô hình B2 chính thức đã sẵn sàng bàn giao cho Thành viên 4:
- **Đường dẫn file:** `outputs/b2_crop_classifier/b2_run01/best_model.pt`
- **Kích thước:** `89,548,866 bytes` (~85.4 MB)
- **SHA-256 Checksum:** `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`
- **Cách nạp an toàn (`weights_only=True`):**
  ```python
  import torch
  from src.models.b2_classifier import B2CropClassifier

  # Nạp an toàn không dùng unpickler không giới hạn
  ckpt = torch.load("outputs/b2_crop_classifier/b2_run01/best_model.pt", map_location="cpu", weights_only=True)
  class_map = ckpt["class_map"]
  id_to_label = ckpt["id_to_label"]
  num_classes = ckpt["num_classes"]
  preprocessing = ckpt["preprocessing"]

  # Khởi tạo kiến trúc ResNet-18
  model = B2CropClassifier(num_classes=num_classes,
      backbone_name=ckpt["backbone_name"], pretrained=False)
  model.load_state_dict(ckpt["model_state_dict"])
  model.eval()
  ```

---

## 7. Hướng Dẫn Tích Hợp Dự Đoán Cho TV4 (Phân Biệt Hai Chế Độ)

Để đảm bảo pipeline và demo hoạt động đúng yêu cầu kỹ thuật, TV4 cần phân biệt rõ hai chế độ suy luận:

### 7.1. Chế Độ 1: Benchmark Đánh Giá (So sánh chuẩn với B1)
- Áp dụng khi chạy trên tập dữ liệu benchmark đã biết trước mỗi ảnh chỉ có **một nhãn duy nhất**.
- Lấy trung bình vector xác suất (mean softmax probabilities) của tất cả crop trong cùng ảnh, sau đó chọn $\text{argmax}$ để xác định nhãn cấp ảnh:
  $$p_{\text{image}} = \frac{1}{K} \sum_{k=1}^K \text{softmax}(\text{logits}_k)$$
  $$\hat{y}_{\text{image}} = \arg\max(p_{\text{image}})$$

### 7.2. Chế Độ 2: Inference Thực Tế & Demo (Nhiều cá thể / Nhiều loài)
- **Tuyệt đối không gộp chung các bounding box của ảnh demo thành một nhãn duy nhất**, vì một bức ảnh camera trap thực tế có thể chứa đồng thời nhiều cá thể thuộc **nhiều loài khác nhau** (ví dụ: 1 Lợn rừng và 1 Nai trong cùng một khung hình).
- **Quy tắc xử lý:**
  1. Mỗi bounding box được cắt (crop) và đưa qua mô hình phân loại **hoàn toàn độc lập**.
  2. Giữ nguyên **Top-3 loài dự đoán kèm điểm số (confidence score)** riêng cho từng bounding box để hiển thị trên giao diện demo.
  3. Điểm số từ hàm Softmax của ResNet-18 là điểm số chưa qua hiệu chuẩn (uncalibrated score), phản ánh độ tự tin tương đối của mạng chứ không phải xác suất thống kê tuyệt đối.
  4. Heuristic tham khảo: Khi điểm số cao nhất của một box $< 0.50$ (đặc biệt khi dự đoán rơi vào cặp Mang lớn hoặc Nai), giao diện nên hiển thị chỉ báo độ không chắc chắn (Uncertainty Indicator) để người giám sát lưu ý. Đây là gợi ý heuristic hỗ trợ giao diện, không phải ngưỡng cắt bỏ chính thức.
