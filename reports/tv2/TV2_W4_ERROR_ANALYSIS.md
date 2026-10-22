# TV2 W4 Test error analysis

**PENDING OFFICIAL TEST RUN.** Chưa có prediction Test nên chưa xác định lớp Precision/Recall thấp, cặp nhầm lẫn, tỷ lệ lỗi hay ví dụ model sai trên Test. Không dùng lỗi Validation thay thế kết quả Test.

## Quan sát có bằng chứng trước Test

TV1 inventory cho biết 57 ảnh nhiều box, 70 ảnh có box dưới 1% diện tích ảnh, 171 ảnh có box cách mép <=1 px; các nhóm có thể giao nhau. Đây là cờ dữ liệu, không phải số lỗi mô hình hoặc nhãn sai. Test có cặp RGB trùng tại loc_0851: `d86f91b0-8c29-11eb-8c2e-000d3a74c7de` và `d86f91b6-8c29-11eb-94af-000d3a74c7de`; giữ nguyên cả hai. Xem [đối chiếu TV1](w4_evidence/tv1_inventory_audit.json) và [nguồn commit](w4_evidence/repository_audit.json).

Theo **Validation** TV3, Mang lớn/Nai khó và nhầm lẫn đáng chú ý; đây chỉ là bối cảnh Validation, không dự đoán kết quả Test. Giả thuyết ánh sáng đêm/góc nhìn cần kiểm tra ảnh hoặc metadata thực tế; không tự gán nguyên nhân cho ví dụ Test chưa inference.

## Phân tích sau official run

Evaluator xuất per-class errors/support, Precision/Recall/F1 và cặp nhầm lẫn từ CM, kèm image ID/true/predicted/softmax score/số crop cho mọi lỗi. Khi có run hợp lệ, đối chiếu với inventory nhiều box, box nhỏ/sát mép và metadata đủ chứng cứ; nếu trình bày ảnh phải ghi nguồn và trạng thái kiểm tra trực quan. Không đổi nhãn, bỏ mẫu, sửa model hoặc chọn threshold theo những lỗi này. Detector miss chỉ phân tích bằng kết quả end-to-end riêng của TV4.

## Giới hạn khoa học

- 600 ảnh không phải 600 quan sát độc lập: 495 chuỗi, 98 địa điểm và một cặp trùng RGB. Mỗi lớp 75 ảnh; mỗi lỗi đổi recall lớp khoảng 1.33 điểm phần trăm. Không mặc định crop/ảnh độc lập khi ước lượng độ bất định.
- Dữ liệu cân bằng lớp không đại diện tần suất động vật tự nhiên; bối cảnh camera có thể tập trung theo địa điểm.
- Closed-set 8 lớp; không suy rộng sang loài lạ. Softmax chưa calibration và điểm thấp không chứng minh loài mới.
- Ground-truth-box classification khác MegaDetector+classifier demo. Một số phiên bản MegaDetector đã dùng SWG trong nguồn train; SWG không tự là detector test độc lập.
- Số ảnh/chuỗi không phải số cá thể. Không kết luận nhãn gốc sai khi chưa thẩm định loài.
