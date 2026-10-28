# TV1 tuần 5 — bàn giao dữ liệu ứng viên và kế hoạch đánh giá

**Ngày:** 28/10/2026. **Nhánh:** `feat/metadata-split`. **Người kiểm tra:** TV2.
**Trạng thái:** đã hoàn thành kiểm kê metadata, manifest ứng viên, phân tích
khả năng có test mới và phần dữ liệu báo cáo. Bàn giao trên nhánh
`feat/metadata-split`, chờ TV2 kiểm tra trước khi merge vào `main`.

## Kết quả chính

- Kiểm kê lại **31.589 ảnh** trong nguồn v1; giữ nguyên `comparison_v1` 4.000 ảnh.
- **19.266 ảnh** ngoài pilot thuộc train v1 đạt điều kiện nhãn/box của bản so sánh.
- Chọn **1.665 ứng viên bổ sung**, 1 ảnh/chuỗi mới so với pilot, tối đa 250/lớp,
  phân bổ lượt qua địa điểm với seed 42. Đây là danh sách để xem xét mở rộng,
  **chưa phải 1.665 ảnh đã tải hoặc được phép đưa ngay vào huấn luyện**.
- **9 ảnh** nguồn v1 bị loại khỏi ứng viên do có cạnh crop nhỏ hơn 8 px: 7 train,
  2 validation. Không ảnh nào trong pilot cũ bị sửa, loại hoặc chuyển split.
- Tập test v1 ở địa điểm chưa có trong các nguồn lịch sử đã rà: **109 ảnh,
  50 chuỗi, 21 địa điểm**. Thỏ vằn 1 ảnh, cầy vòi hương 3 ảnh: **chưa đủ hỗ trợ
  để phát hành một test mới cho 8 lớp**.
- Không có giao ID, đường dẫn, chuỗi hoặc địa điểm giữa train đề xuất, val cũ,
  Test cũ và holdout ứng viên. Đây là kiểm tra **metadata**; ảnh ứng viên chưa
  qua decode, byte/RGB hash hoặc kiểm tra near-duplicate.

Đọc [báo cáo đầy đủ](../reports/tv1_w5/REPORT.md) và
[phần dữ liệu để đưa vào báo cáo môn học](../reports/tv1_w5/DATA_CHAPTER.md).

## TV2 và TV3 dùng gì ngay?

Lượt DINO đầu tiên vẫn dùng bản **`comparison_v1` đã khóa**:

- `data/processed/comparison_v1/b2/train.jsonl`: 2.800 ảnh / 3.125 crop.
- `data/processed/comparison_v1/b2/val.jsonl`: 600 ảnh / 680 crop.
- Class map cũ, tọa độ crop, mean vector softmax cấp ảnh và seed/config được ghi rõ.
- Chọn bằng validation theo protocol TV2. Giữ Test B2 cũ như kết quả lịch sử;
  không dùng Test cũ để lựa chọn ứng viên DINO.

Phương án test mới trong slide là **có điều kiện**. Kiểm kê W5 cho thấy nguồn
hiện tại chưa đáp ứng; không gọi 109 ảnh này là test mới đã khóa chất lượng,
không dùng tập ít mẫu để tuyên bố “đạt accuracy 88% độc lập”.

## Snapshot ứng viên

Thư mục: [`data/processed/w5_candidates_v1/`](../data/processed/w5_candidates_v1/).

| File | Ý nghĩa |
| --- | --- |
| `decisions.jsonl` | Quyết định với đủ 31.589 ảnh, lý do loại/giữ và trạng thái chọn train |
| `train_extension_candidates.jsonl` | 1.665 dòng nguồn v1 nguyên giá trị, vẫn `split=train` |
| `holdout_candidates.jsonl` | 109 dòng nguồn v1 nguyên giá trị, vẫn `split=test`; chỉ khảo sát |
| `excluded_invalid.jsonl` | 9 ảnh, dòng nguồn và lý do geometry |
| `summary.json`, `audit.json` | Tổng, từng lớp, mẫu/chuỗi/địa điểm/box, rò rỉ metadata |
| `baseline_references.json` | Đường dẫn và hash của dữ liệu dùng cho lượt DINO đầu |
| `historical_exposure.json` | 16 nguồn lịch sử B0/crop đã rà, kể cả lượt tải lỗi |
| `class_map.json`, `policy.json`, `provenance.json` | Class ID, seed/quy tắc và SHA đầu vào/đầu ra |

