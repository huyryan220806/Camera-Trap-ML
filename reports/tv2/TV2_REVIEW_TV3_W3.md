# TV2 review W3-03 — BLOCKED; CODE REVIEW FAIL

## Cập nhật CONTINUATION_02 – 18/10/2026

Trạng thái mới nhất: **W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**. TV1 `7e9b1949f10126fbcfa83fa12baeca488b6aeab3` đã phát hành;
provenance/native adapter và full train/val preflight PASS; 3.400 ảnh đã kiểm byte/pixel
hash/decode. Protocol đã được người dùng xác nhận cụ thể cho nhóm. CUDA batch32 smoke
PASS trong venv riêng; 87/87 regression PASS. Chưa có budget/window và official
environment freeze, chưa train/validation/checkpoint B1 thật. TV3 vẫn d08eba7 cần sửa.
Xem [báo cáo mới](TV2_W3_CONTINUATION_02_REPORT.md) và [README bàn giao](README_W3_HANDOFF_TEMP.md).
Các phần bên dưới giữ làm lịch sử; các kết luận cũ “TV1 chưa push”, “chưa có cache”,
“chưa thống nhất thông số” không còn là trạng thái hiện tại.

Continuation 01 ngày 16/10/2026: đã fetch, TV3 vẫn `d08eba7`; chưa có commit sửa
mới. **PENDING TV3 FIX / REVIEW**. 9/9 là kết quả snapshot ở lần review trước,
không được coi là bộ test mới của lượt này hoặc acceptance. Không chạy lại bộ
TV3 không đổi; đã đọc lại config/model/training/evaluator để cập nhật
[bảng protocol](TV2_W3_PROTOCOL.md). Thêm điểm cần chốt: batch crop với trọng
số1/N và drop_last chưa bảo đảm cùng số update/ảnh với B1; epoch train loss B2
đang cộng batch-weighted mean theo số crop thay vì tổng trọng số. Giữ các lỗi
blocking bên dưới và chờ TV3 sửa; không can thiệp nhánh TV3.

Ngày 16/10/2026. Nhánh đọc `origin/feat/crop-classifier`, commit
`d08eba7fffbfb6ecc813de8522fb4d58cd8ed904`. TV2 không sửa hoặc chạy trực tiếp
trong nhánh TV3; một snapshot tạm được dùng để kiểm thử độc lập.

Commit thêm 10 file cho B2: config, dataset, model ResNet18, training CLI,
evaluator và tests. Chín test synthetic của TV3 đều PASS trên snapshot
(9/9, 0 fail, 0 skipped). Lệnh official dừng đúng với exit code 1 vì thiếu
`data/processed/comparison_v1/b2/{train,val}.jsonl`, `class_map.json` và
`provenance.json`. Chưa có checkpoint, epoch log, validation report, reload
evidence hoặc handoff B2 chính thức. Logs:
[tests](w3_evidence/tv3_w3_tests.txt),
[official gate](w3_evidence/tv3_w3_official_gate.txt).

Các lỗi cần sửa trước khi nghiệm thu hoặc train chính thức:

1. **Đường dẫn dữ liệu không nhất quán.** Preflight kiểm tra
   `ROOT/data/processed/comparison_v1/...`, nhưng DataLoader ghép
   `ROOT / config["data"]["dataset_version"]`. Với giá trị `comparison_v1`,
   loader sẽ đọc `ROOT/comparison_v1`, nên vẫn lỗi sau khi gate đã PASS.
2. **Preflight chỉ kiểm tra file tồn tại.** Chưa xác minh hash, trạng thái frozen,
   commit, provenance, class map, source membership, eligible IDs, split,
   leakage, exclusion accounting hoặc crop mapping. Config còn đặt
   `preflight_hash_check=false`.
3. **Protocol B1/B2 chưa đồng nhất.** B2 dùng 15 epoch, AdamW, cosine,
   lr `1e-4`, dropout 0.2, Resize vuông 224, saturation 0.2,
   `drop_last=true` và nhiều crop/ảnh với mean-probability aggregation. B1 đang
   đề xuất 50 epoch, SGD/StepLR, không dropout, Resize256 + crop224,
   saturation 0.1 và `drop_last=false`. So sánh hiện tại không công bằng.
4. **Early stopping chưa được thi hành.** Config có patience 5 nhưng training
   loop không dừng sớm.
5. **`best_epoch` sai.** Evaluator không trả epoch; report đọc
   `best_metrics.get("epoch", epochs)` nên thường ghi epoch cuối, không phải epoch
   tạo best checkpoint.
6. **Checkpoint và metrics không cùng trạng thái model.** File cuối lưu
   `model.state_dict()` sau epoch cuối nhưng đính kèm `best_metrics`; chưa reload
   best weights trước khi đóng gói checkpoint.
7. **Thiếu kiểm định fresh reload/provenance.** Không có SHA-256 checkpoint,
   fresh-process reload và đối chiếu logits/metrics. Evaluator dùng
   `torch.load(..., weights_only=False)` trước khi xác minh hash.
8. **Run không bất biến.** Tên output cố định, CSV append và checkpoint/report
   bị ghi đè; chưa reserve run ID hoặc bảo vệ run đã tồn tại. Không ghi đủ môi
   trường, GPU, peak memory và validation time.
9. **Validation dữ liệu/crop chưa đủ.** Bbox chỉ kiểm `len == 4`, chưa kiểm số
   hữu hạn, thứ tự, biên, crop rỗng, crop trùng hoặc nhãn nhất quán giữa các crop
   của cùng ảnh. Aggregation lấy nhãn crop đầu tiên mà không xác nhận các nhãn
   còn lại. CLI evaluator còn cho phép `--split test`, trái quy tắc W3 không mở
   test. Tests hiện tại chưa bao phủ các trường hợp này.

Checklist nghiệm thu còn BLOCKED:

- Cùng freeze receipt/version/hash, class map, eligible image IDs và split B1.
- Quy tắc bbox/padding/multiple-box và đơn vị sampling/aggregation được TV2/TV3
  đồng thuận trước kết quả.
- Cùng backbone, pretrained weights, seed, augmentation, optimizer/scheduler,
  số bước và early stopping, hoặc có protocol ghi rõ khác biệt được duyệt.
- Best checkpoint theo validation macro-F1 đủ mọi lớp, có per-class metrics,
  confusion matrix và prediction-level evidence có thể tính lại.
- Checkpoint gắn đúng best epoch, hash/provenance, fresh reload PASS và run bất
  biến; runtime/GPU log đầy đủ.

**Final: BLOCKED; CODE REVIEW FAIL. PENDING TV3 FIXES AND OFFICIAL HANDOFF.**
