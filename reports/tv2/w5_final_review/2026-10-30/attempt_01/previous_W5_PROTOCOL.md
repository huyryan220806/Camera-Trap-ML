# TV2 W5 validation protocol

**DRAFT — cập nhật 30/10/2026 sau khi đọc đủ ba file TV3. TV2 đồng ý kỹ thuật
có điều kiện; còn blocker config hash, xác nhận TV3 và verification bundle.**
Chưa đăng ký chính thức `DINOv3_LP_run01` hoặc khóa training config. Lập theo kế
hoạch cập nhật 28/10/2026; thực hiện từ 28 sang 29/10 giờ Việt Nam. Lịch W5
28/10–03/11 là đề xuất. TV2 không phê duyệt thay nhóm và không thực hiện W6.

## Nguồn và phạm vi

Kết quả review mới nhất:
[TV2_W5_PRETRAINED_REVIEW_2026-10-30.md](TV2_W5_PRETRAINED_REVIEW_2026-10-30.md).
Ba file nhận từ TV3 tại `dino/` được lưu bản sao nguyên byte kèm SHA trong
`w5_pretrained_review/2026-10-30/attempt_01/received/`. Người dùng tự xác nhận
là TV2 đã đồng ý kỹ thuật với các hyperparameter ngày 30/10 và xác nhận chưa
có tài liệu bổ sung ngoài ba file; yêu cầu giữ DRAFT, không bỏ qua điều kiện.
Ghi đúng ý kiến này trong `approval_evidence.TV2` dưới dạng CONDITIONAL; không
tự ghi tên reviewer TV3 hoặc coi READY/smoke PASS là approval chạy.

Config nhận SHA `e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce`
khác SHA config ghi trong smoke
`32071801dc6eb6408310e6393f73acda9bd9902303236836e4bf8d8a4cb6d6e8`.
JSON values giống nhau nhưng CRLF/LF normalization không tái tạo SHA smoke.
Không chọn một bản chuẩn thay TV3, không sửa hash smoke. Chưa đủ điều kiện
chuyển APPROVED: cần TV3 xác định/xác nhận config byte chuẩn, nguồn approval
TV3 và gói source/pretrained verification/data-preflight mà READY dẫn chiếu.

Các đoạn mô tả chưa nhận gói ở thời điểm nền dưới đây là lịch sử; bảng khai
báo cập nhật hiện tại và report review 30/10 có ưu tiên cho trạng thái W5 mới.

Nền tích hợp: `60516f51fccbb85e6e266a022d94ea90d2239a11` (main và nhánh TV2
trên origin lúc bắt đầu). TV1 W5: `9abc9c5` trên `feat/metadata-split`, được đọc
và chạy verify-only trong snapshot riêng, chưa merge vào nhánh TV2. TV3 tại
`60516f5` chưa có gói DINO; TV4 PR #8 mở tại
`fef2511b571b23be3d4e2cf6c1ccedd659097b6f`. PR #7 đã merge ngày 25/10.

Cập nhật cấu hình ngày **29/10/2026** theo chỉ thị người dùng trong chat
“Cập nhật TV2 W5 protocol theo cấu hình TV3 đã thống nhất”. Đây là nguồn quyết
định cho seed, ngân sách, epochs/patience, effective batch và thiết bị dự kiến
bên dưới; không tự coi là chữ ký/review độc lập của TV2/TV3.
Đã fetch và đọc lại `feat/metadata-split` tại
`9abc9c572a9191e8a43a5abef05ebaf846b8356f:docs/plans/TV3_W5_W6.md`, SHA-256
nội dung Git `7708c9683b0938b728276302f88c15df5e9bac99edb0944a79e3fa0118f5d88a`.
Commit do TV1 công bố kế hoạch; tài liệu mô tả hướng DINO/frozen backbone,
dữ liệu và seed 42, **không phải approval riêng của TV3 cho toàn bộ đăng ký**.
Kế hoạch cũ có đề xuất thêm seed/fine-tune khi đủ ngân sách; lượt cập nhật này
chỉ cho tối đa một candidate training run, backbone frozen, seed 42. Không
mở thêm seed, fine-tune hay lượt fallback thứ hai theo đề xuất cũ.

