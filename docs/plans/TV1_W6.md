# TV1 — Tuần 6: mở rộng train có kiểm định và giữ phép so sánh công bằng

**Cập nhật:** 03/11/2026. **Nhánh:** `feat/metadata-split`. **Người kiểm tra:** TV2.
Khởi động tối 03/11; lịch làm việc đề xuất **04–10/11/2026**, giờ Việt Nam.
Giảng viên cho thêm vài tuần nhưng chưa chốt hạn mới. Tuần này chuyển sang
cải thiện mô hình; đây không phải hạn nộp chính thức được giảng viên xác nhận.

## Mục tiêu chung và phần việc TV1

Đối chứng trực tiếp là **`DINOv3_LP_run01`: accuracy 84,50%, macro-F1 84,4401%**
trên 600 ảnh validation / 680 GT crop. Nhóm phấn đấu accuracy **≥88%**, đồng
thời tăng macro-F1; chưa cam kết đạt. TV3 thử pooling và fine-tune nhẹ trên dữ
liệu cũ trước, rồi thử dữ liệu mở rộng riêng để phân biệt hai nguồn cải thiện.
Các điểm trên là phân loại từ GT box, không phải điểm toàn hệ thống detector.

TV1 biến **1.665 ứng viên train W5** thành một bản dữ liệu có chất lượng và
truy vết. Không đổi nhãn/split để tăng điểm, không tải toàn bộ SWG, không
chạy mô hình trên Test. Giữ nguyên `comparison_v1` và snapshot ứng viên W5.

## Đầu vào và sản phẩm cần bàn giao

- Nguồn: `data/processed/w5_candidates_v1/train_extension_candidates.jsonl`;
  1.665 ảnh / 1.665 chuỗi mới / 480 địa điểm / 1.835 box, chỉ `split=train`.
- Pilot đã khóa: train 2.800, val 600, Test 600 ảnh; train 3.125 GT crop.
- Bản phát hành mới: `data/processed/train_expansion_w6_v1/`, gồm manifest
  train, view toàn ảnh/crop, class map, số giữ/loại, audit, policy và SHA nguồn.
  **Tối đa 4.465 ảnh train / 4.960 crop**, số thực tế phụ thuộc kiểm định.
- Log tải tiếp tục, danh sách lỗi, bằng chứng kiểm tra trực quan và báo cáo:
  `reports/tv1_w6/REPORT.md`, `docs/handoff_tv1_w6.md`,
  `docs/progress_tv1_w6.md`. Đây là đầu ra phải tạo, không phải đã nghiệm thu.
- Ảnh/trạng thái/cache để trong `data/images/`, `data/interim/`, `outputs/`,
  không đưa vào Git. Bàn giao kèm lệnh tải lại đúng manifest và checksum.

## Lịch và việc thực hiện

| Ngày | Công việc | Kết quả kiểm tra được |
| --- | --- | --- |
| D1 — 04/11 | Khóa quy tắc chất lượng, nguồn, seed và lưu progress; kiểm tra dung lượng | Config và lệnh tiếp tục |
| D2 — 05/11 | Tải 1.665 ảnh với retry/receipt; decode, kích thước, byte/RGB SHA | Log đủ mọi ID, không thay ảnh tải lỗi |
| D3 — 06/11 | Kiểm tra rò rỉ, trùng nội dung, box và mẫu nhãn trực quan | Danh sách giữ/loại/cần rà, bằng chứng |
| D4 — 07/11 | Xuất snapshot mới; TV2 kiểm tra trước khi TV3 sử dụng | Manifest có quality và SHA, số mẫu từng lớp |
| D5 — 08/11 | Hỗ trợ TV3 nạp đúng bản; đối chiếu log dữ liệu thí nghiệm mở rộng | Cùng 600 val cũ, không lẫn split |
| D6 — 09/11 | Phân tích mất cân bằng, hạn chế nhãn/chuỗi và phương án thêm dữ liệu | Phần dữ liệu cho báo cáo chung |
| D7 — 10/11 | Bàn giao, review chéo TV2 và kiểm tra tái lập | Báo cáo trạng thái thực tế, việc còn lại |

Có thể hoàn thành sớm các bước không phụ thuộc thành viên khác; không ghi nhận
TV2 đã duyệt khi chưa có bằng chứng review của TV2.

## Quy tắc chất lượng bắt buộc

