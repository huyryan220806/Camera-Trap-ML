# TV2 W5 handoff and continuation

W5 **PARTIAL**. Không có training run DINO hoặc đánh giá Test mới. Xem
[protocol DRAFT](../reports/tv2/W5_PROTOCOL.md),
[báo cáo](../reports/tv2/TV2_W5.md),
[review TV4](../reports/tv2/TV2_W5_TV4_REVIEW.md) và
[tiến độ](progress_tv2_w5_w6.md). Không thực hiện nghiệm thu W6 trong lượt này.

## Người nhận

- TV3 (`dohoangphuc2006`): chốt tie/seed/ngân sách và đăng ký experiment trước
  lượt chính thức; bàn giao DINO thật với checkpoint, code nạp, preprocessing,
  head/pooling, pretrained source/hash/version, config/log/predictions/reload.
- TV1 (`huyryan220806`): đối chiếu verify-only gói `9abc9c5` và dataset hashes;
  ứng viên1.665 vẫn chưa được phép train. Không cần phát hành test109 ảnh.
- TV4 (`TienMoi79`): xem review PR #8 tại `fef2511`; API đạt nhưng cần kiểm tra
  UI trực quan 1440/390/320, chọn box/hàng, export/reload trình duyệt. Không có
  lỗi sản phẩm đã tái hiện trong phần API; không yêu cầu CSV ngoài phạm vi PR8.
- TV2: kiểm tra nguồn approval và gói TV3, chạy adapter/reload theo kiến trúc
  thật, hoàn thành bảng so sánh và review browser. B2 vẫn là fallback.

## CLI và hợp đồng đầu vào

Không có `.venv` ở gốc trên máy này. Interpreter đã dùng:
`outputs/w2_final_handoff/tv4_env/Scripts/python.exe` (Python3.12.14).
Không đổi môi trường trong lúc có process khác đang chạy. Mỗi output mới dùng
attempt/path chưa tồn tại; không xóa attempt cũ để chạy lại.

```powershell
$tv2py = 'outputs/w2_final_handoff/tv4_env/Scripts/python.exe'
& $tv2py -X utf8 scripts/evaluate_w5_validation.py --help
& $tv2py -X utf8 scripts/verify_w5_pixels.py --output outputs/tv2_w5/attempt_02/train_val_pixels.json
```

Đừng chạy lại pixel gate nếu chưa có đầu vào mới: attempt01 đã kiểm tra đủ
3.400 ảnh train/val. Không dùng validator toàn snapshot để làm pixel gate W5.

Sau approval thật, TV3/TV2 tạo receipt từ draft config, giữ approval trong PR/Git:
`status=APPROVED`, `reviewers.TV3`, danh sách `seeds`, `max_candidate_runs`,
`experiments` đã chốt; metric/tie policy khớp protocol. Không điền giá trị để
vượt gate khi chưa có xác nhận. Gate tự động không xác thực tác giả approval.

Handoff JSON cần đủ các trường (N/A chưa được chấp nhận để chạy chính thức):

```json
{
  "experiment_id": "ID_DA_DANG_KY",
  "model_name": "TEN_THUC_TE",
  "architecture": "KIEN_TRUC_VA_HEAD_THUC_TE",
  "model_version": "PHIEN_BAN_CODE_VA_BACKBONE",
  "pretrained_source": "NGUON_VA_HASH_WEIGHTS",
  "checkpoint_sha256": "SHA256_THUC_TE_64_HEX",
  "checkpoint_bytes": null,
  "seed": null,
  "dataset_version": "comparison_v1",
  "train_dataset_version": "comparison_v1",
  "val_dataset_version": "comparison_v1",
  "evaluation_split": "val",
  "provenance_sha256": "d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f",
  "manifest_sha256": {},
  "class_order": [],
  "aggregation": "mean_crop_softmax_then_argmax",
  "preprocessing": {},
  "training_status": "complete",
  "training_commit": "SHA_THUC_TE",
  "training_log": "DUONG_DAN_LOG",
  "device": "CAU_HINH_THUC_TE",
  "fresh_process_reload": {"status": "PASS", "evidence": "DUONG_DAN_BAO_CAO"},
  "artifacts": {
    "training_config": {"path": "config.json", "sha256": "SHA_THUC_TE"},
    "training_log": {"path": "train.jsonl", "sha256": "SHA_THUC_TE"},
    "reload_report": {"path": "reload.json", "sha256": "SHA_THUC_TE"}
  },
  "validation_metrics": {"accuracy": null, "macro_f1": null, "macro_precision": null, "macro_recall": null}
}
```

Đây là **hướng dẫn trường dữ liệu**, không phải artifact DINO đã tồn tại.
Copy đầy đủ `manifest_sha256` và `class_order` từ protocol/bằng chứng B2, không
đổi thứ tự score. Đường dẫn artifact tương đối với thư mục chứa handoff JSON.
Reload report phải ghi status PASS, fresh_process true, checkpoint_sha256,
evaluation_split val, manifest_sha256 khớp, test_inference_performed false;
reviewer kiểm tra nội dung và chạy lại thật, không chỉ tin các trường này.

Crop JSONL theo `contracts/w5_crop_prediction.schema.json`: đủ crop IDs từ
`b2/val.jsonl`, `ground_truth` ID0–7 và **một trong** logits/class_scores đủ8.
Không nộp top3 thay vector8, không làm tròn scores.

```powershell
& $tv2py -X utf8 scripts/evaluate_w5_validation.py `
  --protocol outputs/tv2_w5/approved_protocol.json `
  --handoff outputs/tv3_w5/handoff.json `
  --checkpoint outputs/tv3_w5/model.pt `
  --crop-predictions outputs/tv3_w5/val_crops.jsonl `
  --b2-predictions reports/tv2/w5_evidence/attempt_01/validation_02/b2_predictions.jsonl `
  --output outputs/tv2_w5/attempt_02/candidate_audit
```

Các đường dẫn TV3/approved ở lệnh là **đầu vào cần nhận sau**, chưa tồn tại.
CLI audit predictions, không nạp DINO hoặc tự thực hiện reload. ARTIFACT_VERIFIED
khác technical inference PASS, reviewer approved và PR merged. Sau adapter
thật mới đánh giá readiness. Nếu preprocessing/model khác dự kiến, cập nhật
protocol trước lượt chính thức, giữ vết thay đổi và không dùng Test để quyết định.

Để tái hiện API QA: tạo snapshot đúng commit PR8 bằng Git archive, chuẩn bị
checkpoint B2/MD và tám ảnh mẫu **train** theo đường dẫn gốc. Chạy
`scripts/review_tv4_w5.py --snapshot <snapshot> --commit fef2511b571b23be3d4e2cf6c1ccedd659097b6f --url http://127.0.0.1:8767 --output outputs/tv2_w5/attempt_02/ui_api`.
Script xác minh nội dung code với Git (ghi riêng CRLF conversion), tự mở/đóng
server local. Browser QA là bước riêng, không được thay bằng API PASS.

Trên Windows, regression cần TEMP ngoài `repo/outputs` để path-guard tests giữ
đúng điều kiện. Attempt01 dùng writable visualization root riêng, đã lưu lệnh,
thời gian và log. Không sửa test hoặc thêm proof giả để che lỗi TEMP.
