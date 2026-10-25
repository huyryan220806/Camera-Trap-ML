# TV3 W4 - Hoàn thiện sau review ngày 25/10/2026

Đã sửa theo ủy quyền của TV1: đối chiếu reload theo ID/nhãn dự đoán, ma trận và
metrics; lưu đầy đủ bằng chứng riêng và báo FAIL nếu không khớp. Không dùng
dung sai F1 0,01. Giữ checkpoint để điều tra, không ghi đè tham chiếu.

Công cụ phân tích lỗi bắt buộc kiểm tra SHA checkpoint B2/B3 đã bàn giao,
provenance và manifest train/validation/class map đã khóa, metadata và SHA ảnh
validation. Từ chối tắt kiểm tra và ghi đè; attempt mới có file riêng. Lưu mọi
dự đoán chưa làm tròn và runtime. Không mở tập Test trong công cụ này.

Mẫu nạp B2 dùng B2CropClassifier, không dùng ResNet18 trần. Đã sửa lời giải thích
sai lệch B3: nguyên nhân gốc chưa được chứng minh, log/runtime/training commit
gốc còn thiếu. B3 vẫn là exploratory, UNRESOLVED và ngoài Test.

Chạy mới B2 và B3 trên 600 ảnh validation / 680 crop mỗi mô hình, CPU 4 threads:
B2 vẫn 152 lỗi, CM khớp kiểm định PASS; B3 vẫn 154 lỗi và CM khớp chẩn đoán CPU
ngày 23/10, không khớp hoàn toàn báo cáo tham chiếu gốc. Không thay checkpoint,
không huấn luyện lại, không dùng Test để thay lựa chọn B2.

Kết quả kiểm định mới trên máy TV1: outputs/review_w4_2026-10-25/fixed_validation/.
Các báo cáo error_analysis_b2/b3 gốc và log B2 được giữ nguyên trong Git.
Toàn bộ 109/109 kiểm thử PASS (25,391 giây). Các sửa đổi kỹ thuật đã được kiểm tra;
TV4 tiếp tục với B2. Điều này không phải
nghiệm thu tính tái lập chính xác của B3 hoặc tuyên bố B3 đã PASS.
