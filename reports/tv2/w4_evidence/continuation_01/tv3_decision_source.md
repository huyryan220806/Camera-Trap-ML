# Báo Cáo Quyết Định Mô Hình Phân Loại Tuần 4 (TV3 - W4-03)
**Lựa chọn chính thức giữa B3 (Class-Weighted Crop Classifier) và B2 (Crop Classifier Baseline)**

---

## 1. Mục Tiêu & Tiêu Chí Nghiệm Thu Tuần 4

Theo đề cương và thỏa thuận kỹ thuật tuần 4:
- **Nhiệm vụ:** Thử nghiệm trọng số lớp (B3) và chốt bộ phân loại cuối cùng cho pipeline CameraTrapML.
- **Quy tắc nghiệm thu:**
  1. Mô hình B3 là **tùy chọn** (optional exploratory variant).
  2. Quyết định lựa chọn phải được thực hiện chậm nhất vào **Ngày 3 của Tuần 4**.
  3. **Quy tắc ngăn chặn rò rỉ dữ liệu (No Data Leakage):** Tuyệt đối **KHÔNG** mở hoặc dùng tập Test để chọn mô hình. Quyết định hoàn toàn dựa trên tập Validation (600 ảnh / 680 crops). Tập Test chỉ được TV2 mở một lần duy nhất sau khi bộ phân loại đã chốt và đóng băng.
  4. Nếu B3 không vượt trội hơn B2 trên tập validation, bảo lưu mô hình B2 và dành toàn bộ thời lượng còn lại cho **Phân tích lỗi (Error Analysis)** chuyên sâu.
  5. Đóng gói checkpoint chính thức cùng siêu dữ liệu đầy đủ bàn giao cho TV4 tích hợp adapter.

---

## 2. Bảng So Sánh Đối Sánh Thực Nghiệm Chính Thức: B2 vs B3

Cả hai mô hình đều được huấn luyện trên cùng tập ảnh đóng băng `comparison_v1` (TV1 commit `7e9b194`), cùng kiến trúc ResNet-18, cùng SGD optimizer (lr=0.001, momentum=0.9), cùng cơ chế gom nhóm ảnh `ImageGroupedBatchSampler` và cùng tập Validation 600 ảnh:

| Chỉ số (Cấp Ảnh - Image Level) | B1 Baseline (TV2) | B2 Baseline (TV3) | B3 Trọng số lớp (TV3) | Chênh lệch (B3 vs B2) | Kết luận tiêu chí |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Macro F1-Score** | 56.24% | **74.55%** | 74.10% | <span style="color:red">**-0.45%**</span> | **B3 không đạt $\ge +0.5\%$** |
| **Độ chính xác (Accuracy)** | 56.50% | **74.67%** | 74.33% | <span style="color:red">**-0.34%**</span> | Giảm nhẹ |
| **Macro Precision** | 56.88% | **74.84%** | 74.06% | <span style="color:red">**-0.78%**</span> | Giảm |
| **Macro Recall** | 56.50% | **74.67%** | 74.33% | <span style="color:red">**-0.34%**</span> | Giảm |
| **Số ảnh đoán sai (Errors)** | — | **152 / 600** | 154 / 600 | +2 ảnh sai | B2 ổn định hơn |
| **Epoch tốt nhất (Best Epoch)** | — | Epoch 21 (dừng ở 28) | Epoch 14 (dừng ở 21) | — | B3 dừng sớm hơn |
| **Thời gian huấn luyện** | — | 2,652s (~44.2 phút) | 1,660s (~27.7 phút) | — | Cùng môi trường GPU |

---

## 3. So Sánh Hiệu Suất Từng Loài (Per-Class F1 Score)

| Class ID | Loài động vật (Species) | Trọng số $w_c$ (B3) | B2 F1-Score | B3 F1-Score | Biến thiên ($\Delta$) | Nhận xét thực nghiệm |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | `annamite_striped_rabbit` (Thỏ vằn) | 1.1002 | 80.95% | **86.96%** | <span style="color:green">**+6.01%**</span> | Tăng mạnh do được ưu tiên trọng số |
| 0 | `large_antlered_muntjac` (Mang lớn) | 1.0726 | 54.17% | **57.75%** | <span style="color:green">**+3.58%**</span> | Cải thiện nhẹ độ tự tin |
| 5 | `masked_palm_civet` (Cầy vòi mốc) | 1.0909 | 73.42% | **73.68%** | +0.26% | Ổn định |
| 6 | `silver_pheasant` (Gà lôi trắng) | 0.8557 | **94.44%** | 93.88% | -0.56% | Ổn định ở mức rất cao |
| 3 | `chinese_serow` (Sơn dương) | 1.0697 | **78.38%** | 77.33% | -1.05% | Giảm nhẹ |
| 4 | `common_palm_civet` (Cầy vòi đốm) | 1.0940 | **78.62%** | 77.12% | -1.50% | Giảm nhẹ |
| 2 | `sambar` (Nai) | 0.9147 | **65.73%** | 62.67% | <span style="color:red">**-3.06%**</span> | **Suy giảm** do bị hạ trọng số ($w < 1$) |
| 7 | `eurasian_wild_pig` (Lợn rừng) | 0.8022 | **70.67%** | 63.45% | <span style="color:red">**-7.22%**</span> | **Suy giảm nặng** do bị phạt trọng số thấp nhất |

