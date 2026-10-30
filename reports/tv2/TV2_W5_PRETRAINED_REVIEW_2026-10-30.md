# TV2 W5 review gói pretrained DINOv3 nhận ngày 30/10/2026

**Chưa đủ điều kiện official training. Protocol vẫn DRAFT.** TV2 đã nhận sự
đồng ý hyperparameter **có điều kiện** từ người dùng tự xác nhận là TV2 trong
chat ngày 30/10; không yêu cầu TV2 xác nhận lại những hyperparameter đã nêu.
Chưa có cấu hình byte chuẩn được TV3 chọn/xác nhận và chưa đủ gói kiểm chứng
được tài liệu bàn giao dẫn chiếu. `DINOv3_LP_run01` vẫn là ID đề xuất, **chưa
đăng ký chính thức**, `experiments=[]`; không khóa config hoặc tự tạo approval.

## Nguồn đã đọc và bảo toàn

Base TV2 `163947b5eec79785c89b00dfc5b2b2d618a0d772`, nhánh `feat/baseline`.
Đã fetch origin: TV3 vẫn `60516f51fccbb85e6e266a022d94ea90d2239a11`, TV1 plan
`9abc9c572a9191e8a43a5abef05ebaf846b8356f`. Không thấy gói W5 được commit trên
nhánh TV3; danh sách PR hiện chỉ có PR8 mở, PR6 là W4 đã đóng; comments PR6
đã kiểm không có xác nhận W5. Không dùng trạng thái này thay approval.

Ba file nhận tại `dino/` được giữ nguyên, không stage thư mục nguồn untracked.
Bản sao nguyên byte trong
`w5_pretrained_review/2026-10-30/attempt_01/received/`; không có weights nhị phân
hoặc URL tải ký số trong gói này.

| File | Bytes | SHA-256 nhận tại TV2 |
| --- | ---: | --- |
| dinov3_lp_w5.local.json | 1063 | e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce |
| backbone_smoke_2026-10-29.json | 3189 | 52c635be70f6f4a5466a7a816d9fc425036924f350ed9b6ea0a7a99e94549043 |
| W5_PRETRAINED_READY.md | 2230 | 0c5d7947d1d3aeb8e2421eb380e01a1d88c0d2639644ccc8aee5971a4c2de261 |

## Config bàn giao so với config smoke

| Kiểm tra | Kết quả |
| --- | --- |
| SHA byte config thực nhận | e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce |
| SHA config ghi trong smoke | 32071801dc6eb6408310e6393f73acda9bd9902303236836e4bf8d8a4cb6d6e8 |
| So sánh JSON đã parse | **Giống toàn bộ giá trị**, kể cả hyperparameters và paths |
| Đổi CRLF thành LF | SHA446bf4b26ecf496b4d3a597d5522ba6d6951303f71705fb60ad9cea12d63d00e, vẫn không khớp smoke |
| Đổi về CRLF | Trở lại SHAe9303b…, không khớp smoke |
| Canonical sorted compact JSON | SHA8a1d9edaf9adda04cc69b5831e94cc1c86c010a0d071f58baeb8759a1cff90f8; chỉ dùng chẩn đoán, không thay raw lock |

Không kết luận đã biết nguyên nhân chênh lệch; có thể khác serialization nhưng
chưa có file byte gốc của SHA320718… để xác minh. **Không chỉ sửa hash trong
smoke cho khớp file mới**, không chuẩn hóa/ghi đè nguồn. TV3 phải xác định file
chuẩn và full SHA, giải thích quan hệ với smoke và cung cấp bằng chứng bind
smoke/preflight với cấu hình chuẩn. Đây là blocker B1 theo yêu cầu người dùng.

## Đối chiếu cấu hình và dữ liệu

| Thành phần | Đã xác minh từ các file nhận | Giới hạn |
| --- | --- | --- |
| Backbone | dinov3_vits16, frozen; READY mô tả eval | Chưa replay model ở TV2 |
| Head/pooling | CLS x_norm_clstoken 384 → Linear8 theo READY | Chưa có source local của pipeline để kiểm tra head/data loader |
| Optimizer | SGD, lr0.01, momentum0.9, weight_decay0.0001 | Giá trị config/smoke giống nhau; chưa kiểm implementation |
| Scheduler | cosine; READY ghi cosine50 | Cần source/config chuẩn để kiểm scheduler params và thứ tự step |
| Seed/budget/epochs | Seed42, max50epochs, patience7; budget TV2 vẫn max1candidate run | Không có run chính thức được đăng ký |
| Effective batch | 32 parent images; cache extraction batch32 crops, shard128 | Hai batch khác đơn vị; READY ghi không accumulation, head học cache |
| Loss/last batch | Mean CE các crop trong parent rồi mean parents; giữ batch cuối theo READY | Cần source kiểm chứng grouping/normalization, không chỉ tin tên config |
| Aggregation/ties | Mean crop softmax theo image_id; argmax tie ID thấp, checkpoint tie epoch sớm | Theo READY, khớp protocol |
| Precision | amp=false trong config và runtime report, TF32=false | Chưa có tensor/model dtype từ code để kiểm FP32 đầy đủ |
| Preprocessing | Chỉ có ID dinov3_square256_bilinear_uint8 | Thiếu implementation: dtype/scaling/normalize/antialias/crop geometry cần đối chiếu source |
| Data | Provenance d9fd5461…0a5f; đủ2800/3125train và600/680val | Chỉ audit metadata lần này, không chạy lại pixel gate |

