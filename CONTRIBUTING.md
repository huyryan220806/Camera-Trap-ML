# Quy ước làm việc nhóm

## Branch và Pull Request

Mỗi công việc dùng một branch. `main` dành cho bản đã kiểm tra. Người làm push branch, tạo Pull Request (PR), nhờ một thành viên khác kiểm tra rồi mới merge. Không force-push branch người khác.

| Thành viên | Phạm vi chính | Người kiểm tra tuần 1 |
|---|---|---|
| TV1 | Metadata, EDA, split | TV2 |
| TV2 | Môi trường học máy và đánh giá | TV3 |
| TV3 | Box và pipeline vùng cắt | TV1 |
| TV4 | Cấu trúc dự án và giao diện dữ liệu | TV2 |

```powershell
git switch main
git pull --ff-only origin main
git switch -c feat/ten-cong-viec
# Sửa file và chạy kiểm tra
git status
git add duong-dan-file-can-nop
git commit -m "Describe the completed change"
git push -u origin feat/ten-cong-viec
```

Nhánh tuần 1 `feat/demo` kế thừa `feat/metadata-split`, vì cần class map và manifest của TV1. Nếu hai PR cùng mở, merge TV1 vào `main` trước, sau đó kiểm tra PR của TV4. Người kiểm tra không được tính phần TV1 là phần mới của TV4. Với công việc sau này, tạo branch mới từ `main` đã cập nhật.

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
