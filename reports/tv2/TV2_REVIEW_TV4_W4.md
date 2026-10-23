# TV2 review TV4 W4-04 — 23/10/2026

**W4-04 HANDOFF NOT VERIFIED.** Fetch thực tế xác nhận `origin/feat/demo` vẫn ở `254b40eab77b849647a2291aa0257c1b161b4da2`, không có W4/Week4 paths mới trong tree. [Audit](w4_evidence/continuation_02/pre_test_integrity.json). Không lấy W3 thay bằng chứng nghiệm thu W4.

TV4 cần bàn giao màn hình duyệt lại/sửa nhãn; JSON và CSV export phân biệt nhãn người sửa với prediction gốc; test nhiều box, confidence thấp, detector bỏ sót/no_detection và cache/không giữ prediction cũ. Cần benchmark W4 nêu hardware, CPU/GPU, batch size, resolution, cold/warm, phân phối latency và tách load/preprocess/MegaDetector/classifier. Chưa có artifact W4 để xác minh các mục này.

Code/fixture W3 review trước vẫn là evidence lịch sử; regression TV2 tiếp tục kiểm tra contract và adapter. Không sửa code TV4, không tự xác nhận UI acceptance. Confidence thấp không chứng minh loài lạ và softmax chưa calibration.

Handoff TV4 là cross-review riêng, không có phụ thuộc bắt buộc từ evaluator B2 ground-truth crop đến UI/detector TV4. Thiếu W4-04 không chặn official Test B2. TV1 nghiệm thu W4-02 sau khi sản phẩm TV2 hoàn thành.
