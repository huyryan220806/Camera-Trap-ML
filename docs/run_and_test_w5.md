# Chạy và test demo tuần 5

Cập nhật 03/11/2026. Bản main có UI, DINOv3, B2, duyệt nhãn, lô tối đa10ảnh và CSV/JSON. Không cần train lại để chạy web.

## 1. Máy TV1: mở PowerShell và chạy

Gói DINO và checkout kiến trúc đã được chuẩn bị, kiểm checksum trên máy này.

```powershell
Set-Location D:\VLU\261\ML\CameraTrapML
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765 --dino-package outputs/tv4/w5/intake_20261102/DINOv3_LP_run01 --dino-repo outputs/tv4/w5/dinov3_architecture
```

Mở **http://127.0.0.1:8765** trong Edge/Chrome. Giữ PowerShell mở; dừng bằng `Ctrl+C`.
Nếu đã có server cũ, dừng đúng cửa sổ đó rồi chạy lại; hoặc đổi `--port 8766` và mở `http://127.0.0.1:8766`.
Không mở trực tiếp `app/index.html` bằng `file://`.

Trang vẫn mặc định **MegaDetector + B2**. Muốn thử mô hình mới, chọn **DINOv3_LP_run01** trong Classifier trước khi bấm **Phân tích ảnh**.
Nếu chỉ muốn B2, lệnh ngắn là:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/run_demo.py --port 8765
```

Không chạy hai server trên cùng một cổng. DINO thiếu/sai trọng số sẽ báo lỗi hoặc bị vô hiệu hóa; chọn B2 tường minh nếu muốn dùng B2.

## 2. Checklist thử bằng giao diện

| Bước | Thao tác | Kết quả cần thấy |
| --- | --- | --- |
| 1 | Chọn ảnh mẫu train, MegaDetector + DINO, bấm phân tích | Có kết quả, tên DINO và top3 cho từng box; không chuyển ngầm sang B2 |
| 2 | Chạy lại cùng ảnh | Có kết quả từ model đã cache; thời gian đầu thường cao hơn lần sau |
| 3 | Chọn B2 rồi phân tích cùng ảnh | Hiển thị B2 đúng tên; dùng để thử tích hợp, không dùng vài ảnh demo thay metric600ảnh |
| 4 | Chuyển **Giả lập**, chọn tình huống nhiều động vật | Nhiều box, chọn box/hàng thứ2 phải chuyển đúng vùng đang duyệt; nhãn giả lập hiển thị rõ |
| 5 | Điền người duyệt, sửa nhãn một vùng, thêm ghi chú, **Lưu bản duyệt** | Revision tăng, trạng thái đã lưu; dự đoán gốc giữ riêng |
| 6 | **Nạp lại**, sau đó xuất JSON | Nhãn duyệt và revision đúng bản đã lưu; nháp chưa lưu không được xuất |
| 7 | Chọn2ảnh hợp lệ và1ảnh hỏng trong **Lô nhỏ**, bấm chạy | Ảnh hỏng báo lỗi; các ảnh khác vẫn hoàn tất; mỗi ảnh có phiên riêng |
| 8 | Mở từng hàng lô, sửa/lưu một ảnh; xuất CSV và JSON lô | Có dòng cho ảnh lỗi/không box; nhãn gốc và nhãn duyệt riêng; CSV lấy bản đã lưu |
| 9 | Trong Giả lập chọn không phát hiện; ghi outcome bỏ sót và lý do | Vẫn giữ kết quả no_detection gốc, quyết định của người duyệt ở phần riêng |
| 10 | Thu nhỏ cửa sổ hoặc dùng DevTools ở390/320px | Không tràn ngang, box nằm trên ảnh và nút xuất vẫn dùng được |

Khi test sửa nhãn, dùng người duyệt **TV1 QA** và ghi chú **kiểm thử**, không xem nhãn cố tình sửa là nhãn chuyên gia. Sau đó quay lại MegaDetector để chạy model thật.

Tạo một file JPEG hỏng riêng để thử bước7, không làm hỏng ảnh thật:

```powershell
$demoQa = Join-Path (Get-Location) 'outputs/demo-manual-test'
New-Item -ItemType Directory -Path $demoQa -Force | Out-Null
Set-Content -LiteralPath (Join-Path $demoQa 'bad.jpg') -Value 'QA: this is not a JPEG'
```

Giới hạn mỗi ảnh16MiB/24MP, tối đa10ảnh/lô; queue xử lý tuần tự. Đóng/reload tab mất queue và nháp; phiên đã lưu vẫn ở server. Xuất JSON lô trước khi đóng trang nếu cần giữ bản tổng hợp.

## 3. Kiểm tra tự động

Chạy từ gốc repo bằng môi trường `.venv` hiện có; không cần bật server cho unittest:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/check_environment.py
.venv/Scripts/python.exe -X utf8 scripts/validate_results.py
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -v
```

Bản kết hợp đã qua **440/440 tests** tại lượt review02/11. Nếu chỉ kiểm phần demo:

```powershell
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p "test_tv4*.py" -v
```

