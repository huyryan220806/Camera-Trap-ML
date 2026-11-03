# Cấu trúc dự án và sơ đồ luồng

## Cấu trúc hiện có đến tuần 5

```text
Camera-Trap-ML/
  app/                     Web HTML/CSS/JavaScript
  src/                     Dữ liệu, mô hình, đánh giá và demo
  configs/                 Cấu hình split, model registry và model lock
  contracts/               JSON Schema cho kết quả suy luận
  coordination/            Tài nguyên và lượt đăng ký GPU
  data/processed/          v1, v2 và comparison_v1 đã khóa
  docs/                    Hướng dẫn và checklist bàn giao
  examples/results/        Kết quả giả lập cho TV2, TV3, TV4
  notebooks/               Notebook EDA
  reports/                 EDA, bàn giao từng thành viên và bằng chứng kiểm thử
  experiments/             Cấu hình và kết quả các lượt huấn luyện
  scripts/                 Demo, xử lý dữ liệu, huấn luyện và kiểm định
  tests/                   Kiểm thử tự động
  requirements.txt         Phụ thuộc của phần đã triển khai
```

Các thư mục local `data/raw`, `data/interim`, `data/images`, `.venv`, `outputs`,
`runs` không được push. `outputs` chứa weights/cache và nhật ký duyệt. Các file
trọng số `.pt/.pth/.ckpt` không đưa lên Git dù nằm trong thư mục thí nghiệm.

## Luồng dữ liệu nghiên cứu đã triển khai

```mermaid
flowchart LR
  A[Metadata SWG] --> B[TV1 kiểm kê và chuẩn hóa nhãn]
  B --> C[Kiểm tra box và chọn lớp]
  C --> D[Chia theo location với seed 42]
  D --> E[Manifest v1 và class map]
  E --> V[Tải và kiểm tra pilot v2]
  V --> W[Khóa comparison_v1]
  W --> F[TV2 B1 dùng toàn ảnh]
  W --> G[TV3 B2 dùng vùng cắt GT]
  F --> H[Đánh giá trên cùng tập ảnh]
  G --> H
  W --> I[DINOv3 backbone dong bang va linear head]
  I --> H
```

comparison_v1 gồm 4.000 ảnh với split 2.800/600/600; B1/B2 dùng cùng ảnh gốc.
B2 đã khóa và đã đánh giá Test; B3 vẫn thăm dò, chưa tái lập khớp hoàn toàn.
GT boxes dùng trong đánh giá classifier khác với box do detector tạo khi chạy
demo. Nhãn thật trong manifest không đi vào demo để quyết định dự đoán.
DINO W5 dùng cùng train/validation và GT crops, chọn bằng macro-F1 cấp ảnh;
chưa có Test DINO độc lập. Cache feature phục vụ linear probe, khác cache
model của ứng dụng. Dữ liệu mở rộng W5 mới là ứng viên metadata.

## Luồng ứng dụng đã triển khai

```mermaid
flowchart TD
  A[Nhận ảnh và cấp request_id] --> B{Đọc ảnh được không}
  B -->|Không| E[error với mã lỗi đọc ảnh]
  B -->|Có| C[Phát hiện vùng động vật]
  C -->|Lỗi detector| E2[error với mã lỗi mô hình]
  C --> D{Có box đạt ngưỡng không}
  D -->|Không| N[no_detection và cần kiểm tra]
  D -->|Có| F[Cắt từng box và phân loại]
  F -->|Lỗi classifier| E3[error và không công bố kết quả một phần]
  F --> G{Mọi top 1 đạt ngưỡng duyệt}
  G -->|Có| O[ok và lưu gợi ý loài]
  G -->|Không| R[needs_review và giữ top 3]
  O --> V[Kiểm tra schema và quy tắc dữ liệu]
  R --> V
  N --> V
  E --> V
  E2 --> V
  E3 --> V
  V --> U[Lưu original và hiển thị kết quả]
  U --> R2[Người dùng duyệt từng box và ghi bỏ sót]
  R2 --> J[Nhật ký revision riêng và xuất JSON/CSV]
```

`no_detection` không chứng minh ảnh trống; `ok` chỉ là đạt ngưỡng demo. Mô hình
mặc định là MDv5a.0.1 + B2, top 3 riêng từng box. Cache model trong RAM, batch
crop tối đa 8, score chưa hiệu chỉnh. B0/B1 và Giả lập vẫn dùng được cho kiểm thử.
DINOv3 được bật tường minh bằng package/repo đúng pin, dùng resize256 và
linear head8lớp, CPU FP32; lỗi không tự chuyển sang B2. Lô nhỏ tối đa10ảnh
được hàng đợi frontend gửi tuần tự qua API ảnh đơn.

Mỗi phiên có `inference.json` bất biến và `events.jsonl` bổ sung từng lần duyệt.
Sửa nhãn không thay original hoặc dữ liệu khóa. Điểm thấp/không rõ loài được
chuyển cần kiểm tra, không tự nhận dạng loài lạ. Xem [hợp đồng JSON](result_contract.md)
và [bàn giao TV4](handoff_tv4_w4.md).

## Ranh giới tích hợp

| Bên cung cấp | Bên nhận | Định dạng |
|---|---|---|
| TV1 | TV2 và TV3 | Manifest JSONL, class_map.json, location_split.json |
| TV2 và TV3 | TV4 | Checkpoint, preprocessing, class map/version và kết quả theo schema |
| TV4 | Giao diện và xuất file | JSON phiên duyệt, wrapper JSON lô và CSV từ phiên đã lưu |
| Người kiểm tra | Nhóm | Nhận xét trên PR và checklist nghiệm thu |

Model ID, ngưỡng, ánh xạ nhãn và preprocessing đi cùng checkpoint/registry.
Web xử lý một ảnh mỗi request. Benchmark chạy tuần tự, lưu từng job có trạng
thái, phần cứng, cỡ lô và thời gian; resume không bỏ qua lỗi hoặc chạy trùng job.
Queue/nháp W5 ở RAM của tab, không tự khôi phục khi reload; phiên đã lưu nằm
ở server. Xem [hướng dẫn chạy/test](run_and_test_w5.md).
