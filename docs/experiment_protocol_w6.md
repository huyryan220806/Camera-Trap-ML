# TV2 W6 — protocol đánh giá DINOv3

**APPROVED cho R1/R2 — 06/11/2026; RESULT PENDING.** Phê duyệt chỉ cho cấu hình frozen R1/R2 dùng `comparison_v1` và có hiệu lực thực thi sau khi protocol, registry, cấu hình và receipt này được kiểm tra/commit lên `feat/baseline`; không cho phép R3–R6 tự động chạy.
Owner TV2, reviewer TV1; cấu hình/training thuộc TV3, adapter/demo thuộc TV4.
Nguồn kế hoạch: `feat/metadata-split` tại
`11e451071f58146522df20e1890cc6fe6e488eb0`, `docs/plans/TV{1,2,3,4}_W6.md`.
Lịch 04–10/11 chỉ là lịch đề xuất; chưa có hạn nộp mới do giảng viên xác nhận.
Registry máy đọc: `experiments/w6/registry.json`. Approval TV2 và TV3 đã được xác nhận riêng và khóa bằng reference trong biên nhận `reports/tv2/w6_evidence/lock_20261106/W6_R1_R2_LOCK_RECEIPT.json`. TV3 confirmation: commit `a5e24eb27e4bff4d3649adeee3b70efffdc11e2c`; TV2 confirmation: `reports/tv2/TV2_W6_TV2_TECHNICAL_APPROVAL_2026-11-06.md` tại commit `73bc9c2b69f202f123657db4b9dbf128810732f3`. Approval TV2/TV3 không chứng minh chất lượng mô hình hoặc full-run time budget.

## Mục tiêu, đối chứng và giả thuyết

R0 = `DINOv3_LP_run01`, frozen ViT-S/16 CLS384 + Linear(384,8), seed42,
đã được TV2 nghiệm thu độc lập W5. Accuracy **0.845 = 507/600**,
macro-F1 **0.8444008279545706**, checkpoint 86.851.958 byte, SHA-256
`acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3`.
R0 là reference, không phải lượt train mới và không chạy lại trong D1.
Đối chứng phụ B2: accuracy `0.7466666666666667`, macro-F1 `0.7454765175212033`;
checkpoint `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`.

Giả thuyết R1: patch tokens bổ sung thông tin cho CLS. Giả thuyết R2: recipe
fine-tune nhẹ cải thiện đặc trưng. R2 thay optimizer và augmentation cùng lúc,
nên chỉ kết luận về recipe, không quy toàn bộ thay đổi cho hai block cuối.
R5/R6 chỉ thay dataset với cùng recipe/seed để tách hiệu ứng dữ liệu.
Mục tiêu accuracy ≥88% = ≥528/600, tăng ròng ít nhất21 ảnh, đồng thời tăng
macro-F1 so R0. Đây là mục tiêu, chưa phải kết quả hay lý do sửa phép đo.

## Dữ liệu, geometry và tiền xử lý

R1–R4 dùng `comparison_v1`: train2800 ảnh/3125 GT crop; val600 ảnh/680 crop,
75 ảnh/lớp. Provenance SHA
`d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`.
File hashes nằm trong provenance và `reports/tv2/W5_PROTOCOL.md`; validator
W6 gọi loader Train/Val W5 kiểm hash độc lập, không đọc Test manifest.
Không thay split/nhãn/ảnh, không lọc confidence hoặc ảnh khó.

Class IDs giữ nguyên: 0 large_antlered_muntjac, 1 annamite_striped_rabbit,
2 sambar, 3 chinese_serow, 4 common_palm_civet, 5 masked_palm_civet,
6 silver_pheasant, 7 eurasian_wild_pig.
GT bbox integer XYXY, phải/dưới exclusive, round-half-even rồi clip theo TV1,
padding0, cạnh tối thiểu8px, giữ mọi box hợp lệ. Không reround box đã khóa.
Loss = mean CE các crop trong mỗi parent rồi mean trên parent trong update;
không nhân `1/N` hai lần. Batch cuối dùng số parent thực tế, không drop_last.

DINOv3: convert RGB, không EXIF transpose; crop GT → ToImage uint8 → resize
vuông **256×256 bilinear antialias=True trên uint8** → float32 scale=True →
ImageNet mean[.485,.456,.406], std[.229,.224,.225]. Validation không random.
B2 dùng Resize cạnh ngắn256 → CenterCrop224; không dùng transform B2 cho DINO.
Vendor pin `6876159a11b4df116f30f667f8c9888617df0751`, pretrained SHA
`08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d`.

