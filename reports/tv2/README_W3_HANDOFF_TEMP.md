# TV2 W3 handoff

Ngày 18/10/2026. Trạng thái:
**B1 CHECKPOINT HANDOFF VERIFIED – B1/B2 COMPARISON PENDING OFFICIAL B2**.

## Git refs

- main: `468d81f7272a4497d8b54a53a3651fd13c6dfbc2`
- TV1 frozen data: `7e9b1949f10126fbcfa83fa12baeca488b6aeab3`
- TV2 code/config chạy B1: `d81f584c50c9f2724ad545ef30940079bd7c1b89`
- TV2 kết quả trước cập nhật bàn giao: `f6593d52f2f12c3f001cc9cc41cfb272f7d90b7d`
- TV3 mới nhất đã review: `c01a75141bb8350c8a38a28cfc9b44a3f3ad12ba`

## Handoff table

| Task | Status | Evidence | Next step / owner |
|---|---|---|---|
| TV1 data/provenance | PASS | B1 data gate, frozen commit | Không sửa bundle |
| Protocol/runtime authorization | AGREED/BOUND | `W3_PROTOCOL_AND_RUNTIME_AUTHORIZATION_2026-10-18.json` | Không đổi config/run đã khóa |
| B1 official training | COMPLETED | `experiments/B1_run01/status.json` | Giữ nguyên run |
| B1 validation/reload local | PASS | `continuation_03/b1_run01_verification.json` | Không dùng test để tuning |
| B1 Google Drive bytes/hash | PASS | `continuation_04/remote_checkpoint_verification.json` | TV4 kiểm hash lại sau tải |
| B1 Google Drive validator | PASS | `continuation_04/remote_drive_validator.json` | TV4 vẫn kiểm hash khi tải |
| B2 implementation | BLOCKED PENDING TV3 FIX | `TV2_REVIEW_TV3_W3.md` | TV3 sửa 4 P1 và phát hành commit mới |
| B2 official run/reload | NOT AVAILABLE | Không có artifact trên nhánh TV3 | TV3 train và bàn giao |
| B1/B2 comparison | PENDING | `TV2_W3_COMPARISON.md` | Chỉ so khi B2 official/reload PASS |

## B1 checkpoint for TV4

- Download: [Google Drive best_model.pth](https://drive.google.com/file/d/19efNKKDz0IwhoUYGrBr5X9fI_CnQ-EPq/view?usp=sharing)
- Size: 44.815.625 byte.
- SHA-256: `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c`.
- Model: ResNet18 `IMAGENET1K_V1`, full fine-tune, 8 outputs, no dropout.
- Best epoch: 22; run dừng ở epoch 29 theo patience 7.
- Validation Macro-F1 `0,5624506868`; precision `0,5748610369`;
  recall/accuracy `0,565`; loss `1,3379992723`.
- Validation preprocessing: RGB, resize 256, center crop 224, ImageNet mean/std.
- Class order: `large_antlered_muntjac`, `annamite_striped_rabbit`, `sambar`,
  `chinese_serow`, `common_palm_civet`, `masked_palm_civet`, `silver_pheasant`,
  `eurasian_wild_pig`.

TV4 phải kiểm cả size và SHA-256 trước khi load. Nếu checkpoint, class mapping
hoặc provenance sai, phải dừng thay vì cố chạy. Chi tiết đầy đủ ở
[checkpoint handoff](TV2_W3_CHECKPOINT.md).

## B2 blockers

TV3 chưa bật source-image hash trong official config; grouped loss chỉ đúng trong
từng batch trong khi crop bị shuffle; official output có thể bị ghi đè; và chưa
có fresh-process reload. Nhánh không chứa official B2 checkpoint/log/metrics.
Do đó chưa thể tính chênh lệch B1/B2 hoặc chọn model thắng.

## Acceptance boundary

Tập test không được dùng để chọn checkpoint hoặc so sánh trong W3. Handoff này
xác nhận artifact B1 và các điều kiện còn thiếu; không phải `READY FOR SUBMISSION`,
không phải nghiệm thu reviewer và không cho phép merge tự động.
