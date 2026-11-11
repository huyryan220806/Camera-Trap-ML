# Tích hợp tuần 6 — tiến độ 11/11/2026

Người dùng xác nhận cả nhóm đã xong và yêu cầu merge vào main. Được phép merge
và push, không đổi model mặc định hoặc mở lại Official Test.

## Snapshot đã lấy

- Main ban đầu: `cfcf006`.
- TV1 `feat/metadata-split`: `11e4510`.
- TV2 `feat/baseline`: `96d2025`, R6 independent replay ACCEPTED.
- TV3 `feat/crop-classifier`: `450f15b`, R6 519/600 validation đúng,
  accuracy 86,50%, macro-F1 86,41867348%.
- TV4 `feat/demo`: `bbbccf9`, adapter R1–R4 và R6, PR #9.

## Tiếp tục nếu bị gián đoạn

Worktree tích hợp tách biệt ở `outputs/integration_w6_20261111/worktree`, detached
HEAD. Repo chính và dữ liệu/ảnh/checkpoint/slide local được giữ nguyên. Kiểm
`git status`, `git log` trong worktree này trước khi tiếp tục; không merge lại
các nhánh đã là ancestor. Chưa push cho tới khi kiểm thử tích hợp đạt.

TV1, TV2, TV3 đã merge tại `4b41570`, `04ddffa`, `52505d6`. Merge TV4 có một
conflict add/add tại `src/training/dino_w6.py`: TV3 chứa validator R6 3 giờ,
TV4 cần source cũ R1–R4 với hash cố định. Giải pháp giữ canonical TV3, sao chép
nguyên byte source cũ sang `dino_w6_r1_r4.py`, giữ riêng snapshot R6 sẵn có,
đổi adapter trỏ tới snapshot cũ. Không thay config/checkpoint hoặc hash đã khóa.

## Tiếp tục ngày 12/11/2026

Full suite đã kết thúc trước khi hết quota: **551/551 PASS**, 110,221 giây,
exit 0. Không còn tiến trình Python của lượt kiểm thử. Đã đọc log và receipt
thật, không chạy lại suite khi source không đổi.

Fetch lại xác nhận main và bốn đầu nhánh không đổi. Kiểm bổ sung môi trường,
sáu JSON examples, JavaScript syntax, registry R6 đã khóa và comparison
metadata đều PASS. Bốn loại giao cắt ảnh/path/chuỗi/địa điểm đều bằng 0;
không thay split, không mở ảnh Test.

Đã kiểm 5 source pins và 6 nhóm dữ liệu/artifact không đổi. Bằng chứng được
lưu ở `reports/integration_w6/`. README, mục lục và hướng dẫn native snapshot
đã cập nhật. [Biên bản](integration_week6.md) ghi đủ phạm vi và giới hạn.

Bước còn lại: stage đúng các file tích hợp, commit merge TV4, kiểm remote,
fast-forward main, push không force và xác minh cả bốn đầu nhánh đã nằm trong
origin/main. Chưa công bố trạng thái push thành công ở mốc này.