## Đăng ký recipe và điều kiện

| Run | Recipe / seed / dữ liệu | Điều kiện |
| --- | --- | --- |
| R0 | W5 frozen CLS384 /42/comparison_v1 | reference, không train |
| R1 | CLS384 + mean patch384, head768→8 /42/cũ | smoke + freeze + review |
| R2 | 2 block cuối + final norm + head, CLS384 /42/cũ | smoke + freeze + review |
| R3 | recipe thắng R1/R2 /43/cũ | vượt R0 và còn budget |
| R4 | cùng recipe R3 /44/cũ | vượt R0 và còn budget |
| R5 | recipe chọn hoặc R0 fallback /42/mở rộng | TV2 data PASS và budget |
| R6 | như R5 /43/mở rộng | TV2 data PASS và budget |

R1 backbone frozen/eval; concatenate `x_norm_clstoken` với mean riêng
`x_norm_patchtokens`, không storage/register tokens. Head mới 768→8;
backbone lấy W5, head384 cũ không thể nạp vào head768. Giữ SGD W5 lr.01,
momentum.9, WD.0001, nesterovFalse/dampening0, cosine50 eta_min0 sau validation,
max50epoch, patience7,32parent/update, không augmentation. Cache768 riêng:
identity phải có pooling/dimension, source/vendor/weights, preprocessing,
data/image/crop order và runtime; không tái dùng cache384.

R2 nạp backbone và head W5. Chỉ train hai block cuối, final norm, head384→8;
AdamW backbone1e-5/head1e-4, WD.01, không decay bias/norm; max20epoch,
patience5, warmup2epoch rồi cosine. Horizontal flip train p=.5, không vertical
flip hoặc random crop. Effective batch16parent, microbatch≤8crop. FP32,
AMP/TF32false, không feature cache khi backbone trainable. Lưu full backbone
và head. RNG/sampler/optimizer/scheduler/epoch/best/patience phải được resume
đúng, không đặt lại early stopping. Cách nội suy warmup, AdamW betas/eps,
train/eval mode chi tiết và runtime pin phải được TV3 khai báo và TV2 review
trước freeze; không tự đoán tham số còn thiếu trong kế hoạch.

Các config `configs/w6/R1.draft.json`, `R2.draft.json` chỉ giữ lại như đề xuất D1;
config chính thức R1/R2 đã khóa và đăng ký là `configs/w6/tv3/R1.frozen.json`,
`configs/w6/tv3/R2.frozen.json`, copy nguyên byte từ handoff TV3 `8cd97538390a3f55c66193d79e637dfd73ace770`.
Source đã review `127cac5b64d37fdda630a2f84b006a8e420dc9ed`; runtime lock
`7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a`.
Config canonical SHA R1 `2ab03b7e13d798b8aace5e4b3542a189389c43c7630f4132303b9200fced63bf`,
R2 `55dea8ab328e43581642deb964631d391a5b88596feb191a5fa5911a7a94acb7`.
TV2 D2 pretraining review: `reports/tv2/TV2_W6_TV3_PRETRAIN_REVIEW_2026-11-06.md`
(`READY_FOR_TV2_DECISION`), tiếp theo là quyết định TV2 và TV3 được ghi ở receipt.
Smoke raw SHA R1 `9d5418745cf2cd45519415935246cb3be6ee6b5f0349341b9accb821b2cca1f6`,
R2 `6b7ead35a2bfbfb002154db14d992c2fd3ececfe3bf3c546be6bdb62433279e5`.
Không suy từ smoke ngắn rằng official run sẽ kết thúc trong 2 GPU-giờ.

## Freeze, train-only smoke và budget

TV3 chạy smoke trên train riêng, run ID mới và thư mục mới; không dùng val để
thử cấu hình. Checklist cần artifact có SHA, command/exit code/runtime:

- GPU/VRAM, OOM và số parent/crop thực tế; microbatch đã chọn trước official.
- Danh sách named parameters/frozen mask; gradients hữu hạn và chỉ ở tầng cho phép;
  frozen params không đổi sau step; kiểm model train/eval và norm.
