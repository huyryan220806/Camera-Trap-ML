# TV3 W6 — hướng dẫn chạy và bàn giao

Cập nhật 05/11/2026. **Đã viết code; chưa chạy test, smoke, train, reload hoặc push
trong lượt triển khai này. Chưa có checkpoint/kết quả W6.**

Dùng yêu cầu mới `TV3_W6.md`, không dùng phần W6 cũ của `TV3_W5_W6.md`.
TV2 tại `b91476d3d9658e006027225cfc93008125536c0f` đã hoàn thành **D1 chuẩn bị**,
protocol vẫn DRAFT; chờ TV3 smoke/config/source/runtime. Không hiểu “TV2 làm xong”
là đã cho phép train. W5 đã tích hợp ở `cfcf00615847d52fba73ee3e44fe0e6076bb840c`.

## 1. Đồng bộ source rồi kiểm thử

Mở PowerShell tại repo. Các file notebook/EDA và tài liệu riêng đang sửa từ trước
không thuộc lần nộp này. Không dùng `git add .`, `git reset --hard`, force push.
Mỗi lệnh Git phải thành công mới tiếp tục; nếu báo conflict/overwritten files,
dừng và giữ nguyên output để xử lý, không chọn bỏ toàn bộ một phía.

```powershell
Set-Location -LiteralPath 'C:\Users\Admin\OneDrive\Documents\VLU\Năm 3\HK1nam3\Học máy và ứng dụng\Project ML'
git status --short --branch
git fetch origin
git merge --ff-only origin/feat/crop-classifier
git merge --no-edit origin/feat/baseline
```

Hai lệnh merge trên để bạn thực hiện: local khi viết code đang ở `5734d38`,
remote TV3/main ở `cfcf006`, TV2 ở `b91476d`. Code mới dùng tên riêng,
`configs/w6/tv3/`, không ghi đè config DRAFT của TV2. Merge TV2 mang theo
validator, schema và registry cần thiết. Chưa cần merge dữ liệu TV1 cho R1/R2.

Dùng **Python đã chạy W5 thành công**, không cài lại/nâng cấp thư viện tùy ý:

```powershell
$pyW6 = 'C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe'
& $pyW6 --version
& ./scripts/check_tv3_w6.ps1 -Python $pyW6 -Output outputs/tv3_w6/checks01 -FullSuite
```

Script chạy environment, contracts, unit tests W6 TV3/TV2 và full suite;
lưu log + exit code + SHA vào thư mục mới. Các vòng train trong unit test là
fixture CPU giả, không dùng ảnh thật, không tính như official experiments.
Nếu FAIL thì dừng, gửi log để sửa lỗi thật; chưa smoke/train. `checks02` chỉ dùng
khi có lý do chạy lại; không ghi đè `checks01`.

Khi test đạt, **commit source trước smoke** để có source SHA thật:

```powershell
git config user.name
git config user.email
# Nếu cần sửa email local của repo:
git config user.email 'phuc.2474802010313@vanlanguni.vn'
git add -- src/training/dino_w6.py src/training/dino_w6_control.py src/training/dino_w6_delivery.py scripts/dino_w6.py scripts/check_tv3_w6.ps1 tests/test_dino_w6.py configs/w6/tv3/R1.candidate.json configs/w6/tv3/R2.candidate.json docs/handoff_tv3_w6.md docs/progress_tv3_w6.md reports/tv3/w6/REPORT.md reports/tv3/w6/.gitattributes
git diff --cached --check
git diff --cached --stat
git commit -m 'feat(tv3): add W6 pooling and partial fine-tuning pipeline'
git push origin feat/crop-classifier
git rev-parse HEAD
```

Source guard chỉ kiểm các file thực sự tham gia chạy. Thay đổi notebook/EDA
ngoài phạm vi được giữ nguyên. Source, config và approval cần nằm trong lịch sử
Git trước official validation; không cần sửa config để chèn SHA của chính commit
chứa config (tránh vòng lặp hash).

