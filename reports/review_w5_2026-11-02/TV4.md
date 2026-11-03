# TV4 tuần 5 — kết quả kiểm tra ngày 02/11/2026

**Đạt kiểm tra kỹ thuật UI, DINO adapter, lô nhỏ và CSV.** Commit `8d4a255881c445b5528e69cd9d07a503c02ec11d`, nhánh `feat/demo`. Không phát hiện lỗi chức năng đang chặn tích hợp trong phạm vi đã chạy. Đây là kiểm tra của TV1; chưa gửi approval thay TV2 lên PR #8.

## Đã xác minh tại máy TV1

- 47/47 tests TV4 PASS; bản kết hợp cả nhóm 440/440 PASS.
- Nạp checkpoint DINO thật và checkout kiến trúc đúng pin. Logits native/adapter bằng tuyệt đối trên crop RGB, ảnh xám, ảnh nhỏ, batch 1/3/8+1; ảnh dọc có hai box trả top3 riêng. Thiếu/sai checkpoint hoặc sai checkout bị từ chối cả sau warm cache; không fallback ngầm.
- Edge chạy MegaDetector + DINO thật trên train sample; provenance giữ tên và SHA DINO. Chạy B2 thật riêng cũng PASS, B2 vẫn là lựa chọn mặc định.
- Sửa nhãn, lưu/reload/export JSON đúng revision, original bất biến; revision cũ trả 409. Duyệt nhiều box và nháp từng ảnh khôi phục đúng khi chuyển ảnh/mode.
- Lô good/corrupt/good tiếp tục đủ 3 ảnh, tên trùng vẫn khác ID; 11 ảnh bị từ chối mà giữ kết quả cũ; dừng sau ảnh hiện tại và resume đúng.
- CSV UTF-8/quoting/chuỗi công thức PASS, không xuất nháp chưa lưu. Parser độc lập đọc 5 dòng (2 box + 1 lỗi + 2 box); no detection vẫn có 1 dòng, giữ outcome `detector_miss` đã lưu. JSON gốc vẫn lưu riêng dự đoán và quyết định người duyệt.
- 1440/390/320 px không tràn ngang, box trong ảnh, không lỗi JS. **UI-A11Y-01 đã sửa và retest PASS**: nút export có accessible name khi ẩn chữ trên mobile.
- JPEG hỏng dùng decoder thật; nhiều box/no detection/detector error dùng fixture có nhãn giả lập. Native checkpoint failure được kiểm riêng; không gọi fixture là độ chính xác detector thực tế.

## Phạm vi và việc tuần 6

Giữ DINO là ứng viên opt-in và B2 mặc định đến khi nhóm chốt. Không coi accuracy 84,5% GT-box validation là độ chính xác end-to-end của web. Ngưỡng review0,70 là cấu hình demo, không phải ngưỡng đã hiệu chỉnh cho DINO.

TV4 đã ghi rõ CPU, batch ảnh/crop, resolution và cold/warm. Các số đo vẫn là smoke ít mẫu, thread cold/warm chưa đồng nhất; không dùng làm cam kết tốc độ. Nếu trình bày benchmark ở tuần 6, chuẩn hóa cấu hình trước load và đo nhiều ảnh/lượt hơn.

Trước gói nộp: thử cài sạch, cung cấp checkpoint/checkout đúng pin, video dự phòng. Hiện cần Git chứa training commit; queue/bản nháp nằm trong RAM của tab và mất khi reload, còn phiên đã lưu vẫn ở server. Đây là giới hạn đã công bố; không gọi là queue bền vững hoặc demo GPU.

Cập nhật progress và liên kết đến kiểm tra này; TV2 có thể dùng làm evidence kiểm chéo, nhưng không ghi đã có APPROVED GitHub khi chưa có. PR #8 hiện OPEN/mergeable ở đúng head đã kiểm.

[Browser](evidence/browser_verification.json) · [batch regression](evidence/batch_verification.json) · [B2 và CSV no-box](evidence/extra_ui_verification.json) · [native/adapter](evidence/native_adapter_equivalence.json) · [tests](evidence/tv4_tests.txt) · [biên bản chung](REPORT.md).
