# TV2 W5 validation protocol

**APPROVED — 30/10/2026. B1/B2/B3 PASS; đăng ký chính thức duy nhất
`DINOv3_LP_run01`. W5 PARTIAL, chưa có kết quả DINO.**

Quyết định thực hiện theo đồng ý có điều kiện của người dùng TV2 trong chat và
ủy quyền mới: khóa sau khi độc lập kiểm đủ B1–B3. TV3 đã xác nhận đúng config
qua receipt Git. Không tạo chữ ký hoặc xác thực danh tính bằng mật mã; TV1
reviewer=null. Xem [final review](TV2_W5_FINAL_REVIEW_2026-10-30.md),
[handoff](../../docs/handoff_tv2_w5.md) và [progress](../../docs/progress_tv2_w5_w6.md).

## Nguồn khóa và receipt

TV2 base `9f528d241c607be81853a2669d189bd1dd9c4237`, chỉ nhánh `feat/baseline`.
TV3 HEAD `14d79fd18e2a22bc853cc89559ec9bbb708403da`, source commit
`173db631cf74611aca5f95044fe572ab08e81d26` trên `feat/crop-classifier`.
Bundle `reports/tv3/w5_review_response_2026-10-30/`; TV2 tự kiểm38/38 artifact
SHA/bytes/Git blob, source và receipt. Không merge source TV3 vào TV2.

- Config chuẩn: `configs/dinov3_lp_w5.local.json`,1063 bytes, raw SHA-256
  `e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce`.
- `config_sha256` của validator/smoke là **serialized digest**, SHA-256
  `32071801dc6eb6408310e6393f73acda9bd9902303236836e4bf8d8a4cb6d6e8`:
  `json.dumps(config, sort_keys=True, ensure_ascii=False, allow_nan=False)`
  encode UTF-8, dấu phân cách mặc định có khoảng trắng, không newline cuối.
  Hai SHA đã tái tạo, cùng config values; không phải lỗi CRLF/LF. Smoke cũ giữ nguyên.
- Receipt khóa: `configs/dinov3_lp_w5.local.protocol.json`, SHA-256
  `e47b96f5e576c234e2e48143c7c008df79ca62156cebf6b2bf65c0119a6f133a`.
- `configs/tv2_w5_protocol.draft.json` giữ tên cũ để tương thích nhưng nội dung
  **APPROVED**, byte-identical receipt. `experiments=[DINOv3_LP_run01]`.
- TV2 approval ghi nguồn chat/ủy quyền và điều kiện đã PASS; TV3 approval ghi
  receipt/commit/SHA nguồn thực; TV1=null. DRAFT trước khóa lưu nguyên byte tại
  `w5_final_review/2026-10-30/attempt_01/previous_protocol.draft.json` và
  `previous_W5_PROTOCOL.md`; các receipt lịch sử không sửa.

Commit chứa receipt truy bằng `git log -1 -- configs/dinov3_lp_w5.local.protocol.json`
và được báo đúng SHA sau push. Không điền SHA commit giả hoặc tự tham chiếu.

## Dữ liệu và class order khóa

Chỉ comparison_v1: train2800 parent/3125 GT crops; validation600 parent/680 GT
crops,75 ảnh/lớp. GT integer XYXY, right/bottom exclusive, padding0; không đổi
nhãn/split/geometry hoặc nguồn ảnh. Không sử dụng Test hay1665 ứng viên mở rộng
chưa quality gate. Image_id là đơn vị metric; mọi crop theo đúng parent/split.

| File trong data/processed/comparison_v1 | SHA-256 |
| --- | --- |
| provenance.json | d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f |
| class_map.json | 122c3a8c6b297c1d63c3b18db91cf6b3f279a2f979e6b3e77824dbdd086fc58e |
| train.jsonl | 537d467f7f0ec1ea9fb6a182a37caf0ca1b4f572818789eb6a8c7fc118ef0a11 |
| val.jsonl | 4a18d30378619a39a317af93e1a375ba95162b234380cbf373f26308ac0dfd34 |
| b2/train.jsonl | 023c3cbf31c42e6e35547a5d928fa93cc00a31a0657879d5e775b4a9d37ce3d3 |
| b2/val.jsonl | 7a4c1b2edf1712e675b5b84c581733f3112b950d2318d4f9ae51d33dd366067e |

Class ID0–7: large_antlered_muntjac, annamite_striped_rabbit, sambar,
chinese_serow, common_palm_civet, masked_palm_civet, silver_pheasant,
eurasian_wild_pig. Không đổi class order. Metadata và mẫu train32 byte SHA đã
kiểm hiện tại; full3400 image/RGB preflight là bằng chứng lịch sử. Không có
chứng minh near-duplicate mới hoặc annotation chuyên gia mới.

## Model và preprocessing khóa

DINOv3 ViT-S/16, CLS `x_norm_clstoken`384, backbone frozen/eval;
Linear(384,8,bias=True). Chỉ model này cho lượt đã đăng ký, không tự fallback
DINOv2/đổi seed/chạy thêm candidate. Dự phòng ở proposal cũ chưa phải quyền chạy.

Pretrained `facebookresearch/dinov3:LVD-1689M:ViT-S16`, upstream commit
`6876159a11b4df116f30f667f8c9888617df0751`, weights SHA-256
`08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d`,86531063bytes.
Source kiểm clean checkout/commit/import path/full weights SHA và strict loading.

