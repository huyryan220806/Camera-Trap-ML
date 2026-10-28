# TV1 tuần 5 — kiểm kê mở rộng dữ liệu và khả năng có test mới

**Ngày:** 28/10/2026. **Nền mã:** `60516f5`. **Branch:** `feat/metadata-split`.
**Phiên bản bàn giao:** `w5_candidates_v1`. **Người kiểm tra tiếp theo:** TV2.

## Kết luận bàn giao

Đã hoàn thành phần TV1 W5 theo kế hoạch cập nhật: kiểm kê train bổ sung,
manifest ứng viên có quy tắc/seed/hash, kiểm tra split và lịch sử dữ liệu,
phương án đánh giá khi chưa đủ test mới, cùng phần dữ liệu cho báo cáo.

- Nguồn: **31.589 ảnh / 13.258 chuỗi / 792 địa điểm / 38.322 box** trong v1.
- Giữ nguyên baseline: **4.000 ảnh**, train/val/Test **2.800/600/600**.
- Train bổ sung đạt điều kiện metadata: **19.266 ảnh**; chọn **1.665 ứng viên**,
  **1.665 chuỗi**, **480 địa điểm**, **1.835 box**.
- Loại khỏi ứng viên **9 ảnh** vì có cạnh crop dưới 8 px; không sửa bản nguồn.
- Holdout khảo sát: **109 ảnh / 50 chuỗi / 21 địa điểm / 123 box**;
  trạng thái **`NOT_READY_INSUFFICIENT_SUPPORT`**.
- **0 đổi split; 0 sửa nhãn; 0 thay đổi byte trong các nguồn đã khóa** được đối chiếu hash.
- **0 ảnh mới tải, 0 huấn luyện, 0 suy luận model trên Test** trong công việc này.

Đây là bản **ứng viên metadata**, không phải một training release mở rộng hoặc
bộ test mới đã được nghiệm thu. `training_ready=false`, `holdout_ready=false`.

## 1. Nguồn và các kiểm tra bảo vệ dữ liệu

Dùng [v1](../../data/processed/v1/provenance.json),
[comparison_v1](../../data/processed/comparison_v1/provenance.json) và
[config W5](../../configs/data_w5_candidates_v1.json). Không tải lại metadata
khác phiên bản hoặc chạy lại phép chia tập tuần 1.

Đối chiếu hash các file nguồn v1/v2/comparison và kiểm định lại quan hệ dẫn
xuất của comparison. Kiểm tra đủ khóa định danh, class map, location map,
nhãn ảnh/box, geometry và trường `sequence_id`/`seq_id`. Tọa độ crop giữ quy
ước tuần 3: Python round-half-even, clip theo biên ảnh, padding 0, cạnh tối
thiểu 8 pixel. Một box không đạt làm loại cả ảnh khỏi nguồn ứng viên.

Lịch sử khảo sát gồm **16 manifest/log B0 và crop** trong repo, kể cả ảnh tải
lỗi đã được đưa vào danh sách thử, cộng toàn bộ pilot hiện có: **9.143 ID ảnh,
689 địa điểm** đã xuất hiện trong hồ sơ. Tập vị trí này được bảo vệ khi tìm
holdout; không chỉ loại riêng ID ảnh đã dùng.

Chi tiết nguồn và SHA: [historical_exposure.json](../../data/processed/w5_candidates_v1/historical_exposure.json)
và [provenance.json](../../data/processed/w5_candidates_v1/provenance.json).
Đây là kiểm tra theo hồ sơ có sẵn, không chứng minh không có thử nghiệm ngoài
repo hoặc không trùng dữ liệu tiền huấn luyện của mô hình nền tảng.

## 2. Đối chiếu đủ 31.589 ảnh

Các nhóm dưới đây loại trừ nhau; tổng bằng nguồn v1:

| Quyết định | Ảnh | Cách xử lý |
| --- | ---: | --- |
| Baseline đã khóa | 4.000 | Giữ nguyên dữ liệu và kết quả cũ |
| Train ứng viên ngoài baseline | 19.266 | Chỉ có nguồn `split=train`; chưa xác nhận chất lượng ảnh |
| Validation ngoài baseline | 4.233 | Giữ vai trò validation, không đưa vào train/holdout |
| Test ngoài baseline, địa điểm đã có trong hồ sơ | 3.972 | Không gọi là holdout ở địa điểm mới |
| Holdout khảo sát ở địa điểm chưa có trong hồ sơ | 109 | Chỉ metadata ứng viên, chưa đủ hỗ trợ 8 lớp |
| Không đạt geometry | 9 | 7 train + 2 val; không ảnh nào thuộc baseline |
| **Tổng** | **31.589** | **Không đổi split nguồn** |

