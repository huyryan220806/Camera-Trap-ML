# TV2 – W2-02 – Baseline B0

Ngày chạy: 08/10/2026. Nhánh duy nhất có thay đổi: `feat/baseline`. Audit trước khi sửa code: [W2-02_pre_implementation_audit.md](W2-02_pre_implementation_audit.md).

## Dataset

- Manifest nguồn: `data/processed/v1/pilot_v1.jsonl` của TV1, SHA-256 `e014967e8ecdda18ea7468fba2a7312973b4eec468e61a3faabfd84169a75f8f`.
- Dataset root ảnh gốc: `data/images/`. Tải theo đúng `url` và lưu theo `file_name` trong manifest. Không dùng ảnh vẽ bbox/crop của TV3.
- Pilot v1 có 2.800 train, 600 validation, 600 test. Do máy chỉ có CPU và ảnh gốc chưa có sẵn, lượt chạy thử này chọn cố định 16 train và 8 validation mỗi lớp từ pilot theo SHA-256 của `seed:image_id`. Danh sách ID chính xác ở `experiments/B0_run01/selected_train.jsonl` và `selected_val.jsonl`; không tạo lại split và không chọn bằng nhãn/metric test.
- Số ảnh thực sự dùng: **128 train, 64 validation**, đủ 8 lớp (16 và 8 ảnh/lớp). 192/192 ảnh tải và giải mã được; 0 file thiếu/hỏng, `image_errors.json` rỗng. Các dòng dùng huấn luyện/đánh giá đã đối chiếu nguyên vẹn với pilot v1; train/validation không trùng ID.
- Class mapping: `data/processed/v1/class_map.json`: `0=large_antlered_muntjac`, `1=annamite_striped_rabbit`, `2=sambar`, `3=chinese_serow`, `4=common_palm_civet`, `5=masked_palm_civet`, `6=silver_pheasant`, `7=eurasian_wild_pig`.
- **Test used for model selection: NO.** Không tải ảnh test, không chạy suy luận hay tính metric test. Con số 600 test ở trên là metadata pilot đã bàn giao, chỉ để mô tả dataset.

## Model và tiền xử lý

- ResNet18 `ResNet18_Weights.DEFAULT` pretrained ImageNet-1K; phân loại **toàn ảnh**. Đóng băng mọi tham số backbone và giữ BatchNorm ở chế độ eval; thay `fc` bằng `Linear(512, 8)`.
- Tổng tham số: **11.180.616**; trainable chỉ `fc.weight` và `fc.bias`: **4.104**; frozen: **11.176.512**.
- Train: `Resize(256) → RandomCrop(224) → RandomHorizontalFlip(0.5) → ColorJitter(0.2,0.2,0.1,0.05) → ToTensor → ImageNet Normalize`.
- Validation: `Resize(256) → CenterCrop(224) → ToTensor → ImageNet Normalize`, không có augmentation ngẫu nhiên.

## Configuration và môi trường thực chạy

- Config gốc: `configs/b0.yaml` (cú pháp JSON hợp lệ theo YAML 1.2). Config đã giải quyết và hash dữ liệu: `experiments/B0_run01/config.yaml`.
- Seed **42** cho `random`, NumPy, PyTorch và CUDA nếu có; `cudnn.deterministic=True`, `cudnn.benchmark=False`.
- Adam, learning rate **0.001**, weight decay **0.0001**, batch size **32**, CrossEntropyLoss, tối đa **30 epochs**, early stopping patience **5**, không scheduler. Chọn best bằng **validation macro-F1**; macro precision/recall và F1 tính đủ 8 lớp, `zero_division=0` theo mã W1-02.
- Thiết bị: **CPU**. Python **3.14.3**, PyTorch **2.13.0+cpu**, torchvision **0.28.0+cpu**, CUDA không khả dụng. Commit gốc `fb51b41574d7df8c812a2aa26b8a4664be791b7a` được lưu trong config.
- Môi trường thực chạy mới hơn bộ phiên bản ghim trong `requirements-tv2.txt` dành cho Python 3.12; cần dùng phiên bản ghi trong run config khi muốn đối chiếu bit-level.

## Kết quả validation thật

| Chỉ số | Giá trị |
|---|---:|
| Best epoch | 4 |
| Train loss tại best epoch | 1.737651288509369 |
| Validation loss tại best epoch | 1.7887232899665833 |
| Macro-F1 | 0.3616866793337382 |
| Macro-Precision | 0.46773504273504274 |
| Macro-Recall | 0.375 |
| Accuracy | 0.375 |

