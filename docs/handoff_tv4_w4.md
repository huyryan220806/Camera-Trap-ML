# TV4 tuần 4: duyệt lại và đo tốc độ demo

Ngày 25/10/2026. Nhánh cố định `feat/demo`. Demo tiếp tục dùng B2 đã khóa;
B3 vẫn là thử nghiệm có vấn đề tái lập chưa giải quyết, chưa được bật trong demo.

## Chạy và sử dụng

Từ thư mục gốc repo, dùng môi trường Python 3.12 và `requirements-tv4.txt` đã
cài cho tuần 3. Máy này đã có MegaDetector và B2 đúng SHA. Chạy:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765
```

Mở http://127.0.0.1:8765. Nếu server đã chạy thì chỉ mở trang; không chạy thêm
server trên cùng cổng. Máy khác cần chuẩn bị trọng số theo
[bàn giao tuần 3](handoff_tv4_w3.md). B2 hiện có tại `outputs/tv3/b2/best_model.pt`:

```powershell
.venv/Scripts/python.exe scripts/prepare_tv4_classifier.py --model B2 --source outputs/tv3/b2/best_model.pt
```

1. Giữ MegaDetector + B2, chọn ảnh mẫu train hoặc nạp ảnh riêng rồi phân tích.
2. Xem box, top 3 và điểm từng box. Top 1 dưới ngưỡng 0,70 chuyển `needs_review`.
   Ngưỡng này là quy tắc demo chưa tối ưu; softmax chưa được hiệu chỉnh. Điểm
   thấp không chứng minh ảnh chứa loài mới, điểm cao không xác nhận nhãn đúng.
3. Trong phần duyệt, điền người duyệt, chọn từng vùng và xác nhận/sửa một trong
   8 lớp đã biết. Nếu không đủ bằng chứng, chọn chưa xác định; có thể đánh dấu
   vùng không phải động vật. Bộ lọc điểm thấp chỉ lọc danh sách, không xóa box.
4. Chọn kết luận cho ảnh. Chỉ đánh dấu đã duyệt khi mọi vùng đã xử lý. Nếu thấy
   động vật không có box, chọn detector bỏ sót và ghi vị trí/nội dung trong ghi
   chú; áp dụng cả khi có một số box và khi không có box nào. `no_detection`
   không tự động là ảnh trống. Lỗi đọc ảnh/suy luận được ghi riêng, không là bỏ sót.
5. Lưu bản duyệt rồi xuất JSON. JSON xuất là bản **đã lưu**; thay đổi chưa lưu
   được nhắc trên màn hình. Nạp lại lấy bản trên đĩa. Lưu từ bản cũ bị từ chối
   bằng HTTP 409 để tránh ghi đè lần duyệt khác.

Các chỉnh sửa là chú thích của người duyệt, không tự sửa dự đoán gốc, manifest,
nhãn huấn luyện hoặc kết quả Test. Màn hình này chưa có công cụ vẽ thêm box;
vùng detector bỏ sót được ghi bằng kết luận và ghi chú vị trí.

## Đầu ra và lưu sau gián đoạn

Mỗi lần phân tích tạo `outputs/tv4/w4/sessions/<request_id>/`:

- `inference.json`: ảnh chụp kết quả gốc bất biến, SHA ảnh, model/provenance,
  runtime, thời gian suy luận, batch và trạng thái ban đầu.
- `events.jsonl`: nhật ký bổ sung từng lần lưu, người duyệt, nhãn, ghi chú,
  thời gian UTC và revision; flush/fsync sau mỗi lần lưu.

Ảnh upload chỉ ở RAM; log không chứa dữ liệu ảnh. Giữ ảnh nguồn riêng nếu cần
duyệt lại bằng hình ảnh sau khi tắt trình duyệt. API GET `/api/review/<request_id>`
đọc lại phiên đã lưu sau khi server khởi động lại; POST `/api/review` ghi bản duyệt.
Giao diện hiện nạp lại phiên đang mở, chưa có danh sách tìm kiếm các phiên cũ.
Nhật ký hỏng phải được xử lý rõ ràng, không âm thầm bỏ dòng lỗi. Sao lưu thư mục
sessions để giữ bản duyệt; thư mục outputs được bỏ qua bởi Git.

JSON xuất dùng `schema_version=review-session-1.0`; trường `original` giữ nguyên
schema suy luận tuần 3. API phân tích vẫn trả `result`, `classification`,
`preview` và bổ sung `review_session`, để các client cũ không bị thay hợp đồng.

## Đo tốc độ có thể chạy tiếp

```powershell
.venv/Scripts/python.exe -X utf8 scripts/benchmark_tv4_w4.py --output outputs/tv4/w4/benchmark_final_20261025
# Chỉ thêm --resume nếu thư mục đã được tạo bởi lần chạy cùng cấu hình/code:
.venv/Scripts/python.exe -X utf8 scripts/benchmark_tv4_w4.py --output outputs/tv4/w4/benchmark_final_20261025 --resume
```

Nếu thử nghiệm mới hoặc thay code/cấu hình, dùng tên thư mục đầu ra mới.
Benchmark khóa tiến trình, kiểm tra fingerprint cấu hình/code, ghi từng request
vào `inference.jsonl` và bỏ qua job đã hoàn tất. Nếu bị ngắt giữa một request,
lần sau chạy lại request chưa ghi xong; lần nạp model mới được ghi là cold.
Không được tự ghép số đo cold vào warm. Nhật ký JSON bị cắt dở sẽ báo lỗi để
điều tra, không tự xóa bằng chứng.

Chọn 8 ảnh train cố định bằng image ID nhỏ nhất từng lớp, chạy một request cold
và 2 vòng warm. Thêm 4 ảnh train có GT box nhỏ nhất theo diện tích chuẩn hóa để
thăm dò bỏ sót; nhóm này tách khỏi thống kê tốc độ chính. Kiểm tra SHA ảnh,
manifest và provenance trước suy luận. Không mở Test, không sửa ngưỡng dựa trên Test.

Log gồm phần cứng, phiên bản thư viện, CPU threads, batch ảnh/detector, batch
crop thực tế, kích thước đầu vào, cache hit, trạng thái và thời gian. Thời gian
đo là decode + detector + classifier + kiểm tra/cache trọng số, không gồm đọc
file đầu vào, upload, preview, ghi log, trình duyệt hoặc thời gian người duyệt.
Mean/p50/p95 và throughput chỉ dùng request warm thành công của 8 ảnh chính.

GT chưa được khớp với box detector tại IoU 0,5 là **ứng viên bỏ sót hoặc định vị
không khớp**, chưa phải kết luận ground truth. Nhật ký lưu cả GT, box dự đoán,
ID và trường hợp không có phát hiện để đối chiếu bằng mắt. MegaDetector
**MDv5a.0.1 / megadetector 10.0.25** đã dùng SWG khi huấn luyện; mẫu train nhỏ này
không đo khả năng tổng quát hóa hay recall độc lập của toàn hệ thống.

## Kiểm thử và người nhận bàn giao

- [Báo cáo và bằng chứng](../reports/tv4_w4/REPORT.md).
- [Progress và điểm tiếp tục](progress_tv4_w4.md).
- TV2 có thể kiểm tra luồng duyệt/log; TV3 giữ checkpoint, preprocessing và
  mapping B2 đã khóa. Không cần huấn luyện lại để chạy phần này.
- TV3 đã được sửa trên nhánh riêng `feat/crop-classifier`, commit `a692a10`.
  Sửa lỗi kiểm định không làm B3 tự chuyển thành PASS; demo vẫn dùng B2.

Chạy kiểm thử hồi quy bằng `.venv/Scripts/python.exe -m unittest discover -s tests -v`.
Kiểm thử browser ở `scripts/qa_tv4_w4.cjs`, cần Node, Playwright, Edge và server
đang chạy. Nó tạo các bản duyệt QA với ghi chú rõ ràng, không phải nhãn đã thẩm định.
Không chạy kiểm thử hoặc inference khác đồng thời khi lấy số đo tốc độ chính.
