# TV4 tuần 4: kết quả bàn giao ngày 25/10/2026

**Hoàn thành màn hình duyệt/sửa nhãn, log suy luận và phép đo tốc độ trên máy
TV1. Demo dùng B2 đã khóa. B3 chưa đủ bằng chứng tái lập để bật chính thức.**

Nhánh `feat/demo`, nền `c6aee9f` đã tích hợp tuần 3 và TV2 tuần 4. Công việc này
không chạy lại Test chính thức, không huấn luyện, không thay checkpoint/nhãn/split.

## Đối chiếu yêu cầu

| Yêu cầu | Kết quả |
| --- | --- |
| Điểm thấp chuyển cần kiểm tra | Top 1 < 0,70 ở bất kỳ box nào → `needs_review`; lọc được các vùng điểm thấp |
| Không kết luận loài lạ | Có lựa chọn chưa xác định; không suy diễn novel species từ softmax thấp |
| Màn hình sửa nhãn | Sửa/xác nhận từng box trong 8 lớp, người duyệt, ghi chú, trạng thái ảnh, lưu và nạp lại |
| Log suy luận | Original bất biến, SHA ảnh, checkpoint, runtime, thời gian, batch và nhật ký các lần duyệt riêng |
| Detector bỏ sót | Có trạng thái và ghi chú cho bỏ sót một phần/toàn ảnh; lỗi ảnh không được đổi thành bỏ sót |
| Tốc độ có cấu hình rõ | Có số đo CPU, cold/warm, batch thực tế, kích thước đầu vào, sample IDs và code hashes |
| Tiếp tục sau quota/gián đoạn | Progress, journal từng job, khóa tiến trình, kiểm tra config và lệnh `--resume` |

`ok` chỉ nghĩa đạt ngưỡng demo; không bảo đảm nhãn đúng hoặc detector đủ box.
Ngưỡng 0,70 là heuristic giữ từ tuần 3, không được hiệu chỉnh/tối ưu trong tuần này.
Softmax là điểm dự đoán chưa hiệu chỉnh, không dùng để khẳng định loài ngoài 8 lớp.

## Kiểm thử

- **356/356** unit/integration tests PASS, 72,621 giây:
  [log đầy đủ](evidence/tv4_tests.txt).
- Browser Edge PASS trên 1440×1100, 390×844 và 320×740: MD+B2 thật, sửa nhãn
  từng box, lưu/nạp lại, xuất JSON, điểm thấp, chưa xác định, mock bỏ sót,
  ảnh hỏng, thay đầu vào xóa kết quả cũ. Không có lỗi JavaScript.
  [Kết quả](evidence/browser_verification.json), [desktop](evidence/desktop.png),
  [điện thoại](evidence/mobile.png).
- [JSON duyệt mẫu](evidence/review_example.json) có chỉnh nhãn giả lập phục vụ
  QA, ghi rõ `QA correction only; not a ground-truth adjudication.` Đây không
  phải nhãn sinh học đã được xác nhận và không đưa vào dữ liệu huấn luyện.
- Restart/resume benchmark đã hoàn thành: **21 → 21** dòng, SHA journal
  không đổi, 0 job inference mới. [Bằng chứng](evidence/resume_verification.json).
  Chưa mô phỏng mất điện giữa một lần ghi; journal hỏng sẽ báo lỗi rõ ràng.

## Tốc độ MD + B2

Máy: AMD Ryzen 5 7535HS with Radeon Graphics, 12 logical CPUs, RAM 31,24 GiB;
**chạy CPU 4 threads**, Windows 11, Python 3.12.10, PyTorch 2.8.0 CPU,
torchvision 0.23.0, Pillow 12.2.0, megadetector 10.0.25.

- Detector MDv5a.0.1, đầu vào 1280, batch ảnh = 1, batch detector = 1.
- B2 ResNet18, Resize(256) → CenterCrop(224), crop batch tối đa 8.
- Ngưỡng detector 0,20; ngưỡng review 0,70; không thay theo kết quả đo.
- 8 ảnh train, chọn image ID nhỏ nhất mỗi lớp; 1 request cold và 2 vòng warm
  = **16 request warm**. Không chạy test/browser inference khác đồng thời.
- 4 ảnh train có GT box rất nhỏ là nhóm thăm dò riêng, **không tính vào tốc độ
  chính**. Tổng cả hai nhóm 21 request trên 12 ảnh khác nhau.

| Chỉ số | Kết quả |
| --- | ---: |
| Lần đầu nạp model trong process | 18,079 giây |
| Warm mean | 5,547 giây/ảnh |
| Warm p50 | 6,000 giây/ảnh |
| Warm p95 (nearest rank, n=16) | 6,239 giây/ảnh |
| Warm throughput tuần tự | 0,180 ảnh/giây |
| Trạng thái toàn bộ 21 request | 17 ok, 3 needs_review, 1 no_detection, 0 error |

