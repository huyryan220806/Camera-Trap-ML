# TV3 tuần 5 — DINO linear probe và đối chứng B2

Ngày 28/10/2026. **CODE PREPARED; DATA PREFLIGHT PASS; DINO RUN PENDING.**
Đây là báo cáo triển khai và kiểm tra đầu vào, chưa phải bàn giao mô hình DINO
đã huấn luyện. Chưa có điểm validation, checkpoint DINO hoặc kết luận đạt 88%.

Cập nhật mới nhất 30/10: đã có pretrained thật, smoke GPU ngày29 PASS và
xác nhận TV3 trên config chuẩn. Gói trả lời TV2 B1–B3 và bằng chứng hiện tại:
[w5_review_response_2026-10-30/README.md](w5_review_response_2026-10-30/README.md).
Protocol vẫn DRAFT chờ TV2 kiểm tra; nội dung ngày28/29 bên dưới là lịch sử.

Cập nhật 29/10: đồng bộ định dạng predictions, handoff, reload và protocol
với nhánh TV2 `3f76643`; thêm kiểm định bằng mã TV2 nguyên bản, không merge
nhánh. Chi tiết và kiểm thử mới: [W5_TV2_COMPATIBILITY.md](W5_TV2_COMPATIBILITY.md).
Các kiểm tra ngày 28/10 bên dưới là evidence lịch sử, không thay kết quả mới.

## Phạm vi và nguồn

