# Tài liệu Bàn giao Công việc Tuần 1 – TV2

## 1. Thông tin chung

*   **Tên đồ án:** CameraTrapML – Ứng dụng học máy hỗ trợ nhận dạng một số loài động vật ưu tiên bảo tồn tại Trường Sơn từ ảnh bẫy camera
*   **Thành viên thực hiện:** TV2 (Phụ trách Baseline & Evaluation)
*   **Gói công việc:** W1-02 (Xây khung đánh giá và môi trường học máy)
*   **Người nghiệm thu (Reviewer):** TV3
*   **Nhánh Git làm việc:** `feat/baseline`

---

## 2. Danh mục sản phẩm bàn giao (Deliverables Checklist)

Dưới đây là danh sách toàn bộ các tệp tin đã hoàn thành và bàn giao trong Tuần 1. Bạn có thể bấm vào đường dẫn để xem trực tiếp code:

1.  [`requirements.txt`](file:///d:/Năm 3/HK1_2026/Học máy và ứng dụng/Do_an/requirements.txt): Danh sách thư viện chuẩn của dự án (bao gồm PyTorch, Torchvision, Scikit-learn, PyYAML, Matplotlib, v.v.) và hướng dẫn cài đặt CUDA.
2.  [`check_environment.py`](file:///d:/Năm 3/HK1_2026/Học máy và ứng dụng/Do_an/check_environment.py): Script Python tự động kiểm tra phần cứng, phiên bản CUDA/PyTorch, tính khả dụng của GPU VRAM và chạy thử smoke-test nhân ma trận.
3.  [`gpu_env_report.txt`](file:///d:/Năm 3/HK1_2026/Học máy và ứng dụng/Do_an/gpu_env_report.txt): Báo cáo log sinh ra tự động ghi nhận trạng thái môi trường và GPU thực tế.
4.  [`src/evaluation/metrics.py`](file:///d:/Năm 3/HK1_2026/Học máy và ứng dụng/Do_an/src/evaluation/metrics.py): Module lõi tính toán các chỉ số thống nhất. Hỗ trợ đầu vào linh hoạt (PyTorch/NumPy) và xuất ra Macro-F1, Precision, Recall, Accuracy, cùng từ điển Confusion Matrix.
5.  `demo_confusion_matrix.png`: Hình ảnh minh họa ma trận nhầm lẫn dạng heatmap (được sinh ra tự động khi chạy self-test file `metrics.py`).
6.  [`docs/experiment_protocol.md`](file:///d:/Năm 3/HK1_2026/Học máy và ứng dụng/Do_an/docs/experiment_protocol.md): Bản đề cương thí nghiệm cốt lõi quy định chi tiết 4 mô hình (B0, B1, B2, B3), tiêu chí checkpoint, augmentation và chiến lược dữ liệu.

---

## 3. Tóm tắt các quy ước cốt lõi đã chốt

Để đảm bảo tính nhất quán cho toàn bộ vòng đời phát triển dự án, TV2 đã thiết lập và yêu cầu toàn nhóm tuân thủ các quy tắc sau:

*   **Metric chọn mô hình (Checkpoint Metric):** Bắt buộc sử dụng **`Macro-F1`** trên tập Validation để chọn best checkpoint và làm mốc Early Stopping. Không sử dụng `Accuracy` do tình trạng mất cân bằng lớp (Class Imbalance) rất nghiêm trọng.
*   **Quy tắc cô lập tập Test (Test Set Isolation):** Tuyệt đối không mở, không phân tích, không tune tham số trên tập Test. Tập Test **chỉ mở duy nhất ở Tuần 4** sau khi mô hình đã khóa. Mọi quyết định phát triển dựa trên Validation.
*   **Tính công bằng B1 vs B2 (Fair Comparison):** Baseline 1 (dùng toàn ảnh) và Baseline 2 (dùng vùng cắt của TV3) bắt buộc phải dùng chung một danh sách ảnh đủ điều kiện (1 loài duy nhất, bounding box hợp lệ) và phải dùng chung manifest phân chia dữ liệu theo trạm (Site-level split) của TV1.
*   **Tính tái lập (Reproducibility):** Mọi script huấn luyện bắt buộc gọi hàm cố định random seed (`set_seed(42)`).

---

## 4. Hướng dẫn nhanh cho TV3 kiểm tra (Quick Start / Verification)

Để TV3 nghiệm thu mã nguồn, vui lòng mở Terminal (tại thư mục gốc của dự án) và chạy lần lượt các lệnh sau:

**Bước 1: Cài đặt môi trường**
*(Lưu ý: Nếu máy tính có GPU hỗ trợ CUDA, hãy chạy lệnh cài PyTorch bằng URL chuyên biệt được ghi trong file `requirements.txt` trước).*
```bash
pip install -r requirements.txt
```

**Bước 2: Chạy kiểm tra nhận diện GPU**
```bash
python check_environment.py
```
*Kết quả kỳ vọng:* In ra console chi tiết hệ thống, GPU VRAM, báo cáo thời gian test nhân ma trận và sinh ra file `gpu_env_report.txt`.

**Bước 3: Chạy Self-test module đánh giá**
```bash
python -m src.evaluation.metrics
```
*Kết quả kỳ vọng:* Chạy luồng dữ liệu giả định 5 lớp, in ra console bảng `EVALUATION METRICS SUMMARY` (gồm Macro-F1, Precision, Recall...) và sinh ra file ảnh ma trận nhầm lẫn `demo_confusion_matrix.png` trong cùng thư mục.

---

## 5. Bảng nghiệm thu (Review Sign-off)

Vui lòng rà soát các hạng mục dưới đây và ký xác nhận khi hoàn tất:

| Tiêu chí | Trạng thái cam kết (TV2) | Phản hồi (TV3 - Reviewer) |
| :--- | :---: | :--- |
| 1. Code script kiểm tra môi trường chạy tốt, xuất log đầy đủ. | [x] Hoàn thành | [ ] Đạt / [ ] Cần sửa |
| 2. Module `metrics.py` xuất đủ 4 chỉ số (Macro-F1, Pre, Rec, Acc) và Confusion Matrix. | [x] Hoàn thành | [ ] Đạt / [ ] Cần sửa |
| 3. Xây dựng tài liệu Đề cương thí nghiệm chi tiết B0, B1, B2. | [x] Hoàn thành | [ ] Đạt / [ ] Cần sửa |
| 4. Chốt rõ quy tắc giữ kín tập Test và metric chọn Checkpoint. | [x] Hoàn thành | [ ] Đạt / [ ] Cần sửa |

**Xác nhận của Reviewer (TV3):**

*   **Chữ ký (Tên GitHub/Username):** ___________________________
*   **Ngày review:** ____/____/2026
*   **Nhận xét bổ sung (nếu có):**
    > ...
