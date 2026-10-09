# Điểm tiếp tục công việc TV1 tuần 2

Cập nhật: 2026-10-09. Nhánh: `codex/tv1-week2-download-quality`.

## Nhiệm vụ đã thống nhất

Tải **pilot 4.000 ảnh**, không phải toàn bộ 31.589 ảnh, từ
`data/processed/v1/pilot_v1.jsonl`. Bàn giao ảnh hợp lệ, manifest v2 và log tải.
Giữ nguyên nhãn, box, địa điểm, chuỗi, split và seed 42 của v1; không tự bù mẫu.

## Tiến độ hiện tại: HOÀN THÀNH

- Đã tải đủ 4.000 ảnh, 6.280.158.773 byte. Lượt tải hoàn tất lúc
  `2026-10-08T12:29:16+00:00`, không cần tải lại toàn bộ.
- Đã bổ sung lệnh tiếp tục, checkpoint trên đĩa và khóa chống chạy trùng.
- Đã chốt `data/processed/v2/`: 4.000 ảnh chấp nhận, 0 loại, train 2.800,
  validation 600, test 600, không đổi split.
- Kiểm định độc lập giải mã đủ 4.000 ảnh đạt lúc `2026-10-09T03:54:30+00:00`.
  `reports/tv1_w2/verification.json`: `passed: true`, `local_images_redecoded: true`.
- 79/79 test đạt. Có một cặp trùng trong cùng test/cùng nhãn, đã ghi rõ ở
  `data/processed/v2/duplicates.json`; không có trùng pixel giữa các split.
- Checkpoint máy: `data/interim/download_pilot_v2/task_state.json`, trạng thái
  `complete`. Lượt xử lý đã kết thúc, không còn `active.lock`.
- Báo cáo bàn giao: [REPORT.md](../reports/tv1_w2/REPORT.md).
- Không còn bước xử lý dữ liệu tuần 2 đang dở. Nhánh bàn giao GitHub:
  `codex/tv1-week2-download-quality`; việc review/merge vào `main` là bước riêng.
  Không tự bắt đầu tuần tiếp theo khi người dùng chỉ yêu cầu kiểm tra hoặc tiếp tục.

## Lệnh tiếp tục

Từ thư mục gốc repo, trong PowerShell:

```powershell
.venv/Scripts/python.exe scripts/resume_tv1_w2.py
```

Lệnh tự tìm bước còn thiếu từ dữ liệu trên đĩa. Nếu hoàn thành rồi, chỉ xác minh
lại; không tải lại ảnh hợp lệ, không ghi đè v2. Nếu có tiến trình cũ còn chạy,
không chạy bản thứ hai hoặc xóa lock; đợi tiến trình đó.

Có thể nhắn trợ lý ở lần sau: **"Đọc docs/progress_tv1_w2.md và checkpoint,
tiếp tục phần còn thiếu; không tạo lại split hoặc tải lại toàn bộ."**

## Các file cần giữ

| Đường dẫn | Vai trò |
|---|---|
| `data/images/swg_pilot_v2/` | Ảnh thật, bị Git bỏ qua |
| `data/interim/download_pilot_v2/records/` | Biên nhận/checksum từng ảnh, bị Git bỏ qua |
| `data/interim/download_pilot_v2/task_state.json` | Bước chạy và lỗi gần nhất |
| `reports/tv1_w2/download_events.jsonl` | Log tải nối tiếp, giữ lịch sử lỗi và resume |
| `data/processed/v2/` | Snapshot chỉ đọc sau khi chốt |
| `reports/tv1_w2/verification.json` | Kết quả lần kiểm định gần nhất |
| `docs/handoff_tv1_w2.md` | Quy tắc chất lượng và hướng dẫn bàn giao |

## Lưu ý cho lần làm việc sau

1. Đọc checkpoint, log cuối và kiểm tra tiến trình trước khi chạy lại. Nếu dừng
   đột ngột, trạng thái có thể còn `running`; đó không phải bằng chứng tiến trình còn sống.
2. Nếu thiếu môi trường, dùng Python 3.12 và `requirements-tv2.txt` để chạy toàn bộ test.
3. Nếu chạy lỗi, lưu nguyên văn lỗi và xử lý; không sửa checksum hoặc đổi split để qua kiểm tra.
4. Không đưa ảnh lên Git. Repo có nhiều file chưa track của các thành viên khác;
   không dùng `git add .`, không xóa hoặc gộp chúng vào phần TV1 tuần 2.
5. Không tự bắt đầu tuần 3, huấn luyện hoặc dùng pilot test để chọn mô hình.
6. Người dùng đã yêu cầu push phần tuần 2. Không tự merge vào `main`; chỉ đưa
   những file thuộc bàn giao TV1 tuần 2 vào commit, giữ nguyên file của thành viên khác.