- Kế hoạch người dùng: `TV3_W5_W6.md`, cùng hướng với
  [plan TV3 của TV1](https://github.com/huyryan220806/Camera-Trap-ML/blob/9abc9c5/docs/plans/TV3_W5_W6.md).
- Đã đọc [handoff TV1 W5](https://github.com/huyryan220806/Camera-Trap-ML/blob/9abc9c5/docs/handoff_tv1_w5.md)
  và [plan TV2](https://github.com/huyryan220806/Camera-Trap-ML/blob/9abc9c5/docs/plans/TV2_W5_W6.md).
- Cập nhật nhánh TV3 bằng fast-forward tới main tích hợp `60516f5`; chưa commit
  hoặc push phần W5. Không thay notebook/ảnh/báo cáo EDA đã đổi từ trước.
- TV1 W5 hoàn tất kiểm kê/ứng viên; chưa có train release mở rộng hoặc test mới
  đủ điều kiện. Lượt đầu giữ comparison_v1, không dùng 1.665 ứng viên metadata.

## Phần đã triển khai

| Thành phần | Tệp / hành vi |
|---|---|
| Hai cấu hình riêng | `configs/dinov3_lp_w5.json`, `configs/dinov2_lp_w5.json` |
| CLI | `scripts/dino_w5.py`: pin, preflight, cache, train/resume, reload |
| Core | `src/training/dino_probe.py`: data gate, model loader, features, loss, metric, resume |
| Adapter TV4 | `load_package` kiểm SHA; `predict_crops` trả N×8 logits riêng từng box |
| Kiểm thử W5 | `tests/test_dino_w5.py`, dữ liệu tổng hợp/metadata; không tải DINO |
| Hướng dẫn | `docs/handoff_tv3_w5.md`, đủ lệnh nhận weights, pin, chạy, resume và push |
| Đồng thuận | `W5_PROTOCOL_PROPOSAL.md`, trạng thái PROPOSED, chưa thay TV2 xác nhận |
| Tiếp tục | `docs/progress_tv3_w5_w6.md` |

Backbone eval/frozen, CLS 384 chiều → Linear 8 lớp. Transform tách riêng cho
DINOv3/v2 theo nguồn chính thức; cache một view xác định/crop, không augmentation
ngẫu nhiên. Cache identity gồm weights/source commit, release/manifest hashes,
preprocessing, code hash, runtime và batch/shard. Shard có SHA và crop IDs;
cache đổi khi đầu vào đổi, cache hỏng thì dừng. Cắt trực tiếp từ ảnh RGB theo
bbox đã khóa, padding0, không round lại/EXIF transpose/nén JPEG bổ sung.

Mỗi batch chọn 32 ảnh nguồn, giữ đủ crop của ảnh, mean CE trong ảnh rồi mean
giữa ảnh. Validation mean vector softmax theo image_id rồi argmax, đủ 8 lớp,
zero_division=0. Chọn best theo macro-F1; hòa giữ epoch sớm hơn. JSON giữ
logits, probabilities, metric và per-class support trước làm tròn.

Checkpoint cuối chứa weights backbone + head, config, class map hai chiều,
source hashes, protocol, runtime và validation reference. Last checkpoint giữ
optimizer/scheduler/RNG/best head và log như một giao dịch epoch. Resume từ
epoch hoàn tất; đổi binding thì từ chối. Pipeline tự gọi tiến trình mới trích
lại 680 crop để kiểm tra đầy đủ prediction/reference, lưu mọi attempt và sai
khác. Không nới tolerance để ép PASS.

## Kiểm tra thực hiện trên máy này

Data preflight đã giải mã và đối chiếu byte SHA, RGB SHA, kích thước của đủ
**3.400 ảnh nguồn train/val**, kiểm hash manifest/class map/provenance và cùng
parent IDs với B1. Counts: **2.800 train / 3.125 crop; 600 val / 680 crop**.
Không đọc manifest/ảnh Test trong preflight W5. Chứng cứ:
[`w5_evidence/preflight.json`](w5_evidence/preflight.json).

Provenance: `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`.
B2 weights trên máy: 89.548.866 byte, SHA đúng
`8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`.
Đây là kiểm hash checkpoint B2, không chạy lại B2 validation ở lượt này.

Môi trường thực: Python3.12.10, torch2.6.0+cu124, torchvision0.21.0+cu124,
CUDA12.4, cuDNN90100, RTX4060 Laptop, VRAM8.585.216.000 bytes,
Pillow12.2.0, NumPy2.5.3, sklearn1.9.0. Nhận GPU chưa chứng minh backbone DINO
thật đã tương thích; `preflight --with-model` còn cần chạy sau nhận weights.

- Toàn bộ suite tại thời điểm kiểm tra: **386/386 PASS**, 73,173 giây.
- Môi trường CPU chung: PASS; 6 JSON result contracts: PASS.
- Kiểm thử W5 cuối **10/10 PASS**, 7,823 giây, gồm xuất gói và từ chối ghi đè.
  Kiểm thử W5 ban đầu 9/9 PASS sau chạy ngoài sandbox. Lượt sandbox đầu lỗi
  quyền Temp ở 3 fixture, không coi là PASS. Log cuối ở
  `w5_evidence/tests_w5_final.txt`; full suite 386 chạy trước bổ sung test xuất gói.
- Không có real feature extraction, head training, reload hoặc benchmark
  DINO GPU trong lượt triển khai này. Fixture backbone chỉ dùng kiểm tra logic.

## Bảng đối chứng hiện tại

| Mô hình | Validation accuracy | Macro-F1 | Dữ liệu / trạng thái |
|---|---:|---:|---|
| B2 b2_run01 | 0.7466666666666667 | 0.7454765175212033 | Kết quả lịch sử, 600 ảnh / 680 crop |
| DINOv3_LP_run01 | Chưa chạy | Chưa chạy | Config đề xuất, chưa weights/protocol |
| DINOv2_LP_run01 | Chưa chạy | Chưa chạy | Phương án dự phòng, không tự chạy thêm |

Các số B2 tính lại từ confusion matrix trong báo cáo đã khóa SHA
`51becb94cc4837657fade7e341dd9f874079136bbc763ad4e7266d40c24c3806`.
Lượt DINO thật sẽ sinh bảng JSON/Markdown với số chưa làm tròn, nguồn weights,
seed, counts, thời gian và môi trường. Không gọi so sánh này cùng ngân sách
compute B2: backbone, pretrained, transform và cách học khác nhau.

## Còn lại trước bàn giao mô hình

1. Nhận DINOv3 weights hợp lệ (hoặc chọn DINOv2 theo plan), pin SHA và commit;
   chạy preflight backbone thật.
2. TV2/TV3 chốt cấu hình và ngân sách một lượt, ghi evidence thật trong protocol.
3. Người dùng chạy cache/train theo hướng dẫn; kiểm đầy đủ reload. Nếu lệch,
   giữ evidence và điều tra trước khi gọi gói tái lập thành công.
4. Điền bảng kết quả thật, cấp link weights ngoài Git + SHA/size, gửi TV4 adapter,
   TV2 đối chiếu metrics và TV1 review. Những việc này chưa được thực hiện.

GT boxes khác detector boxes; 8 lớp và địa điểm pilot không đại diện toàn SWG;
chưa calibration và chưa independent test cho DINO. Một seed chưa chứng minh
độ ổn định. B3 tiếp tục UNRESOLVED/exploratory; giữ nguyên B2 lịch sử.
