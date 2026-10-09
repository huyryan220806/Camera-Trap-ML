# Kết quả TV4 tuần 2

Ngày 2026-10-09. Nhánh `codex/tv4-week2-demo-detector`.

## Đã hoàn tất

- Demo cục bộ nạp ảnh, ảnh mẫu train v2, vẽ box, bật/tắt box, xem và xuất JSON.
- Chế độ giả lập tách riêng với MegaDetector thật; không tự fallback khi model lỗi.
- Bộ lọc category animal, threshold, chuyển box normalized về pixel gốc, ghi lỗi
  đọc ảnh/detector và trường hợp không phát hiện.
- Phiên bản/hash model và cảnh báo overlap SWG được lưu; không bịa kết quả loài.
- Tiến độ và cache được lưu để không cần làm lại sau quota.

## Thử detector thật

Nguồn ảnh: dòng đầu của **train v2**, không dùng validation/test để thử giao diện.
Chi tiết ID, fingerprint và JSON thực tế ở `detector_smoke.json`.

| Thuộc tính | Giá trị |
|---|---|
| File checkpoint | md_v5a.0.1.pt |
| Metadata trong checkpoint | v5a.0.0, model_type yolov5 |
| MegaDetector Python | 10.0.25 |
| PyTorch / torchvision | 2.8.0 / 0.23.0 |
| Thiết bị | CPU, tối đa 4 thread PyTorch, chưa dùng CUDA |
| Kích thước suy luận / ngưỡng | 1280 / 0,20 |
| Ảnh gốc | image_00001.jpg, 3264 x 2448 |
| Kết quả | detected, 1 vùng animal, score 0,733 |
| Box XYWH pixel | [250,6752; 1162,8; 310,7328; 361,8144] |
| Thời gian smoke | 16.412,11 ms, bao gồm load model ở lần gọi đầu |
| Nhận dạng loài | Chưa có classifier; species = null |
| Dung lượng weights | 280.767.041 byte |
| SHA-256 weights | fe3e90e4b1955821ab7c1f88b446dc0c8cb25e109fdd1872916a55305294a5ef |

Đã chạy lại setup/smoke: in `Reusing verified MegaDetector weights` và
`Reusing matching successful smoke report`, không tải lại hay suy luận lại.

## Xác minh

- **91/91 tests đạt**: 79 test hiện có và 12 test TV4 mới.
- Đã kiểm tra lại sau gián đoạn quota lúc `2026-10-09T08:54:45+00:00`:
  91 đạt, 0 lỗi, 0 bỏ qua; xem `test_verification.json`. Server vẫn hoạt động,
  setup tiếp tục từ cache và checksum snapshot TV1 v2 không thay đổi.
- `pip check`: không có dependency lỗi. MegaDetector kéo setuptools từ 84.0.0
  xuống 81.0.0 trong `.venv`; thư viện chung được pin vẫn giữ nguyên.
- Playwright qua Edge headless: **đạt**, desktop 1440x1100, mobile 390x844.
- Đã thử preview, upload, hình học box, ẩn/hiện, mock/real, không phát hiện,
  lỗi detector, ảnh hỏng, JSON export, không tràn ngang trên mobile.
- 0 lỗi JavaScript; detector thật chạy thành công qua giao diện với 1 box.
- Đã xem screenshot desktop-real và mobile-mock để kiểm tra bố cục/box.
- Kết quả máy đọc: `browser_verification.json`. Screenshot nằm cục bộ tại
  `outputs/tv4/browser/`, không chứa trong Git.
- Manifest v1/v2 và schema phân loại v1 không bị sửa.

Cảnh báo `pkg_resources` của YOLOv5 xuất hiện trong log nhưng không làm inference
thất bại. Giữ phiên bản runtime đã kiểm tra; không tự nâng dependency trước buổi demo.

## Giới hạn

Đây là **smoke test tích hợp trên một ảnh**, không phải đo precision/recall/mAP,
không chứng minh chất lượng hay tốc độ tổng quát. MDv5a đã dùng SWG trong huấn luyện;
không trình bày thử nghiệm SWG như đánh giá độc lập detector/end-to-end.
Nguồn: [MegaDetector training data](https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md#can-you-share-the-training-data).

Chưa nhận dạng 8 loài, chưa huấn luyện, chưa triển khai dịch vụ công khai. Demo
chỉ CPU, một ảnh mỗi yêu cầu, giới hạn 16 MiB/24 MP. Ngưỡng 0,20 chưa được tối ưu
cho đồ án. Không phát hiện không đồng nghĩa ảnh trống; mọi kết quả cần kiểm tra.

## Tiếp tục và bàn giao

Hướng dẫn: `docs/handoff_tv4_w2.md`. Điểm tiếp nhận sau quota:
`docs/progress_tv4_w2.md`; checkpoint setup ở `outputs/tv4/setup/progress.json`.
Chạy lại server bằng `.venv/Scripts/python.exe scripts/run_demo.py --port 8765`.

Nhánh bàn giao: `codex/tv4-week2-demo-detector`, kế thừa TV1 tuần 2 `b9a92b9`.
Cần TV2 kiểm tra chéo trước khi nghiệm thu/merge; không gộp file chưa track
của thành viên khác vào commit.
