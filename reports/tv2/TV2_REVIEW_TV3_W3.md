# TV2 review W3-03 — PENDING TV3 W3-03 HANDOFF

Ngày 15/10/2026. Nhánh đọc `origin/feat/crop-classifier`, commit
`2c3c9928edb8f913f24df657464f47d480e3ae95`. Không sửa code TV3.

Sản phẩm tìm thấy là W2 crop: `scripts/crop_dataset.py`,
`src/data/crop_dataset.py`, `data/crops/v1_run03/crop_manifest_{train,val}.jsonl`
và `run_meta_{train,val}.json`. Không tìm thấy B2 training config, checkpoint,
epoch log, validation report hay reload evidence W3.

| Chỉ số artifact W2 | Train | Validation |
|---|---:|---:|
| Số crop | 4.480 | 1.131 |
| Ảnh gốc duy nhất | 4.000 | 1.000 |
| Giao với cùng split pilot v2 TV1 | 595 | 147 |
| Pilot v2 chưa có crop tương ứng | 2.205 | 453 |
| Ảnh crop ngoài pilot v2 cùng split | 3.405 | 853 |

`run_meta` ghi source manifest v1, limit4000/1000, không phải pilot v2.
Chênh lệch là khác nguồn W2, **không gọi đây là lỗi của B2 chưa tồn tại**.
Chưa có căn cứ so sánh metric B1/B2. Artifact mapping có image_id,
annotation_id, original bbox, clamped bbox, nguồn URL, crop hash; khả năng truy
vết bằng metadata có sẵn nhưng chất lượng crop W3 chưa kiểm định.

Khác biệt transform/multiple-box/drop_last cần chốt ở
[protocol đề xuất](TV2_W3_PROTOCOL.md). Chưa xác minh crop bytes tại máy TV3;
không chạy source TV3, không train B2 thay TV3.

Checklist sau handoff (tất cả **NOT TESTED** đối với W3):

- Cùng freeze receipt/version/hash, class map, eligible image IDs và split B1.
- Source/annotation/bbox/padding/crop pixels đúng, không thất lạc hay thêm mẫu.
- Không leakage; thống nhất một crop/ảnh hoặc phương án sampling/aggregation
  khác đã phê duyệt trước khi train.
- Cùng backbone, khởi tạo, seed, optimizer/scheduler, augmentation, số bước,
  budget/early stopping; mọi khác biệt có lý do và ghi trước kết quả.
- Best checkpoint theo val macro-F1 đủ mọi lớp, không test selection.
- Validation metrics/per-class/confusion matrix có thể tính lại từ prediction.
- Reload/hash/provenance PASS, runtime/GPU log và checkpoint có thể tải thật.

**Status: PENDING TV3 W3-03 HANDOFF.** Không có B2 metrics để công bố.
