# Progress: push TV4 và review TV2/TV3 tuần 2

Yêu cầu mới: push/bàn giao TV4, kiểm tra công việc TV2 và TV3. Không tự merge.

## Mốc nguồn

- TV4: nhánh `codex/tv4-week2-demo-detector`, nền TV1 `b9a92b9`.
- TV2 đã fetch: `origin/feat/baseline`, commit `8a48b86`.
- TV3 đã fetch: `origin/feat/crop-classifier`, commit `a63d9b3`.
- main vẫn `4e7ad47`. Không xóa/sửa file chưa track của thành viên khác.

## Đã hoàn thành

1. Đã commit/push TV4 `c69283a659c27498d1e9ec43781777af4dc37282` lên
   `origin/codex/tv4-week2-demo-detector`; đã xác minh remote SHA. 91 test đạt.
2. TV2: 29 test đạt; audit 192 ID khớp pilot/v2, metric khớp confusion matrix.
   Tái hiện smoke/prepare ghi đè manifest cũ và validator bỏ qua hash validation.
   Chưa có checkpoint thật để reload độc lập.
3. TV3: 51 test đạt; 6.895 crop/5.996 ảnh cha, không trùng split ID, mapping đúng.
   Tái hiện lỗi resume (skip tải lỗi/crop thiếu), limit tăng tập mẫu và Dataset
   nhận split/nhãn sai. Đầu vào hiện là v1 đầy đủ, chưa phải pilot v2 chung.
4. Báo cáo: `reports/review_TV2_W2_2026-10-09.md`,
   `reports/review_TV3_W2_2026-10-09.md`; evidence/probe `reports/review_w2/`.
5. Bàn giao chung: `docs/handoff_team_w2.md`. Bộ docs/evidence được quản lý trong
   commit `docs: hand off TV4 and review week-2 member branches` trên nhánh TV4.
   Khi tiếp nhận, đối chiếu `git log` và remote trước khi push thêm; không đưa
   ảnh/weights hoặc file lạ vào commit.

## Checkout review có thể tái sử dụng

- TV2: `C:/Users/loval/.codex/worktrees/review-tv2-week2/CameraTrapML`.
- TV3: `C:/Users/loval/.codex/worktrees/review-tv3-week2/CameraTrapML`.
- Cả hai là managed worktree đã gắn vào chat; code không bị sửa, Git sạch sau test.
- Main giữ `4e7ad47`; không tạo PR hoặc merge trong lần review này.

## Tiếp tục sau quota

Đọc file này và trạng thái Git/remote. Không push lại bằng force, không merge
nhánh thành viên vào main chỉ để chạy test. Dùng checkout review đã có trong
artifacts; không tạo thêm nếu checkout cũ còn phù hợp. Kết luận phải phân biệt
test đạt với việc đã có đủ checkpoint/crop artifact để tái kiểm định kết quả.
