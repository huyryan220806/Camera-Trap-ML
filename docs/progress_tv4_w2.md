# Progress TV4 tuần 2

Cập nhật: 2026-10-09. Nhánh: `codex/tv4-week2-demo-detector`.
Nhánh bắt đầu từ commit bàn giao TV1 tuần 2 `b9a92b9`; không sửa snapshot v2.

## Yêu cầu

Thực hiện thay TV4: demo sơ bộ và adapter detector. Nạp ảnh, vẽ box, hiển thị
kết quả mẫu; ghi phiên bản MegaDetector và việc SWG có trong dữ liệu huấn luyện.
Lưu tiến độ để tiếp tục sau quota. Người dùng đã yêu cầu push và bàn giao TV4;
chưa yêu cầu merge vào main.

## Trạng thái: HOÀN THÀNH TRIỂN KHAI

- Đã đọc hợp đồng suy luận v1: bắt buộc top-3 loài, không phù hợp detector-only.
- Quyết định: giữ nguyên v1; detector-only dùng cấu trúc riêng, không bịa top-3.
- Demo local: Python HTTP server + HTML/CSS/JS, không đưa ảnh lên dịch vụ ngoài.
- Đã cài `megadetector==10.0.25`, `torchvision==0.23.0` với torch 2.8.0 CPU;
  không có CUDA. Đã tải MDv5a.0.1, checksum MD5 chính thức khớp.
- Chỉ dùng mẫu từ train v2 để thử; không xem/tune bằng test.
- Đã dựng `app/`, `src/demo/detector.py`, `scripts/run_demo.py`, schema detector
  riêng và 12 test TV4 đều đạt. Upload/sample, mock/real, box, JSON export đã có.
- Smoke thật ĐẠT: MDv5a.0.1 trên ảnh train 3264x2448, 1 box động vật, score 0.733,
  CPU 16.41 giây gồm tải model. Báo cáo ở `reports/tv4_w2/detector_smoke.json`.
- QA UI ĐẠT bằng Playwright + Edge headless: desktop 1440x1100 và mobile 390x844,
  mock/real, upload, error/empty, box, xuất JSON, không tràn ngang. Đã xem screenshot.
- Toàn bộ 91/91 test đạt; pip check đạt. Chạy lại setup/smoke đã bỏ qua tải/infer
  khi fingerprint trùng. Source v1/v2 và inference schema v1 giữ nguyên.
- Handoff: `docs/handoff_tv4_w2.md`; báo cáo: `reports/tv4_w2/REPORT.md`.
- Nhánh bàn giao: `codex/tv4-week2-demo-detector`, phụ thuộc bản TV1 tuần 2
  `b9a92b9`. Còn kiểm tra chéo của TV2; không tự merge `main`.
- Đã push code TV4: `c69283a659c27498d1e9ec43781777af4dc37282`, xác minh bằng
  `git ls-remote`. Bàn giao chung và review: `docs/handoff_team_w2.md`.

## Xác nhận sau lần gián đoạn quota

Tiếp nhận lại ngày 2026-10-09, kiểm tra lúc `2026-10-09T08:54:45+00:00`:

- Demo ở cổng 8765 vẫn trả API bình thường; không mở thêm server hoặc tải model lại.
- Chạy lại toàn bộ **91 test đạt**, 0 lỗi, 0 bỏ qua. Bằng chứng máy đọc:
  `reports/tv4_w2/test_verification.json`.
- Setup/smoke tái sử dụng weights đã xác minh và báo cáo thành công có fingerprint khớp.
- Checksum toàn bộ snapshot TV1 v2 giữ nguyên. Không còn bước triển khai TV4 đang dở.

## Các bước tiếp theo của nhóm

1. TV2 kiểm tra chéo theo checklist handoff. Không cần dựng lại demo hoặc tải model lại.
2. Code đã push; gửi `docs/handoff_team_w2.md` cho nhóm. Không merge main khi
   TV2/TV3 còn các mục sửa trong báo cáo review ngày 09/10/2026.
3. Tích hợp classifier loài khi có checkpoint của TV2/TV3 ở bước sau; không bịa top-3.

## Lệnh chạy/tiếp tục

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/prepare_tv4_demo.py --smoke
.venv/Scripts/python.exe scripts/run_demo.py --port 8765
```

Checkpoint setup: `outputs/tv4/setup/progress.json`. Weights hoàn tất được tái
sử dụng; `.part` chưa hoàn tất tải lại riêng model. Smoke đã thành công chỉ được
bỏ qua khi hash ảnh/weights/code và package version khớp. Không chạy lại bước tải TV1.
Server local: http://127.0.0.1:8765. Kiểm tra server đang chạy trước khi mở thêm;
log hiện tại ở `outputs/tv4/server.stdout.log` và `server.stderr.log`.

## Tiếp nhận sau quota

Đọc file này, `git status`, kiểm tra process/log trước khi chạy lại. Không xóa
cache/weights để bắt đầu lại; không sửa file chưa track của thành viên khác.
Cập nhật file này sau mỗi mốc và ghi rõ lỗi nếu bị chặn. Không tuyên bố chạy thật
thành công chỉ vì mock hoặc unit test đạt.

Nguồn: https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md#can-you-share-the-training-data
MDv5b có SWG; MDv5a kế thừa dữ liệu MDv5b. Chia location của dự án không xóa
được việc detector tiền huấn luyện có thể đã thấy dữ liệu SWG.
