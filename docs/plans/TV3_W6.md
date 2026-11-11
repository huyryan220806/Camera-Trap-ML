# TV3 — Tuần 6: cải thiện DINOv3 bằng pooling, fine-tune và dữ liệu mới

**Cập nhật:** 03/11/2026. **Nhánh:** `feat/crop-classifier`.
**Người kiểm tra:** TV2 về metric/tái lập, TV1 về dữ liệu, TV4 về adapter.
Lịch đề xuất **04–10/11/2026**, không phải hạn nộp mới của giảng viên.
Plan này thay phần W6 đóng gói trong plan W5–W6, giữ nguyên hồ sơ W5.

## Đích so sánh

Vượt `DINOv3_LP_run01` trên cùng val: **accuracy 84,50%, macro-F1 84,4400828%**;
phấn đấu accuracy ≥88% và tăng macro-F1. Không hứa trước mức cải thiện.
W5 dùng DINOv3 ViT-S/16 frozen, CLS 384D + Linear 8 lớp, seed 42, square 256,
train 2.800 ảnh / 3.125 crop, val 600 / 680. Dùng GT box; không trộn hiệu quả
detector vào bảng đối chứng phân loại. Áp dụng backbone hiện đại không tự
chứng minh đồ án đạt SOTA trên SWG.

Nhận đúng gói đã kiểm định theo [bàn giao TV3 W5](../handoff_tv3_w5.md).
Trên máy TV1, gói nằm ở `outputs/tv4/w5/intake_20261102/DINOv3_LP_run01`;
máy khác cần nhận bundle ngoài Git và đối chiếu SHA, không chỉ chép notebook.

## Sáu lượt tối đa, không tìm kiếm không giới hạn

| Lượt | Recipe | Dữ liệu | Seed |
| --- | --- | --- | --- |
| R1 | `DINOv3_CLS_PATCH_W6`: CLS + mean patch, frozen | Cũ | 42 |
| R2 | `DINOv3_FT2_W6`: mở 2 block cuối + norm + head, CLS | Cũ | 42 |
| R3, R4 | Recipe R1/R2 thắng R0 theo TV2 | Cũ | 43, 44 |
| R5, R6 | Recipe đã chọn, chỉ thay train bằng release TV1 | Mở rộng | 42, 43 |

R0 là W5 sẵn có. R3/R4 chỉ chạy khi có cải thiện; R5/R6 có điều kiện dữ liệu
được TV2 duyệt và còn ngân sách. Nếu R1/R2 không thắng, có thể dùng recipe R0
cho R5/R6 theo nhánh đã đăng ký. Đặt run ID riêng, không ghi đè `DINOv3_LP_run01`.
Tối đa **12 GPU-giờ gồm trích xuất, ≤2 giờ/lượt**, tối đa sáu lượt mới gồm cả
lượt lỗi/dừng. Đây là trần kế hoạch, chưa phải dự báo thời gian hay đặt chỗ.
Thiếu ngân sách: R1/R2 → kiểm tra seed → hoãn mở rộng; không bỏ kiểm định.

### R1 — frozen CLS + mean patch

Concat `x_norm_clstoken` 384D với trung bình `x_norm_patchtokens` 384D →
Linear 768→8. Không lấy storage/register token vào trung bình. Giữ preprocessing
và SGD recipe W5: lr .01, momentum .9, weight decay .0001, cosine tối đa
50 epoch, patience 7, batch 32 ảnh, seed 42. Cache mới phải ghi pooling/feature
dimension/ảnh/crop/pretrained/source/preprocess/runtime SHA, không dùng cache 384D.

### R2 — fine-tune nhẹ, recipe đề xuất để khóa trước chạy

- Khởi tạo backbone và head từ checkpoint W5. Train đúng hai transformer block
  cuối, final norm và head; các tầng trước giữ nguyên. CLS 384D.
- AdamW: backbone lr `1e-5`, head `1e-4`, decay `.01`, không decay bias/norm;
  max 20 epoch, patience 5, warmup 2 epoch rồi cosine. Đây là giả thuyết của
  nhóm, không phải recipe đã được chứng minh tối ưu cho SWG.
- Train horizontal flip p=.5; không vertical flip hoặc random crop làm mất
  con vật nhỏ. Val giữ resize square 256, tensor uint8 bilinear antialias,
  RGB/ImageNet normalization, padding 0 như W5.
- Effective batch 16 **ảnh**, microbatch tối đa 8 **crop**; mean loss trong
  từng ảnh rồi mean theo ảnh. Accumulation phải tính đúng mẫu batch cuối,
  kể cả ảnh có nhiều box. FP32 mặc định; smoke bộ nhớ chỉ trên train trước
  khóa config. Nếu OOM, giảm microbatch và giữ effective batch trước lượt
  chính thức; không âm thầm đổi AMP/device/recipe giữa lượt.