## 2. Preflight và smoke chỉ trên train

Dùng lại **checkpoint W5 thật** đã có; không tải thêm DINOv3. Mặc định:

- Init: `outputs/tv3_w5/runs/DINOv3_LP_run01/best_model.pt`.
- SHA: `acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3`.
- Vendor: `outputs/tv3_w5/vendor/dinov3`, commit `6876159a11b4df116f30f667f8c9888617df0751`.

Nếu file ở chỗ khác, truyền `--init-checkpoint` / `--repo` đúng đường dẫn; nội dung
vẫn phải đúng SHA/commit. Không sửa `src/training/dino_probe.py` hoặc checkpoint W5.

```powershell
& $pyW6 -X utf8 scripts/dino_w6.py preflight --config configs/w6/tv3/R1.candidate.json --registry experiments/w6/registry.json --output outputs/tv3_w6/preflight_R1_01.json
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed; stop.' }
& $pyW6 -X utf8 scripts/dino_w6.py preflight --config configs/w6/tv3/R2.candidate.json --registry experiments/w6/registry.json --output outputs/tv3_w6/preflight_R2_01.json
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed; stop.' }
```

Preflight kiểm bytes/RGB train/val, không chạy model. Smoke bên dưới chỉ decode
mẫu **train** và không tính metric val. Thống nhất GPU/thời gian với nhóm rồi nhập
slot thực tế; đây là ghi nhận lịch sử, không phải chương trình tự đặt GPU:

```powershell
$slotW6 = Read-Host 'Ghi GPU và khung giờ đã thống nhất thực tế với nhóm'
& $pyW6 -X utf8 scripts/dino_w6.py smoke --config configs/w6/tv3/R1.candidate.json --attempt R1_smoke01 --booking "$slotW6"
if ($LASTEXITCODE -ne 0) { throw 'R1 smoke failed; stop and retain evidence.' }
& $pyW6 -X utf8 scripts/dino_w6.py smoke --config configs/w6/tv3/R2.candidate.json --attempt R2_smoke01 --booking "$slotW6"
if ($LASTEXITCODE -ne 0) { throw 'R2 smoke failed; stop and retain evidence.' }
```

Receipt: `outputs/tv3_w6/smoke/R1_smoke01/receipt.json` và tương tự R2.
Smoke dùng parent nhiều crop nhất, đủ một batch và batch cuối 3 ảnh; ghi
named parameter mask, gradient, mode, frozen unchanged, strict load, resume,
VRAM, runtime, source, command/exit và thời gian. Đây không phải full model replay.

R2 nếu OOM: giữ receipt FAIL, **chỉ trước freeze/official** mới giảm
`crop_microbatch` từ 8 xuống 4 hoặc 2, giữ `parent_batch=16`; tạo config candidate
mới, test và smoke ID mới rồi gửi TV2 review. Không đổi AMP/FP32, batch ảnh, lr,
epochs hoặc tự chạy lại official để chữa OOM. Mọi smoke đều vào trần 12 GPU-giờ.

## 3. Tạo hồ sơ freeze và gửi TV2 phê duyệt

`freeze` khóa config từ evidence thật, **không cấp approval**. Dùng proposal R1
làm đầu vào cho R2 để không mất thông tin R1:

