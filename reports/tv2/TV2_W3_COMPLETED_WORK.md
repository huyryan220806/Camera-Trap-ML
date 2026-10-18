# CÔNG VIỆC ĐÃ HOÀN THÀNH TUẦN 3 — THÀNH VIÊN 2

## Cập nhật CONTINUATION_02 – 18/10/2026

Trạng thái mới nhất: **W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**. TV1 `7e9b1949f10126fbcfa83fa12baeca488b6aeab3` đã phát hành;
provenance/native adapter và full train/val preflight PASS; 3.400 ảnh đã kiểm byte/pixel
hash/decode. Protocol đã được người dùng xác nhận cụ thể cho nhóm. CUDA batch32 smoke
PASS trong venv riêng; 87/87 regression PASS. Chưa có budget/window và official
environment freeze, chưa train/validation/checkpoint B1 thật. TV3 vẫn d08eba7 cần sửa.
Xem [báo cáo mới](TV2_W3_CONTINUATION_02_REPORT.md) và [README bàn giao](README_W3_HANDOFF_TEMP.md).
Các phần bên dưới giữ làm lịch sử; các kết luận cũ “TV1 chưa push”, “chưa có cache”,
“chưa thống nhất thông số” không còn là trạng thái hiện tại.

**Ngày cập nhật:** 16/10/2026

**Nhánh:** `feat/baseline`

**Commit triển khai P1:** `bf9aae404286a71ba6e912ce47f323bdcf53052d`

**Trạng thái:** **W3-02 CODE READY — OFFICIAL TRAINING BLOCKED**

**Cập nhật continuation 01:** đã kiểm chứng lại 78/78 test và smoke/reload;
P1 **VERIFIED LOCALLY**, chưa được reviewer nghiệm thu trên bundle thật.
Máy có RTX4060 Laptop 8188MiB nhưng runtime PyTorch hiện CPU-only. README bàn
giao mới: [README_W3_HANDOFF_TEMP.md](README_W3_HANDOFF_TEMP.md). Snapshot mới
`LOCAL_REVIEW_RESULTS/W3/CONTINUATION_01/` giữ riêng bản sao và hash; số 19 file
bên dưới là gói trước continuation, không bị ghi đè. TV1/TV3 remote không đổi.

## 1. Pipeline B1 đã hoàn thành

- Xây dựng mô hình B1 bằng ResNet18 pretrained ImageNet-1K.
- Fine-tune toàn bộ backbone và classifier; không khởi tạo tiếp từ B0.
- Hoàn thiện training loop, validation, early stopping và lựa chọn checkpoint
  theo validation macro-F1.
- Ghi log loss, accuracy, macro-precision, macro-recall, macro-F1, learning
  rate, thời gian và peak GPU memory.
- Tạo artifact validation, per-class metrics, confusion matrix và learning
  curves khi có lượt chạy chính thức.
- Bảo vệ run đã tồn tại, ghi trạng thái lỗi/interruption và không ghi đè kết
  quả cũ.
- Hoàn thiện kiểm tra checkpoint hash, provenance và fresh-model reload.

Các file chính:

- `configs/b1.yaml`
- `src/models/b1.py`
- `src/training/b1.py`
- `src/training/b1_gate.py`
- `scripts/train_b1.py`
- `scripts/validate_b1.py`
- `tests/test_b1.py`

## 2. Sửa gate theo review P1

Gate đã được sửa để tương thích với hợp đồng `comparison_v1` được mô tả trong
review ngày 16/10/2026:

- B1 đọc projection một dòng/ảnh với `sample_id`, `image_id`,
  `input_type=full_image` và `sample_weight=1`.
- Không yêu cầu B1 view phải lặp lại toàn bộ `boxes` hoặc giống nguyên dict của
  manifest ảnh nguồn.
- Đối chiếu các trường provenance có ý nghĩa giữa B1 view và nguồn: image ID,
  split, class, label và các trường nguồn tùy chọn nếu có.
- B2 chấp nhận **nhiều crop trên cùng một ảnh**, tương ứng với mọi box hợp lệ
  cùng loài.
- B2 dùng đặc tả `bbox_xyxy` để crop on-the-fly từ ảnh nguồn; không yêu cầu JPEG
  crop, `file_path` hoặc hash riêng của crop.
- Kiểm tra `crop_id` và `annotation_id` duy nhất, mapping box đầy đủ, parent IDs
  B1/B2 giống nhau, nhãn/split/URL/hash ảnh nguồn đúng.
- Kiểm tra `sample_weight = 1 / số crop của ảnh` để cân bằng loss cấp ảnh.
- Đơn vị so sánh B1/B2 là ảnh nguồn; dự đoán B2 được tổng hợp bằng trung bình
  xác suất của các crop thuộc cùng ảnh.

## 3. Kiểm thử đã hoàn thành

