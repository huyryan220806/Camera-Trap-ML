# TV2 W6 D2 — review hồ sơ TV3 R1/R2 trước official training

**Ngày review:** 06/11/2026. **Kết luận:** `READY_FOR_TV2_DECISION`.
Đây là kết luận kiểm định kỹ thuật của TV2 trên hồ sơ đã nhận, **không phải
approval**. Registry `experiments/w6/registry.json` vẫn `DRAFT`, approval TV2
và TV3 đều `null`; R1/R2 chưa có official attempt, checkpoint hay metric W6.
Không chạy official training, GPU smoke mới, R0 rerun hoặc Official Test W4.

## Phạm vi, Git và cách phân biệt SHA

- Nhánh làm việc `feat/baseline`, HEAD trước review
  `b91476d3d9658e006027225cfc93008125536c0f`; tracked index/working tree
  sạch. Các file untracked có sẵn của người dùng, gồm báo cáo D1 vừa tạo,
  `dino/` và ZIP TV1, được giữ nguyên. Fetch remote thành công, không checkout,
  merge, rebase hoặc sửa `feat/crop-classifier`.
- TV3 handoff `8cd97538390a3f55c66193d79e637dfd73ace770` là HEAD remote
  `feat/crop-classifier` tại lúc fetch. Source `127cac5b64d37fdda630a2f84b006a8e420dc9ed`
  tồn tại và là tổ tiên của handoff. Review dùng `git show` trên hai commit,
  không tin riêng tên file ZIP hoặc `status: PASS`.
- ZIP local 110.470 byte, SHA-256 **tự tính từ bytes**
  `030093e92f07fcbe9a2a7ed39eb60919d66250181cd6c0dd9278106927e21ce7`;
  file `.sha256.txt` ghi cùng giá trị. Đây là hash raw ZIP. 35 entry, không
  trùng/đường dẫn nguy hiểm, `testzip()` không báo CRC lỗi. `manifest_sha256.json`
  khớp toàn bộ 34 entry còn lại về raw byte SHA và kích thước. 24 snapshot có
  đường dẫn Git tương ứng bằng **đúng bytes** ở commit đã pin. `git show` dùng
  để lấy raw blob; Git object ID không bị dùng thay SHA-256.
- JSON `handoff_audit.json` chứa hash raw file, hash canonical JSON và 5 trường
  thay đổi candidate→frozen. Canonical SHA = SHA-256 UTF-8 JSON sorted keys,
  separators `(',',':')`, `ensure_ascii=False`, không newline. Vì cách serialize
  khác, canonical SHA không được coi là raw file SHA.

Evidence TV2 và index SHA: [D2 evidence](w6_evidence/d2_20261106_01/index.json),
[audit từng entry](w6_evidence/d2_20261106_01/handoff_audit.json).
Lệnh kiểm ZIP được lưu thành [script TV2](../../scripts/review_tv3_w6_handoff.py);
script chỉ đọc ZIP/Git/local manifest, không giải nén để thực thi và không tải model.

## Bảng kiểm định

`PASS` nghĩa là đạt trong **phạm vi được ghi**; `PENDING` là bằng chứng chưa đủ
để khẳng định riêng mục đó. `L` thấp, `M` trung bình. Producer = điều TV3 ghi;
TV2 = phép kiểm độc lập hoặc kiểm code cụ thể. Hash raw của từng file nằm trong
`handoff_audit.json`, không lặp toàn bộ trong bảng.

