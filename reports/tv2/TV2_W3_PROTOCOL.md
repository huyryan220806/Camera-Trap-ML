# TV2 W3 B1/B2 protocol — AGREED BY USER FOR TEAM

## Quyết định hiện tại – 18/10/2026

Người dùng dẫn chiếu `origin/main:docs/experiment_protocol.md` tại 468d81f,
sau đó xác nhận lựa chọn cụ thể: **“Xác nhận cấu hình trên cho nhóm”**.
Evidence machine-readable: [W3_PROTOCOL_AGREEMENT_2026-10-18.json](W3_PROTOCOL_AGREEMENT_2026-10-18.json).
Đây là xác nhận của người dùng cho nhóm, không phải chữ ký/review độc lập TV3.

| Thuộc tính | Quyết định đã xác nhận | B2 hiện tại | Việc cần làm |
|---|---|---|---|
| Model | ResNet18 IMAGENET1K_V1, full fine-tune, no dropout | dropout0.2 | TV3 đồng bộ |
| Seed / precision | 42 / FP32 | 42 / AMP | TV3 đồng bộ |
| Optimizer | SGD lr0.001, momentum0.9, WD0.0001 | AdamW0.0001 | TV3 đồng bộ |
| Scheduler | StepLR step10 gamma0.1 | Cosine | TV3 đồng bộ |
| Epoch / stopping | max50 / patience7 theo val macro-F1, tie giữ sớm | 15 / config5 chưa thực thi | TV3 sửa |
| Batch / preprocessing | 32; transforms mục6 đề cương, Resize256/Crop224 | crop batches/drop_last/Resize224 | TV3 đồng bộ và chứng minh sampling/compute |
| Geometry B2 | TV1 bbox_xyxy, padding0, Python round/clip/min8 | bbox crop reader đã có | Không dùng padding10–15% từ đề cương W1 |
| Loss B2 | Mean CE các crop trong từng ảnh rồi mean theo ảnh | Weighted crop batch normalization | TV3 sửa; không nhân thêm 1/N sau mean |
| Evaluation | Một dự đoán/ảnh; B2 mean probability tất cả crop | Mean probability đã có | Kiểm label/parent completeness và fresh reload |
| Budget | Chưa được xác nhận thời lượng/khung giờ | Chưa booking | Chủ GPU trả lời; không tự tạo approval |

Config `b1_comparison_v1.pending.yaml` gắn dữ liệu/protocol; còn chờ budget/environment
freeze. B1/B2 dùng cùng parent IDs đã xác minh. Code B2 chưa khớp agreement nên chưa
đủ điều kiện công bố comparison. Native provenance TV1 không có status=FROZEN/owner/task:
adapter xác thực Git hash, config, sources, views, audit, verification; không thêm chữ ký giả.

Các bảng PROPOSED bên dưới là lịch sử trước xác nhận; không phải lựa chọn còn mở hiện tại.

## Current B1 / B2 — continuation 01 (16/10/2026)

Đã fetch lại: B1 tại `881d143510d23e3862e3748ed2b7cb707aab7dc5` (P1 tại
`bf9aae4`); B2 vẫn tại `d08eba7fffbfb6ecc813de8522fb4d58cd8ed904`.
Không tìm thấy bằng chứng approval TV3. Mọi hàng đề xuất dưới đây có trạng thái
**PROPOSED – AWAITING TV3 APPROVAL**, kể cả khi giá trị hiện tại trùng nhau.
Không sửa config hoặc tự tạo receipt AGREED trong lượt này.

