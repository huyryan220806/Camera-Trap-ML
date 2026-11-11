# TV1 tuần 6 — phát hành train mở rộng và kiểm định chất lượng

**Hoàn thành kỹ thuật:** 03/11/2026, trước lịch đề xuất 04–10/11.
**Nhánh:** `feat/metadata-split`. **Nền tích hợp W5:** `cfcf006`.
**Trạng thái:** phần dữ liệu TV1 hoàn thành; **chờ TV2 peer review** trước khi TV3
chạy thí nghiệm mở rộng. Không ghi nhận thay TV2 một phê duyệt chưa có.

## 1. Kết quả bàn giao

- Tải đủ **1.665/1.665 ảnh train**, tổng **2.577.829.468 byte**; không có lỗi
  HTTP/decode/kích thước trong lượt tải, không retry do lỗi, không thay mẫu.
- Giữ thêm **1.446 ảnh / 1.446 chuỗi / 470 địa điểm / 1.604 GT box**.
- Cách ly **219 ảnh**: 5 trùng RGB chính xác, 191 nghi trùng gần đang chờ rà,
  23 mơ hồ trong kiểm tra trực quan. `1.446 + 219 = 1.665`.
- Train mới: **4.246 ảnh / 3.723 chuỗi / 540 địa điểm / 4.729 crop**.
  Tăng 51,64% số ảnh so với 2.800 train cũ; không hứa mức tăng accuracy tương ứng.
- **Validation 600 ảnh / 680 crop và Test cũ 600 / 680 giữ nguyên byte**.
  Không đổi nhãn/split nguồn, không tự bù mẫu, không train hoặc suy luận B2/DINO.
- Snapshot: [`train_expansion_w6_v1`](../../data/processed/train_expansion_w6_v1/summary.json),
  `quality_ready=true`, `peer_review_status=pending_TV2`.
  Đây là chất lượng theo protocol bên dưới, không chứng nhận chuyên gia cho mọi ảnh.

## 2. Phân bố thực tế

| Lớp | Xin bổ sung | Giữ thêm | Loại/cách ly | Train mới | Chuỗi train | Địa điểm train | Crop train |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 · large_antlered_muntjac | 250 | 234 | 16 | 584 | 562 | 199 | 602 |
| 1 · annamite_striped_rabbit | 13 | 10 | 3 | 360 | 212 | 61 | 360 |
| 2 · sambar | 250 | 222 | 28 | 572 | 530 | 167 | 666 |
| 3 · chinese_serow | 206 | 164 | 42 | 514 | 451 | 148 | 529 |
| 4 · common_palm_civet | 250 | 186 | 64 | 536 | 462 | 173 | 539 |
| 5 · masked_palm_civet | 208 | 171 | 37 | 521 | 435 | 220 | 528 |
| 6 · silver_pheasant | 238 | 220 | 18 | 570 | 499 | 179 | 735 |
| 7 · eurasian_wild_pig | 250 | 239 | 11 | 589 | 572 | 300 | 770 |
| **Tổng duy nhất** | **1.665** | **1.446** | **219** | **4.246** | **3.723** | **540** | **4.729** |

Không cộng các hàng địa điểm thành tổng vì một địa điểm có nhiều lớp.
Train cũ 350 ảnh/lớp; nay lớp ít nhất 360 và nhiều nhất 589 ảnh (tỷ lệ 1,64).
Thỏ vằn chỉ thêm **10/13** ảnh; không thể coi đây là mở rộng cân bằng tám lớp.
TV3 giữ cách tính loss theo ảnh, báo từng lớp; không âm thầm thêm sampler/class
weight trong cùng lượt được đăng ký là “chỉ thay dữ liệu”.

## 3. Kiểm định và cách xử lý ảnh nghi vấn

### Tải, nội dung và chia tập

Đã kiểm tra decode hoàn chỉnh, kích thước gốc, byte SHA và RGB SHA của tổng
**5.774 ảnh**: 4.000 pilot + 1.665 train ứng viên + 109 holdout đối chiếu.
Ảnh giữ được đối chiếu byte lại trước phát hành; cache decode chỉ dùng lại
khi byte SHA vẫn khớp. Geometry theo comparison cũ: round-half-even, clip,
padding 0, cạnh crop tối thiểu 8 px; giữ mọi box của ảnh được nhận.

109 holdout được tải **chỉ để kiểm tra chất lượng và trùng nội dung**,
173.588.482 byte. Không xem trực quan ảnh holdout/Test trong đợt rà mẫu,
không chạy mô hình hoặc phát hành test mới. Nguồn này vẫn thiếu hỗ trợ từng lớp.

Không giao ID/đường dẫn/chuỗi/địa điểm giữa train mở rộng và các split bảo vệ;
không có RGB trùng chính xác giữa ảnh mới giữ và ảnh cũ/holdout. Địa điểm giữa
train cũ và train mới được phép trùng. Kiểm tra trên nguồn trước lọc cũng không
phát hiện rò rỉ metadata. Không chọn ảnh theo prediction hoặc điểm confidence.

