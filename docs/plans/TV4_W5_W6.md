# TV4 — Kế hoạch tuần 5–6: hoàn thiện UI, tích hợp model và đóng gói demo

**Cập nhật:** 28/10/2026. **Branch:** `feat/demo`. **Người kiểm tra:** TV2;
TV3 phối hợp adapter/checkpoint, TV1 đối chiếu dữ liệu và điều phối.

Lịch đề xuất: tuần 5 **28/10–03/11**, tuần 6 **04/11–10/11** (giờ Việt Nam),
điều chỉnh cùng nhóm nếu lịch lớp khác; đây không phải hạn nộp đã xác nhận.

## 1. Tiếp tục từ bản nào?

- Code UI đã push: **`0179d97`**; đầu `origin/feat/demo` lúc kiểm tra là
  **`fef2511`**, có progress ghi [PR #8](https://github.com/huyryan220806/Camera-Trap-ML/pull/8).
  Theo progress, layout, responsive, chọn vùng và trạng thái bản duyệt đã sửa.
- Việc đầu tiên là phối hợp TV2 review bản này và sửa phản hồi. Không phải làm
  lại giao diện từ đầu. Các thông tin PASS trong progress là bằng chứng do tác
  giả ghi; TV2 cần kiểm tra chéo đúng commit trước khi merge.
- Main hiện có nền tuần 1–4. Đọc [bàn giao đầy đủ](../handoff_tv4_return_ui.md)
  và progress UI trên branch của mình để biết ID/selector, API, schema và QA.
- Model hoạt động hiện tại: MegaDetector + B2. DINOv3 mới là kế hoạch của TV3,
  chưa có checkpoint của dự án đã nghiệm thu. B3 không nằm trong demo.

## 2. Thứ tự ưu tiên tuần 5

| Ưu tiên | Việc | Điều kiện bàn giao |
| --- | --- | --- |
| 1 | Hoàn tất review giao diện mới | Dễ xem ảnh/box, dễ duyệt, chạy desktop/mobile; TV2 xác nhận các luồng cũ |
| 2 | Giữ demo B2 ổn định và chuẩn bị adapter model mới | Chỉ bật ứng viên khi TV3 có gói weights/config/hash/reload đạt kiểm định |
| 3 | Xử lý lô nhỏ và CSV | Ảnh lỗi không làm mất cả lô; trạng thái và nhãn duyệt được xuất đúng |
| 4 | Đo lại tốc độ, cập nhật hướng dẫn/video | Thiết bị, batch, cold/warm và số mẫu rõ ràng |

Nếu thiếu thời gian, thu hẹp lô/CSV sau trao đổi trong nhóm; vẫn bàn giao UI,
duyệt/lưu/JSON ổn định và video. Việc hoàn thiện UI không phụ thuộc TV3 có đạt
accuracy 88% hay không.

## 3. Lịch tuần 5

| Mốc | Công việc TV4 | Bằng chứng |
| --- | --- | --- |
| Ngày 1–2 | Nhận review TV2 cho PR #8; chỉnh lỗi, kiểm tra responsive/focus | Screenshot và biên bản từng lỗi đã sửa |
| Ngày 3 | Chốt giao diện adapter với TV3; thiết kế hàng đợi lô/CSV nhỏ | Sơ đồ dữ liệu, mẫu output; phần chưa có checkpoint ghi rõ |
| Ngày 4–5 | Triển khai lô/CSV nếu trong phạm vi; giữ B2 làm model đang chạy | Kiểm thử hàng đợi, ảnh lỗi/no detection, xuất nhãn duyệt |
| Ngày 6–7 | Nhận ứng viên đủ điều kiện, tích hợp và đo tốc độ; demo nội bộ | `reports/tv4_w5/REPORT.md`, log inference, hướng dẫn |

Tên file W5/W6 trong plan là **đầu ra cần tạo**, không phải đã hoàn thành.

### Giữ đúng chức năng khi đổi UI

- Vùng ảnh chính đủ lớn; box theo đúng raster, kể cả ảnh dọc và thay đổi kích
  thước. Box/hàng kết quả/vùng duyệt nối bằng `detection_id`, không dựa vào vị trí
  mảng khi sắp xếp hoặc lọc.
- Phân biệt đang chạy, kết quả, cần kiểm tra, không có phát hiện và ảnh/model
  lỗi. Không có box không chứng minh ảnh trống; điểm thấp không kết luận loài lạ.
- Nhiều box có top 3 riêng; điểm số chưa hiệu chỉnh. Không dùng chữ “chính xác
  90%” hoặc “xác suất đúng” để diễn giải điểm softmax.
- Bản dự đoán gốc bất biến; bản nháp/bản đã lưu rõ ràng; xử lý revision 409;
  export dùng bản đã lưu. Ghi được detector bỏ sót và lý do.
- Nút/nhãn có thể dùng bàn phím; 1440, 390, 320 px không tràn ngang. Màu không
  phải tín hiệu duy nhất cho lỗi hoặc trạng thái.

### Tích hợp DINO khi nhận đủ gói TV3

1. Nhận weights thật + SHA/kích thước, config backbone/head, class map 8 lớp,
   preprocessing, feature pooling và mẫu nạp đã kiểm định.
2. Tạo adapter đúng kiến trúc; mã hiện tại nạp ResNet18, không tự tương thích
   với DINO. Không chỉ thêm tên vào dropdown hoặc đổi đường dẫn `.pt`.
3. Cache theo danh tính checkpoint và config; hỗ trợ nhiều crop và top 3, batch
   có giới hạn theo thiết bị. Nếu model lỗi, báo lỗi và cho người dùng chọn B2;
   không im lặng dùng B2 nhưng hiển thị tên DINO.
4. Metadata/log ghi model/version/hash và ngưỡng đã dùng. Ngưỡng duyệt hiện tại
   không tự được coi là tối ưu cho model mới; phối hợp TV2 hiệu chỉnh bằng
   validation nếu có, không dùng Test cũ.
5. Giữ cảnh báo MegaDetector đã dùng SWG khi huấn luyện. Metric GT-box của
   classifier khác hiệu năng toàn bộ luồng detector + classifier.

### Phạm vi lô nhỏ và CSV

Đề xuất bắt đầu tối đa **10 ảnh/lô**, xử lý tuần tự để hạn chế RAM; giới hạn
thực tế phải hiện trên UI và ghi trong báo cáo. Không hứa xử lý lô lớn khi chưa đo.

- Một ảnh có trạng thái/ID riêng, lỗi không dừng toàn bộ lô; người dùng biết
  ảnh nào xong, lỗi hoặc đang chờ. Đổi ảnh không làm mất liên kết với bản duyệt.
- CSV: một dòng/box; ảnh không có box hoặc ảnh lỗi vẫn có một dòng trạng thái.
  Cột tối thiểu: image/request ID, tên file, detection ID, tọa độ box, model/hash,
  top 3 và điểm, trạng thái, nhãn duyệt, outcome, người duyệt, revision, thời điểm.
- Giữ riêng nhãn dự đoán gốc và nhãn duyệt; nhãn chưa xác định không bị biến
  thành lớp mới. Hỗ trợ UTF-8, dấu phẩy/xuống dòng/ngoặc kép trong ghi chú và
  xử lý chuỗi có thể bị Excel diễn giải thành công thức.
- JSON hiện tại vẫn là bản truy vết đầy đủ. Chốt thay đổi API/schema với TV2
  trước khi phá tương thích; không coi CSV là thay thế log gốc.

## 4. Tuần 6 — nghiệm thu sản phẩm và gói nộp

| Mốc | Công việc | Điều kiện hoàn thành |
| --- | --- | --- |
| Ngày 1–2 | Chốt model demo theo kiểm định, đo tốc độ và review TV2 | B2 hoặc ứng viên đủ điều kiện; log có cả lỗi/no detection/detector miss |
| Ngày 3 | Cài sạch, hướng dẫn tải weights, thử không cần Internet sau chuẩn bị | Người khác mở web được bằng README |
| Ngày 4 | Tập bảo vệ lần 1 và quay bản demo nháp | Ảnh train minh họa, không dùng Test để khoe chọn mẫu |
| Ngày 5 | Tập lần 2, video dự phòng và sửa lỗi cuối | Số liệu hiển thị khớp báo cáo, không ghi “đã đạt 88%” nếu chưa có |
| Ngày 6–7 | Đóng gói mã/config/manifest/tài liệu và link weights ngoài Git | `reports/tv4_w6/REPORT.md`, danh mục gói nộp, SHA và video |

Log tốc độ ghi CPU/GPU, RAM/VRAM, OS/runtime, threads, batch ảnh và batch crop,
resolution detector, số mẫu, cold/warm, mean/p50/p95 khi đủ lượt. Phân biệt
thời gian model với tổng thời gian upload/decode/UI; số 5,55 giây/ảnh của B2
trước đây không được sao chép sang DINO nếu chưa đo.

## 5. Lệnh hiện có và cách tiếp tục

```powershell
git fetch origin
git switch feat/demo
git merge --ff-only origin/feat/demo
git merge origin/main
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765
```

Mở <http://127.0.0.1:8765>. Không mở HTML bằng `file://`. Nếu thiếu weights,
làm theo bàn giao TV4; không tải/huấn luyện model khác để lấp chỗ trống.

```powershell
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p "test_tv4*.py" -v
.venv/Scripts/python.exe -X utf8 scripts/validate_results.py
node --check app/app.js
node --check app/review.js
node scripts/qa_tv4_w4.cjs
```

Browser QA cần Node/Playwright/Edge, server, B2/MegaDetector và ảnh train đã
cài; xem bàn giao để chuẩn bị. QA có thể tạo phiên duyệt mẫu và ghi đè ảnh
chụp trong thư mục output QA: giữ bằng chứng từng lượt riêng nếu cần truy vết.
Trước PR chạy thêm kiểm tra môi trường, unittest toàn bộ và `git diff --check`.

Tiếp tục cập nhật `docs/progress_tv4_ui.md` trên branch TV4; thêm mục W5/W6
với commit, việc xong/dở, checkpoint/hash, log và lệnh tiếp theo. Khi ngắt,
kiểm tra server/job còn chạy trước khi bật bản thứ hai. Giữ nguyên phiên duyệt,
revision và log; không xóa `outputs/tv4/w4/sessions/` để làm sạch demo.
Gửi TV2 kiểm tra, merge sau nghiệm thu, giữ branch `feat/demo`.
