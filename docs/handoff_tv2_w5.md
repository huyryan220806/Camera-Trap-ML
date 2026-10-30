# TV2 W5 handoff and continuation

W5 **PARTIAL**. Không có training run DINO hoặc đánh giá Test mới. Xem
[protocol DRAFT](../reports/tv2/W5_PROTOCOL.md),
[báo cáo](../reports/tv2/TV2_W5.md),
[review TV4](../reports/tv2/TV2_W5_TV4_REVIEW.md) và
[tiến độ](progress_tv2_w5_w6.md). Không thực hiện nghiệm thu W6 trong lượt này.

**Cập nhật 30/10:** đã review đủ ba file TV3. TV2 đồng ý kỹ thuật có điều kiện
với SGD0.01/momentum0.9/WD0.0001/cosine, seed42/max50/patience7/effective32parents
và các quy tắc đánh giá. Protocol vẫn DRAFT theo xác nhận trực tiếp của TV2;
không đăng ký `DINOv3_LP_run01` chính thức khi B1–B3 dưới đây chưa đạt.
Xem [review pretrained](../reports/tv2/TV2_W5_PRETRAINED_REVIEW_2026-10-30.md).

TV3 cần bàn giao chính xác các phần còn thiếu (không cần đề xuất lại LR/SGD/seed):

1. **B1:** file config chuẩn/full SHA và giải thích/bind smoke hash320718… với
   file nhận hashe9303b…; JSON giống nhau nhưng CRLF/LF vẫn không khớp hash.
2. **B2:** xác nhận thực tế của TV3 trên bản chuẩn/experiment qua nguồn truy vết;
   READY hiện tự ghi còn chờ TV2/TV3 xác nhận, chưa commit/push.
3. **B3:** gói `pretrained_2026-10-29/` và preflight28/10 được READY dẫn chiếu:
   source pipeline đúng SHA852989…/commit, proof checkout/weights hash+strict-load,
   transform/cache/parent-weighted loss/scheduler code và report/sample IDs/hash
   dữ liệu train/val. Không cần URL ký số hay credential. TV2 chưa nhận weights,
   vendor hoặc code ở đường dẫn gói nêu; source_images counter smoke là0.

Evidence nhận nguyên byte và metadata comparison nằm trong
`reports/tv2/w5_pretrained_review/2026-10-30/attempt_01/`.

## Người nhận

- TV3 (`dohoangphuc2006`): xác nhận cấu hình cập nhật 29/10 cùng TV2, hoàn tất
  tham số còn thiếu và đăng ký model/experiment trước lượt chính thức;
  bàn giao DINO thật với checkpoint, code nạp, preprocessing,
  head/pooling, pretrained source/hash/version, config/log/predictions/reload.
- TV1 (`huyryan220806`): đối chiếu verify-only gói `9abc9c5` và dataset hashes;
  ứng viên1.665 vẫn chưa được phép train. Không cần phát hành test109 ảnh.
- TV4 (`TienMoi79`): xem review PR #8 tại `fef2511`; từ30/10 browser responsive
  1440/390/320, chọn box/hàng, export/reload và fixtures đã PASS. Còn findingP2
  UI-A11Y-01: nút export mobile thiếu accessible name; TV4 sửa, TV2 retest.
  Không yêu cầu CSV ngoài phạm vi PR8 và không tự merge.
- TV2: kiểm tra nguồn approval và gói TV3, chạy adapter/reload theo kiến trúc
  thật, hoàn thành bảng so sánh và retest finding UI. B2 vẫn là fallback.

## CLI và hợp đồng đầu vào

Cấu hình cập nhật **29/10/2026 theo chỉ thị người dùng**, đối chiếu kế hoạch
TV3 ở `feat/metadata-split` commit `9abc9c572a9191e8a43a5abef05ebaf846b8356f`,
`docs/plans/TV3_W5_W6.md`. Plan này không thay thế xác nhận TV2/TV3 thực tế;
`status` vẫn **DRAFT**. Từ cập nhật 30/10 đã có TV2 CONDITIONAL trong chat;
approval TV3 và approval có hiệu lực vẫn chưa có.

- Ưu tiên DINOv3 ViT-S/16 frozen backbone + linear head 8 lớp; DINOv2 ViT-S/14
  chỉ dự phòng nếu thiếu weights DINOv3. Chọn và đăng ký trước official run.
- comparison_v1: train 2.800 parent/3.125 GT crops, val 600 parent/680 GT crops.
- Seed 42, tối đa **1 candidate training run**, max epochs 50, patience 7.
- Chọn checkpoint bằng image-level val macro-F1; hòa giữ epoch sớm nhất.
  Mean crop softmax vectors theo image_id rồi argmax; hòa chọn class ID nhỏ nhất.
- Effective batch 32 **ảnh nguồn**; crop microbatch có thể nhỏ hơn theo VRAM,
  nhưng loss là mean CE crops trong parent rồi mean parents của effective batch.
  Ghi microbatch/accumulation/chuẩn hóa loss thực; không reweight parent hai lần.
- Thiết bị dự kiến RTX 4060 Laptop 8 GB, FP32; chưa xác minh khả dụng.

Các giá trị learning rate/optimizer/momentum/WD/scheduler/pooling/pretrained
source/commit/SHA đã có ở ba file nhận và được ghi rõ là khai báo chưa lock.
Còn phải kiểm config byte chuẩn và source thực, đặc biệt preprocessing ID
chưa có implementation, grouping/normalization loss và scheduler step. Không
tự điền default. Không dùng Test/mở rộng chưa gate, thêm lượt fallback ngoài
ngân sách hoặc fine-tune backbone. Smoke reported PASS không là official approval.

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

Draft config đã ghi `seeds=[42]`, `max_candidate_runs=1`, nhưng `experiments=[]`
và `model.selected_model=null` để chưa đăng ký thay TV3. TV2 đã đồng ý có điều
kiện ngày30/10, không yêu cầu lại. Chỉ sau khi TV3 giải quyết B1–B3 và điều kiện
TV2 đạt, giữ nguồn xác nhận trong PR/Git và kiểm đủ training
config, mới chuyển `status=APPROVED`/ghi reviewer thực cùng experiment/model đã
chọn. Không tạo approval receipt, chữ ký hoặc giá trị giả để vượt gate.
Gate tự động không xác thực tác giả approval và chưa kiểm toàn bộ tham số train
mới; cần review training config trước official run, không nới code gate ở lượt này.

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
  "seed": 42,
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
