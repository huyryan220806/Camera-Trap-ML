# Demo W5 — B2 mặc định, ứng viên DINO chọn tường minh

## Chạy B2 như trước

```powershell
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765
```

## Bật ứng viên DINO để kiểm thử

Dùng ZIP TV3 đã bàn giao ngoài Git, SHA-256
`9e969585cd7c7355733976b37bda912dd8deb2667d096ddf9193d62bbc276301`.
Giải nén trong `outputs/tv4/w5/intake_20261102/`, giữ nguyên cả gói cạnh checkpoint.
Không đưa ZIP/weights/ảnh train vào Git. Fetch nhánh TV3 để Git có training commit
`aa64fd7661827af78ddec4e3e0155b2b9c87b9e2` phục vụ kiểm source.

```powershell
git clone --no-checkout https://github.com/facebookresearch/dinov3.git outputs/tv4/w5/dinov3_architecture
git -C outputs/tv4/w5/dinov3_architecture checkout --detach 6876159a11b4df116f30f667f8c9888617df0751
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8766 --dino-package outputs/tv4/w5/intake_20261102/DINOv3_LP_run01 --dino-repo outputs/tv4/w5/dinov3_architecture
```

Mở `http://127.0.0.1:8766`, chọn **DINOv3_LP_run01** trong Classifier.
Trang vẫn khởi tạo bằng B2. DINO không cấu hình/thiếu weights sẽ bị vô hiệu hóa
trên dropdown; checkpoint sai hoặc source/vendor thay đổi sẽ tạo lỗi phân loại.
Chọn B2 và chạy lại nếu muốn dùng B2; không có fallback tự động.

Môi trường hiện dùng Python 3.12, `requirements-tv4.txt`; DINO adapter chạy CPU FP32,
4 threads, tối đa 8 crop/lần forward. Chưa triển khai GPU selector. DINO resize
tensor uint8 thành 256×256 bilinear antialias trước float32 và normalize; không
dùng CenterCrop224 của B2. Source `src/training/dino_probe.py` giữ nguyên byte từ
training commit TV3 (SHA-256 `8529891d6cd213f4cc186de104b31d58d539782e2003fa6c475eb4000cdcb988`).
Loader kiểm checkpoint, source và checkout kiến trúc cả khi cache đã warm.
Lưu ý việc kiểm source hiện cần Git checkout có training commit, chưa phải gói W6 độc lập.

## Lô nhỏ và xuất

Chọn tối đa 10 ảnh tại vùng Lô nhỏ, sau đó Chạy lô. Mỗi ảnh tối đa 16 MiB/24 MP;
queue xử lý tuần tự, detector batch ảnh=1, classifier batch crop≤8.
Một ảnh hỏng không dừng các ảnh khác. Dừng sau ảnh hiện tại để giữ các ảnh chờ;
Chạy lô tiếp tục các ảnh chưa xử lý. Tên file trùng vẫn có ID riêng.

Chọn từng hàng để xem ảnh, top3/box và bản duyệt. Bản nháp từng ảnh giữ trong
tab; chuyển mode/ảnh rồi chọn lại hàng sẽ khôi phục trạng thái của kết quả đó.
Lưu duyệt tạo revision trên máy chủ. Xuất CSV/JSON lô đọc lại các phiên đã lưu;
thay đổi chưa lưu không xuất ra. Nếu đọc phiên thất bại, báo lỗi và không xuất
bản cache cũ thay thế. JSON gốc từng phiên tiếp tục là bằng chứng đầy đủ.

CSV có BOM UTF-8, một dòng/box, một dòng trạng thái cho ảnh không box/lỗi/chờ.
Có model/hash, top3, tọa độ, nhãn gốc và nhãn duyệt riêng, operator/revision/note.
Chuỗi đầu vào có thể thành công thức Excel được thêm dấu nháy đơn; dữ liệu JSON
vẫn giữ nguyên chuỗi gốc. CSV là bản tổng hợp, không sửa schema kết quả lõi.

Kết quả/ảnh của hàng đợi nằm trong RAM của tab. Đóng/reload tab mất queue và bản
nháp; phiên đã lưu trên server vẫn còn nhưng không tự khôi phục ảnh upload.
Tải JSON lô trước khi đóng trang. Cảnh báo SWG và score chưa hiệu chỉnh vẫn áp dụng.

## Kiểm thử lại

```powershell
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p "test_tv4*.py" -v
.venv/Scripts/python.exe scripts/validate_results.py
node --check app/batch.js
.venv/Scripts/python.exe -X utf8 scripts/verify_tv4_dino.py --package outputs/tv4/w5/intake_20261102/DINOv3_LP_run01 --repo outputs/tv4/w5/dinov3_architecture --output outputs/tv4/w5/new_equivalence_attempt
node scripts/qa_tv4_w5.cjs
node scripts/qa_tv4_batch.cjs
```

Browser QA cần Playwright+Edge, server 8766 và ít nhất một ảnh train gốc đã kiểm
hash ở đường dẫn manifest. `PLAYWRIGHT_MODULE` cho phép trỏ package Playwright
ngoài repo. Dùng `QA_OUTPUT` mới cho mỗi lần QA W5 để giữ bằng chứng cũ.
`FAILURE_DEMO_URL` tùy chọn trỏ server QA riêng với checkpoint cố ý sai để kiểm UI
lỗi model; không dùng thư mục weights thật làm fixture lỗi. Script batch riêng
dùng output cố định `outputs/tv4/w5/batch_final`, hãy đổi tên output trong script
trước lượt mới nếu đã tồn tại. Các script từ chối ghi đè output cũ.

Schema `classifier-demo-1.0` mở rộng enum model thêm `DINOv3_LP_run01`, giữ các
trường/kết quả cũ; JSON lô có wrapper mới `batch-demo-1.0`. Cần TV2 kiểm chéo
thay đổi contract này trên PR, chưa có approval thay nhóm.
