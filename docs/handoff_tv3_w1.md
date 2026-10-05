# Bàn giao tuần 1 - TV3 (Crop classifier EDA)

Nhánh: `feat/crop-classifier`. Phạm vi: kiểm tra metadata box và xem trực quan mẫu **chỉ từ train** trước khi làm crop classifier.

## File bàn giao

| File | Nội dung |
|---|---|
| `notebooks/crop_classifier_eda.ipynb` | Notebook chạy toàn bộ phần EDA của TV3 (không lưu output trong notebook) |
| `scripts/tv3_crop_eda.py` | Logic quét metadata, lấy mẫu, tải và vẽ ảnh; dùng `valid_bbox` từ `scripts/prepare_swg.py` (không giữ bản sao) |
| `tests/test_tv3_crop_eda.py` | 13 test dùng dữ liệu tổng hợp, gồm tải thất bại toàn bộ và không có mẫu; không tải ảnh, không dùng ảnh test |
| `reports/tv3/sampled_audit.json` | 80 ảnh mẫu: image ID, loài, split, location, sequence, URL, SHA-256, trạng thái; seed 42; SHA-256 và commit của train manifest |
| `reports/tv3/bien_ban_loi_w1.json` | Thống kê box metadata, kết quả tải mẫu theo loài, danh sách lỗi và giới hạn |
| `reports/tv3/<loài>/NN_<id>_bbox.jpg`, `grid_<loài>.png` | Hình minh họa box cho 8 lớp (10 ảnh/lớp + 1 lưới) |

Ảnh gốc `reports/tv3/**/*_raw.jpg` chỉ lưu cục bộ, bị `.gitignore` bỏ qua.

## Chạy lại (Windows, Python 3.12)

Chạy từ thư mục gốc repo, sau khi đã cài `requirements.txt` và tải metadata bằng `scripts/download_metadata.py`
(cần `data/raw/swg_camera_traps.bounding_boxes.with_species.zip`). `data/processed/v1/train.jsonl` đã có trong repo.

```powershell
.venv/Scripts/python.exe -m unittest tests.test_tv3_crop_eda -v
```

Sau đó mở `notebooks/crop_classifier_eda.ipynb` (kernel `.venv`) và chạy tuần tự các cell. Notebook tự tìm thư mục gốc
repo nên mở từ thư mục nào cũng được. Bước lấy mẫu cần Internet để tải 80 ảnh từ Google Cloud Storage; không cần GPU.

## Kết quả lần chạy 03/10/2026

**Thống kê box** - phạm vi: toàn bộ 133.837 annotation trong file box metadata gốc (mọi split, mọi loài);
đọc bằng `ijson` với `use_float=True`, áp dụng `valid_bbox` của TV1:

| Trạng thái | Số lượng |
|---|---:|
| Box hợp lệ (`valid`) | 101.384 |
| Thiếu bbox (`no_bbox`) | 32.178 |
| Lỗi hình học (`outside_or_nonpositive_bbox`) | 275 |
| Ảnh đánh dấu `corrupt` (trong 120.321 ảnh của file box) | 0 |

**Mẫu ảnh** - nguồn: chỉ `data/processed/v1/train.jsonl` (commit `9d5eb1a`, SHA-256 `c2473cd1…32d8`), seed 42,
xoay vòng theo location đã xáo trộn của từng lớp:

- Chọn 80 ảnh (10/lớp × 8 lớp); lưu thành công 80; lỗi tải 0; lỗi giải mã 0.
- Cả 80 ID được đối chiếu lại với train manifest (không chỉ dựa vào trường `split` trong log); không có ID trùng.
- Không có ảnh trùng byte (SHA-256) trong 80 ảnh mẫu.

## Giới hạn

- SHA-256 chỉ so trùng byte giữa 80 ảnh mẫu của lần chạy này; **không** kết luận toàn dataset hay giữa các split không có ảnh trùng/gần giống.
- Hình bbox mới được xem để minh họa; chưa kiểm tra trực quan có hệ thống chất lượng box của toàn bộ train.
- Số liệu box ở trên là của file metadata box gốc, khác phạm vi manifest v1 (đã lọc theo 8 lớp và điều kiện của TV1).
