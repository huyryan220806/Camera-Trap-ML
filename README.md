#  Camera Trap Wildlife Crop Classifier

Dự án phân tích và phân loại động vật hoang dã từ ảnh bẫy camera (camera trap) sử dụng dataset **SWG Camera Traps** (Southeast Asia Wildlife Group) từ LILA BC.

##  Mô tả

Notebook này thực hiện pipeline tiền xử lý dữ liệu ban đầu cho bài toán phân loại động vật từ ảnh bẫy camera, bao gồm:

1. **Đọc & phân tích dữ liệu JSON** — Nạp metadata bounding box với nhãn loài, xây dựng các dictionary tra cứu nhanh theo `image_id`, `category_id`.

2. **Kiểm tra chất lượng dữ liệu** — Phát hiện và phân loại các lỗi:
   - Ảnh bị đánh dấu `corrupt`
   - Bản ghi thiếu trường `bbox` (chỉ có nhãn cấp ảnh)
   - Bounding box lỗi hình học (kích thước ≤ 0, tọa độ tràn mép ảnh)
   - Ảnh chứa nhiều loài khác nhau

3. **Trực quan hoá mẫu** — Tải ảnh từ Google Cloud Storage và vẽ bounding box kiểm tra tính đúng đắn của nhãn.

4. **Lấy mẫu đa dạng theo địa điểm** — Chọn 10 ảnh hợp lệ / loài cho 8 loài mục tiêu, lấy xoay vòng từ các `location` độc lập để tối đa hoá sự đa dạng. Kiểm tra trùng lặp bằng SHA-256.

##  8 Loài mục tiêu

| Loài (tiếng Anh) | Loài (tiếng Việt) |
|---|---|
| `large_antlered_muntjac` | Mang lớn |
| `annamite_striped_rabbit` | Thỏ vằn Trường Sơn |
| `sambar` | Nai |
| `chinese_serow` | Sơn dương |
| `common_palm_civet` | Cầy vòi hương |
| `masked_palm_civet` | Cầy vòi mốc |
| `silver_pheasant` | Gà lôi trắng |
| `eurasian_wild_pig` | Lợn rừng |

##  Dataset

- **Tên**: SWG Camera Traps (Southeast Asia Wildlife Group)
- **Nguồn**: [LILA BC](https://lila.science/datasets/swg-camera-traps)
- **File metadata**: `swg_camera_traps.bounding_boxes.with_species.json`
- **Quy mô**:
  - Tổng số ảnh: 120,321
  - Tổng số loài: 121
  - Tổng số nhãn (bounding boxes): 133,837

##  Cấu trúc thư mục

```
Camera-Trap-ML/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   └── crop_classifier_eda.ipynb    # Notebook phân tích & tiền xử lý
├── scripts/                         # Các file xử lý và thống kê (chuẩn bị dữ liệu)
├── requirements.txt                 # Thư viện Python cần thiết
└── README.md                        # Tài liệu dự án
```

> **Lưu ý**: File dataset `swg_camera_traps.bounding_boxes.with_species.json` (~72.5 MB) không được commit vào repo. Tải về từ [LILA BC](https://lila.science/datasets/swg-camera-traps) và đặt cùng thư mục với notebook trước khi chạy.

##  Cách chạy

### 1. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### 2. Chuẩn bị dữ liệu

Tải file metadata từ LILA BC và đặt vào cùng thư mục với notebook:

```
swg_camera_traps.bounding_boxes.with_species.json
```

Các bước xử lý môi trường dự án bằng các scripts chuẩn hóa:
```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/download_metadata.py
.venv/Scripts/python.exe scripts/prepare_swg.py
.venv/Scripts/python.exe scripts/split_swg.py
.venv/Scripts/python.exe scripts/report_eda.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

### 3. Chạy notebook phát triển (TV3)

Mở `notebooks/crop_classifier_eda.ipynb` trong Jupyter Notebook hoặc Google Colab rồi chạy tuần tự các cell.

> **Lưu ý**: Notebook tải ảnh trực tiếp từ Google Cloud Storage, cần kết nối Internet. Sử dụng GPU (T4) trên Google Colab để xử lý nhanh hơn.

##  Kết quả kiểm tra chất lượng dữ liệu ban đầu

| Loại lỗi | Số lượng |
|---|---|
| Ảnh đánh dấu hỏng (`corrupt=True`) | 0 |
| Bản ghi không có trường `bbox` | 32,178 |
| Bounding box lỗi hình học | 205 |
| Ảnh có từ 2 loài trở lên | 0 |

## 🔧 Công nghệ sử dụng

- Python 3.x
- Google Colab (GPU T4)
- Pandas, NumPy
- Pillow (PIL)
- Matplotlib
- ImageHash
- Requests

##  Nhóm tác giả & Bàn giao (W1)

**Môn học**: Học máy và ứng dụng - Trường Đại học Văn Lang (VLU)

### Bàn giao của TV1
- **Báo cáo EDA:** `reports/eda/EDA_member1.md`
- **Notebook:** `notebooks/01_metadata_eda.ipynb`
- **Danh sách 8 lớp đề xuất:** `data/processed/v1/selected_classes.json`
- **Manifest chính:** `data/processed/v1/manifest_v1.jsonl`
- **Seed và kiểm tra rò rỉ:** `configs/split_v1.json`, `data/processed/v1/provenance.json`, `data/processed/v1/audit.json`.

### Bàn giao của TV3
- Notebook phát triển Crop Classifier EDA (`notebooks/crop_classifier_eda.ipynb`)
- Tích hợp pipeline tiền xử lý chung của nhóm vào EDA.

## Nguồn tham khảo

SWG (2021): Northern and Central Annamites Camera Traps 2.0. IUCN SSC Asian Wild Cattle Specialist Group's Saola Working Group. Dataset.

- [Trang SWG trên LILA](https://lila.science/datasets/swg-camera-traps)
- [Quy ước COCO Camera Traps](https://github.com/agentmorris/MegaDetector/blob/main/megadetector/data_management/README.md#coco-camera-traps-format)
