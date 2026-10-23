# TV2 W4-02 Test evaluation — tiếp nối 23/10/2026

**BLOCKED — CHƯA MODEL INFERENCE TEST.** Không có official Test run, metric Test, per-class Test hoặc Confusion Matrix Test. Lần tiếp nối không ghi đè run, không tạo số liệu giả.

## Điều kiện còn thiếu

B2 đã có file thật tại `experiments/B2_run01/checkpoints/best_model.pt`, đúng SHA/89,548,866 byte/epoch21, Validation reference PASS. B3 đã có file thật nhưng reference reproduction FAIL cả CPU và CUDA. [Model lock](TV2_W4_MODEL_SELECTION_LOCK.json) vẫn `FINAL MODEL LOCK PENDING`, `locked_utc=null`; [protocol](TV2_W4_EVALUATION_PROTOCOL.json) vẫn pending. Không commit một lock giả hay chọn runtime có điểm đẹp hơn để vượt cổng.

## Population và dữ liệu tái sử dụng

600 ảnh Test / 680 crop / 495 chuỗi / 98 địa điểm / 8 lớp, 75 ảnh/lớp. Không tải lại 600 ảnh: SHA 600/600 vẫn đúng, frozen manifests/provenance không đổi. [Integrity](w4_evidence/continuation_01/integrity_before_finalization.json). Một cặp RGB trùng cùng Test vẫn giữ nguyên; không loại ảnh khó, multi-box, box nhỏ/sát mép.

Provenance `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`; source Test manifest `e86e776dbf6416d21028230599b2699cf186d13d68f2f4c24d4c6a25ad2200f2`; B2 crop Test manifest `2504cb38c946eba8a2e19cbcbe26f38973023a7bc4db32089a801ebde7bc9bbb`.

## Phương pháp giữ nguyên

Chỉ B2 dự kiến đánh giá; B1 `NOT EVALUATED BY FROZEN PLAN`, B3 không Test. Dùng nguyên evaluator W4 đã có: RGB không EXIF rotation, integer GT crop/padding0, Resize short256 → CenterCrop224 → ImageNet normalize, eval/inference_mode, CPU/batch crop<=32/4 threads/seed42, không augmentation. Mean đủ softmax vector mọi crop theo parent → argmax (tie ID nhỏ nhất), một prediction/ảnh. Macro qua đủ labels0–7, zero_division0, không làm tròn trước macro; CM hàng thật/cột dự đoán. Không threshold để bỏ ảnh khó; threshold review chưa được chọn Validation, softmax chưa calibration. Test loss không báo cáo.

## Kết quả Test thực tế

| Metric / artifact | Kết quả |
|---|---|
| Macro-F1 / Macro-Precision / Macro-Recall / Accuracy | NOT RUN |
| Per-class P/R/F1/support | NOT RUN; expected support75/lớp |
| Evaluated source images | 0; expected600 |
| Confusion Matrix8×8 / CSV / PNG | NOT GENERATED |
| Official run ID | Chưa tạo; candidate W4_test_eval01 |

Ma trận/predictions trong `continuation_01/b2_validation/` và `b3_validation_*` là **Validation**, không phải Test. Không sử dụng chúng để điền bảng Test.

## Lệnh tái lập và gate

```powershell
$py = 'outputs/w2_final_handoff/tv4_env/Scripts/python.exe'
& $py scripts/evaluate_w4_test.py --checkpoint experiments/B2_run01/checkpoints/best_model.pt
# Hiện BLOCKED trước Test inference; chỉ sau final lock/protocol hợp lệ đã commit:
& $py scripts/evaluate_w4_test.py --checkpoint experiments/B2_run01/checkpoints/best_model.pt --execute
```

Evaluator giữ nguyên SHA/code và gate đã kiểm thử. Một official marker toàn repo chặn lần chạy thứ hai; không resume an toàn thì giữ journal/state và dừng để review. Khi được phép, artifact ở `outputs/tv2_w4/W4_test_eval01/`: metrics/per-class/CM/predictions/config/manifest/checkpoint verification/log/environment/error analysis. Hiện chưa tạo thư mục official này. Không upload ảnh hoặc weights lên GitHub.
