# Kiểm tra tuần 5 — TV2, TV3 và TV4

Ngày 02/11/2026, theo yêu cầu TV1. **Đạt kiểm tra kỹ thuật tuần 5 trong phạm vi đã cập nhật. Không phát hiện lỗi chức năng hoặc sai số liệu đang chặn tích hợp.** Chưa push báo cáo này, gửi approval GitHub hoặc merge nhánh.

## Kết luận từng thành viên

| Thành viên | Commit đã kiểm tra | Kết luận | Bằng chứng mới tại máy TV1 |
| --- | --- | --- | --- |
| TV2 | `df31029c2dfa3b87e4efd1b1f210babd89c60cbd` | Đạt phần đánh giá/đối chứng và chương thực nghiệm | 32/32 tests; chạy evaluator trên gói DINO thật, tính lại metric và đối chiếu B2 |
| TV3 | `5734d38c3af2fe052cf04c4c33d940e8f186306d` | Đạt gói DINO linear probe, checkpoint và bằng chứng tái lập | 16/16 tests; ZIP 27/27 payload khớp; checkpoint/config/log/dự đoán và source lock khớp |
| TV4 | `8d4a255881c445b5528e69cd9d07a503c02ec11d` | Đạt adapter, UI, lô nhỏ và CSV trong phạm vi W5 | 47/47 tests; native/adapter logits giống hệt; browser thật MD+DINO và B2, lưu/xuất/CSV/resize PASS |

Biên bản riêng để gửi thành viên: [TV2](TV2.md), [TV3](TV3.md), [TV4](TV4.md).

## Kết quả mô hình đã đối chiếu

Đủ **600 ảnh validation / 680 GT crop**, 8 lớp, 75 ảnh/lớp; cùng image ID và nhãn của `comparison_v1`. Mỗi ảnh lấy trung bình đầy đủ vector softmax của các crop rồi argmax; không loại ảnh điểm thấp để tính lại accuracy.

| Chỉ số validation cấp ảnh | B2 | DINOv3_LP_run01 |
| --- | ---: | ---: |
| Đúng / tổng | 448/600 | 507/600 |
| Accuracy | 74,67% | **84,50%** |
| Macro-F1 | 74,55% | **84,44%** |

DINO sửa được 95 ảnh B2 sai, đồng thời sai 36 ảnh B2 đúng: tăng ròng 59 ảnh, tương ứng **+9,83 điểm phần trăm accuracy**. Có 412 ảnh cùng đúng và 57 ảnh cùng sai. F1 trung bình tăng không có nghĩa mọi lớp đều cải thiện recall: masked palm civet đúng giảm 58 xuống 56/75; nhầm lẫn giữa hai lớp civet tăng 7 lên 13 ảnh.

**Chưa đạt mục tiêu 88%.** Đây là kết quả validation với GT box, một seed, một lượt đăng ký; không phải accuracy end-to-end của MegaDetector + classifier, không chứng minh SOTA trên SWG hoặc hiệu quả trên test độc lập. Test B2 tuần 4 giữ nguyên như mốc lịch sử. Chưa có test mới đủ điều kiện, và không dùng 1.665 ứng viên metadata để huấn luyện.

## Phạm vi đã thực sự chạy

