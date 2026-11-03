# TV3 tuần 5 — kết quả kiểm tra ngày 02/11/2026

**Đạt bàn giao DINOv3 linear probe trong phạm vi W5.** Commit `5734d38c3af2fe052cf04c4c33d940e8f186306d`, nhánh `feat/crop-classifier`. Không phát hiện lỗi kỹ thuật đang chặn nhận checkpoint. Đây là biên bản TV1, không thay approval GitHub của thành viên khác.

## Đã xác minh

- ZIP thật nhận tại `reports/tv3_w5/DINOv3_LP_run01_handoff_2026-11-02.zip`, 81.225.769 bytes, SHA `9e969585cd7c7355733976b37bda912dd8deb2667d096ddf9193d62bbc276301`. CRC, đường dẫn và 27/27 payload PASS.
- Best checkpoint 86.851.958 bytes, SHA `acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3`. Best/last nạp an toàn; tensors hữu hạn, head 8×384; class map/config/binding/log/validation khớp.
- Best epoch 9, dừng epoch 16, patience 7; learning rate theo cosine50 và lựa chọn macro-F1 đúng hồ sơ. Best head trong last bằng checkpoint best.
- Source ba file pipeline nguyên byte so với training commit `aa64fd7`; protocol đã khóa giống TV2. Dữ liệu `comparison_v1` không đổi; không lấy ứng viên metadata chưa qua kiểm định để train.
- 16/16 tests mới PASS, gồm resume epoch/cache, kiểm protocol và tương thích evaluator TV2. Đây là kiểm thử tổng hợp, không huấn luyện lại DINO thật.
- Đủ 600 ảnh/680 crop, accuracy **84,50%**, macro-F1 **84,44%**. Logits/softmax, mean vector, nhãn, CM, metric và đối chứng B2 khớp khi kiểm lại từ artifact.
- TV2 đã công bố fresh-process real replay exact; TV1 đối chiếu toàn bộ kết quả đó với TV3. Native/adapter TV4 dùng checkpoint này tại máy TV1 cũng exact trên fixture, và MD+DINO thật chạy qua browser.

## Việc cần chốt tài liệu

Bổ sung phần trạng thái hiện tại trong handoff/progress và `reports/tv3/TV3_W5.md`: TV2 đã kiểm độc lập ở `df31029`, TV4 đã tích hợp ở `8d4a255`, và TV1 có biên bản này. Handoff vẫn mở bằng hướng dẫn chuẩn bị ngày 30/10; nên đặt đường dẫn gói cuối/nghiệm thu ở đầu để người nhận không tưởng cần pin/train lại. Giữ mục chuẩn bị cũ thành lịch sử.

**Không coi chưa đạt 88% là chưa hoàn thành W5.** Chưa có test DINO độc lập, chỉ một seed; không suy ra ưu thế ổn định hoặc SOTA. B3 cũ vẫn UNRESOLVED, không đổi tên DINO thành B3 đã sửa. Tuần 6 tập trung gói model, hướng dẫn máy sạch và nội dung bảo vệ; mọi lượt train mới cần kế hoạch riêng.

[ZIP intake](evidence/zip_intake.json) · [tests](evidence/tv3_tests.txt) · [audit độc lập](evidence/independent_audit.json) · [native/adapter](evidence/native_adapter_equivalence.json) · [biên bản chung](REPORT.md).
