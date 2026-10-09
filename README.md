# CameraTrapML

## TV2 – Week 2 – Baseline B0

- Task: **W2-02**.
- Model: ResNet18 pretrained ImageNet, phân loại toàn ảnh.
- Backbone được đóng băng; chỉ classifier cuối (`fc`) được huấn luyện.
- Số lớp: **8**.
- Lượt chạy thử: **128 train, 64 validation**.
- Best epoch: **4**.
- Validation Macro-F1: **0.3616866793337382**.
- Validation Macro-Precision: **0.46773504273504274**.
- Validation Macro-Recall: **0.375**.
- Validation accuracy: **0.375**.
- Checkpoint reload: **PASS**, sai khác 0 ở các metric chính.
- Test set used for model selection: **NO**.

Đây là baseline B0 trên tập thử nhỏ, không phải hiệu năng cuối của hệ thống. `configs/b0.yaml` là JSON hợp lệ theo YAML 1.2; lượt chạy chọn cố định 16 ảnh train và 8 ảnh validation mỗi lớp từ `pilot_v1.jsonl` bằng seed 42, giữ nguyên split của TV1 và không đọc ảnh test.

Tại thư mục gốc repo, dùng Python 3.12 và cài `requirements-tv2.txt`. Việc tải ảnh cần Internet. Trọng số ImageNet được torchvision tự tải vào cache khi khởi tạo B0; nếu cần cache trong workspace, đặt `TORCH_HOME` hoặc lưu file ResNet18 chính thức tại `data/images/torch/hub/checkpoints/resnet18-f37072fd.pth` như code huấn luyện.

```powershell
.venv/Scripts/python.exe scripts/prepare_b0_pilot.py
.venv/Scripts/python.exe scripts/train_b0.py --smoke
.venv/Scripts/python.exe scripts/train_b0.py
.venv/Scripts/python.exe scripts/validate_b0.py --checkpoint experiments/B0_run01/checkpoints/best_model.pth
```

Tệp chính:

- Training: [`scripts/train_b0.py`](scripts/train_b0.py)
- Validation: [`scripts/validate_b0.py`](scripts/validate_b0.py)
- Notebook: [`notebooks/TV2_W2_B0_Demo.ipynb`](notebooks/TV2_W2_B0_Demo.ipynb)
- Report: [`reports/tv2/TV2_W2.md`](reports/tv2/TV2_W2.md)

Các file `.py` là pipeline train/validation chính thức; file `.ipynb` dùng để trình bày và phân tích kết quả đã sinh. Config đã giải quyết, danh sách ảnh chọn/dùng, lỗi ảnh, log từng epoch và báo cáo validation nằm ở `experiments/B0_run01/`. Best checkpoint nằm ở `experiments/B0_run01/checkpoints/best_model.pth` (bị `.gitignore` bỏ qua nhưng phải được giữ cục bộ hoặc sao lưu riêng). Không chạy lại `prepare_b0_pilot.py` với config khác sau khi đã chọn checkpoint mà không tạo run ID mới.

Đồ án Học máy và ứng dụng: hỗ trợ nhận dạng động vật từ ảnh bẫy camera SWG tại Trường Sơn. Kế hoạch Word/Excel ở `plan_outputs` chỉ được lưu trên máy đã tạo, không nằm trong Git.

## Bàn giao tuần 1 của thành viên 2

- [Hướng dẫn bàn giao Baseline & Evaluation](docs/handoff_tv2_w1.md)
- [Đề cương thí nghiệm B0–B3](docs/experiment_protocol.md)
- [Notebook kiểm tra môi trường và metric](notebooks/TV2_baseline_evaluation.ipynb)

Phần TV2 dùng `data/processed/v1/class_map.json` và manifest v1 của TV1. Cài các thư viện bổ sung bằng `requirements-tv2.txt`; notebook và hình confusion matrix hiện chỉ kiểm tra trên dữ liệu giả, chưa phải kết quả của mô hình đã huấn luyện.

## Bàn giao tuần 1 của thành viên 4

