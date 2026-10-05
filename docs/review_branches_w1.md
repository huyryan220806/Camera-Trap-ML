# Kiểm tra các nhánh tuần 1

> Báo cáo lịch sử ngày 01/10. Các lỗi chặn dưới đây đã được kiểm tra lại và xử lý trong [kết quả tích hợp ngày 05/10](review_branches_w1_round3.md).

Ngày kiểm tra: 2026-10-01. Người dùng yêu cầu kiểm tra tất cả nhánh thành viên
và gộp các nhánh đủ điều kiện vào `main`. Đây là kiểm tra kỹ thuật bằng công cụ,
không thay cho chữ ký nghiệm thu của TV2/TV3 trong các checklist phân công.

## Kết quả

| Thành viên | Nhánh và commit đã kiểm tra | Quyết định |
|---|---|---|
| TV1 | `feat/metadata-split` / `9d5eb1a` | Gộp vào main trước TV4 |
| TV2 | `feat/baseline` / `acd6c59` | Chưa gộp: lỗi thực thi và tích hợp |
| TV3 | `feat/crop-classifier` / `1576c08` | Chưa gộp: quy tắc box và bảo vệ test chưa thống nhất |
| TV4 | `feat/demo` / `c4a81c0` | Gộp vào main sau TV1 |

Giữ nguyên các nhánh thành viên. Không force-push, không sửa lịch sử hoặc đưa
các ảnh, metadata và notebook chưa được Git theo dõi trên máy vào commit.

## Lỗi cần sửa trước khi gộp

### P1: Notebook TV2 không chạy được

File: `notebooks/TV2_baseline_evaluation.ipynb` tại `acd6c59`.
Đánh số cell từ 0: cell 1, dòng mã 35 và cell 2, dòng mã 34 đều phát sinh
`SyntaxError: unterminated string literal` khi kiểm tra bằng `compile()`.
Cell môi trường kết thúc giữa câu `print`; cell metric kết thúc giữa
`ax.set_title`. Cell 3 không chứa mã. Vì vậy notebook hiện tại không tái lập
được báo cáo GPU hoặc kết quả đánh giá đã lưu.

Cần khôi phục đầy đủ mã, chạy lại notebook từ kernel mới và bổ sung kiểm thử
metric. Khi tính macro metric/report/confusion matrix, truyền đầy đủ danh sách
class ID từ class map: hiện code không truyền `labels`, nên một batch thiếu lớp
có thể làm sai phạm vi tính trung bình hoặc gây lỗi với `target_names`.

### P1: TV3 chọn ảnh test để phân tích trực quan trong giai đoạn phát triển

File: `notebooks/crop_classifier_eda.ipynb`, cell 12 tại `1576c08`.
Việc lấy ảnh đầu tiên của mỗi location từ metadata gốc không lọc manifest hoặc
split. Tái tạo danh sách 80 ảnh mà code sẽ chọn, không tải hay xem ảnh, cho thấy:

| Phạm vi theo image ID trong manifest v1 | Số ảnh |
|---|---:|
| Train | 54 |
| Validation | 11 |
| Test | 11 |
| Không thuộc manifest v1 | 4 |

Ví dụ image ID thuộc test: `c7f84c16-8c29-11eb-8b90-000d3a74c7de`.
Code sẽ tải và hiển thị các ảnh này khi chạy; việc kiểm tra này không chứng minh
ai đã xem ảnh trước đó. Cần lấy mẫu EDA từ train manifest và giữ test đóng trong
giai đoạn phát triển. Nếu đã dùng ảnh test để quyết định thiết kế, ghi nhận việc
đó trong báo cáo; không tự sửa hoặc chia lại manifest v1 để che giấu.

### P1: TV3 chấp nhận box không hợp lệ theo hợp đồng TV1

