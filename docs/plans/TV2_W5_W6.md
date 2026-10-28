# TV2 — Kế hoạch tuần 5–6: so sánh mô hình và kiểm định sản phẩm

**Cập nhật:** 28/10/2026. **Branch:** `feat/baseline`. **Người kiểm tra phần mô hình:** TV3; TV1 đối chiếu dữ liệu. TV2 đồng thời kiểm tra chéo phần ứng dụng của TV4.

Lịch đề xuất: tuần 5 **28/10–03/11**, tuần 6 **04/11–10/11**, giờ Việt Nam.
Đây là lịch làm việc, chưa phải hạn nộp đã được giảng viên xác nhận; nếu lịch lớp
khác, cả nhóm cùng dịch mốc, giữ thứ tự khóa dữ liệu → chọn model → đánh giá.

## 1. Trạng thái nhận bàn giao

- B2 là đối chứng đã kiểm định: validation accuracy **74,67%**, macro-F1 **74,55%**;
  Test cũ accuracy **73,00%**, macro-F1 **72,63%**, dùng GT boxes.
- B3 còn giới hạn tái lập tham chiếu gốc, không đưa vào bảng model đã nghiệm thu.
- TV1 đã kiểm kê [dữ liệu tuần 5](../../reports/tv1_w5/REPORT.md): 19.266 ảnh trong
  nguồn train mở rộng, chọn **1.665 ứng viên metadata**; chưa phải ảnh đã kiểm định.
- Tập test mới ở địa điểm chưa có trong lịch sử được rà chỉ có **109 ảnh**,
  thỏ vằn 1 ảnh, cầy vòi hương 3 ảnh. Trạng thái **chưa đủ hỗ trợ cho đánh giá
  độc lập 8 lớp**. Hiện chọn phương án đánh giá ứng viên trên validation.
