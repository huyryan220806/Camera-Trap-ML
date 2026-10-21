# TV1 tuần 3 - Kết quả khóa dữ liệu so sánh

Dataset: `comparison_v1`. Kiểm định ảnh hoàn tất lúc `2026-10-14T09:48:10+00:00`.

## Kết Luận

Đã khóa **4,000 ảnh**, loại **0/4,000 ảnh** từ pilot v2.
B1/B2 dùng cùng image ID, nhãn và split; B2 có **4,485 crop specification**.
Không thay split, lấy mẫu lại hoặc bù ảnh. Chưa huấn luyện/chọn mô hình.

## Theo Split

| Split | Nguồn | Giữ | Loại | B1 ảnh | B2 crop | Chuỗi | Địa điểm |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 2,800 | 2,800 | 0 | 2,800 | 3,125 | 2,277 | 458 |
| val | 600 | 600 | 0 | 600 | 680 | 508 | 102 |
| test | 600 | 600 | 0 | 600 | 680 | 495 | 98 |

## Theo Lớp

Mỗi ô ảnh dưới đây là giữ/loại; số crop tính riêng vì một ảnh có thể có nhiều cá thể cùng loài.

| Loài | Train ảnh | Val ảnh | Test ảnh | Train crop | Val crop | Test crop |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| large_antlered_muntjac | 350/0 | 75/0 | 75/0 | 359 | 77 | 77 |
| annamite_striped_rabbit | 350/0 | 75/0 | 75/0 | 350 | 76 | 75 |
| sambar | 350/0 | 75/0 | 75/0 | 421 | 86 | 92 |
| chinese_serow | 350/0 | 75/0 | 75/0 | 360 | 76 | 78 |
| common_palm_civet | 350/0 | 75/0 | 75/0 | 352 | 77 | 75 |
| masked_palm_civet | 350/0 | 75/0 | 75/0 | 353 | 75 | 75 |
| silver_pheasant | 350/0 | 75/0 | 75/0 | 450 | 103 | 102 |
| eurasian_wild_pig | 350/0 | 75/0 | 75/0 | 480 | 110 | 106 |

## Giữ Và Loại

- Một nhãn loài trong class map và mọi box cấp ảnh đồng ý với nhãn ảnh.
- Mọi box hữu hạn, trong biên; sau round/clip có cạnh ít nhất 8 px. Padding = 0.
- Một box lỗi làm loại cả ảnh khỏi B1/B2; không chỉ bỏ crop lỗi ở B2.
- `excluded.jsonl` lưu dòng gốc và từng lý do. `summary.json` thống kê theo split/lớp.
- Lý do loại thực tế: `{}`.
- Kết quả 0 loại (nếu có) là do nguồn đã được làm sạch, không phải bỏ qua bộ lọc.

## Kiểm Tra Chia Tập

- Giao nhau qua split: `{'image_id': 0, 'file_name': 0, 'seq_id': 0, 'location': 0}`.
- ID trùng: 0; đường dẫn trùng: 0.
- Có 3,280 chuỗi và 658 địa điểm giữ lại.
- Kiểm tra cả nguồn trước lọc và đầu ra sau lọc; không che rò rỉ bằng cách lọc mất bằng chứng.
- Có 1 nhóm trùng RGB cùng split/cùng nhãn; giữ và báo cáo trong `duplicates.json`.
- Tổng nội dung pixel khác nhau: 3,999. Không phát hiện trùng RGB qua split.
- Chưa tìm ảnh gần giống/perceptual duplicate. Không khẳng định toàn bộ SWG không rò rỉ.

## Tính Toàn Vẹn

- Đã giải mã và đối chiếu byte/pixel SHA-256 của toàn bộ ảnh nguồn trên máy TV1.
- Validator tái dựng danh sách đủ điều kiện, đối chiếu từng field nguồn và mọi view B1/B2.
- Hash nguồn, cấu hình và các file snapshot nằm trong `provenance.json`.
- SHA-256 provenance: `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`.
- Ảnh gốc tái sử dụng tại `data/images/swg_pilot_v2`, không upload ảnh lên Git.

## Bàn Giao

- Snapshot: `data/processed/comparison_v1/`.
- TV2: `b1/train.jsonl`, `b1/val.jsonl`; một dòng/ảnh.
- TV3: `b2/train.jsonl`, `b2/val.jsonl`; cắt ảnh gốc theo `bbox_xyxy`, không phải JPEG crop đã xuất.
- Giữ nguyên `image_id`, nhãn, split và class map; không dùng crop run `v1_run03` thay thế.
- B2 lấy trung bình loss theo ảnh khi train, trung bình xác suất crop theo ảnh khi đánh giá.
- Test chỉ kiểm tra kỹ thuật; chưa dùng để chọn mô hình hoặc ngưỡng.
- Hướng dẫn: [handoff_tv1_w3.md](../../docs/handoff_tv1_w3.md).
- Tiếp tục: `.venv/Scripts/python.exe scripts/freeze_comparison.py`.

## Bằng Chứng Bổ Sung

- `verification.json`: đối chiếu snapshot và toàn bộ ảnh nguồn.
- `tests.json`: kết quả unit suite, gồm các trường hợp lỗi và resume.
- `crop_compatibility.json`: đối chiếu hình học với pipeline TV3 và smoke crop trên train.
- `tv2_loader_compatibility.json`: reader TV2 đọc đủ B1, nạp 8 ảnh train thành tensor.
- Không xem các kiểm tra kỹ thuật này là điểm số phân loại/phát hiện.

## Giới Hạn

Đây là pilot có chọn mẫu/cân bằng lớp từ tuần 1, không phải toàn bộ 31.589 ảnh có box.
Một loài được xác nhận bằng tính nhất quán metadata, không phải thẩm định lại bởi chuyên gia.
B2 dùng box ground truth; không phải đánh giá phát hiện của MegaDetector.
Chưa train B1/B2, không có điểm số mô hình. Việc tích hợp loader của TV3 là bước tiếp theo.
