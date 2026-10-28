# TV2 W5 validation protocol

**DRAFT — chờ TV3 xác nhận trước thử nghiệm ứng viên chính thức.** Lập theo kế
hoạch cập nhật 28/10/2026; thực hiện từ 28 sang 29/10 giờ Việt Nam. Lịch W5
28/10–03/11 là đề xuất. TV2 không phê duyệt thay nhóm và không thực hiện W6.

## Nguồn và phạm vi

Nền tích hợp: `60516f51fccbb85e6e266a022d94ea90d2239a11` (main và nhánh TV2
trên origin lúc bắt đầu). TV1 W5: `9abc9c5` trên `feat/metadata-split`, được đọc
và chạy verify-only trong snapshot riêng, chưa merge vào nhánh TV2. TV3 tại
`60516f5` chưa có gói DINO; TV4 PR #8 mở tại
`fef2511b571b23be3d4e2cf6c1ccedd659097b6f`. PR #7 đã merge ngày 25/10.

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

Ứng viên ưu tiên theo plan là DINOv3 ViT-S/16; dự phòng DINOv2 ViT-S/14 phải
ghi đúng kiến trúc thực tế. **Chưa nhận model/pretrained/checkpoint/version,
pooling/head, preprocessing, config hoặc adapter**, nên các trường đó là N/A.
TV3 phải bàn giao giá trị chính xác và hash, không kế thừa preprocessing B2
theo giả định. TV2 không viết adapter DINO bằng cách đổi tên ResNet.

## 3. Dự đoán và metric

Tính softmax từng crop, trung bình đủ vector tám lớp của **mọi** crop cùng
`image_id`, rồi argmax. Không trung bình nhãn, majority vote, mean logits, chọn
crop dễ hoặc lọc confidence. Dự đoán hòa vector chọn class ID nhỏ nhất (kế
thừa B2; đề xuất dùng cùng rule cho DINO).

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

Đề xuất: chọn macro-F1 validation cao nhất, hòa chính xác giữ epoch sớm nhất;
argmax hòa chọn ID nhỏ nhất; seed đầu42 theo hướng TV3. Không đổi sau khi xem
kết quả. Chưa chốt tie giữa ứng viên/seed hoặc ngân sách số lượt/epoch/GPU-hour.
Không tuyên bố ưu thế ổn định từ một seed; chưa có seed DINO hợp lệ để phân tích.

`configs/tv2_w5_protocol.draft.json`: status DRAFT, `seeds=[]`,
`max_candidate_runs=null`, `experiments=[]`, reviewer TV3/TV1 chưa xác nhận.
Seed42/rule hòa là **đề xuất, chưa phê duyệt W5**. TV3 xác nhận qua PR hoặc
receipt có nguồn truy vết trước khi đăng ký lượt chính thức. Chỉ sửa thành
APPROVED sau xác nhận thật. Gate CLI đã kiểm tra từ chối DRAFT trước khi đọc
file dự đoán; không tạo prediction giả để thử DINO.

B2 reference verification và API smoke train/fixture là công việc kiểm định,
không phải ngân sách huấn luyện ứng viên. TV2 không tự chiếm việc train TV3.

## 5. Runtime và điều kiện nhận bàn giao

Reference lần này: Windows11, Intel i7-13620H, 16 logical CPUs, RAM15,71 GiB;
Python3.12.14, torch2.8.0+cpu, torchvision0.23.0, Pillow12.2.0. Không có `.venv`
ở gốc; dùng venv3.12 có sẵn `outputs/w2_final_handoff/tv4_env/Scripts/python.exe`,
không thay môi trường. B2 FP32/eval/inference_mode, CPU threads4, crop batch32,
workers0, không drop_last. DINO runtime/budget: N/A chờ TV3.

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