Bảy file train/val/class map trong smoke có SHA khớp toàn bộ byte local.
Class order và disjoint Train/Val đã kiểm qua loader audit metadata; không mở
manifest/pixel Test. Không đổi dữ liệu, B2 checkpoint hoặc dùng mở rộng chưa gate.
Raw kết quả kiểm tra nằm trong
[audit.json](w5_pretrained_review/2026-10-30/attempt_01/audit.json).

## Source commit và weights

Đã đối chiếu [commit upstream chính thức](https://github.com/facebookresearch/dinov3/commit/6876159a11b4df116f30f667f8c9888617df0751).
[Factory tại đúng commit](https://raw.githubusercontent.com/facebookresearch/dinov3/6876159a11b4df116f30f667f8c9888617df0751/dinov3/hub/backbones.py)
có dinov3_vits16, patch16, embedding384 và tiền tố weights08c60483. Điều này
khớp khai báo kiến trúc/tiền tố hash, **không chứng minh full weights SHA**.

TV3 khai báo weights LVD-1689M 86.531.063bytes, SHA
`08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d`.
Hai đường dẫn `outputs/tv3_w5/vendor/dinov3` và
`outputs/tv3_w5/pretrained/dinov3_vits16.pth` đều **không tồn tại tại TV2**;
không rehash/load được binary hoặc đối chiếu checkout actual với commit.
Không yêu cầu URL ký số/credential; TV3 có thể cung cấp gói kiểm chứng truy vết
được thay vì chuyển nguyên weights sang máy TV2 nếu quy trình nhóm cho phép.

Smoke khai báo SHA code pipeline
`8529891d6cd213f4cc186de104b31d58d539782e2003fa6c475eb4000cdcb988`
nhưng file code tương ứng không nằm trong ba file nhận, chưa có trên branch
TV3 đã fetch. Cần source có commit/hash để kiểm factory strict-load, frozen/eval,
preprocessing, feature cache và parent-weighted training. Không yêu cầu TV2
huấn luyện thử. [README upstream tại cùng commit](https://raw.githubusercontent.com/facebookresearch/dinov3/6876159a11b4df116f30f667f8c9888617df0751/README.md)
có ví dụ square resize256/float32 scaling/normalization; không tự áp ví dụ đó
cho ID transform của TV3 khi chưa thấy implementation thực.

## GPU smoke: đã nhận PASS, chưa tái chứng minh độc lập

Report ghi RTX4060Laptop, VRAM8.585.216.000bytes; Python3.12.10,
torch2.6.0+cu124/torchvision0.21.0+cu124/CUDA12.4, threads10, AMPfalse,
TF32false, deterministic algorithms true. Features `[32,384]`, frozen true,
forward4,632043s, peak allocated299.583.488bytes/reserved402.653.184bytes.
Đây là **smoke report của TV3**, không phải phép đo mới của TV2, metric val
hoặc peak bộ nhớ cả training. READY nói hữu hạn/strict-load trên32crops train;
TV2 chưa có sample IDs/hash receipts và source code để kiểm lại các khẳng định.

`data.verified_source_images=0`; READY nói sampled byte hashes và có data
preflight28/10 riêng, nhưng thư mục `pretrained_2026-10-29/`/report preflight
được dẫn chiếu chưa bàn giao. Không gọi đây là FAIL GPU, cũng không coi smoke
này chứng minh đủ chất lượng/hash toàn bộ train/val cho official run. Preflight
TV2 lịch sử vẫn có giá trị lịch sử, chưa bind tới code/config chuẩn lần này.

## Phê duyệt và yêu cầu tối thiểu còn lại

TV2: lưu nguyên ý kiến người dùng trong config `approval_evidence.TV2`, trạng
thái **CONDITIONAL**, phụ thuộc hash/dữ liệu/procedure. Không giả tên GitHub,
chữ ký hoặc biến điều kiện thành đã đạt. TV3: READY tự ghi đang chờ TV2/TV3
xác nhận và chưa commit/push; do đó `reviewers.TV3=null`, evidence TV3 chưa có.

| Blocker | Owner | Bổ sung cần thiết |
| --- | --- | --- |
| B1 canonical config | TV3 | File chuẩn/full SHA; giải thích SHAe9303b… so với320718…; bind smoke/preflight vào bản chuẩn trước lock |
| B2 TV3 approval | TV3 | Xác nhận thực tế đúng config chuẩn/experiment qua phản hồi, commit hoặc PR có nguồn truy vết |
| B3 verification bundle | TV3 | Source pipeline đúng SHA/commit + pretrained hash/strict-load/checkout proof và data preflight/sample hash receipts đã được READY dẫn chiếu; đủ kiểm preprocessing/parent grouping/train-only procedure |

Không yêu cầu đề xuất lại lr/optimizer/seed/budget hoặc xin lại ý kiến TV2 về
các giá trị đó. TV2 chỉ xem các điều kiện sau khi TV3 trả lời B1–B3. Khi tất
cả đạt mới điền official `experiments=["DINOv3_LP_run01"]`, chọn model,
khóa config chuẩn và chuyển APPROVED. **Hiện chưa được TV3 chạy official
training theo protocol này.** Không train, Test W4, sửa B2 hay merge PR.
