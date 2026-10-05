# Môi trường phát triển

## Cài đặt cho toàn nhóm tuần 1

Cần Git và Python 3.12. Bộ cài dưới đây gồm thư viện chung và phần đánh giá của TV2, đủ để chạy toàn bộ unittest và notebook TV2 trên CPU. Không cần CUDA hoặc Streamlit để kiểm tra tuần 1.

```powershell
git clone --branch main https://github.com/huyryan220806/Camera-Trap-ML.git
cd Camera-Trap-ML
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-tv2.txt
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Với repo đã clone, dùng `git fetch origin` và chuyển branch sau khi đã commit công việc hiện tại; không clone chồng lên thư mục đang có dữ liệu.

Nếu chỉ làm metadata hoặc kiểm tra JSON đầu ra, có thể cài `requirements.txt` nhẹ hơn. Bộ tối thiểu này không chứa scikit-learn/seaborn cho test TV2; chỉ chạy các test tương ứng, không dùng lệnh chạy toàn bộ test khi chưa cài phần TV2.

Không cần kích hoạt venv nếu gọi trực tiếp `.venv/Scripts/python.exe`. Trên Linux/macOS, thay bằng `.venv/bin/python`. Trong VS Code, chọn interpreter thuộc `.venv`; mở notebook có thể cần cài thêm `ipykernel` trong chính môi trường đó.

## Colab

Colab dành cho lượt huấn luyện sau khi TV2/TV3 chốt phụ thuộc GPU. Đầu mỗi lượt ghi Python, GPU, VRAM, phiên bản thư viện và commit vào log. Không giả định mọi phiên Colab có cùng GPU hoặc cùng Python 3.12. Không ép cài bộ phiên bản tuần 1 vào Python khác mà chưa kiểm tra tính tương thích.

Clone đúng commit/branch dùng cho thí nghiệm; lấy manifest và class map từ cùng phiên bản. Lưu checkpoint và cấu hình sang nơi lưu trữ lâu dài trước khi kết thúc phiên. Không đưa thông tin đăng nhập Drive hoặc GitHub vào notebook được commit.

## Máy có GPU

TV2 chạy kiểm tra ban đầu và điền thông tin vào `coordination/gpu_bookings.json` trước khi xác nhận lịch GPU local. `nvidia-smi` chỉ cho biết driver nhìn thấy GPU NVIDIA; không chứng minh PyTorch/CUDA hoặc mô hình chạy được. Notebook `notebooks/TV2_baseline_evaluation.ipynb` đã có smoke test CPU/CUDA và ghi thiết bị thực tế. Chọn bản PyTorch phù hợp với máy trước khi huấn luyện; không thay bộ thư viện trong lúc người khác đang chạy.

## Chạy từ repo vừa clone

Kiểm tra JSON mẫu và unittest không cần `data/raw` hoặc SQLite. Muốn tính lại EDA toàn bộ, thực hiện các bước tải và ingest trong README. Manifest v1 đã tồn tại nên khi tái lập split phải dùng `--output data/processed/repro_check`; không chạy đè v1.

`scripts/validate_handoff.py` là kiểm tra dữ liệu đầy đủ của TV1, cần metadata gốc và thư mục `repro_check`. Nó không phải điều kiện bắt buộc để xem JSON mẫu hoặc bắt đầu phần giao diện tuần 1.
