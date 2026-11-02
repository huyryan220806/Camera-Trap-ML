# Bàn giao DINOv3_LP_run01 — 02/11/2026

Training COMPLETE; fresh-process reload PASS; auditor TV2 ARTIFACT_VERIFIED.
Đang chờ TV2 kiểm định model độc lập và TV4 xác nhận tích hợp.
Không có Test mới hoặc kết luận accuracy88% độc lập.

| Validation cùng comparison_v1 | B2 | DINOv3 |
|---|---:|---:|
| Accuracy | 0.7466666666666667 | 0.845 |
| Macro-F1 (training report) | 0.7454765175212033 | 0.8444008279545705 |
| Ảnh đúng / tổng | 448/600 | 507/600 |

Best epoch9; dừng sau16 epoch theo patience7. Seed42, một lượt chính thức,
không đổi recipe. B2 sai/DINO đúng95 ảnh; B2 đúng/DINO sai36; cùng đúng412;
cùng sai57. Đây là cải thiện validation, không tách riêng hiệu ứng kiến trúc,
pretraining, preprocessing và recipe, không chứng minh ổn định nhiều seed.

Source thực thi: `aa64fd7661827af78ddec4e3e0155b2b9c87b9e2`.
Protocol TV2: `8137ef720222784bac859ab953124b4cc293f179`, raw receipt SHA
`e47b96f5e576c234e2e48143c7c008df79ca62156cebf6b2bf65c0119a6f133a`.
Auditor pin tại `3f76643d1bc395098d90105e67a9cf29c8fe3256`; audit này chạy
trên máy TV3 bằng code TV2, không thay phép nạp model độc lập của TV2.

Checkpoint `best_model.pt`: 86.851.958 bytes, SHA-256:
`acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3`.
File binary gửi ngoài Git, cùng gói ZIP; không có link tải được tạo tự động.

## Nội dung

Giữ nguyên byte artifacts gốc: config, binding, class_map, preprocessing,
train_log, validation, val_crops.jsonl680 dòng, val_images.jsonl600 dòng,
confusion_matrix.csv/png, comparison, MODEL_CARD, handoff, status, cache reference
và reload report/predictions. `tv2_audit/` chứa auditor log/invocation/predictions
và audit. `artifact_index.json` ghi SHA/bytes, không tự hash chính nó.

Reload trích lại đủ680 crop trong tiến trình mới, không dùng feature cache;
logits/metrics khớp chính xác, max_abs_logit_delta0. Auditor tính metric độc
lập có sai khác dấu phẩy động cuối (~1e-16); giữ nguyên cả hai báo cáo, không
làm tròn/sửa evidence để ép bằng. Paths tuyệt đối trong binding/reload là
đường dẫn lịch sử của máy TV3; handoff artifact paths tương đối được giữ nguyên.

## TV2

Nhận weights ngoài Git, kiểm SHA/bytes trước nạp; giải nén để các artifact
nằm cạnh best_model.pt theo đường dẫn trong handoff. Dùng protocol.approved.json
và val_crops.jsonl cho evaluator. Chuẩn bị đúng dữ liệu comparison_v1 nếu replay
validation; không tải lại Test hay dùng tập mở rộng. Ghi attempt mới cho mỗi
lần kiểm, không ghi đè evidence của TV3. Checklist tiếp nhận: source/config/
weights SHA, class order, full600/680 predictions, metrics/CM, reload, paired B2.

## TV4

Dùng source của Camera-Trap-ML ở training commit trên, Python/torch runtime
ghi trong binding và checkout DINOv3 chính thức tại
`6876159a11b4df116f30f667f8c9888617df0751`.
Package chứa cả backbone/head; không cần tải lại pretrained gốc để nạp best.
Cần checkout kiến trúc, có thể truyền repo_dir tới `load_package`.
Ví dụ sử dụng nằm trong `docs/handoff_tv3_w5.md` của repo: kiểm SHA qua
load_package, RGB crop → predict_crops → softmax/top3 riêng từng box.
Không thay đường dẫn checkpoint ResNet18 rồi giả định adapter tương thích;
không im lặng fallback B2 khi DINO lỗi. Scores chưa calibration. Giữ B2 dự
phòng đến khi nhóm kiểm định và thống nhất ứng viên demo.

## Trạng thái

TV3 đã có đủ artifact training/validation/reload để gửi. Việc đóng gói không
đồng nghĩa TV2 đã nghiệm thu hoặc TV4 đã tích hợp. Không chạy thêm seed/lượt
training khi chưa có ngân sách mới. Giữ original run và last_model.pt để sao lưu.