- R1 head768, không register tokens; cache invalidation khi đổi bất kỳ identity.
- R2 mean loss parent, accumulation qua ranh giới crop/parent; parent nhiều crop
  và batch cuối không đủ16 vẫn dùng đúng mẫu số; không double weighting.
- Best/last save/load strict, resume optimizer/scheduler/RNG/sampler/patience,
  không ghi đè W5; interrupted attempt giữ log và thời gian.
- Khóa config canonical SHA, source commit + file SHA, input manifests,
  pretrained/init checkpoint, preprocessing/runtime/version/device/threads SHA.

DRAFT→APPROVED chỉ sau smoke đạt, config được đối chiếu và review thật TV2/TV3
có evidence. Freeze phải được commit trước khi xem **official validation metrics**;
không ghi người khác đã duyệt. Các trường null là thiếu bằng chứng.
Config SHA W6 = SHA256 của UTF-8 JSON sort_keys=True, separators=(',',':'),
ensure_ascii=False, allow_nan=False, không newline. Khác serialized digest W5;
package phải ghi cả SHA raw file khi bàn giao, không nhầm hai loại hash.

Tối đa6 official attempts mới gồm FAILED/OOM/STOPPED; TV3≤12GPU-giờ tổng
gồm extraction, mỗi attempt≤2giờ; TV2≤2GPU-giờ replay. R0 không tính lượt mới.
Smoke ghi thời gian riêng; mọi GPU smoke/extraction TV3 cũng tính vào trần12h.
Trần không phải booking; cần chốt GPU/time thực. Nếu usage chưa đo hoặc chưa
có booking thì không mở lượt mới. Resume cùng attempt chỉ khi binding toàn bộ
giữ nguyên; khởi động lại từ đầu hoặc đổi recipe là attempt mới và tốn budget.
Không xóa run lỗi hoặc chạy lén để chọn kết quả đẹp. Thay config sau FAIL phải
review lại trước lượt mới, không nới tolerance. Mọi artifact mới write-once;
revision registry giữ lịch sử bằng Git, attempts không được xóa.

## Metric, chọn recipe và demo

Đơn vị metric **ảnh nguồn**. Softmax8 từng GT crop → mean vector đủ tất cả
crop cùng image_id → argmax một lần; tie class ID nhỏ nhất. Không mean logits,
majority vote, confidence cutoff hay trọng số theo số crop cho metric ảnh.
Checkpoint chọn image-level macro-F1 cao nhất; hòa giữ epoch sớm hơn.
Accuracy, macro-P/R/F1 (đủ8 lớp, zero_division0), từng lớp P/R/F1/support,
CM8×8 hàng thật/cột đoán, paired ID outcomes với R0 phải được báo đầy đủ.
Saved image scores phải khớp mean crop scores atol1e-10, probability sum
atol1e-5, metric arithmetic atol1e-10, không làm tròn trước quyết định.

Chọn R1/R2 **seed42** theo macro-F1 → accuracy → chi phí inference thấp hơn
trên cùng benchmark → run ID đăng ký trước. Nếu hòa metric mà thiếu benchmark
so sánh được: PENDING, không đoán chi phí từ tên model. Recipe vượt R0 khi
macro-F1 > R0; demo còn yêu cầu accuracy≥R0. R3/R4 chỉ khi vượt R0 và còn budget;
nếu không, R5/R6 có thể fallback R0 sau quyết định có evidence.
Seed43/44 báo riêng, mean và sample SD (ddof1); một seed SD=null, không lấy seed
tốt nhất thay headline. Không gộp khác recipe/dataset. R0 chỉ một seed nên không
có so sánh đa seed cân xứng. CI nếu làm phải paired cluster bootstrap cùng cụm
location, fixed seed; hiện **NOT RUN**, không dùng bootstrap IID ảnh làm CI độc lập.

Rà common↔masked civet (R0:13 nhầm hai chiều), muntjac↔sambar (12), mọi lớp
mất≥4/75 ảnh đúng (recall giảm≥.0533333). R0 masked56/75, muntjac54/75.
Regression cần lý do chấp nhận bằng review cụ thể; chưa review thì không đề nghị
đổi demo. Demo gate: macro-F1 tăng, accuracy không giảm, package/source/replay/
adapter đạt, per-class regression được review. +1điểm%F1 là mục tiêu thực dụng,
không phải ngưỡng thống kê đã chứng minh. TV2 chỉ đề nghị; TV4 mới tích hợp.
Giữ B2 mặc định, DINO W5 opt-in nếu W6 chưa đủ gate.

