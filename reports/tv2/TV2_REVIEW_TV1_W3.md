# TV2 review W3-01 — BLOCKED / PENDING TV1 HANDOFF

Ngày 15/10/2026. Nhánh đọc: `origin/codex/tv1-week2-download-quality`, commit
`b9a92b95edcc377aafcbe1efc4161bb7520f2090`. Không sửa nhánh TV1.

W2-01 có artifact thật: `docs/handoff_tv1_w2.md`, `reports/tv1_w2/REPORT.md`,
`data/processed/v2/{train,val,class_map,provenance}.json[l]`.
Handoff giới hạn pilot thử pipeline; không có W3-01 freeze/acceptance cho tập
so sánh chính thức. Vì vậy không nâng W2 v2 thành W3 frozen dataset.

Đối chiếu độc lập train/val từ Git, không mở test:

| Kiểm tra | Kết quả W2 metadata | W3 acceptance |
|---|---|---|
| Version | Pilot v2 | NOT TESTED — chưa version W3 |
| Ảnh | 2.800 train, 600 val | Chưa khóa số ảnh W3 |
| Chuỗi | 2.277 train, 508 val | Chưa khóa W3 |
| Lớp | 8; mỗi lớp 350 train, 75 val | Mapping W3 chưa chốt |
| ID/path train–val overlap | 0 / 0 | Chỉ chứng cứ W2 |
| Location/sequence overlap | 0 / 0 | Chỉ chứng cứ W2 |
| Byte/pixel hash overlap | 0 / 0 theo hash khai trong manifest | Chưa kiểm lại ảnh cục bộ W3 |
| Ảnh giữ/loại | TV1 báo W2 giữ đủ; cần ledger W3 | NOT TESTED |
| B1/B2 cùng nguồn | Crop W2 hiện không khớp pilot v2 | BLOCKED |
| TV1 freeze evidence W3 | Không tìm thấy trong nhánh/commit đã fetch | BLOCKED |
| Chất lượng ảnh/box W3 | Chưa có ảnh và review W3 được bàn giao | NOT TESTED |
| Toàn bộ split kể cả test | Không mở test; cần attestation kiểm định TV1 | NOT TESTED bởi TV2 |

Hashes và kết quả đếm thực tế: [repository_audit.json](w3_evidence/repository_audit.json).
Class map ID 0–7 vẫn là large_antlered_muntjac, annamite_striped_rabbit, sambar,
chinese_serow, common_palm_civet, masked_palm_civet, silver_pheasant,
eurasian_wild_pig. Không đổi ID.

TV1 cần bàn giao W3 freeze có version/commit/hash; train/val-only source và
eligible manifests; mapping; ledger loại có lý do; counts ảnh/chuỗi/lớp/split;
QA ảnh/nhãn/box; crop mapping đã thống nhất TV3; attestation leakage toàn bộ
split và bằng chứng nguồn W2. Không cần TV2 mở test để lấy bằng chứng này.

Sau handoff: kiểm lại hash/row membership, ID/path duplicates, location/sequence,
byte/pixel duplicate, missing class, missing/corrupt image, wrong label, bbox,
accepted/excluded accounting và crop coverage. Gate đã có fixture tests cho
các nhóm lỗi này. Chưa được đánh dấu PASS cho W3 chỉ vì tests synthetic PASS.

**Final: BLOCKED – W3-01 MANIFEST NOT FROZEN.**
