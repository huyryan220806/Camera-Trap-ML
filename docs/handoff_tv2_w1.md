# Bàn giao tuần 1 – TV2 Baseline & Evaluation

**Công việc:** W1-02, xây khung đánh giá và kiểm tra môi trường học máy.

**Người kiểm tra:** TV3.

**Nhánh tích hợp:** `feat/baseline` (tạo từ `main`).

Phần bàn giao tuần 1 gồm mã đánh giá, tài liệu và demo trên dữ liệu giả. Chưa huấn luyện mô hình B0–B3 và chưa đánh giá trên tập Test.

## Sản phẩm bàn giao

| Tệp | Nội dung |
|---|---|
| [requirements-tv2.txt](../requirements-tv2.txt) | Thư viện bổ sung cho TV2; cài kèm `requirements.txt` chung qua dòng `-r`. |
| [notebooks/TV2_baseline_evaluation.ipynb](../notebooks/TV2_baseline_evaluation.ipynb) | Kiểm tra thiết bị, đọc class map chung và chạy demo metric. |
| [src/evaluation/metrics.py](../src/evaluation/metrics.py) | Hàm tính metric, xác thực đầu vào và vẽ confusion matrix. |
| [tests/test_evaluation.py](../tests/test_evaluation.py) | Kiểm thử metric với đủ lớp, lớp vắng mặt và đầu vào sai. |
| [docs/experiment_protocol.md](experiment_protocol.md) | Thiết kế B0–B3, chọn checkpoint, chia dữ liệu và bảo vệ tập Test. |
| [reports/tv2/environment_report.txt](../reports/tv2/environment_report.txt) | Log Python, PyTorch và thiết bị của lần chạy notebook gần nhất. |
| [reports/tv2/demo_confusion_matrix.png](../reports/tv2/demo_confusion_matrix.png) | Ma trận nhầm lẫn từ dữ liệu giả, không phải điểm số mô hình thật. |

## Cách chạy lại để TV3 kiểm tra

Chạy các lệnh sau tại thư mục gốc dự án. Với máy mới, tạo môi trường Python 3.12 trước; nếu đã có `.venv`, dùng lại môi trường đó.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-tv2.txt
.venv/Scripts/python.exe -m jupyter nbconvert --to notebook --execute --inplace notebooks/TV2_baseline_evaluation.ipynb --ExecutePreprocessor.timeout=120
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe scripts/validate_gpu_schedule.py
git diff --check
```

`requirements-tv2.txt` cài `requirements.txt` chung trước rồi thêm PyTorch, scikit-learn, seaborn và Jupyter. Nếu cần CUDA, chọn bản PyTorch tương thích với máy theo hướng dẫn chính thức trước khi chạy; chỉ kết luận GPU hoạt động khi notebook thực hiện phép tính CUDA thành công.

Notebook tự tìm thư mục gốc, đọc [class map v1](../data/processed/v1/class_map.json) và ghi hai file trong `reports/tv2/`. Nếu thiếu class map, notebook phải báo lỗi; không dùng danh sách lớp demo thay thế. Lệnh `nbconvert --inplace` cập nhật output của notebook, vì vậy cần xem diff trước khi commit. Chạy `unittest` không thay thế việc chạy các assertion trong notebook.

## Quy ước đánh giá

- Chọn checkpoint và early stopping bằng **Macro-F1 trên Validation**; Accuracy là metric tham khảo.
- Macro-Precision, Macro-Recall, Macro-F1, báo cáo từng lớp và confusion matrix dùng đủ ID từ class map, kể cả lớp vắng mặt. Lớp vắng mặt nhận `0` theo `zero_division=0`; với map v1, confusion matrix có kích thước 8 × 8.
- B1 (toàn ảnh) và B2 (vùng cắt) dùng cùng danh sách ảnh đủ điều kiện và cùng manifest chia theo địa điểm của TV1.
- Cố định seed `42` cho các lần huấn luyện ở tuần sau và ghi cấu hình, commit, checkpoint cùng log của từng thí nghiệm.
- Không nạp, thống kê, trực quan hóa hoặc dùng Test để điều chỉnh mô hình. Chỉ đánh giá Test một lần sau khi khóa mô hình ở tuần 4.

## Checklist gửi lại TV3

- [ ] Notebook chạy hết trên kernel mới với class map chung; mọi assertion đạt.
- [ ] Log CPU/GPU được sinh từ lần chạy thực tế; hình vẫn ghi rõ dữ liệu giả.
- [ ] Unit test và các script kiểm tra chung đạt; `git diff --check` sạch.
- [ ] `README.md` chung liên kết tới tài liệu này và không mất phần TV1/TV4.
- [ ] Gửi commit, link nhánh/PR, các lệnh đã chạy và kết quả cho TV3.
