# Bàn giao tuần 1 của TV4

**Công việc:** Khởi tạo dự án và giao diện dữ liệu. **Người kiểm tra:** TV2. **Trạng thái:** Chờ TV2 kiểm tra; chưa tự xác nhận nghiệm thu.

| Tiêu chí | Sản phẩm để kiểm tra |
|---|---|
| Cấu trúc repo rõ ràng | `docs/architecture.md`, các thư mục hiện có và ranh giới phần sẽ làm tuần 2 |
| Sơ đồ luồng | Hai sơ đồ Mermaid trong `docs/architecture.md` |
| Hướng dẫn môi trường | `docs/environment.md`, `requirements.txt`, `scripts/check_environment.py` |
| Quy ước Git | `CONTRIBUTING.md`, `.gitignore`, `.gitattributes` |
| JSON kết quả mẫu | Schema trong `contracts`, 6 ví dụ trong `examples/results`, validator |
| Thiếu phát hiện và ảnh lỗi | Bốn trạng thái và bảng mã lỗi trong `docs/result_contract.md` |
| Lịch GPU chung | `docs/gpu_schedule.md`, sổ đăng ký JSON, kiểm tra chồng lịch |

## Lệnh nghiệm thu

Sau khi cài môi trường trong tài liệu:

```powershell
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe scripts/validate_gpu_schedule.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
git diff --check
```

Các lệnh này không cần ảnh thật, metadata ZIP, SQLite hoặc GPU. TV2 có thể kiểm tra ngay từ repo vừa clone. Không chạy script tạo split đè lên manifest v1 đã có.

## Checklist dành cho TV2

- [ ] Chạy các lệnh trên và ghi kết quả vào PR.
- [ ] Đối chiếu nhãn trong ví dụ với class_map v1 của TV1.
- [ ] Xác nhận ngưỡng trong ví dụ chỉ là minh họa, phải chọn lại bằng validation khi có mô hình.
- [ ] Xác nhận `no_detection` khác ảnh trống và khác lỗi đọc ảnh.
- [ ] Xác nhận một box điểm thấp làm ảnh cần duyệt; một crop lỗi không được xuất như kết quả hoàn chỉnh.
- [ ] Xác nhận người dùng không nhìn thấy dữ liệu giả lập như kết quả mô hình thật.
- [ ] Cùng chủ máy điền thông tin GPU và thống nhất ngày bắt đầu trước khi duyệt lượt thực tế.
- [ ] Ghi nhận xét và quyết định nghiệm thu; không đánh dấu hoàn thành thay người kiểm tra.

## Giới hạn và bước nối tiếp

Gói này chưa triển khai detector, classifier, frontend, đọc ảnh thật, lưu kết quả theo batch hay chạy huấn luyện. Sơ đồ mô tả luồng sẽ tích hợp. Sáu JSON đều ghi mode mock và thời gian 0 để không gây hiểu nhầm là benchmark.

TV4 tuần 2 có thể xây giao diện bằng sáu fixture; TV2/TV3 có thể viết adapter theo hợp đồng. Tài nguyên GPU và thời điểm bắt đầu chưa có thông tin thực tế, nên sổ đăng ký để trống và khung tuần chỉ là đề xuất.
