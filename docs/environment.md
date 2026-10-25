# Môi trường phát triển

## Cài đặt cho bản tích hợp tuần 4

Cần Git và Python 3.12. Bộ cài dưới đây gồm phụ thuộc dữ liệu, đánh giá và demo,
đủ để chạy toàn bộ unittest trên CPU. Giao diện dùng HTML/JavaScript và HTTP
server Python; không cần Node, Streamlit hoặc CUDA để mở web.

```powershell
git clone --branch main https://github.com/huyryan220806/Camera-Trap-ML.git
cd Camera-Trap-ML
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-tv2.txt -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Với repo đã clone, dùng `git fetch origin` và chuyển branch sau khi đã commit công việc hiện tại; không clone chồng lên thư mục đang có dữ liệu.

Chỉ mở demo: cài `requirements-tv4.txt`. Chỉ xử lý metadata/JSON: dùng
`requirements.txt`. Hai lựa chọn này không thay thế bộ phụ thuộc đầy đủ khi
chạy toàn bộ test. `check_environment.py` kiểm tra các gói chung; không xác nhận
GPU, checkpoint hay khả năng inference thật.

Không cần kích hoạt venv nếu gọi trực tiếp `.venv/Scripts/python.exe`. Trên Linux/macOS, thay bằng `.venv/bin/python`. Trong VS Code, chọn interpreter thuộc `.venv`; mở notebook có thể cần cài thêm `ipykernel` trong chính môi trường đó.

## Chuẩn bị và mở web

```powershell
.venv/Scripts/python.exe scripts/prepare_tv4_demo.py
.venv/Scripts/python.exe scripts/prepare_tv4_classifier.py --model B2 --source "D:/duong-dan/best_model.pt"
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765
```

Thay đường dẫn bằng B2 nhận từ TV3; trên máy TV1 là
`outputs/tv3/b2/best_model.pt`. Script giữ SHA đã khóa và không huấn luyện lại.
Mở [http://127.0.0.1:8765](http://127.0.0.1:8765), giữ PowerShell mở, dừng bằng
`Ctrl+C`. Nếu cổng bận, kiểm tra server cũ hoặc chọn `--port 8766`.

Trọng số nằm trong `outputs/tv4/models/`; ảnh upload chỉ ở RAM. Nhật ký duyệt
ở `outputs/tv4/w4/sessions/`. Không có weights thì chọn Giả lập để thử giao diện;
đó không phải suy luận mô hình thật. [Hướng dẫn duyệt](handoff_tv4_w4.md).

## Ảnh và manifest

Repo có manifest đã khóa, không có 4.000 ảnh nguồn. Upload ảnh riêng không cần
tải cả pilot. Để tải/tiếp tục tập pilot và có ảnh mẫu train trong demo:

```powershell
.venv/Scripts/python.exe scripts/resume_tv1_w2.py
```

Ảnh được lưu ở `data/images/swg_pilot_v2/`. Giữ nguyên các thư mục này giữa các
lần làm; xem [bàn giao tải ảnh](handoff_tv1_w2.md) và
[comparison_v1](handoff_tv1_w3.md). Không chạy lại chia tập để mở web.

## Colab

Colab dùng cho thí nghiệm có cấu hình và run ID riêng. Đầu mỗi lượt ghi Python,
GPU, VRAM, phiên bản thư viện và commit vào log. Không giả định mọi phiên Colab
có cùng GPU/Python; không đổi phụ thuộc hoặc viết lại run B2/B3 cũ để khớp điểm.

Clone đúng commit/branch dùng cho thí nghiệm; lấy manifest và class map từ cùng phiên bản. Lưu checkpoint và cấu hình sang nơi lưu trữ lâu dài trước khi kết thúc phiên. Không đưa thông tin đăng nhập Drive hoặc GitHub vào notebook được commit.

## Máy có GPU

TV2 chạy kiểm tra ban đầu và điền thông tin vào `coordination/gpu_bookings.json` trước khi xác nhận lịch GPU local. `nvidia-smi` chỉ cho biết driver nhìn thấy GPU NVIDIA; không chứng minh PyTorch/CUDA hoặc mô hình chạy được. Notebook `notebooks/TV2_baseline_evaluation.ipynb` đã có smoke test CPU/CUDA và ghi thiết bị thực tế. Chọn bản PyTorch phù hợp với máy trước khi huấn luyện; không thay bộ thư viện trong lúc người khác đang chạy.

## Chạy từ repo vừa clone

Kiểm tra JSON mẫu và unittest không cần `data/raw` hoặc SQLite. Tái lập EDA là
việc riêng; xem [báo cáo EDA](../reports/eda/EDA_member1.md). Manifest đã tồn tại;
nếu được giao tái lập split, dùng `--output data/processed/repro_check`, không
ghi đè v1/v2/comparison_v1. Test chính thức đã chạy, không dùng làm smoke test.

`scripts/validate_handoff.py` là kiểm tra dữ liệu tuần 1 đầy đủ của TV1, cần
metadata gốc và thư mục `repro_check`; không phải điều kiện mở web. Kiểm tra
metadata comparison_v1 hiện tại mà không sửa snapshot:

```powershell
.venv/Scripts/python.exe scripts/validate_comparison.py --metadata-only --report outputs/comparison_audit.json
```