| Thuộc tính | Current B1 | Current B2 | Proposed Agreement | Evidence | Status |
|---|---|---|---|---|---|
| Architecture | ResNet18, FC 8 lớp, không dropout | ResNet18, dropout 0.2 + FC 8 lớp | ResNet18, cùng head không dropout để cô lập ảnh/crop | src/models/b1.py; TV3 src/models/b2_classifier.py | PROPOSED – AWAITING TV3 APPROVAL |
| Pretrained | IMAGENET1K_V1, trực tiếp ImageNet | ResNet18_Weights.DEFAULT | Ghim IMAGENET1K_V1, URL/hash weights; không tiếp tục B0 | Hai module model | PROPOSED – AWAITING TV3 APPROVAL |
| Fine-tune / BN | Toàn bộ layer, BN train/eval | Toàn bộ layer, model.train()/eval() | Giữ cùng chiến lược | src/training/b1.py; TV3 scripts/train_b2.py | PROPOSED – AWAITING TV3 APPROVAL |
| Resolution | Resize cạnh ngắn 256, crop 224 | Resize vuông 224 | Cùng Resize256/crop224; kiểm ảnh hưởng lên crop trước khi chốt | src/data/b0_dataset.py; TV3 src/data/b2_dataset.py | PROPOSED – AWAITING TV3 APPROVAL |
| Train augmentation | RandomCrop, flip .5, jitter (.2,.2,.1,.05) | Resize, flip .5, jitter (.2,.2,.2,.05) | Cùng augmentation B1 hiện tại | Hai module dataset | PROPOSED – AWAITING TV3 APPROVAL |
| Validation preprocessing | Resize256 + CenterCrop224 | Resize(224,224) | Cùng phép biến đổi xác định; normalize ImageNet | Hai module dataset | PROPOSED – AWAITING TV3 APPROVAL |
| Seed | 42, worker/generator, deterministic cuDNN | 42; generator, chưa deterministic cuDNN/worker đầy đủ | 42 và cùng chính sách seed | B1 set_seed/make_loaders; TV3 set_seed/make_b2_loaders | PROPOSED – AWAITING TV3 APPROVAL |
| Optimizer / LR | SGD .001, momentum .9 | AdamW .0001 | SGD .001/.9 là đề xuất, cần TV3 đánh giá trước chạy | configs/b1.yaml; TV3 configs/b2_crop_classifier.json | PROPOSED – AWAITING TV3 APPROVAL |
| Weight decay | .0001 | .0001 | .0001 | Hai config | PROPOSED – AWAITING TV3 APPROVAL |
| Scheduler | StepLR10, gamma .1, sau validation | Cosine T_max=epochs, trước validation | StepLR10/.1, cùng thời điểm step | Hai training loop | PROPOSED – AWAITING TV3 APPROVAL |
| Batch / drop_last | 32 ảnh, False | 32 crop, True | 32 ảnh nguồn/update hoặc thiết kế tương đương cần TV3 triển khai; giữ batch cuối | Hai loader | PROPOSED – AWAITING TV3 APPROVAL |
| Epoch / compute budget | Tối đa 50 epoch | 15 epoch | Chốt đồng thời epoch, số update, ảnh/crop processed và giới hạn giờ; 50 chỉ là đề xuất | Hai config; chưa có budget reference | PROPOSED – AWAITING TV3 APPROVAL |
| Early stopping | Patience7 đã thực thi | Config5, loop chưa thực thi | Patience7, cùng metric và tie rule | Hai training loop | PROPOSED – AWAITING TV3 APPROVAL |
| Loss B1 | Mean CE, mỗi ảnh trọng số1 | Không áp dụng | Mean CE cấp ảnh | src/training/b1.py | PROPOSED – AWAITING TV3 APPROVAL |
| Loss B2 | Gate kiểm trọng số1/N | Sum(CE/N)/sum(1/N) từng batch crop | Mean theo ảnh của mean CE các crop; cần group ảnh hoặc estimator đã thống nhất | TV3 train_one_epoch; B1 verify_data | PROPOSED – AWAITING TV3 APPROVAL |
| Loss logging | Sum loss ảnh / số ảnh | Mean batch weighted loss rồi nhân số crop | Ghi sum(weight*CE)/sum(weight) toàn epoch; phân biệt với loss trên xác suất tổng hợp | TV3 train_one_epoch/evaluate_b2_model | PROPOSED – AWAITING TV3 APPROVAL |
| Aggregation | Một dự đoán/ảnh | Mean softmax crop, argmax cấp ảnh | Mean probability; nhãn crop cùng ảnh phải nhất quán | TV3 src/evaluation/b2_evaluator.py | PROPOSED – AWAITING TV3 APPROVAL |
| Metrics | Macro đủ 8 lớp, zero_division=0 | Macro theo toàn bộ num_classes | So ở cấp ảnh, đủ lớp/support, tính lại từ predictions | src/evaluation/metrics.py; TV3 evaluator | PROPOSED – AWAITING TV3 APPROVAL |
| Best checkpoint | Max val macro-F1; tie giữ sớm | Max image macro-F1; best_epoch report sai | Cùng rule; reload best artifact thật | Hai training loop | PROPOSED – AWAITING TV3 APPROVAL |
| Precision | FP32 | AMP khi CUDA | Cùng precision hoặc ghi rõ khác biệt được duyệt | Hai training loop | PROPOSED – AWAITING TV3 APPROVAL |
| Workers | 0 | 4 trong config | Ghim và ghi runtime thực tế; ưu tiên0 cho tái lập ban đầu | Hai config | PROPOSED – AWAITING TV3 APPROVAL |
| GPU budget | null; runtime CPU-only hiện tại | Chưa có booking được duyệt | Chủ GPU xác nhận thiết bị/khung giờ, ghi budget reference trước chạy | coordination/gpu_bookings.json; continuation_01/environment.txt | PROPOSED – AWAITING TV3 APPROVAL |