### Trùng chính xác và sàng lọc gần trùng

- Có 4 nhóm nội dung trùng chính xác trong toàn bộ nguồn đối chiếu; file báo
  ghi 8 mục vì kiểm tra riêng SHA byte và RGB. Ba nhóm liên quan **5 ảnh mới**,
  nhóm còn lại là cặp trong Test cũ đã được báo cáo từ trước, được giữ nguyên.
- So toàn khung hình bằng pHash DCT 64 bit (khoảng cách ≤4) **và** dHash
  ngang+dọc 128 bit (≤8), trước khi nhìn ảnh mẫu. **347 cặp đều là train/train**,
  liên quan 193 ảnh mới, trong đó 2 đã thuộc nhóm trùng chính xác.
- Vì vậy 191 ảnh có lý do chính `near_duplicate_pending_review` được cách ly,
  không gọi chúng là 191 ảnh chắc chắn trùng hoặc 347 cặp rò rỉ Test. Nền cùng
  camera có thể gây dương tính giả. Toàn bộ cờ và khoảng cách được giữ để TV2
  rà; muốn đưa lại vào train cần release mới, không chỉnh snapshot này.
- Đây là sàng lọc toàn ảnh, không phải chứng minh không còn mọi dạng near-duplicate
  hoặc crop giống nhau. Không dùng pretrained classifier để quyết định giữ/loại.

**Phạm vi file audit:** `audit.json` là kết quả hàm dùng chung cho metadata và
RGB chính xác; câu `near duplicates NOT checked` trong `image_content_note`
chỉ mô tả phạm vi hàm đó. Bước sàng lọc pHash/dHash riêng của W6 có bằng chứng
trong `features.jsonl`, `near_duplicates.json` và `scan_result.json`. Không
được dùng riêng một trường của audit chung để kết luận về toàn bộ pipeline.

### Rà trực quan mẫu và các ví dụ lỗi

Chọn cố định seed 42, **10 ảnh/lớp**, sau bước cách ly tự động; xem 80 ảnh
kèm toàn cảnh và tất cả crop. **Codex trợ lý thực hiện kiểm tra trực quan**,
chưa phải một chuyên gia động vật hoặc review của TV2. Giữ nhãn metadata
cho 57 mẫu; cách ly cả ảnh cho 23 mẫu không đủ chi tiết do tối, mờ, che khuất
hoặc cắt quá nhiều ở biên. Không sửa nhãn hoặc bỏ riêng box để làm ảnh “đạt”.

| Chỉ số mẫu | Lớp | Quan sát và quyết định |
| --- | --- | --- |
| 9 | `large_antlered_muntjac` | Chỉ phần hông/lưng sát mép dưới, thiếu đầu và hầu hết chân; cách ly chờ rà. |
| 15 | `annamite_striped_rabbit` | Ảnh mờ và trắng sương, chi tiết đầu/thân khó phân biệt; cách ly chờ rà. |
| 30 | `sambar` | Box rất sát góc ảnh, chỉ mảnh nhỏ thân giữa lá, không đủ chi tiết để rà; cách ly. |
| 38 | `chinese_serow` | Gần như toàn tối, không đủ chi tiết con vật để rà; cách ly. |
| 48 | `common_palm_civet` | Vùng box bị gỗ/cây và bóng tối che gần hết; không xác nhận được vùng con vật, cách ly. |
| 56 | `masked_palm_civet` | Chủ yếu vệt sáng/thân hoặc đuôi sát mép dưới, không đủ đối tượng để rà; cách ly. |
| 68 | `silver_pheasant` | Ba box, một box ở mép trái chỉ còn mẩu đuôi/vệt mờ; cách ly cả ảnh, không tự bỏ riêng box đó. |
| 76 | `eurasian_wild_pig` | Chỉ mảng lưng/lông sát máy, thiếu đầu/chân và hình dáng; cách ly. |

Mẫu 64 có box chồng nhau: đã xem ảnh phóng to, có **ba con chim thực sự**,
không tự loại box chỉ vì chồng nhau. Đối chiếu đầy đủ trong
[visual_review.json](visual_review.json), có ID/SHA/quyết định/quan sát cho đủ 80 mẫu.

Không phải mọi ảnh giữ đều rõ hoặc đã được rà bởi chuyên gia; còn ảnh IR,
nhòe vừa, góc sau, khác giới tính và nhiều con. 23/80 là kết quả triage của
mẫu đã sàng lọc, **không phải tỷ lệ nhãn sai của toàn dataset**. Các ảnh nghi
trùng ngoài mẫu vẫn chờ rà, không được tự coi là đã xác nhận bằng mắt.

## 4. Bằng chứng tái lập

