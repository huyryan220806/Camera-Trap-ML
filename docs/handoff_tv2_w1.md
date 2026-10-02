# Bàn giao Tuần 1 - TV2 Baseline & Evaluation

TV2 cung cấp evaluation pipeline dùng class map và manifest v1 của TV1. Phần bàn giao này không huấn luyện model Tuần 2 và không đọc tập Test.

## Thành phần

- `notebooks/TV2_baseline_evaluation.ipynb`: kiểm tra PyTorch/CPU/GPU và demo evaluation bằng dữ liệu synthetic.
- `src/evaluation/metrics.py`: metric, input validation và confusion matrix dùng đầy đủ class map.
- `tests/test_evaluation.py`: test cho 8 class, missing class và input không hợp lệ.
- `docs/experiment_protocol.md`: giao thức thí nghiệm B0-B3 và quy tắc bảo vệ Test.
- `reports/tv2/environment_report.txt`: kết quả phần cứng của lần chạy notebook gần nhất.
- `reports/tv2/demo_confusion_matrix.png`: confusion matrix của demo synthetic, không phải kết quả model thật.

## Chạy kiểm tra

Từ thư mục gốc repository:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m jupyter nbconvert --to notebook --execute --inplace notebooks/TV2_baseline_evaluation.ipynb --ExecutePreprocessor.timeout=120
```

Notebook tự tìm root repository, đọc `data/processed/v1/class_map.json` và ghi report vào `reports/tv2/`. Kết luận CPU/GPU được tạo từ `torch.cuda.is_available()` trong chính lần chạy, không được viết sẵn.

## Quy ước đánh giá

- Dùng Validation Macro-F1 để chọn checkpoint và early stopping.
- Accuracy chỉ là metric tham khảo và được tính bằng `accuracy_score(y_true, y_pred)`.
- Macro Precision, Macro Recall, Macro-F1, classification report và confusion matrix dùng cùng danh sách class ID đầy đủ từ class map.
- B1 và B2 dùng chung danh sách ảnh đủ điều kiện và cùng manifest chia train/val/test theo location của TV1.
- Không nạp, thống kê, trực quan hóa hoặc tune trên Test; chỉ đánh giá một lần sau khi khóa model ở Tuần 4.