Nguồn ưu tiên: `docs/experiment_protocol.md` (bảo vệ Test),
`docs/handoff_tv1_w3.md` (geometry/data bất biến), kế hoạch W5–W6 cập nhật
28/10 trong `TV2_W5_W6.md` và bản cùng nội dung ở snapshot
`docs/plans/TV2_W5_W6.md`, `docs/handoff_tv1_w5.md`, báo cáo TV1 W5.
Kế hoạch sáu tuần DOCX được đọc để đối chiếu trách nhiệm; phạm vi mới theo
kế hoạch 28/10. Không tìm thấy tài liệu trình bày tiến độ 27/10 hoặc
`reports/tv2/TV2_REVIEW.md` trong inventory/lịch sử Git đã rà. Không thay bằng
báo cáo tự tạo. Danh mục/hash nguồn: `w5_evidence/attempt_01/source_audit.json`.

## 1. Dữ liệu và định danh

Chỉ dùng `comparison_v1`, train 2.800 ảnh/3.125 GT crop, validation 600 ảnh/680
GT crop. Tám lớp, validation có 75 ảnh/lớp. Ảnh/crop cùng split với parent;
không sửa nhãn, geometry, split, thêm padding hay chọn lại mẫu.

| File trong data/processed/comparison_v1 | SHA-256 |
| --- | --- |
| provenance.json | d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f |
| class_map.json | 122c3a8c6b297c1d63c3b18db91cf6b3f279a2f979e6b3e77824dbdd086fc58e |
| train.jsonl | 537d467f7f0ec1ea9fb6a182a37caf0ca1b4f572818789eb6a8c7fc118ef0a11 |
| val.jsonl | 4a18d30378619a39a317af93e1a375ba95162b234380cbf373f26308ac0dfd34 |
| b2/train.jsonl | 023c3cbf31c42e6e35547a5d928fa93cc00a31a0657879d5e775b4a9d37ce3d3 |
| b2/val.jsonl | 7a4c1b2edf1712e675b5b84c581733f3112b950d2318d4f9ae51d33dd366067e |

| ID | Loài |
| --- | --- |
| 0 | large_antlered_muntjac |
| 1 | annamite_striped_rabbit |
| 2 | sambar |
| 3 | chinese_serow |
| 4 | common_palm_civet |
| 5 | masked_palm_civet |
| 6 | silver_pheasant |
| 7 | eurasian_wild_pig |

`image_id` là đơn vị metric; `crop_id` nhận dạng crop; `image_id` trên crop là
source image ID. Giữ `seq_id/sequence_id`, `location`, `quality.local_path`,
file SHA/RGB SHA và `bbox_xyxy`. Metadata validator kiểm tra dẫn xuất, hash và
giao ID/path/sequence/location giữa split; pixel gate riêng chỉ đọc train/val.
Near-duplicate/perceptual hash và nhãn chuyên gia chưa được chứng minh.

TV1 kiểm kê nguồn train mở rộng 19.266 ảnh và chọn 1.665 **ứng viên metadata**;
`training_ready=false`. Không dùng vào train chính thức. Holdout khảo sát 109
ảnh chưa đủ hỗ trợ độc lập tám lớp, `holdout_ready=false`. Một training release
mở rộng cần quality gate TV1 và protocol/experiment ID riêng; khác dữ liệu
không cho phép quy toàn bộ thay đổi metric cho kiến trúc.

## 2. Loader, GT boxes và preprocessing

