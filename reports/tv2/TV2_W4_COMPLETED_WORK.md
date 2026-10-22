# TV2 W4 completed work and blockers

**W4-02 BLOCKED**. Hoàn thành tối đa phần độc lập; không tự nghiệm thu.

| Hạng mục | Trạng thái / bằng chứng |
|---|---|
| Fetch, audit main và bốn branch | DONE; repository_audit.json ghi exact commit |
| Đồng bộ baseline | DONE; fast-forward 8a7c99c → 0d822a9, không merge PR thành viên khác |
| Đọc hai kế hoạch local | DONE; SHA và trích nội dung tại plans.json; không sửa/stage tài liệu cá nhân |
| Kiểm kê manifest/provenance/TV1 quality handoff | DONE; metadata + khôi phục và kiểm tra 600/600 raster gốc, không inference |
| Tính lại B2/B3 Validation từ CM | DONE; validation_matrix_audit.json |
| Review crop-vs-image weights B3 | DONE; kết luận nghiệm thu PENDING FIX |
| Review TV4 W4 | DONE phần xác minh nguồn; HANDOFF NOT VERIFIED |
| Evaluator và tests TV2 | DONE; log regression và w4_tests_py312.txt |
| Hồ sơ final selection và protocol | PREPARED/PENDING; không khóa giả |
| Test inference/metrics/CM/per-class/lỗi thực | BLOCKED; không có số liệu giả |
| Commit/push/PR | Xem publication.json và PR; không suy diễn từ checklist |
| TV1 nghiệm thu | PENDING; chưa có bằng chứng phê duyệt W4 |

## Điều kiện tiếp tục

1. TV3 bàn giao B2 file/hash đã công bố qua đường dẫn truy cập được; không đổi checkpoint. Bàn giao B3 weights ngoài Git cùng SHA/size, config, provenance, log, validation/reload artifact gốc và giải thích basis='crop'. TV2 đối chiếu Validation ID, metric và đánh lại review.
2. DONE: đã khôi phục đủ 600 ảnh Test chính xác theo SHA/byte size/pixel hash và decode. Không loại mẫu, không đổi split/nhãn và không dùng hình ảnh để chọn model/ngưỡng.
3. Khi bằng chứng đủ, tạo final lock thực sự với timestamp/SHA, review và protocol liên kết; commit trước official Test forward. Giữ B2 theo quyết định Validation. Không tự đổi JSON thành LOCKED nếu chưa kiểm chứng.
4. TV4 push bàn giao W4-04 riêng để kiểm thử sửa nhãn và benchmark; blocker này thuộc cross-review, không tự nó cấm argmax classification khi các điều kiện khoa học khác đạt.

Tiếp tục trong W4; không triển khai W5/W6, không train lại các mô hình, không sửa nhánh TV1/TV3/TV4.
