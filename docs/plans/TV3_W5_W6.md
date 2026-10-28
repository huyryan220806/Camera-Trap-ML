# TV3 — Kế hoạch tuần 5–6: DINOv3, đối chứng B2 và bàn giao checkpoint

**Cập nhật:** 28/10/2026. **Branch:** `feat/crop-classifier`. **Người kiểm tra:** TV1;
TV2 kiểm tra cách tính metric, TV4 kiểm tra khả năng tích hợp.

Lịch đề xuất: tuần 5 **28/10–03/11**, tuần 6 **04/11–10/11** (giờ Việt Nam).
Hạn nộp chính thức vẫn theo lớp. Mục tiêu là thử mô hình hiện đại một cách có
đối chứng; accuracy ≥88% là mục tiêu phấn đấu, không phải điều kiện để sửa dữ liệu.

## 1. Trạng thái và dữ liệu được phép dùng

- Giữ B2 `b2_run01` làm đối chứng; SHA checkpoint:
  `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`.
- B3 còn `UNRESOLVED` với tham chiếu gốc. Không gọi thí nghiệm DINO mới là
  “B3 đã sửa”; đặt experiment ID riêng, ví dụ `DINOv3_LP_run01`.
- Lượt đầu dùng **`comparison_v1` train 2.800 ảnh / val 600 ảnh**, tương ứng
  **3.125 / 680 GT crop**. Tọa độ, class ID, nhãn và split giữ nguyên.
- TV1 có [1.665 ứng viên train bổ sung](../../data/processed/w5_candidates_v1/summary.json),
  nhưng **chưa tải/kiểm định ảnh mới, chưa có training release mở rộng**.
  Không truyền trực tiếp manifest ứng viên vào loader để huấn luyện.
- Holdout ứng viên chỉ 109 ảnh, thỏ vằn 1 ảnh: **chưa có test mới đủ điều kiện**.
  TV3 chỉ làm train/validation; Test B2 cũ không dùng chọn mô hình.

## 2. Hướng mô hình và giới hạn tài nguyên

