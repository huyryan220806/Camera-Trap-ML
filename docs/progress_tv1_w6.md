# Progress TV1 W6 — train mở rộng và kế hoạch bốn thành viên

**Bắt đầu:** 03/11/2026. **Nhánh:** `feat/metadata-split`. Nền: `cfcf006`.
**Trạng thái hiện tại:** hoàn thành phần kỹ thuật TV1; snapshot đã phát hành local,
chờ TV2 peer review. Bốn kế hoạch đã tạo. Chưa push/merge trong nhiệm vụ này.

## Kết quả cuối và cách tiếp tục

- `train_expansion_w6_v1`: thêm **1.446** ảnh, cách ly **219**; train mới
  **4.246 ảnh / 4.729 crop**. Val/Test cũ giữ nguyên; 0 đổi nhãn/split.
- Kiểm định 5.774 ảnh; 80 mẫu được Codex xem trực quan (không phải chuyên gia),
  23 mẫu cách ly. 191 ảnh nghi trùng gần vẫn pending, không được gọi là trùng chắc chắn.
- 72 test PASS; portable verify, audit độc lập, resume không đổi byte và thử
  manifest bị sửa đều đạt. [Báo cáo](../reports/tv1_w6/REPORT.md) có đủ bằng chứng.
- Checkout sạch từ Git index, không ảnh/state tải, cũng verify PASS:
  `reports/tv1_w6/portable_checkout_verification.json`.
- Gói train ngoài Git: `outputs/tv1_w6/swg_train_expansion_w6_v1_additional.zip`,
  2.246.204.406 byte; [checksum](../reports/tv1_w6/image_package.json).
- Gói hình rà mẫu: `outputs/tv1_w6/visual_review_contact_sheets.zip`.
- Không còn tải/audit chạy nền; các PID trong lịch sử bên dưới đã kết thúc.
- Không chạy lại `scan` hoặc tạo lại release. Chạy wrapper resume hoặc
  `scripts/prepare_tv1_w6.py verify` để xác minh bản đã có. Chỉ thêm
  `--check-images` khi muốn decode lại độc lập và có đầy đủ ảnh.
- Việc tiếp theo của nhóm: TV2 review SHA release, TV3 chạy các lượt đã đăng ký,
  TV4 tích hợp ứng viên vượt kiểm định. Không có model W6 đã train trong nhiệm vụ TV1.

Provenance SHA: `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`.
[Bàn giao và lệnh dùng dữ liệu](handoff_tv1_w6.md).

## Lịch sử triển khai (không phải trạng thái còn đang chạy)


## Đã chuẩn bị

- Bốn kế hoạch `docs/plans/TV1_W6.md` đến `TV4_W6.md`; mục tiêu vượt DINO W5.
- Config `configs/train_expansion_w6_v1.json` quy định chất lượng trước xem ảnh.
- Nguồn: 1.665 train ứng viên W5, 4.000 pilot cũ; 109 holdout chỉ kiểm tra
  nội dung/trùng lặp, không suy luận hoặc phát hành test mới.

## Tiếp tục nếu bị ngắt

Trước tiên đọc file này, kiểm tra `git status` và tiến trình theo PID trong
`outputs/tv1_w6/download_processes.json`. Không chạy thêm writer nếu tiến trình
cũ còn đang hoạt động. Log stdout/stderr nằm cùng thư mục. Tiến trình tải chạy
ẩn để có thể tiếp tục sau khi chat hết quota; nếu dừng, chạy lại đúng lệnh dưới.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/download_subset.py --source data/processed/w5_candidates_v1/train_extension_candidates.jsonl --images data/images/swg_w5_extension --state data/interim/download_w5_extension --log outputs/tv1_w6/train_download_events.jsonl --workers 4
.venv/Scripts/python.exe -X utf8 scripts/download_subset.py --source data/processed/w5_candidates_v1/holdout_candidates.jsonl --images data/images/swg_w6_holdout_audit --state data/interim/download_w6_holdout_audit --log outputs/tv1_w6/holdout_download_events.jsonl --workers 2
```

Ảnh có receipt hợp lệ được xác minh và dùng lại; ảnh tải dở chỉ tải lại ảnh đó.
Không xóa state/quarantine/log, không đổi split, không tự bù ảnh lỗi.
Sau tải còn bước decode/hash, near-duplicate, kiểm tra trực quan, phát hành
write-once, kiểm thử và báo cáo. File này sẽ cập nhật với lệnh audit/release.

## Công cụ đã viết, chưa đồng nghĩa dữ liệu đã phát hành

- `scripts/prepare_tv1_w6.py`: scan → sheets → release → verify; dùng lock,
  cache đã đối chiếu byte SHA, staging và snapshot không ghi đè.
- `scripts/resume_tv1_w6.ps1`: tiếp tục toàn bộ pipeline; dừng ở bước rà trực
  quan nếu chưa có bản ghi, không tự điền đã kiểm tra.
- `requirements-data-w6.txt`: môi trường audit có SciPy cho pHash.
- 12 kiểm thử W6 đã PASS lúc phát triển; kết quả tổng hợp sẽ nằm trong báo cáo.
- Kiểm thử tập trung W2/W3/W5/W6: **72/72 PASS**, log
  `reports/tv1_w6/tests.txt` (10,282 giây).
- Tải chạy nền từ 22:47 ngày 03/11; PID wrapper train 31484, holdout 10256.
  Holdout đã tải đủ 109/109, 173.588.482 byte, không suy luận model.
- Hash nội dung 4.000 pilot + 109 holdout đang chạy độc lập; PID wrapper
  22216, log `outputs/tv1_w6/reference_hashes.stdout.log`, state trong
  `data/interim/train_expansion_w6_v1/task_state.json`. Chờ writer này kết thúc
  trước `scan`; cache giữ lại cho lần audit đầy đủ.
- Lúc 22:58: đã tải hơn 1.100/1.665 train hợp lệ; con số mới nhất trong log,
  chưa kết luận cuối cùng về chất lượng/rò rỉ nội dung.
- **23:04:** train tải đủ **1.665/1.665**, 2.577.829.468 byte, chưa có lỗi tải;
  hash 4.109 ảnh tham chiếu đã hoàn tất. Warm hash ảnh mới PID 28284.
  Wrapper `outputs/tv1_w6/finish_scan.ps1` PID 9516 chờ writer này kết thúc,
  rồi tự chạy `scan` và `sheets`; stdout/stderr tại `outputs/tv1_w6/scan.*.log`.
  Nếu chat ngắt, chờ wrapper này xong, đọc audit/visual queue và tiếp tục rà ảnh.

Lệnh tiếp tục toàn phần (sau khi xác nhận downloader cũ đã dừng):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/resume_tv1_w6.ps1
```

Hoặc từng bước sau tải:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w6.py scan
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w6.py sheets
# Xem ảnh, ghi reports/tv1_w6/visual_review.json đúng queue/hash trước bước release.
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w6.py release
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w6.py verify --check-images
```

`verify` có thể chạy từ snapshot trên máy khác không cần state tải cũ. Không
chạy `scan` sau khi đã phát hành; khi đó wrapper chỉ xác minh bản đã có.

Không sửa `src/training/dino_probe.py`, các snapshot W1–W5 hoặc weights.
Không huấn luyện model/khởi động việc TV2–TV4 trong nhiệm vụ TV1 này.