## Release mở rộng và replay

TV1 release `train_expansion_w6_v1`, provenance
`a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`:
1665ứng viên =1446giữ+219cách ly; tổng4246train/4729crop. `quality_ready=true`
khác TV2 acceptance. R5/R6 vẫn **BLOCKED** đến khi peer review PASS có SHA:
counts/class map/source membership/geometry/weights/manifest hashes;
5 exact RGB +191 suspected near +23 ambiguous được cách ly đúng; không leakage
ID/path/sequence/location/bytes/RGB, val/Test snapshot giữ nguyên theo hash.
Kiểm bytes/RGB/decode ảnh thật trong phạm vi được phép; thiếu ảnh cách ly,
holdout hoặc bằng chứng thị giác phải ghi PENDING. Không chạy model hoặc mở
raster Test. Kiểm Test chỉ Git blob/hash metadata, không dùng kết quả W4 chọn W6.
Không sửa snapshot TV1 hoặc gán approval vào artifact của họ.

TV3 bàn giao checkpoint thật, classmap, raw/canonical config hash, source index,
vendor pin, data hashes, runtime lock, log tất cả epoch/attempt/GPU hours,
crop/image vectors đủ680/600, best/last và fresh-process reload. TV2 validator
hash/artifact-only không phải full model replay; authorship approval phải kiểm
Git/receipt riêng, không tin một chuỗi PASS là chữ ký.

Replay checkpoint trong process mới, pin cùng runtime TV3 đã freeze; eval(),
inference_mode(), FP32, không cache, đủ600val/680crop, không train/Test. Chính sách
mặc định **exact equality** logits/scores/predictions/metrics trên runtime đã pin
(như W5). Cross-device tolerance hiện **CHƯA ĐĂNG KÝ**, không dùng cross-device
để nhận PASS; muốn dùng phải review/commit policy trước replay, không nới sau FAIL.
TV4 native/adapter kiểm logits/per-box vector theo cùng policy. Ghi model replay,
producer reload, artifact audit và adapter verification thành các kết luận riêng.

## Bảo toàn và giới hạn

Cấm dùng Official Test W4 để phát triển/chọn/tuning/threshold/so W6; không chạy
lại R0 hoặc Official Test. W1–W5 data/protocol/checkpoint/log/predictions/selection
lock giữ nguyên. B3 W4 vẫn UNRESOLVED. Trạng thái W5 mới nhất lấy từ
`docs/integration_week5.md` (đã tích hợp), không dùng PENDING lịch sử thay nó.
Validation được tái dùng để chọn model; một seed R0; GT-box classification không
phải detector end-to-end; mẫu cân bằng75/lớp không đại diện tần suất tự nhiên.
Score chưa calibrated, không chứng minh loài lạ/SOTA/khái quát địa điểm mới.
Chưa đạt88% vẫn có thể hoàn thành W6 đúng quy trình; báo cả thất bại và giới hạn.

## Freeze receipt W6 R1/R2 — 06/11/2026

- Hai thành viên TV2, TV3 xác nhận theo đúng file/commit ghi trong `reports/tv2/w6_evidence/lock_20261106/W6_R1_R2_LOCK_RECEIPT.json`.
- `freeze_evidence`: `reports/tv2/w6_evidence/lock_20261106/W6_R1_R2_LOCK_RECEIPT.json`.
- `smoke_evidence`: `reports/tv2/w6_evidence/lock_20261106/SMOKE_BINDINGS.json`, ghi nguồn smoke và raw SHA tại handoff TV3.
- R1/R2: `REGISTERED`, seed42, chưa chạy official; registry `APPROVED` không có nghĩa đã có checkpoint/accuracy W6.
- R3/R4 CONDITIONAL (chờ recipe thắng R0); R5/R6 CONDITIONAL và bị chặn bởi review dữ liệu TV1 PENDING.
- TV3 chỉ bắt đầu official khi Git commit chứa protocol/registry/config đã được push và kiểm lại runtime, usage, không mở W4 Test.


## R3/R4 approval addendum — 2026-11-07

