# Quy ước làm việc nhóm

## Branch và Pull Request

Từ 16/10/2026, mỗi thành viên dùng **một branch cố định** cho các tuần tiếp theo. `main` dành cho bản đã kiểm tra. Người làm push branch, tạo Pull Request (PR), nhờ một thành viên khác kiểm tra rồi mới merge. Không force-push branch người khác và không tạo thêm nhánh `codex/...` cho công việc thường lệ.

| Thành viên | Branch cố định | Phạm vi chính | Người kiểm tra tuần 1 |
|---|---|---|---|
| TV1 | `feat/metadata-split` | Metadata, EDA, split | TV2 |
| TV2 | `feat/baseline` | Môi trường học máy và đánh giá | TV3 |
| TV3 | `feat/crop-classifier` | Box và pipeline vùng cắt | TV1 |
| TV4 | `feat/demo` | Cấu trúc dự án và giao diện dữ liệu | TV2 |

```powershell
# Ví dụ TV1; các thành viên khác thay bằng branch của mình.
# Commit hoặc cất giữ thay đổi đang làm trước khi cập nhật.
git fetch --prune origin
git switch feat/metadata-split
git pull --ff-only origin feat/metadata-split
git merge origin/main
# Sửa file và chạy kiểm tra
git status
git add duong-dan-file-can-nop
git commit -m "Describe the completed change"
git push origin feat/metadata-split
```

Trên máy chưa có branch local, dùng `git switch --track origin/feat/metadata-split` một lần (thay tên cho đúng thành viên). Giữ nguyên bốn branch cố định sau khi merge PR; không chọn xóa branch sau merge. Khi `main` cập nhật, merge `origin/main` vào branch đang làm và giải quyết conflict, không reset làm mất công việc chưa gộp.

TV1 và TV4 tuần 2 đã chuyển từ các nhánh `codex/...` về nhánh cố định. Xem
[tuần 2](docs/integration_week2.md), [tuần 3](docs/integration_week3.md) và
[bản tích hợp tuần 4 ngày 25/10/2026](docs/integration_week4.md). `main` hiện
gồm các phần tuần 4 đã kiểm tra của cả nhóm, kèm giới hạn B3 chưa tái lập.
Push branch không tự cập nhật `main`; mỗi lượt tiếp theo vẫn cần kiểm tra và merge.

## Trước khi yêu cầu kiểm tra

1. Chạy `scripts/check_environment.py`, `scripts/validate_results.py` và toàn bộ unittest theo README.
2. Xem `git diff --check` và `git diff --stat`; chỉ stage file liên quan.
3. Ghi trong PR: vấn đề, thay đổi, lệnh kiểm tra, kết quả và phần chưa triển khai.
4. Người kiểm tra chạy lại các lệnh, đối chiếu tiêu chí bàn giao và ghi nhận xét. Chỉ người kiểm tra xác nhận nghiệm thu.

## Dữ liệu và mô hình

- Không commit `.venv`, ảnh, ZIP metadata, SQLite, trọng số, token hoặc mật khẩu.
- Manifest v1 đã đưa vào repo làm bản dùng chung. Không sửa trực tiếp split, class ID hay kết quả kiểm tra của phiên bản này. Tạo phiên bản mới nếu có thay đổi hợp lệ.
- Mọi crop kế thừa split của ảnh gốc. Không dùng test hoặc pilot test để chọn mô hình, ngưỡng hay augmentation.
- Không xóa, sửa hoặc định dạng lại file ngoài công việc đang làm. Nếu hai người cần sửa cùng file, trao đổi trước và giữ các thay đổi của nhau khi giải quyết conflict.
- `.gitattributes` giữ nguyên byte của JSON/JSONL để bảo toàn checksum. Không tự đổi kiểu xuống dòng trong manifest đã khóa.

## Khi có conflict

Commit hoặc cất giữ công việc của mình trước. Chạy `git fetch origin`, merge nhánh nền vào branch đang làm, xem từng file conflict với người phụ trách, chạy lại kiểm tra rồi commit. Không dùng `reset --hard` hoặc chọn bỏ toàn bộ một phía để xử lý nhanh.