| Kiểm tra | Kết quả / bằng chứng |
| --- | --- |
| Snapshot W5 và nguồn trước tải | PASS — [source_verification.json](source_verification.json) |
| Tải tất cả ID, không ảnh thay thế | PASS — [summary](download_summary.json), [log train](train_download_events.jsonl), [log đối chiếu](holdout_download_events.jsonl) |
| Decode/hash và screening 5.774 ảnh | PASS trong phạm vi mô tả — [scan_result.json](scan_result.json) |
| Phát hành write-once | [release_result.json](release_result.json) |
| Validator từ snapshot, không cần state tải | PASS — [verify_result.json](verify_result.json) |
| Checkout sạch từ Git index, không có ảnh/state tải | PASS — [portable_checkout_verification.json](portable_checkout_verification.json) |
| Kiểm tra độc lập ID/split/count/crop weight | PASS — [independent_audit.json](independent_audit.json) |
| Chạy thật wrapper resume sau phát hành | PASS, mọi byte snapshot và log tải giữ nguyên — [resume_check.txt](resume_check.txt) |
| Manifest crop bị sửa trong bản sao tạm | Bị từ chối do checksum, bản thật không thay đổi |
| 72 kiểm thử downloader/manifest/comparison/W5/W6 | PASS — [tests.txt](tests.txt), 10,282 giây |
| ZIP ảnh bàn giao | Đủ membership, đọc lại SHA từng entry khớp — [image_package.json](image_package.json) |

Lần portable verify không decode lại tất cả ảnh lần nữa (`images_redecoded=false`);
việc decode đã thực hiện ở scan, byte được kiểm tra lại trước phát hành. TV2 có
thể chạy `verify --check-images` độc lập khi có đủ ảnh. Kiểm thử 72 test tập
trung phần dữ liệu, không phải báo cáo chạy lại toàn bộ test web/training W5.

Provenance SHA-256:
`a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`.
Môi trường: Python 3.12.10, Pillow 12.2.0, NumPy 2.5.3, SciPy 1.18.1.
Git attributes giữ đúng newline của requirements và log kiểm thử để checksum
không thay chỉ vì checkout Windows/Colab. Không đổi phiên bản package mô hình.
Bản checkout sạch đã được kiểm tra thực tế trên máy Windows hiện tại; chưa
thực hiện một lượt chạy Colab mới chỉ để kiểm định dữ liệu này.

## 5. File gửi TV2 và TV3

Đọc [hướng dẫn bàn giao](../../docs/handoff_tv1_w6.md) để tải, xác minh và dùng
đúng manifest. Ảnh ở ngoài Git; chưa có link cloud được tạo trong nhiệm vụ này.

- ZIP ảnh bổ sung và manifest: `outputs/tv1_w6/swg_train_expansion_w6_v1_additional.zip`.
  **2,246,204,406 byte**, gồm 1.446 ảnh được giữ và 19 file snapshot;
  cần bộ `swg_pilot_v2` cũ riêng. SHA: `a88bfbf99aa25ac70637f35dca6056851e4c300dd89c3906185f943b13b3f659`.
- ZIP bằng chứng trực quan: `outputs/tv1_w6/visual_review_contact_sheets.zip`,
  10 contact sheet và 1 ảnh zoom, kèm queue/quyết định; [checksum](visual_package.json).
- TV3 chỉ dùng `b2/train.jsonl` mới cho R5/R6 sau TV2 review. R1/R2 và kiểm tra
  seed trên dữ liệu cũ tiếp tục dùng `comparison_v1`; val luôn là cùng 600 ảnh.
- Nhãn/class map, ngữ nghĩa crop, nhóm ảnh và quy tắc mean vector softmax cấp ảnh
  không đổi. Loader W6 là nhiệm vụ TV3; chưa sửa loader/source đã khóa của W5.

## 6. Giới hạn và việc tiếp theo

TV1 đã hoàn thành phần có thể thực hiện độc lập: kế hoạch, tải, kiểm định,
manifest, log, ví dụ lỗi, gói ảnh và cách resume. TV2 vẫn phải review release;
TV3 chưa chạy R1–R6 và TV4 chưa tích hợp model W6 chỉ vì dữ liệu này tồn tại.

Đối chứng là DINOv3_LP_run01 **84,50% accuracy / 84,4401% macro-F1 validation**.
Mục tiêu ≥88% là ≥528/600 ảnh đúng thay vì 507/600; vẫn phải đo thực tế. So
recipe mới trên train cũ trước, rồi chỉ thay dữ liệu ở lượt mở rộng. Không
đánh đổi class khó, dùng Test để chọn model hoặc gọi validation đã tái dùng
là kiểm chứng độc lập. Muốn tuyên bố tổng quát hóa tốt hơn cần thêm holdout
đủ lớp/chuỗi/địa điểm theo protocol ở giai đoạn sau gia hạn.

Kế hoạch hiện hành: [TV1](../../docs/plans/TV1_W6.md),
[TV2](../../docs/plans/TV2_W6.md), [TV3](../../docs/plans/TV3_W6.md),
[TV4](../../docs/plans/TV4_W6.md). [Progress](../../docs/progress_tv1_w6.md)
chỉ rõ trạng thái local/Git và lệnh tiếp tục; không tự coi là đã push hoặc merge.
