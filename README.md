# CameraTrapML

Đồ án **Học máy và ứng dụng**: nhận dạng động vật từ ảnh bẫy camera tại Trường
Sơn, sử dụng dữ liệu SWG. Nhóm 4 thành viên. Bản tích hợp **tuần 5, ngày
03/11/2026** có dữ liệu khóa, DINOv3 linear probe, đối chứng B2, demo duyệt
ảnh, xử lý lô nhỏ và xuất CSV/JSON. Bốn phần đã được kiểm tra kỹ thuật.

Giảng viên đã cho thêm vài tuần; chưa có hạn nộp mới cụ thể. Kế hoạch ban đầu
6 tuần được giữ làm lịch sử; xem [ghi nhận lịch mới](docs/progress_integration_w5_2026-11-03.md).

## Mở web

Trên máy TV1 đã chuẩn bị môi trường và gói DINO, mở PowerShell tại thư mục repo:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765 --dino-package outputs/tv4/w5/intake_20261102/DINOv3_LP_run01 --dino-repo outputs/tv4/w5/dinov3_architecture
```

Mở **[http://127.0.0.1:8765](http://127.0.0.1:8765)** và giữ PowerShell đang chạy.
Dừng bằng `Ctrl+C`. Nếu cổng đã dùng, mở trang đang chạy hoặc dùng `--port 8766`
rồi truy cập đúng cổng. Đây là web cục bộ trên máy của bạn.

1. Chọn ảnh mẫu train hoặc **Nạp ảnh**.
2. Giữ **MegaDetector**, chọn **DINOv3_LP_run01** rồi bấm **Phân tích ảnh**.
   Trang vẫn khởi tạo bằng **B2**; chọn B2 nếu muốn thử mô hình đối chứng.
3. Xem box và top 3 từng vùng; điểm thấp chuyển **Cần kiểm tra**.
4. Điền người duyệt, sửa/xác nhận nhãn hoặc ghi chưa xác định/bỏ sót; **Lưu duyệt**
   trước khi **Xuất JSON**. Dự đoán gốc luôn được giữ riêng.

5. Chọn tối đa 10 ảnh trong **Lô nhỏ**; xem từng ảnh, lưu bản duyệt, rồi xuất
   **CSV đã lưu** hoặc **JSON lô đã lưu**. Bản nháp chưa lưu không được xuất.

Chỉ chạy B2: bỏ hai cờ `--dino-package` và `--dino-repo`. DINO chưa được cấu
hình sẽ bị vô hiệu hóa; ứng dụng không tự chuyển model khi suy luận lỗi.

**[Hướng dẫn chạy và checklist test](docs/run_and_test_w5.md)** ·
[Chi tiết adapter/lô/CSV](docs/tv4_w5_demo.md).

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
Để bật DINO trên máy khác, nhận ZIP checkpoint từ TV3, kiểm SHA và chuẩn bị
checkout kiến trúc theo [hướng dẫn W5](docs/run_and_test_w5.md). Trọng số không nằm trong Git.

## Kết quả hiện tại

| Mô hình | Dữ liệu đánh giá | Macro-F1 | Trạng thái |
| --- | --- | ---: | --- |
| B1: ResNet18 toàn ảnh | 600 ảnh validation | 56,25% | Mốc so sánh |
| **B2: ResNet18 crop** | 600 ảnh validation, 680 GT crop | **74,55%** | Đã khóa `b2_run01`, epoch 21 |
| **DINOv3 ViT-S/16 + linear head** | Cùng 600 ảnh validation, 680 GT crop | **84,44%** | Accuracy **84,50%**, đúng **507/600**; epoch 9 |
| **B2: Test chính thức** | 600 ảnh test, 680 GT crop | **72,63%** | Accuracy 73,00%, đúng 438/600 |
| B3: thử nghiệm trọng số lớp | Validation | Chưa chốt tái lập | **UNRESOLVED**, ngoài Test và demo |

Nguồn: [B1](reports/tv2/TV2_W3.md), [B2 validation](reports/tv4_w3_continuation/REPORT.md),
[B2 Test](reports/tv2/TV2_W4_TEST_EVALUATION.md), [giới hạn B3](reports/tv3/W4_FINAL_FIX.md).
[DINO và đối chứng](reports/tv2/TV2_W5_DINO_ACCEPTANCE_2026-11-02.md),
[kiểm tra độc lập W5](reports/review_w5_2026-11-02/REPORT.md).
DINO tăng 9,83 điểm phần trăm accuracy validation so với B2; **chưa đạt mục tiêu
88%**, chưa có test DINO độc lập. Các metric trên dùng **box ground truth**,
không phải điểm của toàn luồng detector + classifier.

Tốc độ phụ thuộc model, máy và số box; xem [log W5 cùng giới hạn đo](reports/tv4_w5/REPORT.md).
Số đo B2 tuần 4 được giữ ở [báo cáo cũ](reports/tv4_w4/REPORT.md), không dùng thay tốc độ DINO.

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
- W5 có 1.665 ứng viên train bổ sung mới ở mức metadata; chưa phát hành train
  mở rộng. 109 ảnh holdout ứng viên chưa đủ hỗ trợ 8 lớp; chưa có test mới.

## Bàn giao tuần 5

| Thành viên | Công việc đã tích hợp | Tài liệu |
| --- | --- | --- |
| TV1 | Manifest ứng viên, kiểm kê train/holdout, phần dữ liệu báo cáo | [Bàn giao](docs/handoff_tv1_w5.md) · [Báo cáo](reports/tv1_w5/REPORT.md) |
| TV2 | Protocol validation, đối chứng B2, nghiệm thu DINO | [Nghiệm thu](reports/tv2/TV2_W5_DINO_ACCEPTANCE_2026-11-02.md) · [Chương thực nghiệm](reports/tv2/W5_EXPERIMENT_CHAPTER.md) |
| TV3 | DINOv3 frozen backbone + head tám lớp, checkpoint và reload | [Gói cuối](reports/tv3/w5_final/DINOv3_LP_run01/README.md) · [Hướng dẫn](docs/handoff_tv3_w5.md) |
| TV4 | Adapter DINO, UI, lô nhỏ, CSV/JSON | [Hướng dẫn](docs/tv4_w5_demo.md) · [Báo cáo](reports/tv4_w5/REPORT.md) |

[Biên bản tích hợp tuần 5](docs/integration_week5.md) ghi commit, kiểm tra và giới hạn.
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
Môi trường CPU trên máy TV1 đã qua **440/440 tests** của bản kết hợp W5.
Môi trường training/replay GPU của TV3 được pin riêng trong `requirements-tv3-w5.txt`;
không cài chồng cả hai pin scikit-learn khác nhau vào một môi trường.

## Làm việc nhóm

`main` là bản tích hợp; mỗi người giữ một nhánh: TV1 `feat/metadata-split`,
TV2 `feat/baseline`, TV3 `feat/crop-classifier`, TV4 `feat/demo`.
Trước việc mới, đồng bộ `origin/main` theo [quy ước Git](CONTRIBUTING.md).

[Mục lục tài liệu](docs/README.md) · [Kiến trúc](docs/architecture.md) ·
[Hợp đồng JSON](docs/result_contract.md) · [Lịch GPU](docs/gpu_schedule.md) ·
[Nguồn SWG](https://lila.science/datasets/swg-camera-traps)