Kỳ vọng hiện tại **47/47**. Các test dùng fixture/thư mục tạm; không huấn luyện lại model thật hoặc mở official Test để đánh giá ứng viên. `check_environment.py` chỉ kiểm phụ thuộc chung, không chứng minh inference model thật.

Native/adapter DINO đã được kiểm exact. Nếu đổi môi trường hoặc cần chạy lại phép kiểm này, chọn thư mục output **mới** để giữ bằng chứng cũ:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/verify_tv4_dino.py --package outputs/tv4/w5/intake_20261102/DINOv3_LP_run01 --repo outputs/tv4/w5/dinov3_architecture --output outputs/tv4/w5/manual_equivalence_01
```

Nếu thư mục đã tồn tại thì đọc kết quả hoặc đổi số attempt; không xóa để chạy chồng. Browser QA dùng Node/Playwright/Edge theo [hướng dẫn TV4](tv4_w5_demo.md); checklist thủ công ở trên không cần cài Node.

Không dùng `scripts/evaluate_w4_test.py` làm lệnh test web. Test B2 đã khóa; DINO chưa có test độc lập. Hiện chỉ được trình bày accuracy**84,50%**,macro-F1**84,44%** trên validation với GT boxes.

## 4. Máy mới hoặc máy thành viên khác

Đọc [cài môi trường](environment.md). Bộ CPU demo/tests dùng `requirements-tv2.txt` + `requirements-tv4.txt`; môi trường training/replay GPU TV3 có pin riêng. Đừng cài chồng hai phiên bản scikit-learn khác nhau. Máy TV1 đã chạy được, không cần cài lại.

Ảnh gốc và trọng số không có trên Git. B2 nhận từ TV3 rồi chạy `prepare_tv4_classifier.py --model B2 --source <đường-dẫn-file>`. MegaDetector tải và kiểm qua `prepare_tv4_demo.py`. Không cần tải cả4000ảnh để upload ảnh riêng; ảnh mẫu train chỉ xuất hiện khi ảnh đã có local.

Để bật DINO, nhận **DINOv3_LP_run01_handoff_2026-11-02.zip** ngoài Git; nguồn hiện có tại máy TV1 là `reports/tv3_w5/`. Kiểm ZIP trước giải nén:

```powershell
$dinoZip = 'D:/duong-dan/DINOv3_LP_run01_handoff_2026-11-02.zip'
if ((Get-FileHash -LiteralPath $dinoZip -Algorithm SHA256).Hash.ToLower() -ne '9e969585cd7c7355733976b37bda912dd8deb2667d096ddf9193d62bbc276301') { throw 'ZIP DINO sai SHA-256' }
if (Test-Path outputs/tv4/w5/intake_20261102) { throw 'Thu muc da co; kiem tra goi hien tai, khong giai nen de' }
Expand-Archive -LiteralPath $dinoZip -DestinationPath outputs/tv4/w5/intake_20261102
git fetch origin
git clone --no-checkout https://github.com/facebookresearch/dinov3.git outputs/tv4/w5/dinov3_architecture
git -C outputs/tv4/w5/dinov3_architecture checkout --detach 6876159a11b4df116f30f667f8c9888617df0751
```

Chỉ clone khi chưa có thư mục kiến trúc; giữ checkout sạch. Gói có best/last checkpoint, config, class map, log, predictions và bằng chứng reload; giữ nguyên gói cạnh checkpoint. SHA best_model.pt phải là `acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3`,86.851.958bytes. Không cần tải lại pretrained gốc để nạp best.

Sau đó dùng lệnh ở mục1. Loader hiện cần Git của dự án có training commit `aa64fd7` và checkout kiến trúc đúng pin; tải source ZIP đơn lẻ chưa thay thế một Git clone. Cài sạch/gói offline hoàn chỉnh sẽ được nghiệm thu riêng ở tuần6.

## 5. Khi gặp lỗi

| Hiện tượng | Cách xử lý |
| --- | --- |
| DINO bị mờ trong dropdown | Kiểm hai cờ và đường dẫn package/repo, mở đúng cổng của server mới |
| Lỗi classify | Xem PowerShell/log, kiểm SHA và checkout sạch; không đổi tên checkpoint ResNet thành DINO |
| Không có ảnh mẫu | Upload ảnh riêng hoặc tiếp tục tải pilot theo bàn giao TV1; không chạy lại split |
| Không có box | Kiểm ảnh; không có phát hiện không có nghĩa ảnh trống; có thể ghi cần duyệt/bỏ sót |
| CSV không có nhãn vừa sửa | Lưu bản duyệt trước rồi xuất lại; export dùng phiên đã lưu trên server |
| Revision409 | Nạp lại phiên mới nhất, xem thay đổi rồi sửa/lưu; không ép ghi đè revision cũ |
| Web không mở | Giữ PowerShell chạy, kiểm lỗi import/cổng, dùng đúng localhost và port |

Log duyệt nằm ở `outputs/tv4/w4/sessions/` (đường dẫn được giữ để tương thích các tuần trước), ảnh upload chỉ ở RAM. Không xóa các phiên thật khi dọn demo; dùng tên QA để phân biệt phiên thử.