[decisions.jsonl](../../data/processed/w5_candidates_v1/decisions.jsonl) có một
dòng cho mọi ID nguồn. [excluded_invalid.jsonl](../../data/processed/w5_candidates_v1/excluded_invalid.jsonl)
giữ dòng nguồn cùng lý do. Loại khỏi **ứng viên W5** không phải xóa ảnh khỏi v1
hoặc thay các thống kê/điểm của tuần trước.

## 3. Train mở rộng: tiềm năng và danh sách giới hạn

Chính sách chọn để kiểm soát thời gian: tối đa **250 ảnh bổ sung/lớp**, chỉ
lấy chuỗi chưa xuất hiện trong pilot, một ảnh/chuỗi. Chọn đại diện bằng SHA-256
kết hợp seed 42; phân bổ lần lượt qua các địa điểm theo thứ tự hash. Không
xem điểm dự đoán hoặc chọn ảnh dễ. Mọi tham số nằm trong config và snapshot.

| Lớp | Nguồn train bổ sung | Chuỗi chưa có trong pilot | Ứng viên chọn | Train nếu mọi ứng viên đạt chất lượng |
| --- | ---: | ---: | ---: | ---: |
| large_antlered_muntjac | 5,217 | 1,999 | 250 | 600 |
| annamite_striped_rabbit | 47 | 13 | 13 | 363 |
| sambar | 2,382 | 811 | 250 | 600 |
| chinese_serow | 876 | 206 | 206 | 556 |
| common_palm_civet | 860 | 272 | 250 | 600 |
| masked_palm_civet | 720 | 208 | 208 | 558 |
| silver_pheasant | 806 | 238 | 238 | 588 |
| eurasian_wild_pig | 8,358 | 3,260 | 250 | 600 |
| **Tổng** | **19.266** | **7.007** | **1.665** | **4.465** |

Trong 19.266 ảnh: **3.017** cùng chuỗi với pilot không được chọn; **1.665**
được chọn; **14.584** còn lại không được chọn do quy tắc đại diện chuỗi hoặc
hạn mức lớp. Chúng không bị gắn nhãn ảnh hỏng.

Thỏ vằn chỉ còn **47 ảnh** ngoài pilot, trong đó **13 ảnh/13 chuỗi** mới.
Không thể kỳ vọng cứ tăng ảnh sẽ tăng đồng đều hỗ trợ cho mọi loài. Nếu tải
và kiểm định thành công toàn bộ danh sách, train đề xuất có 4.465 ảnh,
3.942 chuỗi, 540 địa điểm và 4.960 crop; đây là **số dự kiến**, chưa phải bản
train đã phát hành. Dữ liệu sẽ mất cân bằng so với pilot 350 ảnh/lớp.

Lượt DINO đầu dùng nguyên train/val cũ để đối chứng B2. Thử mở rộng là lượt
riêng; nếu không chạy B2 với cùng train mở rộng, không quy riêng mức thay đổi
cho kiến trúc DINO. Dung lượng tải và chất lượng ảnh mới hiện chưa đo.

## 4. Test mới: chưa đủ điều kiện trong phạm vi dữ liệu hiện có

Chỉ xét ảnh có GT box trong v1 và giữ nguyên `split=test`. Không lấy các địa
điểm train/val chưa chọn vào pilot rồi đổi tên thành test. Loại toàn bộ địa
điểm đã xuất hiện trong hồ sơ phát triển/kiểm tra trước đây.

| Lớp | Ảnh | Chuỗi | Địa điểm |
| --- | ---: | ---: | ---: |
| large_antlered_muntjac | 9 | 3 | 3 |
| annamite_striped_rabbit | 1 | 1 | 1 |
| sambar | 13 | 5 | 3 |
| chinese_serow | 19 | 7 | 4 |
| common_palm_civet | 3 | 1 | 1 |
| masked_palm_civet | 7 | 5 | 5 |
| silver_pheasant | 10 | 8 | 3 |
| eurasian_wild_pig | 47 | 20 | 11 |
| **Tổng duy nhất** | **109** | **50** | **21** |

