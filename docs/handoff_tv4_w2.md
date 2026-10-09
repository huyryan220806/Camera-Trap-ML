# TV4 tuần 2: Demo sơ bộ và adapter detector

## Nghiệm thu

| Tiêu chí | Bàn giao |
|---|---|
| Nạp ảnh | Upload/kéo thả JPEG, MPO qua JPEG, PNG, WEBP; ảnh mẫu chỉ lấy train v2 |
| Vẽ box | Box theo pixel raster gốc; overlay tỷ lệ theo ảnh hiển thị, bật/tắt được |
| Kết quả mẫu | Chế độ Giả lập ghi rõ, có tình huống có box/không phát hiện/lỗi |
| Detector thật | Adapter MDv5a, CPU, kích thước suy luận 1280; đã chạy smoke thật |
| Phiên bản | Checkpoint `md_v5a.0.1.pt`, package `megadetector==10.0.25`, checksum trong JSON |
| Giới hạn SWG | Banner luôn hiển thị; JSON và báo cáo có cảnh báo training overlap |
| Sau quota | `docs/progress_tv4_w2.md` và checkpoint `outputs/tv4/setup/progress.json` |

Nhánh `codex/tv4-week2-demo-detector` bắt đầu từ bản TV1 tuần 2 `b9a92b9`.
Nhận bàn giao từ nhánh này; không sửa split hoặc hợp đồng phân loại v1 của nhóm.
Phụ thuộc phần TV1 tuần 2 chưa merge vào main; không bỏ commit nền TV1 khi tích hợp.

## Cài và chạy trên Windows

Từ gốc repo, dùng Python 3.12 và môi trường `.venv` hiện có:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/prepare_tv4_demo.py --smoke
.venv/Scripts/python.exe scripts/run_demo.py --port 8765
```

Mở http://127.0.0.1:8765. Nếu cổng đang dùng bởi một demo đang chạy thì mở lại
demo đó; nếu là chương trình khác, dùng `--port 8766`. Không dừng tiến trình khác
để chiếm cổng. Lệnh server chạy trong terminal cho tới khi nhấn Ctrl+C.

Giả lập không cần package/model MegaDetector, chỉ cần `requirements.txt` và lệnh
server. Detector thật cần `requirements-tv4.txt` và weights đã xác minh. Máy chưa
có ảnh pilot vẫn upload ảnh riêng được; muốn có mẫu train, chạy lệnh tiếp tục TV1.
Không tự tải 4.000 ảnh khi người dùng chỉ muốn thử upload.

Weights khoảng 280,77 MB tại `outputs/tv4/models/`, không đưa lên Git. Upload
ở trong bộ nhớ server, không lưu ra đĩa hoặc gửi lên dịch vụ ngoài. Chỉ khi chọn
Xuất JSON, trình duyệt tải file kết quả về máy. Demo chỉ bind loopback; không dùng
server này như dịch vụ production hoặc mở công khai ra Internet.

## Phiên bản và giới hạn khoa học

- Model phát hiện: **MDv5a**, file phát hành **`md_v5a.0.1.pt`**, package Python
  **10.0.25** (phiên bản cố định để tái lập, không khẳng định mới nhất).
- Metadata bên trong checkpoint vẫn ghi `v5a.0.0`; `.0.1` là tên bản file phát
  hành. Báo cáo giữ cả tên file và hash để không dựa riêng vào tên phiên bản.
- MD5 nguồn: `60f8e7ec1308554df258ed1f4040bc4f`.
- SHA-256 bản tải: `fe3e90e4b1955821ab7c1f88b446dc0c8cb25e109fdd1872916a55305294a5ef`.
- MDv5a kế thừa dữ liệu huấn luyện MDv5b có SWG. Chia theo location ở dự án
  không đảm bảo detector chưa thấy dữ liệu. Thử SWG chỉ để kiểm tra tích hợp,
  không báo cáo như độ chính xác độc lập của detector hoặc end-to-end.
- Detector không phân biệt 8 loài. Không lấy ground-truth label từ manifest để
  điền dự đoán; `classifier_id` và `species` luôn null trong bàn giao tuần này.
- Ngưỡng mặc định 0,20 chỉ phục vụ demo, chưa tối ưu bằng validation của nhóm.
  Không phát hiện không đồng nghĩa ảnh trống. Score chưa phải xác suất hiệu chỉnh.

Nguồn: [dữ liệu huấn luyện MegaDetector](https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md#can-you-share-the-training-data),
[model registry chính thức](https://github.com/agentmorris/MegaDetector/blob/main/megadetector/detection/run_detector.py),
[package cố định](https://pypi.org/project/megadetector/10.0.25/).

## Giao diện adapter

```python
from src.demo.detector import MegaDetectorAdapter, analyze

