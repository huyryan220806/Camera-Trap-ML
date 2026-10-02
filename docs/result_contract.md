# Hợp đồng kết quả suy luận phiên bản 1

Schema: `contracts/inference_result.schema.json`, JSON Schema Draft 2020-12. Ví dụ: `examples/results/*.json`. Kiểm tra bằng `scripts/validate_results.py`, dùng thư viện [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/validate/) và kiểm tra ngữ nghĩa bổ sung.

## Nguyên tắc

Mỗi ảnh trả về một object. Một batch lưu JSONL, mỗi dòng một kết quả độc lập; không bỏ qua ảnh lỗi. `request_id` do bên gọi cấp, dùng để đối chiếu đầu vào/đầu ra. Trong batch, bên gọi cấp ID duy nhất cho mỗi ảnh hoặc mỗi lần thử lại. `image_id` có thể null với ảnh người dùng tải lên; không bịa ID SWG.

Các ví dụ là giả lập (`pipeline.mode = mock`), không chứa ảnh thật và không chứng minh chất lượng mô hình. `elapsed_ms = 0` là giá trị mẫu, không phải phép đo hiệu năng. Ngưỡng 0.5 và 0.7 chỉ minh họa; TV2/TV3 phải chọn ngưỡng bằng validation khi có mô hình.

| Trường | Quy ước |
|---|---|
| `schema_version` | `1.0.0`; thay đổi không tương thích cần phiên bản mới |
| `request_id` | ID đối chiếu với yêu cầu xử lý ảnh |
| `image` | Tên file, ID nếu có, kích thước ảnh gốc; không ghi đường dẫn tuyệt đối trên máy cá nhân |
| `pipeline` | Mode, model ID, class map version và hai ngưỡng đang dùng |
| `status` | Một trong bốn trạng thái dưới đây |
| `needs_review` | Có cần đưa vào danh sách kiểm tra không |
| `detections` | Chỉ vùng động vật đạt ngưỡng detector; mỗi vùng có box, điểm detector và top 3 loài |
| `error` | Null hoặc mã lỗi, giai đoạn và thông báo ngắn; không chứa stack trace, token hay nội dung nhạy cảm |
| `elapsed_ms` | Thời gian xử lý ảnh không âm; chỉ có ý nghĩa đo lường ở mode inference |

## Trạng thái và hành vi giao diện

| Trạng thái | Khi nào dùng | Hành vi thống nhất |
|---|---|---|
| `ok` | Có ít nhất một box, mọi top 1 đạt `review_threshold` | Vẽ từng box và gợi ý loài; không gọi là xác nhận chuyên gia |
| `needs_review` | Có box nhưng ít nhất một top 1 dưới ngưỡng | Giữ top 3, đưa ảnh vào danh sách duyệt; không gắn nhãn loài lạ |
| `no_detection` | Đọc ảnh và detector thành công nhưng không có box đạt ngưỡng | `detections=[]`, `error=null`, `needs_review=true`; hiển thị Chưa phát hiện động vật, không tự kết luận ảnh trống |
| `error` | Không đọc được ảnh hoặc mô hình thất bại | `detections=[]`, có error, `needs_review=true`; cho phép thử lại; không ghi nhận như ảnh trống |

Nếu một crop lỗi classifier, phiên bản 1 trả `error` cho toàn ảnh và không xuất dự đoán một phần như kết quả hoàn chỉnh. Các ảnh khác trong batch vẫn được xử lý. Có thể bổ sung kết quả một phần ở phiên bản hợp đồng sau.

## Tọa độ và nhãn

- Box `[x,y,width,height]` tính theo pixel của ảnh gốc, gốc ở góc trên trái. Adapter đổi box đã resize/normalize về ảnh gốc trước khi xuất. Rộng/cao phải dương, toàn bộ box phải trong ảnh.
- Chỉ có detection động vật trong `detections`; box người/phương tiện của detector không được đưa vào classifier loài.
- Mỗi detection có `detection_id` duy nhất trong ảnh, không được dùng như ID cá thể động vật.
- `top_k` gồm 3 lớp khác nhau, sắp điểm giảm dần, `class_id` và `label` phải khớp `data/processed/v1/class_map.json`.
- Điểm nằm trong [0,1], chưa được coi là xác suất đã hiệu chỉnh. Không suy ra tình trạng bảo tồn hoặc số cá thể từ điểm và số box.
- Dùng quy tắc `score >= threshold` là đạt. `ok` khi tất cả top 1 đạt ngưỡng; một box điểm thấp làm cả ảnh cần duyệt.
- Các trường hợp bằng điểm giữ thứ tự do adapter tạo một cách ổn định. Không cần tổng điểm top 3 bằng 1 vì còn các lớp khác.

## Lỗi thống nhất

| Giai đoạn | Mã lỗi | Kích thước ảnh |
|---|---|---|
| `read` | `FILE_NOT_FOUND`, `IMAGE_DECODE_ERROR`, `UNSUPPORTED_FORMAT` | Cả width và height null |
| `detect` | `DETECTOR_FAILED` | Kích thước ảnh đã đọc |
| `classify` | `CLASSIFIER_FAILED` | Kích thước ảnh đã đọc |

Kết quả không có lỗi phải có kích thước ảnh hợp lệ. Không dùng chuỗi rỗng hoặc số 0 để thay null. JSON không chấp nhận NaN, Infinity hoặc khóa trùng.

## Tích hợp và kiểm tra

```powershell
.venv/Scripts/python.exe scripts/validate_results.py
.venv/Scripts/python.exe scripts/validate_results.py outputs/result.json
```

TV2/TV3 chuyển đầu ra mô hình sang hợp đồng này; TV4 chỉ phụ thuộc schema và class map, không phụ thuộc cấu trúc nội bộ của checkpoint. Validator kiểm tra cấu trúc, nhãn, top 3, ngưỡng, box và trạng thái; không chứng minh kết quả nhận dạng đúng hoặc ảnh tồn tại.

Schema tự kiểm tra được kiểu dữ liệu và hình dạng trạng thái; các ràng buộc so sánh giữa trường như biên box, class map và ngưỡng được kiểm tra trong Python. Không bỏ qua bước Python rồi coi schema hợp lệ là đủ.

Khi người dùng sửa nhãn ở tuần 5, lưu bản duyệt riêng gắn `request_id` và `detection_id`, giữ nguyên dự đoán gốc để truy vết. Bộ bàn giao tuần 1 chưa triển khai lưu bản duyệt hay giao diện web.
