# CameraTrapML

Đồ án **Học máy và ứng dụng**: nhận dạng động vật từ ảnh bẫy camera tại Trường
Sơn, sử dụng dữ liệu SWG. Nhóm 4 thành viên, lộ trình 6 tuần. Bản tích hợp đến
**tuần 4, ngày 25/10/2026** có dữ liệu khóa, B0/B1/B2, thử nghiệm B3 và demo duyệt ảnh.

## Mở web

Trên máy đã cài môi trường và trọng số, mở PowerShell tại thư mục repo:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765
```

Mở **[http://127.0.0.1:8765](http://127.0.0.1:8765)** và giữ PowerShell đang chạy.
Dừng bằng `Ctrl+C`. Nếu cổng đã dùng, mở trang đang chạy hoặc dùng `--port 8766`
rồi truy cập đúng cổng. Đây là web cục bộ trên máy của bạn.

1. Chọn ảnh mẫu train hoặc **Nạp ảnh**.
2. Giữ **MegaDetector + B2**, bấm **Phân tích ảnh**.
3. Xem box và top 3 từng vùng; điểm thấp chuyển **Cần kiểm tra**.
4. Điền người duyệt, sửa/xác nhận nhãn hoặc ghi chưa xác định/bỏ sót; **Lưu duyệt**
   trước khi **Xuất JSON**. Dự đoán gốc luôn được giữ riêng.

Chi tiết: [bàn giao demo tuần 4](docs/handoff_tv4_w4.md).

## Cài trên máy mới

Dùng Git và Python **3.12**. Máy đã có repo/môi trường thì không cần cài lại.

```powershell
git clone https://github.com/huyryan220806/Camera-Trap-ML.git
cd Camera-Trap-ML
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/prepare_tv4_demo.py
# Nhận checkpoint B2 từ TV3 và thay đường dẫn bằng file đã nhận:
.venv/Scripts/python.exe scripts/prepare_tv4_classifier.py --model B2 --source "D:/duong-dan/best_model.pt"
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765
```

B2 được bàn giao ngoài Git; script kiểm tra SHA trước khi bật. Trên máy TV1,
file nguồn là `outputs/tv3/b2/best_model.pt`. Chưa có trọng số thì chọn **Giả lập**
để thử giao diện; box/điểm khi đó là dữ liệu giả. Không cần tải 4.000 ảnh để
upload ảnh riêng. [Môi trường và dữ liệu](docs/environment.md).

## Kết quả hiện tại

| Mô hình | Dữ liệu đánh giá | Macro-F1 | Trạng thái |
| --- | --- | ---: | --- |
| B1: ResNet18 toàn ảnh | 600 ảnh validation | 56,25% | Mốc so sánh |
| **B2: ResNet18 crop** | 600 ảnh validation, 680 GT crop | **74,55%** | Đã khóa `b2_run01`, epoch 21 |
| **B2: Test chính thức** | 600 ảnh test, 680 GT crop | **72,63%** | Accuracy 73,00%, đúng 438/600 |
| B3: thử nghiệm trọng số lớp | Validation | Chưa chốt tái lập | **UNRESOLVED**, ngoài Test và demo |

Nguồn: [B1](reports/tv2/TV2_W3.md), [B2 validation](reports/tv4_w3_continuation/REPORT.md),
[B2 Test](reports/tv2/TV2_W4_TEST_EVALUATION.md), [giới hạn B3](reports/tv3/W4_FINAL_FIX.md).
Test B2 dùng **box ground truth**; không phải điểm của toàn luồng MegaDetector + B2.

Demo CPU Ryzen 5 7535HS, 4 threads, batch ảnh 1: mean **5,55 giây/ảnh khi có cache**,
lần đầu **18,08 giây**. Mẫu train nhỏ; xem [cấu hình và log](reports/tv4_w4/REPORT.md).

## Dữ liệu và giới hạn

- `comparison_v1`: **4.000 ảnh / 8 lớp**, train 2.800, validation 600, test 600;
  B1/B2 dùng cùng ảnh gốc, không giao nhau về chuỗi hoặc địa điểm.
- [Manifest](data/processed/comparison_v1/); ảnh local ở `data/images/swg_pilot_v2/`.
  Tải tiếp bằng `.venv/Scripts/python.exe scripts/resume_tv1_w2.py`.
  [Hướng dẫn dữ liệu](docs/handoff_tv1_w3.md).
- MegaDetector **MDv5a.0.1** đã dùng SWG khi huấn luyện; demo trên SWG không phải
  đánh giá detector độc lập. Softmax chưa hiệu chỉnh; ngưỡng review 0,70 là quy
  tắc demo. Điểm thấp không kết luận loài lạ; không có box không chứng minh ảnh trống.
- Mẫu được chọn/cân bằng có chủ đích, không đại diện phân bố tự nhiên của toàn
  SWG. Không mặc định cả 8 lớp đều có cùng tình trạng bảo tồn.
- Giữ nguyên nhãn/split/checkpoint đã khóa. Không chạy lại Test để chọn mô hình,
  ngưỡng hoặc sửa nhãn nhằm tăng điểm.

## Bàn giao tuần 4

| Thành viên | Công việc đã tích hợp | Tài liệu |
| --- | --- | --- |
| TV1 | Kiểm kê test và ví dụ lỗi dữ liệu | [Bàn giao](docs/handoff_tv1_w4.md) · [Báo cáo](reports/tv1_w4/REPORT.md) |
| TV2 | Khóa đánh giá và công bố Test B2 | [Kết quả](reports/tv2/TV2_W4_TEST_EVALUATION.md) · [Phân tích lỗi](reports/tv2/TV2_W4_ERROR_ANALYSIS.md) |
| TV3 | Phân tích B2/B3, sửa kiểm định và nạp checkpoint | [Bản sửa](reports/tv3/W4_FINAL_FIX.md) · [Quyết định](reports/tv3/TV3_W4_DECISION.md) |
| TV4 | Duyệt/sửa nhãn, ghi bỏ sót và đo tốc độ | [Bàn giao](docs/handoff_tv4_w4.md) · [Kiểm thử](reports/tv4_w4/REPORT.md) |

[Biên bản tích hợp tuần 4](docs/integration_week4.md) ghi commit, kiểm tra và giới hạn.
Báo cáo cũ giữ trạng thái tại thời điểm viết; xem biên bản cho trạng thái mới nhất.

## Cấu trúc và kiểm tra

```text
app/                    Giao diện web
src/                    Dữ liệu, mô hình, đánh giá và suy luận
scripts/                Chạy demo, tải/kiểm tra dữ liệu và thí nghiệm
configs/ · contracts/   Cấu hình, model lock và JSON Schema
data/processed/         Manifest và ánh xạ lớp đã khóa
experiments/            Cấu hình/kết quả thí nghiệm được theo dõi trong Git
docs/ · reports/        Hướng dẫn, bàn giao và bằng chứng
tests/                  Kiểm thử tự động
outputs/                Trọng số/cache/log local; không đưa lên Git
```

Để chạy toàn bộ kiểm thử, cài cả phụ thuộc TV2 và TV4:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-tv2.txt -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe scripts/validate_comparison.py --metadata-only --report outputs/comparison_audit.json
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Không dùng lệnh đánh giá Test chính thức như smoke test. Kiểm thử tự động dùng
fixture/thư mục tạm, không thay kết quả thí nghiệm đã khóa.

## Làm việc nhóm

`main` là bản tích hợp; mỗi người giữ một nhánh: TV1 `feat/metadata-split`,
TV2 `feat/baseline`, TV3 `feat/crop-classifier`, TV4 `feat/demo`.
Trước việc mới, đồng bộ `origin/main` theo [quy ước Git](CONTRIBUTING.md).

[Mục lục tài liệu](docs/README.md) · [Kiến trúc](docs/architecture.md) ·
[Hợp đồng JSON](docs/result_contract.md) · [Lịch GPU](docs/gpu_schedule.md) ·
[Nguồn SWG](https://lila.science/datasets/swg-camera-traps)