```powershell
& $pyW6 -X utf8 scripts/dino_w6.py freeze --config configs/w6/tv3/R1.candidate.json --smoke outputs/tv3_w6/smoke/R1_smoke01/receipt.json --registry experiments/w6/registry.json --output configs/w6/tv3/R1.frozen.json --proposal experiments/w6/tv3_R1.proposal.json
if ($LASTEXITCODE -ne 0) { throw 'R1 freeze failed.' }
& $pyW6 -X utf8 scripts/dino_w6.py freeze --config configs/w6/tv3/R2.candidate.json --smoke outputs/tv3_w6/smoke/R2_smoke01/receipt.json --registry experiments/w6/tv3_R1.proposal.json --output configs/w6/tv3/R2.frozen.json --proposal experiments/w6/tv3_R1_R2.proposal.json
if ($LASTEXITCODE -ne 0) { throw 'R2 freeze failed.' }
& $pyW6 -X utf8 scripts/evaluate_w6_validation.py --registry experiments/w6/tv3_R1_R2.proposal.json
Get-FileHash configs/w6/tv3/R1.frozen.json,configs/w6/tv3/R2.frozen.json -Algorithm SHA256
```

SHA raw = bytes file; SHA canonical W6 = compact sorted JSON UTF-8, không newline.
Chương trình in canonical SHA. Không dùng công thức digest có dấu cách của W5.
Receipt smoke được sao chép nguyên byte sang `reports/tv3/w6/smoke/`.

```powershell
git add -- configs/w6/tv3/R1.frozen.json configs/w6/tv3/R2.frozen.json experiments/w6/tv3_R1.proposal.json experiments/w6/tv3_R1_R2.proposal.json reports/tv3/w6/smoke/R1_smoke01.json reports/tv3/w6/smoke/R2_smoke01.json
git diff --cached --check
git diff --cached --stat
git commit -m 'docs(tv3): submit W6 smoke and frozen config proposal'
git push origin feat/crop-classifier
git rev-parse HEAD
```

Gửi TV2 commit này, log `checks01`, hai preflight JSON và usage.json. Nhắn:

> TV3 đã bổ sung pipeline W6 riêng cho R1 CLS+mean patch và R2 fine-tune hai
> block cuối. Mình gửi source commit [SHA], hai config frozen kèm raw/canonical
> SHA, train-only smoke, test logs và GPU accounting tại [link]. AdamW betas
> (0.9,0.999), eps 1e-8; warmup epoch1=0.5×lr, epoch2=1×lr, rồi cosine về 0
> tại epoch20; bias/norm không decay, LayerScale vẫn decay. FP32, microbatch
> đã smoke, frozen modules eval. Mình chấp thuận dùng đúng các config này cho
> R1/R2 trong ngân sách W6, chưa chạy official. Nhờ bạn review và commit registry
> APPROVED cùng evidence, rồi gửi commit và SHA receipt để mình đồng bộ.

Chỉ gửi đoạn “smoke/test đạt” sau khi thật sự PASS. Reviewer không được ghi
approval thay người khác. Các chi tiết recipe mới là đề xuất triển khai, chưa
được TV2 đồng ý chỉ vì có trong code. `freeze` không sửa các dictionary optimizer/
scheduler đã đề xuất của TV2; chi tiết bổ sung ở `implementation`.

## 4. Sau khi TV2 trả APPROVED: official R1 rồi R2

Nhận đúng commit TV2 và đồng bộ bằng Git. Kiểm SHA file receipt mà TV2 gửi bằng
`Get-FileHash`. Ví dụ dưới giả sử receipt được TV2 đặt tại
`experiments/w6/registry.approved.json`; **thay bằng tên thật**, không tự đổi
`DRAFT` thành `APPROVED` trên máy bạn.

```powershell
git fetch origin
git merge --no-edit origin/feat/baseline
Get-FileHash experiments/w6/registry.approved.json -Algorithm SHA256
& $pyW6 -X utf8 scripts/evaluate_w6_validation.py --registry experiments/w6/registry.approved.json
```

Registry và frozen config phải đã commit, source phải khớp commit smoke,
runtime giống chính xác, usage.json phải đầy đủ. Khi đổi máy phải mang cả
`outputs/tv3_w6/usage.json`, runs, features, smoke và receipts; không bắt đầu
một ledger rỗng. R2 vẫn giữ batch16 ảnh, microbatch≤8 crop; không bỏ batch cuối.

