# TV2 W6 — kiểm tra gate approval R1/R2 ngày 06/11/2026

**BLOCKED — thiếu bằng chứng approval riêng của TV3.** Không chuyển protocol
hoặc registry sang `APPROVED`; không cho chạy official R1/R2. Người dùng thông
báo TV3 đã xác nhận riêng, nhưng chưa cung cấp link/receipt/commit chứa lời
xác nhận để TV2 kiểm và dẫn chiếu. Báo cáo này không phủ nhận thông báo đó;
nó ghi đúng tình trạng bằng chứng có thể truy vết tại thời điểm kiểm tra.

## Git và receipt TV2

- Chỉ đọc trên `feat/baseline` HEAD
  `73bc9c2b69f202f123657db4b9dbf128810732f3`; tracked working tree sạch.
  Các file untracked cá nhân giữ nguyên. Fetch `feat/crop-classifier` và
  `feat/baseline` không đổi HEAD local.
- TV2 receipt đã commit tại HEAD:
  `reports/tv2/TV2_W6_TV2_TECHNICAL_APPROVAL_2026-11-06.md`, raw SHA-256
  `aaad710bfb2106712d693c4a88daa1c7142f01d5b5c295dd5ea2b650b1232ee3`.
  Receipt trích lời TV2 chấp thuận kỹ thuật có điều kiện; chính receipt ghi
  TV3 approval PENDING và official training NOT AUTHORIZED. Review được gắn:
  `reports/tv2/TV2_W6_TV3_PRETRAIN_REVIEW_2026-11-06.md`, raw SHA-256
  `48c2c24bb01da224f410c5ffa6d68afa4677f5751bc8d187746b21d1eb228707`,
  kết luận `READY_FOR_TV2_DECISION`.

## Binding kỹ thuật đã kiểm lại

| Mục | Kết quả |
| --- | --- |
| Remote TV3 handoff | `8cd97538390a3f55c66193d79e637dfd73ace770`, vẫn là `origin/feat/crop-classifier` sau fetch |
| Source commit | `127cac5b64d37fdda630a2f84b006a8e420dc9ed`; config và smoke cùng pin source này |
| ZIP | Raw SHA-256 `030093e92f07fcbe9a2a7ed39eb60919d66250181cd6c0dd9278106927e21ce7`, CRC PASS |
| R1 frozen canonical | `2ab03b7e13d798b8aace5e4b3542a189389c43c7630f4132303b9200fced63bf`; bytes config khớp Git handoff |
| R2 frozen canonical | `55dea8ab328e43581642deb964631d391a5b88596feb191a5fa5911a7a94acb7`; bytes config khớp Git handoff |
| Runtime lock canonical | Cả hai: `7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a`, tính từ runtime trong smoke |
| R1/R2 smoke | Raw SHA lần lượt `9d5418745cf2cd45519415935246cb3be6ee6b5f0349341b9accb821b2cca1f6` và `6b7ead35a2bfbfb002154db14d992c2fd3ececfe3bf3c546be6bdb62433279e5`; bytes khớp Git handoff |

Phép kiểm lại là artifact/hash-only, không chạy model/GPU/Test. Bằng chứng D2
chi tiết nằm ở `reports/tv2/w6_evidence/d2_20261106_01/`.

## Bằng chứng approval TV3 còn thiếu

Đã xem remote branch sau fetch, cây `reports/tv3/w6/`, handoff summary,
repo/local TV3 handoff ZIP và các file liên quan trong thư mục bàn giao.
Handoff ZIP chứa proposal với `approvals.TV3=null`; `handoff_summary.json`
yêu cầu TV2 review và trả về approval. Smoke `status=PASS`, source commit và
author của commit **không phải** lời TV3 chấp thuận R1/R2 frozen. Không có
receipt/commit/PR comment có nội dung xác nhận TV3 và pin đồng thời R1/R2
config, source, runtime, smoke được tìm thấy trong các nguồn này. TV3 approval
W5 ngày 30/10 không áp dụng cho recipe/config W6.

Cần TV3 cung cấp lời xác nhận thực tế có nguồn truy vết (đường dẫn tệp và
commit, PR comment URL, hoặc receipt nguồn) nêu rõ TV3 chấp thuận **cả R1 và
R2** cùng các canonical config SHA, source commit, runtime lock và smoke SHA ở
bảng trên. TV2 sẽ kiểm nguồn và hash trước khi ghi approval; không tạo receipt
thay TV3. Booking GPU thực và budget cần được xác nhận trước execution.

## Trạng thái giữ nguyên

`docs/experiment_protocol_w6.md` vẫn DRAFT;
`experiments/w6/registry.json` vẫn `protocol_status=DRAFT`, global/per-run
`approvals.TV3=null` và `approvals.TV2=null`. R1/R2 `REGISTERED` nhưng
`attempts=[]`. R3/R4 conditional; R5/R6 còn chặn vì TV1 data review PENDING.
CLI `scripts/evaluate_w6_validation.py --registry experiments/w6/registry.json`
trả `VALID / DRAFT / 0 official attempts`; `VALID` là schema/semantic DRAFT,
không phải giấy phép training. Registry TV2 chưa nhập hai smoke GPU seconds từ
proposal TV3 vì chưa tiến hành approval freeze.
Không có thay đổi W1–W5, nhánh TV3, official training hay merge.
