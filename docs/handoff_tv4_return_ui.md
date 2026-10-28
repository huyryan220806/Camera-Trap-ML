# Bàn giao TV4 trở lại: toàn bộ tuần 1–4 và hướng chỉnh giao diện

**Ngày bàn giao:** 26/10/2026. **Người nhận:** TV4. **Người bàn giao:** TV1, đã hỗ trợ thực hiện phần TV4 trong thời gian thành viên bận. **Người kiểm tra sau khi sửa:** TV2.

**Đọc nhanh:** lấy code từ `main`, làm tiếp trên **`feat/demo`**. Web hiện chạy được bằng **MegaDetector + B2**, có top 3 từng box, duyệt/sửa nhãn và xuất JSON. Có thể bắt đầu làm đẹp giao diện ở `app/`; không cần huấn luyện lại mô hình.

Repo: <https://github.com/huyryan220806/Camera-Trap-ML>.
Bản nền đã xác minh bằng `git fetch origin`: `main` và `feat/demo` cùng commit **`60516f51fccbb85e6e266a022d94ea90d2239a11`** tại thời điểm bàn giao. Nếu có commit mới hơn, đọc diff trước khi tiếp tục.

**Cách đọc:** làm theo mục 2 để mở web, xem mục 3 để biết file cần sửa, dùng mục 5 và 8 để tránh làm hỏng luồng đang chạy. Mục 1 tổng hợp lịch sử; mục 7 phân biệt việc đã có với kế hoạch tiếp theo. Nếu nhận Markdown qua tin nhắn, đặt file trong `docs/` của repo để các liên kết tương đối mở đúng.

## 1. TV4 nhận những gì?

| Tuần | Công việc đã thực hiện | Nơi tiếp nhận |
| --- | --- | --- |
| **1** | Cấu trúc repo, sơ đồ luồng, hướng dẫn môi trường, quy ước Git, JSON mẫu, quy tắc ảnh lỗi/thiếu phát hiện và lịch GPU | [Bàn giao W1](handoff_tv4_w1.md), [kiến trúc](architecture.md), [môi trường](environment.md), [Git](../CONTRIBUTING.md), [hợp đồng kết quả](result_contract.md), [lịch GPU](gpu_schedule.md), [JSON mẫu](../examples/results/) |
| **2** | Web nạp/kéo thả ảnh, ảnh mẫu train, vẽ box, giả lập các trạng thái, adapter MegaDetector thật, kiểm tra phiên bản/hash | [Bàn giao W2](handoff_tv4_w2.md), [bằng chứng W2](../reports/tv4_w2/), [review TV2 W2](../reports/tv2/TV2_REVIEW_TV4_W2.md) |
| **3** | Nối B0 rồi B1/B2 thật; nhiều box, top 3 riêng mỗi box, cache model, kiểm tra checkpoint/preprocessing/class map, ghi điểm chưa hiệu chỉnh | [Bàn giao W3](handoff_tv4_w3.md), [kiểm định B1/B2 và tích hợp tiếp](../reports/tv4_w3_continuation/REPORT.md) |
| **4** | Duyệt/sửa nhãn, ghi detector bỏ sót, lưu phiên và lịch sử revision, xuất JSON đã lưu, log suy luận và benchmark có resume | [Bàn giao W4](handoff_tv4_w4.md), [báo cáo W4](../reports/tv4_w4/REPORT.md), [biên bản tích hợp chung](integration_week4.md) |

**Trạng thái hiện tại có ưu tiên hơn báo cáo lịch sử.** W3 lúc đầu dùng B0, hiện mặc định là B2. Dòng “chưa push”, “chờ review” trong hồ sơ cũ mô tả thời điểm viết; phần code đã được tích hợp vào bản chung. Riêng [review TV2 W4 ngày 23/10](../reports/tv2/TV2_REVIEW_TV4_W4.md) được viết trước khi phần duyệt W4 xuất hiện, không phải kết luận về bản tích hợp ngày 25/10. Việc đã merge không được diễn giải thành TV2 đã ký một biên bản nghiệm thu mới chưa có.