---

## 4. Phân Tích Nguyên Nhân Kỹ Thuật (Vì Sao B3 Không Vượt Được B2?)

1. **Bản chất tập dữ liệu gốc đã cân bằng ở cấp ảnh:**
   - Tập huấn luyện gốc gồm đúng 350 ảnh cho mỗi loài (2.800 ảnh / 8 loài = 350 ảnh/loài).
   - Sự chênh lệch số crop (từ 350 đến 480 crops) không phải là mất cân bằng mẫu (class imbalance) do thiên vị thu thập, mà phản ánh **đặc tính bầy đàn tự nhiên** (Lợn rừng và Gà lôi thường đi theo đàn, xuất hiện nhiều con trong 1 ảnh).
2. **Hệ quả tiêu cực của việc hạ trọng số lớp đa số crop:**
   - Lợn rừng có 480 crops nên công thức inverse frequency gán trọng số thấp nhất ($w_7 = 0.8022$).
   - Điều này khiến mạng nơ-ron ít chú ý đến các đặc trưng của Lợn rừng hơn, làm số ảnh Lợn rừng bị phân loại sai tăng từ **22 ảnh (B2) lên 29 ảnh (B3)**, F1 giảm từ **70.67% xuống 63.45%**.
   - Tương tự, Nai (`sambar`) bị hạ trọng số ($w_2 = 0.9147$), kéo F1 giảm từ **65.73% xuống 62.67%**.
3. **Bản chất lỗi là do tương đồng thị giác, không phải mất cân bằng tần suất:**
   - Cả B2 và B3 đều gặp khó khăn lớn nhất ở cặp **Mang lớn $\leftrightarrow$ Nai** (25 ảnh nhầm lẫn ở B2, 22 ảnh ở B3) do cùng họ Hươu nai, màu lông nâu đỏ tương tự trên ảnh hồng ngoại ban đêm. Việc điều chỉnh trọng số lớp không thể giải quyết được sự thiếu hụt chi tiết hình thái trong ảnh ban đêm.

---

## 5. Quyết Định Chính Thức Của Nhóm TV3

Căn cứ vào tiêu chí hoàn thành đã cam kết trong đề cương:
> *"B3 là tùy chọn; quyết định chậm nhất ngày 3 bằng validation; lưu lý do, checkpoint và giới hạn. Nếu bỏ B3, dành giờ cho phân tích lỗi."*

Nhóm TV3 đưa ra quyết định chính thức:

### 🏆 **CHÍNH THỨC GIỮ MÔ HÌNH B2 LÀM BỘ PHÂN LOẠI CHÍNH THỨC CỦA DỰ ÁN**

- **Lý do lựa chọn B2:**
  - Macro F1 của B2 cao hơn B3 (**74.55% vs 74.10%**).
  - B2 có độ ổn định đồng đều hơn trên các lớp đông crop như Lợn rừng (+7.22% F1) và Nai (+3.06% F1).
  - Không vi phạm tiêu chí suy giảm recall của các lớp khác.
- **Tình trạng của B3:** Lưu trữ toàn bộ mã nguồn huấn luyện (`scripts/train_b3.py`), nhật ký (`train_log.jsonl`) và checkpoint B3 (`outputs/b3_class_weighted/b3_run01/best_model.pt`) trong dự án để làm bằng chứng thực nghiệm đầy đủ cho báo cáo đồ án.

---

## 6. Hướng Dẫn Bàn Giao Checkpoint Cho TV4 (Tích Hợp Adapter)

Mô hình B2 chính thức đã sẵn sàng bàn giao cho Thành viên 4:
- **Đường dẫn file:** `outputs/b2_crop_classifier/b2_run01/best_model.pt`
- **Kích thước:** `89,548,866 bytes` (~85.4 MB)
- **SHA-256 Checksum:** `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`
- **Tập siêu dữ liệu tích hợp sẵn trong checkpoint:**
  ```python
  import torch
  ckpt = torch.load("outputs/b2_crop_classifier/b2_run01/best_model.pt", map_location="cpu", weights_only=False)
  print("Class mapping:", ckpt["class_map"])
  print("Preprocessing:", ckpt["preprocessing"])
  print("Validation Macro F1:", ckpt["val_metrics"]["image_level"]["macro_f1"])  # 0.7455
  ```

---

## 7. Khuyến Nghị Cho TV4 Dựa Trên Báo Cáo Phân Tích Lỗi

Dựa trên kết quả phân tích tại `reports/tv3/error_analysis_b2.md`:
1. **Gắn nhãn cảnh báo độ tin cậy thấp:** Khi mô hình dự đoán ra Mang lớn (`large_antlered_muntjac`) hoặc Nai (`sambar`) với xác suất $\text{confidence} < 0.50$, giao diện người dùng (TV4) nên hiển thị cảnh báo để kiểm tra thủ công.
2. **Aggregation đa crop:** TV4 cần đảm bảo khi 1 ảnh có nhiều bounding box (nhiều crop), adapter phải tính trung bình vector xác suất (softmax) của tất cả crop rồi mới argmax để giữ độ chính xác tối ưu 74.67%.