B2: `B2ComparisonDataset` và `B2CropClassifier`, ResNet18 FC8/dropout0, full
fine-tuning đã hoàn tất từ W3; trọng số khởi tạo
`torchvision ResNet18_Weights.IMAGENET1K_V1`, nguồn được ghi trong protocol W3:
`https://download.pytorch.org/models/resnet18-f37072fd.pth`.
Checkpoint cố định SHA
`8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`,
89.548.866 bytes, best epoch 21. Config train đã đối chiếu từ commit TV3
`65b99b9def6a147abe6a4d436c18a067f3f37dc4`; config embedded và preprocessing
được lưu cùng bằng chứng reload.

RGB, không xoay EXIF; cắt đúng tọa độ nguyên `bbox_xyxy` đã khóa (right/bottom
exclusive, padding0, geometry TV1 round-half-even/clip/min8). Validation B2:
Resize cạnh ngắn256 → CenterCrop224 → ToTensor → ImageNet normalize
mean `[.485,.456,.406]`, std `[.229,.224,.225]`. Không augmentation khi đánh giá.
Không train lại B0/B1/B2. B1 dùng full-image, chỉ dẫn số liệu lịch sử đã có.

Ứng viên ưu tiên: **DINOv3 ViT-S/16, frozen backbone, linear classification
head tám lớp**. Dự phòng **DINOv2 ViT-S/14** chỉ khi không lấy được weights
DINOv3; phải chọn backbone thực tế và đăng ký experiment **trước official run**.
Fallback dùng chung ngân sách tối đa một lượt, không cho phép chạy cả hai rồi
chọn theo validation. Không đổi kiến trúc giữa lượt hoặc fine-tune backbone
trong cấu hình này.

TV3 đã khai báo source commit `6876159a11b4df116f30f667f8c9888617df0751`,
weights LVD-1689M SHA `08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d`,
86.531.063bytes; pooling `x_norm_clstoken` 384 → Linear8, frozen/eval.
Official upstream factory đúng commit có patch16/embed384/prefix08c60483;
đối chiếu này không chứng minh full SHA weights hoặc checkout actual của TV3.
Weights/vendor paths không có tại TV2. Config chỉ nêu preprocessing ID
`dinov3_square256_bilinear_uint8`, chưa có implementation để kiểm dtype/scaling/
normalization/geometry. Không tự điền preprocessing B2 hoặc default upstream.

`model.selected_model=null`, `experiments=[]` và canonical config hash=null
vẫn giữ nguyên; `proposed_experiment_id=DINOv3_LP_run01` chỉ là đề xuất.
Các SHA/pretrained/pooling trong draft được gắn trạng thái khai báo, chưa có
independent weight rehash/strict-load tại TV2; không biến thành model READY.

## 3. Dự đoán và metric

Tính softmax từng crop, trung bình đủ vector tám lớp của **mọi** crop cùng
`image_id`, rồi argmax. Không trung bình nhãn, majority vote, mean logits, chọn
crop dễ hoặc lọc confidence. Dự đoán hòa vector chọn **class ID nhỏ nhất**,
cùng quy tắc B2 và cấu hình ứng viên cập nhật.

Metric chọn checkpoint: **macro-F1 cấp ảnh**. Phụ: accuracy **top-1** cấp ảnh,
macro-precision, macro-recall, P/R/F1/support đủ tám lớp; zero_division=0.
Confusion matrix hàng thật/cột dự đoán. Lưu scores độ chính xác gốc, chỉ làm
tròn bảng trình bày. Mục tiêu accuracy ≥88% chưa phải kết quả.

Mỗi JSONL ảnh gồm `image_id`, `ground_truth`, `predicted_class`, `class_scores`
đủ8, `crop_count`, `experiment_id`, `checkpoint_sha256`. Schema trong
`contracts/w5_image_prediction.schema.json`; input crop có schema riêng.
Kiểm tra đủ600 ID/680 crops, không trùng/mất/thừa ID, nhãn, score NaN/Inf,
class order, sum softmax, argmax/tie, checkpoint hash. Metric được tính độc lập
từ predictions đã lưu bằng CM arithmetic và kiểm thử đối chiếu sklearn.

## 4. Chọn checkpoint, hòa, seed và ngân sách

