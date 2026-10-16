# TV2 W3 – TEMPORARY HANDOFF README

## 1. General Information

- Project: Camera-Trap-ML; TV2 phụ trách B1 full-image fine-tuning và evaluation.
- Branch duy nhất được sửa/push: `feat/baseline`.
- Current commit được audit: `881d143510d23e3862e3748ed2b7cb707aab7dc5`.
  Commit chứa README này lấy bằng `git log -1 --format=%H -- reports/tv2/README_W3_HANDOFF_TEMP.md`.
- Review base: `8c0039ecb6e9987904e8a52b405cea4f8ccaac25`; P1 fix:
  `bf9aae404286a71ba6e912ce47f323bdcf53052d`.
- Date: 16/10/2026, continuation 01; timestamp UTC trong evidence.
- Main / TV1 `feat/metadata-split`: `468d81f7272a4497d8b54a53a3651fd13c6dfbc2`.
- TV3 `feat/crop-classifier`: `d08eba7fffbfb6ecc813de8522fb4d58cd8ed904`.
- [Draft PR #4](https://github.com/huyryan220806/Camera-Trap-ML/pull/4) đang mở,
  draft=true, merged=false, mergeable=false tại audit. Push cập nhật PR hiện có;
  không tạo PR mới, không giải quyết conflict bằng merge/rebase trong lượt này.
- Current W3 status: **W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**.

## 2. Completed Work

| Task | Status | Evidence | Notes |
|---|---|---|---|
| Fetch và đọc main trước các nhánh thành viên | DONE | [remote.json](w3_evidence/continuation_01/remote.json) | Không sửa main/TV1/TV3/TV4 |
| B1 pipeline, config, full fine-tune, BN, checkpoint protection | READY | src/models/b1.py; src/training/b1.py | Chưa chạy official |
| Adapter B1 projection, B2 multi-crop, hash/URL/box mapping | P1 CODE FIX VERIFIED LOCALLY | src/training/b1_gate.py; [tests](w3_evidence/continuation_01/tests.txt) | Fixture; không phải reviewer acceptance |
| Regression: mapping, leakage, image hash, gradient, reload, run immutability | DONE | [verification.json](w3_evidence/continuation_01/verification.json) | Tổng số/fail/skip lấy từ lần chạy mới |
| Synthetic smoke và fresh-model reload | DONE | [smoke.txt](w3_evidence/continuation_01/smoke.txt) | Không có official checkpoint; artifact tạm đã xóa |
| CLI train/validate và official gate từ chối đúng | DONE | [train help](w3_evidence/continuation_01/train_help.txt), [validate help](w3_evidence/continuation_01/validate_help.txt), [gate](w3_evidence/continuation_01/official_gate.txt) | Không có flag resume hoặc preflight trên CLI |
| Audit phần cứng, Python/dependencies/CUDA và dung lượng | DONE; official environment FAIL | [environment](w3_evidence/continuation_01/environment.txt), [nvidia-smi](w3_evidence/continuation_01/nvidia_smi.txt), [checker](w3_evidence/continuation_01/environment_check.txt) | Có RTX4060 8188MiB; torch2.13+cpu chưa chạy CUDA |
| So sánh config B1/B2 hiện tại, owner và đề xuất | DONE | [protocol](TV2_W3_PROTOCOL.md) | PROPOSED – AWAITING TV3 APPROVAL |
| Kiểm tra TV3 có commit sửa mới hay chưa | DONE | remote.json; [review](TV2_REVIEW_TV3_W3.md) | Commit không đổi; giữ 9/9 là evidence trước, không chạy lại vô ích |
| W2/B0 và tài liệu local được bảo vệ | DONE | [integrity.json](w3_evidence/continuation_01/integrity.json) | So SHA-256 trước/sau, gồm checkpoint B0 local |
| README tạm và snapshot local mới | DONE | File này; LOCAL_REVIEW_RESULTS/W3/CONTINUATION_01/FILE_MANIFEST.json | Chỉ copy, không ghi đè snapshot cũ |

`REAL COMPARISON_V1 VERIFICATION PENDING`. Chưa có bằng chứng độc lập để ghi
`P1 REVIEWER ACCEPTED`. Test synthetic không xác nhận chất lượng dataset thật.

## 3. Pending and Blocked Tasks

| ID | Công việc chưa hoàn thành | Nguyên nhân | Người phụ trách | Điều kiện mở khóa | Việc TV2 làm tiếp |
|---|---|---|---|---|---|
| BLOCKER-01 | TV1 W3-01 official data/preflight | Không có bundle comparison_v1/freeze/handoff trên refs đã fetch | TV1 bàn giao; TV2 kiểm tra | Commit đã push, provenance/hash/receipt hợp lệ, ảnh nguồn truy cập được, preflight PASS | Đối chiếu commit/hash, B1 view/source, class map, parent IDs, đủ box, split/location/sequence/content leakage và decode train/val |
| BLOCKER-02 | Common B1/B2 protocol | SGD/StepLR/50/patience7 khác AdamW/cosine/15/patience5; transforms, dropout, batching cũng khác | TV2 + TV3; chủ GPU xác nhận budget | Bằng chứng approval có danh tính/version/hash và config thống nhất | Cập nhật config/adapter nếu cần, tests, freeze hyperparameters; kiểm sampling/loss/compute |
| BLOCKER-03 | Môi trường CUDA và budget | Phần cứng có RTX4060, nhưng runtime torch CPU; Python/dependencies khác bộ ghim; booking trống | TV2 + chủ GPU | Environment riêng được kiểm định, CUDA forward/backward PASS, đủ VRAM/storage và khung giờ/budget xác nhận | Ghi phiên bản/thiết bị/VRAM, kiểm tra GPU smoke rồi data smoke; không cài đè environment hiện tại |
| BLOCKER-04 | Official B1 training | Phụ thuộc 01–03 và config chưa freeze | TV2 | Tất cả gate PASS, code/config commit, run ID mới | Chạy train_b1.py, giữ epoch logs/metrics/runtime/VRAM |
| BLOCKER-05 | Checkpoint/validation/reload/URL thật | Chưa có official run | TV2 | Training thành công, checkpoint đúng best epoch và hash, reload PASS | Fresh model + process validation; kiểm size/hash; upload và tải kiểm độc lập khi có nơi chia sẻ |
| BLOCKER-06 | TV3 B2 cross-review đạt | d08eba7 chưa có commit sửa, vẫn lỗi đường dẫn/gate/best epoch/reload/immutability | TV3 sửa, TV2 review | Commit sửa và handoff artifact thật, tests và acceptance đủ | Review diff mới, chạy tests cần thiết, đối chiếu mapping/weighting/aggregation/checkpoint/provenance |
| BLOCKER-07 | B1/B2 comparison | Cả hai chưa có kết quả thật, chưa cùng protocol | TV2 + TV3 | Cùng frozen parent IDs/val/classes, protocol tương đương, cả hai reload được | Điền bảng metric thật và paired support/per-class; ghi giới hạn khoa học |
| BLOCKER-08 | Nghiệm thu W3-02 và khả năng merge | P1 mới verified local; PR4 draft/mergeable=false | Reviewer + người tích hợp, phối hợp TV2 | Review độc lập sau artifact thật; conflict được xử lý trong công việc được phép | Bàn giao evidence và phản hồi review; không tự nghiệm thu hoặc merge |

### TV1 cần bàn giao chính xác

Push commit W3-01 trên `feat/metadata-split` và gửi SHA 40 ký tự. Cần bundle
`data/processed/comparison_v1/` (hoặc đường dẫn chính thức có mapping rõ):
`train.jsonl`, `val.jsonl` ảnh đầy đủ; `b1/train.jsonl`, `b1/val.jsonl`;
`b2/train.jsonl`, `b2/val.jsonl`; `class_map.json`; provenance/version và
freeze evidence; ledger kept/excluded có lý do, source train/val, counts
ảnh/chuỗi/lớp, QA/leakage attestation toàn split. TV2 chỉ đọc train/val và
attestation tổng hợp, không mở test rows/pixels.

Cần SHA-256 từng file và SHA-256 receipt/provenance **từ commit bàn giao**;
đối chiếu byte Git, byte local, image byte hash và pixel hash. Hash provenance
local `d9fd...a5f` ghi trong review không thay thế commit phát hành. Giao diện
receipt hiện là đề xuất TV2 trong protocol; nếu TV1 dùng schema khác, TV2 phải
đọc schema thật rồi sửa adapter có test, không yêu cầu TV1 sửa dữ liệu cho gate xanh.

### TV3 cần xử lý trước review lại

Sửa path `ROOT/comparison_v1` lệch với `ROOT/data/processed/comparison_v1`;
kiểm hash/freeze/source; thực thi early stopping; lưu best_epoch đúng; không gắn
best_metrics vào last-model weights; bảo vệ run mới và fresh reload có hash;
kiểm bbox/crop/nhãn nhất quán; tách test khỏi W3; ghi đủ runtime/VRAM. Chốt loss
theo ảnh và sampling/compute cùng TV2. Danh sách có evidence trong review TV3.

## 4. Official Training Gate

- [x] P1 verified locally (không phải reviewer accepted).
- [x] Regression tests PASS, bằng chứng lần continuation mới.
- [ ] TV1 frozen manifest available.
- [ ] Manifest hash verified trên bundle official.
- [ ] B1/B2 common parent IDs verified trên bundle official.
- [ ] Protocol approved.
- [ ] Environment/GPU ready (hardware detected không đủ).
- [ ] Config frozen (receipt/hash/git_ref/budget vẫn null).
- [ ] Real data preflight PASS.
- [x] Official run ID `B1_run01` chưa tồn tại lúc audit; kiểm lại ngay trước chạy.

Thiếu bất kỳ gate bắt buộc nào: **KHÔNG TRAIN CHÍNH THỨC**.

## 5. Resume Instructions

Đây là tiếp tục công việc dự án. Pipeline chưa hỗ trợ resume epoch/checkpoint;
nếu run đã tồn tại hoặc lỗi, dùng run ID mới và giữ run cũ.

### Chọn interpreter và kiểm tra repo/môi trường

Từ repository root, chọn interpreter đã được kiểm định. Trên máy hiện tại,
interpreter dưới đây chỉ dùng cho CPU tests/smoke, không dùng official training:

```powershell
$py = 'C:\Users\Huỳnh Phúc\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$env:TEMP = Join-Path (Get-Location) 'outputs/tv2_w3/tmp'
$env:TMP = $env:TEMP
$env:PYTHONPATH = Join-Path (Get-Location) 'outputs/tv2_w3/deps'
$env:MPLBACKEND = 'Agg'
git fetch origin
git branch --show-current
git status --short
git log origin/main --oneline -5
git ls-tree -r --name-only origin/feat/metadata-split -- data/processed/comparison_v1
& $py -X utf8 scripts/check_environment.py
& $py -m pip check
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
& $py -c "import torch,torchvision; print(torch.__version__,torchvision.__version__,torch.version.cuda,torch.cuda.is_available()); print(torch.cuda.get_device_properties(0) if torch.cuda.is_available() else 'CUDA NOT READY')"
& $py -X utf8 scripts/validate_gpu_schedule.py
```

Hiện checker môi trường ghim FAIL; không bỏ kiểm tra hoặc sửa pin để đạt PASS.
Sau khi thống nhất môi trường đích, tạo venv mới bằng interpreter phù hợp,
cài dependencies/CUDA build tương thích đã được kiểm tra và giữ nguyên môi trường
cũ. Không dùng `nvidia-smi` hay validator lịch GPU thay cho GPU model smoke hoặc
approval của chủ tài nguyên. Ghi budget_reference thật; không tự tạo booking confirmed.

### Kiểm dữ liệu và preflight không train

Sau khi TV1 push bundle: lấy các file train/val/provenance từ đúng SHA bằng cách
giữ nguyên byte; không merge nhánh khác, không lấy test manifest. Kiểm
`git show <SHA>:<receipt-path>` và `Get-FileHash -Algorithm SHA256 <receipt-path>`.
Điền receipt path/hash/Git ref vào config chỉ theo evidence thật. Sau đây gọi API
hiện có (không có CLI `--preflight`):

```powershell
@'
import json
from pathlib import Path
from src.training.b1_gate import committed_receipt, validate_config, verify_data
root = Path.cwd()
config = json.loads((root / 'configs/b1.yaml').read_text(encoding='utf-8'))
validate_config(config)
data = config['data']
if not all(data.get(k) for k in ('freeze_receipt','freeze_sha256','freeze_git_ref')):
    raise SystemExit('BLOCKED - TV1 W3-01 OFFICIAL HANDOFF MISSING')
receipt = committed_receipt(root, data['freeze_receipt'], data['freeze_sha256'], data['freeze_git_ref'])
if (receipt.get('task'),receipt.get('owner'),receipt.get('status')) != ('W3-01','TV1','FROZEN') or not receipt.get('dataset_version'):
    raise SystemExit('BLOCKED - INVALID FREEZE EVIDENCE')
_, _, _, proof = verify_data(receipt, root, root / data['image_root'], config['model']['num_classes'])
print(json.dumps(proof, indent=2))
'@ | & $py -X utf8 -
```

Lệnh trên kiểm đầy đủ ảnh train/val, không reserve run. Lưu stdout và exit code
vào **file evidence mới**; không gọi data preflight PASS là approval protocol/GPU.
Sau khi protocol/budget có approval thật, kiểm gate chung:

```powershell
& $py -X utf8 -c "import json; from pathlib import Path; from src.training.b1_gate import official_gate; r=Path.cwd(); official_gate(json.loads((r/'configs/b1.yaml').read_text()),r); print('RECEIPT/PROTOCOL/BUDGET METADATA PASS; GPU/data smoke still required')"
```

### Tests, smoke, train và reload

```powershell
& $py -X utf8 -m unittest discover -s tests -v
& $py -X utf8 scripts/train_b1.py --smoke
& $py -X utf8 scripts/train_b1.py --help
& $py -X utf8 scripts/validate_b1.py --help
# Chỉ sau toàn bộ checklist PASS; $py phải là interpreter CUDA đã kiểm định:
& $py -X utf8 scripts/train_b1.py --config configs/b1.yaml
```

Train tự chạy lại gate, data inspection và synthetic smoke, kiểm code/config đã
commit, từ chối run tồn tại. Cần GPU smoke với dữ liệu thật trước lượt đầy đủ;
CLI hiện không có chế độ GPU smoke riêng. Không tự tạo flag chưa được triển khai.

Sau run thành công, chọn đúng path từ config/run thật:

```powershell
$checkpoint = 'experiments/B1_run01/checkpoints/best_model.pth'
$digest = (Get-FileHash -LiteralPath $checkpoint -Algorithm SHA256).Hash.ToLowerInvariant()
Get-Item -LiteralPath $checkpoint | Select-Object FullName,Length
& $py -X utf8 scripts/validate_b1.py --checkpoint $checkpoint --sha256 $digest
```

`validate_b1.py` đã tạo model mới, kiểm provenance, chạy validation lại, đối
chiếu metrics/predictions/logits trong một process mới. Ghi stdout thành report
mới bên ngoài run bất biến. Giữ `config.yaml`, `data_gate.json`, `status.json`,
`logs/train_log.csv`, `results/val_metrics.json`, `per_class_metrics.csv`,
`confusion_matrix.png`, `learning_curves.png`, `reload_validation.json` của run
thật làm nguồn báo cáo. Cập nhật checkpoint handoff với size/hash/URL tải thật,
kiểm file tải về độc lập. Nếu chưa có nơi upload: `CHECKPOINT UPLOAD PENDING USER ACTION`.

## 6. Important Files

| Nội dung | Path |
|---|---|
| B1 config / model | configs/b1.yaml; src/models/b1.py |
| Training / validation CLI | scripts/train_b1.py; scripts/validate_b1.py |
| Training module / data gate | src/training/b1.py; src/training/b1_gate.py |
| Regression tests | tests/test_b1.py; tests/test_b0_integrity.py |
| W3 report | reports/tv2/TV2_W3.md |
| TV1 / TV3 reviews | reports/tv2/TV2_REVIEW_TV1_W3.md; reports/tv2/TV2_REVIEW_TV3_W3.md |
| Protocol / checkpoint / comparison | reports/tv2/TV2_W3_PROTOCOL.md; reports/tv2/TV2_W3_CHECKPOINT.md; reports/tv2/TV2_W3_COMPARISON.md |
| Fresh evidence | reports/tv2/w3_evidence/continuation_01/ |
| Final continuation report | reports/tv2/TV2_W3_CONTINUATION_REPORT.md |

## 7. What Must Not Be Changed

- B0_run01, checkpoint B0 và W2 metrics.
- Frozen split, class IDs, byte manifest TV1.
- Nhánh main/TV1/TV3/TV4 và lịch sử Git; không force push.
- Test isolation và provenance guards.
- Snapshot local cũ, file nguồn khi copy; không push LOCAL_REVIEW_RESULTS.

## 8. Final Temporary Status

**W3-02 CODE READY – OFFICIAL TRAINING BLOCKED**.

**B1 CHECKPOINT: NOT AVAILABLE – TRAINING BLOCKED**.
**B1/B2 COMPARISON PENDING**. **PENDING TV3 FIX / REVIEW**.
Không có official epoch, metric, checkpoint hay reviewer acceptance để nghiệm thu.