Địa điểm có thể có nhiều lớp nên không cộng các hàng địa điểm thành tổng.
Sàn hỗ trợ nội bộ dùng cho lập kế hoạch là **75 ảnh, 10 chuỗi, 2 địa điểm/lớp**:
75 ảnh tương ứng mức hỗ trợ test pilot trước đây, số nhóm kế thừa mức tối thiểu
W1. Đây không phải phân tích power hay bảo đảm thống kê. Nguồn hiện tại
không đạt sàn; thỏ vằn 1 ảnh và cầy vòi hương 3 ảnh cũng cho thấy giới hạn ngay
cả khi giảm sàn. Không hạ tiêu chí sau khi thấy điểm model để công bố đạt 88%.

**Phương án áp dụng:** dùng validation cũ để phát triển và so sánh ứng viên;
báo rõ đó là validation. Giữ Test B2 cũ như kết quả lịch sử. Không chạy lại
Test cũ để chọn checkpoint/threshold. Chưa phát hành test mới hoặc khóa một
protocol đánh giá độc lập trên 109 ảnh này.

Kết luận này chỉ áp dụng cho tập ứng viên **8 lớp có GT box trong nguồn v1**.
Muốn có holdout mạnh hơn cần thêm dữ liệu/địa điểm, GT box và rà nhãn, có thể
ngoài phạm vi hai tuần còn lại. Nếu có nguồn mới đủ điều kiện, khóa tập và
protocol trước chọn ứng viên, rồi khóa model bằng validation trước mở đánh giá.
So sánh B2 và ứng viên trên cùng tập mới, không trừ điểm trên hai tập khác nhau.

## 5. Kiểm định và giới hạn chất lượng

- Kiểm định nguồn/snapshot, chạy lại và verify-only đều PASS, cùng SHA snapshot.
- Kiểm tra độc lập đọc JSONL đối chiếu đủ ID nguồn, dòng nguồn nguyên giá trị,
  một ảnh/chuỗi bổ sung, location exposure và các checksum: PASS.
- Giao nhau giữa train đề xuất, val, Test cũ, holdout ứng viên: ID/đường dẫn/
  chuỗi/địa điểm đều **0**. Các ảnh trong cùng train được phép cùng địa điểm.
- **389/389 unittest PASS**, 106,401 giây; gồm 12 test mới cho lựa chọn dữ liệu,
  rò rỉ qua địa điểm, burst, box lỗi, thứ tự đầu vào, staging và không ghi đè.
- Môi trường CPU và 6 fixture hợp đồng kết quả PASS. Không đánh giá tốc độ/model mới.

Bằng chứng: [lần tạo](verification.json), [chạy lại](resume_verification.json),
[verify-only](independent_verification.json), [audit độc lập](independent_audit.json),
[toàn bộ kiểm thử](tests.txt).

Ảnh ứng viên **chưa được decode/hashing/rà nhãn trực quan**; chưa kiểm tra trùng
pixel hoặc near-duplicate với các tập khác. Kiểm tra metadata không thay thế
quality gate. Nhãn nhất quán theo metadata/box chưa phải chứng nhận chuyên gia.
Tập pilot được chọn có chủ đích; không suy rộng cho mọi động vật Trường Sơn.

## 6. Bàn giao và việc sau bước metadata

- TV2 kiểm tra [protocol/kế hoạch](../../docs/plans/TV2_W5_W6.md), xác nhận số
  liệu và cách đánh giá trước lượt DINO đầu. TV1 chưa tự nghiệm thu thay TV2.
- TV3 dùng [plan mô hình](../../docs/plans/TV3_W5_W6.md), chưa dùng train ứng viên.
- TV4 tiếp tục [plan ứng dụng](../../docs/plans/TV4_W5_W6.md) từ UI đã push,
  không cần đợi model mới để hoàn tất review giao diện.
- [Hướng dẫn TV1](../../docs/handoff_tv1_w5.md) có lệnh tải tiếp tục nếu mở đợt
  mở rộng sau này, và các kiểm tra bắt buộc trước phát hành train.
- [Phần dữ liệu báo cáo](DATA_CHAPTER.md) đã viết để nhóm ghép vào báo cáo chung.

Không chạy huấn luyện hoặc merge trong đợt kiểm kê. Gói bàn giao được chuẩn bị
trên `feat/metadata-split` theo yêu cầu push tiếp theo của TV1. Trọng số, ảnh và
state ở ngoài Git theo quy ước. [Progress](../../docs/progress_tv1_w5.md) ghi
nhánh công bố và cách khôi phục.
