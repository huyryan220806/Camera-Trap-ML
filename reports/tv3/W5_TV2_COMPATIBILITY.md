# TV3 — đồng bộ bàn giao với TV2, 29/10/2026

**Đã triển khai phần tương thích. Chưa huấn luyện DINO, chưa có approval W5.**
Người dùng đã nhắn TV2; chưa có phản hồi chốt cấu hình/ngân sách trong phiên này.
Không tự sửa trạng thái proposal thành APPROVED, không commit hoặc push.

## Nguồn đã kiểm tra

- TV1 `9abc9c5`: giữ comparison_v1; 1.665 ứng viên chưa training-ready.
- TV2 `3f76643d1bc395098d90105e67a9cf29c8fe3256`: protocol vẫn DRAFT, seed42 và
  quy tắc hòa là đề xuất; chưa nhận checkpoint DINO. Nguồn chính là
  [bàn giao TV2](https://github.com/huyryan220806/Camera-Trap-ML/blob/3f76643/docs/handoff_tv2_w5.md),
  [protocol](https://github.com/huyryan220806/Camera-Trap-ML/blob/3f76643/reports/tv2/W5_PROTOCOL.md),
  schemas và mã `src/evaluation/w5_validation.py` tại đúng commit này.

## Thay đổi TV3

- `pin` tạo protocol DRAFT cùng schema TV2. Trainer yêu cầu APPROVED, reviewer
  TV2/TV3 có nguồn xác nhận, seed/experiment nằm trong đăng ký và ngân sách,
  đúng metric/tie/dataset; config SHA gắn cả optimizer, epoch, batch và runtime.
  Thay đổi config cần đồng thuận mới. Code không xác thực danh tính reviewer;
  PR hoặc receipt thật vẫn cần kiểm tra bởi người nhận.
- `val_crops.jsonl` xuất ground_truth và class_scores đủ8, một dòng/crop.
  Gửi softmax thật tránh khác biệt FP32/FP64 khi tính lại từ logits. Bản
  `validation.json` gốc vẫn giữ cả logits và probabilities để kiểm tra reload.
- `val_images.jsonl` đủ ID/nhãn/prediction/vector8/crop_count/experiment/SHA.
- `handoff.json` thêm toàn bộ trường TV2 yêu cầu, metadata pretrained/head/
  pooling, class order, preprocessing, runtime, provenance/manifest hashes,
  bốn metric chưa làm tròn và artifact paths tương đối kèm SHA.
- Manifest gate kiểm tra thêm `train.jsonl`, `val.jsonl` cấp gốc theo hash
  frozen provenance để khớp bộ manifest mà TV2 nhận. Không thêm dữ liệu mới.
- `class_map.json` và `preprocessing.json` tách riêng; hash mã export vào
  binding để resume không dùng code bàn giao đã thay đổi.
- Reload giữ kiểm tra đầy đủ reference trước đó, thêm status, split, manifest
  SHA, test_inference_performed và hash bằng chứng. Handoff chỉ PASS khi tiến
  trình thành công và report khớp checkpoint/dataset; report thiếu/sai/FAIL
  không được chuyển thành PASS. Không nới dung sai.
- `scripts/audit_dino_tv2.py` tạo snapshot tối thiểu từ Git object TV2, giữ
  nguyên code/schema và B2 predictions. Không merge nhánh, sửa TV2 hoặc chạy
  B2 lại. Sau training gọi auditor để tính lại metric và paired outcomes đủ
  600 ảnh. Kết quả ARTIFACT_VERIFIED không phải review hoặc inference PASS.

## Kiểm tra

Toàn bộ **393/393 kiểm thử PASS**, gồm **16 kiểm thử DINO/tương thích TV2**,
không SKIP (65,811 giây). Lần đầu trong sandbox có 6 lỗi HTTP localhost do
WinError10013; chạy lại ngoài sandbox PASS, giữ cả hai log để truy vết.
Kiểm tra môi trường cơ bản PASS, result contracts 6/6 PASS, diff/whitespace
PASS. Summary có SHA code và bằng chứng tại
[`w5_evidence/compat_2026-10-29/summary.json`](w5_evidence/compat_2026-10-29/summary.json).

Kiểm thử tương thích dùng code auditor nguyên bản TV2, metadata validation
thật và **predictions/checkpoint/receipt DINO tổng hợp**. Những fixture này
được tạo trong thư mục tạm, không phải checkpoint hay kết quả DINO bàn giao.
Auditor chạy trong tiến trình riêng, kiểm tra schema, đủ600 ảnh/680 crop,
metric khớp và ghép cặp với B2 predictions TV2 đã công bố. Kiểm thử âm xác
nhận từ chối DRAFT, sai config/budget/tie, thiếu crop, sửa log/hash/manifest,
reload sai checkpoint hoặc thất bại. Test reload CLI dùng FakeBackbone và
reference tổng hợp để kiểm tra cả báo PASS/FAIL; không thay smoke model thật.

Lệnh kiểm thử có thể tái hiện:

```powershell
python -X utf8 -m unittest discover -s tests -p 'test_dino*.py' -v
```

Cross-branch tests cần Git object `3f76643`; nếu chưa có, chạy `git fetch origin`.
Trường hợp object thiếu, unittest ghi SKIP và không được gọi là đã kiểm tra
tương thích. Log kiểm tra lần này được lưu tại `w5_evidence/compat_2026-10-29/`.

## Còn chờ trước lượt chính thức

1. TV2 phản hồi về protocol/ngân sách; giữ đề xuất 1 lượt, seed42, tối đa50
   epoch, patience7, batch32 ảnh nguồn đến khi có quyết định khác.
2. Nhận weights pretrained hợp lệ, pin SHA/commit và smoke model thật; nếu
   chọn DINOv2 phải ghi rõ ID/cấu hình và thống nhất trước khi chạy.
3. Lưu phiên bản code/config được review, huấn luyện và reload thật.
4. Chạy audit TV2, bàn giao gói thật cho TV2/TV4, cập nhật báo cáo số thực.

Không dùng các test hoặc snapshot chuẩn bị sẵn làm bằng chứng đã có DINO.
