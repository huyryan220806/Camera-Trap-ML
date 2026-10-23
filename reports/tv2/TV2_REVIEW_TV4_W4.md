# TV2 review TV4 W4-04 — kiểm tra lại 23/10/2026

**PENDING FIX — W4-04 HANDOFF NOT VERIFIED**. Fetch lại cho thấy `origin/feat/demo` vẫn ở `254b40eab77b849647a2291aa0257c1b161b4da2`; không có đường dẫn W4/Week4 mới trong Git tree. [Audit mới](w4_evidence/continuation_01/repository_audit.json).

Tái sử dụng review W3 đã kiểm tra: needs_review/top predictions/no_detection, cache, xóa kết quả khi đổi ảnh/model và JSON contract có code/fixtures. Regression mới kiểm tra lại chúng; không lấy W3 thay nghiệm thu W4. [Review lịch sử](https://github.com/huyryan220806/Camera-Trap-ML/blob/a66f41cb7f966f17de7e132e1433103958c1af72/reports/tv2/TV2_REVIEW_TV4_W4.md).

TV4 vẫn cần push màn hình sửa nhãn và contract/export phân biệt nhãn người sửa với dự đoán gốc; log benchmark W4 với hardware/CPU-GPU, batch size/resolution, cold/warm, thống kê latency và phân tách load/preprocessing/MegaDetector/classifier. Cần bằng chứng nhiều box, detector miss/no_detection, confidence thấp và không giữ prediction cũ. Chưa có artifact W4 để chạy smoke/UI acceptance thực tế. Không sửa code TV4, không coi điểm thấp là loài lạ hoặc softmax đã calibration.

Handoff TV4 thiếu là công việc cross-review riêng; blocker khoa học trực tiếp của Test B2 hiện là việc xác minh reference B3/final selection chưa đóng.
