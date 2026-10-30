# Tiếp tục TV3 W5–W6

Ngày 28/10/2026, nhánh `feat/crop-classifier`. Đã fetch và fast-forward từ
`4b4a691` đến bản tích hợp `60516f5` (main và nhánh TV3 remote cùng commit).
Đã đọc TV1 W5 tại `origin/feat/metadata-split` commit `9abc9c5` và hai plan
TV2/TV3 trong nhánh đó. Chưa merge W5 của TV1; metadata ứng viên không phải
đầu vào của thí nghiệm này. Không thay các sửa đổi EDA/notebook có sẵn.

## Trạng thái

- Cập nhật 30/10: TV3 đã xác nhận config raw SHA e9303ba3… và cho phép
  commit/push gói B1–B3. Xem `reports/tv3/w5_review_response_2026-10-30/README.md`
  và `TV3_APPROVAL.json` trong đó. Config/pretrained/smoke giữ nguyên; TV2 đã
  đồng ý hyperparameter có điều kiện tại9f528d2. Protocol vẫn DRAFT, chưa train.
- Cập nhật sau khi nhận email weights 29/10: đã pin DINOv3 ViT-S/16 thật và
  smoke GPU 32 crop PASS. Xem `reports/tv3/W5_PRETRAINED_READY.md`. Thông tin
  "chưa tải pretrained" phía dưới thuộc trạng thái trước bước này. Chưa train;
  receipt vẫn DRAFT. Loader dùng factory backbone chính thức trực tiếp để
  không kéo phụ thuộc segmentation từ hubconf.
- Cập nhật 29/10: đã đồng bộ schema/protocol/export/reload với TV2 `3f76643`;
  thêm auditor snapshot nguyên bản TV2 và kiểm thử tương thích. Xem
  `reports/tv3/W5_TV2_COMPATIBILITY.md`. Người dùng đã nhắn TV2 nhưng chưa có
  phản hồi chốt; receipt vẫn DRAFT, không có approval hoặc run DINO thật.
- Phiên bản đồng bộ 29/10: full suite 393/393 PASS (gồm 16 test DINO/TV2),
  không SKIP; lần sandbox bị chặn localhost đã giữ log và chạy lại thành công.
- Đã triển khai pipeline linear probe DINOv3 và cấu hình DINOv2 dự phòng.
- Đối chứng B2 trên máy khớp SHA `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`.
- Ngày 28/10: data preflight đủ 3.400 ảnh train/val PASS; full suite 386/386
  PASS, kiểm thử W5 cuối 10/10 PASS. Evidence cũ giữ nguyên tại
  `reports/tv3/w5_evidence/`; kiểm tra phiên bản đồng bộ TV2 ngày 29/10 ở
  `reports/tv3/w5_evidence/compat_2026-10-29/`.
- Đã có pretrained và smoke thật (29/10); chưa cache đặc trưng chính thức,
  chưa có checkpoint/metric DINO và chưa có protocol APPROVED của TV2.
- Chỉ thực hiện data preflight và kiểm thử; không chạy Test để chọn mô hình.
- Báo cáo công việc: `reports/tv3/TV3_W5.md`; lệnh chạy: `docs/handoff_tv3_w5.md`.

## Khôi phục công việc

1. Đọc `reports/tv3/TV3_W5.md`, kiểm tra `git status`, và đọc log ở
   `outputs/tv3_w5/`. Những file này cho biết bước thật đã hoàn thành.
2. Kiểm tra tiến trình Python đang chạy trước khi khởi động lại:
   `Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Select-Object ProcessId,CommandLine`.
3. Feature cache: gọi lại lệnh `cache` hoặc `train --resume`. Shard đã được
   công bố trong index phải khớp SHA/crop IDs; shard lỗi làm dừng. Shard dang dở
   chưa có trong index sẽ được tính lại. Không xóa `writer.guard`.
4. Training: `last_model.pt` là giao dịch của epoch hoàn tất gần nhất, chứa
   head hiện tại, best head, optimizer, scheduler, RNG Python/NumPy/torch/CUDA,
   lịch sử epoch. `--resume` chạy lại toàn bộ epoch bị ngắt. Không hứa tiếp tục
   giữa minibatch. FP32, AMP/scaler không sử dụng. Best standalone được xuất
   khi kết thúc train; best head vẫn được giữ trong last checkpoint khi bị ngắt.
5. Config, code hash, Git commit, runtime, data hoặc protocol đổi thì resume
   bị từ chối. Khởi tạo experiment ID mới theo protocol mới. Run COMPLETE
   không được ghi đè. Nếu chỉ reload lỗi, dùng lệnh `reload` với tên report mới;
   giữ nguyên reference cũ để điều tra.
6. Sao lưu cả `runs/`, `features/`, pretrained weights và architecture checkout
   trên ổ bền vững; runtime Colab tạm không phải bản sao lưu. Không đưa weights,
   cache hoặc ảnh vào Git. Bản model gửi TV4 phải kèm SHA, code commit, repo
   backbone đúng commit, config và đầy đủ validation/reload.

## Các việc còn cần thực hiện sau khi chuẩn bị

- Gửi TV2 gói B1–B3 và commit SHA; chờ TV2 kiểm tra và khóa APPROVED.
- Không thay config hoặc chạy thêm smoke chỉ để bổ sung hồ sơ; weights,
  architecture và smoke ViT-S/16 đã có bằng chứng riêng.
- Chạy lượt seed 42, kiểm tra reload độc lập, gửi gói cho TV4/TV2.
- Bổ sung kết quả thật vào báo cáo W5. Không đánh dấu toàn bộ tuần 5 hoàn thành
  khi mới có code/kiểm thử. Week 6 là phạm vi tiếp theo.