- Toàn bộ test repository: **78/78 PASS**.
- Test W2 được giữ nguyên: **52**.
- Test B1: **26**.
- FAIL: **0**.
- SKIPPED: **0**.
- Synthetic CPU smoke: **PASS**.
- Forward, backward, gradient toàn mạng và BatchNorm: **PASS**.
- Optimizer step và checkpoint save/load: **PASS**.
- Fresh-model reload: **PASS**.
- Sai khác macro-F1, precision, recall, accuracy và logits sau reload: **0**.
- Không ghi đè B0 hoặc run đã tồn tại.
- Không mở manifest hoặc ảnh test.

Các trường hợp mới được kiểm thử:

- Một ảnh có hai box hợp lệ được gate chấp nhận.
- Thiếu một crop bị từ chối.
- Trùng crop ID hoặc annotation ID bị từ chối.
- Đổi nhãn, class, split, tọa độ hoặc mapping nguồn bị từ chối.
- Đổi SHA-256 ảnh nguồn bị từ chối.
- Sai `input_type` hoặc `sample_weight` bị từ chối.

Bằng chứng: `reports/tv2/w3_evidence/tests_after_p1.txt`.

## 4. Kiểm tra chéo TV1 và TV3

### TV1 — W3-01

- Đã fetch và kiểm tra toàn bộ remote heads.
- `feat/metadata-split` hiện bằng main.
- Chưa tìm thấy `comparison_v1`, freeze receipt, script freeze hoặc handoff
  W3-01 trên remote.
- Đã xác minh metadata W2 v2 và hashes hiện có mà không mở dữ liệu test.
- Đã chuẩn bị adapter và fixture theo schema review để chạy preflight ngay khi
  TV1 push bundle thật.

### TV3 — W3-03

- Đã kiểm tra commit `d08eba7fffbfb6ecc813de8522fb4d58cd8ed904`.
- Chạy độc lập snapshot tests: **9/9 PASS**.
- Official B2 gate dừng đúng vì thiếu `comparison_v1`.
- Đã phát hiện và ghi nhận các vấn đề về đường dẫn dữ liệu, preflight hash,
  early stopping, best epoch/checkpoint, run immutability, reload và protocol.
- Kết luận hiện tại: **BLOCKED; CODE REVIEW FAIL**.

## 5. Báo cáo và bàn giao đã hoàn thành

- Báo cáo triển khai W3: `reports/tv2/TV2_W3.md`.
- Protocol B1/B2: `reports/tv2/TV2_W3_PROTOCOL.md`.
- Trạng thái checkpoint: `reports/tv2/TV2_W3_CHECKPOINT.md`.
- Bảng so sánh B1/B2: `reports/tv2/TV2_W3_COMPARISON.md`.
- Review TV1: `reports/tv2/TV2_REVIEW_TV1_W3.md`.
- Review TV3: `reports/tv2/TV2_REVIEW_TV3_W3.md`.
- Remote audit và test logs: `reports/tv2/w3_evidence/`.
- Gói kiểm tra local: `LOCAL_REVIEW_RESULTS/W3/`, gồm 19 file với **19/19
  SHA-256 MATCH**.

Các commit W3 đã push:

1. `8c0039ecb6e9987904e8a52b405cea4f8ccaac25` — chuẩn bị pipeline B1 và gate.
2. `af8a5bdf4b36c825a9e95764e156653673e1f73a` — kiểm tra handoff TV1/TV3.
3. `bf9aae404286a71ba6e912ce47f323bdcf53052d` — sửa adapter theo review P1.

## 6. Phần chưa thể hoàn thành

Những mục sau chưa được trình bày là kết quả hoàn thành:

- Preflight trên bundle TV1 thật vì `comparison_v1` chưa có trên remote.
- Đồng thuận chính thức TV2/TV3 về optimizer, scheduler, epoch, preprocessing
  và GPU budget.
- Huấn luyện và validation B1 chính thức trên GPU.
- Checkpoint B1 chính thức, hash và URL bàn giao.
- Metric validation thật và bảng so sánh B1/B2.

Các trường receipt/hash/Git ref, protocol approval và budget trong config vẫn
để trống có chủ đích. Official training tiếp tục dừng fail-closed cho đến khi
có dữ liệu khóa, protocol được phê duyệt và GPU/budget hợp lệ.

## 7. Kết luận

TV2 đã hoàn thành pipeline, gate, adapter schema, kiểm thử, synthetic smoke,
cross-review và tài liệu kỹ thuật thuộc phạm vi có thể thực hiện độc lập trong
tuần 3. Kết quả hợp lệ hiện tại là:

**W3-02 CODE READY — OFFICIAL TRAINING BLOCKED.**

Không có metric, checkpoint hoặc kết luận B1/B2 giả được tạo khi dữ liệu và
protocol chính thức chưa sẵn sàng.