Snapshot cố ý có `training_ready=false`, `holdout_ready=false`.
Danh sách ứng viên không có trường `quality` của ảnh đã tải; loader huấn luyện
không được tự điền hoặc tắt kiểm tra để sử dụng nó.

## Nếu cần mở rộng train sau lượt đối chứng

TV1 phối hợp TV2/TV3 thực hiện một **đợt phát hành khác**, không sửa snapshot
hiện tại. Thứ tự:

1. Chốt có đủ GPU/thời gian và ghi experiment riêng cho dữ liệu mở rộng.
2. Tải đúng danh sách, lưu trạng thái tiếp tục, ảnh thiếu/hỏng; không tự thay ảnh.
3. Giải mã ảnh, đối chiếu kích thước, byte/RGB hash; kiểm tra trùng nội dung với
   toàn bộ train/val/Test cũ và holdout dự kiến. Rà box/nhãn theo quy tắc chung,
   công khai giới hạn chưa có chuyên gia và near-duplicate.
4. Nếu có ảnh lỗi hoặc trùng chéo, giữ nguyên tập cũ, ghi lý do loại ảnh bổ sung;
   không chuyển ảnh sang split khác. Cả mô hình đối chứng cần dùng cùng danh sách
   nếu mục tiêu là tách hiệu ứng kiến trúc khỏi hiệu ứng dữ liệu.
5. Xuất phiên bản train mở rộng có `quality`, crop view, counts và provenance;
   TV2 kiểm tra trước khi TV3 dùng. Tối đa **4.465 ảnh train** nếu 1.665 ứng viên
   đều đạt, không phải số ảnh train mới đã phát hành hôm nay.

Lệnh tải dưới đây **chỉ dùng khi bắt đầu đợt mở rộng**, chưa chạy trong bàn giao này:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/download_subset.py --source data/processed/w5_candidates_v1/train_extension_candidates.jsonl --images data/images/swg_w5_extension --state data/interim/download_w5_extension --log outputs/tv1_w5_extension/download_events.jsonl --workers 4
```

Lệnh hỗ trợ tiếp tục từng ảnh; không tự tạo training release. Không dùng
`build_manifest_v2.py` đơn lẻ để kết luận đã kiểm tra trùng với pilot cũ:
validator đó chỉ đối chiếu các ảnh trong tập được cung cấp.

## Kiểm tra và tiếp tục sau hết quota

```powershell
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w5.py
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w5.py --verify-only --report outputs/tv1_w5/verify_again.json
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_tv1_w5.py -v
```

Lần đầu tạo staging rồi đổi tên công bố snapshot. Chạy lại kiểm tra cùng kết
quả, không ghi đè file đã khóa. Nếu tiến trình ngắt, lock được hệ điều hành
nhả; chạy lại tiếp tục staging sau đối chiếu nguồn. Không xóa lock/state để
chạy hai writer. Nếu nguồn, config hoặc builder đã đổi, lệnh dừng để giữ bản
cũ; cần xem diff và thiết kế phiên bản mới, không cập nhật hash cho qua lỗi.

State: `data/interim/w5_candidates_v1/`; log xác minh: `outputs/tv1_w5/`.
[Progress](progress_tv1_w5.md) có trạng thái mới nhất. Trên máy mới cần nhận
đủ code/config/snapshot và các manifest lịch sử trong Git; không cần tải
2 triệu ảnh hoặc có GPU để chạy công cụ W5.

## Kế hoạch gửi ba thành viên

- [TV2 — đánh giá và kiểm tra chéo tuần 5–6](plans/TV2_W5_W6.md).
- [TV3 — DINO và checkpoint tuần 5–6](plans/TV3_W5_W6.md).
- [TV4 — UI, adapter và đóng gói tuần 5–6](plans/TV4_W5_W6.md).

TV4 đã có code UI mới trên remote; plan ghi tiếp nhận review thay vì yêu cầu
làm lại. Không có phần nào được xem là đã nghiệm thu chỉ nhờ kế hoạch này.