```powershell
$slotW6 = Read-Host 'GPU và khung giờ official đã thống nhất thực tế'
& $pyW6 -X utf8 scripts/dino_w6.py train --config configs/w6/tv3/R1.frozen.json --registry experiments/w6/registry.approved.json --attempt R1_attempt01 --booking "$slotW6"
if ($LASTEXITCODE -ne 0) { throw 'R1 failed/interrupted; stop, retain files and report.' }
& $pyW6 -X utf8 scripts/dino_w6.py reload --run outputs/tv3_w6/runs/R1_attempt01 --receipt reload01 --booking "$slotW6"
if ($LASTEXITCODE -ne 0) { throw 'R1 exact reload failed; report to TV2.' }
```

`reload` là lần gọi Python mới, không dùng cache, đủ 600 val/680 crop, exact
logits/scores/metrics. Không chạy lại R0 hoặc mở Test. Khi PASS, chạy auditor:

```powershell
& $pyW6 -X utf8 scripts/evaluate_w6_validation.py --registry outputs/tv3_w6/runs/R1_attempt01/registry.result.json --run-id R1 --handoff outputs/tv3_w6/runs/R1_attempt01/handoff.json --checkpoint outputs/tv3_w6/runs/R1_attempt01/best_model.pt --output outputs/tv3_w6/audit_R1_01
if ($LASTEXITCODE -ne 0) { throw 'R1 artifact audit failed.' }
```

Sau R1, làm tương tự R2: thay `R1.frozen.json`→`R2.frozen.json`,
`R1_attempt01`→`R2_attempt01`, `--run-id R1`→`R2`, `audit_R1_01`→`audit_R2_01`.
Không chạy song song hai recipe trên cùng ledger. Handoff sau cùng dùng
`registry.result.json` của lượt hoàn thành gần nhất, chứa cả lịch sử trước đó.

**Khi bị ngắt:** giữ nguyên attempt/config/receipt/source/runtime, dùng lại lệnh
train với `--resume`. Resume khôi phục epoch hoàn tất gần nhất và chạy lại phần
epoch bị ngắt; không reset patience/RNG/optimizer/scheduler. Nếu training đã xong
nhưng reload FAIL thì chỉ điều tra/reload, không dùng `train --resume` để train lại.
Không đổi attempt ID để che lỗi.

Nếu máy/Colab chết đột ngột, session có seconds=null chặn lượt mới. Gửi usage.json
và log cho TV2; cần receipt accounting thật có `status=REVIEWED`, `session_id`,
`elapsed_seconds`, `reviewers.TV2`, `reviewers.TV3`, `evidence`,
`process_confirmed_stopped=true`; sau khi đối chiếu tiến trình và thời gian mới dùng:

```powershell
& $pyW6 -X utf8 scripts/dino_w6.py settle-usage --receipt duong_dan_receipt_accounting_da_duyet.json
```

Không tự điền thời gian ngắn hơn heartbeat. Receipt không phải chữ ký mật mã;
TV2 phải kiểm authorship/evidence. Giới hạn 2h/attempt và 12h tổng dùng wall time
của GPU session (tính bảo thủ cả I/O trong session), có dự phòng 60 giây trước
batch tiếp theo. Nếu một tác vụ vượt dự phòng, ghi thời gian thật và dừng; không
cam kết hard realtime, không cắt số đo để làm đẹp budget. Giữ mọi FAIL/OOM/STOPPED.

## 5. Chọn recipe và điều kiện R3–R6

Gửi **cả R1 lẫn R2**, kể cả không thắng, cho TV2 kiểm định và chọn bằng seed42:
macro-F1 → accuracy → chi phí inference trên cùng benchmark → run ID. Nếu hòa
mà thiếu benchmark thì chờ, không đoán từ kiến trúc. Không tự chọn seed cao nhất.

