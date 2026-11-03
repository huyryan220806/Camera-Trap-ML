# TV1 tuần 6 — bàn giao train mở rộng để so với DINO W5

**Ngày bắt đầu:** 03/11/2026. **Nhánh:** `feat/metadata-split`.
**Người kiểm tra tiếp theo:** TV2. Trạng thái nghiệm thu, counts và SHA cuối
cùng nằm trong [báo cáo](../reports/tv1_w6/REPORT.md);
[progress](progress_tv1_w6.md) ghi bước hiện tại. Không coi file hướng dẫn này
là bằng chứng dữ liệu đã đạt hoặc TV2 đã duyệt.

**Đã phát hành local ngày 03/11:** thêm 1.446 ảnh, cách ly 219; train mới
4.246 ảnh / 4.729 crop. Chất lượng kỹ thuật đã kiểm định; TV2 chưa peer review.
Phân bố val/Test cũ giữ nguyên. Chi tiết và giới hạn rà mẫu trong báo cáo.

## TV2 nhận và kiểm tra

1. Cập nhật code, `configs/train_expansion_w6_v1.json` và snapshot
   `data/processed/train_expansion_w6_v1/` từ nhánh TV1 khi đã được push.
2. Xác minh độc lập từ snapshot, không cần state tải của TV1:

   ```powershell
   .venv/Scripts/python.exe -m pip install -r requirements-data-w6.txt
   .venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w6.py verify
   ```

   Môi trường tạo bản: Python 3.12.10, NumPy 2.5.3, Pillow 12.2.0,
   SciPy 1.18.1. Dùng môi trường dữ liệu riêng nếu môi trường train của TV2
   có pin khác; không nâng cấp gói trong runtime mô hình đang dùng để replay.
3. Đọc `summary.json`, `excluded.jsonl`, `decisions.jsonl`, `audit.json`,
   `near_duplicates.json`, `visual_review.json` và `provenance.json`.
   Kiểm tra đủ 1.665 quyết định và các ảnh cũ không đổi; nguyên nhân loại phải
   là chất lượng/trùng/mơ hồ, không phải model dự đoán sai.
4. Khi có ảnh local đúng cấu trúc, thêm `--check-images` để giải mã/đối chiếu
   byte và RGB SHA toàn bộ ảnh cũ, ảnh train mới được giữ và holdout đối chiếu.
5. Ghi review riêng có SHA `provenance.json` và PASS/FAIL; không sửa
   `peer_review_status` trong snapshot đã khóa. Snapshot có `quality_ready`
   không đồng nghĩa một thành viên khác đã nghiệm thu.

## TV3 dùng dữ liệu nào?

| Thí nghiệm | Train | Validation |
| --- | --- | --- |
| R1/R2, kiểm tra seed trên dữ liệu cũ | `data/processed/comparison_v1/b2/train.jsonl` | `data/processed/comparison_v1/b2/val.jsonl` |
| R5/R6 có điều kiện, sau TV2 review | `data/processed/train_expansion_w6_v1/b2/train.jsonl` | **Cùng val cũ ở trên** |

Không chạy R5/R6 trước protocol W6 và review dữ liệu. Không đưa trực tiếp
`w5_candidates_v1/train_extension_candidates.jsonl` vào loader. **Code train
W5 chưa hỗ trợ release mở rộng**; TV3 phải viết loader/config W6 theo
[plan TV3](plans/TV3_W6.md), giữ nguyên code/source SHA W5.

`quality.local_path` là đường dẫn tương đối từ gốc repo. Ảnh gốc pilot vẫn ở
`data/images/swg_pilot_v2/`; ảnh mới ở `data/images/swg_w5_extension/`. Nhãn,
class ID, split, tọa độ nguyên gốc giữ nguyên; `bbox_xyxy` và crop weight theo
quy tắc comparison cũ. Mỗi ảnh đóng góp loss ngang nhau; không nhân weight
một lần trong loader rồi thêm lần nữa trong training loop.

Train mở rộng mất cân bằng. So cùng recipe/seed giữa train cũ và train mới;
không đồng thời thêm class weight/sampler để rồi quy toàn bộ hiệu quả cho dữ
liệu. Mục tiêu ≥88% là giả thuyết thử nghiệm, không phải bảo đảm của release.

## Tải lại ảnh và tiếp tục

Ảnh/trọng số không nằm trên GitHub. Máy này đã có thư mục ảnh khi tải hoàn
tất; nếu chuyển sang máy khác, chép đúng cây thư mục hoặc chạy lệnh tải nguồn
ứng viên như dưới. Lệnh có thể tải cả ảnh bị cách ly; **loader chỉ đọc manifest
đã phát hành**, không quét toàn bộ thư mục để huấn luyện.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/download_subset.py --source data/processed/w5_candidates_v1/train_extension_candidates.jsonl --images data/images/swg_w5_extension --state data/interim/download_w5_extension --log outputs/tv1_w6/train_download_events.jsonl --workers 4
```

Nếu cần kiểm tra ảnh holdout để tái lập audit, dùng lệnh riêng trong progress.
109 ảnh đó chỉ làm đối chiếu nội dung, chưa đủ hỗ trợ cho test mới, không đưa
vào train/val hoặc đánh giá mô hình. Không lấy ảnh Test cũ để chọn checkpoint.

Gói đã tạo trên máy TV1, **chưa upload cloud**:

- `outputs/tv1_w6/swg_train_expansion_w6_v1_additional.zip`: 2.246.204.406 byte,
  gồm 1.446 ảnh được giữ và snapshot. [SHA và nội dung](../reports/tv1_w6/image_package.json).
  Giải nén tại gốc repo để có đúng `data/images/...` và `data/processed/...`;
  vẫn cần `swg_pilot_v2` cũ riêng. Không chứa ảnh holdout hoặc ảnh cách ly.
- `outputs/tv1_w6/visual_review_contact_sheets.zip`: các hình đối chiếu của
  80 mẫu để TV2 xem quyết định; [SHA](../reports/tv1_w6/visual_package.json).

Lệnh tạo lại/kiểm tra gói ảnh: `.venv/Scripts/python.exe scripts/package_tv1_w6.py`.
Nếu gói đã tồn tại, đối chiếu hash rồi dùng lại; không tự ghi đè một gói bị thay đổi.

Pipeline TV1 có thể tiếp tục bằng:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/resume_tv1_w6.ps1
```

Wrapper từ chối writer khác còn chạy; sau khi đã phát hành chỉ kiểm tra lại,
không ghi đè. Nếu mất state nhưng đã có snapshot, `verify` vẫn chạy được.
Rà trực quan không được tự đánh dấu xong: lệnh `sheets` tạo hình đối chiếu,
bản ghi phải có đúng ID/SHA/quan sát/giữ hoặc cách ly. Đổi quy tắc → phiên
bản mới, không chỉnh SHA để vượt kiểm định.

## TV4 và nhóm nhận gì?

TV4 ghi dataset ID của checkpoint được nhận; không cần thay detector hoặc
UI để tải dữ liệu train. Mô hình được chọn vẫn cần TV2 replay và TV4 kiểm tra
adapter. Bốn kế hoạch: [TV1](plans/TV1_W6.md), [TV2](plans/TV2_W6.md),
[TV3](plans/TV3_W6.md), [TV4](plans/TV4_W6.md).

Việc chưa thể tự hoàn tất thay các thành viên: TV2 peer review, TV3 huấn luyện
và TV4 tích hợp. Bằng chứng TV1 chỉ kết luận về dữ liệu; không tự công bố model
mới đã tốt hơn `DINOv3_LP_run01`.