TV2 approved R3/R4 individually for recipe R2 seed43/44, under `reports/tv2/w6_evidence/lock_20261107/W6_R3_R4_LOCK_RECEIPT.json`, after TV3 approval at `6cbe8522b873dcbb2c5783baa3364f449cc62da6`. Use `experiments/w6/tv3_R3_R4.approved.json` as the TV3 **execution registry** (includes completed R1/R2 official attempts); `experiments/w6/registry.json` remains the protocol snapshot and is NOT the execution ledger. Each run is REGISTERED, with no R3/R4 official attempt at lock. R5/R6 and Official Test W4 remain blocked.


## R5/R6 bilateral lock addendum — 2026-11-08

TV2 và TV3 đã hoàn thành bilateral protocol lock cho R5/R6 theo biên nhận `reports/tv2/w6_evidence/lock_20261108/W6_R5_R6_LOCK_RECEIPT.json`, dựa trên phê duyệt kỹ thuật của TV2 (`reports/tv2/TV2_W6_R5_R6_TECHNICAL_APPROVAL_2026-11-08.md`) và TV3 (`reports/tv3/w6/approvals/TV3_R5_R6.json`). Dataset khóa chặt tại `train_expansion_w6_v1` (`a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`), source commit `947fbb85aacec9417f248f5f1e1f08c2da75de09`, runtime lock `7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a`. Cả R5 và R6 đều áp dụng recipe R2 (seed 42 và 43), giới hạn 2,0 GPU-giờ/attempt.


## Protocol amendment: R6 3-Hour Allowance (2026-11-09)

### 1. Bối cảnh và Phạm vi Điều chỉnh
- Sự cố R5 (`R5_attempt01`) gặp lỗi I/O `WinError 5` trên Windows NTFS khi atomic replace file `usage.json` tại epoch 14 (1.779 GPU-giờ, 6.405,3 s). Biên nhận đối soát kế toán song phương TV2/TV3 (`W6_R5_ATTEMPT01_ACCOUNTING_RECONCILIATION`) đã xác nhận PID 32064 dừng hẳn, kết toán toàn bộ 6.405,3 s, giữ trạng thái `FAILED`, bảo toàn checkpoint epoch 14 và đồng thuận không resume R5.
- TV3 đề xuất điều chỉnh giới hạn thời gian cho lần chạy chính thức duy nhất còn lại `R6_attempt01` từ 2,0 GPU-giờ lên tối đa 3,0 GPU-giờ (10.800 s) nhằm đảm bảo hoàn thành đủ 20 epochs trên tập mở rộng mà không bị ngắt quãng bởi budget timeout.
- TV3 đã triển khai bản vá retry giới hạn (5 lần thử, backoff tối đa 1,55 s, chỉ áp dụng cho `winerror == 5`) tại `write_usage()` trong `src/training/dino_w6_control.py`, đã được kiểm chứng độc lập bởi 18/18 unit tests.

### 2. Các Ràng buộc Bất biến (Strict Protocol Invariants)
1. **Phạm vi đặc cách duy nhất**: Chỉ `R6_attempt01` (run `R6`, seed 43, recipe `R2`) được áp dụng mức trần tối đa 3,0 GPU-giờ.
2. **Bảo toàn lịch sử R1–R5**: Toàn bộ các attempt lịch sử và bất kỳ attempt nào khác ngoài `R6_attempt01` vẫn duy trì giới hạn nghiêm ngặt 2,0 GPU-giờ/attempt.
3. **Trần ngân sách tổng TV3**: Tổng ngân sách GPU của TV3 trong W6 giữ nguyên mức trần tuyệt đối **12,0 GPU-giờ** (43.200 s). Với lũy kế đã kết toán hiện tại là 4,064 GPU-giờ (gồm 5 official attempts và các smoke/reload sessions), việc chạy tối đa 3,0 GPU-giờ cho R6 đưa tổng GPU lên tối đa ~7,064 GPU-giờ, hoàn toàn nằm trong ngân sách và còn dư ~4,936 GPU-giờ.
4. **Giới hạn số lượt chạy chính thức**: Trần số lượt chạy chính thức (official attempts) giữ nguyên tối đa **6 lượt**. Với 5 lượt đã dùng (R1_attempt01, R2_attempt01, R3_attempt01, R4_attempt01, R5_attempt01), `R6_attempt01` là lượt chạy chính thức thứ 6 và là lượt cuối cùng của dự án.
5. **Ngân sách TV2 replay**: Trần GPU của TV2 độc lập replay giữ nguyên **2,0 GPU-giờ**.
6. **Bảo toàn dữ liệu**: Dữ liệu huấn luyện khóa chặt tại `train_expansion_w6_v1` với release SHA-256 `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`.
7. **Niêm phong Official Test W4**: Tuyệt đối không mở raster ảnh, không suy luận trên tập Test W4.
8. **Runtime & Code Binding**:
   - `source_sha`: `3b4b106c01e64901f213f6eebfdd10ffa55a7eb7` (commit chứa bản vá WinError 5 retry và candidate config).
   - `runtime_lock`: `7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a`.
   - `config_sha256` (canonical): `08a01874ccc2cf0f21e652ed082893bfc666e4489c01e7b5cb36404bebe67a70`.
   - `smoke_evidence`: `reports/tv3/w6/smoke/R6_3h_smoke01.json` (SHA-256 `4ef74db223ac7ab45e88cd11de78e878c9c0253c2e2a0a95b473b6a25bae287d`).