- Không dùng frozen-feature cache cho backbone đang học. Check gradient và
  `train/eval` mode; lưu full backbone + head, không chỉ head W5.

R1/R2 so sánh hai recipe; không khẳng định R2 tốt lên chỉ vì hai block nếu
optimizer/augmentation cũng khác. Không thêm ensemble/TTA/model lớn trong
ngân sách này; ghi đề xuất tuần tiếp theo nếu bằng chứng cho thấy cần.

## Triển khai và kiểm thử cần thiết

1. Tạo module/CLI/config **W6 riêng**. Không sửa `src/training/dino_probe.py`
   đã được adapter W5 khóa source SHA. Loader W5 hiện chỉ nhận snapshot,
   feature và seed đã khóa; không giả định hỗ trợ mở rộng/fine-tune sẵn.
2. Cùng TV2 chốt protocol, seed và dataset hashes trước chạy. Giữ val 600 ảnh
   và class map. Loss theo ảnh một lần; val mean softmax vector tất cả crop.
3. Test gradient của tầng frozen/trainable, head 768/384, cache invalidation,
   crop grouping/batch cuối, save/reload, dataset SHA sai và resume.
4. Resume checkpoint `last` gồm optimizer, scheduler, epoch/best, RNG Python/
   NumPy/Torch/CUDA, sampler và AMP state nếu dùng; không reset early stopping.
   Ghi run lỗi/OOM/mất Colab, không khởi động lượt tìm kiếm mới để che lỗi.
5. Lưu cả best/last, log metric chưa làm tròn, vector val đầy đủ, thời gian,
   GPU/VRAM/batch/precision, source commit, init SHA, manifest/preprocess hashes.
6. Seed 42 là lượt chính; 43/44 đo dao động, không lấy seed cao nhất thay
   headline. Mở rộng dữ liệu dùng cùng recipe/seed để tách hiệu ứng dữ liệu;
   không đồng thời thêm class weights hoặc sampler mới chưa đăng ký.

## Lịch và bàn giao

| Ngày | Công việc | Đầu ra |
| --- | --- | --- |
| D1 — 04/11 | Module W6, config, train-only memory smoke, chốt protocol TV2 | Contract checkpoint và run registry |
| D2 — 05/11 | R1 + kiểm định vector | Log/cache/checkpoint R1 |
| D3 — 06/11 | R2 + kiểm tra frozen/gradient/reload | Log/checkpoint R2 |
| D4 — 07/11 | Cùng TV2 chọn recipe; R3 nếu đủ điều kiện | Quyết định và seed 43 |
| D5 — 08/11 | R4; R5/R6 nếu còn ngân sách và TV1 đã được review | Từng seed, tách dữ liệu mới |
| D6 — 09/11 | Gửi gói cho TV2 replay và TV4 adapter | Gói checkpoint có SHA, mã nạp mẫu |
| D7 — 10/11 | Sửa lỗi tích hợp, báo cáo cả thử nghiệm không thắng | `reports/tv3/w6/REPORT.md` |

Gói ngoài Git: weights thật + config/model card + class map + nguồn/vendor
commit + hashes + script nạp độc lập + dự đoán val và metrics + môi trường.
`best_model.pt` không được là link rỗng hoặc chỉ ghi SHA. Bundle mới khai báo
format/version, pooling, tầng trainable; không giả danh checkpoint W5.
TV2 xác minh, TV4 đối chiếu score native trước cân nhắc đổi model mặc định.

Hoàn thành khi có thí nghiệm theo ngân sách, bằng chứng replay và kết luận
trung thực; không cần ép 88% bằng lọc ảnh hay mở Test. Commit trên nhánh cố
định, lưu `docs/progress_tv3_w6.md` với run/epoch/path/command và việc còn lại.

Nguồn phương pháp: [DINOv3 chính thức](https://github.com/facebookresearch/dinov3),
[feature API tại vendor commit đã khóa](https://github.com/facebookresearch/dinov3/blob/6876159a11b4df116f30f667f8c9888617df0751/dinov3/models/vision_transformer.py),
[PyTorch: transfer learning](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html).
Các nguồn hỗ trợ cách lấy đặc trưng/fine-tune; hyperparameter W6 ở trên là
đề xuất của nhóm phải kiểm chứng, không phải kết quả công bố cho dataset này.

Kế hoạch liên quan: [TV1](TV1_W6.md), [TV2](TV2_W6.md), [TV4](TV4_W6.md).
