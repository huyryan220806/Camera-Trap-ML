# TV4 — Tuần 6: tích hợp ứng viên DINO mới và đo chi phí thực tế

**Cập nhật:** 03/11/2026. **Nhánh:** `feat/demo`. **Người kiểm tra:** TV2;
TV3 kiểm tra score adapter, TV1 kiểm tra thông tin dữ liệu.
Lịch đề xuất **04–10/11/2026**, chưa phải hạn nộp mới. Giảng viên đã gia hạn;
tuần này hỗ trợ cải thiện mô hình, dời gói bảo vệ cuối cùng sang lịch chốt sau.

## Mục tiêu

Demo đã có DINOv3_LP_run01, B2, nhiều box/top 3, duyệt nhãn, batch và CSV.
Tuần 6 cần nhận được ứng viên mới **khi vượt kiểm định**, đồng thời so chất
lượng và chi phí với DINO W5 (val accuracy 84,50%, macro-F1 84,4401%). Nhóm
phấn đấu ≥88% accuracy nhưng TV4 không hứa mức điểm này trên ảnh người dùng.

Không phải xây lại UI từ đầu. Ưu tiên adapter/config/cache và lỗi thực tế;
chỉnh giao diện phục vụ chọn model, nguồn kết quả và trạng thái cần kiểm tra.
Nền chạy/test hiện tại: [hướng dẫn W5](../run_and_test_w5.md),
[contract UI/adapter W5](../tv4_w5_demo.md).

## Việc phải làm

1. Thống nhất contract W6 với TV3/TV2: model ID/version, checkpoint SHA,
   vendor/source hashes, class map, preprocessing, pooling 384D/768D, tầng
   được fine-tune và dataset ID. TV3 cung cấp weights thật và mã nạp độc lập.
2. Adapter W5 đang khóa checkpoint/source. Tạo registry/adapter W6 riêng có
   kiểm định config + hash, không bỏ kiểm tra để nạp mọi file `.pt` và không
   sửa source W5 đã khóa. Sai checkpoint phải báo lỗi, không tự đổi sang B2.
3. Hỗ trợ CLS+mean patch 768D hoặc CLS384D với backbone đã fine-tune; kiểm tra
   logits/vector với native TV3 trên fixture nhiều crop và ảnh thật. Cache key
   gồm SHA trọng số, config/preprocess/source/device; đổi model làm hết hiệu
   lực cache tương ứng. Model chưa được TV2 duyệt chỉ được gắn nhãn thử nghiệm.
4. Mỗi box hiển thị top 3, điểm dự đoán chưa hiệu chỉnh. Giữ ngưỡng review .70
   của demo nếu chưa có nghiên cứu ngưỡng riêng; không gọi điểm là xác suất
   đã hiệu chỉnh, không kết luận loài lạ, không loại ảnh điểm thấp để tăng accuracy.
5. Giữ DINO W5 và B2 dùng được. Chỉ đổi mặc định sau biên bản TV2 có cải thiện
   và kiểm định tích hợp; nếu ứng viên không thắng, hoàn thành bằng hỗ trợ
   adapter và giữ model cũ. Không mặc định “mới hơn thì tốt hơn”.
6. UI ghi model/dataset version và loại đánh giá. GT-box validation không
   thay cho toàn bộ detector → classifier. MegaDetector có SWG trong huấn
   luyện; nhắc giới hạn này, ghi cả ảnh không phát hiện và lỗi detector.

## Đo tốc độ có thể so sánh

- Khóa **24 ảnh train, 3 ảnh/lớp**, chọn seed 42 trước đo; lưu ID và SHA.
  Cùng bộ ảnh, cấu hình detector, resize và máy cho W5 và ứng viên W6.
- Ghi CPU/GPU, RAM/VRAM, OS, runtime/threads, MD version/SHA, ngưỡng và image
  size detector, classifier square 256, batch ảnh 1, crop microbatch 8.
- Đo cold load trong tiến trình mới; hai vòng warm trên 24 ảnh (48 request/model).
  Báo mean/p50/p95, số ảnh/số box, thời gian detector/classifier/end-to-end,
  mẫu lỗi/no_detection và phạm vi phép đo. Không gọi 48 request là 48 ảnh độc lập.
- CPU là đường chạy bắt buộc trên máy hiện tại; GPU chỉ khi có thiết bị và
  đặt lịch, tối đa **2 GPU-giờ** TV4. Đây là trần đề xuất, chưa có booking.
  Không ngoại suy số CPU thành GPU hoặc ngầm đổi device khi OOM.
- File đầu ra dự kiến: `reports/tv4_w6/benchmark.json`, danh sách ảnh đo,
  cấu hình máy, log suy luận và `reports/tv4_w6/REPORT.md`.

## Lịch và phụ thuộc

| Ngày | Việc TV4 | Bàn giao |
| --- | --- | --- |
| D1 — 04/11 | Chốt contract TV3; kiểm tra demo W5 còn chạy | Danh sách trường config/model card |
| D2 — 05/11 | Registry/adapter W6, cache, lỗi hash/format | Code và kiểm thử có ý nghĩa |
| D3 — 06/11 | Fixture benchmark train, UI model/version/review | Danh sách ảnh và cách đo |
| D4 — 07/11 | Nhận checkpoint thử; kiểm định nạp/shape | Log nhận model, lỗi cụ thể nếu có |
| D5 — 08/11 | Đối chiếu native nhiều box; sửa tích hợp | Score equivalence, review TV3/TV2 |
| D6 — 09/11 | Benchmark CPU, GPU nếu có; hồi quy batch/review/CSV | Log tốc độ và hồi quy |
| D7 — 10/11 | Hướng dẫn chạy/test/chọn model, quyết định mặc định | Bàn giao TV1 và báo cáo W6 |

## Tiêu chí hoàn thành

- Không lỗi luồng ảnh hợp lệ/hỏng, nhiều box, no_detection, detector bỏ sót,
  model load/inference lỗi; không bịa box/kết quả thành công khi lỗi.
- Duyệt sửa nhãn giữ nguyên kết quả gốc, revision conflict 409, CSV một dòng
  mỗi box hoặc một dòng no-box/error, chỉ xuất review đã lưu; batch vẫn hoạt động.
- Model/cache thay đúng, thiếu weights thông báo rõ, CPU chạy được; kết quả
  adapter khớp native theo chính sách TV2 đã chốt, không nới sai số cho qua.
- Có báo cáo tốc độ cùng phần cứng/bộ ảnh, không dùng Test để chọn mẫu đẹp.
  Chụp UI desktop/mobile; cập nhật hướng dẫn chạy thật sau khi test xong.
- Báo giới hạn: detector dùng SWG, crop GT khác box detector, score chưa hiệu
  chỉnh, validation đã dùng chọn model, chưa có test độc lập đủ mạnh.

Lưu `docs/progress_tv4_w6.md` sau mỗi mốc, kèm commit/run/config/SHA và lệnh
tiếp tục. Commit trên `feat/demo`, không đưa weights/ảnh/cache vào Git. Không
ghi đã tích hợp khi mới chỉ có config; chờ TV2/TV3 bàn giao weights đã kiểm định.

Kế hoạch liên quan: [TV1](TV1_W6.md), [TV2](TV2_W6.md), [TV3](TV3_W6.md).
