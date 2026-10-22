# TV2 W4-02 Test evaluation

Trạng thái: **BLOCKED — Test chưa mở để model inference**. Không có official Test run, metric hay Confusion Matrix Test trong gói này.

## Điều kiện và dữ liệu

Final model lock còn `FINAL MODEL LOCK PENDING`: thiếu checkpoint B2 local và artifact run B3 gốc. Bộ ảnh Test gốc đã khôi phục đúng SHA. [Lock](TV2_W4_MODEL_SELECTION_LOCK.json), [protocol](TV2_W4_EVALUATION_PROTOCOL.json), [audit](w4_evidence/repository_audit.json).

Manifest Test được kiểm tra metadata: 600 ảnh nguồn, 680 crop, 495 chuỗi, 98 địa điểm, 75 ảnh/lớp. SHA provenance `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`; SHA Test source manifest `e86e776dbf6416d21028230599b2699cf186d13d68f2f4c24d4c6a25ad2200f2`; SHA B2 Test manifest `2504cb38c946eba8a2e19cbcbe26f38973023a7bc4db32089a801ebde7bc9bbb`. Không giao image ID/file/location/sequence/file SHA giữa các split theo audit metadata. Việc kiểm kê không phải model inference.

TV1 đã kiểm tra 600 ảnh trên máy TV1, có 599 nội dung RGB duy nhất. TV2 đối chiếu đủ 600 quality record, ID, SHA file, kích thước và manifest; **600/600 file Test đã được khôi phục** từ URL gốc, khớp SHA-256/byte size, decode/kích thước và RGB hash theo hàm TV1. Việc khôi phục chỉ kiểm tra dữ liệu, không model inference. [Bằng chứng local](w4_evidence/test_source_restoration.json). [Đối chiếu TV1](w4_evidence/tv1_inventory_audit.json). Cặp ảnh trùng cùng Test được giữ nguyên.

## Phương pháp đề xuất đã hiện thực

Sau khi bằng chứng đầy đủ, khóa hai JSON và SHA sidecar trong commit trước Test. Chỉ B2 nằm trong kế hoạch; B1 Test là `NOT EVALUATED BY FROZEN PLAN`, B3 không đánh giá Test. Không thay đổi danh sách sau khi xem điểm.

Mỗi ảnh dùng đủ crop nguyên đã khóa, padding 0, RGB không EXIF rotation, Resize(short side 256) → CenterCrop224 → tensor → ImageNet normalization. Chạy `eval`, `inference_mode`, không augmentation ngẫu nhiên. Trung bình vector softmax của mọi crop rồi argmax theo ID 0–7; tie chọn ID nhỏ nhất. Chỉ một prediction/ảnh. Không làm tròn trước macro average; zero_division=0; ma trận hàng thật/cột dự đoán.

Không có ngưỡng review được chọn bằng Validation. Phân loại cơ bản dùng argmax toàn bộ 600 ảnh, không bỏ ảnh điểm thấp. Softmax chưa calibration. Loss không báo cáo để tránh nhập nhằng crop CE và CE trên xác suất ảnh trung bình. CPU batch tối đa 32 crop, seed 42, 4 threads là phương án chưa frozen; không suy ra GPU latency.

## Kết quả Test

| Metric | B2 Test |
|---|---|
| Macro-F1 | NOT RUN |
| Macro-Precision | NOT RUN |
| Macro-Recall | NOT RUN |
| Accuracy | NOT RUN |
| Evaluated support | 0; expected 600 |
| Per-class P/R/F1/support | NOT RUN; expected support 75/lớp |
| Confusion Matrix 8×8 | NOT GENERATED |

Các ma trận trong [audit Validation](w4_evidence/validation_matrix_audit.json) thuộc **Validation**, không phải Test.

## Chạy an toàn và tính toàn vẹn

```powershell
$py = 'outputs/w2_final_handoff/tv4_env/Scripts/python.exe'
& $py scripts/evaluate_w4_test.py
# Hiện trả exit 2 BLOCKED trước khi đọc Test rows hay import inference runtime.
# Chỉ sau khi thực sự hoàn tất/commit final lock và protocol:
& $py scripts/evaluate_w4_test.py --checkpoint <verified-B2-file> --execute
```

Preflight kiểm tra lock committed, SHA code/config/provenance/manifests/checkpoint, mapping, threshold và kế hoạch đúng B2. Sau gate kiểm tra leakage/crop/source hash/full decode, metadata checkpoint và tái kiểm tra gate. Marker exclusive toàn repository chặn run thứ hai. Không hỗ trợ resume an toàn: nếu gián đoạn giữ journal/state và dừng để review, không xóa marker hay tự tạo run mới.

Artifact dự kiến ở `outputs/tv2_w4/W4_test_eval01/`: metric JSON, per-class CSV, CM CSV/PNG, prediction CSV và journal đầy đủ softmax, config/manifest/checkpoint verification/log/environment/error analysis. Không tạo các file này khi bị chặn. Test synthetic kiểm tra đường xuất toàn bộ file và SHA trong thư mục tạm, không phải kết quả SWG. Metric kiểm tra chéo từ CM trước khi đánh COMPLETE. Không upload ảnh hay weights.
