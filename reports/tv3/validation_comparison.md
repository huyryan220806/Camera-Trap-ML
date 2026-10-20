## Bảng so sánh Validation B1 (Toàn ảnh) vs B2 (Vùng cắt)

| Chỉ số | B1 (Toàn ảnh) | B2 Crop (Cấp Crop) | B2 Crop (Tổng hợp Cấp Ảnh) |
| :--- | :---: | :---: | :---: |
| **Độ chính xác (Accuracy)** | Chờ B1 | 72.94% | **74.67%** |
| **Macro F1-Score** | Chờ B1 | 72.54% | **74.55%** |
| **Macro Precision** | Chờ B1 | 72.71% | **74.84%** |
| **Macro Recall** | Chờ B1 | 73.02% | **74.67%** |
| **Số lượng mẫu** | 600 ảnh | 680 crops | **600 ảnh** |

> **Ghi chú đánh giá công bằng:** Chỉ số **B2 Crop (Tổng hợp Cấp Ảnh)** được tính bằng cách lấy trung bình vector xác suất của các crop trong cùng một ảnh rồi chọn argmax theo đúng khuyến nghị của TV1 tại `handoff_tv1_w3.md`.