adapter = MegaDetectorAdapter()  # Tái sử dụng instance; load model ở lần gọi đầu.
result = analyze(image_bytes, "upload.jpg", mode="megadetector",
                 threshold=0.2, adapter=adapter)
```

Đầu ra theo `contracts/detector_demo.schema.json`, `schema_version=detector-demo-1.0`.
Không phải `inference_result.schema.json` v1, vì v1 yêu cầu top-3 loài mà hiện
chưa có classifier thật. Không nới lỏng v1 hoặc bịa top-3 để qua validator.

| Trường hợp | Đầu ra |
|---|---|
| Có box động vật đạt ngưỡng | `detected`, box pixel gốc, score, species null |
| Không box động vật đạt ngưỡng | `no_detection`, detections rỗng, needs_review true |
| Ảnh lỗi/vượt giới hạn | `error`, stage read, kích thước null |
| Thiếu model/sai checksum/lỗi inference | `error`, stage detect, không công bố box một phần |
| Giả lập | pipeline.mode mock, detector mock-geometry-v1; không tự đổi sang mode thật |

Chỉ category animal đi vào detections; person/vehicle đạt ngưỡng được đếm riêng
trong ignored_non_animals, không đưa vào classifier loài. Tọa độ normalized XYWH
của MD được đổi về pixel raster gốc; chỉ chặn sai số biên 1e-5, không sửa box lỗi
lớn. Không xoay EXIF, thống nhất với pipeline v2. Preview sau inference được tạo
từ chính raster đã giải mã để box không lệch do trình duyệt tự xoay ảnh.

TV2/TV3 tích hợp classifier ở bước sau: crop bằng box pixel gốc, chạy model loài,
rồi tạo result v1 đầy đủ và chạy validator v1. Kết quả detector-only không được
coi là kết quả nhận dạng loài hoàn chỉnh.

## Lưu tiến độ và chạy lại

`prepare_tv4_demo.py --smoke` khóa chống chạy trùng, xác minh weights trước khi
load, dùng `.part` khi tải và ghi checkpoint nguyên tử. Nếu bị ngắt khi tải, chỉ
tải lại file model còn dở; file hoàn tất không tải lại. Không resume từng byte.
Smoke thành công được tái sử dụng khi hash ảnh, weights, code adapter và phiên
bản package trùng. Nếu cần thử lại toàn bộ inference, đổi tên báo cáo smoke cũ
để giữ bằng chứng rồi chạy cùng lệnh.

Checkpoint `complete` ở đây chỉ nói bước setup/smoke hoàn tất, không có nghĩa
server sẽ tự chạy sau khi khởi động máy. Mở lại bằng `scripts/run_demo.py`.
Đọc `docs/progress_tv4_w2.md` trước khi tiếp nhận việc sau quota.

## Kiểm tra chéo cho TV2

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe scripts/prepare_tv4_demo.py --smoke
```

Kiểm tra UI tự động tùy chọn: `node scripts/qa_tv4.cjs`, cần package Playwright
và Chromium đã cài. Có thể đặt `PLAYWRIGHT_CHANNEL=msedge` để dùng Edge. Script
giả định server ở cổng 8765 và có ảnh train cục bộ; đặt `DEMO_URL` nếu đổi cổng.

- [ ] Nạp ảnh, thấy preview, chạy mock và phân biệt được với suy luận thật.
- [ ] Chạy MD, xem box, đối chiếu JSON/version/threshold/hash.
- [ ] Thử không phát hiện, file lỗi và lỗi detector; không có fallback giả lập ngầm.
- [ ] Đổi ảnh/chế độ/ngưỡng thì kết quả cũ được xóa, không gán box cũ cho ảnh mới.
- [ ] Xuất JSON và đọc cảnh báo SWG, classifier chưa có.
- [ ] Mở trên màn hình nhỏ; kiểm tra box không lệch và không tràn ngang.

Kết quả chạy của người triển khai ở `reports/tv4_w2/`; checklist trên dành cho TV2
kiểm tra chéo, chưa thay cho xác nhận của TV2. Lucide dùng bản vendored, có license
trong `app/vendor/`; không cần CDN khi chạy demo.
