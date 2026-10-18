# CÔNG VIỆC ĐÃ HOÀN THÀNH TUẦN 3 — THÀNH VIÊN 2

**Ngày hoàn tất B1:** 18/10/2026

**Nhánh:** `feat/baseline`

**Trạng thái:** **W3-02 B1 TRAINED – B1/B2 COMPARISON PENDING**

## Kết quả chính

TV2 đã xác minh handoff W3-01 của TV1, khôi phục và kiểm tra 3.400 ảnh
train/validation, đóng băng protocol B1/B2, chuẩn bị CUDA, huấn luyện B1 chính
thức và kiểm tra checkpoint trong một process mới. Test set không được mở.

| Hạng mục | Kết quả |
|---|---|
| Run | `B1_run01`, official, COMPLETED |
| Dữ liệu | 2.800 train + 600 validation, 8 lớp |
| Epoch | 29; early stopping patience 7 |
| Best epoch | 22 |
| Validation macro-F1 | **0,5624506868** |
| Macro-precision | **0,5748610369** |
| Macro-recall | **0,565** |
| Accuracy | **0,565** |
| Validation loss | **1,3379992723** |
| Peak GPU memory | 895.525.376 byte |
| Checkpoint | 44.815.625 byte; SHA-256 `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c` |
| Reload độc lập | PASS; metric/loss/logit delta đều 0 |

## Phần TV2 đã hoàn thành

- Xác minh TV1 commit `7e9b1949f10126fbcfa83fa12baeca488b6aeab3`, provenance
  `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`.
- Kiểm byte hash, pixel hash, decode và kích thước của toàn bộ 3.400 ảnh
  train/validation; preflight dữ liệu thật PASS.
- Gắn quyết định protocol của nhóm và quyền chạy GPU vào bằng chứng Git bất biến.
- Dùng ResNet18 ImageNet, full fine-tune, FP32, SGD/StepLR, batch 32, seed 42,
  tối đa 50 epoch và patience 7 đúng cấu hình đã chốt.
- Chạy 87/87 regression test PASS trước training.
- Huấn luyện B1 chính thức; lưu log, metric, per-class report, confusion matrix,
  learning curves, data gate và status.
- Xác minh checkpoint ngay sau training và chạy lại `validate_b1.py` trong process
  mới: provenance/reload/metric/loss/logit đều PASS.
- Kiểm lại 53 artifact được bảo vệ của W1/W2/B0: không file nào thay đổi.
- Fetch và review read-only TV3 commit `c01a751`; 23/23 test cô lập PASS.

## Artifact

- [Báo cáo Continuation 03](TV2_W3_CONTINUATION_03_REPORT.md)
- [Bằng chứng B1](w3_evidence/continuation_03/b1_run01_verification.json)
- [Checkpoint handoff](TV2_W3_CHECKPOINT.md)
- [Review TV3](TV2_REVIEW_TV3_W3.md)
- [Trạng thái so sánh](TV2_W3_COMPARISON.md)
- Local run: `experiments/B1_run01/`.

Checkpoint `.pth` không commit lên Git. URL tải vẫn chờ nơi lưu artifact được nhóm
chỉ định.

## Phần còn phụ thuộc TV3

B1 đã hoàn thành. So sánh B1/B2 vẫn chưa hợp lệ vì B2 chưa có official run được
TV2 nghiệm thu. Commit TV3 mới đã sửa nhiều lỗi nhưng còn phải bật source hash
preflight, bảo đảm loss cân bằng theo parent image trên toàn epoch, chống ghi đè
run và thực hiện fresh-process reload. Không có metric B2 được chấp nhận và chưa
chọn mô hình thắng.
