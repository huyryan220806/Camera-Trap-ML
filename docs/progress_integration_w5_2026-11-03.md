# Tích hợp tuần 5 — tiến độ ngày 03/11/2026

Người dùng yêu cầu push báo cáo review, merge các phần tuần 5 vào main và hướng dẫn chạy/test. Đã cho phép merge trong lượt này; không cần hỏi lại vì ghi chú chờ review của tài liệu cũ.

## Đầu vào đã xác minh

- TV1 `9abc9c5`, TV2 `df31029`, TV3 `5734d38`, TV4 `8d4a255`; main `60516f5`.
- Fetch ngày 03/11 không có commit mới so với kiểm tra ngày 02/11.
- Cây gộp thử `33e3be4c9cce0ab98196b67ff17325eda4a0cbe6` đã qua 440/440 tests; adapter và browser thật PASS. Không cần lặp training hay official Test.
- Báo cáo cần công bố: `reports/review_w5_2026-11-02/` và `docs/progress_review_w5_2026-11-02.md`. Giữ nguyên byte các evidence theo index SHA; không stage ZIP DINO trong `reports/tv3_w5/` hoặc file cá nhân cũ.

## Công việc lượt này

1. Commit/push báo cáo trên nhánh TV1.
2. Gộp các nhánh đã nghiệm thu vào main, giữ nguyên lịch sử và bốn nhánh cố định.
3. Cập nhật README/hướng dẫn/trạng thái bàn giao; kiểm mã và dữ liệu giống cây đã test.
4. Chuẩn bị DINO local, kiểm lệnh chạy demo với đường dẫn chính thức; giữ checkpoint và journal QA.
5. Push main, xác minh remote/PR và đồng bộ các nhánh theo fast-forward nếu không có công việc mới.

Trạng thái chi tiết tiếp tục được cập nhật trong file này và `outputs/integration_w5_2026-11-03/`. Khi quay lại, kiểm `git status`, log, remote và tiến trình trước khi lặp lệnh. Không reset, force-push hoặc xóa branch.

## Ghi nhớ lịch dự án từ TV1

Ngày **03/11/2026**, TV1 cho biết sẽ triển khai tuần 6 vào tối nay; giảng viên đã cho thêm vài tuần. **Chưa có hạn nộp mới cụ thể.** Mốc W6 04–10/11 trong plan cũ chỉ là lịch đề xuất trước khi gia hạn, không còn là căn cứ khẳng định hạn cuối. Lượt này chỉ ghi nhận thông tin, chưa triển khai tuần 6, tự thay lịch chi tiết hoặc mở thêm thí nghiệm/GPU job.
