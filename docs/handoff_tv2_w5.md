# TV2 W5 handoff — protocol APPROVED, 30/10/2026

**B1/B2/B3 PASS. Đã đăng ký chính thức DINOv3_LP_run01, tối đa một lượt,
seed42. W5 PARTIAL: chưa có kết quả/checkpoint DINO.**

TV2 final review theo ủy quyền người dùng; TV3 receipt có nguồn Git, không phải
chữ ký mật mã; TV1 reviewer=null. Không cần xác nhận lại cùng hyperparameter.
Xem [final review](../reports/tv2/TV2_W5_FINAL_REVIEW_2026-10-30.md),
[protocol](../reports/tv2/W5_PROTOCOL.md), [progress](progress_tv2_w5_w6.md).

## Bản khóa bàn giao cho TV3

- TV3 source commit: `173db631cf74611aca5f95044fe572ab08e81d26`.
- TV3 bundle HEAD: `14d79fd18e2a22bc853cc89559ec9bbb708403da`.
- TV2 base trước khóa: `9f528d241c607be81853a2669d189bd1dd9c4237`.
- Config chuẩn `configs/dinov3_lp_w5.local.json`: raw SHA-256
  `e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce`.
- Config serialized digest cho validator/smoke:
  `32071801dc6eb6408310e6393f73acda9bd9902303236836e4bf8d8a4cb6d6e8`.
- Receipt **`configs/dinov3_lp_w5.local.protocol.json`**, SHA-256
  **`e47b96f5e576c234e2e48143c7c008df79ca62156cebf6b2bf65c0119a6f133a`**.
- `configs/tv2_w5_protocol.draft.json` byte-identical receipt, statusAPPROVED
  dù tên file có draft để giữ tương thích đường dẫn.

Commit TV2 mới chứa receipt được báo sau push trong bàn giao cuối. Truy bằng
`git log -1 -- configs/dinov3_lp_w5.local.protocol.json` trên feat/baseline.
Không ghi SHA commit tự tham chiếu trong chính receipt. Các source commit TV3,
base TV2 và hash artifact cụ thể đã có trong receipt/evidence.

## TV3 phải thực hiện trước official run

1. Fetch commit TV2 mới được bàn giao, lấy **nguyên byte receipt** từ commit đó
   và áp dụng vào nhánh TV3. Không merge nhánh TV2/đổi proposal DRAFT bằng tay.
2. Kiểm SHA receipt/config và serialized digest đúng giá trị trên; giữ nguyên
   ba pipeline file hashes trong `source_lock.files_sha256`. Ghi receipt hash,
   actual execution commit và full binding trong output training.
3. Recheck weights/full SHA, vendor clean đúng upstream commit và data
   comparison_v1 bằng verifier local-assets, output mới. Kiểm CUDA hiện tại.
4. Gọi validator TV3 trên config/receipt thật **trước** official training.
   Gate FAIL hoặc assets/config/source đổi thì dừng/review, không sửa field
   cho qua gate, tự đổi model/device/batch hoặc mở thêm seed/lượt chạy.
5. Chỉ TV3 chạy lượt DINOv3_LP_run01 đã đăng ký; tối đa50epochs/patience7,
   SGD.01/momentum.9/WD.0001/cosine50, FP32, effective32parents. Feature cache32
   crops/shard128 là bước riêng; mean crop CE per parent rồi mean parents,
   batch cuối16 giữ lại. Không tự fallback DINOv2 hoặc dùng1665 ảnh mở rộng.

Lệnh kiểm do **TV3 chạy tại repository/môi trường của TV3** sau áp dụng receipt:

```powershell
python -X utf8 scripts/verify_tv3_w5_bundle.py --local-assets --output outputs/tv3_w5/preofficial_after_tv2_lock_01.json
python -X utf8 -c "from src.training import dino_probe as d, dino_handoff as h; c=d.read_json('configs/dinov3_lp_w5.local.json'); p=d.read_json('configs/dinov3_lp_w5.local.protocol.json'); d.validate_config(c); h.validate_protocol(c,p); assert d.sha('configs/dinov3_lp_w5.local.json')==p['config_file_sha256']; print('PROTOCOL GATE PASS')"
```

Chọn output mới nếu path đã tồn tại. Hai lệnh chỉ kiểm chứng, không train.
Validator này ràng buộc serialized digest/registration/policy và reviewer
fields; không xác thực danh tính hay tự kiểm mọi nội dung source. Review nguồn
và đối chiếu hash phải giữ nguyên. Recheck availability/asset trước thực thi là
điều kiện vận hành của TV3, không phải B1–B3 đang BLOCKED tại TV2.

TV2 không có weights/vendor và không replay GPU; chấp nhận receipt TV3 rehash/
clean checkout ngày30 cùng strict-load smoke ngày29 gắn exact source SHA.
Không có missing/unexpected-key log riêng. Full3400 pixel gate là lịch sử;
TV2 kiểm7 metadata/provenance và32 train byte SHA hôm nay. Không gọi đó là
independent binary load, GPU benchmark hoặc full pixel rerun của TV2.

## TV3 bàn giao sau training

Checkpoint full model/head với SHA/bytes; config chuẩn, protocol receipt và
hash; binding actual execution commit/source hashes/runtime; train_log đủ epoch,
selected epoch, optimizer/scheduler/early-stop; class_map/preprocessing;
validation crop/image predictions đủ680crops/600parents, scores đầy đủ;
metrics/CM/per-class support; fresh-process reload report và predictions/hashes;
handoff.json/model card/cache identity/runtime/time/peak memory/thực tế batch.
Chỉ validation, không mở Test W4 hoặc đổi B2. Không coi synthetic test fixture
là checkpoint, metric hoặc approval thật.

## Việc TV2 tiếp theo

- Kiểm integrity/provenance/budget/split của gói thật, config/receipt/source/hash,
  đủ600parent/680crop và selected epoch theo macro-F1, hòa epoch sớm nhất.
- Chạy artifact auditor và model/adapter reload tiến trình sạch trên validation;
  tính lại accuracy, macro-F1/P/R, per-class/support/CM và error analysis.
- So sánh B2 cùng frozen release; không suy ra lợi thế kiến trúc thuần túy từ
  khác pretraining/recipe, không dùng mục tiêu88% hay một seed làm kết quả.
- Chỉ đề xuất DINO cho demo sau validation/reload/review; B2 vẫn fallback demo.
- TV4 sửa UI-A11Y-01 P2 (export mobile thiếu accessible name), TV2 retest.
  Functional review15cases đã PASS; không merge/APPROVE PR8 thay reviewer.

## Trạng thái và lịch sử

48 tests liên quan mới PASS, verifier/environment/contracts PASS; receipt thật
qua validator,7 mutation sai bị chặn. Mọi code/tests production giữ nguyên.
Evidence mới `reports/tv2/w5_final_review/2026-10-30/attempt_01/` lưu DRAFT cũ,
ủy quyền, TV3 receipts, audit, tests và integrity; lịch sử trong
[review trước khóa](../reports/tv2/TV2_W5_PRETRAINED_REVIEW_2026-10-30.md) không sửa.

W5 **PARTIAL — APPROVAL PASS, DINO RESULT PENDING**. Draft PR từng chuẩn bị và
GitHub connector403 được giữ như lịch sử; không tự merge PR hoặc làm W6.
Không train DINO thay TV3, chạy Test W4, sửa B2/dataset hoặc receipt lịch sử.