| Tham số cấu hình cập nhật từ người dùng | Giá trị |
| --- | --- |
| Seed | 42, duy nhất |
| Ngân sách | Tối đa **1 candidate training run**, gồm lựa chọn DINO chính hoặc dự phòng |
| Max epochs | 50 |
| Early stopping | Patience 7, theo image-level validation macro-F1 |
| Optimizer TV3 đề xuất, TV2 đồng ý kỹ thuật có điều kiện | SGD lr0.01, momentum0.9, weight_decay0.0001 |
| Scheduler khai báo | Cosine50 theo READY; source/params/step order chưa kiểm |
| Chọn checkpoint | Image-level validation macro-F1 lớn nhất; hòa giữ epoch sớm nhất |
| Prediction tie | Class ID nhỏ nhất |
| Aggregation | Mean crop softmax vectors theo image_id, rồi argmax |
| Effective batch | **32 ảnh nguồn** mỗi optimizer update; không phải 32 crops |
| Precision | FP32 |
| Thiết bị dự kiến | RTX 4060 Laptop, VRAM 8 GB; chưa xác minh khả dụng |

Cho phép crop microbatch phù hợp VRAM 8 GB. TV3 phải giữ mỗi ảnh có tổng trọng
số bằng nhau: trung bình CE các crop trong từng ảnh, rồi trung bình trên
effective batch 32 ảnh nguồn. Nếu chia crop qua microbatch/gradient accumulation,
không lấy mean mỗi microbatch rồi coi chúng có trọng số bằng nhau; không áp
trọng số `1 / parent_crop_count` hai lần. Ghi crop microbatch thực, cách gom
parent, accumulation/chuẩn hóa loss và cách xử lý batch cuối trong training
config/log trước khi chạy. Không tự chọn kích thước microbatch chưa đo.

`configs/tv2_w5_protocol.draft.json` ghi `seeds=[42]`, `max_candidate_runs=1`,
max epochs 50/patience 7 và các giá trị trên, nhưng **status vẫn DRAFT**,
`experiments=[]`, `model.selected_model=null`; reviewer TV2 ghi đúng xác nhận
có điều kiện trong chat 30/10, TV3/TV1 chưa có nguồn xác nhận; approval evidence
TV2 có trạng thái CONDITIONAL, TV3=null và effective_official_approval=false.
Các trường seed/budget/hyperparameter mô tả cấu hình được yêu cầu và bàn giao,
**không phải approval receipt hoàn tất hoặc quyền chạy chính thức**.
Không tự tạo tên reviewer/chữ ký hay experiment giả để vượt gate.

Trước official run: phải giải quyết B1 config byte chuẩn, B2 xác nhận thực tế
TV3 trên đúng bản đó, B3 gói source/pretrained/data-preflight có hash/commit để
kiểm implementation và điều kiện TV2. LR/SGD/momentum/WD/cosine/seed/epochs đã
được bàn giao, không yêu cầu đề xuất hoặc xác nhận lại các giá trị từ TV2.
Chỉ đăng ký model/experiment và chuyển APPROVED sau khi kiểm đủ các nguồn này.
Gate hiện tại chặn DRAFT trước khi đọc predictions; gate không tự kiểm tra đủ
mọi tham số huấn luyện mới, nên không coi việc qua gate là training-config
approval. Không chạy lượt thứ hai, kể cả đổi sang fallback, khi chưa có quyết
định ngân sách mới. Một seed không cho phép tuyên bố độ ổn định giữa seed.

B2 reference verification và API smoke train/fixture là công việc kiểm định,
không phải ngân sách huấn luyện ứng viên. TV2 không tự chiếm việc train TV3.

## 5. Runtime và điều kiện nhận bàn giao