- TV4 đã push UI lên `feat/demo`, code `0179d97`, đầu nhánh ghi nhận `fef2511`;
  [PR #8](https://github.com/huyryan220806/Camera-Trap-ML/pull/8) có trong progress
  của TV4 và đang chờ kiểm tra ở thời điểm báo cáo đó. Kiểm tra trạng thái PR
  thực tế trước review; không coi lời báo PASS của tác giả là nghiệm thu của TV2.

## 2. Tuần 5 — đầu ra và lịch cụ thể

| Mốc | Công việc TV2 | Bàn giao / người nhận |
| --- | --- | --- |
| Ngày 1 | Kiểm tra bàn giao TV1; chốt quy trình và ngân sách thí nghiệm cùng TV3 trước lượt chạy | `reports/tv2/W5_PROTOCOL.md` và bản cấu hình đã thống nhất |
| Ngày 2–3 | Kiểm tra loader, gộp crop, class map; đối chiếu B2 với thử nghiệm DINO đầu tiên | Bảng validation và dự đoán từng ảnh; báo lỗi cho TV3 |
| Ngày 3–4 | Review UI TV4 trên đúng commit PR #8, cả B2 thật và fixture lỗi | Biên bản TV2, screenshot, danh sách lỗi có bước tái hiện |
| Ngày 4–5 | So sánh các lượt chạy đã đăng ký; xem lớp ít mẫu, sai khác giữa seed nếu có | Bảng tổng hợp, cấu hình được chọn và lý do |
| Ngày 6–7 | Kiểm tra checkpoint nạp lại, kiểm tra adapter cùng TV4; viết chương thực nghiệm | `reports/tv2/TV2_W5.md`, bằng chứng số liệu, phần báo cáo |

Tên file W5/W6 ở đây là **đầu ra TV2 cần tạo**, không phải file đã có.

### Quy trình phải ghi trước khi chạy

1. Lượt đầu giữ `comparison_v1`: **2.800 ảnh train, 600 val**, 8 class ID cũ.
   Dùng view `b2/train.jsonl`, `b2/val.jsonl`, cùng GT crop và quy tắc mean
   vector softmax theo `image_id`, sau đó argmax. Không so metric crop với metric ảnh.
2. Mặc định tiếp tục chọn checkpoint theo **macro-F1 cấp ảnh**; báo accuracy
   để theo dõi mục tiêu ≥88%. Nếu đổi tiêu chí, ghi rõ trước lượt thử đầu,
   không đổi sau khi thấy kết quả. Ghi quy tắc xử lý hòa và ngân sách số lượt.
3. Bảng phải có: experiment ID, kiến trúc, nguồn pretrained, phiên bản train,
   seed, số ảnh/crop, accuracy, macro-F1, precision/recall/F1/support từng lớp,
   thời gian và cấu hình máy. Lưu vector điểm, nhãn dự đoán và ID trước làm tròn.
4. Thử train mở rộng chỉ sau khi TV1 bàn giao phiên bản **đã qua quality gate**.
   Đây là thí nghiệm khác dữ liệu train, không quy toàn bộ cải thiện cho kiến trúc.
5. Test cũ đã được phân tích ở tuần 4: không dùng để chọn augmentation,
   checkpoint hoặc ngưỡng. Giữ kết quả B2 cũ như mốc lịch sử. Không chạy các
   lệnh `evaluate_w4_test.py` để sàng lọc ứng viên mới.
6. Nếu sau này TV1 có test mới đạt điều kiện, khóa danh sách và protocol trước
   lựa chọn ứng viên; khóa model bằng validation rồi mới mở. B2 và ứng viên
   phải cùng tập mới, cùng metric. Hiện **chưa có bản test mới đủ điều kiện**.

**Mục tiêu 88%** là accuracy top-1 cấp ảnh trên đủ các ảnh trong manifest,
không chỉ tính ảnh điểm cao. Báo cùng macro-F1 để không che khuất lớp khó.
Một lượt chạy tốt hơn chưa đủ chứng minh ưu thế ổn định hoặc đạt SOTA.

### Checklist kiểm tra TV4

- [ ] Nạp ảnh, nhiều box, chọn box/hàng kết quả đúng `detection_id` sau khi đổi bố cục.
- [ ] Cỡ màn hình 1440, 390 và 320 px; box bám đúng ảnh, không tràn ngang.
- [ ] `needs_review`, `no_detection`, ảnh lỗi và detector bỏ sót hiển thị đúng.
- [ ] Nhãn sửa không ghi đè dự đoán gốc; lưu/reload revision và JSON đúng bản đã lưu.
- [ ] Điểm dự đoán không được gọi là xác suất đã hiệu chỉnh; tình huống giả lập có nhãn rõ.
- [ ] Log tốc độ ghi CPU/GPU, threads, batch ảnh/crop, số mẫu, cold/warm.
- [ ] Nếu có lô/CSV: một ảnh lỗi không làm mất ảnh khác; nhãn duyệt và ảnh không có box xuất đúng.

## 3. Tuần 6 — kiểm chứng và hoàn thành báo cáo

| Mốc | Công việc | Tiêu chí xong |
| --- | --- | --- |
| Ngày 1–2 | Đối chiếu kết quả cuối theo protocol; nếu chưa có test mới chỉ báo validation | `reports/tv2/TV2_W6.md` tách rõ validation, Test B2 lịch sử và demo |
| Ngày 3 | Thử cài sạch cùng TV4, nạp đúng model và kiểm tra bằng train/val/fixture | Log môi trường, SHA checkpoint, class map và smoke test |
| Ngày 4 | Tập bảo vệ lần 1; chuẩn bị Q&A về leakage, accuracy/macro-F1, SOTA | Các câu trả lời dựa trên kết quả thật |
| Ngày 5 | Rà lỗi, tập lần 2 và xác nhận video dự phòng | Bảng số liệu khớp báo cáo, slide, model card |
| Ngày 6–7 | Review gói nộp và ghi kết luận nghiệm thu phần đánh giá | Không thiếu dự đoán, config, log và giới hạn |

Không buộc dùng DINO nếu kiểm định chưa đạt. Nếu chỉ cải thiện trên validation,
ghi đúng mức bằng chứng; B2 vẫn là phương án demo dự phòng.

## 4. Đầu vào, lệnh kiểm tra và cách bàn giao

Đọc [bàn giao TV1 W5](../handoff_tv1_w5.md), [dữ liệu so sánh W3](../handoff_tv1_w3.md),
[kết quả Test B2](../../reports/tv2/TV2_W4_TEST_EVALUATION.md),
[bàn giao TV4](../handoff_tv4_return_ui.md).

```powershell
git fetch origin
git switch feat/baseline
git merge --ff-only origin/feat/baseline
git merge origin/main
.venv/Scripts/python.exe -X utf8 scripts/validate_comparison.py --metadata-only --report outputs/tv2_w5/comparison.json
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv1_w5.py --verify-only --report outputs/tv2_w5/candidates.json
```

Lệnh W5 cần nhận cả code/config/snapshot TV1 trước, không chỉ một manifest.
`--metadata-only` không kiểm tra ảnh local; preflight pixel/hash vẫn cần trước
huấn luyện hoặc đánh giá. Không dùng `reset --hard` nếu nhánh có commit riêng.

Trước bàn giao chạy `scripts/check_environment.py`, `scripts/validate_results.py`,
`python -m unittest discover -s tests -v` bằng `.venv`, và `git diff --check`.
Push nhánh TV2, tạo/cập nhật PR, đưa TV3 kiểm tra; giữ nhánh sau merge.

## 5. Tiếp tục khi bị ngắt

Tạo `docs/progress_tv2_w5_w6.md` ngay ngày 1. Mỗi lượt ghi commit, config/hash,
dataset version, experiment ID, bước đã xong, log và lệnh chạy tiếp. Lưu dự đoán
và bảng metric theo từng attempt; không ghi đè bằng chứng cũ. Hết quota hội
thoại không có nghĩa tiến trình đã dừng: kiểm tra tiến trình/log trước khi chạy lại.
Không bắt đầu lại official Test để khôi phục công việc.