Trọng số `1/N` ở từng crop là cần thiết nhưng chưa đủ để bảo đảm mỗi ảnh có
cùng ảnh hưởng trong SGD: batch crop ngẫu nhiên có mẫu số trọng số thay đổi,
ảnh nhiều crop có thể trải qua nhiều update, và `drop_last=True` có thể bỏ crop.
TV2/TV3 phải chốt sampling/normalization/compute cùng nhau. TV2 không đổi riêng
thuật toán hoặc gọi hai run là tương đương chỉ vì cùng số epoch.

Giao diện receipt và literal `input_type=bbox_crop` bên dưới vẫn là adapter theo
fixture/review, chưa được xác minh với bundle TV1 đã phát hành. Sau khi có bundle
thật, điều chỉnh adapter theo schema có bằng chứng, giữ nguyên byte dữ liệu TV1.
`P1 CODE FIX VERIFIED LOCALLY`; `REAL COMPARISON_V1 VERIFICATION PENDING`.

Ngày 15/10/2026. Đây là đề xuất của TV2, **chưa được TV3 đồng thuận**.
Không dùng việc config tồn tại làm bằng chứng cho phép train.

| Thuộc tính | Đề xuất cần TV2/TV3 chốt |
|---|---|
| Dữ liệu | W3-01 do TV1 khóa; cùng ảnh gốc, nhãn, split và danh sách loại |
| Đơn vị so sánh | Một ảnh nguồn; B2 trung bình xác suất của mọi box hợp lệ cùng loài để tạo một dự đoán/ảnh |
| Chọn box | Không tự chọn một box; dùng đủ annotation hợp lệ TV1 đã khóa, `sample_weight=1/N` với N crop của ảnh |
| Khởi tạo | ResNet18, ImageNet-1K `IMAGENET1K_V1` trực tiếp; không tiếp tục B0 |
| Nguồn weights | `https://download.pytorch.org/models/resnet18-f37072fd.pth`; torchvision enum cụ thể, không DEFAULT |
| Fine-tune | Mở tất cả layer; BatchNorm cập nhật affine/running statistics khi train, eval khi validation |
| Seed | 42; Python, NumPy, torch, CUDA, DataLoader generator và worker seeds |
| Budget | Tối đa 50 epoch, patience 7 theo macro-F1; cùng quy tắc cho B2 |
| Batch | 32, giữ batch cuối (`drop_last=False`), workers 0; không tự giảm khi OOM |
| Input | B1 ảnh gốc; B2 crop on-the-fly từ `bbox_xyxy` đã khóa, tuyệt đối không detector crop trong phép so sánh |
| Resolution | Resize cạnh ngắn 256, crop 224; normalize ImageNet |
| Train augmentation | RandomCrop224, horizontal flip 0.5, ColorJitter(0.2,0.2,0.1,0.05) |
| Validation | Resize256, CenterCrop224, không ngẫu nhiên |
| Optimizer | SGD, lr 0.001, momentum 0.9, weight decay 0.0001 |
| Scheduler | StepLR, step 10 epoch, gamma 0.1, step sau validation mỗi epoch |
| Loss | CrossEntropyLoss không class weights |
| Checkpoint | Validation macro-F1 cao nhất; hòa điểm giữ epoch sớm hơn |
| Metrics | `src/evaluation/metrics.py`; toàn bộ lớp, zero_division=0, đơn vị ảnh nguồn |
| Runtime | CUDA được xác nhận và có budget reference; log GPU, version, thời gian, peak allocated VRAM |

Phần hợp đồng dữ liệu đã được adapter hóa theo bàn giao review: B1 một dòng/ảnh;
B2 mọi box hợp lệ cùng loài, loss cân bằng cấp ảnh bằng `1/N`, validation dùng
mean-probability aggregation cấp ảnh. Gate và fixture tests đã được cập nhật.
Các hyperparameter/budget vẫn chưa được TV2/TV3 thống nhất; không bật train bằng
cách chỉ sửa chữ PROPOSED thành AGREED.