Reference lần này: Windows11, Intel i7-13620H, 16 logical CPUs, RAM15,71 GiB;
Python3.12.14, torch2.8.0+cpu, torchvision0.23.0, Pillow12.2.0. Không có `.venv`
ở gốc; dùng venv3.12 có sẵn `outputs/w2_final_handoff/tv4_env/Scripts/python.exe`,
không thay môi trường. B2 FP32/eval/inference_mode, CPU threads4, crop batch32,
workers0, không drop_last. Đây là môi trường reference đã đo trước đó, không
phải thiết bị DINO. DINO dự kiến RTX 4060 Laptop 8 GB/FP32, effective batch
32 parent images, tối đa một training run. Smoke TV3 báo RTX4060Laptop/CUDA,
AMPfalse/TF32false, features32×384, forward4.632s và peak allocated299.583.488
bytes cho smoke. Đó không phải runtime đo mới của TV2 hoặc peak toàn training.
Cache extraction batch32crops khác effective batch32parents. READY nêu head
học cache, không gradient accumulation, giữ batch cuối; cần source kiểm chứng.
Smoke counter verified_source_images=0 không chứng minh full pixel/hash gate;
report preflight/sample IDs/hash receipts được dẫn chiếu chưa nhận. Không có
training hoặc load checkpoint mới trong lần review này.

Một lượt hợp lệ cần đầy đủ checkpoint/hash/bytes, train/val version và manifest
hash, class order, preprocessing, seed/config/train commit, log huấn luyện,
nguồn pretrained/version, runtime/thiết bị/bộ nhớ/batch/threads/thời gian,
predictions đủ manifest, fresh-process reload report và log có hash. Không nhận
một dòng PASS thiếu artifact. Sai SHA/ID/mapping/preprocessing, fallback model,
mất crop, metric không khớp hoặc dữ liệu mở rộng chưa gate: FAIL/BLOCKED, giữ
attempt cũ để điều tra; không sửa kết quả cho đạt.

`evaluate_w5_validation.py` chỉ audit artifact đã bàn giao; **không nạp DINO và
không chứng minh tác giả của approval**. Nó yêu cầu file config/log/reload thật
có SHA, recompute metrics và chỉ trả ARTIFACT_VERIFIED. TV2 phải kiểm tra nguồn
approval, nội dung log/config và chạy adapter tiến trình sạch khi có gói thật;
không suy diễn thành READY/Reviewer approved. B2 fresh-process/native-adapter
đã kiểm tra riêng, nhưng checkpoint B2 không embed run_id/git_commit và thiếu
original training log; inference tái lập PASS không hoàn thiện training provenance.

## 6. Bảo vệ Test và quyết định demo

Không dùng Test W4 để chọn checkpoint/hyperparameters/augmentation/preprocess/
threshold/model. Không chạy `evaluate_w4_test.py`. Dẫn kết quả W4 chỉ như lịch sử.
Các lệnh B2 W5, evaluator và pixel gate mới chỉ đọc train/val. Unit fixture có
nhãn `test` là dữ liệu tổng hợp kiểm tra phần mềm, không phải ảnh Test thực.

**Sai lệch vận hành đã ghi nhận:** đầu lượt đã gọi nhầm validator integrity
ảnh toàn snapshot rồi dừng bằng Ctrl+C. Log cuối ghi750/4000; số/ID ảnh đã decode
thực trước ngắt không xác định, scope có cả Test. Không xem ảnh, không forward
model/tính metric hay dùng đầu ra đó chọn mô hình; không có receipt PASS và
không gọi đó là pixel gate hoàn tất. Giữ log, thay bằng gate train/val đã PASS
3.400/3.400; xem `w5_evidence/attempt_01/deviations.json`. Không tuyên bố toàn
session chưa hề truy cập raster Test. Reviewer cần đối chiếu sai lệch này.

Giữ B2 làm fallback demo. Chỉ đề xuất DINO khi validation cùng dữ liệu và
reload/adapter đạt, có review; không thay checkpoint sản xuất TV4. GT-box
classifier metric khác end-to-end detector+classifier. MegaDetector đã dùng
SWG khi huấn luyện, nên demo SWG không phải đánh giá detector độc lập.
