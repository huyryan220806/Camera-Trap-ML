# TV2 review W3-01 — BLOCKED / HANDOFF NOT PRESENT ON REMOTE

Ngày 16/10/2026. TV2 đã `git fetch --prune origin` và đối chiếu trực tiếp
remote heads bằng `git ls-remote --heads origin`. Không sửa nhánh TV1.

`origin/feat/metadata-split` hiện trỏ tới
`468d81f7272a4497d8b54a53a3651fd13c6dfbc2`, đúng bằng `origin/main`.
Không còn remote branch `codex/tv1-week2-download-quality`. Tìm trên toàn bộ
refs đã fetch không thấy `data/processed/comparison_v1`,
`scripts/freeze_comparison.py`, `docs/handoff_tv1_w3.md` hoặc
`reports/tv1_w3`. Vì vậy W3-01 chưa được bàn giao trên Git.

Main có W2 v2 đã tích hợp. Đây là bằng chứng W2, không tự động trở thành bộ dữ
liệu so sánh đã khóa cho W3:

| Thuộc tính W2 v2 | Giá trị kiểm tra |
|---|---|
| Manifest SHA-256 | `5f957ea6004d9a8d468bd111bae2a7a2ffb29ffef295cde33c0df1a8ff3454cc` |
| Train SHA-256 | `537d467f7f0ec1ea9fb6a182a37caf0ca1b4f572818789eb6a8c7fc118ef0a11` |
| Validation SHA-256 | `4a18d30378619a39a317af93e1a375ba95162b234380cbf373f26308ac0dfd34` |
| Accepted / excluded | 4.000 / 0 |
| Train / validation / test | 2.800 / 600 / 600 |
| Exact duplicate giữa split | 0 theo integrity report TV1 |
| Perceptual duplicate | Chưa kiểm tra |
| Ảnh cục bộ được decode lại trong lượt tích hợp | Không |

TV2 chỉ đọc số đếm và integrity attestation; không mở dòng manifest hoặc pixel
của test. Bằng chứng remote được lưu tại
[remote_audit_2026-10-16.json](w3_evidence/remote_audit_2026-10-16.json).

| Tiêu chí W3-01 | Trạng thái |
|---|---|
| Freeze receipt có version/commit/hash | BLOCKED — không có trên remote |
| Train/val source và eligible manifest | BLOCKED — chưa bàn giao W3 |
| Class map cố định | Có W2 v2; chưa có receipt W3 |
| Ledger kept/excluded và lý do | BLOCKED — chưa có artifact W3 |
| QA ảnh/nhãn/bbox | BLOCKED — chưa có báo cáo W3 |
| Leakage toàn bộ split | Có attestation exact-duplicate W2; perceptual chưa kiểm tra |
| Cùng image IDs/split cho B1 và B2 | BLOCKED — chưa có comparison manifest |
| Crop mapping thống nhất với TV3 | BLOCKED — chưa có handoff W3 |

TV1 cần push commit chứa bộ `comparison_v1` hoặc tên phiên bản chính thức,
freeze receipt, hashes, provenance, ledger loại, QA và handoff. Sau đó TV2 mới
có thể đối chiếu byte/hash, membership, mapping, train/val leakage, decode ảnh
và crop coverage bằng gate hiện có. Không được đổi config để dùng W2 v2 làm
fallback hoặc tự ghi receipt thay TV1.

**Final: BLOCKED — W3-01 HANDOFF NOT PRESENT ON REMOTE.**
