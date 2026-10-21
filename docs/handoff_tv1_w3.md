# TV1 tuần 3 - Khóa dữ liệu so sánh B1/B2

## Phạm Vi

Nhánh bàn giao trên GitHub: **`feat/metadata-split`**. Bản `main` tuần 2 chưa
có `comparison_v1`. TV2/TV3 commit hoặc cất giữ công việc đang làm, sau đó
`git fetch origin` và `git merge origin/feat/metadata-split` trên nhánh của mình.
Không reset nhánh hoặc chỉ lấy riêng một manifest thiếu code/validator đi kèm.

Khóa bản **`comparison_v1`** từ pilot 4.000 ảnh đã tải và kiểm định ở tuần 2
(`data/processed/v2`). Đây là phiên bản đầu của **dữ liệu so sánh**, không phải
ghi đè `data/processed/v1` hay đổi tên manifest v2 cũ.

Giữ nguyên seed 42, nhãn, ID, chuỗi, địa điểm và split. Không lấy mẫu lại,
không bù ảnh, không dùng dự đoán của mô hình để chọn ảnh. Pilot được cân bằng
có chủ đích từ tuần 1, không đại diện phân bố tự nhiên của toàn SWG.

## Tiêu Chí Và Sản Phẩm

| Tiêu chí | Cách thực hiện | File bàn giao |
| --- | --- | --- |
| B1/B2 cùng ảnh đủ điều kiện | Sinh cả hai view từ một danh sách đã lọc, validator đối chiếu từng dòng | `manifest.jsonl`, `b1/*.jsonl`, `b2/*.jsonl` |
| Một loài xác định | Nhãn ảnh trong class map; mọi box có cùng nhãn đó | `policy.json`, `excluded.jsonl` |
| Không rò rỉ chuỗi/địa điểm | Kiểm tra trên nguồn và trên tập giữ lại; phát hiện là dừng, không tự chia lại | `audit.json` |
| Thống kê giữ/loại | Tổng, từng split và lớp/split; ảnh, box, chuỗi, địa điểm, lý do loại | `summary.json` |
| Bản dữ liệu v1 khóa cố định | Hash nguồn, cấu hình và mọi file; chỉ công bố khi hoàn chỉnh | `provenance.json` |
| Tiếp tục sau gián đoạn | Biên nhận từng ảnh, khóa tiến trình, không ghi đè snapshot | `scripts/freeze_comparison.py` |

Các file dữ liệu trên nằm trong `data/processed/comparison_v1/`.
Ảnh gốc giữ tại `data/images/swg_pilot_v2/`, không copy thêm và không đưa vào Git.
Crop B2 bàn giao ở dạng **tọa độ cắt từ ảnh gốc đã khóa hash**, không phải thư mục
JPEG crop đã xuất. TV3 có thể cắt khi đọc dữ liệu hoặc xuất cache theo các dòng này.

## Quy Tắc Khóa

1. Nhãn ảnh phải là một chuỗi loài trong `class_map.json`, class ID phải khớp.
   Mọi annotation box phải có ID và nhãn trùng với nhãn ảnh. Nhiều cá thể cùng
   loài được giữ; không yêu cầu mỗi ảnh chỉ có một cá thể.
2. Mọi box phải hữu hạn, nằm trong ảnh, có kích thước dương. Sau `round` theo
   Python và clip theo biên ảnh, cả hai cạnh crop phải ít nhất **8 pixel**.
   Quy tắc tọa độ này khớp pipeline TV3 tuần 2 đã được review.
3. Nếu bất kỳ box nào không đạt, loại **cả ảnh** khỏi B1 và B2, lưu nguyên dòng
   nguồn cùng danh sách vấn đề. Không giữ riêng box tốt rồi để hai tập khác nhau.
4. Bản chuẩn này dùng **padding = 0**, chưa resize, chưa augmentation và không
   xoay EXIF. Đề xuất padding 10-15% trong đề cương ban đầu chưa được dùng cho
   bản chuẩn này. Thử padding là biến thể riêng, phải khai báo và không sửa v1.
5. Mất/hỏng/thay checksum ảnh cục bộ là lỗi môi trường: dừng và khôi phục cache
   tuần 2, không coi đây là lý do để âm thầm khóa một tập nhỏ hơn.
6. Rò rỉ ID/đường dẫn/chuỗi/địa điểm hoặc trùng pixel RGB qua split làm lệnh thất
   bại. Trùng RGB cùng split/cùng nhãn được giữ và báo cáo theo chính sách v2.
   Chưa tìm ảnh gần giống bằng perceptual hash.

Một loài xác định ở đây là **nhất quán theo metadata đã có và box cấp ảnh**,
không phải xác nhận lại bằng chuyên gia. Nhãn ảnh SWG có nguồn gốc cấp chuỗi.

## Bàn Giao Cho TV2

- Dùng `data/processed/comparison_v1/b1/train.jsonl` và `b1/val.jsonl`.
- Class map: `data/processed/comparison_v1/class_map.json`.
- Mở ảnh bằng `ROOT / row['quality']['local_path']`; đối chiếu `quality.sha256`.
- View B1 có một dòng/ảnh. Reader `FullImageDataset` của TV2 đã hỗ trợ
  `quality.local_path`; cần cấu hình `image_root=data/images/swg_pilot_v2`.
- Đã thử reader TV2 tại `8988d28` với đủ metadata B1 và 8 ảnh train, mỗi lớp
  một ảnh: đọc được, tensor sau transform thử có kích thước `3 x 224 x 224`.
  Đây là kiểm tra dữ liệu vào, không phải chạy huấn luyện B1.