Ưu tiên **DINOv3 ViT-S/16** với trọng số học sẵn. Bước đầu giữ nguyên backbone,
trích xuất đặc trưng từ GT crop, lưu cache và học bộ phân loại tám lớp.
Nguồn kiến trúc/trọng số: [repo DINOv3 chính thức](https://github.com/facebookresearch/dinov3).
Đây là phương án thử của nhóm, chưa phải mô hình đã chạy hoặc kết quả SOTA của đồ án.

Nếu ngày 1 chưa tải được trọng số/quyền truy cập, dùng **DINOv2 ViT-S/14** làm
phương án dự phòng, ghi đúng tên trong log/báo cáo. Nguồn:
[model card DINOv2](https://github.com/facebookresearch/dinov2/blob/main/MODEL_CARD.md).
Không dùng preprocessing hoặc patch size của DINOv3 cho DINOv2 theo giả định.

Không huấn luyện backbone từ đầu. Fine-tune một phần hoặc toàn bộ chỉ là bước
sau, khi có ngân sách GPU và kết quả validation cho thấy cần thiết. Ghi GPU,
VRAM, batch, AMP, thời lượng và môi trường thật; không giả định Colab luôn sẵn.

## 3. Tuần 5 — thứ tự triển khai

| Mốc | Công việc TV3 | Bàn giao |
| --- | --- | --- |
| Ngày 1 | Cùng TV2 chốt protocol; kiểm tra dữ liệu, weights, GPU và smoke loader | Config, nguồn/pretrained SHA, môi trường, kế hoạch số lượt |
| Ngày 2–3 | Adapter dữ liệu crop → đặc trưng; cache có hash; học bộ phân loại | Experiment đầu tiên, log, checkpoint best/last và dự đoán validation |
| Ngày 4–5 | Thử cấu hình/seed trong ngân sách; cân nhắc fine-tune sau linear probe | Bảng đối chứng cùng TV2, ứng viên đã chọn bằng validation |
| Ngày 6 | Nạp lại checkpoint trong tiến trình mới, đối chiếu đầy đủ dự đoán | Biên bản reload và gói model gửi TV4 |
| Ngày 7 | Hỗ trợ tích hợp, viết phương pháp và model card | `reports/tv3/TV3_W5.md`, kết quả và hướng dẫn nạp |

Các đường dẫn W5/W6 ở đây là **đầu ra cần tạo**, không phải đã tồn tại.

### Yêu cầu dữ liệu và huấn luyện

1. Đọc `comparison_v1/b2/train.jsonl` và `b2/val.jsonl`. Crop dùng đúng
   `bbox_xyxy` đã khóa, padding 0; preprocessing của backbone mới được khai
   báo thành cấu hình riêng, không sửa geometry trong snapshot chung.
2. Cache đặc trưng gắn với SHA ảnh, crop ID/tọa độ, dataset provenance,
   preprocessing, kiến trúc và SHA trọng số. Bất kỳ thành phần đổi thì cache
   phải là phiên bản khác. Chỉ cache backbone khi trọng số thực sự giữ nguyên.
3. Mỗi ảnh có tổng trọng số đóng góp ngang nhau: trung bình loss trong ảnh
   rồi trung bình giữa các ảnh, hoặc trọng số crop `1 / parent_crop_count`
   đúng một lần. Không vô tình ưu tiên ảnh có nhiều box.
4. Theo protocol TV2: mặc định chọn bằng macro-F1 cấp ảnh, đồng thời theo dõi
   accuracy mục tiêu ≥88%. Gộp **vector softmax của mọi crop cùng ảnh**, rồi
   argmax; không majority vote hoặc trung bình logits mà không đăng ký biến thể.
5. Chạy trước seed 42; nếu còn ngân sách, lặp ứng viên với seed khác đã đăng ký.
   Không công bố “ổn định” khi chỉ có một seed. Không đổi class map để tăng điểm.
6. Nếu train mở rộng được TV1 phát hành sau quality gate, mở experiment ID mới.
   Thỏ vằn có ít ảnh bổ sung; báo rõ mất cân bằng và tách hiệu ứng dữ liệu khỏi
   hiệu ứng kiến trúc. Không tự lấy ảnh validation/test để bù lớp thiếu.

### Gói checkpoint cho TV4 và TV2

- File weights thật, link/đường dẫn tải ngoài Git, kích thước và SHA-256.
- Config: backbone, head 8 lớp, feature pooling, preprocessing chính xác,
  thứ tự class ID, nguồn pretrained, dataset/provenance hash, seed và runtime.
- Mã nạp mẫu chạy được, không phụ thuộc biến đang có trong notebook.
- Dự đoán validation đầy đủ, metric chưa làm tròn, confusion matrix và log.
- Kết quả nạp lại trong tiến trình mới. Nếu có sai khác, báo rõ và điều tra;
  không nới dung sai metric để ép PASS như bài học từ B3.
- Model card: dữ liệu, mục đích, giới hạn 8 lớp/địa điểm, thiếu calibration,
  GT box khác detector box, nguồn pretrained và hạn chế kiểm chứng test.

TV4 cần adapter mới cho backbone mới; đổi đường dẫn checkpoint ResNet18 hiện
có không đủ. Thống nhất trước giao diện nạp model, batch crop, output 8 điểm và
metadata. Không im lặng fallback sang B2 nếu ứng viên lỗi.

## 4. Tuần 6 — tái lập và hỗ trợ bàn giao

| Mốc | Công việc | Đầu ra |
| --- | --- | --- |
| Ngày 1–2 | Hoàn thiện reload/model card; hỗ trợ TV2 đối chiếu | `reports/tv3/TV3_W6.md`, checkpoint cuối có hash |
| Ngày 3 | Cài sạch và chạy mẫu train/val với TV4; đo tốc độ inference | Mã nạp độc lập, thông số thiết bị và batch |
| Ngày 4 | Slide kỹ thuật và tập bảo vệ lần 1 | Giải thích được đặc trưng, transfer learning, crop và metric |
| Ngày 5 | Sửa điểm khó giải thích, tập lần 2 | Lời nói khớp đúng model đã chạy |
| Ngày 6–7 | Kiểm tra gói weights/config/log, sao lưu | Người khác nạp được, có B2 dự phòng |

Chỉ TV2 thực hiện đánh giá độc lập theo protocol nếu TV1 có tập mới đạt điều
kiện và model đã khóa. Hiện phương án mặc định là báo validation cho ứng viên,
giữ nguyên Test B2 lịch sử. Nếu không đạt 88%, báo số thật và phân tích giới hạn.

## 5. Bắt đầu và tiếp tục sau gián đoạn

Đọc [bàn giao TV1 W5](../handoff_tv1_w5.md) và [plan TV2](TV2_W5_W6.md).

```powershell
git fetch origin
git switch feat/crop-classifier
git merge --ff-only origin/feat/crop-classifier
git merge origin/main
.venv/Scripts/python.exe -X utf8 scripts/validate_comparison.py --report outputs/tv3_w5/comparison.json
```

Lệnh trên chỉ kiểm định dữ liệu/hash/decode, không chạy model Test. Dùng môi
trường/requirements mới có phiên bản rõ ràng nếu DINO cần dependency khác;
không nâng cả môi trường demo một cách âm thầm.

Tạo `docs/progress_tv3_w5_w6.md` trước lượt chạy đầu. Lưu best/last checkpoint,
optimizer/scheduler, epoch, RNG state và trạng thái AMP nếu có; lưu đặc trưng
theo shard kèm danh sách crop đã hoàn tất. Đặt trên ổ bền vững/Drive, không chỉ
trong runtime Colab. Nếu công cụ chưa hỗ trợ resume, ghi rõ phải chạy lại bước
nào; không hứa tiếp tục chính xác chỉ vì có best checkpoint.

Trước chạy lại kiểm tra job còn hoạt động, config/hash và log. Tên lượt mới
không ghi đè run cũ. Trước PR: chạy kiểm tra môi trường/hợp đồng, unittest toàn
bộ và `git diff --check`, gửi TV1/TV2 kiểm tra. Giữ `feat/crop-classifier` sau merge.