## 2. Bắt đầu trên máy TV4

### 2.1. Nhận code và dùng đúng branch

Nếu chưa có repo:

```powershell
git clone https://github.com/huyryan220806/Camera-Trap-ML.git
cd Camera-Trap-ML
git switch --track origin/feat/demo
git merge origin/main
```

Nếu đã có repo và branch local `feat/demo`, cất giữ/commit công việc đang làm trước khi cập nhật:

```powershell
git status
git fetch origin
git switch feat/demo
git merge --ff-only origin/feat/demo
git merge origin/main
```

Nếu fast-forward bị từ chối vì có commit riêng, xem `git log --oneline --graph --all` và giải quyết merge theo [CONTRIBUTING](../CONTRIBUTING.md); không dùng `reset --hard` để bỏ việc. Giữ branch `feat/demo` cho các tuần sau, không tạo thêm `codex/...`.

### 2.2. Cài môi trường và mở web

Dùng **Python 3.12**. Trên repo mới:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/prepare_tv4_demo.py
.venv/Scripts/python.exe scripts/prepare_tv4_classifier.py --model B2 --source "D:/duong-dan/best_model.pt"
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765
```

Thay đường dẫn `best_model.pt` bằng file nhận từ TV1/TV3. Mở **<http://127.0.0.1:8765>** và giữ terminal chạy; dừng bằng `Ctrl+C`. Cổng đã bận thì mở demo đang chạy hoặc dùng `--port 8766` và truy cập đúng cổng.

Máy đã cài và có trọng số chỉ cần lệnh `run_demo.py`. **Không mở `app/index.html` bằng double-click/file://**, vì web cần các API Python. Đây là HTML/CSS/JavaScript thuần được Python phục vụ; không có bước `npm run dev`, không cần Node/React/Streamlit để sử dụng web.

Chỉnh CSS/HTML/JS thì tải lại trang; nếu trình duyệt giữ bản cũ, dùng `Ctrl+F5`. Chỉnh Python thì khởi động lại server. Sau restart, model được nạp lại ở lần suy luận đầu.

### 2.3. File phải nhận ngoài Git

| Tài nguyên | Cách nhận và sử dụng |
| --- | --- |
| **B2 chính thức** | TV1/TV3 gửi file `best_model.pt`. Trên máy TV1: `D:/VLU/261/ML/CameraTrapML/outputs/tv3/b2/best_model.pt`. Script chuẩn bị kiểm tra rồi chép thành `outputs/tv4/models/b2_approved.pth`. Hai tên khác nhau nhưng phải cùng nội dung/hash. |
| **MegaDetector** | `prepare_tv4_demo.py` tải và kiểm tra; đích `outputs/tv4/models/md_v5a.0.1.pt`, khoảng 281 MB. Không cần TV1 gửi nếu TV4 tải được. |
| **Ảnh minh họa** | Có thể upload ảnh riêng để dùng web. Ảnh mẫu trong dropdown chỉ xuất hiện khi có ảnh train pilot tương ứng trên máy. Muốn tải lại pilot có resume, xem [TV1 W2](handoff_tv1_w2.md). Không bắt buộc tải đủ 4.000 ảnh để sửa bố cục/upload. |
| **B0/B1** | Tùy chọn nếu muốn kiểm tra model cũ; xem [W3](handoff_tv4_w3.md). Thiếu các file này không cản việc chạy B2. |
| **Nhật ký duyệt cũ** | Chỉ cần chuyển `outputs/tv4/w4/sessions/` nếu muốn giữ các phiên đã lưu trên máy TV1. Không cần cho lần cài mới. Đây không phải tập nhãn huấn luyện. |

B2 đã đối chiếu lại khi chuẩn bị tài liệu này:

```text
Kích thước: 89,548,866 bytes
SHA-256: 8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5
```

Lệnh tự đối chiếu:

```powershell
(Get-Item -LiteralPath "D:/duong-dan/best_model.pt").Length
(Get-FileHash -LiteralPath "D:/duong-dan/best_model.pt" -Algorithm SHA256).Hash
```

Chưa có trọng số vẫn có thể dùng chế độ **Giả lập**, chọn **Chỉ detector** để thử bố cục và trạng thái cơ bản. Nghiệm thu luồng thật cần MegaDetector + B2. Không bỏ kiểm tra hash hoặc tự chuyển sang mock khi model thật lỗi. Trọng số, ảnh, `.venv` và `outputs/` không đưa lên Git.

## 3. Bản đồ mã nguồn để làm đẹp UI

| File | Trách nhiệm | Khi sửa thiết kế |
| --- | --- | --- |
| [`app/index.html`](../app/index.html) | Khung trang, controls, ảnh, bảng kết quả, form duyệt | Sắp xếp lại bố cục, tiêu đề, nhãn, vùng thao tác |
| [`app/style.css`](../app/style.css) | Màu, font, khoảng cách, responsive, box overlay, trạng thái | Nơi nên bắt đầu; có thể định dạng lại CSS cho dễ bảo trì |
| [`app/app.js`](../app/app.js) | Upload, chọn mẫu/mode/model, gọi phân tích, render top 3/box, khóa nút, export | Chạm vào khi đổi cấu trúc DOM hoặc tương tác |
| [`app/review.js`](../app/review.js) | Chọn box, bản nháp duyệt, lưu/nạp, revision, đổi nhãn | Giữ đúng liên kết `detection_id` và phân biệt bản nháp/bản đã lưu |
| [`app/vendor/`](../app/vendor/) | Lucide icon và giấy phép local | Dùng icon hiện có; giữ license |
| [`scripts/run_demo.py`](../scripts/run_demo.py) | HTTP server local, static routes, API, preview từ raster đã decode | Chỉ cần sửa nếu thêm route/static asset hoặc đổi hợp đồng API |
| [`src/demo/detector.py`](../src/demo/detector.py) | Đọc ảnh, giới hạn kích thước, MD adapter, đổi tọa độ box | Không cần đổi để làm đẹp UI |
| [`src/demo/classifier.py`](../src/demo/classifier.py) | Nạp/xác minh B0/B1/B2, class map, crop và cache | Không cần đổi để làm đẹp UI |
| [`src/demo/inference.py`](../src/demo/inference.py) | Ghép detector/classifier, top 3, trạng thái và provenance | Giữ quy tắc đầu ra |
| [`src/demo/review.py`](../src/demo/review.py) | Lưu original, sự kiện duyệt, revision và validation | Giữ dữ liệu gốc bất biến |
| [`configs/demo_classifiers.json`](../configs/demo_classifiers.json) | Registry checkpoint/hash/preprocessing | Không sửa để thay tên hiển thị hay trang trí giao diện |
| [`contracts/`](../contracts/) | JSON Schema detector, classifier và kết quả lõi | Không nới schema chỉ để UI gửi dữ liệu sai vẫn qua |

**Không cần chuyển framework để thực hiện yêu cầu làm đẹp.** Có thể cải thiện bố cục, typography, trạng thái và tương tác ngay trong `app/`. Nếu chọn đổi framework, phải giữ API và bổ sung cách build/serve tài nguyên trong server hiện tại.

Hai điểm cần lưu ý khi chia lại file:

- `app.js` được nạp trước `review.js`, đều dùng `defer`. `review.js` dùng chung `$`, `result`, `working`, `setBusy`; `app.js` gọi các hàm duyệt. Không đổi tùy ý sang `type="module"` hoặc đổi thứ tự mà chưa tách phụ thuộc.
- Server chỉ phục vụ danh sách static route cụ thể. Thêm `logo.svg`, font, JS/CSS mới vào `app/` **chưa tự tạo URL**; phải cập nhật route tương ứng. CSP hiện cho script từ cùng origin, icon đã vendored. Đừng thêm CDN rồi coi lỗi tải tài nguyên là lỗi mô hình.

## 4. Luồng ứng dụng hiện tại

1. Chọn ảnh upload hoặc mẫu train, chế độ detector và classifier.
2. Gửi `POST /api/analyze`, UI khóa thao tác trong lúc chờ.
3. Server đọc ảnh; detector tạo box; classifier chạy riêng trên từng box nếu có.
4. Server tạo preview từ đúng raster đã dùng suy luận, trả kết quả và phiên duyệt.
5. UI hiển thị box, top 3, điểm và trạng thái. Người dùng chọn từng vùng để duyệt.
6. **Lưu duyệt** tạo revision mới. **Xuất JSON** tải phiên đã lưu, giữ riêng dự đoán gốc.

| API | Dùng cho UI |
| --- | --- |
| `GET /api/config` | Model khả dụng, tên lớp, phiên bản detector và danh sách ảnh mẫu |
| `GET /api/sample/<id>` | Preview của ảnh mẫu train |
| `POST /api/analyze` | Nhận ảnh/chế độ/ngưỡng; trả `result`, `preview`, `classification`, `review_session` |
| `GET /api/review/<request_id>` | Đọc lại phiên đã lưu |
| `POST /api/review` | Lưu bản duyệt; từ chối revision cũ bằng HTTP 409 |

Body phân tích dùng **một trong hai**: `sample_id`, hoặc `file_name` + `image_base64` (chỉ phần base64, không kèm đầu `data:image/...`). Các tùy chọn hiện có:

```json
{
  "sample_id": "0",
  "mode": "megadetector",
  "threshold": 0.2,
  "classifier": "B2",
  "review_threshold": 0.7
}
```

`sample_id: "0"` chỉ hợp lệ nếu API config trả mẫu đó trên máy đang dùng. `mode` nhận `mock`/`megadetector`; `classifier` nhận `B0`/`B1`/`B2`/`none`. Mock có `scenario`: `animal`, `multiple`, `empty`, `error`.

HTTP 200 vẫn có thể chứa **lỗi suy luận nghiệp vụ** trong `result.status="error"`; phải đọc trạng thái và `error.stage`, không chỉ kiểm tra HTTP. Lỗi request/transport cần hiển thị riêng.

### Trạng thái và cách diễn đạt

| Giá trị | Ý nghĩa cần giữ |
| --- | --- |
| `ok` | Các điểm top 1 đạt ngưỡng demo, chưa phải người duyệt đã xác nhận |
| `needs_review` | Có vùng cần kiểm tra; giữ top 3 để người dùng xem |
| `no_detection` | Không có box động vật đạt ngưỡng; không tự gọi là ảnh trống |
| `error` | Lỗi đọc ảnh/detector/classifier; không biến thành kết quả không có động vật |
| `detected` | Trạng thái có box trong đường **detector-only**; chưa có dự đoán loài |

Mặc định detector 0,20 và review 0,70 là quy tắc demo. UI gọi là **điểm dự đoán/điểm mô hình**, không gọi “xác suất đúng 90%”. Nếu hiển thị dạng phần trăm, vẫn phải ghi đây là score chưa hiệu chỉnh. Điểm thấp không kết luận loài lạ.

## 5. Các điểm dễ vỡ khi thay bố cục

### 5.1. DOM và trạng thái

Ưu tiên giữ các ID dưới đây. Nếu đổi, tìm và cập nhật toàn bộ JS + QA liên quan:

| Nhóm | ID/selector liên kết với hành vi |
| --- | --- |
| Đầu vào | `upload`, `file`, `file-name`, `sample`, `[data-mode]`, `scenario`, `threshold`, `classifier`, `review-threshold`, `run`, `reset` |
| Ảnh và box | `stage`, `image-frame`, `preview`, `boxes`, `show-boxes`, `busy`, `.box`, `.selected-box` |
| Kết quả | `results`, `status`, `timing`, `json`, `export`, `mode-badge`, `classifier-state`, `cache-state` |
| Duyệt | `review-panel`, `reviewer`, `review-box`, `review-label`, `review-only`, `image-outcome`, `review-note`, `save-review`, `reload-review`, `review-status`, `review-revision`, `review-runtime` |

`setBusy()` hiện khóa control qua selector `.controls ...` và `#review-panel ...`. Di chuyển nút ra ngoài các vùng này phải cập nhật selector để không gửi nhiều request hoặc đổi ảnh trong lúc đang xử lý. Các ID metadata/nhãn còn lại được tham chiếu trong JS cũng phải giữ hoặc sửa đồng bộ.

