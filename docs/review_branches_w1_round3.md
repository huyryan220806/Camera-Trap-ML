# Kiểm tra tích hợp TV2 và TV3 - 05/10/2026

## Kết luận

Hai nhánh đủ điều kiện kỹ thuật để gộp vào main sau một sửa nhỏ trong bước tích hợp.
Các vấn đề chặn được nêu ở lần kiểm tra 01/10 và 02/10 đã được xử lý trong phạm vi
tuần 1. Kết luận này không thay chữ ký nghiệm thu của thành viên được phân công.

| Thành viên | Nhánh | Commit đầu vào đã kiểm tra |
|---|---|---|
| TV2 | `feat/baseline` | `fb51b41574d7df8c812a2aa26b8a4664be791b7a` |
| TV3 | `feat/crop-classifier` | `22d20129eb492bac7e8ce6a3fe4008da598fe2f5` |

Nền main trước tích hợp: `232cc63`. Hai nhánh đều có lịch sử chung với main;
gộp thử với nhau không có conflict. Không force-push hoặc sửa lịch sử nhánh
thành viên. Giữ nguyên manifest v1 và các file chưa được Git theo dõi trên máy.

## Kết quả kiểm tra

- **42 unittest đạt:** 20 test TV1/TV4, 9 test đánh giá TV2, 13 test TV3 (gồm 2 test bổ sung khi tích hợp).
- **Notebook TV2 chạy hết** trong kernel mới dùng môi trường `.venv`: Python 3.12.10, PyTorch 2.8.0+cpu; phép nhân ma trận trên CPU đạt.
- Notebook đọc đúng class map chung 8 lớp; mọi assertion metric đạt; confusion matrix 8 x 8. Macro-F1 demo là 0.766667, chỉ là dữ liệu giả, không phải kết quả huấn luyện.
- Đã chạy lại quét toàn bộ metadata box bằng code TV3: **101.384 hợp lệ, 32.178 thiếu bbox, 275 lỗi hình học**, khớp report đã commit.
- Tái tạo chính xác danh sách **80 ID ảnh train khác nhau** với seed 42, khớp audit. Đối chiếu label, location, sequence, số box và checksum train manifest đều đạt.
- Cả 80 đường dẫn hình bbox trong audit tồn tại; 80 hình bbox và 8 hình lưới đọc được bằng Pillow. Đã xem trực quan một lưới train để kiểm tra hình/box hiển thị.
- Bản hiện tại không theo dõi ảnh raw trong Git. Audit và biên bản JSON đã được commit; không còn quy tắc bỏ qua mọi JSON.
- `validate_handoff.py`, kiểm tra môi trường, 6 JSON mẫu và lịch GPU đều đạt. Lịch GPU vẫn có 0 đăng ký thực tế.
- `pip check` không phát hiện dependency hỏng; `git diff --check` sạch.

## Sửa nhỏ trong bước tích hợp

### Bộ đếm TV3 khi mọi lượt tải thất bại

`process_species` dùng `Counter` nhưng chưa tạo khóa `saved` khi không lưu được
ảnh nào. Chuyển Counter sang dict làm mất trường đó; notebook truy cập
`counts['saved']` sẽ dừng với KeyError nếu mạng lỗi toàn bộ hoặc không có mẫu.

Đã thêm hai test (tải thất bại toàn bộ và lựa chọn rỗng), xác nhận cả hai thất bại
trước sửa. Khởi tạo đủ `selected`, `saved=0`, `failed=0` giải quyết lỗi; cả 42
test đạt sau sửa. Không thay thuật toán chọn mẫu, quy tắc box hoặc manifest.

### Hướng dẫn môi trường sau tích hợp

README và `docs/environment.md` được cập nhật để cài `requirements-tv2.txt`
trước khi chạy toàn bộ test, vì test TV2 cần scikit-learn và seaborn. File này
đã bao gồm requirements chung. Hướng dẫn clone chuyển sang main; tác vụ metadata
và JSON riêng vẫn có thể dùng bộ thư viện tối thiểu.

## Cách chạy lại

Từ thư mục gốc repo, với Python 3.12 và môi trường đã chuẩn bị:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-tv2.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe scripts/validate_gpu_schedule.py
.venv/Scripts/python.exe -m pip check
git diff --check
```

Notebook TV2 được chạy trong bản sao kiểm tra để không ghi đè notebook và report
đã nộp. Trên máy thực hiện review, kết quả nằm ở
`outputs/review-20261005/TV2_executed.ipynb`; report CPU và hình được sinh trong
`outputs/review-20261005/repo/reports/tv2/`. Thư mục outputs chỉ lưu cục bộ.

`validate_handoff.py` cần metadata ZIP và bản `data/processed/repro_check` đã
có sẵn, không phải kiểm tra áp dụng ngay trên một clone sạch chưa tải dữ liệu.

## Giới hạn còn lại

- Chưa kiểm chứng CUDA/GPU hoặc huấn luyện mô hình thật; toàn bộ notebook TV2 chỉ dùng dữ liệu giả.
- Không chạy lại toàn notebook TV3 để tải lại 80 ảnh. Đã kiểm tra code bằng dữ liệu tổng hợp, quét metadata thật và đối chiếu audit/hình đã nộp; chưa xác minh độc lập SHA-256 của toàn bộ ảnh nguồn đã tải.
- Chưa kiểm tra trùng nội dung toàn dataset hoặc kiểm tra có hệ thống chất lượng mọi box bằng mắt.
- Ảnh raw từng commit trên nhánh TV3 vẫn có thể còn trong lịch sử Git dù không còn ở phiên bản hiện tại. Không tự viết lại lịch sử để giảm dung lượng.
