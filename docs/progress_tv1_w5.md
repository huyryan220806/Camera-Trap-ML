# TV1 tuần 5 — tiến độ và cách tiếp tục

Ngày bắt đầu: 28/10/2026 (giờ Việt Nam). Phạm vi: kiểm kê train bổ sung,
manifest ứng viên, kiểm tra khả năng có test mới và phần dữ liệu báo cáo;
tạo ba kế hoạch riêng cho TV2/TV3/TV4 tuần 5–6.

## Hoàn thành

- Nền mã `60516f5`, nhánh cố định `feat/metadata-split`; bàn giao nhánh theo yêu cầu push tiếp theo của TV1 ngày 28/10/2026.
- `comparison_v1` có 4.000 ảnh, split 2.800/600/600. Giữ nguyên toàn bộ dữ liệu khóa.
- Nguồn v1 gồm 31.589 ảnh. Đã lọc geometry giống comparison_v1 và đối chiếu
  16 manifest/log B0/crop; ghi đủ quyết định của mọi ID nguồn.
- 19.266 ảnh train ứng viên; chọn 1.665 ảnh/1.665 chuỗi mới so với pilot,
  tối đa 250/lớp, round-robin địa điểm với SHA-256/seed 42.
- 9 ảnh không đạt cạnh crop 8 px (7 train, 2 val), không thuộc pilot cũ.
- Holdout ở địa điểm chưa có trong hồ sơ chỉ 109 ảnh/50 chuỗi/21 địa điểm;
  thỏ vằn 1 ảnh. Trạng thái `NOT_READY_INSUFFICIENT_SUPPORT`; chưa có test mới.
- Snapshot metadata `data/processed/w5_candidates_v1/` thuộc gói bàn giao;
  SHA provenance: `37db148ec716e5666431eca6f78a3440651f63c9359779dc456fd9decd26cd07`.
- Chạy lại và verify-only giữ nguyên snapshot; audit độc lập PASS, 0 giao
  ID/đường dẫn/chuỗi/địa điểm qua các tập, 0 đổi nhãn/split/byte nguồn khóa.
- 12 kiểm thử mới PASS; toàn bộ **389/389 PASS**, 106,401 giây. Môi trường CPU
  và 6 fixture JSON PASS. Bằng chứng ở `reports/tv1_w5/`.
- Đã viết `docs/handoff_tv1_w5.md`, `reports/tv1_w5/REPORT.md`, `DATA_CHAPTER.md`
  và đúng ba plan thành viên `docs/plans/TV2_W5_W6.md`, `TV3_W5_W6.md`, `TV4_W5_W6.md`.
- Remote TV4 đã có commit `fef2511` (UI code `0179d97`). Kế hoạch TV4 phải
  tiếp nối bản đã push; chưa coi là TV2 đã nghiệm thu hoặc đã merge main.

## Phạm vi chưa thực hiện, đã ghi rõ trong bàn giao

Không tải 1.665 ảnh mới; không phát hành train mở rộng có quality/crop view;
không huấn luyện hoặc suy luận trên Test. Đây không phải phần còn dở của
kiểm kê metadata W5: chỉ mở đợt tải/kiểm định mới nếu nhóm chọn thí nghiệm train
mở rộng. Lượt DINO đầu dùng train/val comparison_v1 hiện có.

Chưa có nghiệm thu TV2 cho bàn giao W5 và chưa merge vào `main`. Các plan
đã tạo không đồng nghĩa thành viên đã hoàn thành tuần 5/6.

## Bàn giao qua GitHub

Nhánh công bố: [feat/metadata-split](https://github.com/huyryan220806/Camera-Trap-ML/tree/feat/metadata-split).
Gói gồm công cụ/config W5, snapshot ứng viên, kiểm thử và bằng chứng, báo cáo,
bàn giao TV1, ba plan W5/W6, lịch GPU cập nhật và tài liệu TV4 trở lại được các
plan tham chiếu. Không kèm ảnh, weights, state hoặc các slide/báo cáo local
không thuộc đợt bàn giao này. TV2/TV3/TV4 nhận cả commit trên nhánh TV1 trước
khi chạy lệnh W5, không lấy riêng một manifest thiếu config/validator.

## Khi tiếp tục

Đọc file này, `git status`, các file mới dưới `scripts/`, `configs/`,
`data/processed/w5_candidates_v1/`, `reports/tv1_w5/`, và
`outputs/tv1_w5/`. Không xóa state hay ghi đè bản dữ liệu khóa.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w5.py
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w5.py --verify-only --report outputs/tv1_w5/verify_again.json
```

Nếu đã có snapshot, lệnh chỉ đối chiếu, không ghi đè. Nếu dừng giữa staging,
chạy lại cùng nguồn/config để tiếp tục. Nếu builder/nguồn đổi, giữ nguyên
receipt và xem diff, không xóa checksum để tạo lại cùng tên.

Nhánh TV1 đã được chuyển về workspace chính. Worktree review-tv2-week2 cũ
được giữ nguyên tại commit `60516f5`, trạng thái detached và sạch trước khi
chuyển nhánh; không xóa checkout. Các báo cáo/slide local cũ không thuộc thay
đổi dữ liệu W5; không stage hàng loạt.