- Không tự lọc lại, chia lại hoặc thay bằng danh sách B0 cũ. Nếu gặp ảnh lỗi,
  dừng và báo TV1, không bỏ qua mẫu riêng trong loader.
- Lưu hash `comparison_v1/provenance.json` trong config/log thí nghiệm.

## Bàn Giao Cho TV3

- Dùng `data/processed/comparison_v1/b2/train.jsonl` và `b2/val.jsonl`.
- Mỗi dòng là một crop, giữ `image_id`, `crop_id`, annotation ID, nhãn, split,
  chuỗi, địa điểm và checksum ảnh **nguồn** trong `quality.sha256`.
- Dùng `bbox_xyxy=[left, top, right, bottom]` đã khóa, biên phải/dưới loại trừ
  theo Pillow. Không tự round lại hoặc thêm padding.
- Ví dụ cắt từ một dòng B2 đã qua validator:

  ```python
  from PIL import Image

  with Image.open(ROOT / row['quality']['local_path']) as source:
      crop = source.convert('RGB').crop(tuple(row['bbox_xyxy']))
  ```

- File B2 là **crop specification**, không phải định dạng `crop_manifest` đã
  xuất JPEG của tuần 2. Loader/adapter TV3 cần đọc định dạng này hoặc chuyển
  sang cache mới, giữ nguyên ID, nhãn, tọa độ và split; không truyền trực tiếp
  vào loader JPEG cũ rồi giả định tương thích.
- Không dùng lại run `v1_run03` (4.000 train + 1.000 val). Run đó lấy từ nguồn v1,
  **không cùng tập ảnh** với pilot chung 2.800 train + 600 val + 600 test.
- Nếu cache crop, lưu hash của nguồn và provenance chung; lỗi crop phải được
  báo, không tự bỏ ảnh chỉ ở B2.

## So Sánh Công Bằng

- B1/B2 cùng tập **image ID**, không nhất thiết cùng số dòng: một ảnh có nhiều
  box sẽ có nhiều dòng B2. Không lấy số crop làm số ảnh độc lập.
- Khi huấn luyện B2, `sample_weight=1/parent_crop_count` là trọng số đóng góp
  của crop trong ảnh. Khuyến nghị gom crop theo ảnh, lấy trung bình loss trong
  từng ảnh rồi trung bình theo ảnh; tránh vô tình tăng trọng số ảnh nhiều box.
  Không áp dụng đồng thời thêm một lần trọng số 1/n sau khi đã lấy trung bình.
- Khi đánh giá, lấy trung bình **vector xác suất lớp** của tất cả crop cùng
  `image_id`, rồi argmax. Đánh giá B1/B2 một dự đoán/ảnh, cùng danh sách ID và
  class map. Không so metric B1 cấp ảnh với metric B2 cấp crop.
- Chỉ train và validation được dùng phát triển mô hình. File test đã khóa để
  bảo toàn chia tập; không chạy mô hình trên test để chọn checkpoint/ngưỡng.
  B0 cũ dùng danh sách khác không phải mốc so sánh trực tiếp trên tập này.

## Chạy Và Tiếp Tục

Từ gốc repo, không cần GPU:

```powershell
.venv/Scripts/python.exe scripts/freeze_comparison.py
```

Lần đầu kiểm tra nguồn và ảnh, tạo staging hoàn chỉnh rồi công bố snapshot.
Lần sau kiểm tra snapshot và ảnh, **không ghi đè bất kỳ file nào trong snapshot**.
Nếu bị ngắt trước công bố, chạy lại cùng lệnh: biên nhận ảnh đã đạt được dùng
lại sau đối chiếu byte hash. Kiểm định cuối vẫn giải mã toàn bộ ảnh nguồn.

Trên máy mới, lấy code/manifest qua Git, tải đúng ảnh gốc tuần 2 trước:

```powershell
.venv/Scripts/python.exe scripts/resume_tv1_w2.py
.venv/Scripts/python.exe scripts/freeze_comparison.py
```

Độc lập kiểm tra lại:

```powershell
.venv/Scripts/python.exe scripts/validate_comparison.py
.venv/Scripts/python.exe scripts/validate_comparison.py --metadata-only --report outputs/comparison_metadata_check.json
.venv/Scripts/python.exe -m unittest discover -s tests -p test_comparison.py -v
```

`--metadata-only` không xác nhận file ảnh trên máy nhận. Không dùng nó thay cho
preflight ảnh trước huấn luyện. Báo cáo mặc định: `reports/tv1_w3/verification.json`.

Tiến độ nằm ở `data/interim/comparison_v1/task_state.json`, biên nhận ở
`records/`. Hết quota hội thoại không ảnh hưởng script; lệnh có thể chạy trực
tiếp trong PowerShell. Nếu máy hoặc tiến trình dừng, chạy lại, không xóa state.
Khóa writer dùng cơ chế hệ điều hành, không tự xóa `writer.guard` hay lock PID
chưa chứng minh đã dừng. Staging còn dở không được coi là bản đã khóa.

Thay nguồn/ngưỡng/cách crop phải tạo config, output và state của phiên bản mới,
thông báo TV2/TV3; không sửa trực tiếp `comparison_v1` để làm validator đạt.

## Tệp Đọc Tiếp

- [Báo cáo kết quả](../reports/tv1_w3/REPORT.md).
- [Progress sau gián đoạn](progress_tv1_w3.md).
- [Cấu hình đóng băng](../configs/comparison_v1.json).