Đổi ảnh, mode, classifier, ngưỡng hoặc scenario phải xóa kết quả/box/phiên cũ. Đừng gắn box của request trước lên ảnh vừa chọn. Giữ cơ chế chống kết quả đọc file bất đồng bộ cũ (`generation`) hoặc thay bằng cơ chế tương đương.

### 5.2. Tọa độ box

- `bbox_xywh` là pixel theo kích thước raster gốc; overlay hiện chuyển sang phần trăm dựa trên `result.image.width/height`.
- `#image-frame` phải bám đúng phần ảnh đang hiển thị. Nếu đặt ảnh trong khung cố định có khoảng trống do `object-fit: contain`, cần tính phần ảnh thật; không trải box theo toàn khung trống.
- Dùng preview server trả sau suy luận để tránh lệch do EXIF. Không tự xoay ảnh một phía.
- Mỗi box giữ `detection_id`; nếu sắp lại danh sách theo score, đồng bộ chọn box/overlay/bản duyệt. Không dùng chỉ số hàng mới làm định danh.
- Thử ảnh dọc, ngang, nhiều box, đổi cỡ màn hình và bật/tắt box. Chỉ thay CSS chưa chứng minh tọa độ vẫn đúng.

### 5.3. Bản duyệt và xuất file

- `original` bất biến; nhãn sửa nằm trong `review.box_reviews`, không thay `top_k` hoặc manifest.
- Bộ lọc “chỉ vùng điểm thấp” chỉ lọc cách nhìn, không xóa các vùng còn lại khỏi bản gửi lưu.
- Payload lưu gồm `request_id`, `revision`, `operator`, `note`, `image_outcome`, `box_reviews`; phải có đúng một bản duyệt cho mỗi detection gốc.
- `image_outcome`: `pending`, `reviewed`, `unresolved`, `detector_miss`, `empty`. Quyết định box: `pending`, `confirmed`, `corrected`, `unresolved`, `not_animal`.
- `reviewed` chỉ hợp lệ khi có vùng và không còn vùng pending/unresolved. `empty` yêu cầu các box đều được đánh dấu not_animal. Lỗi suy luận chỉ được để pending/unresolved. Detector miss phải có ghi chú.
- Tên người duyệt tối đa 80 ký tự, ghi chú tối đa 2.000 ký tự. Nhãn được lấy từ API/class map, không tự thêm loài hoặc đổi class ID khi Việt hóa nhãn.
- Hiển thị rõ “có thay đổi chưa lưu” và “đã lưu”. Export hiện dùng **phiên đã lưu**, không tự xuất bản nháp chưa được backend chấp nhận.
- HTTP 409: báo cần nạp lại; không tự gửi lại để ghi đè revision mới.

