# Báo cáo bàn giao TV1 tuần 2

Ngày: **2026-10-09**. Nhánh: `codex/tv1-week2-download-quality`.
Nhiệm vụ: **Tải tập con và kiểm tra chất lượng**.

## Phạm vi và kết quả

Đã tải pilot **4.000 ảnh / 8 lớp** từ `data/processed/v1/pilot_v1.jsonl`,
không tải toàn bộ 31.589 ảnh. Dung lượng ảnh: **6.280.158.773 byte**, khoảng
**6,28 GB** (không tính manifest, log và môi trường Python).

Snapshot v2 tạo lúc `2026-10-09T03:51:43+00:00`. Giữ nguyên tất cả trường gốc
của v1; chỉ bổ sung thông tin chất lượng và đường dẫn ảnh cục bộ. Seed gốc: **42**.
Không lấy mẫu lại, không bù ảnh và không điều chỉnh split.

| Split | Yêu cầu | Chấp nhận | Bị loại | Chuỗi | Địa điểm | Box |
|---|---:|---:|---:|---:|---:|---:|
| Train | 2.800 | 2.800 | 0 | 2.277 | 458 | 3.125 |
| Validation | 600 | 600 | 0 | 508 | 102 | 680 |
| Test | 600 | 600 | 0 | 495 | 98 | 680 |
| Tổng | **4.000** | **4.000** | **0** | **3.280** | **658** | **4.485** |

Mỗi lớp có **350 train + 75 validation + 75 test = 500 ảnh**, gồm
`large_antlered_muntjac`, `annamite_striped_rabbit`, `sambar`, `chinese_serow`,
`common_palm_civet`, `masked_palm_civet`, `silver_pheasant`, `eurasian_wild_pig`.
Đối chiếu chi tiết 24 cặp lớp/split nằm trong `data/processed/v2/summary.json`.

## Chất lượng và rò rỉ

- 4.000 ảnh tải thành công và qua kiểm tra khi xuất v2; 0 ảnh thiếu/hỏng cuối cùng,
  0 lỗi kích thước hoặc box vượt biên. `excluded_v2.jsonl` rỗng là kết quả hợp lệ.
- Giải mã ảnh chính bằng Pillow, kiểm tra byte tải, kích thước, box, SHA-256 byte
  và pixel RGB. Không resize, xoay EXIF hoặc sửa box để làm kiểm tra đạt.
- Pillow nhận diện **2.109 JPEG, 1.891 MPO** dù đường dẫn có đuôi `.jpg`.
  MPO được kiểm tra ảnh chính; không khẳng định đã kiểm tra mọi frame phụ.
- Không có ID, đường dẫn, chuỗi hoặc địa điểm trùng giữa các split.
- Không có nhóm pixel giống hệt giữa các split. Có **1 cặp trùng byte và pixel**
  trong cùng tập **test**, cùng nhãn `common_palm_civet`, được giữ và ghi rõ trong
  `duplicates.json` theo chính sách đã đặt. Do đó 4.000 ID tương ứng **3.999 nội
  dung pixel khác nhau**, không phải 4.000 quan sát độc lập.
- Hai ID của cặp trùng: `d86f91b0-8c29-11eb-8c2e-000d3a74c7de` và
  `d86f91b6-8c29-11eb-94af-000d3a74c7de`.
- Chưa tìm ảnh gần giống bằng perceptual hash; kiểm tra kỹ thuật không xác nhận
  nhãn loài hoặc độ chính xác ngữ nghĩa của box bằng chuyên gia.

## Log tải và bằng chứng tiếp tục

Log gốc: `reports/tv1_w2/download_events.jsonl`; bản sao đóng băng trong v2.
Có 4.000 sự kiện tải qua mạng thành công, 4.003 lượt tái sử dụng ảnh hợp lệ qua
các lần chạy. Không cộng số sự kiện thành số ảnh duy nhất.

1. 2026-10-08: smoke test 8 ảnh thành công.
2. Lượt tải đầy đủ đầu tiên gặp lỗi xử lý đường dẫn Windows khi tạo thư mục song
   song; giữ lại **3.995 receipt**. Sự kiện `run_interrupted` lưu nguyên lý do.
