# Tiến độ TV4 — cải thiện giao diện demo

**Cập nhật:** 26/10/2026

**Branch:** `feat/demo`

**Commit nền:** `60516f51fccbb85e6e266a022d94ea90d2239a11`

## File đã sửa

- `app/index.html`: tổ chức lại luồng thao tác thành ba bước; ưu tiên vùng ảnh, kết quả và duyệt.
- `app/style.css`: bổ sung hệ màu, typography, card, trạng thái, responsive và focus rõ ràng.
- `app/app.js`: thêm trạng thái trực quan, chọn vùng bằng box hoặc hàng kết quả và đồng bộ theo `detection_id`.
- `app/review.js`: đồng bộ vùng đang duyệt, phân biệt bản nháp/chưa lưu/đã lưu/lỗi.
- `docs/progress_tv4_ui.md`: ghi tiến độ và bằng chứng kiểm tra.

## Đã hoàn thành

- Làm mới bố cục desktop/mobile mà không đổi API, schema, class ID hoặc checkpoint.
- Giữ toàn bộ ID/selector đang được app và QA sử dụng.
- Giữ box bám theo raster ảnh; chọn box/hàng kết quả sẽ chọn đúng vùng duyệt bằng `detection_id`.
- Giữ nhãn giả lập rõ ràng và phân biệt các trạng thái đạt ngưỡng, cần xem, không phát hiện và lỗi.
- Đưa runtime và JSON truy vết vào vùng mở rộng để giảm nhiễu cho thao tác chính.
- Chuẩn bị và xác minh checkpoint B2 chính thức tại `outputs/tv4/models/b2_approved.pth` (không theo dõi bởi Git).
- Chuẩn bị và xác minh MegaDetector MDv5a.0.1 tại `outputs/tv4/models/` (không theo dõi bởi Git).

## Kiểm tra đã chạy

```text
node --check app/app.js                                      PASS
node --check app/review.js                                   PASS
git diff --check                                             PASS
.venv/Scripts/python.exe -X utf8 -m unittest discover \
  -s tests -p "test_tv4*.py" -v                              PASS (44/44)
.venv/Scripts/python.exe -X utf8 scripts/validate_results.py PASS (6/6 ví dụ)
.venv/Scripts/python.exe -X utf8 scripts/check_environment.py PASS
.venv/Scripts/python.exe -X utf8 -m unittest discover \
  -s tests -v                                                PASS (377/377)
```

Browser QA bằng Microsoft Edge:

- `1440×1100`: PASS, không tràn ngang.
- `390×844`: PASS, không tràn ngang.
- `320×740`: PASS, không tràn ngang.
- Box nằm trong đúng phần ảnh ở cả ba kích thước.
- Chọn hàng thứ hai đồng bộ đúng box và `review-box` theo `detection_id`.
- Trạng thái thay đổi chưa lưu hiển thị đúng.
- Luồng thật MegaDetector + B2: PASS; trạng thái `needs_review`, 1 detection, không có lỗi JavaScript.

## Việc còn lại

- PR [#8](https://github.com/huyryan220806/Camera-Trap-ML/pull/8) đã được tạo; đang chờ TV2 kiểm tra và nghiệm thu.
- Ảnh browser QA mới là bằng chứng local trong `outputs/`, không đưa vào Git theo `.gitignore`.
- Chức năng xử lý lô nhỏ/CSV là phần tiếp theo của W5, không nằm trong lượt làm đẹp UI này.

## Bước tiếp theo

1. TV2 kiểm tra lại hành vi UI/API và luồng lưu/nạp revision trên PR #8.
2. Sửa các nhận xét review nếu có mà không thay đổi hợp đồng dữ liệu.
3. Chỉ merge sau khi TV2 xác nhận; giữ branch `feat/demo` sau merge.