JSON xuất W4 là `review-session-1.0`, gồm `original`, `review`, `events` và runtime. Khi có classifier, `original` là `classifier-demo-1.0`, bên trong có `result` v1.0.0. Detector-only dùng `detector-demo-1.0`. `validate_results.py` chỉ kiểm tra kết quả lõi v1.0.0; không đưa cả review-session/detector-only vào validator này rồi sửa schema để nó qua.

Xem [hợp đồng](result_contract.md), [mã validation duyệt](../src/demo/review.py) và [JSON phiên mẫu](../reports/tv4_w4/evidence/review_example.json). Phiên mẫu có chỉnh nhãn phục vụ QA, **không phải nhãn chuyên gia hoặc bằng chứng nhận dạng đúng**.

## 6. Hướng làm giao diện đẹp hơn

Đây là gợi ý thiết kế để TV4 tự quyết chi tiết, chưa phải chức năng mới đã triển khai:

| Ưu tiên | Hướng sửa | Tiêu chí nhìn/thao tác |
| --- | --- | --- |
| 1 | Làm vùng ảnh nổi bật, rút gọn controls | Người dùng thấy ngay bước nạp ảnh, phân tích và vùng đang kiểm tra |
| 2 | Chuẩn hóa font, khoảng cách, màu và trạng thái | Chữ dễ đọc, nút chính rõ, trạng thái không chỉ phân biệt bằng màu |
| 3 | Gắn kết quả từng vùng với ảnh | Chọn một vùng thì người dùng nhận ra box và top 3 tương ứng |
| 4 | Làm form duyệt gọn và rõ | Tách nhãn mô hình/nhãn người duyệt; thấy trạng thái chưa lưu và revision |
| 5 | Đưa JSON/hash/runtime chi tiết vào phần mở rộng | Giữ thông tin truy vết nhưng không để chiếm vùng thao tác chính |
| 6 | Responsive và bàn phím | Không tràn ngang ở 390 px/320 px; có focus, label, loading và lỗi dễ hiểu |