File: `notebooks/crop_classifier_eda.ipynb`, các cell 3, 5, 8 và 12.
Cell 3 chấp nhận x/y âm tới -1, trong khi `scripts/prepare_swg.py:valid_bbox`
loại tọa độ âm. Chạy lại quy tắc trên metadata cục bộ cho kết quả TV3 chấp nhận
101.454 box, trong đó 70 box bị TV1 loại. Ví dụ box có x = -0.8101248.
Do đó số lỗi hình học là 205 theo TV3 nhưng 275 theo TV1.

Cell 8 và biến `has_valid_box` ở cell 12 chỉ kiểm tra có trường bbox, không
kiểm tra tính hợp lệ hình học. Việc suy đoán bbox chuẩn hóa từ w/h <= 1 cũng
không tương đương phân biệt tường minh `bbox` và `bbox_relative` của TV1.
Cần dùng chung `valid_bbox` hoặc các box đã làm sạch trong manifest; không
thay đổi quy tắc làm sạch hay manifest đã khóa. Thêm test cho tọa độ âm, box
1 pixel, box tràn viền và bản ghi thiếu bbox.

### P2: Các trở ngại tích hợp và tài liệu

- TV2 có lịch sử gốc riêng (`e75942a`), không có merge base với main hoặc TV3.
  `git merge-tree` trả về `refusing to merge unrelated histories`.
  Nên chuyển riêng các file đã sửa sang một nhánh mới từ main; không ép gộp
  lịch sử hoặc ghi đè cây thư mục chung. TV2 không kế thừa TV3.
- TV2 dùng `Readme.md`, khác hoa/thường với `README.md` chung, có thể xung đột
  trên Windows. README TV2 vẫn hướng dẫn chạy các file đã bị xóa:
  `check_environment.py`, `src/evaluation/metrics.py`; đường dẫn report cũng cũ.
  Cần giữ một README chung và chuyển bàn giao TV2 vào docs với link chính xác.
- TV3 có conflict với nền TV1+TV4 tại `.gitignore`, `README.md`, `requirements.txt`.
  Khi giải quyết, giữ các dependency của TV1/TV4, bổ sung phần TV3 và giữ quy tắc
  không commit dữ liệu/thông tin bí mật; không chọn bỏ toàn bộ một phía.

## Kiểm tra đã đạt cho TV1 và TV4

Chạy tại repo với Python 3.12.10 và môi trường `.venv` hiện có:

```powershell
.venv/Scripts/python.exe scripts/check_environment.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/validate_handoff.py
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe scripts/validate_gpu_schedule.py
git diff --check origin/main origin/feat/demo
```

- 20 unittest đạt; môi trường CPU đúng các phiên bản đã ghim.
- Manifest 31.589 ảnh, pilot 4.000 ảnh; train/val/test: 22.073/4.835/4.681.
- Không giao nhau về image ID, đường dẫn, sequence hoặc location giữa các split.
- Manifest/pilot/location split trùng byte với bản tái tạo cục bộ đã lưu.
- Đối chiếu metadata box: 101.384 hợp lệ, 32.178 thiếu bbox, 275 lỗi hình học.
- Cả 6 JSON mẫu đầu ra hợp lệ; lịch GPU có 0 đăng ký thực tế và hợp lệ.
- Diff TV1+TV4 không có lỗi whitespace.

`validate_handoff.py` cần metadata và thư mục `repro_check` cục bộ; đây không
phải kiểm tra chạy được trên một clone sạch chưa chuẩn bị dữ liệu. Không chạy
lại toàn bộ quá trình tạo split trong đợt review này. Chưa kiểm tra trùng nội dung
ảnh toàn bộ dataset, notebook TV1 chưa chạy trong Jupyter, GPU và suy luận thật
chưa được kiểm chứng. Với TV2/TV3 chỉ kiểm tra tĩnh và tái tạo logic trên metadata;
không chạy notebook tải ảnh hoặc cài môi trường GPU riêng của thành viên.
