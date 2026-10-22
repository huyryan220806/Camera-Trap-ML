# Prepared TV2 W4 draft PR

Destination: `huyryan220806/Camera-Trap-ML`, `feat/baseline` → `main`, **Draft**.

Title: `feat(tv2): prepare W4 evaluation with verified gates and pending model evidence`

## Description

W4-02 hiện **BLOCKED**: thiếu checkpoint B2 truy cập được và hồ sơ run B3 gốc có checksum/provenance. Final model lock và protocol còn PENDING; chưa chạy inference hoặc tạo metric/CM Test.

Đã triển khai evaluator fail-closed, mean softmax đủ crop theo ảnh, metric/CM cố định 8 lớp, SHA/leakage checks, khóa file/code phải commit trước Test và chặn official run thứ hai. Khôi phục đủ 600 ảnh Test theo SHA/size/RGB hash và kiểm tra 3.400 ảnh Train/Validation. 465 file/weights/tài liệu cũ giữ nguyên. Không đưa ảnh hay weights vào Git.

Validation: 311/311 regression PASS (gồm 48 test W4), thêm 6/6 source restoration tests PASS; 6/6 test TV3 W4 cô lập PASS; contract 6/6, environment Python3.12, pip, metadata validator và diff check PASS. Giữ log lỗi môi trường/sandbox trước đó.

Cross-review: TV3 W4-03 PENDING FIX; TV4 W4-04 HANDOFF NOT VERIFIED. Không train lại baseline chính thức, không Test tuning, không sửa nhánh thành viên khác. TV1 chưa nghiệm thu W4-02.

Báo cáo: `reports/tv2/TV2_W4.md`. Implementation commit đã push và local/remote HEAD khớp tại lần xác minh: `eff4b1ddd74a94bd6fe54ca7c8078cff7100be50`. Một commit tài liệu tiếp theo ghi nhận trạng thái xuất bản; không thay đổi model lock/protocol hay code đã kiểm thử.

PR chưa được tạo: connector GitHub trả 403; automatic approval review từ chối cả fallback credential-helper và luồng tạo PR qua UI. Tệp này là mô tả đã chuẩn bị, không phải URL hoặc bằng chứng PR đã tồn tại.
