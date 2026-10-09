# TV1 tuần 2 - Tải tập con và kiểm tra chất lượng

## Phạm vi đã thống nhất

Người dùng chọn **pilot 4.000 ảnh** có sẵn trong `data/processed/v1/pilot_v1.jsonl`,
không phải toàn bộ 31.589 ảnh. Giữ nguyên các ID, nhãn, box, địa điểm, chuỗi và
split của v1. Không lấy mẫu lại, không đổi seed 42, không tự bù ảnh bị loại.

Đây là tập pilot để thử pipeline tuần 2, có phân bố lớp được chọn có chủ đích;
không dùng điểm số trên pilot test để chọn mô hình hoặc ngưỡng. Việc tải/giải mã
test chỉ là kiểm tra kỹ thuật tự động, không xem ảnh test để điều chỉnh thiết kế.

## Tiêu chí và sản phẩm

| Tiêu chí | Thực hiện |
|---|---|
| Tải có tiếp tục | `scripts/download_subset.py`; tái sử dụng file có receipt và checksum hợp lệ, không tải lại toàn bộ |
| Ảnh thiếu/hỏng | Log từng lần thử, mã HTTP, thiếu nguồn, lỗi mạng, lỗi giải mã, kích thước không khớp và file cục bộ thay đổi |
| Ảnh hợp lệ | `data/images/swg_pilot_v2/`, ảnh gốc không nén lại, không xoay EXIF và không đưa lên Git |
| Manifest v2 | `data/processed/v2/manifest_v2.jsonl` và `train.jsonl`, `val.jsonl`, `test.jsonl` |
| Đối chiếu số mẫu | `data/processed/v2/summary.json`: theo split và theo loài/split, requested = accepted + excluded |
| Giải thích ảnh bị loại | `data/processed/v2/excluded_v2.jsonl`, gồm đầy đủ bản ghi nguồn và lý do |
| Không thay split âm thầm | Đối chiếu từng trường gốc với v1, checksum nguồn và class map; không ghi đè manifest v1/v2 |
| Log tải | `reports/tv1_w2/download_events.jsonl`; bản sao đóng băng trong v2 |
| Kiểm tra độc lập | `scripts/validate_manifest_v2.py`, kết quả ở `reports/tv1_w2/verification.json` |

## Cài đặt và chạy

Python 3.12, `requirements.txt` đủ cho phần tải và chất lượng. Muốn chạy toàn bộ
test của nhóm cần `requirements-tv2.txt`. Không cần GPU cho công việc này.

**Lệnh chạy/tiếp tục duy nhất**, thực hiện từ thư mục gốc repo:

```powershell
.venv/Scripts/python.exe scripts/resume_tv1_w2.py
```

Lệnh kiểm tra nguồn và receipt trên đĩa, chỉ gọi bước tải khi có ảnh thiếu hoặc
checksum không khớp, xuất v2 nếu chưa có, rồi giải mã và kiểm định toàn bộ ảnh.
Nếu v2 đã tồn tại, giữ nguyên từng byte của snapshot và chỉ kiểm tra lại.
Máy mới nhận snapshot qua Git cũng dùng lệnh này để tải ảnh cục bộ trước khi xác minh.
Nếu ảnh nguồn đã đổi so với snapshot, validator báo lỗi, không sửa snapshot theo ảnh mới.

Các bước riêng lẻ để chẩn đoán hoặc kiểm tra chéo:

```powershell
.venv/Scripts/python.exe scripts/download_subset.py --workers 8
.venv/Scripts/python.exe scripts/build_manifest_v2.py
.venv/Scripts/python.exe scripts/validate_manifest_v2.py
```

Chỉ chạy bước build riêng nếu v2 chưa tồn tại. Có thể thử một ít ảnh bằng `--limit 8`;
giới hạn chỉ áp dụng lượt tải đó, bước xuất v2 vẫn yêu cầu đủ kết quả cho toàn bộ
nguồn. Tải thất bại trả exit code khác 0; xem log và thử lại trước khi xuất v2.
Không chạy đồng thời hai downloader dùng cùng thư mục state.