1. Tải có tiếp tục theo từng ảnh; ghi cả 404, timeout, ảnh hỏng, file thiếu,
   kích thước sai. Không lặng lẽ thay bằng ảnh khác hoặc bỏ qua ID chưa xử lý.
2. Xác nhận một loài, mọi box cùng nhãn, hình học theo `comparison_v1`:
   round-half-even, clip, padding 0, cạnh crop tối thiểu 8 px. Giữ mọi box hợp lệ.
3. So sánh ID/đường dẫn/chuỗi/địa điểm với train/val/Test cũ và 109 holdout
   ứng viên. Địa điểm giữa train cũ và train mới được trùng; chuỗi mới phải mới.
4. Kiểm tra SHA byte và RGB với toàn bộ 4.000 ảnh cũ và ảnh mới. Có thể tải
   109 holdout **chỉ để kiểm tra chất lượng/trùng nội dung**, không suy luận
   model, không dùng làm tập chọn mô hình hoặc gọi là test mới đủ điều kiện.
   Nếu đối chiếu ảnh nào chưa thực hiện được, công khai và giữ release chưa sẵn sàng.
5. Ảnh mới trùng chính xác hoặc nghi near-duplicate chưa được giải quyết được
   cách ly khỏi train mới, ghi lý do; ảnh gốc đã khóa giữ nguyên. Near-duplicate
   là tín hiệu cần rà, không đồng nghĩa chắc chắn trùng hoặc nhãn sai.
6. Rà trực quan theo mẫu cố định seed 42: ít nhất 10 ảnh/lớp nếu đủ. Mọi ảnh
   gắn cờ phải được rà trước khi giữ hoặc cách ly với trạng thái chờ rà;
   không mặc định đã kiểm tra bằng mắt toàn bộ ảnh cách ly. Xem box/khả năng nhận diện; không tự sửa nhãn
   loài khó chỉ dựa dự đoán model. Mẫu mơ hồ cách ly và ghi nhận cần chuyên gia.
   Báo rõ đây là kiểm tra mẫu, không chứng nhận chuyên gia cho mọi ảnh.
7. Nhãn/box bất thường được ghi riêng, không sửa bản gốc. Mẫu loại không được
   bù tự động; thống kê trước/sau và tất cả lý do loại, không chỉ tổng giữ.

## Tiêu chí hoàn thành

- 1.665 ứng viên đều có quyết định; `giữ + loại = 1.665`. Mọi ảnh giữ có
  nguồn, quality và crop view; tải lại/resume không làm đổi snapshot đã khóa.
- 2.800 ảnh train cũ và 600 val/600 Test cũ giữ nguyên; không giao chuỗi/địa
  điểm giữa các split của train mở rộng và các tập bảo vệ. SHA nguồn không đổi.
- Báo số ảnh/chuỗi/địa điểm/box từng lớp và giới hạn: thỏ vằn chỉ có **13**
  ứng viên mới, train mở rộng sẽ mất cân bằng; không nói “thêm dữ liệu đều 8 lớp”.
- Phân biệt `quality_ready` với `peer_review_status`; TV2 phải kiểm tra release
  trước lượt mở rộng của TV3. Chưa có test độc lập đủ hỗ trợ cho tám lớp.
- Công cụ kiểm định có kiểm thử tình huống lỗi/rò rỉ/resume; không sửa loader
  W5 để ép nhận dữ liệu mới. TV3 triển khai loader W6 theo contract riêng.

## Phối hợp, Git và tiếp tục khi gián đoạn

TV1 không cần GPU. TV2 nhận manifest và audit; TV3 chỉ dùng release đã review,
không nạp trực tiếp danh sách ứng viên W5; TV4 nhận dataset ID cho model card.
Commit phần mình trên nhánh cố định; PR nêu counts, loại, SHA và kiểm thử.

Progress phải ghi bước xong, tiến trình còn chạy, lệnh tiếp tục và đường dẫn
log/state. Trước chạy lại kiểm tra tiến trình; không chạy hai writer, không
xóa state để làm lại, không ghi đè snapshot đã khóa. Nếu quy tắc đổi, tạo v2.
TV2/TV3 có thể thử trên train cũ trong khi chờ release, nên tải ảnh không chặn R1/R2.

Kế hoạch liên quan: [TV2](TV2_W6.md), [TV3](TV3_W6.md), [TV4](TV4_W6.md).