Đây là mẫu nhỏ; p95 không phải cam kết vận hành. Trong lần đo, warm dao động
khoảng 4,35–6,24 giây; không suy diễn nguyên nhân khi chưa có log tải hệ thống.
Cold là cache model rỗng trong process, không khẳng định disk cache của OS rỗng.
Thời gian gồm decode, detector, classifier và kiểm tra/cache trọng số; loại
trừ đọc file ảnh, upload, preview, ghi journal, trình duyệt và thời gian duyệt.

[Summary và cấu hình](evidence/benchmark_summary.json),
[21 bản ghi inference](evidence/benchmark_inference.jsonl).
Lần đo sơ bộ `outputs/tv4/w4/benchmark_20261025` trùng thời gian với unit tests,
nên được giữ làm chẩn đoán và không dùng cho các con số trên.

## Ví dụ detector không khớp GT

Nhóm này được chọn từ metadata theo diện tích box chuẩn hóa trước inference.
GT khớp one-to-one với detection tại IoU ≥ 0,5. “Không khớp” là ứng viên bỏ sót
hoặc định vị sai, chưa phải lỗi được chuyên gia thẩm định. Mọi box và điểm đều
được giữ trong journal; không đổi nhãn để tăng điểm.

| Job / image ID | GT / detection | GT chưa khớp (index từ 0) | Crop batch thực tế |
| --- | --- | --- | --- |
| small-box-0 / d8424165-8c29-11eb-820f-000d3a74c7de | 3 / 2 | 0 | [2] |
| small-box-1 / d5212da4-8c29-11eb-b4b4-000d3a74c7de | 1 / 0 | 0 | [] |
| small-box-2 / d5c5b9cf-8c29-11eb-a843-000d3a74c7de | 1 / 1 | 0 | [1] |
| small-box-3 / cf2b5120-8c29-11eb-b8f5-000d3a74c7de | 14 / 12 | 0, 1 | [8, 4] |

Đã xem ảnh nguồn của small-box-1 và small-box-3. Ảnh thứ nhất có GT rất nhỏ
gần mép dưới phải, không đủ rõ ở toàn cảnh để xác nhận loài bằng mắt. Ảnh thứ
hai thấy đàn lợn rừng với nhiều cá thể nhỏ/chồng lấp; giữ hai GT chưa khớp để
người dùng duyệt tiếp. Tên loài từ manifest chỉ là tham chiếu, không phải kết
luận mới của người kiểm tra. Đường dẫn ảnh lấy theo ID trong train.jsonl đã khóa.

8 ảnh chính không có GT chưa khớp; không được diễn giải là recall 100% trên SWG.
MDv5a đã dùng SWG khi huấn luyện, và đây là mẫu train nhỏ có chủ đích. Không dùng
kết quả này làm đánh giá detector độc lập hoặc so sánh B2/B3 trên Test.

## TV3: sửa kỹ thuật đã kiểm tra, giới hạn B3 vẫn giữ

Commit **a692a10**, nhánh `feat/crop-classifier`:

- Đối chiếu replay theo ID/nhãn dự đoán, ma trận và metrics chưa làm tròn;
  ghi bằng chứng và FAIL khi khác, không chấp nhận F1 lệch tới 0,01.
- Bắt buộc xác minh SHA checkpoint, metadata, provenance, manifest và ảnh
  train/validation trước phân tích lỗi; không cho ghi đè báo cáo gốc.
- Sửa ví dụ nạp checkpoint sang lớp native `B2CropClassifier`.
- Không khẳng định CPU/CUDA là nguyên nhân khi thiếu bằng chứng runtime gốc.
- **109/109** tests PASS. Chạy mới mỗi mô hình trên 600 ảnh validation / 680
  crop: B2 152 lỗi, khớp kiểm định trước; B3 154 lỗi, khớp chẩn đoán CPU nhưng
  chưa khớp báo cáo tham chiếu gốc. Không huấn luyện lại hoặc chạy Test.

B3 vẫn **UNRESOLVED / exploratory / ngoài Test**; các sửa kỹ thuật cho phép
TV4 tiếp tục bằng B2, không phải tuyên bố B3 đã đạt tái lập chính xác.
Hồ sơ chi tiết và tests nằm trên nhánh TV3; kết quả validation mới trên máy TV1
ở `outputs/review_w4_2026-10-25/fixed_validation/`.

## Tiếp tục công việc

Xem [hướng dẫn chạy, định dạng log và resume](../../docs/handoff_tv4_w4.md),
[progress](../../docs/progress_tv4_w4.md). Các bản sửa được lưu local trên hai
nhánh cố định; lượt công việc này chưa push và chưa merge main.
