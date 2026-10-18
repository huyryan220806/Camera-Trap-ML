# TV2 W3 B1/B2 comparison

Trạng thái: **B1 TRAINED – B1/B2 COMPARISON PENDING**.

| Điều kiện / metric | B1 full image | B2 crop |
|---|---:|---:|
| Commit code được chạy/review | `d81f584` | `c01a751` review read-only |
| Dữ liệu chung | TV1 `comparison_v1`, PASS | Bundle có mặt; official gate chưa đạt |
| Protocol | Đúng cấu hình nhóm | Cấu hình chính đã gần khớp; còn lỗi triển khai |
| Official training | COMPLETED | Chưa có run được nghiệm thu |
| Best epoch | 22 | N/A |
| Macro-F1 cấp ảnh | **0,5624506868** | N/A |
| Macro-precision | **0,5748610369** | N/A |
| Macro-recall | **0,565** | N/A |
| Accuracy | **0,565** | N/A |
| Validation support | 600 parent images | N/A |
| Checkpoint reload | PASS | NOT TESTED |

Không tính chênh lệch B1–B2 và không chọn mô hình thắng khi B2 chưa có kết quả
official tái lập. Synthetic test hoặc metric crop-level không thay thế metric cấp
parent image trên cùng 600 ảnh validation.

TV3 commit `c01a751` đã PASS 23/23 test cô lập, nhưng test hiện chưa phát hiện loss
cân bằng ảnh bị sai khi crop của một parent bị chia qua nhiều shuffled batch. Ngoài
ra config tắt hash preflight, output có thể ghi đè, và training không chạy fresh
reload. Chi tiết ở [review TV3](TV2_REVIEW_TV3_W3.md).
