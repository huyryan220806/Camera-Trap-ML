# Tiến độ kiểm tra W5 — 02/11/2026

**Hoàn tất kiểm tra TV2/TV3/TV4.** Người dùng ban đầu nói W4 rồi sửa thành W5. Đọc [biên bản tổng hợp](../reports/review_w5_2026-11-02/REPORT.md) và ba biên bản TV2/TV3/TV4 cùng thư mục.

- TV1 workspace vẫn ở `feat/metadata-split` `9abc9c5`; `main` vẫn `60516f5`.
- Đầu remote đã fetch và xác minh lại: TV2 `df31029`, TV3 `5734d38`, TV4 `8d4a255`.
- Snapshot nguyên byte mỗi nhánh, intake/checkpoint thật và bản cây gộp thử ở `outputs/review_w5_2026-11-02/`. Không switch/reset hoặc sửa branch thành viên.
- ZIP DINO người dùng cung cấp ở `reports/tv3_w5/`; chưa theo dõi Git. Không stage ZIP này khi push báo cáo.
- ZIP 27 payload PASS; kiểm checkpoint/source/log/protocol; audit đủ600ảnh/680crop khớp accuracy84,50%,macro-F1 84,44%. Gói model đã đạt, chưa đạt mục tiêu88%.
- 32 TV2 +16 TV3 +47 TV4 tests PASS; cây kết hợp bốn nhánh không conflict,440/440tests PASS. Cây gộp chỉ là object/snapshot kiểm tra, chưa là merge nhánh.
- Native/adapter CPU exact, delta0; browser MD+DINO thật, B2 thật, CSV/lô/review/error/resize PASS. Full-validation replay TV2 đã công bố được đối chiếu artifact; không forward lại600ảnh tại TV1 hoặc chạy Test chính thức.
- Evidence đủ dùng bàn giao được chép vào `reports/review_w5_2026-11-02/evidence/`, có index SHA. Screenshots/ảnh/checkpoint/journal QA giữ local.
- Hai attempt browser đầu lỗi bố trí junction snapshot; copy riêng ảnh/weights rồi PASS. Log cũ giữ nguyên. Một attempt batch thiếu thư mục output cha; tạo thư mục rồi PASS. Đây là lỗi thiết lập review, không sửa code hoặc gọi là lỗi sản phẩm.
- Không thực hiện training experiment, sửa nhãn/split, push, merge hoặc gửi review/comment cho người khác.

## Khi tiếp tục

Không chạy lại các kiểm tra đã hoàn tất nếu source/checkpoint không đổi. Nếu chỉ yêu cầu push, stage riêng thư mục báo cáo và file progress này, kiểm hash/link rồi push nhánh TV1. Không `git add .` vì workspace còn slide, notebook, ZIP và báo cáo cũ ngoài scope.

Nếu người dùng yêu cầu merge: fetch lại, đối chiếu ba SHA; nếu có commit mới phải review phần thay đổi. Giữ bốn branch cố định; cập nhật trạng thái tài liệu với kết quả mới; không xóa hoặc đổi byte evidence đã khóa. Không tự chạy lại official Test để nghiệm thu.

PR8 đã đọc API: OPEN,mergeable=true,head8d4a255; review trong API chỉ COMMENTED ở commit cũ0179d97. Chưa gửi APPROVED thay TV2. Bản kiểm tra này là của TV1 theo yêu cầu người dùng.

Server review dùng cổng8876 và thư mục snapshot TV4, không phải demo sản xuất. Trước khi dùng lại xem trạng thái cổng/PID; giữ journal QA. Chi tiết lệnh ở log và scripts trong outputs. Trạng thái server cuối lượt được ghi trong `outputs/review_w5_2026-11-02/final_state.json`.