Có thể giữ tông xanh rừng, nền sáng, màu vàng cho cần kiểm tra và màu đỏ cho lỗi. Phần giới hạn SWG và score vẫn cần dễ tìm/đọc. Giữ nhãn **Giả lập** rõ ràng, không che để màn hình trông giống suy luận thật. Không thêm số accuracy, tổng số cá thể hoặc trạng thái hệ thống giả để trang trí dashboard.

Đề xuất chia việc thành hai lượt dễ review: **lượt 1** bố cục/CSS/nhãn; **lượt 2** tương tác vùng ảnh và duyệt. Mỗi lượt giữ ảnh chụp trước/sau và chạy kiểm tra phù hợp. Không phải xin duyệt lại từng thay đổi màu/font.

## 7. Cái đã có, cái chưa có và kế hoạch mới

| Hạng mục | Trạng thái lúc bàn giao |
| --- | --- |
| Upload một ảnh, ảnh mẫu train, mock, detector thật, top 3 nhiều box | Đã có |
| Cache model, kiểm tra SHA/class map/preprocessing, lưu/nạp phiên, sửa nhãn, JSON | Đã có |
| Ghi detector bỏ sót bằng kết luận và ghi chú | Đã có |
| Vẽ thêm/sửa tọa độ box bằng chuột | **Chưa có** |
| Giao diện xử lý một lô ảnh và xuất CSV | **Chưa có**, là việc dự kiến W5 |
| Tìm kiếm/danh sách các phiên duyệt cũ trong UI | **Chưa có**; API đọc được phiên theo request_id |
| Lưu lại ảnh upload trên server | **Không có**; ảnh ở RAM, nhật ký không lưu ảnh |
| DINOv3 / DINOv2 trong app | **Chưa có**; mới là hướng nghiên cứu W5–6 |
| Accuracy ≥88% | **Mục tiêu phấn đấu**, không phải kết quả đã đạt |

