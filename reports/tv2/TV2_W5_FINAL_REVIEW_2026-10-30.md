# TV2 W5 — final review B1–B3 và khóa protocol, 30/10/2026

**B1 PASS, B2 PASS, B3 PASS. Protocol APPROVED; đăng ký chính thức duy nhất
`DINOv3_LP_run01`. W5 vẫn PARTIAL, chưa có kết quả/checkpoint DINO.**
TV3 được triển khai lượt đã đăng ký sau khi áp dụng đúng receipt TV2 trên nhánh
của mình và kiểm gate/assets tại môi trường chạy. TV2 không chạy training.

## Nguồn, phạm vi và thẩm quyền

- TV2 base: `9f528d241c607be81853a2669d189bd1dd9c4237`, chỉ sửa `feat/baseline`.
- TV3 fetched HEAD: `14d79fd18e2a22bc853cc89559ec9bbb708403da` trên
  `origin/feat/crop-classifier`.
- Source/evidence commit: `173db631cf74611aca5f95044fe572ab08e81d26`, là ancestor
  của HEAD. Commit HEAD chỉ thêm `publication.json`; source không đổi.
- Bundle: `reports/tv3/w5_review_response_2026-10-30/`. Đọc toàn bộ bundle và
  source pipeline/CLI/handoff/verifier/tests tại commit cố định trong snapshot
  riêng ở `outputs/tv2_w5/final_review_20261030_01/tv3_snapshot/`; không checkout,
  merge hoặc sửa nhánh TV3. Kiểm lại 38/38 artifact: SHA, bytes, Git blob ID,
  và nội dung giống source commit.
- TV2 đã đồng ý kỹ thuật có điều kiện trong chat. Yêu cầu mới của chính người
  dùng TV2 cho phép phê duyệt sau khi kiểm đủ B1–B3; bản gốc yêu cầu lưu tại
  [tv2_review_authorization.txt](w5_final_review/2026-10-30/attempt_01/tv2_review_authorization.txt).
  Không yêu cầu TV2 xác nhận lại cùng hyperparameter sau khi điều kiện đã đạt.

Receipt ghi nguồn quyết định thực tế, không tạo chữ ký hoặc tên reviewer giả.
TV3 là lời xác nhận được quy thuộc trong receipt Git, **không phải xác thực
danh tính bằng mật mã**. TV1 reviewer vẫn null; không phát sinh approval TV1.

## B1 — PASS: hai SHA đúng với hai đầu vào khác nhau

| Đối tượng tự tính lại từ Git | SHA-256 |
| --- | --- |
| Config chuẩn `configs/dinov3_lp_w5.local.json`, 1063 bytes | `e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce` |
| JSON tuần tự hóa, 897 bytes | `32071801dc6eb6408310e6393f73acda9bd9902303236836e4bf8d8a4cb6d6e8` |
| Smoke lịch sử, 3189 bytes | `52c635be70f6f4a5466a7a816d9fc425036924f350ed9b6ea0a7a99e94549043` |
| Source `src/training/dino_probe.py` | `8529891d6cd213f4cc186de104b31d58d539782e2003fa6c475eb4000cdcb988` |

Source thật dùng:

```python
hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False,
                         allow_nan=False).encode('utf-8')).hexdigest()
```

Dấu phân cách mặc định có khoảng trắng `, ` và `: `, không indent/newline cuối.
TV2 tự tính lại và đối chiếu byte với `config.digest-input.txt`; config nhúng
smoke bằng toàn bộ config chuẩn. Source SHA cũng đúng smoke. Đây là nguyên
nhân hash khác nhau, đã được kiểm chứng; không sửa smoke hoặc đổi config.

Preflight 28/10 có digest template `2c510c31091a741a13803726fd38ab51529b8ce9e39d5641a97604485a341c38`.
So sánh toàn bộ object chỉ khác ba trường `model.repo_commit`,
`model.weights_sha256`, `model.weights_source` được pin sau đó. Mọi training,
runtime, cache, data và preprocessing giữ nguyên. Metadata train/val và
provenance cùng hash; không có thay hyperparameter hoặc release ngầm.

## B2 — PASS: TV3 xác nhận đúng config và ngân sách

`TV3_APPROVAL.json` tại HEAD đã công bố ghi đúng raw SHA, serialized SHA,
experiment `DINOv3_LP_run01`, tối đa một official training run và chỉ bắt đầu
sau TV2 khóa APPROVED. SHA receipt:
`4a9de9f794b3619cdc95a63d9d706f3aa53d79d6ee39475497e912aa8208cfdf`.
Receipt lưu nguyên lời người dùng TV3 xác nhận gửi B2 và cho phép commit/push;
nguồn phát biểu/giới hạn xác thực được ghi rõ. Trạng thái TV3 pending TV2 trong
receipt cũ là đúng thời điểm phát hành, không bị viết lại thành approval TV2.

