# Tiến độ TV4 — cải thiện giao diện demo

## W5 tiếp tục và bàn giao kiểm chéo — 02/11/2026

- Đã nhận ZIP TV3 và handoff/acceptance TV2; tiếp tục từ `fef2511`, giữ B2 mặc định.
- Hoàn thiện bản nháp lô10ảnh/CSV/JSON; thêm adapter DINO opt-in CPU FP32,
  kiểm source/architecture/checkpoint, crop batch≤8, giữ top3 theo detection.
- Sửa UI-A11Y-01 bằng aria-label của nút export mobile.
- Kết quả: 47/47TV4,380/380toàn suite PASS; native/adapter logits exact0,
  batch1/3/8+1, RGB/grayscale/portrait; browser real MD+DINO, saved review,
  revision409, lỗi model thật, queue/corrupt/drafts/CSV/stop-resume/3viewport PASS.
- Bằng chứng và giới hạn: `reports/tv4_w5/REPORT.md`, `reports/tv4_w5/evidence/`.
  Hướng dẫn: `docs/tv4_w5_demo.md`; script QA mới được version-control.
- Lỗi preview cũ khi mở mục ảnh lỗi đã sửa và chạy lại regression riêng;
  kết quả mở lại phục hồi đúng mode/model/ngưỡng của chính phiên đó.
- Source TV3 `src/training/dino_probe.py` giữ nguyên byte của training commit;
  model/ZIP/vendor checkout không đưa vào Git. B2 registry/checkpoint giữ riêng.
- Chờ TV2 review PR #8 và retest đúng commit; chưa merge hoặc thay production.
  GPU adapter/cài sạch/video/W6 chưa thực hiện; không chạy official Test.

Mục tạm dừng dưới đây là lịch sử ngày28/10, đã được tiếp tục sau khi nhận gói.

## Tạm dừng W5/W6 — 28/10/2026

Theo yêu cầu của TV4, dừng triển khai để chờ TV3 gửi gói model.

- HEAD tại thời điểm dừng: `fef2511`, branch `feat/demo`; PR #8 vẫn OPEN, chưa có review chuyên môn của TV2.
- TV4 xác nhận chưa nhận gói DINO vì TV3 chưa làm xong.
- Bản nháp local đã sửa `app/index.html`, `app/style.css`, `app/app.js`, `scripts/run_demo.py` và thêm `app/batch.js`.
- Bản nháp gồm hàng đợi tối đa 10 ảnh, xử lý tuần tự, dừng sau ảnh hiện tại, lưu trạng thái/bản nháp theo ảnh, xuất CSV và JSON lô từ phiên backend đã lưu.
- Mới chạy `node --check app/batch.js` trước chỉnh sửa nhỏ cuối; chưa chạy browser QA, kiểm thử CSV hoặc regression cho bản nháp W5. Chưa coi phần W5 là hoàn thành.
- Chưa commit/push thay đổi W5; giữ nguyên để tiếp tục. Không xóa phiên duyệt hoặc outputs.
- Khi tiếp tục: kiểm tra `git status`, đọc phân công `C:/Users/lequy/Downloads/TV4_W5_W6.md`, kiểm tra tiến trình/cổng trước khi khởi động demo; nhận weights/config/class map/preprocessing/pooling/hash và bằng chứng reload từ TV3, rồi kiểm thử bản nháp và tích hợp adapter nếu đủ điều kiện.

Các kết quả PASS và ảnh trong phần dưới thuộc bản UI ngày 26/10, không phải bản nháp W5.

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