Train chạy 9 epoch rồi early stopping. Log từng epoch: `experiments/B0_run01/logs/train_log.csv`. Metric từng lớp và confusion matrix: `experiments/B0_run01/results/val_metrics.json`, `confusion_matrix.png`; đường học: `learning_curves.png`. Đây là metric tính từ dự đoán trên **64 ảnh validation thật**, không phải dữ liệu giả trong notebook tuần 1.

## Checkpoint và reload

- File thật: `experiments/B0_run01/checkpoints/best_model.pth`.
- Dung lượng đã xác minh trước khi commit: **44.837.567 bytes**. Chứa toàn bộ `model_state_dict`, optimizer state, epoch, best validation macro-F1, class mapping hai chiều, num_classes, model, pretrained source, frozen flag, seed và config.
- Sau training, mô hình cũ được giải phóng; một ResNet18 mới khởi tạo với `weights=None` và được nạp toàn bộ state dict từ checkpoint. Chạy lại validation 64 ảnh: macro-F1 **0.3616866793337382**, precision **0.46773504273504274**, recall **0.375**, accuracy **0.375**. Sai khác tuyệt đối với metric khi lưu: **0** cho cả bốn chỉ số. Lệnh `scripts/validate_b0.py` độc lập cũng **PASS** với cùng giá trị.
- Chi tiết kiểm tra và SHA-256 checkpoint: `experiments/B0_run01/results/reload_validation.json`. File `.pth` được `.gitignore` bỏ qua theo quy ước Git của nhóm; phải giữ/copy artifact này riêng khi chuyển máy, không chỉ lấy các file Git.

## Chạy lại

Tại thư mục gốc repo, với Python và dependencies phù hợp:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-tv2.txt
.venv/Scripts/python.exe scripts/prepare_b0_pilot.py
.venv/Scripts/python.exe scripts/train_b0.py --smoke
.venv/Scripts/python.exe scripts/train_b0.py
.venv/Scripts/python.exe scripts/validate_b0.py --checkpoint experiments/B0_run01/checkpoints/best_model.pth
```

Lệnh `prepare_b0_pilot.py` cần Internet để tải ảnh public trong manifest. Khi chạy lại trên cùng máy, ảnh đã có sẽ được kiểm tra và dùng lại. `--smoke` đã PASS: load dataset, một batch train, forward/backward, batch validation và save/load checkpoint tạm. Toàn bộ **29 unittest trên nhánh TV2** đạt khi có `ijson` và thư mục TEMP có quyền ghi. Lệnh provenance bổ sung đã xác nhận các dòng train/validation giống pilot gốc, không trùng ID, đủ 8 lớp và 0 ảnh lỗi.

Notebook trình bày kết quả: `notebooks/TV2_W2_B0_Demo.ipynb`. Notebook đọc artifact đã có, trực quan hóa dữ liệu/metric và kiểm tra lại checkpoint trên 64 ảnh validation; không train lại B0 và không đọc test. Run All đã **PASS** với 22/22 code cells, 0 lỗi. Các script `.py` ở trên vẫn là pipeline train/validation chính thức; notebook dùng để trình bày và phân tích.

## Phụ thuộc và giới hạn

- TV1 `origin/feat/metadata-split`: class map, pilot/manifest v1, seed và split theo địa điểm. Các file này đã có trên nhánh TV2, không copy/chỉnh nhánh TV1.
- TV4 `origin/feat/demo`: cấu trúc dự án, cách lưu ảnh và quy tắc không commit weights. TV3 `origin/feat/crop-classifier` chỉ được đọc để xác nhận ranh giới B0 toàn ảnh; không dùng crop hoặc ảnh bbox của TV3. `origin/main` đã được fetch và đọc trước implementation.
- Lượt này chỉ **192 ảnh trong 3.400 ảnh train+validation của pilot**, không phải đánh giá trên toàn pilot hay manifest v1 31.589 ảnh. Validation 8 ảnh/lớp có độ bất định lớn; không diễn giải số liệu này là hiệu năng triển khai hoặc so sánh trực tiếp với B1/B2 tương lai. Khi có tài nguyên, tạo run ID mới để train trên tập lớn hơn, giữ nguyên split TV1 và vẫn chỉ chọn checkpoint bằng validation.
- Không có GPU/CUDA trên môi trường chạy. Không làm B1/B2 và không dùng test để điều chỉnh bất kỳ quyết định mô hình nào.