Điều kiện đồng ý của TV2 về hash, dữ liệu và quy trình đã được kiểm ở B1/B3.
Phê duyệt cuối này thực hiện đúng ủy quyền mới của người dùng TV2; không coi
GPU smoke hoặc unit fixture là lời phê duyệt của con người.

## B3 — PASS: source, data, pretrained và giới hạn

| Điều kiện | Kiểm chứng |
| --- | --- |
| Backbone/head | `load_backbone`: factory DINOv3 ViT-S/16, `strict=True`, `requires_grad_(False).eval()`; `extract`: CLS384; head Linear(384,8,bias=True) |
| Nguồn/pin | LVD-1689M ViT-S/16; upstream `6876159a11b4df116f30f667f8c9888617df0751`; SHA weights `08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d`, 86.531.063 bytes; code kiểm commit/clean checkout, import path và full SHA |
| Preprocessing | RGB, không EXIF transpose; crop integer XYXY khóa, right/bottom exclusive, padding0; ToImage uint8 → Resize 256×256 bilinear antialias → float32 scale=True → normalize mean [.485,.456,.406], std [.229,.224,.225]; không random augmentation |
| Dữ liệu | comparison_v1; train2800 parents/3125 crops, val600 parents/680 crops; kiểm 7 metadata hash + provenance; read_release chỉ train/val; 1665 ứng viên mở rộng không được dùng |
| Loss/grouping | `groups_for` gom đủ crop theo image_id; mean CE crops từng parent rồi mean parents. Không nhân sample_weight lần hai; không drop batch cuối |
| Batch/cache | Mỗi update32 parents; batch cuối16. Cache extraction32 crops/shard128 là bước riêng; frozen backbone, head học feature cache, không gradient accumulation |
| Optimizer | SGD lr.01, momentum.9, WD.0001; defaults source nesterov=False, dampening0 |
| Scheduler | CosineAnnealingLR T_max50, eta_min0; optimizer updates → validation/best/early-stop → scheduler.step mỗi epoch hoàn tất |
| Budget/stopping | Seed42, tối đa50epochs, patience7; `score > best` mới thay best, nên hòa giữ epoch trước; chỉ một candidate run |
| Metric/aggregation | Softmax từng crop → mean vector theo parent → argmax; class order0–7, argmax hòa chọn ID nhỏ nhất; macro-F1 ảnh gồm đủ8 lớp, zero_division0 |
| Runtime | FP32; AMP/TF32false, deterministic mode; CUDA unavailable thì chặn; không tự đổi model/device/config |
| Gate/handoff | CLI check protocol trước cache/train; raw config/serialized digest được ràng buộc; binding lưu actual code commit/source/CLI/handoff hashes/runtime/receipt; export đủ crop/ảnh và fresh-process reload độc lập |

**Phân biệt nguồn bằng chứng:**

- TV2 tự kiểm: 38 Git artifacts, raw/serialized hash, source/hyperparameter/
  grouping/transform/scheduler/tie logic; metadata hiện tại; byte SHA32 ảnh
  train đúng recipe smoke; verifier chạy lại không local-assets; software tests
  và validator chạy trên receipt thật. Không decode ảnh Test.
- TV3 báo cáo: rehash weights đầy đủ/checkout sạch ngày30; GPU smoke ngày29
  trên RTX4060Laptop8GB, FP32, output32×384, frozen. Preflight ngày28 kiểm đủ3400
  ảnh train/val byte/RGB/dimensions. TV2 đối chiếu các receipt đã công bố với
  config/source/data hiện tại; không diễn giải chúng thành phép chạy mới TV2.
- Weights/vendor không có trên máy TV2: **không tự rehash binary, strict-load
  hoặc replay GPU smoke**. Strict loading có bằng chứng smoke thành công gắn
  source đúng SHA chứa strict=True; không có log missing/unexpected keys riêng.
  Danh sách32 crop smoke dựng lại từ recipe/manifest frozen, không phải log
  sample ghi đồng thời ngày29. Counter verified_source_images=0 của smoke là
  do read_release(verify_images=False); crop_tensor vẫn kiểm byte SHA từng ảnh.
  Hôm nay TV2 kiểm byte32 mẫu, không gọi là full RGB/pixel recheck3400 mới.