3. Sau sửa lỗi, tiếp tục bằng **3.995 ảnh cũ + 5 ảnh tải thêm**, hoàn tất đủ 4.000
   lúc `2026-10-08T12:29:16+00:00`. Không xóa cache để tải lại toàn bộ.
4. 2026-10-09: lệnh tiếp tục kiểm tra checksum ảnh cũ và bỏ qua tải mạng trước
   khi chốt v2. Không có lỗi HTTP hoặc lỗi tải ảnh được ghi ở `attempt_failed`
   trong log thực tế; lỗi thiếu/hỏng và retry được kiểm thử bằng dữ liệu giả.

## Tiếp tục sau quota hoặc gián đoạn

Chạy từ thư mục gốc repo:

```powershell
.venv/Scripts/python.exe scripts/resume_tv1_w2.py
```

Script lưu checkpoint ở `data/interim/download_pilot_v2/task_state.json`, receipt
từng ảnh ở `records/`, và luôn kiểm tra dữ liệu thực tế thay vì chỉ tin cờ hoàn tất.
Ảnh hợp lệ được tái sử dụng; `.part` tải dở bắt đầu lại **riêng ảnh đó**, không
resume theo byte. Snapshot v2 đã có không được ghi đè. Lỗi mới không được giữ
báo cáo `passed: true` của lượt cũ làm kết quả cho lượt chạy thất bại.

Khóa hệ điều hành chống chạy trùng và tự nhả khi tiến trình chết; lock PID cũ chỉ
được lưu trữ lại khi chứng minh tiến trình đã dừng. Không tự xóa lock của tiến
trình đang chạy. Ghi chú cho lần tiếp nhận: `docs/progress_tv1_w2.md`.

Script có thể chạy trong PowerShell mà không gọi AI; không có automation tự
khởi động sau quota hoặc sau khi bật máy. Nếu tiến trình dừng, chạy lại lệnh trên.

## Kiểm thử và xác minh

- **79/79 unit/integration tests đạt** với lệnh
  `.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests`.
- Có test tải lại offline, lỗi HTTP/retry, ảnh thiếu/hỏng, tải dở, cache đổi,
  bảo toàn split, đối chiếu số lượng, phát hiện sửa snapshot, chạy lần hai không
  build đè, khóa tiến trình và phục hồi sau tiến trình con thoát đột ngột.
- **Kiểm định độc lập đạt trên đủ 4.000 ảnh**, hoàn tất lúc
  `2026-10-09T03:54:30+00:00` (10:54:30 giờ Việt Nam).
  `reports/tv1_w2/verification.json` ghi `passed: true`, `local_images_redecoded: true`,
  `v1_fields_preserved: true`, `checksums_verified: true`, `split_changes: 0`.
- Checkpoint đã ghi `complete`; tiến trình kết thúc thành công và nhả khóa.
- Manifest v1 không thay đổi. Checksum pilot nguồn:
  `e014967e8ecdda18ea7468fba2a7312973b4eec468e61a3faabfd84169a75f8f`.
- Checksum manifest v2:
  `5f957ea6004d9a8d468bd111bae2a7a2ffb29ffef295cde33c0df1a8ff3454cc`.

## Bàn giao cho TV2 và TV3

Ảnh ở `data/images/swg_pilot_v2/`, không đưa lên Git. Dùng cùng `train.jsonl`,
`val.jsonl`, `test.jsonl` trong v2 và mở ảnh bằng `ROOT / row['quality']['local_path']`.
Crop kế thừa split của ảnh gốc, không tự chia ngẫu nhiên lại. Máy khác nhận code
và snapshot qua Git rồi chạy lệnh tiếp tục để tải/xác minh ảnh cục bộ.

Pilot có phân bố cân bằng được chọn có chủ đích, chỉ dùng thử pipeline. Không
chọn mô hình/ngưỡng bằng pilot test hoặc coi điểm trên pilot là kết quả cuối cùng
đại diện toàn SWG. Các kiểm tra trên test trong tuần này đều tự động và kỹ thuật.

Nhánh bàn giao code, snapshot và báo cáo: `codex/tv1-week2-download-quality`.
Ảnh và cache không thuộc commit. Việc review/merge vào `main` là bước riêng.
