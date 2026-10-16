# TV2 W3 B1/B2 protocol — PROPOSED

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
