# TV4 W6 — R1-R4 candidate integration

Phạm vi R1/R2/R3/R4; R5/R6 để đợt bổ sung sau. B2 vẫn mặc định; DINO W5 vẫn
chạy được qua loader/registry cũ. Không thay checkpoint hoặc source W5 đã khóa.

## Chuẩn bị gói

`scripts/prepare_tv4_w6.py` nhận bốn ZIP và bốn `.sha256.json` từ TV3, kiểm
ZIP size/SHA, CRC, đường dẫn/symlink/duplicate và từng payload trước inference.
Ví dụ vị trí gói trên máy TV4:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv4_w6.py --desktop 'C:/Users/lequy/OneDrive/Desktop' --downloads 'C:/Users/lequy/Downloads'
```

Thư mục đích mới `outputs/tv4/w6/intake`; script không ghi đè lần intake cũ.
Trên máy khác, đặt R1/R2/R4 ZIP trong thư mục truyền qua `--desktop`, R3 ZIP và
bốn file SHA trong thư mục `--downloads`. Hoặc giải nén gói đã xác minh vào
đúng đường dẫn registry; không đưa weights/ảnh/cache lên Git.

Kiến trúc DINO chính thức dùng lại checkout W5 clean tại
`6876159a11b4df116f30f667f8c9888617df0751`. Không cần tải pretrained weights;
checkpoint W6 chứa backbone và head. Source native W6 giữ nguyên byte của
TV3 `127cac5b64d37fdda630a2f84b006a8e420dc9ed`, SHA
`56f99e6ea2deed71f3281c531dc7d40a1a1e21f0d60faa8aae1c493ddb362fbc`.
R3/R4 source commit khác nhưng file inference này có cùng SHA, được ghi riêng
trong registry/provenance.

## Khởi động demo

```powershell
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8766 --dino-package outputs/tv4/w5/intake_20261102/DINOv3_LP_run01 --dino-repo outputs/tv4/w5/dinov3_architecture --w6-registry configs/demo_w6.json
```

Mở `http://127.0.0.1:8766`, chọn `DINO_W6_R2` trước để kiểm thử.
R1 dùng CLS+mean patch768D; R2/R3/R4 dùng CLS384D, backbone đã fine-tune.
Cả bốn là ứng viên tích hợp; TV2 model acceptance không tự đổi mặc định app.
Model/version/dataset/device/SHA và loại đánh giá hiển thị cạnh kết quả.
GT-box validation không phải accuracy toàn bộ detector→classifier.

CPU FP32, square256 tensor uint8 bilinear antialias trước scale/normalize;
RGB, không EXIF transpose, không padding, crop theo geometry hiện có.
Image batch1, crop microbatch8. Điểm chưa hiệu chỉnh, review threshold0.70.
Không tự AMP/TF32, chuyển GPU hoặc fallback sang model khác khi lỗi.

Cache giữ tối đa một ứng viên W6 để giới hạn RAM. Key gồm checkpoint/config/
preprocessing/source/device. Chuyển R2→R1→R2 sẽ nạp lại R2; B2/W5 có cache riêng.
Checkpoint/package/config/class map/source/vendor được xác minh cả khi warm;
checksum sai phải báo classify error, không trả box/score thành công một phần.

Review/batch/JSON/CSV giữ logic W5. CSV thêm model version,dataset version,
config SHA,pooling,feature dimension và loại đánh giá; nhãn gốc/nhãn duyệt vẫn
tách riêng, chỉ xuất phiên backend đã lưu. Các wrapper/version cũ giữ nguyên,
schema classifier chỉ mở rộng enum bốn model mới.

## Kiểm thử và benchmark

```powershell
.venv/Scripts/python.exe -X utf8 scripts/verify_tv4_w6.py --output outputs/tv4/w6/new_equivalence_attempt
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p 'test_tv4*.py' -v
.venv/Scripts/python.exe scripts/validate_results.py
node scripts/qa_tv4_w6.cjs
```

Browser QA dùng Playwright/Edge, server trên, ảnh train gốc local, và tạo review
QA có ghi chú rõ. `PLAYWRIGHT_MODULE` có thể trỏ package ngoài repo;
`QA_OUTPUT` chọn thư mục mới để không ghi đè bằng chứng.

```powershell
.venv/Scripts/python.exe -X utf8 scripts/prepare_tv4_w6_benchmark.py
.venv/Scripts/python.exe -X utf8 scripts/benchmark_tv4_w6.py --output outputs/tv4/w6/new_benchmark_attempt
```

Fixture khóa24ảnh train/3ảnh mỗi lớp,seed42 theo image_id-sorted pools; xác minh
byte/RGB trước đo và giữ ID/SHA trong báo cáo. Chạy tuần tự5process mới (W5,R2,
R1,R3,R4), mỗi model hai vòng24ảnh,4CPUthreads,FP32,detector1280px.
Không chạy training hoặc tác vụ CPU nặng đồng thời với benchmark.

Cold load = gates/checksum+nạp model+forward một crop train trong process mới.
Timer bắt đầu sau import thư viện; không bao gồm khởi động Python, không flush
cache hệ điều hành và không được hiểu là cold boot của máy.
Cold detector request đo riêng khi classifier đã nạp. Warm đo48request/model
trên24ảnh duy nhất; p95 nearest-rank. Pipeline timer gồm decode/detector/
classifier/schema, loại disk-read/hash gate,HTTP/upload,preview,journal/UI.
Classifier timer gồm crop/transform/gates/cache/forward; detector timer gồm
adapter MD. Không gọi đây là độ trễ giao diện hoặc48ảnh độc lập.

Mọi lỗi/no_detection vẫn được giữ trong log và số thống kê. Không bỏ ảnh xấu
để làm đẹp thời gian/accuracy; phép benchmark không tính accuracy train.
Thư mục output mới bảo toàn log partial nếu bị ngắt; kiểm log/process trước
khi quyết định chạy lại, không xóa phiên duyệt cũ.

Chạy full suite/environment/diff-check trước PR; chỉ stage code/config/tài liệu
và bằng chứng liên quan. Chờ TV2/TV3 review score/integration trước lựa chọn
model mặc định. R5/R6 và GPU không được bật trong đợt này.