Kế hoạch cập nhật của nhóm: TV3 thử DINOv3 ViT-S/16 với bộ phân loại 8 lớp, TV1 phụ trách dữ liệu, TV2 so sánh/kiểm định. TV4 làm đẹp UI trước, tiếp tục phần lô nhỏ/CSV và chỉ nối mô hình mới sau khi nhận đủ checkpoint, class map, preprocessing, hash, code nạp và kết quả kiểm định.

**Thêm tên DINOv3 vào dropdown hoặc registry chưa làm model chạy được.** Code hiện whitelist B0/B1/B2 và adapter phục vụ ResNet18. Mô hình mới cần adapter/backend/contract phù hợp và kiểm tra riêng. B2 tiếp tục là bản chạy được để dự phòng; B3 vẫn UNRESOLVED, không bật chỉ vì đã có file.

## 8. Checklist nghiệm thu sau khi làm đẹp

### Tự kiểm tra của TV4

- [ ] Clone/cập nhật branch đúng; mở được web bằng README mà không dùng đường dẫn riêng của máy TV1.
- [ ] Ảnh ngang/dọc hiển thị đúng; nhiều box vẫn khớp ảnh khi resize và ở mobile.
- [ ] Upload/kéo thả/reset; thay ảnh/mode/model/ngưỡng đều xóa kết quả cũ.
- [ ] Loading ngăn thao tác trùng; lỗi mạng/ảnh hỏng/model thiếu có thông báo và có thể thử lại.
- [ ] Mock được ghi rõ; chạy thật không âm thầm đổi model hoặc đổi sang mock.
- [ ] Mỗi box có top 3 riêng; detector score khác classifier score; không gọi score là xác suất đã hiệu chỉnh.
- [ ] Điểm thấp, no_detection, error và detector-only được hiển thị đúng, không kết luận loài lạ/ảnh trống tự động.
- [ ] Chọn/sửa từng box đúng detection_id; lọc điểm thấp không làm mất các box khác khi lưu.
- [ ] Original không đổi sau sửa; bản nháp/bản đã lưu rõ; nạp lại và xuất JSON khớp revision đã lưu.
- [ ] Revision cũ bị từ chối; detector miss có ghi chú; error không thể được ghi thành ảnh trống.
- [ ] Các cảnh báo SWG, model/version và cách xem runtime còn truy cập được.
- [ ] Kiểm tra 1440×1100, 390×844, 320×740, không tràn ngang; không có lỗi JavaScript.

