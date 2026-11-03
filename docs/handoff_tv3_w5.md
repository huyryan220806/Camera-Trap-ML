# TV3 W5 — hướng dẫn chạy và bàn giao DINO linear probe

Cập nhật 30/10: weights/checkout/config pin đã có, smoke32 crop ngày29 PASS.
Không chạy lại lệnh clone/pin với các đường dẫn đã tồn tại. TV3 đã xác nhận
config chuẩn; trước training cần TV2 kiểm gói
`reports/tv3/w5_review_response_2026-10-30/README.md` và khóa protocol APPROVED.
Các lệnh thiết lập bên dưới dành cho máy mới hoặc tham khảo tái lập.

Đầu vào công việc là `TV3_W5_W6.md` người dùng cung cấp, trùng hướng với plan
trên nhánh TV1 `9abc9c5`. Lượt đầu chỉ dùng `comparison_v1`: 2.800/600 ảnh
train/val, 3.125/680 GT crop. Các ứng viên W5 chưa được phát hành cho huấn luyện.

## Cấu hình đề xuất để TV2 rà soát

Đây là **PROPOSED**, không tự ghi nhận TV2 đã đồng ý. Chọn duy nhất một backbone
cho lượt đầu: DINOv3 ViT-S/16, hoặc DINOv2 ViT-S/14 nếu chưa có quyền tải v3.
ID riêng; không coi đây là sửa B3. Chưa đăng ký grid search hoặc seed bổ sung.

| Thành phần | Đề xuất |
|---|---|
| Backbone / feature | Đóng băng, eval mode; `x_norm_clstoken`, 384 chiều, không L2 normalize |
| Head | `Linear(384,8)`, có bias, khởi tạo PyTorch với seed 42 |
| Ngân sách | 1 lượt backbone được chọn, tối đa 50 epoch head, patience 7 |
| Optimizer | SGD lr 0.01, momentum 0.9, weight decay 0.0001 |
| Scheduler | CosineAnnealingLR T_max=50, eta_min=0, step sau validation |
| Batch | 32 ảnh nguồn / optimizer step, toàn bộ crop của các ảnh đó, giữ batch cuối |
| Loss | Mean CE trong ảnh rồi mean giữa ảnh; không thêm trọng số 1/n lần nữa |
| Chọn checkpoint | Macro-F1 cấp ảnh lớn nhất; hòa giữ epoch sớm hơn |
| Validation | Trung bình vector softmax crop cùng image_id rồi argmax; đủ 8 lớp |
| Runtime | CUDA FP32, AMP=false, TF32=false, thuật toán deterministic |
| Features | Cache deterministic 1 view/crop, shard 128 crop, inference batch 32 |

LR/scheduler là đề xuất riêng cho linear probe, không suy ra từ B1 hoặc gọi là
cùng compute với B2. Cùng ảnh, split và cấp metric giúp lập đối chứng; kiến trúc,
pretraining, preprocessing và số tham số được học đều khác. Muốn thử thêm seed,
LR hay fine-tune phải đăng ký lượt khác trước, mở experiment ID mới và mở rộng
validator config có kiểm thử. Phiên bản hiện tại chỉ triển khai seed 42 và frozen backbone.

Preprocessing train và val là xác định để cache có nghĩa:

- DINOv3: RGB → tensor uint8 → resize vuông 256×256, bilinear antialias →
  float32 /255 → ImageNet normalize. Theo ví dụ LVD-1689M trong
  [README chính thức](https://github.com/facebookresearch/dinov3).
- DINOv2: RGB PIL → resize cạnh ngắn 256 bicubic → center crop 224×224 →
  tensor float → ImageNet normalize, theo
  [eval transform chính thức](https://github.com/facebookresearch/dinov2/blob/main/dinov2/data/transforms.py).
- Mean `[0.485,0.456,0.406]`, std `[0.229,0.224,0.225]`. Không random augmentation.
  Bbox nguyên trạng, padding 0, không EXIF transpose. Patch size v3=16, v2=14.

## 1. Môi trường và pretrained

Các lệnh dưới chạy từ gốc repo trong PowerShell. Chưa cần push để chạy local.
Python hiện có đã chạy được kiểm thử W5: 3.12.10, torch 2.6.0+cu124,
torchvision 0.21.0+cu124, RTX 4060 Laptop. Chưa xác nhận import/forward kiến trúc
DINO thật trên bộ này; `preflight --with-model` là bước bắt buộc trước cache.
Không nâng môi trường demo toàn máy. Nếu cần môi trường riêng:

```powershell
py -3.12 -m venv .venv-w5
.venv-w5/Scripts/python.exe -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
.venv-w5/Scripts/python.exe -m pip install -r requirements-tv3-w5.txt
```

Sau đó thay `python` ở các lệnh dưới bằng `.venv-w5/Scripts/python.exe`.
Nếu kiến trúc DINO cần phiên bản khác, dựng environment riêng, chạy lại kiểm
thử/smoke và ghi runtime mới trước chốt protocol. File requirements W5 chỉ
ghim các thư viện dùng trong kiểm thử; không cam kết mọi commit upstream đều tương thích.

Ưu tiên DINOv3:

```powershell
git clone https://github.com/facebookresearch/dinov3.git outputs/tv3_w5/vendor/dinov3
New-Item -ItemType Directory -Force outputs/tv3_w5/pretrained
```

Tự nhận quyền tải **ViT-S/16 pretrained LVD-1689M** theo
[hướng dẫn Meta](https://github.com/facebookresearch/dinov3#pretrained-models),
lưu file thật thành `outputs/tv3_w5/pretrained/dinov3_vits16.pth`.
Không đưa URL ký số, token hay email cấp quyền vào config/Git. Chưa tải được
thì dùng nhánh dự phòng dưới, không đổi tên weights DINOv2 thành v3.

```powershell
python -X utf8 scripts/dino_w5.py pin --config configs/dinov3_lp_w5.json --repo outputs/tv3_w5/vendor/dinov3 --weights outputs/tv3_w5/pretrained/dinov3_vits16.pth --source facebookresearch/dinov3:LVD-1689M:ViT-S16 --output configs/dinov3_lp_w5.local.json
python -X utf8 scripts/dino_w5.py preflight --config configs/dinov3_lp_w5.local.json --with-model --output outputs/tv3_w5/model_preflight_01.json
```

`pin` lưu commit Git upstream thực tế và SHA weights vào config mới; SHA này
xác định file đã nhận, không tự chứng minh nguồn tải. `load_state_dict(strict=True)`
và smoke kiểm tra file tương thích. Giữ checkout upstream sạch, không tự sửa.

Phương án DINOv2, chỉ dùng khi chọn dự phòng:

```powershell
git clone https://github.com/facebookresearch/dinov2.git outputs/tv3_w5/vendor/dinov2
New-Item -ItemType Directory -Force outputs/tv3_w5/pretrained
Invoke-WebRequest https://dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth -OutFile outputs/tv3_w5/pretrained/dinov2_vits14.pth
python -X utf8 scripts/dino_w5.py pin --config configs/dinov2_lp_w5.json --repo outputs/tv3_w5/vendor/dinov2 --weights outputs/tv3_w5/pretrained/dinov2_vits14.pth --source facebookresearch/dinov2:LVD-142M:ViT-S14 --output configs/dinov2_lp_w5.local.json
python -X utf8 scripts/dino_w5.py preflight --config configs/dinov2_lp_w5.local.json --with-model --output outputs/tv3_w5/model_preflight_v2_01.json
```

## 2. Chốt protocol và chạy

Gửi TV2 config đã pin và bảng đề xuất phía trên. `pin` sinh kèm file
`configs/dinov3_lp_w5.local.protocol.json` (hoặc v2) với status DRAFT, theo
định dạng TV2 tại `3f76643`. Sau **đồng thuận thật** của TV2 và TV3, điền
`status=APPROVED`, `reviewers.TV2`, `reviewers.TV3` là người xác nhận,
`approval_evidence` là tham chiếu cuộc thống nhất/commit, `budget_reference`
mô tả tài nguyên và số lượt đã chốt. Điền `seeds=[42]`, `max_candidate_runs=1`,
`experiments=["DINOv3_LP_run01"]` chỉ nếu đúng quyết định thực tế (v2 dùng ID v2).
Không đăng ký cả hai backbone khi ngân sách chỉ cho một lượt. `reviewers.TV1`
để null đến khi có review thật; không tự nhận thay TV1. Giữ nguyên
`config_sha256` đã sinh, metric/tie/dataset policy. Chỉnh config thì phải pin
lại vào file mới và chốt lại. File receipt này dùng được cho cả trainer TV3
và auditor TV2; không cần hai file approval khác nhau.
Đây là yêu cầu ngày 1 trong plan TV3/TV2; không chỉ thay status để bỏ qua.

```powershell
python -X utf8 scripts/dino_w5.py cache --config configs/dinov3_lp_w5.local.json --protocol configs/dinov3_lp_w5.local.protocol.json
python -X utf8 scripts/dino_w5.py train --config configs/dinov3_lp_w5.local.json --protocol configs/dinov3_lp_w5.local.protocol.json
```

Nếu chọn v2, thay đúng hai tên file config/protocol bằng v2. Lệnh train cũng
tự tạo/tiếp tục cache nên lệnh cache là tùy chọn. Pipeline kiểm tra hash và
giải mã đủ 3.400 ảnh train/val trước mỗi lần chạy. Nó không đọc manifest/ảnh Test.
OOM báo lỗi; không tự giảm batch hoặc chuyển CPU. Đổi batch cần config/protocol
mới. Có thể dừng bằng Ctrl+C rồi chạy:

```powershell
python -X utf8 scripts/dino_w5.py train --config configs/dinov3_lp_w5.local.json --protocol configs/dinov3_lp_w5.local.protocol.json --resume
```

Giữ code/commit/config/runtime nguyên trạng giữa các lần resume. Trạng thái
và giới hạn khôi phục xem `docs/progress_tv3_w5_w6.md`.

## 3. Đầu ra và reload

Đầu ra nằm ở `outputs/tv3_w5/runs/DINOv3_LP_run01/` (hoặc v2):

- `best_model.pt`: cả backbone thật, head, config, class map, provenance và
  reference validation đầy đủ. `last_model.pt`: trạng thái resume + best head.
- `validation.json`: ID, logits/probabilities chưa làm tròn của mọi crop,
  mean probabilities mỗi ảnh, metric và per-class support.
- `confusion_matrix.csv/.png`, `train_log.json`, `validation_comparison.json/.md`.
- `binding.json`, `cache_reference.json`, `handoff.json`, `MODEL_CARD.md`.
- `val_crops.jsonl`: đủ 680 crop, trường ground_truth + class_scores đủ 8 lớp;
  giữ vector softmax thật, không tính lại từ logits ở bên nhận.
- `val_images.jsonl`: 600 ảnh, đủ experiment ID/checkpoint SHA, theo schema TV2.
- `class_map.json`, `preprocessing.json`: thứ tự lớp và phép biến đổi tách riêng.
- `reload_*.json` và `.predictions.json`: tiến trình Python mới trích lại toàn
  bộ 680 crop validation từ ảnh; không dùng cache để xác minh.

Reload tự động yêu cầu khớp đầy đủ reference chưa làm tròn. Khi lệch, giữ log
và không gọi là PASS. So CPU/GPU có thể khác; không nới dung sai để ép đạt.
Có thể chạy thêm attempt độc lập, dùng SHA trong `handoff.json`:

```powershell
$run = 'outputs/tv3_w5/runs/DINOv3_LP_run01'
$handoff = Get-Content "$run/handoff.json" -Raw | ConvertFrom-Json
python -X utf8 scripts/dino_w5.py reload --checkpoint "$run/best_model.pt" --sha256 $handoff.checkpoint_sha256 --device cuda --output "$run/reload_manual_01.json"
```

Reload thủ công tạo attempt mới và không tự thay handoff của lượt cũ. Nếu
reload tự động FAIL, giữ bằng chứng, điều tra trước khi công bố lại gói.

### Kiểm định bằng công cụ nguyên bản TV2

`scripts/audit_dino_tv2.py` đọc Git object tại commit cố định
`3f76643d1bc395098d90105e67a9cf29c8fe3256`, tạo snapshot nhỏ trong outputs;
không merge nhánh, không sửa mã TV2, không tải ảnh/model và không đọc Test.
Snapshot gồm code/schema, manifest train/val và predictions B2 do TV2 công bố.
Nếu chưa có commit: `git fetch origin`. Có thể chuẩn bị snapshot trước training:

```powershell
python -X utf8 scripts/audit_dino_tv2.py --prepare-only
```

Chỉ sau khi đã có gói thật và protocol đã duyệt:

```powershell
python -X utf8 scripts/audit_dino_tv2.py --run outputs/tv3_w5/runs/DINOv3_LP_run01 --protocol configs/dinov3_lp_w5.local.protocol.json --attempt dino_run01_audit01
```

Đầu ra dưới `outputs/tv3_w5/tv2_reference/<commit>/outputs/<attempt>/` gồm
audit, predictions và log/lệnh. Auditor tính lại bốn metric và bảng ảnh B2
đúng/DINO sai, B2 sai/DINO đúng, cùng đúng, cùng sai trên đủ 600 ảnh. Đây là
ARTIFACT_VERIFIED, không thay TV2 review hoặc bằng chứng model thật. Bảng
`validation_comparison.json` trong run vẫn ghi rõ nguồn B2 lịch sử; audit mới
bổ sung đối chứng từ predictions B2 W5, không giả vờ chạy lại B2 trên máy này.

## 4. Giao diện cho TV4

Ví dụ mã Python độc lập chạy từ gốc repo, sau khi có package thật:

```python
from pathlib import Path
from PIL import Image
from src.training.dino_probe import load_package, predict_crops, seed_all
seed_all(42)
backbone, head, transform, metadata = load_package(
    Path("outputs/tv3_w5/runs/DINOv3_LP_run01/best_model.pt"),
    expected_sha256="<SHA từ handoff.json>", device="cuda",
    repo_dir="outputs/tv3_w5/vendor/dinov3",
)
with Image.open("<ảnh crop cần dự đoán>") as im:
    logits = predict_crops(backbone, head, transform, [im.convert("RGB")], "cuda")
scores, ids = logits.softmax(-1).topk(3, dim=-1)
print(scores, ids, metadata["class_map"])
```

Không tự tích hợp vào registry TV4. Adapter demo cần gọi `predict_crops` cho
các crop detector và giữ top-3 riêng cho từng box. Gộp crop theo ảnh chỉ áp
dụng benchmark một nhãn. Scores chưa calibration. Không silent fallback B2.
Package chứa weights pretrained nên việc chuyển file cho TV4 phải tuân thủ
điều khoản nguồn weights; giữ thông tin nguồn/license với gói bàn giao.

## 5. Kiểm tra và push đúng phần TV3

```powershell
python -X utf8 scripts/check_environment.py
python -X utf8 scripts/validate_results.py
python -X utf8 -m unittest discover -s tests -v
git diff --check
git status --short
git add .gitignore configs/dinov3_lp_w5.json configs/dinov2_lp_w5.json src/training/dino_probe.py src/training/dino_handoff.py scripts/dino_w5.py scripts/audit_dino_tv2.py tests/test_dino_w5.py tests/test_dino_tv2_compat.py requirements-tv3-w5.txt docs/handoff_tv3_w5.md docs/progress_tv3_w5_w6.md reports/tv3/TV3_W5.md reports/tv3/W5_PROTOCOL_PROPOSAL.md reports/tv3/W5_TV2_COMPATIBILITY.md reports/tv3/w5_evidence
git commit -m "feat(tv3): prepare W5 DINO linear probe with hashed cache and reload"
git push origin feat/crop-classifier
```

Các file config pin/protocol đã được TV2 chốt nên được kiểm tra đường dẫn,
không có bí mật rồi stage riêng trước lượt thật để có code/config commit rõ ràng.
Không dùng `git add .`: workspace có notebook/ảnh EDA/tài liệu cá nhân đã đổi
từ trước. Weights, ảnh, feature shards, output và vendor repo nằm trong
`outputs/` bị Git ignore. Sau training, gửi weights ngoài Git kèm SHA/size;
chỉ đưa báo cáo/log/validation cần thiết vào thư mục report đã kiểm tra.
Nhờ TV1/TV2 review, TV4 kiểm adapter. Giữ nhánh TV3 sau merge.
