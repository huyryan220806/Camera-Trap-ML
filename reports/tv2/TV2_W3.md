# TV2 W3 IMPLEMENTATION REPORT

## Cập nhật CONTINUATION_04 – 18/10/2026

Trạng thái mới nhất:
**B1 CHECKPOINT HANDOFF VERIFIED – B1/B2 COMPARISON PENDING OFFICIAL B2**.
`B1_run01` giữ nguyên: 29 epoch, best epoch 22, validation macro-F1
`0.5624506868`, accuracy `0.565`. Checkpoint local và bản tải riêng từ
[Google Drive](https://drive.google.com/file/d/19efNKKDz0IwhoUYGrBr5X9fI_CnQ-EPq/view?usp=sharing)
cùng có 44.815.625 byte và SHA-256
`5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c`.
Validator đầy đủ trên bản Drive PASS: official reload, provenance và 600 ảnh
validation đều hợp lệ; metric/loss/logit delta bằng 0, test rows không được mở.
Bằng chứng được ghi trong `w3_evidence/continuation_04/`.

Đã fetch remote: TV3 vẫn ở `c01a751`, PASS 23/23 test cô lập nhưng bốn lỗi P1
vẫn tồn tại và nhánh chưa có official checkpoint/log/validation/reload B2. Vì
vậy không điền metric giả và không chọn model thắng. Xem
[checkpoint handoff](TV2_W3_CHECKPOINT.md), [review TV3](TV2_REVIEW_TV3_W3.md),
[comparison](TV2_W3_COMPARISON.md) và [README bàn giao](README_W3_HANDOFF_TEMP.md).
87/87 test TV2 PASS; hash `comparison_v1` và B0 PASS, test rows không được mở.
Các phần bên dưới là lịch sử tại thời điểm chúng được viết.

Ngày cập nhật 16/10/2026. **W3-02 CODE READY – TRAINING BLOCKED**.
Code, synthetic smoke và test đã chuẩn bị; chưa có thí nghiệm B1 chính thức.

## Continuation 01 — kiểm chứng lại ngày 16/10/2026

Trạng thái: **W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**.
[README bàn giao tạm thời](README_W3_HANDOFF_TEMP.md) chứa owner, điều kiện mở
khóa và lệnh tiếp tục. Starting commit `881d143510d23e3862e3748ed2b7cb707aab7dc5`,
đã push; code P1 tại `bf9aae4` không thay đổi trong lượt này.

- Đã fetch/đọc main trước, kiểm TV1/TV3 lại. TV1 vẫn `468d81f`; TV3 vẫn
  `d08eba7`; không có bundle W3-01 chính thức trên refs đã fetch.
- **P1 CODE FIX VERIFIED LOCALLY**: regression mới **78/78 PASS**, 0 fail/error/skip,
  29.998 giây. **REAL COMPARISON_V1 VERIFICATION PENDING**; chưa reviewer accepted.
- Synthetic CPU smoke/reload PASS; official CLI exit1 đúng vì thiếu freeze.
  Không có official epoch/checkpoint/validation metric.
- Sửa nhận định phần cứng trước đây: `nvidia-smi` thấy **RTX4060 Laptop 8188MiB**,
  driver610.78. Interpreter3.14.3 dùng torch2.13.0+cpu/torchvision0.28.0+cpu,
  CUDA unavailable. Không có runtime CUDA hoặc budget được duyệt; checker
  phiên bản ghim vẫn FAIL, pip check PASS. Ổ workspace còn 380165210112 byte
  tại thời điểm audit; ảnh swg_pilot_v2/comparison_v1 chưa có local.
- Draft PR4 đang mở, draft=true, mergeable=false. Giữ root README nguyên vẹn,
  không merge/rebase hoặc sửa nhánh thành viên.
- Đối chiếu SHA-256 trước/sau **53 file được bảo vệ**, gồm B0_run01, checkpoint
  B0, W2 code/tests/reports và ba tài liệu cá nhân: không đổi.
- Evidence mới ở [continuation_01](w3_evidence/continuation_01/verification.json),
  log cũ vẫn giữ nguyên. Snapshot mới: `LOCAL_REVIEW_RESULTS/W3/CONTINUATION_01/`.

Các mục A–N dưới đây giữ lịch sử triển khai; thông tin trạng thái mới nhất lấy
từ mục continuation này và README tạm. Đặc biệt “máy không có GPU” trong lịch
sử chỉ phản ánh torch CPU không thấy CUDA, không mô tả đúng phần cứng hiện tại.

## A. Repository audit

Đã thực hiện READ MAIN → READ TV2/TV1/TV3/TV4 trước sửa code.

| Vai trò | Ref đọc | Commit thực tế |
|---|---|---|
| Main | origin/main | 468d81f7272a4497d8b54a53a3651fd13c6dfbc2 |
| TV2 trước review mới | origin/feat/baseline | 8c0039ecb6e9987904e8a52b405cea4f8ccaac25 |
| TV1 | origin/feat/metadata-split | 468d81f7272a4497d8b54a53a3651fd13c6dfbc2 |
| TV3 | origin/feat/crop-classifier | d08eba7fffbfb6ecc813de8522fb4d58cd8ed904 |
| TV4 | origin/feat/demo | 468d81f7272a4497d8b54a53a3651fd13c6dfbc2 |

Main hiện đã tích hợp W2, gồm dữ liệu metadata v2 của TV1 và các phần khác đã
merge. Không có W3-01 `comparison_v1` hoặc freeze handoff trên bất kỳ remote ref
đã fetch. Nguồn đọc: README.md,
CONTRIBUTING.md, docs/architecture.md, docs/experiment_protocol.md,
docs/environment.md, docs/gpu_schedule.md, docs/result_contract.md,
requirements*.txt, src/evaluation/metrics.py, data/processed/v1/class_map.json,
audit.json, provenance.json và inventory configs/scripts/tests/contracts.
Không đọc test manifest hoặc ảnh test. Đọc audit tổng hợp không phải đánh giá test.

TV2 giữ kiến trúc hiện có: tái sử dụng dataset/transform, seed, evaluate, plotting,
atomic artifact publication và run reservation từ W2; thêm module B1 riêng,
không sửa source B0. Phạm vi TV2: model/training/validation B1, config,
test, báo cáo/review, phần README TV2. Các interface giữ nguyên: class IDs,
manifest split, metric semantics, inference schema và preprocessing metadata
đi kèm checkpoint. TV4 W2 vẫn detector-only, chưa có B1 classifier integration.

TV1/TV3/TV4 chỉ đọc bằng git show/ls-tree; không checkout, merge hay chạy code
của họ. Chênh lệch sẵn có giữa TV2 và main không phải thay đổi của lượt W3.
Không có AGENTS.md trong inventory repository. Ba tệp local chưa tracked có
sẵn được xem là tài liệu người dùng, giữ nguyên và không stage.

## B. W3-01 — Data gate

**BLOCKED – W3-01 HANDOFF NOT PRESENT ON REMOTE.**
Chưa có manifest/version/SHA-256/freeze evidence chính thức W3; train/val/classes
của W3: chưa chốt. Remote `feat/metadata-split` hiện bằng main. Có artifact W2
v2 thật đã tích hợp, nhưng không có commit W3 để nâng nó thành comparison freeze.

| Bằng chứng W2 v2 (không phải W3 frozen) | Giá trị |
|---|---|
| Train | 2.800 ảnh, 2.277 chuỗi, 458 location |
| Validation | 600 ảnh, 508 chuỗi, 102 location |
| Classes | 8; 350 train +75 val mỗi lớp |
| Train SHA-256 | 537d467f7f0ec1ea9fb6a182a37caf0ca1b4f572818789eb6a8c7fc118ef0a11 |
| Val SHA-256 | 4a18d30378619a39a317af93e1a375ba95162b234380cbf373f26308ac0dfd34 |
| Class map SHA-256 | e43e3cec029b4af1ac3c8183e35eed11d60cddc1a21be878e29ad40c1d79f0c3 |
| Train/val overlap ID/path/location/sequence/byte hash/pixel hash | 0, theo metadata Git đã đối chiếu |

Mapping: 0 large_antlered_muntjac; 1 annamite_striped_rabbit; 2 sambar;
3 chinese_serow; 4 common_palm_civet; 5 masked_palm_civet; 6 silver_pheasant;
7 eurasian_wild_pig. Không thay mapping hay split.

Chưa kiểm định ảnh W3 thật, chưa nhận ledger W3 kept/excluded, box QA hay
attestation leakage toàn bộ split. Không mở test để tự làm W3-01 thay TV1.
Gate kiểm SHA-256/committed receipt, mapping, source membership, train/val
leakage, duplicate, số lớp, crop coverage, exclusion accounting, full decode,
dimensions và byte/pixel hash; lỗi dừng, không âm thầm lọc ảnh. Chi tiết:
[review TV1](TV2_REVIEW_TV1_W3.md), [audit máy đọc](w3_evidence/repository_audit.json).

Sau review ngày 16/10, gate đã bỏ giả định một JPEG crop/ảnh. Adapter hiện đọc
B1 projection (`sample_id`, `input_type`, `sample_weight`) và đối chiếu trường
provenance có nghĩa với manifest ảnh nguồn; B2 chấp nhận mọi box hợp lệ cùng
loài theo `bbox_xyxy`, URL/hash ảnh nguồn, ID crop/annotation duy nhất và trọng
số `1/N`. Tập parent IDs và toàn bộ valid boxes phải khớp B1/source. Đây mới là
fixture theo schema review; bundle TV1 thật vẫn chưa có trên Git để chạy preflight.

## C. B1 configuration

Config [b1.yaml](../../configs/b1.yaml) là **PROPOSED**, chưa được TV3 đồng thuận.

- Architecture ResNet18, 8 outputs; pretrained IMAGENET1K_V1 trực tiếp từ
  torchvision, nguồn `https://download.pytorch.org/models/resnet18-f37072fd.pth`.
- B0 chỉ học FC (4.104 parameters), giữ backbone/BatchNorm frozen. B1 mở toàn bộ
  **11.180.616 trainable, 0 frozen** với 8 lớp; optimizer chỉ nhận requires_grad.
  BatchNorm train/eval theo phase. Không khởi tạo từ B0.
- Seed42; SGD lr0.001, momentum0.9, weight_decay0.0001; StepLR10/gamma0.1.
- Batch32, tối đa50 epoch, early stopping7, image224/resize256, workers0.
- Train: random crop, horizontal flip0.5, jitter(0.2,0.2,0.1,0.05); validation:
  center crop xác định. ImageNet normalization, unweighted CE.
- Checkpoint selection: validation macro-F1 trên đủ lớp; hòa điểm giữ best cũ.

Module mới: src/models/b1.py, src/training/b1.py, src/training/b1_gate.py;
scripts/train_b1.py và scripts/validate_b1.py. Giao diện receipt/protocol, command
và giới hạn có trong [protocol PROPOSED](TV2_W3_PROTOCOL.md).

## D. B1 training

**Training executed: NO (official)**. Epochs completed: 0; best epoch, runtime,
peak GPU memory chính thức: N/A. Training status: BLOCKED.

Môi trường thực kiểm thử: Python3.14.3, torch2.13.0+cpu, torchvision0.28.0+cpu,
CUDA available=False, CUDA version=None, GPU=None. Không thay PyTorch/CUDA,
không tự giảm budget sang CPU. Cần môi trường CUDA/budget đã được nhóm xác nhận.

Synthetic smoke riêng chạy 2 epoch trên ảnh RGB sinh tạm, ResNet18 thật,
weights=None, 2 lớp, batch2, input32; trainable11.177.538. Test gồm forward,
loss hữu hạn, toàn bộ gradients, optimizer step, validation, checkpoint save/load
và fresh-model reload. Không phải dữ liệu SWG, không phải training history B1.
Thời gian đo và chứng cứ đầy đủ: [smoke.txt](w3_evidence/smoke.txt).

Official pipeline đã chuẩn bị epoch CSV (loss, 4 metrics, LR, thời gian,
sample count, batch thực tế, peak allocated VRAM), best checkpoint, config,
data gate, trạng thái lỗi/interruption. Không có resume; run đã có phải dùng ID
mới. Không tạo experiments/B1_run01 trong lượt này.

## E. B1 validation

Macro-F1, macro-precision, macro-recall, accuracy, validation loss, per-class
metrics/support, confusion matrix, learning curves, validation samples và best
epoch **đều N/A cho B1 official**. Không tạo bảng số liệu giả, không lấy W2 B0
hoặc fixture làm B1. Pipeline đã được kiểm tra tạo các artifact tương ứng trên
fixture tạm rồi xóa. Không tạo notebook giả khi chưa có kết quả thật.

## F. Checkpoint

Official file chưa tồn tại; size/hash/download URL N/A. Reload official:
NOT TESTED; metric differences official: N/A. **PENDING ARTIFACT UPLOAD** sau
khi có model thật. Synthetic checkpoint reload PASS, bốn metric và logits delta0,
nhưng đã xóa và không dùng bàn giao TV4. [Checkpoint handoff](TV2_W3_CHECKPOINT.md).

## G. TV2 tests

**78/78 PASS, 0 FAIL, 0 SKIPPED**, gồm toàn bộ **52 test W2 +26 test B1**.
Chạy `python -X utf8 -m unittest discover -s tests -v`.
Log mới: [tests_after_p1.txt](w3_evidence/tests_after_p1.txt). Synthetic CLI
smoke PASS; official CLI
bị chặn đúng trước train; [official_gate.txt](w3_evidence/official_gate.txt).

Lượt đầu bị lỗi TEMP sandbox và thiếu ijson, chưa được coi PASS. Đã đặt TEMP/TMP
vào outputs/tv2_w3/tmp, cài riêng đúng ijson3.5.1 vào outputs/tv2_w3/deps và thêm
PYTHONPATH cho tiến trình test; không sửa/bỏ test cũ hoặc đổi environment hệ thống.

`pip check`: PASS (No broken requirements found). Contract validator: 6/6 PASS.
`scripts/check_environment.py`: **FAIL** vì Python3.14.3 khác3.12, NumPy2.4.4
khác2.5.3, matplotlib3.10.9 khác3.11.2. Đây là environment chuẩn W1 chưa tái lập,
không sửa checker để báo PASS. Torch/torchvision hiện cũng khác bộ ghim2.8/0.23.
Chưa xác nhận chạy trên bộ pinned Python3.12 hay CUDA; cần kiểm định trước official.
Logs ở [environment_check.txt](w3_evidence/environment_check.txt),
[pip_check.txt](w3_evidence/pip_check.txt), [contracts.txt](w3_evidence/contracts.txt).

Test độc lập code TV3 được chạy riêng trên snapshot commit `d08eba7`: **9/9
PASS**. Đây không phải một phần của bộ 77 test TV2 và không chứng minh official
B2 run. [TV3 test log](w3_evidence/tv3_w3_tests.txt),
[TV3 official gate](w3_evidence/tv3_w3_official_gate.txt),
[remote audit](w3_evidence/remote_audit_2026-10-16.json).

Lệnh tái lập kiểm thử tại máy này (chọn interpreter có sẵn, không phụ thuộc
WindowsApps python alias):

```powershell
New-Item -ItemType Directory -Force outputs/tv2_w3/tmp | Out-Null
$env:TEMP = Join-Path (Get-Location) 'outputs/tv2_w3/tmp'
$env:TMP = $env:TEMP
$env:PYTHONPATH = Join-Path (Get-Location) 'outputs/tv2_w3/deps'
# Chỉ khi thiếu ijson trong interpreter hiện có:
python -m pip install --target outputs/tv2_w3/deps --no-deps ijson==3.5.1
python -X utf8 -m unittest discover -s tests -v
python -X utf8 scripts/train_b1.py --smoke
```

## H. Cross-review

W3-01 TV1: **BLOCKED — HANDOFF NOT PRESENT ON REMOTE**. Có W2 v2 đã tích hợp
nhưng chưa có comparison freeze, receipt hay handoff W3.
[Checklist/evidence](TV2_REVIEW_TV1_W3.md).

W3-03 TV3: commit `d08eba7fffbfb6ecc813de8522fb4d58cd8ed904` có B2 code.
TV2 kiểm thử snapshot: **9/9 PASS**, nhưng official gate exit 1 vì thiếu
`comparison_v1`; không có checkpoint/kết quả/handoff. Review phát hiện lỗi
đường dẫn dữ liệu, preflight, checkpoint/best epoch, run immutability, reload và
protocol. Kết luận: **BLOCKED; CODE REVIEW FAIL**.
[Checklist/evidence](TV2_REVIEW_TV3_W3.md).

## I. B1/B2 comparison

Same eligible images, same split, same protocol: chưa xác nhận cho W3.
Crop W2 TV3 có4.000 train/1.000 val source images, giao pilot v2 chỉ595/147.
Transform, drop_last và nhiều box/ảnh cũng khác đề xuất. B1/B2 macro-F1 và
difference N/A. **COMPARISON PENDING**, không chọn model thắng.
[Comparison report](TV2_W3_COMPARISON.md). W4 chỉ đề xuất xem lỗi validation
sau khi so sánh hợp lệ; không triển khai B3 hoặc đánh giá test.

## J. W2 integrity

Source B0, tất cả artifacts B0_run01 kể cả checkpoint, metrics W2, reports W2
và test cũ giữ nguyên. Hash trước/sau được so byte trên toàn bộ tracked files
có trước lượt này, ngoại trừ README được phép thêm phần TV2 W3; ba tài liệu
untracked của người dùng cũng được bảo vệ. W2 tests:52/52 PASS.
[Verification](w3_evidence/verification.json) lưu số file kiểm, danh sách sai khác
(phải rỗng), trạng thái B0 checkpoint và SHA-256 thực tế. Không reset/restore W2.

## K. Git safety

Chỉ sửa/commit/push `feat/baseline`. Main, TV1, TV3, TV4 không sửa; không push
branch khác, không merge/rebase/reset/force push. Không stage trọng số, ảnh,
cache, environment, credential, artifacts tạm hoặc tài liệu local có sẵn.
Stage từng đường dẫn TV2 sau kiểm tra diff; chỉ README thêm một mục TV2 W3.

## L. Commit and remote

Implementation commit đã push:
`8c0039ecb6e9987904e8a52b405cea4f8ccaac25` —
`feat(tv2): prepare W3-02 B1 pipeline pending frozen manifest`.
Lượt cập nhật 16/10 chỉ bổ sung bằng chứng remote và review handoff mới; không
merge/cherry-pick code TV1/TV3. SHA của review commit và trạng thái push được ghi
trong phản hồi bàn giao sau khi Git hoàn tất, tránh tự tham chiếu hash trong
chính nội dung commit.

## M. Remaining work

- Hoàn thành trong phạm vi hợp lệ: audit, B1 pipeline, fail-closed gate, adapter
  schema comparison_v1 theo review, multi-crop tests, PROPOSED protocol,
  tests/smoke, cross-review checklists, báo cáo và README.
- Chờ TV1 push frozen W3 dataset/QA/exclusions/provenance và handoff thật; hiện
  không có W3-01 trên remote.
- Chờ TV3 sửa các lỗi code review, thống nhất source IDs, box selection,
  padding/aggregation, transforms, hyperparameters/budget; sau đó mới tạo B2 W3
  training artifacts để review.
- Chờ CUDA và môi trường được kiểm định/budget được duyệt. CPU smoke không
  thay thế GPU smoke/preflight với dữ liệu đã khóa.
- Chưa làm: official B1 train/validation/reload, upload checkpoint, metric
  comparison và nghiệm thu TV3. Không làm W3-01/W3-03/W3-04 thay thành viên khác.
- Không cần thêm xác nhận để chuẩn bị/commit/push phần TV2 đã được yêu cầu.
  Đồng thuận khoa học TV1/TV3 và budget là phụ thuộc thực trước official run.

## N. Final status

**W3-02 CODE READY – TRAINING BLOCKED**.