### Lệnh kiểm tra

Từ gốc repo, kiểm tra tập trung TV4:

```powershell
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p "test_tv4*.py" -v
.venv/Scripts/python.exe scripts/validate_results.py
git diff --check
```

Nếu có Node:

```powershell
node --check app/app.js
node --check app/review.js
```

Trước PR, theo quy ước chung, cài đủ phụ thuộc và chạy toàn bộ suite:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-tv2.txt -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -v
```

Browser QA hiện hành là [`scripts/qa_tv4_w4.cjs`](../scripts/qa_tv4_w4.cjs), cần Node, package Playwright, Edge, server đang chạy, trọng số MD+B2 và ảnh train mẫu local. Script dùng Edge `msedge` cố định; nếu máy dùng trình duyệt khác, cập nhật cấu hình QA rõ ràng. Khi các điều kiện đủ:

```powershell
$env:DEMO_URL = "http://127.0.0.1:8765"
node scripts/qa_tv4_w4.cjs
```

Script ghi ảnh chụp/log vào `outputs/tv4/w4/browser/` và tạo phiên duyệt **QA**. Sao lưu thư mục bằng chứng đó trước lần chạy mới nếu cần giữ lịch sử. Nếu đổi DOM/nhãn, sửa locator tương ứng nhưng giữ các khẳng định về hành vi. Các script browser W2/W3 là hồ sơ cũ, không thay thế QA W4.

**Bằng chứng nền:** lần chuẩn bị bàn giao ngày 26/10 chạy lại **44/44 kiểm thử TV4 PASS, 14,800 giây** trên code chưa sửa UI; log local `outputs/handoff_tv4_return_20261026/tv4_tests.txt`. Đây không phải kiểm thử thiết kế mới. Bản tích hợp ngày 25/10 có 377/377 test và browser QA ở ba cỡ màn hình; xem [biên bản](integration_week4.md).

### Gửi TV2 kiểm tra

PR cần có: mô tả thiết kế đã đổi, ảnh desktop/mobile trước–sau, lệnh và kết quả kiểm tra, JSON một phiên QA, cách tái hiện và phần còn thiếu. TV2 kiểm tra hành vi/API; TV1 góp ý luồng sử dụng, TV3 chỉ cần tham gia nếu có thay model/adapter. Không ghi “đã nghiệm thu” thay người kiểm tra.

## 9. Các giới hạn và tài nguyên cần giữ

- B2 đã khóa; validation macro-F1 **74,55%**, Test macro-F1 **72,63%**, Test accuracy **73,00%**. Các số Test dùng GT boxes, khác luồng MD+B2. Không đưa mục tiêu 88% vào khu vực “kết quả hiện tại”.
- MD **MDv5a.0.1**, package **10.0.25**, đã dùng SWG khi huấn luyện. Demo SWG không là đánh giá detector độc lập.
- Benchmark hiện có: warm mean **5,55 giây/ảnh**, lần đầu **18,08 giây**, Ryzen 5 7535HS, CPU 4 threads, batch ảnh 1, crop batch tối đa 8. Đây là số cũ trên mẫu train nhỏ, không phải cam kết UI hoặc số đo máy TV4. Thời gian này không bao gồm mọi khâu upload/preview/trình duyệt.
- Demo giới hạn ảnh 16 MiB/24 MP, tối đa 64 animal box/request. Box lỗi hoặc classify lỗi không được xuất như kết quả hoàn chỉnh một phần.
- Cache model nằm trong RAM; phiên duyệt nằm ở `outputs/tv4/w4/sessions/<request_id>/inference.json` và `events.jsonl`. Restart không xóa phiên nhưng không khôi phục ảnh upload đã mất khỏi RAM.
- Không sửa các manifest v1/v2/comparison_v1, class ID, model lock, checkpoint và kết quả Test để làm UI đẹp hơn. Không chạy official Test như smoke test.

Nguồn cụ thể: [registry](../configs/demo_classifiers.json), [B2 lock](../configs/model_locks/b2_w3.json), [báo cáo tốc độ](../reports/tv4_w4/REPORT.md), [Test B2](../reports/tv2/TV2_W4_TEST_EVALUATION.md).

## 10. Lưu tiến độ và bàn giao lại

Sau mỗi phần, cập nhật một file `docs/progress_tv4_ui.md` với: branch/commit nền, file đã sửa, việc đã xong, việc đang dở, lệnh kiểm tra đã chạy, lỗi còn lại và bước tiếp theo. Đây là file **TV4 sẽ tạo khi bắt đầu sửa UI**, chưa phải báo cáo công việc đã thực hiện.

Khi gián đoạn: đọc progress, xem `git status`, kiểm tra server/tiến trình/log còn chạy rồi tiếp tục. Không xóa sessions hoặc chạy lại benchmark để “bắt đầu sạch”. Benchmark đã có resume theo fingerprint; nếu code/cấu hình thay đổi, dùng thư mục kết quả mới và xem [W4](handoff_tv4_w4.md).

Khi đã tự kiểm tra, chỉ stage file liên quan, ví dụ:

```powershell
git diff --stat
git diff --check
git add app/index.html app/style.css app/app.js app/review.js
# Thêm chính xác các file QA/tài liệu liên quan nếu có thay đổi.
git commit -m "Improve demo layout and review usability"
git push origin feat/demo
```

Tạo PR `feat/demo` → `main`, nhờ TV2 kiểm tra. Không push thẳng main, không force-push, không xóa branch cố định sau merge. Giữ riêng ảnh/trọng số/log local; không dùng `git add .` khi còn nhiều file của thành viên khác.

## 11. Tin nhắn TV1 có thể gửi kèm

> Mình bàn giao lại toàn bộ phần TV4 tuần 1–4. Code đã ở main và feat/demo, bản nền 60516f5. Bạn đọc docs/handoff_tv4_return_ui.md, cập nhật feat/demo rồi sửa giao diện trong app/. Web hiện chạy MD+B2, có top 3 theo box, duyệt/sửa nhãn và xuất JSON. Mình gửi kèm B2 best_model.pt; detector tải bằng script trong hướng dẫn. Bạn được chỉnh bố cục/màu/font/tương tác, nhưng giữ API, box, original/review và các trạng thái lỗi. Xong thì push feat/demo và tạo PR cho TV2 kiểm tra. DINOv3/accuracy 88% là kế hoạch tiếp theo, chưa có trong app.
