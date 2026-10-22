# TV2 review TV4 W4-04

Kết luận: **PENDING FIX — W4-04 HANDOFF NOT VERIFIED**.

Remote `origin/feat/demo` là `254b40eab77b849647a2291aa0257c1b161b4da2`. Không có đường dẫn W4/Week4 trong tree được audit. Báo cáo mới nhất thực tế là [W3 continuation](../tv4_w3_continuation/REPORT.md), đã tích hợp trên main; không dùng nó làm nghiệm thu W4-04.

## Khả năng đã có từ W3

Code `src/demo/inference.py` chuyển điểm dưới ngưỡng sang `needs_review`, top predictions theo box, `no_detection` không gọi classifier, và ghi cảnh báo softmax chưa calibration. `app/app.js` xóa kết quả khi đổi ảnh/mô hình/ngưỡng, hiển thị điểm và top predictions; fixture kiểm thử nhiều box, cache và JSON export có trong suite chung. Log [regression Python 3.12](w4_evidence/regression_tests_final.txt) ghi kết quả chạy thực tế phiên này. Các fixture không chứng minh độ chính xác detector trên Test.

## Chưa đủ bằng chứng W4

| Yêu cầu | Kết quả |
|---|---|
| Màn hình cho người dùng sửa nhãn | NOT VERIFIED; code W3 được audit chưa có luồng lưu nhãn sửa |
| Nhãn sửa tách nhãn gốc mô hình và JSON export | NOT VERIFIED; chưa có contract W4 hoặc artifact sửa nhãn |
| Top predictions/needs_review/no_detection | Có code và tests W3; chưa nghiệm thu W4 |
| Hardware, CPU/GPU, batch size, resolution cho benchmark W4 | NOT FOUND tại commit đã audit |
| Cold/warm inference, thống kê latency/throughput W4 | NOT FOUND; smoke cold/warm W3 không thay thế benchmark W4 |
| Tách model load, preprocessing, MD và classifier | Chưa có benchmark W4 để kiểm tra |
| Detector bỏ sót và giới hạn end-to-end | No-detection fixture có; chưa có kết quả thực địa hay detector-recall audit W4 |
| Kiểm thử giao diện W4 thực tế | BLOCKED: chưa có code/báo cáo bàn giao W4 |

TV4 cần push code, contract/export nhãn sửa, log tốc độ với cấu hình thực và báo cáo W4. TV2 không sửa code TV4, không điều chỉnh ngưỡng demo, không coi điểm thấp là loài lạ, không gọi softmax là xác suất đã hiệu chỉnh. Chưa có kết luận PASS W4-04.