- R3 seed43/R4 seed44: chỉ khi recipe R1/R2 vượt R0 theo TV2 và còn budget.
- R5 seed42/R6 seed43: chỉ khi TV2 data review PASS release
  `train_expansion_w6_v1` và chốt recipe. Nếu R1/R2 không thắng, R0 fallback cần
  quyết định có evidence. Vẫn val600/680 và cùng class map.
- TV1 release hiện metadata quality-ready nhưng TV2 overall vẫn PENDING;
  không lấy 1665 ứng viên W5 hay dữ liệu chưa review để train.

CLI `prepare` tạo candidate từ **đúng recipe đã được chọn**, không tạo approval:

```powershell
# Ví dụ CHỈ khi TV2 chọn R1; nếu R2 thắng thì dùng R2.frozen.json.
& $pyW6 -X utf8 scripts/dino_w6.py prepare --base configs/w6/tv3/R1.frozen.json --run-id R3 --registry experiments/w6/registry.selected.json --output configs/w6/tv3/R3.candidate.json
```

Tiếp tục smoke/freeze/review cho config đó, run ID và attempt riêng. R4/R5/R6
tương tự, không chạy trước điều kiện. Khi R5/R6 được duyệt, nhận package ảnh TV1,
đồng bộ metadata từ commit được review; loader chỉ thay train bằng 4246 ảnh /
4729 crop. Không sửa cấu hình để trỏ sang thư mục tùy ý.

R0 fallback tái dùng backbone W5 và khởi tạo head384 mới theo seed (như LP),
không warm-start head đã chọn trên val. R2 tiếp tục khởi tạo full W5 cho mọi seed
và cả dữ liệu mở rộng; không khởi tạo R5 từ checkpoint R2 đã tune trên train cũ.
Chi tiết này phải nằm trong quyết định recipe của TV2.

Proposal các lượt sau giữ approval toàn cục đã có của lịch sử R1/R2, nhưng
`runs[R3/R4/R5/R6].approvals` vẫn null cho lượt mới. Không hiểu global APPROVED
là lượt mới đã được duyệt; gate yêu cầu approval riêng đúng config/source/seed.

## 6. Đóng gói, bàn giao và push kết quả

Chỉ package sau producer reload PASS và artifact audit PASS. Ví dụ R1:

```powershell
& $pyW6 -X utf8 scripts/dino_w6.py package --run outputs/tv3_w6/runs/R1_attempt01 --registry outputs/tv3_w6/runs/R1_attempt01/registry.result.json --output outputs/tv3_w6/handoff/R1_attempt01.zip --report-dir reports/tv3/w6/results/R1_attempt01
if ($LASTEXITCODE -ne 0) { throw 'Package verification failed.' }
Get-FileHash outputs/tv3_w6/handoff/R1_attempt01.zip -Algorithm SHA256
```

ZIP chứa best + last thật, config/raw/canonical hash, full backbone+head,
source snapshot, vendor/init pins, runtime, class map, preprocessing, log mỗi
epoch, crop/image vectors, metrics/CM, comparison, reload, usage và registry.
`source_index.json` giữ SHA từng file source; weights/vendor license vẫn phải
được người nhận tuân thủ. Gửi ZIP và SHA ngoài Git; auditor result nằm riêng
`outputs/tv3_w6/audit_R1_01/audit.json`, gửi kèm. Không coi auditor là TV2 đã replay.

`--report-dir` tạo bản nhẹ không weights để commit. Copy audit và test logs nhỏ
vào report bằng thao tác sao chép nguyên byte; giữ nguyên bản local. Cập nhật
`reports/tv3/w6/REPORT.md` bằng **số thực**, tất cả lượt không thắng/lỗi,
seed42 headline, seed43/44 riêng và mean/sample SD, release/recipe tách biệt;
trích kết luận TV2 sau khi có. Mỗi tiến trình ghi run/epoch/command/path vào
`docs/progress_tv3_w6.md`. Không giữ bảng RESULT PENDING như báo cáo cuối.

