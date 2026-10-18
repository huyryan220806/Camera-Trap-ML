# TV2 review TV3 W3 B2

**Commit:** `c01a75141bb8350c8a38a28cfc9b44a3f3ad12ba`

**Cách review:** read-only từ `origin/feat/crop-classifier`; không checkout/push nhánh
TV3; không mở hoặc copy JSONL test.

**Tests:** 23/23 PASS trong snapshot code/test cô lập.

**Kết luận:** **PENDING TV3 FIX / REVIEW**.

## Các phần đã sửa đúng

- Đường dẫn `data/processed/comparison_v1`.
- ResNet18 ImageNet, full fine-tune, no dropout, FP32.
- SGD `0.001/0.9/0.0001`, StepLR `10/0.1`, 50 epoch, patience 7, batch 32.
- `drop_last=false`; aggregation validation bằng mean probability theo parent image.
- Gate hash provenance, kiểm manifest chặt hơn, smoke isolation.
- Theo dõi `best_epoch` và last metrics đúng hơn bản cũ.

## Blocking findings

1. **P1 – Source image hash preflight bị tắt.**
   `configs/b2_crop_classifier.json:33` đặt `preflight_hash_check=false`, nên official
   run không thực thi khả năng hash mà dataset đã hỗ trợ.

2. **P1 – Loss chưa cân bằng parent image trên toàn epoch.**
   `scripts/train_b2.py:186-218` chỉ gom crop theo `image_id` trong batch hiện tại,
   trong khi `src/data/b2_dataset.py:317` shuffle từng crop. Khi crop của cùng một ảnh
   nằm ở nhiều batch, ảnh đó có thể đóng góp nhiều lần và trọng số còn phụ thuộc số
   parent khác trong từng batch. Cần sampler/batch construction giữ đầy đủ crop của
   mỗi parent hoặc công thức weighting chứng minh tương đương trên toàn epoch.

3. **P1 – Official run có thể bị ghi đè.**
   `scripts/train_b2.py:323` dùng `mkdir(..., exist_ok=True)` và dòng 363 mở log bằng
   chế độ `w`; checkpoint/report cùng thư mục cũng bị thay thế. Cần run ID mới và
   fail-closed nếu bất kỳ marker/artifact nào đã tồn tại.

4. **P1 – Chưa có fresh-process checkpoint reload.**
   `src/models/b2_classifier.py:106` có `load_checkpoint`, nhưng official training
   không gọi lại model mới để kiểm hash, mapping, provenance, predictions và metric.

## Test gap

23 test hiện tại PASS nhưng test loss chỉ đặt mọi crop của parent trong cùng một
batch. Cần thêm test chia crop của một parent qua hai batch để phát hiện finding 2,
test config official bắt buộc hash, test từ chối output tồn tại và test fresh reload.

Bằng chứng máy đọc được: [tv3_c01a751_review.json](w3_evidence/continuation_03/tv3_c01a751_review.json),
[test log](w3_evidence/continuation_03/tv3_tests.txt).