| Tiêu chí | Evidence/file/SHA | Producer | TV2 độc lập | Trạng thái | Mức độ / khắc phục |
| --- | --- | --- | --- | --- | --- |
| ZIP và nguồn Git | ZIP SHA `030093e9…e21ce7`; handoff `8cd9753`; source `127cac5` | Gói và source hợp lệ | Rehash ZIP, CRC, 35 paths, 34 manifest entries, 24 Git blobs; commit/ancestry đúng | PASS | L / không cần |
| Data và init | Preflight R1 raw `bdd20ff0…58cbd`, R2 `47eb3468…b357`; provenance `d9fd5461…b0a5f`, R0 checkpoint `acbe3225…0fbc3` | `comparison_v1`, train 2800/3125, val 600/680 | Rehash 7 manifest local đúng receipt; rehash checkpoint W5 local đúng; preflight counts đúng. Không tự rehash 3400 raster lần này | PASS trong phạm vi hash/metadata | L / giữ pin, kiểm raster ở runtime TV3 |
| Candidate→frozen | R1 canonical `87cfa1d7…1b75c`→`2ab03b7e…d63bf`; R2 `ffc5944d…709868`→`55dea8ab…acb7` | Freeze theo smoke | So sánh đệ quy: chỉ `status`, `runtime.source_sha`, `runtime.runtime_lock`, `smoke_evidence.path/sha256`; **0 trường thuật toán khác**. Source/runtime/smoke hash và proposal tương ứng đúng | PASS | L / không cần chạy lại smoke do freeze |
| TV2 D1 protocol/registry | `configs/w6/R{1,2}.draft.json`; TV3 candidate/frozen, proposal; `proposal_validation.json` | R1/R2 khớp | Không có giá trị D1 cụ thể nào bị đổi; TV3 điền `recipe` và `implementation` (AdamW betas/eps, warmup endpoints, module mode, flip, sampler, batch val) đã kiểm với source. Validator TV2 trên proposal và frozen config trả `VALID`, `DRAFT`, 0 official attempt | PASS | L / giữ review này khi chuẩn bị approval |
| R1 model/gradient | `src/training/dino_w6.py` source lines 173–229, 289–313; smoke R1 raw `9d541874…b2cca1f6` | Frozen ViT, 768D head, gradient đúng | `x_norm_clstoken` + mean **chỉ** `x_norm_patchtokens`, không storage/register; chỉ 2 tensor head trainable; 15 CPU tests tái chạy; smoke named mask/grad đều đúng | PASS | L / không cần |
| R1 SGD/cache | Source lines 237–241, 316–361, 392–455; config R1 raw `92bf5966…cef507c` | SGD/cosine, cache 768 riêng | SGD .01/.9/WD .0001, cosine50/patience7, batch32 parent; cache key chứa source/weights/preprocess/data/crop order/pooling/runtime, 768D/shard128, check SHA và crop IDs. CPU cache/corruption tests PASS | PASS trong phạm vi code/fixture | M / production extraction toàn tập chưa được smoke; đo và giám sát attempt đầu |
| R2 init/mask | Source lines 173–229, 237–258; R2 smoke raw `6b7ead35…d63bf3c` | Nạp W5 full, last2/norm/head train | W5 payload/checkpoint hash và strict state load; smoke liệt kê đúng 32 tensor trainable thuộc blocks10–11, final norm, head; frozen params không đổi sau step | PASS | L / không cần |
| R2 optimizer/schedule | Source lines 237–273; config R2 raw `a649fe30…df36c` | AdamW, warmup/cosine | LR backbone1e-5/head1e-4, WD.01, bias/norm no decay; betas(.9,.999), eps1e-8, foreach/AMSGrad false; epoch1=.5×, epoch2=1×, cosine tới epoch20; patience5 và best image macro-F1 | PASS | L / không cần |
| R2 batch/loss/aug | Source lines 276–313, 392–455; CPU test log | 16 parent, crop micro≤8, flip ngang train | CE mỗi crop nhân `1/(crops_parent×actual_parents)` đúng; final partial batch3; không double weighting, cache R2 disabled; horizontal flip p=.5 chỉ khi `training`; không vertical/random crop | PASS trong phạm vi code/fixture | L / không cần |
| Precision/reload/resume | Source lines 96–101, 388–455; CLI lines 98–178, 217–319 | FP32, strict reload/resume | Runtime pin từ smoke canonical đúng `7ae3631e…1527a`; code tắt AMP/TF32, checkpoint giữ optimizer/scheduler/RNG CPU+CUDA/sampler epoch/best/patience; synthetic exact resume/load tests PASS, smoke receipts báo exact trên GPU | PASS trong phạm vi receipt/code | M / full official process replay chưa chạy, sẽ là gate riêng |
| Train-only smoke | `R1_smoke01.json`, `R2_smoke01.json`, `usage.json` raw `0bc5b97b…7f49` | GPU smoke PASS; no val inference/Test | Code `smoke` lấy train groups, forward/backward/step, reload trên train; R1 35 parent/131 crop, R2 19/83; preflight 3400 source images theo producer, smoke gate ghi 0 dù code gọi `verify_pixels(selected)` riêng; không có validation inference trong smoke. Không tái chạy GPU tại TV2 | PASS cho smoke ngắn; GPU tái hiện PENDING | M / nếu yêu cầu GPU độc lập thì cần TV3 cung cấp thêm, không gán là TV2 đã tái hiện |
| GPU time/budget | usage 2 sessions; `dino_w6_control.py` lines 117–187 | 12.079593s R1, 6.0549265s R2; booking ghi “đã thống nhất” | Cộng 18.1345195s ≈0.00503737h, 0 official attempts; code tính cả failure/OOM, extraction trong session, ≤6 attempts, ≤12h và ≤2h/attempt. Không xác minh độc lập đồng thuận nhóm hay dự báo full 20–50 epochs | PASS accounting hiện có; dự báo 2h PENDING | M / TV2/TV3 xác nhận slot và theo dõi thời gian thật mỗi attempt |
| Software tests | `checks02/full_suite.log` raw `be49f697…f27df9b`, TV2 logs ở index | 505 tests PASS, gồm TV3 W6 15 và TV2 W6 50 | TV2 tái chạy **15 TV3 + 50 TV2 W6 + 70 focused W5 = 135 PASS**, 0 fail/skip; TV2 không nhận 505 là tự tái hiện | PASS trong phạm vi 135 | L / không cần mở full suite chỉ để lặp con số |
| Protected Test / R5–R6 | Source `read_data` lines 126–170, CLI smoke lines 98–178; TV2 registry | `test_opened=false`, R5/R6 chưa mở | Static code smoke dùng train-only; preflight có đọc/verify pixels Train+Val nhưng `model_forward=false`, không inference Val; không có Test reader trong đường chạy đã review. Registry TV2 R5/R6 vẫn CONDITIONAL, TV1 data review PENDING | PASS trong phạm vi source/receipts | M / không coi producer field là forensic audit toàn máy |