Giới hạn trên phù hợp quy trình review nguồn/receipt được yêu cầu: không có
điều kiện bắt TV2 sở hữu lại binary/GPU. Receipt và source được công bố đầy
đủ, các đối chiếu độc lập đều PASS, nên B3 được đóng. Smoke peak299.583.488bytes
không chứng minh peak/toàn thời gian official run hoặc availability hiện tại.
TV3 phải gate-check CUDA/assets và giữ source/config khóa trước khi chạy.

## Kiểm thử TV2 tự chạy

| Kiểm tra | Kết quả |
| --- | --- |
| Verifier TV3 trên snapshot đúng Git, không `--local-assets` | PASS |
| `test_dino_w5.py` | 11/11 PASS |
| `test_dino_tv2_compat.py` | 5/5 PASS, không skip |
| TV2 `test_w5_validation.py` | 32/32 PASS |
| Environment / result contracts | PASS / 6 fixtures PASS |
| Receipt APPROVED thật qua `validate_config` + `validate_protocol` TV3 | PASS |
| 7 mutation sai status/hash/registration/budget/reviewer/seed/split | REJECTED đúng gate |
| Receipt hợp lệ nhưng chưa có candidate artifact | TV2 từ chối candidate thiếu registration/fields; không mở checkpoint |

Tổng48 software tests PASS/0FAIL/0SKIP. Unit tests dùng fake backbone/features
và head tổng hợp trong thư mục tạm; không official DINO training, real DINO
inference hoặc Test W4. Không thay code/tests production. Log/command/runtime:
[checks.json](w5_final_review/2026-10-30/attempt_01/checks.json).
Gate kiểm cấu trúc/registration/digest; không tự xác thực reviewer identity,
không thay thế review source và provenance vừa thực hiện.

## Receipt khóa và bàn giao

- Canonical config: `configs/dinov3_lp_w5.local.json`, giữ nguyên byte TV3.
- Receipt: **`configs/dinov3_lp_w5.local.protocol.json`**, SHA-256
  `e47b96f5e576c234e2e48143c7c008df79ca62156cebf6b2bf65c0119a6f133a`.
- `configs/tv2_w5_protocol.draft.json` giữ tên đường dẫn tương thích cũ nhưng
  nội dung APPROVED, byte-identical receipt. Chỉ model DINOv3; fallback bị khóa
  tắt cho registration này. TV1=null. Không tạo thêm seed/experiment.
- DRAFT cũ được bảo toàn nguyên byte trong `previous_protocol.draft.json` và
  `previous_W5_PROTOCOL.md` tại evidence mới; mọi receipt/evidence cũ giữ nguyên.
- Commit mới chứa receipt được cung cấp sau commit/push. Trong file dùng
  `git log -1 -- configs/dinov3_lp_w5.local.protocol.json` để truy commit thực,
  tránh tự tạo SHA commit đang chứa chính nó. TV2 base/TV3 commit đều ghi đủ.

TV3 lấy receipt từ **commit TV2 mới được báo trong bàn giao**, áp dụng đúng byte
vào nhánh của mình; kiểm SHA raw config/receipt và digest, recheck assets/source
đúng lock, gọi validator rồi mới official run. Không lấy proposal DRAFT cũ hoặc
thay tên reviewer thủ công. Bất kỳ thay đổi source/model/config cần review lại;
không tự giảm batch/đổi CPU/lượt thứ hai khi gặp lỗi/OOM. Resume phải giữ binding.
Chi tiết lệnh trong [handoff](../../docs/handoff_tv2_w5.md).

## Sau khi TV3 trả checkpoint

TV2 kiểm checkpoint SHA/bytes/binding, config/log/epoch tốt nhất/class order/
preprocessing/data hashes và run budget; xác minh đủ600 parent/680 crop val.
Chạy auditor trên dự đoán đã lưu rồi fresh-process model/adapter reload trên
validation theo code thật, tính lại macro-F1/accuracy/P/R/F1/support/CM, đối chiếu
B2 cùng release và rà lỗi. Không dùng Test W4 để chọn hoặc mở W6. Chỉ cân nhắc
bàn giao DINO cho demo sau validation/reload/review; B2 giữ làm fallback demo.
Finding UI-A11Y-01 P2 vẫn chờ TV4 sửa/retest, tách khỏi B1–B3 đã đóng.

W5 **PARTIAL — APPROVAL PASS, DINO RESULT PENDING**. Chưa có metric DINO,
không tuyên bố W5 COMPLETE, không merge PR hay đổi checkpoint/dataset.
