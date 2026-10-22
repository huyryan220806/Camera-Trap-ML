# TV2 review TV3 W4-03

Kết luận: **PENDING FIX** tại `65b99b9def6a147abe6a4d436c18a067f3f37dc4`. TV2 không sửa nhánh TV3 và không nghiệm thu thay TV1.

## Bằng chứng xác minh được

- Code thật: `scripts/train_b3.py`, `scripts/error_analysis.py`, `configs/b3_class_weighted.json`, `tests/test_tv3_w4.py`. Xem [index SHA và commit](w4_evidence/repository_audit.json).
- Sáu test W4 của TV3 chạy đạt trong thư mục review độc lập: [log](w4_evidence/tv3_w4_tests.txt). Đây là fixture/synthetic smoke; không train lại B3 chính thức, không dùng ảnh SWG và không phải bằng chứng tái lập checkpoint thật.
- B3 gọi loader mặc định `splits=['train','val']`, tính trọng số từ Train và chọn best epoch bằng image-level Validation Macro-F1. Code không yêu cầu Test trong vòng train; bằng chứng này không thay thế provenance của run thực tế.
- Cả hai ma trận Validation có 600 ảnh, support 75/lớp, đúng thứ tự 0–7. Tính lại từ số đếm nguyên: B2 F1=0.7454765175212033, P=0.7484190016985997, R=0.7466666666666666, Accuracy=0.7466666666666667; B3 F1=0.7410465262846234, P=0.7406316201298413, R=0.7433333333333333, Accuracy=0.7433333333333333. Khớp số công bố khi làm tròn 4 chữ số. [Audit metric](w4_evidence/validation_matrix_audit.json).
- TV3 quyết định giữ B2; commit quyết định có author time 22/10/2026 19:30:11 +07:00. TV2 chưa chạy Test. Không dùng Test để chọn lại B3.

## Trọng số crop và trọng số ảnh

Train có 350 ảnh nguồn/lớp. Số crop theo ID 0–7 là 359, 350, 421, 360, 352, 353, 450, 480. Code tính `u_c=3125/(8*n_crop_c)`, rồi `w_c=u_c/mean(u)`; trọng số tương ứng khoảng 1.072638, 1.100220, 0.914673, 1.069659, 1.093969, 1.090870, 0.855727, 0.802244, khớp bảng TV3.

Loss B3 trung bình CE có trọng số trong từng ảnh, rồi trung bình qua ảnh. B2 đã trung bình crop theo ảnh nên tổng trọng số nền mỗi lớp là 350. Áp dụng thêm nghịch đảo số crop làm thay đổi tầm quan trọng của các lớp vốn cân bằng ở cấp ảnh; đây không phải sửa mất cân bằng ở cấp ảnh. Nếu tính nghịch đảo theo ảnh nguồn thì tất cả trọng số bằng 1. Chuẩn hóa mean=1 có trong code, cần nêu rõ khi tái lập.

Mô tả bầy đàn và suy giảm do giảm trọng số là giả thuyết diễn giải, chưa chứng minh quan hệ nhân quả bằng một run/seed. Không có kiểm định theo cụm hay nhiều seed. Nguồn protocol gốc chỉ nêu inverse frequency; lựa chọn basis='crop' và margin +0.005 chưa có bằng chứng đồng thuận trước thử nghiệm. B3 thấp hơn B2 dưới cả quy tắc cải thiện dương và margin +0.005 nên không cần chọn lại mô hình.

## Điều kiện còn thiếu

1. **NOT FOUND**: `outputs/b3_class_weighted/b3_run01/validation_comparison.json`, `train_log.jsonl`, `best_model.pt` trong Git tree commit đã audit. Không yêu cầu đưa weights vào Git: TV3 cần bàn giao weights ngoài Git với URL/đường dẫn dùng được, SHA-256, byte size và artifact JSON/log nhỏ.
2. Báo cáo error analysis B3 là artifact thứ cấp từ checkpoint được khai báo bằng đường dẫn máy TV3, chưa chứa SHA checkpoint. Chưa kiểm tra được epoch 14, reload thật, config/run provenance hoặc đối chiếu đầy đủ prediction ID với cùng Validation population. Cùng support không tự chứng minh cùng 600 ID.
3. `preflight_hash_check=false` trong config B3: manifest lock có hash nhưng chưa chứng minh ảnh Train/Val của run B3 được hash trước khi train. Không đổi config hay train lại để hợp thức hóa run cũ; cần bằng chứng run gốc và công khai giới hạn.
4. Bảng TV3 dùng Macro-Precision B1 0.5688; artifact gốc TV2 là **0.5748610369**. Đây là sai lệch báo cáo, không làm đổi thứ tự B2/B3.
5. Khuyến nghị review score 0.50 trong báo cáo TV3 chưa có mục tiêu/tie rule/chứng cứ chọn ngưỡng Validation; TV2 không khóa nó làm ngưỡng tối ưu. Demo 0.70 cũng là giá trị minh họa chưa tối ưu.

TV3 cần hoàn tất nguồn artifact và provenance để TV2 chốt review; hiện chưa đủ điều kiện đóng final lock. Những kết quả xác minh được vẫn được giữ nguyên, không sửa số B3.
