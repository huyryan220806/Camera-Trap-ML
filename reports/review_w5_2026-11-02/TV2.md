# TV2 tuần 5 — kết quả kiểm tra ngày 02/11/2026

**Đạt phần kỹ thuật đánh giá.** Commit `df31029c2dfa3b87e4efd1b1f210babd89c60cbd`, nhánh `feat/baseline`. Không phát hiện lỗi đang chặn tích hợp trong phạm vi đã kiểm. Đây là biên bản TV1; chưa gửi review/approval lên GitHub.

## Đã xác minh

- 32/32 kiểm thử `test_w5_validation` PASS.
- Evaluator nguyên bản chạy trên ZIP/checkpoint DINO thật: `ARTIFACT_VERIFIED`, đúng 600 ảnh / 680 crop validation.
- Tính độc lập từ dự đoán gốc ra accuracy 0,845, macro-F1 0,8444008279545706; CM/support và mean vector/argmax khớp. Không nhầm metric crop với metric ảnh.
- Đối chứng cùng image ID với B2: 95 ảnh cải thiện, 36 ảnh giảm, 412 cùng đúng, 57 cùng sai. Phân tích recall masked-civet giảm và hai lớp civet nhầm nhau nhiều hơn đã được giữ trong chương thực nghiệm.
- Dự đoán và metrics từ fresh-process replay do TV2 công bố bằng toàn bộ tham chiếu TV3; cấu hình, protocol, source và checkpoint khớp. TV1 không gọi việc đọc hồ sơ này là một lượt forward validation mới tại TV1.
- Chương thực nghiệm tách validation, Test B2 lịch sử và demo; không tuyên bố 88%/SOTA/test độc lập. Không sửa dữ liệu khóa hoặc hồ sơ Test W4.

## Việc cần chốt tài liệu

Phần đầu `reports/tv2/TV2_W5.md` và chương thực nghiệm còn ghi chờ adapter và `UI-A11Y-01`. Kiểm tra TV1 hôm nay trên TV4 `8d4a255` đã PASS adapter/browser/mobile/CSV; xem [TV4](TV4.md). TV2 cập nhật trạng thái và kiểm tra/ghi nhận review PR theo vai trò của mình, không xóa evidence cũ hoặc ghi rằng TV2 đã chạy một phép thử do TV1 thực hiện.

Không cần train thêm chỉ để hoàn thành W5. Mục tiêu 88% vẫn chưa đạt; cài sạch và gói bảo vệ thuộc tuần 6. Native model acceptance đã đạt, không tiếp tục mô tả checkpoint là chưa được kiểm định.

[Tests TV2](evidence/tv2_tests.txt) · [evaluator](evidence/tv2_evaluator_audit.json) · [audit TV1](evidence/independent_audit.json) · [biên bản chung](REPORT.md).