### Hash cấu hình và provenance cụ thể

| Run | Candidate raw SHA-256 | Candidate canonical SHA-256 | Frozen raw SHA-256 | Frozen canonical SHA-256 |
| --- | --- | --- | --- | --- |
| R1 | `7ca4381eec2694975f8249cdaf21a80bd39e021aee1320f0e754a050898fb2b1` | `87cfa1d7a87049565a9c172f8c05b34a5428d92556253945788144979e01b75c` | `92bf5966fe2b4e228fb52b0ae975c8e5044ca1c35b6a4d06ab79f5733cef507c` | `2ab03b7e13d798b8aace5e4b3542a189389c43c7630f4132303b9200fced63bf` |
| R2 | `959cb63e0eaf259a08a1a9a0090f56eeeb4a1eb8c1c25d816909f22dafebd588` | `ffc5944d2f8f66dc015bb4ffff49e55d3ea84e361f413d5b123c319cba709868` | `a649fe30c436fee538d9a58a904685a558aebd77a1df3af91409f55f1a86f36c` | `55dea8ab328e43581642deb964631d391a5b88596feb191a5fa5911a7a94acb7` |

Frozen runtime source `127cac5…`; runtime lock canonical
`7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a`.
Smoke evidence raw SHA R1 `9d5418745cf2cd45519415935246cb3be6ee6b5f0349341b9accb821b2cca1f6`,
R2 `6b7ead35a2bfbfb002154db14d992c2fd3ececfe3bf3c546be6bdb62433279e5`.
Hai smoke đều pin candidate canonical, cùng source/runtime với freeze. Proposal
TV3 chỉ đổi đường dẫn/config hash/source của R1/R2 so TV2 D1, giữ R0 và các
run conditional; `approvals` global và per-run đều null, data review PENDING.

## Kiểm thử thực sự chạy và giới hạn

TV2 dùng Python **3.14.3, PyTorch 2.13.0+cpu**, CUDA unavailable; TV3 báo GPU
RTX 4060 Laptop, Python 3.12.10, PyTorch 2.6.0+cu124. Vì khác runtime và không
chạy GPU smoke, 15 TV3 tests là kiểm software CPU trên source snapshot đúng byte,
không chứng minh exact GPU reproducibility. Kết quả chi tiết:

| Lệnh/phạm vi | TV2 thực chạy | Producer báo |
| --- | --- | --- |
| `unittest discover -s tests -p test_dino_w6.py -v` trên source ZIP cô lập | 15 PASS, 0 skip/fail | 15 PASS |
| `unittest discover -s tests -p test_w6_validation.py -v` trên baseline | 50 PASS, 0 skip/fail | 50 PASS |
| 5 patterns W5 evaluation/contracts/DINO compatibility | 70 PASS, 0 skip/fail | Không gộp vào 505 để nhận là TV2 chạy full suite |
| Full repository suite | NOT RUN | TV3 báo 505 PASS trong `full_suite.log` |

Log và SHA ở `w6_evidence/d2_20261106_01/index.json`. Test TV3 fixture có
synthetic CPU training loop nhỏ để kiểm gradient/resume, không phải official
training, không tải weights/ảnh lớn hoặc chạy model trên Test.

Smoke R1/R2 được làm trước commit freeze và trước official run, có mask,
gradient hữu hạn, frozen weights giữ nguyên, strict load và resume exact theo
receipt. Smoke chỉ làm **hai bước nhỏ trên 35/19 parent**; nó không kiểm toàn
bộ cache R1, một epoch trên 2800 parent, validation inference 600 parent,
write/reload package lớn, thời gian end-to-end hay mức VRAM đỉnh khi chạy đủ
dữ liệu. Peak memory ghi 333.190.144/367.531.520 byte chỉ cho smoke. Không
suy ra official run sẽ hoàn thành trước 2 GPU-hour. Đường train và budget guard
đã được review tĩnh; thời gian phải đo ở execution thật và giữ failed attempts.
Booking string trong receipt là producer assertion, không phải TV2 tự xác minh
đồng thuận của toàn nhóm.

## Kết luận theo run và quyết định tiếp theo

- **R1: PASS về hồ sơ kỹ thuật pre-training; đủ để trình TV2 quyết định.**
  Candidate và frozen cùng recipe, 768D/cache/SGD/loss đúng code và tests.
  Không cần TV3 sửa code hoặc chạy lại smoke chỉ vì SHA freeze khác candidate.
  Production full-cache extraction, thời gian full run và replay còn là gate
  của official attempt, chưa được coi PASS.
- **R2: PASS về hồ sơ kỹ thuật pre-training; đủ để trình TV2 quyết định.**
  Full W5 init, mask 2 block cuối+norm+head, optimizer/schedule/loss/flip,
  resume và mask theo smoke đạt trong phạm vi trên. R2 là **so sánh recipe**;
  bất kỳ cải thiện sau này không quy riêng cho việc mở hai block cuối.
- **TV2 có đủ căn cứ để tự xem xét approval R1/R2**, nhưng người review thật
  cần đọc báo cáo, xác nhận lịch GPU/budget và ký receipt riêng cùng TV3.
  Chưa có chứng cứ chữ ký TV2/TV3 nên `READY_FOR_TV2_DECISION` không mở gate
  official. Sau khi hai bên phê duyệt, đưa config/source/smoke đã pin vào lịch
  sử Git phù hợp, cập nhật registry approval bằng reference có thể kiểm, xác
  minh runtime và usage tại máy chạy rồi mới cho TV3 official R1/R2. Nếu đổi
  bất kỳ trường thuật toán/source/runtime, cần review lại và smoke mới theo
  binding mới. Không tự điền approval từ biên bản này.
- R5/R6 vẫn chờ `TV1_DATA_REVIEW=PASS`; trạng thái này **không chặn R1/R2**
  vì dùng `comparison_v1`. R3/R4 cũng chưa mở, chỉ xét sau kết quả R1/R2.

Trạng thái registry TV2 sau review: `protocol_status=DRAFT`, `approvals.TV2=null`,
`approvals.TV3=null`, R1/R2 `REGISTERED` và `attempts=[]`; không có kết quả W6
hay quyết định đổi demo. Code W1–W5, source TV3, TV4 và Official Test giữ nguyên.
