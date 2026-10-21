# TV2 review TV3 W3 B2

**Remote fetch:** 18/10/2026.

**Commit mới nhất:** `c01a75141bb8350c8a38a28cfc9b44a3f3ad12ba`.

**Kết luận:** **CODE PARTIAL – OFFICIAL TRAINING BLOCKED – FOUR P1 FIXES REQUIRED**.

Review chỉ đọc từ `origin/feat/crop-classifier`; không checkout, sửa hoặc push
nhánh TV3; không mở/copy JSONL test. Remote không có commit mới sau lần review
trước.

## Bằng chứng hiện có

- 23/23 test PASS trong snapshot code/test cô lập tại đúng commit trên.
- Có model ResNet18, loader crop, training loop, checkpoint helpers và đánh giá
  cấp ảnh bằng trung bình xác suất crop.
- Cấu hình chính khớp phần lớn protocol: ImageNet, full fine-tune, không dropout,
  seed 42, SGD `0.001/0.9/0.0001`, StepLR `10/0.1`, batch 32, tối đa 50 epoch,
  patience 7, FP32 và `drop_last=false`.
- Nhánh không có official B2 checkpoint, training log, validation metrics,
  confusion matrix, learning curves, reload evidence hoặc báo cáo W3 B2.
- Vì vậy test PASS chỉ chứng minh các trường hợp đã được test, không chứng minh
  model B2 đã được huấn luyện hoặc đủ điều kiện so sánh.

## Bốn lỗi chặn còn tồn tại

1. **P1 – Source-image SHA-256 preflight bị tắt.**
   `configs/b2_crop_classifier.json:33` đặt `preflight_hash_check=false`.
   Dataset có khả năng kiểm hash nhưng official config không bật nó. TV3 cần bật
   fail-closed và thêm test xác nhận official config không thể tắt kiểm hash.

2. **P1 – Loss chưa cân bằng parent image trên toàn epoch.**
   `scripts/train_b2.py:186-218` chỉ gom crop theo `image_id` trong batch hiện
   tại, còn `src/data/b2_dataset.py:317` shuffle từng crop. Crop của một parent
   có thể nằm ở nhiều batch nên parent đó được tính nhiều lần và trọng số phụ
   thuộc thành phần từng batch. TV3 cần sampler/batch giữ trọn parent hoặc một
   phép weighting chứng minh tương đương toàn epoch, kèm regression test chia
   crop cùng parent qua ít nhất hai batch.

3. **P1 – Official output không bất biến.**
   `scripts/train_b2.py:323` tạo output bằng `exist_ok=True`; dòng 363 mở log
   bằng chế độ `w`, còn checkpoint/report ghi cùng tên. Chạy lại có thể thay thế
   artifact cũ. TV3 cần run ID riêng và fail nếu run/artifact đã tồn tại.

4. **P1 – Thiếu fresh-process checkpoint reload.**
   `src/models/b2_classifier.py:106` có `load_checkpoint`, nhưng official training
   không gọi validator ở tiến trình mới để kiểm hash, class mapping, provenance,
   prediction và metric. Unit test save/load model không thay thế official reload.

## Test gaps và điều kiện review lại

23 test hiện tại không có regression cho official hash config, crop một parent
bị chia qua nhiều batch, từ chối output tồn tại và fresh-process official reload.
TV3 cần push commit sửa bốn điểm, chạy official B2 trên đúng `comparison_v1`, sau
đó bàn giao checkpoint, hash, log, metric cấp ảnh, plots và reload evidence.

Bằng chứng: [latest test log](w3_evidence/continuation_04/tv3_tests_latest.txt) và
[audit lần trước](w3_evidence/continuation_03/tv3_c01a751_review.json).
