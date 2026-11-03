# TV2 → TV4: kiểm adapter DINOv3 W5, 02/11/2026

TV2 đã nhận gói thật `DINOv3_LP_run01`; xem trạng thái gate/model replay trong
[biên bản nghiệm thu](../reports/tv2/TV2_W5_DINO_ACCEPTANCE_2026-11-02.md).
Đây là tài liệu kiểm tra trên nhánh TV4, không phải xác nhận đã tích hợp hoặc
quyền thay model production. TV2 không sửa nhánh/app/config production TV4.

## Artifact và source chính xác

- Training source: `aa64fd7661827af78ddec4e3e0155b2b9c87b9e2`.
- Report: `5734d38c3af2fe052cf04c4c33d940e8f186306d`.
- Protocol APPROVED TV2: `8137ef720222784bac859ab953124b4cc293f179`, receipt
  `configs/dinov3_lp_w5.local.protocol.json`, SHA-256
  `e47b96f5e576c234e2e48143c7c008df79ca62156cebf6b2bf65c0119a6f133a`.
- Checkpoint `best_model.pt`, 86.851.958 bytes, SHA-256
  `acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3`.
- ZIP nguyên gói,81.225.769bytes, SHA-256
  `9e969585cd7c7355733976b37bda912dd8deb2667d096ddf9193d62bbc276301`.
- Architecture checkout DINOv3 chính thức tại
  `6876159a11b4df116f30f667f8c9888617df0751`; repo phải clean. Checkpoint đã
  chứa backbone/head, không cần tải pretrained gốc riêng để inference.

Các file TV3 phải giữ nguyên. Lấy kết quả/hash đầy đủ từ receipt TV2 và
`reports/tv3/w5_final/DINOv3_LP_run01/` ở report commit; binary lấy từ ZIP đã
gửi ngoài Git. Không đổi checkpoint B2 hoặc trỏ loader ResNet18 vào file DINO.

## Hợp đồng adapter cần TV4 triển khai/kiểm

Dùng `src.training.dino_probe.load_package` và `predict_crops` từ training
commit đã khóa, hoặc adapter mới được kiểm tương đương. Ví dụ gọi API:

```python
backbone, head, transform, payload = load_package(
    checkpoint_path,
    "acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3",
    device="cuda",
    repo_dir=architecture_checkout,
)
logits = predict_crops(backbone, head, transform, rgb_pil_crops, "cuda")
probabilities = logits.softmax(-1)
```

Backbone frozen/eval, CLS384, Linear8; RGB, không EXIF transpose; crop geometry
khớp detector/UI đã thống nhất, không pad hoặc transform lặp. Transform DINO:
ToImage uint8 → square256 bilinear antialias → float32 scale → ImageNet normalize.
Không dùng Resize/CenterCrop224 của B2. Dùng FP32; không tự AMP/TF32/quantize.

Class ID cố định:

| ID | Label |
| --- | --- |
| 0 | large_antlered_muntjac |
| 1 | annamite_striped_rabbit |
| 2 | sambar |
| 3 | chinese_serow |
| 4 | common_palm_civet |
| 5 | masked_palm_civet |
| 6 | silver_pheasant |
| 7 | eurasian_wild_pig |

Demo trả vector8/top3 **riêng từng detection_id/box**, không gộp các box trong
ảnh thành một nhãn. Mean crop softmax theo parent là quy tắc metric GT-box
validation, không phải hợp đồng kết quả per-box của demo. Hòa chọn ID nhỏ nhất.
Điểm chưa calibration; nhãn người duyệt không ghi đè dự đoán gốc.

## Gate TV4 cần trả bằng chứng

1. Backend DINO được chọn tường minh; kiểm SHA/bytes, architecture/source pin,
   class map/preprocess, `weights_only=True`/strict load. Sai hash/vendor,
   thiếu weights/dependency hoặc GPU lỗi phải hiển thị lỗi; không fallback B2
   im lặng. B2 giữ checkpoint/backend riêng, chỉ fallback có lựa chọn và log rõ.
2. Smoke adapter trên train/val hoặc fixture, không Test: một box, nhiều box,
   RGB/grayscale đầu vào, nhiều kích thước. Kiểm output finite[N,8], đúng ID,
   softmax/top3/tie rule, crop/UI overlay và chọn box/hàng.
3. So sánh adapter với native DINO trên cùng crops/batch/device; ghi logits,
   dự đoán, version/thread/batch/precision và sai khác đầy đủ. TV2 fresh replay
   reference dùng extraction32crops và head680crops. Nếu batch/head shape khác
   làm lệch số, báo nguyên trạng; không tự nới tolerance để gọi exact PASS.
4. Kiểm `needs_review`, `no_detection`, ảnh lỗi/detector lỗi; save/reload/export
   đúng revision và giữ model ID/SHA để phân biệt dự đoán B2/DINO. Không coi
   classifier validation84,5% là chất lượng detector hoặc webcam end-to-end.
5. Đo cold/warm thực trên máy demo: device, Python/torch/CUDA, thread, batch,
   số ảnh/crop, thời gian/memory và lỗi. Không dùng thời gian head training hay
   GPU validation thay UI latency. Chỉ chọn cấu hình demo sau smoke/review.
6. Sửa finding cũ UI-A11Y-01 P2: nút export mobile có accessible name ở320/390px;
   gửi commit/evidence để TV2 retest. Không suy ra đã sửa từ UI functional PASS.

TV4 bàn giao commit, adapter/source/config diff, môi trường, hash checkpoint,
log so sánh native/adapter và UI smoke. TV2 kiểm chéo rồi nhóm quyết định đổi
ứng viên demo. Không tự merge PR hoặc làm nghiệm thu/cài sạch W6 trong bước này.

## Giới hạn cần giữ trong demo/báo cáo

DINO tốt hơn B2 trên cùng600ảnh validation; đây là GT crops, một seed/một lượt,
khác architecture/pretraining/preprocessing/recipe. Chưa có Test DINO độc lập,
chưa chứng minh accuracy≥88%, calibration hay chuyển miền/webcam. Muntjac↔sambar
còn12 nhầm trực tiếp; common↔masked civet13 nhầm, tăng từ7 của B2; masked-civet
recall giảm58→56/75. Không bịa nguyên nhân thị giác hoặc nhãn chuyên gia.
