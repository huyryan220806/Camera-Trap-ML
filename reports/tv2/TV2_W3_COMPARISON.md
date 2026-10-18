# TV2 W3 B1/B2 comparison — COMPARISON PENDING

## Cập nhật CONTINUATION_02 – 18/10/2026

Trạng thái mới nhất: **W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**. TV1 `7e9b1949f10126fbcfa83fa12baeca488b6aeab3` đã phát hành;
provenance/native adapter và full train/val preflight PASS; 3.400 ảnh đã kiểm byte/pixel
hash/decode. Protocol đã được người dùng xác nhận cụ thể cho nhóm. CUDA batch32 smoke
PASS trong venv riêng; 87/87 regression PASS. Chưa có budget/window và official
environment freeze, chưa train/validation/checkpoint B1 thật. TV3 vẫn d08eba7 cần sửa.
Xem [báo cáo mới](TV2_W3_CONTINUATION_02_REPORT.md) và [README bàn giao](README_W3_HANDOFF_TEMP.md).
Các phần bên dưới giữ làm lịch sử; các kết luận cũ “TV1 chưa push”, “chưa có cache”,
“chưa thống nhất thông số” không còn là trạng thái hiện tại.

Continuation 01, 16/10/2026: fetch lại xác nhận TV1/TV3 chưa có handoff mới;
B1 full suite mới 78/78 PASS, official training chưa chạy. **B1/B2 COMPARISON
PENDING**. Nguồn trạng thái và owner: [README tạm](README_W3_HANDOFF_TEMP.md).

| Điều kiện / metric | B1 full image | B2 crop |
|---|---|---|
| Code | Sẵn sàng trên `feat/baseline` | Có tại TV3 commit `d08eba7`; review FAIL |
| Synthetic tests | 26/26 B1 PASS; full suite 78/78 | 9/9 TV3 snapshot PASS |
| Frozen W3 data | Chưa có | `comparison_v1` chưa có trên remote |
| Agreed protocol | PROPOSED | Chưa đồng thuận; config đang khác B1 |
| Training / validation chính thức | Chưa chạy | Chưa chạy; official gate exit 1 |
| Macro-F1 / precision / recall / accuracy | N/A | N/A |
| Per-class F1 / best epoch | N/A | N/A |
| Runtime / peak GPU memory / val support | N/A | N/A |

Same eligible images / split / protocol: **chưa xác nhận**. Tập W2 hiện khác
nhau; số lượng và giao ID ở hai báo cáo cross-review. Chênh lệch macro-F1: N/A.
Không chọn mô hình thắng, không dùng B0 pilot hay synthetic smoke thay số B1.

Chưa thể kết luận tác dụng của crop hoặc lớp nào cải thiện/suy giảm. Khi đủ
điều kiện, so cùng đơn vị ảnh nguồn, paired IDs, per-class support và budget;
ghi hạn chế multiple-box aggregation, nhãn cấp sequence và domain/location shift.
W4 chỉ là hướng đề xuất: sau khi hai baseline được kiểm định, xem lỗi validation
để quyết định thử nghiệm được nhóm duyệt. Không triển khai B3 hoặc mở test ở W3.

Trạng thái B2 hiện tại: **BLOCKED; CODE REVIEW FAIL**. Các lỗi đường dẫn dữ liệu,
preflight, best checkpoint/epoch, run immutability, reload và protocol được liệt
kê trong [TV2_REVIEW_TV3_W3.md](TV2_REVIEW_TV3_W3.md).