Preprocess `dinov3_square256_bilinear_uint8`: convert RGB, không EXIF rotation;
crop theo bbox khóa → ToImage uint8 → Resize square256×256 bilinear,
antialias=True → ToDtype float32 scale=True → Normalize mean[.485,.456,.406],
std[.229,.224,.225]. Không random augmentation. Không dùng preprocessing B2.

TV2 không có weights/vendor và không replay GPU. Chấp nhận gói TV3 rehash/
checkout ngày30 và smoke ngày29 gắn source đúng SHA/strict=True; không có log
missing/unexpected keys riêng. Đây là review receipt/source, không tự load lại
binary. GPU smoke reports RTX4060Laptop8GB, FP32, frozen/features32×384,
forward4.632s; peak allocated299583488bytes chỉ phạm vi smoke.

## Huấn luyện và ngân sách khóa

| Tham số | Giá trị |
| --- | --- |
| Official experiment / số lượt tối đa | DINOv3_LP_run01 / 1 |
| Seed | 42 duy nhất |
| Max epochs / early-stop patience | 50 / 7, image-level val macro-F1 |
| Optimizer | SGD lr.01, momentum.9, weight_decay.0001, nesterovFalse,dampening0 |
| Scheduler | CosineAnnealingLR T_max50,eta_min0; step sau optimizer updates và validation mỗi epoch |
| Loss | mean crop CE mỗi parent, rồi mean parents mỗi optimizer update |
| Effective batch | 32 parents; giữ batch cuối16, không drop_last |
| Feature extraction | microbatch32 crops/shard128, frozen backbone; không gradient accumulation |
| Runtime | CUDA RTX4060Laptop8GB, FP32, AMP/TF32false, deterministic |

Cache32 crops khác head32 parents; không nhân sample_weight1/n lần hai.
Nếu OOM hoặc cần đổi microbatch/config/source: dừng và review lại, không tự đổi
raw config đã khóa. Khả dụng GPU/assets hiện tại do TV3 kiểm trước run; receipt
không cam kết peak VRAM/toàn thời gian. Resume cùng run chỉ khi binding nguyên
config/cache/code/runtime; completed run bất biến. Không mở run mới để bỏ kết quả.

## Checkpoint selection, predictions và validation

Chọn epoch có **image-level validation macro-F1 lớn nhất**; chỉ `score > best`
đổi best nên hòa giữ epoch sớm nhất. Patience tăng khi không cải thiện.
Softmax mỗi crop → mean đủ vector8 của mọi crop theo image_id → argmax;
hòa chọn class ID thấp nhất. Không mean logits/majority vote/lọc confidence.

Metric phụ: image top1 accuracy, macro precision/recall, P/R/F1/support8 lớp,
zero_division0; confusion matrix rows=true,columns=predicted. Giữ full precision.
Dự đoán phải đủ600 IDs/680 crops, không mất/thừa/trùng, đúng nhãn/hash/class
order và vector finite/sum/tie rule. Contracts trong
`contracts/w5_crop_prediction.schema.json`, `contracts/w5_image_prediction.schema.json`.
Không dùng mục tiêu88% làm số liệu thực hoặc một seed làm seed stability.

TV3 trả checkpoint/hash/bytes, config/binding/actual execution commit/runtime,
source/pretrained pin, log đủ epochs/best epoch, preprocessing/classmap,
crop+image predictions, metrics/CM, fresh-process reload và artifact hashes.
TV2 audit và reload/adapter độc lập trên validation rồi mới kết luận khả năng
so sánh/bàn giao demo. Gate cấu trúc không tự xác thực danh tính reviewer hoặc
mọi implementation; source/evidence review ở final report là phần bắt buộc.

B2 reference giữ checkpoint SHA
`8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`,
89548866bytes, best epoch21. Native/adapter reference đã kiểm ở attempt cũ;
không sửa/train lại B2. Preprocess/reference chi tiết trong protocol DRAFT đã
lưu và report B2 W5. DINO chỉ được cân nhắc cho demo sau validation/reload/review,
B2 vẫn fallback demo; GT-crop metric không phải end-to-end detector metric.

## Bảo vệ Test và trạng thái W5

Không chạy Test W4 để chọn model/checkpoint/hyperparameter/preprocessing, không
mở rộng chưa gate, không thực hiện W6 hoặc merge PR. Lần final review này chỉ
metadata train/val, byte32 train mẫu và fixture software; không DINO inference.

Sai lệch vận hành lịch sử vẫn được công khai: ở attempt đầu W5 đã gọi nhầm
validator integrity toàn snapshot rồi dừng Ctrl+C, log cuối750/4000, số/ID ảnh
thực decode không xác định, scope có Test. Không model forward/metric/selection
hoặc receipt PASS từ lệnh đó; sau đó gate chỉ train/val3400 đã PASS. Xem
`w5_evidence/attempt_01/deviations.json`; không tuyên bố toàn chat chưa bao giờ
truy cập raster Test. Lần final review không chạy lại lệnh đó.

B1–B3 và approval đã PASS. **W5 PARTIAL — DINO RESULT PENDING**; UI-A11Y-01 P2
chờ TV4 sửa/TV2 retest là việc riêng. Không gọi W5 COMPLETE khi chưa có DINO.