- [Môi trường và kiểm tra cài đặt](docs/environment.md)
- [Cấu trúc dự án và sơ đồ luồng](docs/architecture.md)
- [Quy ước Git và kiểm tra chéo](CONTRIBUTING.md)
- [Hợp đồng JSON và cách xử lý kết quả](docs/result_contract.md)
- [Lịch dùng GPU chung](docs/gpu_schedule.md)
- [Checklist nghiệm thu cho TV2](docs/handoff_tv4_w1.md)

Các JSON trong `examples/results` là **dữ liệu giả lập**, không phải kết quả của mô hình đã huấn luyện. Tuần 1 chốt giao diện dữ liệu; chưa có ứng dụng web hoặc mô hình suy luận chạy thật.

Sau khi cài `requirements.txt`, kiểm tra bộ bàn giao mà không cần tải dữ liệu gốc hoặc GPU:

```powershell
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

## Bàn giao tuần 1 của thành viên 1

- **Báo cáo EDA:** [reports/eda/EDA_member1.md](reports/eda/EDA_member1.md)
- **Notebook:** [notebooks/01_metadata_eda.ipynb](notebooks/01_metadata_eda.ipynb)
- **Danh sách 8 lớp đề xuất:** [data/processed/v1/selected_classes.json](data/processed/v1/selected_classes.json)
- **Manifest chính:** `data/processed/v1/manifest_v1.jsonl` gồm 31.589 ảnh đủ điều kiện so sánh toàn ảnh/vùng cắt.
- **Manifest thử:** `data/processed/v1/pilot_v1.jsonl` gồm 4.000 ảnh, giữ nguyên split của manifest chính.
- **Seed và kiểm tra rò rỉ:** `configs/split_v1.json`, `data/processed/v1/provenance.json`, `data/processed/v1/audit.json`.

Đây là kết quả xử lý **metadata**. Chưa tải ảnh, xác minh URL, kiểm tra ảnh lỗi thực tế, kiểm tra hash nội dung hay xác nhận chất lượng box bằng mắt. Danh sách lớp là đề xuất nghiên cứu; chưa xác nhận tình trạng bảo tồn của từng loài.

## Cách giải thích phần việc của TV1

1. **Ảnh:** một file ảnh. **Chuỗi:** nhiều ảnh của một lần kích hoạt camera. **Địa điểm:** vị trí đặt camera. **Box:** một vùng đối tượng trong ảnh; một ảnh có thể có nhiều box.
2. Đọc và đếm metadata trước. Không lấy số ảnh làm số cá thể, không coi mọi annotation là một box.
3. Giữ dấu vết nhãn gốc, đánh dấu nhãn không dùng được và chuẩn hóa cách viết cùng nhãn.
4. Chọn lớp theo số ảnh, số chuỗi và số địa điểm; kiểm tra riêng lượng ảnh có box vì nhóm cần so sánh B1/B2.
5. Chia theo địa điểm để ảnh cùng bối cảnh không xuất hiện cả trong train lẫn test. Seed làm kết quả có thể lặp lại, nhưng seed không tự ngăn rò rỉ.
6. Bàn giao manifest cố định cho TV2 và TV3. Không để mỗi người tự chia ngẫu nhiên ảnh.

## Chạy lại trên Windows

Yêu cầu Python 3.12 và kết nối mạng ở bước tải metadata. Không cần GPU cho phần tuần 1. Metadata nén khoảng 68 MB; cơ sở dữ liệu và báo cáo cần thêm dung lượng đĩa. Dữ liệu JSON được đọc tuần tự để tránh nạp toàn bộ vào RAM.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/download_metadata.py
.venv/Scripts/python.exe scripts/prepare_swg.py
.venv/Scripts/python.exe scripts/split_swg.py
.venv/Scripts/python.exe scripts/report_eda.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Lần chạy hiện tại đã hoàn tất. Nếu cơ sở dữ liệu đã tồn tại, dùng `scripts/prepare_swg.py --stats` để đọc lại và xuất thống kê. Không chạy ingest đè lên dữ liệu đang có. Nếu ingest bị gián đoạn, đổi tên cơ sở dữ liệu chưa hoàn chỉnh trước khi chạy lại.

Manifest v1 không bị ghi đè. Để kiểm tra tái lập hoặc tạo phiên bản mới:

```powershell
.venv/Scripts/python.exe scripts/split_swg.py --output data/processed/repro_check
```

Nếu đổi quy tắc chọn lớp, cấu hình hoặc seed, tạo thư mục v2 và lưu cấu hình tương ứng; không tự thay split sau khi đã đánh giá mô hình. Muốn mở notebook tương tác có thể chọn môi trường `.venv` trong VS Code/Jupyter; các script và báo cáo không phụ thuộc Jupyter.

## Quy ước manifest

Mỗi dòng JSONL là **một ảnh**, gồm:

| Trường | Ý nghĩa |
|---|---|
| `image_id`, `file_name`, `url` | ID nguồn, đường dẫn và URL dự kiến để tải |
| `seq_id`, `sequence_id` | Cùng một mã chuỗi nguồn; hai tên để tiện tích hợp |
| `location`, `country`, `datetime` | Địa điểm, quốc gia theo đường dẫn và thời điểm trong metadata |
| `label`, `class_id` | Nhãn chuẩn hóa và ID từ `class_map.json` |
| `split` | `train`, `val` hoặc `test` |
| `width`, `height` | Kích thước ảnh trong metadata |
| `image_annotation_sequence_level` | Nhãn ảnh gốc có được gán ở cấp chuỗi hay không |
| `boxes` | Danh sách box cấp ảnh, gồm annotation ID, nhãn và tọa độ pixel `[x,y,w,h]` |

Các file `train.jsonl`, `val.jsonl`, `test.jsonl` là tập con của manifest chính. Mọi crop của một ảnh phải kế thừa split ảnh gốc. Pilot chỉ dùng để thử pipeline; không dùng kết quả trên pilot test để chọn mô hình hay ngưỡng.

## Nguyên tắc chọn lớp và đánh giá

Manifest chính dùng ảnh public, không bị đánh dấu corrupt, đủ thông tin, đúng một nhãn loài đã chọn và tất cả box hợp lệ đồng ý với nhãn đó. Vì tập ảnh có box được gán nhãn chọn lọc, cần ghi rõ kết quả trên tập này không đại diện ngẫu nhiên cho toàn bộ SWG.

Mục tiêu chia 70/15/15 theo địa điểm; dùng seed 42 và 2.000 hoán vị để giảm lệch tỷ lệ ảnh/chuỗi từng lớp. Không dùng độ chính xác mô hình để tìm split thuận lợi. Mỗi lớp có ít nhất 10 chuỗi và 2 địa điểm mỗi tập; đây là ngưỡng khả thi, không bảo đảm kết quả lớp ít mẫu có độ bất định thấp.

**Điểm cần nhớ:** toàn bộ annotation nhãn ảnh trong bản metadata tải về được đánh dấu ở cấp chuỗi. Box cấp ảnh là nguồn bổ sung quan trọng; vẫn phải kiểm tra trực quan mẫu ảnh trước khi nhóm huấn luyện chính thức.

## Việc tiếp theo của TV1 và TV3

- Kiểm tra mẫu ảnh từ nhiều chuỗi và địa điểm của mỗi lớp, ưu tiên train/validation để khảo sát và phát triển.
- Ghi ảnh thiếu, file lỗi, box sai vào biên bản; không sửa nhãn chỉ để tăng điểm mô hình.
- Khi tải ảnh, kiểm tra SHA-256 và trùng nội dung gần giống. Nếu phát hiện rò rỉ thật, sửa ở phiên bản dữ liệu mới và ghi rõ nguyên nhân.
- Đối chiếu tên khoa học và tình trạng bảo tồn bằng nguồn chuyên môn trước khi gọi các lớp là loài quý hiếm.

## Nguồn

SWG (2021): Northern and Central Annamites Camera Traps 2.0. IUCN SSC Asian Wild Cattle Specialist Group's Saola Working Group. Dataset.

- [Trang SWG trên LILA](https://lila.science/datasets/swg-camera-traps)
- [Quy ước COCO Camera Traps](https://github.com/agentmorris/MegaDetector/blob/main/megadetector/data_management/README.md#coco-camera-traps-format)

Nguồn tải, thời điểm tải, ETag và SHA-256 nằm trong `data/raw/sources.json` và bản sao tại `data/processed/v1/provenance.json`.
