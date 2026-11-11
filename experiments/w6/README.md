# W6 registry và bàn giao cho TV3

Trạng thái hiện tại **DRAFT / RESULT PENDING**. `registry.json` có R0 reference
và R1–R6 chưa thực hiện. Config trong `configs/w6/` là contract TV2 để review,
chưa phải config trainer TV3. Không có trainer/GPU launcher trên nhánh TV2.

Kiểm tra read-only từ repository root:

```powershell
python -X utf8 scripts/evaluate_w6_validation.py
python -X utf8 -m unittest discover -s tests -p test_w6_validation.py -v
python -X utf8 scripts/review_tv1_w6.py --output outputs/tv2_w6/new_metadata_attempt
```

Cần `jsonschema` đã nằm trong requirements của dự án. Review ZIP thêm
`--image-zip <đường-dẫn-ZIP>`, dùng Pillow hiện có; chỉ decode ảnh train mới,
không extract/ghi đè ảnh. Mọi output phải là thư mục mới dưới `outputs/`.
Windows sandbox cần TEMP/TMP ghi được cho fixtures; không sửa tests để bỏ gate.

## Trước official run

TV3 cung cấp implementation W6, train-only smoke, runtime/device/time booking,
source Git commit và file hashes. TV2 đối chiếu recipe, review actual evidence,
thống nhất tham số chưa rõ và khóa config trước xem official val metrics.
Config đổi từ DRAFT thành FROZEN là thay đổi nội dung và phải tính lại digest;
source/runtime_lock phải thực, không null. `runtime_lock` dùng canonical digest
W6 của JSON runtime. Receipt approval dẫn evidence có provenance thật, không
dùng tên người hoặc chữ PASS làm bằng chứng duy nhất.

Registry giữ source/config/dataset/seed, approvals, trạng thái, attempts,
checkpoint/metrics/evidence. `tv3_preparation_attempts` ghi GPU smoke/extraction
chưa nằm trong official attempt, tránh tính hai lần. Run lỗi/OOM/dừng vẫn tính
official attempt; thời gian chưa biết là null, không phải 0h. Báo usage chưa đo
và dừng mở lượt mới đến khi đối chiếu xong. Max6 attempts và12h TV3 bao gồm
preparation; mỗi official attempt≤2h; replay TV2≤2h. Run đã bắt đầu không quay
về REGISTERED, không xóa attempt; lịch sử revision giữ trong Git.
R0 ghi source training W5 thực và config reference W5 nguyên byte; trường
config_sha256 dùng canonical digest W6, validator kiểm thêm raw SHA W5 đã khóa.

R3/R4 chỉ mở sau recipe decision vượt R0. R5/R6 cần TV2 review release PASS,
recipe decision (có thể R0 fallback) và budget. `quality_ready` TV1 không mở gate.

## Contract package artifact-only

Lệnh khi có package thật, protocol đã khóa và registry COMPLETED:

```powershell
python -X utf8 scripts/evaluate_w6_validation.py --run-id R1 --handoff <package>/handoff.json --checkpoint <package>/best_model.pt --output outputs/tv2_w6/new_candidate_audit
```

`handoff.json` khai báo đúng các identity sau:

- `run_id`, `seed`, `checkpoint_sha256`, `checkpoint_bytes`, `config_sha256`,
  `source_sha` (Git40hex), `dataset_sha256`, `train_dataset`,
  `val_dataset=comparison_v1`, `evaluation_split=val`.
- `class_order` tám lớp; `manifest_sha256` đúng năm Train/Val hashes do
  `load_frozen_validation` trả về; `aggregation=mean_crop_softmax_then_argmax`.
- `validation_metrics`: accuracy, macro_precision, macro_recall, macro_f1,
  chưa làm tròn. Registry lưu accuracy/macro_f1 và trỏ evidence đầy đủ.
- `artifacts`: config, source_index, training_log, runtime, crop_predictions,
  image_predictions, reload_report; mỗi entry có `path` tương đối trong package
  và SHA256 byte thật. Ghi thêm SHA raw config trong artifact, tách canonical digest.

Source index có `commit` khớp source_sha và `files_sha256` mapping relative
package path → byte SHA. Đóng gói actual source, không chỉ tên commit. Runtime
JSON khớp config.runtime.runtime_lock. Producer reload JSON có status PASS,
fresh_process=true, checkpoint/config/source/runtime hashes, manifest_sha256,
evaluation_split=val, test_inference_performed=false, comparison_policy=exact,
exact_predictions_and_metrics=true. TV2 kiểm receipt/Git provenance riêng;
report do producer tạo không thay TV2 replay.

Crop/image JSONL tái dùng field schema W5 trong `contracts/w5_*prediction.schema.json`;
`experiment_id` của image prediction phải là run W6 (R1…R6). Crop rows cung cấp
đúng một trong logits hoặc class_scores; khuyến nghị raw softmax FP32 thực đã
export, tránh tính lại FP64 exp làm đổi near tie. Cần đủ680 crop và600 image IDs,
đúng parent/nhãn; saved image vector phải khớp aggregation atol1e-10.

`ARTIFACT_VERIFIED` chỉ xác nhận byte/identity/aggregation/metric trong phạm vi
validator. Source review thuật toán trainer, log epoch/budget đầy đủ, xác thực
authorship approvals, fresh-process model replay và TV4 adapter vẫn cần biên
bản riêng. Tool không load model, không gửi approval, không bật model demo.
Không dùng predictions/checkpoint giả để làm đầy registry; synthetic fixtures
chỉ phục vụ unit tests và không được đưa vào bảng kết quả mô hình.