**Mức tiếp tục:** theo từng ảnh, không tiếp tục từng byte. File hoàn tất được
kiểm tra và bỏ qua tải lại; `.part` chưa hoàn tất được tải lại từ đầu ảnh đó.
Mỗi ảnh thử tối đa 3 lần với timeout và khoảng chờ; 404/410 không thử lại liên tục.

## Tiếp tục sau khi hết quota hoặc tắt máy

- Trạng thái máy: `data/interim/download_pilot_v2/task_state.json`, gồm bước hiện tại,
  trạng thái, checksum nguồn, thời điểm, lỗi gần nhất và lệnh tiếp tục.
- Biên nhận từng ảnh: `data/interim/download_pilot_v2/records/`. Mỗi ảnh hoàn thành
  được ghi riêng bằng thay thế file nguyên tử; không cần chờ hết 4.000 ảnh mới lưu.
- Ghi chú cho người hoặc trợ lý tiếp nhận: [progress_tv1_w2.md](progress_tv1_w2.md).
  README có liên kết để tìm lại mà không phụ thuộc lịch sử hội thoại.
- Hết quota hội thoại không xóa dữ liệu đã lưu. Có thể tự chạy lệnh trên trong
  PowerShell; script không cần gọi mô hình AI. Không có lịch tự đánh thức trợ lý.
  Nếu tiến trình dừng hoặc máy tắt, chạy lại cùng lệnh khi máy hoạt động trở lại.
- Không tin riêng cờ `complete`: lần chạy sau luôn đối chiếu file và checksum.
  Nếu bị ngắt giữa kiểm định, chạy lại kiểm định; không tải lại bộ ảnh và không build đè v2.
- `writer.guard` là file khóa hệ điều hành và **vẫn tồn tại sau khi xong**; sự tồn tại
  của file không có nghĩa đang chạy. Không xóa file này để vượt khóa.
- Với `active.lock` còn sót, script chỉ lưu trữ lại lock cũ khi chứng minh PID đã
  dừng. PID đang chạy, không đọc được PID hoặc không xác định được trạng thái thì
  dừng an toàn, yêu cầu kiểm tra thủ công. Không tự giết tiến trình khác.
- Thư mục `v2.staging-*` còn sót không phải snapshot đã chốt. Chạy lại sẽ xuất sang
  thư mục staging mới nếu chưa có v2; không lấy bản dở để báo hoàn thành.

Không xóa ảnh hay state để bắt đầu lại. Dòng log tải bị ghi dở được giữ ở file
`.interrupted-tail.bin` trước khi sửa phần đuôi log. Nếu còn ảnh tải lỗi sau số lần
thử quy định, lệnh tiếp tục dừng trước khi build để người phụ trách đọc log; không
tự chấp nhận một đợt mất mạng hàng loạt là dữ liệu đã bàn giao. Bước build riêng
có hỗ trợ ghi các ảnh lỗi đã xử lý vào `excluded_v2.jsonl` nếu nhóm quyết định
chốt tập thiếu ảnh sau khi xem xét, luôn có lý do và đối chiếu số mẫu.

## Quy tắc chất lượng

1. Chỉ tải URL công khai SWG đúng với đường dẫn trong manifest; không đi theo redirect sang nguồn khác.
2. Kiểm tra độ dài tải, file không rỗng, tối đa 32 MiB/ảnh; Pillow verify và giải mã đầy đủ ảnh chính.
3. Kích thước giải mã phải trùng metadata; box phải nằm trong biên ảnh. Không tự xoay, resize ảnh hoặc sửa box để làm kết quả đạt.
4. Lưu SHA-256 file và SHA-256 pixel RGB đã giải mã; ảnh cũ bị thay đổi hoặc không có receipt nguồn hợp lệ được cách ly và tải lại.
5. Nếu hai ảnh có pixel RGB giống hệt nhưng khác split hoặc nhãn, loại toàn bộ nhóm khỏi v2 và ghi audit. Không chuyển ảnh sang split khác.
6. Ảnh trùng chính xác trong cùng split và cùng nhãn vẫn giữ nhưng được ghi trong `duplicates.json`. Chưa tìm ảnh gần giống bằng perceptual hash.

