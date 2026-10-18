# TV2 W3 handoff

Ngày 18/10/2026. Trạng thái: **W3-02 B1 TRAINED – B1/B2 COMPARISON PENDING**.

## Git refs

- main: `468d81f7272a4497d8b54a53a3651fd13c6dfbc2`
- TV1: `7e9b1949f10126fbcfa83fa12baeca488b6aeab3`
- TV2 code/config chạy B1: `d81f584`
- TV3 mới nhất đã review: `c01a75141bb8350c8a38a28cfc9b44a3f3ad12ba`

## Handoff table

| Task | Status | Evidence | Next step / owner |
|---|---|---|---|
| TV1 data/provenance | PASS | Continuation 02 + B1 data gate | Không sửa bundle |
| Protocol/runtime authorization | AGREED/BOUND | `W3_PROTOCOL_AND_RUNTIME_AUTHORIZATION_2026-10-18.json` | Không đổi config của run đã hoàn tất |
| B1 official training | COMPLETED | `experiments/B1_run01/status.json` | Review kết quả |
| B1 validation/reload | PASS | `w3_evidence/continuation_03/b1_run01_verification.json` | Không dùng test để tuning |
| B1 checkpoint | LOCAL VERIFIED | `TV2_W3_CHECKPOINT.md` | Nhóm chỉ định kho upload; TV2 upload/hash lại |
| B2 implementation | BLOCKED PENDING TV3 FIX | `TV2_REVIEW_TV3_W3.md` | TV3 sửa 4 P1 và phát hành commit mới |
| B1/B2 comparison | PENDING | `TV2_W3_COMPARISON.md` | Chỉ so khi B2 official/reload PASS |

## B1 result

- 29 epoch, best epoch 22, early stopping patience 7.
- Macro-F1 `0.5624506868`; precision `0.5748610369`; recall/accuracy `0.565`.
- Peak GPU memory 895.525.376 byte.
- Checkpoint 44.815.625 byte, SHA-256
  `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c`.
- Reload nội bộ và process mới PASS; mọi delta bằng 0.
- Test rows opened: false.

## Còn thiếu

- URL checkpoint chưa có vì chưa được chỉ định kho artifact.
- TV3 cần sửa và chạy B2 chính thức; chưa có metric B2 hợp lệ.
- Không có nghiệm thu độc lập cuối cùng và chưa merge PR.

Chi tiết đầy đủ: [Continuation 03](TV2_W3_CONTINUATION_03_REPORT.md).