Khác biệt tìm thấy trên TV3 `2c3c992`: `src/data/crop_dataset.py` dùng
Resize(224,224), jitter 0.3, RandomGrayscale(0.05), drop_last train=True;
`scripts/crop_dataset.py` xuất nhiều crop/ảnh với box clamp, chưa thể hiện padding
10–15% như đề cương. Đây là code W2, không phải B2 đã chốt. Chưa có optimizer,
seed/budget/model B2 W3 để nghiệm thu. Cần thống nhất cả số bước cập nhật và đơn vị
tính metric, tránh ảnh nhiều box có trọng số lớn hơn một cách ngầm định.

## Đối chiếu handoff TV3 ngày 16/10/2026

TV3 đã push code B2 tại commit
`d08eba7fffbfb6ecc813de8522fb4d58cd8ed904`. Snapshot tests PASS 9/9, nhưng
không có official artifacts và code review chưa đạt. Config quan sát được dùng
ResNet18 pretrained, dropout 0.2, AdamW lr `1e-4`, cosine scheduler, 15 epoch,
patience 5, Resize vuông 224, color jitter saturation 0.2, `drop_last=true` và
mean-probability aggregation cho nhiều crop. Early stopping chưa được triển khai.

Những giá trị này khác đề xuất B1 ở optimizer/scheduler, budget, dropout,
preprocessing, batch cuối và đơn vị sampling. Đường dẫn B2 giữa preflight và
DataLoader cũng không nhất quán; preflight chưa xác minh hash/freeze/membership.
Do đó protocol vẫn là **PROPOSED**, chưa thể coi là AGREED. TV2 và TV3 cần chốt
một cấu hình chung, hoặc ghi trước từng khác biệt có chủ đích và cách kiểm soát
compute/số bước, trước khi một bên chạy official training. Chi tiết lỗi ở
[review TV3](TV2_REVIEW_TV3_W3.md).

## Giao diện bằng chứng đề xuất cho gate

Đây là **giao diện TV2 đề xuất**, không phải file TV1 đã bàn giao. Không tạo
receipt giả trong `data/processed/`. Có thể điều chỉnh adapter khi nhận schema
thật của TV1 mà vẫn giữ toàn bộ kiểm tra khoa học.

`configs/b1.yaml` dùng JSON, tập con hợp lệ của YAML 1.2 giống B0; parser chỉ đọc
cú pháp JSON này, không nhận YAML dạng tự do. Đường dẫn tính từ repository root.

TV1 cung cấp freeze receipt JSON với:

```json
{
  "task": "W3-01",
  "owner": "TV1",
  "status": "FROZEN",
  "dataset_version": "<version do TV1 chot>",
  "files": {
    "train": {"path": "<train-only JSONL>", "sha256": "<64 hex>"},
    "val": {"path": "<val-only JSONL>", "sha256": "<64 hex>"},
    "source_train": {"path": "<source train-only JSONL>", "sha256": "<64 hex>"},
    "source_val": {"path": "<source val-only JSONL>", "sha256": "<64 hex>"},
    "crop_train": {"path": "<selected crop train JSONL>", "sha256": "<64 hex>"},
    "crop_val": {"path": "<selected crop val JSONL>", "sha256": "<64 hex>"},
    "class_map": {"path": "<class map JSON>", "sha256": "<64 hex>"},
    "excluded": {"path": "<train/val exclusion ledger JSONL>", "sha256": "<64 hex>"},
    "quality_audit": {"path": "<quality attestation JSON>", "sha256": "<64 hex>"}
  }
}
```

Manifest giữ nguyên field và quality của nguồn TV1. `quality.local_path` nằm
trong `data.image_root`; bắt buộc byte SHA-256 và pixel SHA-256. Pixel hash theo
TV1 W2: SHA256(`RGB:{width}:{height}:` + RGB bytes). Kiểm tra tất cả ảnh
train/val: decode, kích thước, hash, nhãn, box, ID/path duplicate, location,
sequence, content leakage. Không tự loại ảnh lỗi hay đổi split. Lỗi chỉ rõ ID;
run lỗi giữ status/exception, không resume hoặc ghi đè run cũ.