Kiểm tra cache không hỏi lại server nếu checksum cục bộ còn đúng. Bởi vậy resume
xác nhận bản đã tải trước đó, không khẳng định server chưa thay ảnh. ETag và
Last-Modified của lần tải được lưu trong log/receipt.

## Quy ước manifest v2

Mỗi dòng giữ toàn bộ trường v1 và bổ sung:

- `source_version`: `v1`.
- `quality.local_path`: đường dẫn ảnh tính từ gốc repo.
- `quality.sha256`, `quality.pixel_sha256`: checksum byte và pixel RGB.
- `quality.bytes`, `quality.image_format`, `quality.image_mode`, `quality.validated_utc`.

TV2/TV3 dùng **cùng các file split v2**, mở ảnh bằng `ROOT / row['quality']['local_path']`.
Crop kế thừa split và box của ảnh gốc. Không dùng đường dẫn tuyệt đối của máy TV1.

`provenance.json` lưu checksum nguồn, seed gốc, chính sách loại ảnh và checksum
mọi file bàn giao. Export tạo thư mục mới hoàn chỉnh rồi công bố; không ghi đè
thư mục v2 đã có. Nếu cần thay tập sau khi đóng băng, tạo phiên bản mới, ghi lý do
và thông báo cả nhóm, không sửa trực tiếp v2.

## Bàn giao qua Git và giữa các máy

Chỉ đưa code, manifest, log và báo cáo lên Git; ảnh nằm trong `data/images/` đã
được bỏ qua. Thành viên khác tải ảnh vào cùng đường dẫn bằng script, rồi chạy
validator v2 để đối chiếu với snapshot đã nhận. Nếu ảnh nguồn thay đổi, validator
sẽ báo mismatch, không tự sửa checksum snapshot.

Máy chưa tải ảnh có thể kiểm tra riêng metadata:

```powershell
.venv/Scripts/python.exe scripts/validate_manifest_v2.py --metadata-only --report outputs/v2_metadata_check.json
```

Lượt này không xác nhận chất lượng file ảnh trên máy đó. Xem số liệu và kết quả
thực tế trong `reports/tv1_w2/verification.json` và `data/processed/v2/summary.json`.
Bản ngày 2026-10-09 đã xác minh đủ **4.000 ảnh**, 0 loại, 0 thay đổi split;
xem [báo cáo bàn giao](../reports/tv1_w2/REPORT.md). Một cặp trùng trong cùng tập
test/cùng nhãn được giữ và báo cáo, nên có 3.999 nội dung pixel khác nhau.

## Checklist kiểm tra chéo

- [ ] Đối chiếu đủ 4.000 ID giữa nguồn, manifest chấp nhận và manifest loại.
- [ ] Chạy downloader lần hai; ảnh đã đạt được tái sử dụng, không tải lại.
- [ ] Đối chiếu số mẫu từng split và từng lớp/split; mọi thay đổi số lượng có lý do.
- [ ] Xác nhận không thay field v1, class map hoặc split.
- [ ] Kiểm tra log lỗi và nhóm trùng, không lấy ảnh khác bù ngầm.
- [ ] Chạy validator với ảnh cục bộ trước khi huấn luyện; không chỉnh mô hình bằng pilot test.

Giới hạn: kiểm tra tự động không thay thế xác nhận nhãn/loài và chất lượng box
bằng chuyên gia; không chứng minh toàn bộ SWG không có ảnh trùng hoặc gần giống.