- Fetch và chốt ba đầu nhánh; dữ liệu khóa và hồ sơ chọn B2/Test tuần 4 không đổi trên cả ba nhánh.
- Kiểm CRC, đường dẫn ZIP, SHA/kích thước và 27 payload; nạp best/last bằng `weights_only=True`, kiểm tensors hữu hạn, head 8×384, config/class map/binding, best epoch 9, dừng epoch 16 và patience 7. Đối chiếu lịch learning rate và source với training commit `aa64fd7`.
- Tính lại từ đủ 680 crop và 600 dự đoán; kiểm ánh xạ nhãn, mean vector, argmax, support/CM, metric và cặp đúng/sai với B2. Chạy lại evaluator nguyên bản của TV2 trên checkpoint thật: `ARTIFACT_VERIFIED`.
- Đối chiếu toàn bộ dự đoán/metric trong bằng chứng fresh-process replay của TV2 với TV3: bằng nhau. **TV1 không forward lại toàn bộ 600 validation trong lượt này**; phân biệt kiểm bằng chứng đó với native/adapter và browser inference mới thực hiện tại TV1.
- Native/adapter CPU: RGB, ảnh xám, ảnh nhỏ, ảnh dọc, batch 1/3/8+1; logits exact, delta 0, top 3 riêng từng box. Gate thiếu/sai checkpoint và sai checkout kiến trúc từ chối cả sau khi cache warm.
- Browser Edge: MD+DINO thật trên ảnh train, B2 thật vẫn chạy được và vẫn mặc định; mock nhiều box, no detection, detector error; JPEG hỏng dùng decoder thật. Lưu/reload/xuất JSON, original bất biến, revision cũ trả 409, bản nháp từng ảnh, CSV chỉ lấy bản đã lưu, UTF-8/quoting/chống công thức, tên trùng, giới hạn 10 ảnh và stop/resume đều PASS.
- Kiểm CSV bằng parser độc lập: lô good/corrupt/good có 5 dòng, giữ dòng lỗi; trường hợp no detection có 1 dòng, giữ outcome `detector_miss` đã lưu. Đây là thao tác QA giả lập, không phải xác nhận chuyên gia về ảnh động vật.
- 1440×1100, 390×844 và 320×740: không tràn ngang, box trong ảnh, không lỗi JavaScript. Nút export mobile đã có accessible name: lỗi `UI-A11Y-01` trước đây đã được retest PASS.
- Dựng cây gộp riêng từ bốn nhánh, không cập nhật branch: không conflict; **440/440 tests PASS**, 71,972 giây. Môi trường CPU cơ bản và 6 fixture JSON PASS; JS syntax và `git diff --check` phần implementation PASS.

Kiểm whitespace trên toàn bộ lịch sử evidence còn báo xuống dòng CRLF/khoảng trắng trong log thô. Không sửa byte của hồ sơ đã gắn SHA chỉ để làm sạch diff; kết luận implementation ở trên không tuyên bố mọi log lịch sử đều sạch whitespace.

## Còn gì trước công bố và tuần 6?

1. **Đồng bộ trạng thái tài liệu:** TV2 còn ghi chờ adapter/UI, TV3 còn ghi chờ TV2/TV4. Bổ sung liên kết đến kiểm tra mới và trạng thái hiện tại; giữ các mục lịch sử rõ ngày. Đây là việc tài liệu, không phải yêu cầu train lại.
2. **Quyết định tích hợp:** về kỹ thuật có thể gộp các nhánh đã kiểm tra. [PR #8](https://github.com/huyryan220806/Camera-Trap-ML/pull/8) hiện OPEN, head `8d4a255`, GitHub báo mergeable. Chưa có APPROVED review ở head này trong lần đọc API. Biên bản này là kiểm tra của TV1, không giả chữ ký hay approval của TV2.
3. **Đóng gói tuần 6:** thử cài máy sạch, cách cung cấp weights ngoài Git, video dự phòng và gói nộp. Adapter DINO hiện CPU; loader cần Git có training commit và checkout kiến trúc đúng pin. GPU selector không phải tính năng đã bàn giao. Queue/bản nháp ở RAM của tab, cần xuất trước khi đóng/reload; giới hạn đã ghi trong hướng dẫn.
4. **Diễn giải tốc độ:** TV4 đã đo và ghi CPU/batch/cold/warm. Số mẫu ít, có khác biệt thread khi cold; đây là smoke timing, chưa là benchmark kiểm soát hoặc cam kết latency. Không dùng số đo của B2 hay GPU validation để thay tốc độ DINO demo.

## Bằng chứng và tiếp tục

[Tóm tắt kiểm tra](evidence/summary.json) · [audit độc lập](evidence/independent_audit.json) · [tests bản kết hợp](evidence/combined_tests.txt) · [native/adapter](evidence/native_adapter_equivalence.json) · [browser](evidence/browser_verification.json) · [CSV/no-box/B2](evidence/extra_ui_verification.json) · [cây gộp thử](evidence/merge_preview.json) · [index SHA](evidence/index.json).

Snapshot, script kiểm độc lập, screenshots, các attempt môi trường và journal QA giữ local ở `outputs/review_w5_2026-11-02/`. Không đưa ZIP/checkpoint/ảnh vào gói báo cáo Git. Hai lượt browser đầu lỗi do cách bố trí junction trong snapshot; đã dùng bản copy riêng trong snapshot rồi kiểm lại PASS, không sửa code TV4 để vượt gate đường dẫn. Xem [progress](../../docs/progress_review_w5_2026-11-02.md) nếu bị gián đoạn.
