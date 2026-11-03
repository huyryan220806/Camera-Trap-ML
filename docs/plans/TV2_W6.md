# TV2 — Tuần 6: protocol đối chứng DINO và kiểm định cải thiện

**Cập nhật:** 03/11/2026. **Nhánh:** `feat/baseline`. **Người kiểm tra:** TV1.
Lịch đề xuất **04–10/11/2026**, khởi động tối 03/11. Giảng viên đã gia hạn,
chưa có hạn nộp mới. Kế hoạch này thay phần W6 “chỉ đóng gói” trong plan cũ.

## Mục tiêu và đối chứng

Chứng minh ứng viên có tốt hơn **DINOv3_LP_run01 (R0)** trên cùng 600 ảnh val
/ 680 GT crop hay không: accuracy **84,50%**, macro-F1 **84,4400828%**.
Mục tiêu accuracy **≥88%**, kèm tăng macro-F1; không đảm bảo trước kết quả.
Giữ B2 như đối chứng phụ (val accuracy 74,6667%, macro-F1 74,5477%).
88% tương ứng ít nhất **528/600 ảnh đúng**, cao hơn W5 507/600 là 21 ảnh
đúng ròng trên cùng tập. Số gốc trong
[biên bản nghiệm thu W5](../../reports/tv2/TV2_W5_DINO_ACCEPTANCE_2026-11-02.md).

W5 đã khóa protocol riêng; **không sửa protocol/log/checkpoint W5**. TV2 tạo
protocol và registry W6 trước các lượt mới. Chọn theo macro-F1 cấp ảnh, báo
accuracy, từng lớp và tất cả seed; kết quả vẫn là validation đã dùng để chọn
mô hình, chưa phải kiểm chứng trên test độc lập.

## Ma trận thí nghiệm cần đăng ký cùng TV3

| ID | Thay đổi chính | Train | Seed | Điều kiện |
| --- | --- | --- | --- | --- |
| R0 | DINOv3_LP_run01 đã có | 2.800 ảnh cũ | 42 | Đối chứng, không train lại |
| R1 | Frozen backbone, CLS + mean patch → head 768D | Cũ | 42 | Thử pooling |
| R2 | Fine-tune 2 block cuối + norm + head, CLS 384D | Cũ | 42 | Khởi tạo từ W5; recipe mới |
| R3, R4 | Lặp recipe thắng trên dữ liệu cũ | Cũ | 43, 44 | Khi R1/R2 vượt R0 và còn ngân sách |
| R5, R6 | Recipe được chọn với train mở rộng | Release TV1 | 42, 43 | Dữ liệu được TV2 duyệt và còn ngân sách |

Nếu R1/R2 không vượt R0, R5/R6 có thể dùng recipe R0 như nhánh điều kiện đã
đăng ký trước. Nếu thiếu thời gian, ưu tiên R1/R2 và kiểm tra seed; hoãn mở rộng.
**Tối đa 6 lượt mới**, kể cả lượt chính thức thất bại/dừng sớm; không thay chúng
bằng tìm kiếm cấu hình ngầm. TV3 tối đa 12 GPU-giờ gồm trích xuất, ≤2 giờ/lượt;
TV2 tối đa 2 GPU-giờ replay. Đây là trần đề xuất, chưa phải lịch GPU đã đặt.

## Việc cần làm

1. Tạo `docs/experiment_protocol_w6.md`, registry `experiments/w6/registry.json`
   và config có run ID, SHA dữ liệu/trọng số/source, pooling, recipe, seed,
   batch, số epoch, tiêu chí chọn/tie và trần tài nguyên. Chốt sau smoke **train**,
   trước xem metric lượt chính thức. Không dùng val để thử hàng loạt tham số.
2. Dùng toàn bộ 600 val, không lọc theo điểm tin cậy hay ảnh dự đoán đúng.
   Gộp trung bình **vector softmax mọi crop cùng ảnh**, argmax một lần; class
   map cố định tám lớp. Loss train theo ảnh, không nhân trọng số crop hai lần.
3. Kiểm tra TV1: ảnh mới hợp lệ, counts/quality/hash, train-only, không rò rỉ,
   val/Test không đổi. Ghi quyết định review có SHA release; không duyệt chỉ
   vì manifest tồn tại. Viết validator W6 riêng, giữ validator W5 nghiêm ngặt.