B1 view dùng `sample_id`, `image_id`, `input_type=full_image`, `sample_weight=1`
và không cần lặp lại `boxes`; gate đối chiếu các trường provenance có ý nghĩa
với manifest ảnh nguồn thay vì so nguyên dict. B2 manifest dùng `crop_id`,
`image_id`, `annotation_id`, split/label/class, `input_type=bbox_crop`,
`sample_weight`, `bbox_xyxy`, `url` và `quality.{local_path,sha256}`. Gate chấp
nhận nhiều crop/ảnh, bắt buộc crop/annotation ID duy nhất, đủ đúng tập box hợp
lệ, cùng parent IDs với B1, cùng nhãn/split/nguồn và trọng số `1/N`. Crop được
tạo on-the-fly nên không yêu cầu JPEG crop hay hash crop riêng; byte hash ảnh
nguồn vẫn được kiểm trước khi huấn luyện.

Excluded ledger có image_id, split, reason; chỉ train/val, không trùng accepted,
accepted ∪ excluded phải bằng source. Mọi lớp phải có mẫu train và val. Counts
ảnh/chuỗi từng lớp lưu ở data_gate.json. Đối với test, chỉ đọc attestation TV1;
TV2 không mở test manifest/ảnh. Quality JSON phải xác nhận true cho
`all_split_location_disjoint`, `all_split_sequence_disjoint`,
`all_split_content_disjoint`, `source_membership_verified`, `box_review_passed`.
Đây là chứng cứ cần reviewer kiểm tra, không thay thế kiểm định của TV1.

Điền `data.freeze_receipt`, `data.freeze_sha256`, `data.freeze_git_ref`.
Git ref là `<40-character commit SHA>:<receipt path>`; gate đối chiếu byte thật
trong commit với SHA-256 đã ghim và file local. TV2 không tự ghi nhận TV1 freeze.

Protocol receipt riêng phải có status AGREED, approved_by `["TV2","TV3"]`,
freeze_sha256 khớp receipt TV1, budget_reference đã xác nhận và `settings` đúng
giá trị trả về từ `src.training.b1_gate.protocol_settings(config)`. Lưu receipt
trong Git sau đồng thuận thực; điền `protocol.receipt`, `sha256`, `git_ref` và
`runtime.budget_reference`. Không coi metadata tự khai là đồng thuận của TV3.

## Chạy và bàn giao

```powershell
python -X utf8 scripts/train_b1.py --smoke
# Chỉ chạy sau khi đã có evidence thật, môi trường CUDA và budget được chốt:
python -X utf8 scripts/train_b1.py --config configs/b1.yaml
python -X utf8 scripts/validate_b1.py --checkpoint experiments/B1_run01/checkpoints/best_model.pth --sha256 <actual-checkpoint-sha256>
```

Config hiện tại chủ động dừng: `BLOCKED - W3-01 MANIFEST NOT FROZEN`. Không có
flag bypass/fallback CPU cho official training. Official yêu cầu code/config
đã commit, chạy lại synthetic preflight, rồi mới reserve run mới. GPU smoke với
ảnh thật vẫn cần reviewer xác minh trước lượt đầy đủ khi có handoff/tài nguyên.

Smoke dùng ResNet18 thật nhưng weights=None, 2 lớp giả, ảnh noise RGB tạm,
2 epoch CPU, input32. Checkpoint được reload/đối chiếu và xóa cùng thư mục tạm;
không được đưa số liệu đó vào bảng kết quả B1. Smoke không kiểm thử download
ImageNet hay CUDA. Test integration kiểm tra chính training loop và gate bằng
fixture; không chứng minh chất lượng dữ liệu hoặc tốc độ GPU thật.

Official artifacts: config.yaml, data_gate.json, status.json, logs/train_log.csv,
checkpoints/best_model.pth, results/val_metrics.json, per_class_metrics.csv,
confusion_matrix.png, learning_curves.png, reload_validation.json. Thời gian
train/validation đo với CUDA synchronize; peak GPU là max_memory_allocated,
không phải tổng VRAM của tiến trình. Exception giữ trạng thái FAILED/INTERRUPTED
và checkpoint tốt nhất đã công bố nguyên tử. Không hỗ trợ resume.

Checkpoint liên kết config, code commit, pretrained source, all-unfrozen/BN
strategy, class mapping hai chiều, receipt/hash/version, seed và preprocessing.
Reload kiểm hash trước torch.load(weights_only=True), kiểm provenance trước
inference; metric tolerance 1e-9, loss atol 1e-6, logits atol1e-6/rtol1e-5,
predictions phải trùng hoàn toàn. Validation không sửa run gốc.
