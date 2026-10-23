# TV2 W4 error analysis — tiếp nối 23/10/2026

**PENDING OFFICIAL TEST RUN**. Chưa có prediction Test nên không có lớp Test Precision/Recall thấp, cặp nhầm lẫn hay ví dụ model sai trên Test. Không suy diễn từ Validation hoặc tạo ví dụ Test giả.

## Phát hiện thật thuộc Validation B3

Hai ID bất đồng reference là `cc293eb4-8c29-11eb-81b9-000d3a74c7de` (GT sambar; reference wild_pig, local CPU/CUDA sambar) và `cbdf50b3-8c29-11eb-a63b-000d3a74c7de` (GT common_palm_civet; reference/local CUDA đúng, CPU annamite_striped_rabbit). CPU crop score ở ảnh thứ hai là rabbit0.3223070502 vs civet0.3222738504: gap khoảng0.0000332. Đây là **Validation diagnostic**, không phải kết quả Test và không dùng để chọn threshold.

Các ID, nhãn, confidence, vector và môi trường có trong [runtime comparison](w4_evidence/continuation_01/b3_runtime_comparison.json). Input tensor của hai ảnh giống hệt giữa hai môi trường; quan sát có runtime sensitivity nhưng chưa giải thích đầy đủ reference gốc. Không khẳng định label gốc sai, checkpoint bị sửa hay nguyên nhân ảnh tối khi chưa có chứng cứ. Không sửa dữ liệu/weights.

## Dữ liệu Test và kế hoạch phân tích sau official run

Tái sử dụng TV1: 57 ảnh nhiều box, 70 ảnh có box<1% diện tích, 171 ảnh box sát mép<=1px; nhóm có thể giao nhau và không phải số ảnh sai. Giữ cặp RGB duplicate cùng Test tại loc_0851 (`d86f91b0-8c29-11eb-8c2e-000d3a74c7de`, `d86f91b6-8c29-11eb-94af-000d3a74c7de`). Đây là data QA, không model error analysis Test.

Khi có official predictions hợp lệ, dùng evaluator đã có để tính P/R/F1 từng lớp, errors/support, directed confusion pairs, multi-crop/small-box/edge subgroups và ví dụ ID/true/predicted/score/source. Ảnh đêm/góc nhìn khó chỉ kết luận nếu metadata/kiểm tra trực quan hỗ trợ; detector miss cần kết quả MegaDetector end-to-end riêng của TV4. Không đổi model/threshold/labels theo Test.

## Giới hạn

600 ảnh không độc lập hoàn toàn:495 chuỗi/98 địa điểm, 75 ảnh/lớp, một cặp RGB trùng; mỗi lỗi đổi Recall lớp khoảng1.33 điểm phần trăm. Pilot cân bằng không phản ánh tần suất tự nhiên. Chỉ closed-set8 lớp, GT-box classification khác demo MegaDetector; một số phiên bản detector có SWG trong nguồn train. Softmax chưa calibration, confidence thấp không chứng minh loài lạ; số ảnh/chuỗi không phải số cá thể.