Gửi TV2:

> TV3 gửi W6 [run IDs], recipe [R1/R2], seed [..], train [release]. Validation
> [accuracy], macro-F1 [giá trị chưa làm tròn], đủ600 ảnh/680crop. Producer reload
> exact [PASS/FAIL], artifact audit [PASS/FAIL]. Source commit [SHA]; ZIP [link],
> SHA256 [hash]; có best/last, config, source/runtime/data hashes, vectors, log,
> usage và bảng so R0. Nhờ bạn replay độc lập, rà regression từng lớp và chốt
> recipe/seed repeats theo protocol. Mình đã gửi cả lượt không thắng/lỗi.

Gửi TV4 sau khi có checkpoint W6 đủ evidence:

> TV3 gửi checkpoint W6 format `TV3_DINO_W6_V1` tại [link], SHA [hash], source
> [commit]. Loader mới `src.training.dino_w6.load_package/predict_crops`;
> pooling [..], dimension [768/384], RGB square256 như contract. Nhờ bạn tạo
> adapter riêng và đối chiếu native logits/per-box scores trên runtime đã pin.
> Producer reload [..], TV2 replay [trạng thái thật]. Chưa đổi model mặc định
> trước khi TV2 kết luận và adapter đạt. Giữ B2 mặc định, DINO W5 opt-in.

Gửi TV1 khi cần mở rộng:

> TV3 đã có pipeline nhận `train_expansion_w6_v1` nhưng R5/R6 vẫn khóa đến
> khi TV2 data review PASS. Nhờ bạn gửi commit/provenance và gói ảnh đúng release,
> cùng bằng chứng còn thiếu trong review TV2; mình giữ nguyên val/class map.

Mẫu gọi của TV4 (trong repo đã có source đúng commit, nhận checkpoint ngoài Git):

```python
from src.training.dino_w6 import load_package, predict_crops
model, transform, payload = load_package(checkpoint_path, checkpoint_sha256, vendor_repo, device="cuda")
logits = predict_crops(model, transform, rgb_pil_crops, "cuda")  # [number_of_boxes, 8]
scores = logits.softmax(-1)  # từng box, không gộp các box của ảnh trong demo
```

Push bản report riêng sau khi rà staged files:

Tạo bảng tổng hợp từ registry kết quả mới nhất (không chạy model), ví dụ sau R2:

```powershell
& $pyW6 -X utf8 scripts/dino_w6.py report --registry outputs/tv3_w6/runs/R2_attempt01/registry.result.json --output reports/tv3/w6/summary01.json
```

Lệnh tạo JSON/Markdown, kiểm artifact, ghi tất cả trạng thái/attempts, tính mean
và sample SD theo recipe/dataset, giữ seed42 headline. Gợi ý thứ tự metric vẫn
là PENDING TV2; hòa mà chưa có benchmark thì không chọn thay nhóm. Sau R3–R6,
dùng registry mới nhất và output `summary02.json`… để giữ lịch sử.

```powershell
git add -- reports/tv3/w6/results/R1_attempt01 docs/progress_tv3_w6.md reports/tv3/w6/REPORT.md
git diff --cached --check
git diff --cached --stat
git commit -m 'docs(tv3): publish W6 R1 validation and handoff evidence'
git push origin feat/crop-classifier
git rev-parse HEAD
```

Làm tương tự các lượt khác; chỉ stage đúng thư mục của lượt cần nộp. Không commit
outputs/ZIP/.pt/cache/ảnh. Push nhánh không tự merge main; tạo PR theo quy ước
nhóm và nhờ reviewer. Hoàn thành W6 khi có kết quả thật trong budget, replay,
kết luận trung thực và xử lý tích hợp; không cần ép accuracy88% bằng tuning thêm.