### 3. Cơ chế Phê duyệt Song phương & Trạng thái Khóa
- Amendment chỉ có hiệu lực thi hành chính thức khi cả TV2 và TV3 đều đã ký receipt phê duyệt độc lập (`decision: APPROVE_R6_3H`) khớp chính xác binding đã khóa.
- Trạng thái amendment trong registry bắt đầu ở `PENDING`. Khi ở trạng thái `PENDING`, mọi lệnh thực thi training chính thức hoặc cấp phát execution registry đều bị chặn (`BLOCKED`).
- TV2 chuẩn bị và cam kết biên nhận phê duyệt kỹ thuật tại `reports/tv2/w6_evidence/r6_3h_approval/TV2_R6_3H_APPROVAL.json`. Sau khi TV3 đối ứng ký biên nhận, hai bên sẽ tiến hành bilateral protocol lock chính thức trước khi chạy R6.


## R6 3-Hour Bilateral Protocol Lock Confirmation — 2026-11-09

Bilateral protocol lock cho R6 3-Hour Amendment đã hoàn tất thành công sau khi cả hai thành viên TV2 và TV3 đã ký biên nhận phê duyệt kỹ thuật độc lập:
- **Biên nhận phê duyệt TV2 (Revision 2):**
  - Path: `reports/tv2/w6_evidence/r6_3h_approval/TV2_R6_3H_APPROVAL.json`
  - Commit: `58205a33983d302856a7fec5b31abffb4c259422`
  - SHA-256: `9dd51e74da0fd9219d73937826bf00a1c4b97d43d5259b56ced0cbf8697c84e8`
  - Quyết định: `APPROVE_R6_3H`
- **Biên nhận phê duyệt TV3:**
  - Path: `reports/tv3/w6/approvals/TV3_R6_3H_APPROVAL.json`
  - Commit: `c43d1b2b629235b9e965a6b7d957d915cc4babea`
  - SHA-256: `7c545287161b32e609098a893be58d1441fd1eb76a7c8c36616dbf8df0932a74`
  - Quyết định: `APPROVE_R6_3H`
- **Biên nhận khóa song phương (Bilateral Lock Receipt):**
  - Path: `reports/tv2/w6_evidence/lock_20261109/W6_R6_3H_LOCK_RECEIPT.json`
  - SHA-256: `0eeaa94a9d936f601daab2516915de58575b332f4a31eed9cf31357f92606231`
- **Execution Registry chính thức:** `experiments/w6/tv3_R6_3h.approved.json`
  - `r6_budget_amendment.status = "APPROVED"`
  - `runs[6].status = "REGISTERED"`
  - `runs[6].attempts = []`
  - `freeze_evidence = "reports/tv2/w6_evidence/lock_20261109/W6_R6_3H_LOCK_RECEIPT.json"`
  - `smoke_evidence = "reports/tv3/w6/smoke/R6_3h_smoke01.json"`
- **Ràng buộc:** Chỉ `R6_attempt01` tối đa 3,0 GPU-giờ; R1–R5 tối đa 2,0 GPU-giờ; tổng TV3 tối đa 12,0 GPU-giờ (lũy kế hiện tại 4,064 GPU-giờ, còn dư 7,936 GPU-giờ); 5/6 official attempts đã sử dụng; R5 giữ FAILED (reconciliation 6405.3003492 s); Official Test W4 SEALED.
