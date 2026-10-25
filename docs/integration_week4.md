# Tích hợp tuần 4 — 25/10/2026

Người dùng yêu cầu gộp toàn bộ phần đã hoàn thành vào main, cập nhật README và
sắp xếp tài liệu. Không tạo nhánh mới, không xóa bốn nhánh cố định.

## Các phần được gộp

| Thành viên | Đầu nhánh đã kiểm tra | Phạm vi |
| --- | --- | --- |
| TV1 | `4bcf85c` | Khóa B2, kiểm kê test và ví dụ dữ liệu |
| TV2 | `5fe9083` | Kết quả Test B2, đã ở main qua PR #7 (`c6aee9f`) |
| TV3 | `a692a10` | Báo cáo B2/B3 và sửa kiểm định sau review; PR #6 |
| TV4 | `beb828d` | Duyệt/sửa nhãn, log và benchmark demo |

Bản tích hợp: `d04fe09` gộp TV1, `93ae799` gộp TV3, `1b9e118` bổ sung tài liệu
và bằng chứng. Lịch sử commit của thành viên giữ nguyên. Main cập nhật sau kiểm tra.

## Trạng thái kiểm tra / tiếp tục

- Toàn bộ kiểm thử bản gộp: **377/377 PASS**, 90,560 giây.
- Môi trường chung và 6 fixture hợp đồng JSON PASS.
- Metadata comparison_v1 PASS: 4.000 ảnh giữ nguyên, 0 thay đổi split,
  B1/B2 cùng ảnh/nhãn; không giao image ID, file path, chuỗi hoặc địa điểm.
- Browser Edge PASS với MegaDetector + B2 thật, duyệt/lưu/xuất JSON và ba cỡ
  màn hình 1440×1100, 390×844, 320×740. Không có lỗi JavaScript.
- Liên kết nội bộ trong các tài liệu đã sửa PASS; checkpoint B2/B3, dữ liệu
  khóa và các hồ sơ thí nghiệm giữ nguyên theo commit gốc/SHA.
- Bằng chứng: [tests](../reports/integration_w4/tests.txt),
  [environment](../reports/integration_w4/environment.txt),
  [contracts](../reports/integration_w4/contracts.txt),
  [metadata](../reports/integration_w4/comparison.json),
  [browser](../reports/integration_w4/browser.json),
  [audit](../reports/integration_w4/audit.json).
- Log làm việc local: `outputs/integration_w4_2026-10-25/`.
- **Đã công bố:** xác minh `1b9e118` có trên `origin/main` và `origin/feat/demo`.
  [PR TV3 #6](https://github.com/huyryan220806/Camera-Trap-ML/pull/6) đã được
  GitHub ghi nhận **merged**, merge commit `93ae799`. TV2 đã merge qua PR #7.
- Bốn nhánh cố định được đồng bộ fast-forward về bản chung, không force-push,
  không tạo hoặc xóa nhánh. Các commit tiếp theo chỉ ghi nhận việc công bố.
- Nếu quota bị ngắt, đọc file này,
  kiểm tra git log/status và các tiến trình trước khi chạy tiếp; không merge lại
  các commit đã là ancestor, không chạy lại official Test hoặc benchmark đã hoàn tất.

Máy thành viên cập nhật bằng `git fetch origin`, chuyển về nhánh của mình rồi
`git merge --ff-only origin/<nhánh-của-mình>` khi working tree sạch. Nếu có commit
chưa push riêng thì merge `origin/main` theo CONTRIBUTING, không reset bỏ việc.

## Dữ liệu và giới hạn giữ nguyên

B2 là mô hình đã khóa; Test macro-F1 72,63% trên 600 ảnh với GT boxes. B3 còn
UNRESOLVED về tái lập tham chiếu gốc, không bật trong demo hay Test. Gộp mã và
hồ sơ B3 không có nghĩa nghiệm thu B3 đạt tái lập hoặc tốt hơn B2.

Giữ nguyên byte dữ liệu khóa, checkpoint, kết quả thí nghiệm và Test chính thức.
Không sửa nhãn/split, không huấn luyện lại hoặc forward lại Test trong lượt tích hợp.
Các báo cáo từng lượt giữ thời điểm và trạng thái cũ để truy vết; biên bản này
là nơi ghi trạng thái tổng hợp mới nhất.

## Dọn tài liệu

README tập trung vào mở web, cài đặt, kết quả, bàn giao và kiểm tra. Thêm
`docs/README.md` làm mục lục hiện tại/lịch sử; cập nhật môi trường, kiến trúc,
hợp đồng review JSON và quy ước nhánh. Không di chuyển/xóa dữ liệu hay bằng chứng
để làm gọn giao diện repo; các file local chưa được theo dõi được giữ riêng.
