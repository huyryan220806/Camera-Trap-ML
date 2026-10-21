# TV2 W3 – CONTINUATION 03 REPORT

## 1. GitHub

Ngày 18/10/2026, nhánh TV2 `feat/baseline`. B1 chạy từ code/config commit
`d81f584`. Sau training đã fetch lại: main `468d81f`, TV1 `7e9b194`, TV3
`c01a751`. Không checkout/push nhánh người khác, không merge hoặc force-push.

## 2. TV1 W3-01

Handoff `comparison_v1` và provenance
`d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`
đã PASS. 2.800 train + 600 validation, 8 lớp; 3.400 ảnh được kiểm byte/pixel
hash, decode và kích thước. Test JSONL/pixels không được mở.

## 3. Protocol và runtime authorization

Protocol nhóm đã chốt: ResNet18 ImageNet V1, full fine-tune/no dropout/FP32,
seed 42, SGD lr 0.001 momentum 0.9 weight decay 0.0001, StepLR10 gamma0.1,
batch32, max50/patience7, transforms đã thống nhất. Chỉ thị của người dùng
“tiếp tục các công việc vẫn chưa hoàn thành” và sau đó “tiếp tục thực hiện công
việc” cho phép hoàn tất một `B1_run01`; bằng chứng bất biến ở
`W3_PROTOCOL_AND_RUNTIME_AUTHORIZATION_2026-10-18.json`.

## 4. Environment

Python 3.11.9, PyTorch 2.8.0+cu126, torchvision 0.23.0+cu126, CUDA 12.6,
NVIDIA GeForce RTX 4060 Laptop GPU. CUDA smoke batch32 ảnh thật PASS. Môi trường
được giữ riêng tại ignored `outputs/tv2_w3/venv_cuda`.

## 5. B1 training

`B1_run01` COMPLETED, 29 epoch; early stopping sau 7 epoch không vượt best;
best epoch 22. Toàn bộ 11.180.616 tham số trainable, frozen=0, gradient check PASS.
Training time 11.409,95 giây; validation time 1.557,83 giây; total wall time
14.805,39 giây. Peak GPU memory 895.525.376 byte. Một khoảng runtime bị kéo dài
do I/O/phiên giám sát; metric và reload không bị sai lệch.

## 6. B1 validation

| Metric | Giá trị |
|---|---:|
| Macro-F1 | 0,5624506868 |
| Macro-precision | 0,5748610369 |
| Macro-recall | 0,565 |
| Accuracy | 0,565 |
| Validation loss | 1,3379992723 |
| Support | 600 |

Per-class F1: large-antlered muntjac 0,4496; Annamite striped rabbit 0,6389;
sambar 0,5271; Chinese serow 0,6370; common palm civet 0,4444; masked palm
civet 0,5238; silver pheasant 0,7126; Eurasian wild pig 0,5660.

## 7. Checkpoint

Local path `experiments/B1_run01/checkpoints/best_model.pth`; 44.815.625 byte;
SHA-256 `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c`.
Reload trong run PASS. Validator process mới PASS; metric, loss và logits delta=0.
Checkpoint không commit; download URL/upload còn PENDING.

## 8. TV3 cross-review

TV3 đã cập nhật từ `d08eba7` lên `c01a751`. 23/23 test cô lập PASS. Các sửa đổi
protocol/path/drop_last/provenance/best epoch/smoke được ghi nhận. Review vẫn
PENDING vì config tắt source hash, grouped loss chỉ đúng trong batch crop,
official output có thể ghi đè và chưa có fresh-process reload. Không mở test data.

## 9. B1/B2 comparison

B1 có kết quả official. B2 chưa có run được nghiệm thu nên không tính delta, không
chọn winner và không suy diễn từ synthetic/crop metric. Trạng thái:
**B1/B2 COMPARISON PENDING – TV3**.

## 10. Tests và integrity

- 87/87 regression test TV2 PASS trước training.
- Real-data preflight PASS sau runtime binding.
- Independent official checkpoint validation PASS.
- TV3 isolated tests 23/23 PASS; review findings vẫn tồn tại ngoài coverage.
- 53/53 artifact bảo vệ W1/W2/B0 không đổi; B0 checkpoint hash vẫn
  `d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680`.

## 11. Artifact và handoff

Run metadata/log/plots/metrics được lưu dưới `experiments/B1_run01/`; weight `.pth`
giữ local và bị Git ignore. Machine-readable evidence ở
`w3_evidence/continuation_03/`. Local review snapshot mới được tạo sau commit/push,
không ghi đè Continuation 02.

## 12. Blockers còn lại

1. Nhóm chưa chỉ định nơi upload checkpoint, nên chưa có URL tải và round-trip hash.
2. TV3 cần sửa bốn finding P1, chạy/validate B2 và phát hành handoff official.
3. Chưa có nghiệm thu độc lập cuối cùng; không merge PR.

## 13. Final status

**W3-02 B1 TRAINED – B1/B2 COMPARISON PENDING**.