4. Đối chiếu prediction đủ ID và score vector: accuracy, macro-F1, precision/
   recall/F1/support từng lớp, confusion matrix, 95% CI nếu thực hiện đúng
   cụm địa điểm. Bootstrap phải lấy cùng cụm cho các model, seed cố định;
   CI trên val được tái dùng chỉ có ý nghĩa thăm dò, không biến thành test mới.
5. Ưu tiên phân tích cặp cầy: lỗi nhầm hai chiều W5 là 13 so với B2 là 7;
   masked palm civet đúng 56/75; muntjac đúng 54/75. Không chỉ báo điểm tổng.
6. Chọn seed 42 theo macro-F1; hòa thì accuracy, rồi chi phí suy luận thấp hơn,
   cuối cùng ID đã đăng ký trước. Seed 43/44 dùng đo độ dao động, **không lấy
   seed tốt nhất thay headline**. Báo từng seed và mean/SD; R0 chỉ có một seed,
   nên chưa có bằng chứng so sánh nhiều seed cân xứng với baseline.
7. Trước đề nghị đổi model demo: macro-F1 tăng, accuracy không giảm so với R0,
   checkpoint/source/adapter/reload đạt; rà mọi lớp giảm recall từ 4/75 ảnh
   trở lên và ghi lý do chấp nhận/giữ model cũ. +1 điểm phần trăm macro-F1 là
   mục tiêu thực dụng, không phải ngưỡng có ý nghĩa thống kê được chứng minh.
8. Replay đầy đủ val từ checkpoint trong tiến trình mới, cùng runtime đã pin.
   Chốt chính sách sai số trước chạy nếu so CPU/GPU; không nới tolerance sau
   khi thất bại. R2 đổi cả optimizer/augmentation: gọi là so recipe, không
   quy toàn bộ cải thiện cho việc mở khóa hai block.

## Lịch và bàn giao

| Ngày | Trọng tâm | Bàn giao |
| --- | --- | --- |
| D1 — 04/11 | Protocol, registry, kiểm tra R0 và config TV3 | Ma trận đã chốt, hash đầu vào |
| D2–3 — 05–06/11 | Validator/metric W6, review R1/R2 | Bảng cùng ảnh, lỗi từng lớp |
| D4 — 07/11 | Review release TV1; chọn recipe theo rule | Quyết định dữ liệu và recipe |
| D5 — 08/11 | Đối chiếu seeds; lượt mở rộng nếu có | Kết quả tách recipe khỏi dữ liệu |
| D6 — 09/11 | Replay checkpoint, đối chiếu adapter TV4 | Biên bản tái lập và gói chấp nhận |
| D7 — 10/11 | Kết luận thắng/thua/chưa đủ bằng chứng | `reports/tv2/TV2_W6.md` và bảng kết quả |

Các đường dẫn W6 là sản phẩm cần tạo. TV4 nhận checkpoint SHA/config/nhãn/
preprocess kèm quyết định cụ thể; chưa đạt thì giữ DINO W5. Lưu cả run lỗi,
thời gian và nguyên nhân, không xóa experiment không cải thiện.

## Hoàn thành và tiếp tục

Hoàn thành khi protocol + registry + báo cáo + review dữ liệu + replay có
bằng chứng và khớp số, kể cả chưa đạt 88%. Không mở Test cũ để chọn threshold,
checkpoint hoặc báo “thắng” bằng cách so hai tập khác nhau. 109 holdout ứng
viên chưa đủ hỗ trợ; kế hoạch test độc lập mạnh hơn chuyển sang tuần sau.

Commit trên `feat/baseline`, lưu progress có bước/lệnh/path/hash/tiến trình.
Khi bị ngắt, tiếp tục từ registry và output đã xác minh, không chạy lại toàn
bộ lượt để chọn kết quả đẹp. Không tự điền review của người khác.

Tham khảo nguyên tắc tách tập phát triển và đánh giá:
[scikit-learn — data leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).
Kế hoạch liên quan: [TV1](TV1_W6.md), [TV3](TV3_W6.md), [TV4](TV4_W6.md).
