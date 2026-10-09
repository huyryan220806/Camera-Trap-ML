# Bàn giao tuần 2: TV4 và review TV2/TV3

Cập nhật 09/10/2026. Nhánh bàn giao:
[`codex/tv4-week2-demo-detector`](https://github.com/huyryan220806/Camera-Trap-ML/tree/codex/tv4-week2-demo-detector).
Mã TV4 đã push ở commit `c69283a`. Không merge vào `main` hoặc nhánh thành viên.
Nhánh này có phần nền TV1 tuần 2 `b9a92b9`; giữ phụ thuộc đó khi tích hợp.

## Gửi cho TV2

Nhờ bạn đọc [review TV2 tuần 2](../reports/review_TV2_W2_2026-10-09.md): bảo vệ
run đã hoàn thành khi smoke/chạy lại, kiểm tra hash validation trước reload,
và bổ sung link checkpoint kèm checksum. Pipeline B0 đã qua 29 test; 192 ID và
metric từ confusion matrix khớp artifact, nhưng chưa reload độc lập weights thật.
Sửa trên `feat/baseline`, push commit mới và gửi lại để review.

TV2 cũng kiểm tra chéo [demo TV4](handoff_tv4_w2.md): upload ảnh, mock/MD thật,
box, JSON, lỗi/không phát hiện, cảnh báo SWG và giao diện màn hình nhỏ. Không
đánh dấu checklist đạt thay cho người kiểm tra.

## Gửi cho TV3

Nhờ bạn đọc [review TV3 tuần 2](../reports/review_TV3_W2_2026-10-09.md): resume
đang bỏ qua ảnh tải lỗi/crop thiếu; chạy lại `--limit` làm tăng tập mẫu; Dataset
cần kiểm tra split/nhãn. 51 test đang đạt nhưng chưa bao phủ các tình huống đó.
Thống nhất đầu vào v2 và tập đánh giá chung với TV1/TV2; giữ nguyên split.
Sửa trên `feat/crop-classifier`, push commit mới và gửi lại để review.

## Nhận demo TV4

- [Hướng dẫn cài/chạy và checklist](handoff_tv4_w2.md).
- [Báo cáo thực nghiệm detector/UI/test](../reports/tv4_w2/REPORT.md).
- [Progress TV4](progress_tv4_w2.md), [progress lần push/review này](progress_review_w2.md).
- [Bằng chứng review và script tái hiện](../reports/review_w2/README.md).

Tại gốc repo trên nhánh bàn giao, sau khi có Python 3.12 và `.venv`:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/prepare_tv4_demo.py --smoke
.venv/Scripts/python.exe scripts/run_demo.py --port 8765
```

Mở http://127.0.0.1:8765. Máy nhận chưa có ảnh pilot vẫn upload ảnh riêng được.
Ảnh/weights không nằm trong Git; setup tải và xác minh model, không tải lại pilot.
MDv5a chỉ phát hiện động vật, chưa nhận dạng 8 loài; bản tiền huấn luyện có SWG,
nên demo trên SWG không phải đánh giá độc lập detector/end-to-end.

## Trạng thái nghiệm thu

| Phần | Kết quả | Việc còn lại |
|---|---|---|
| TV4 | Triển khai và kiểm thử xong, 91 test đạt, đã push | TV2 kiểm tra chéo |
| TV2 | Có B0 pilot và artifact nhất quán | Hai sửa lỗi + bàn giao checkpoint |
| TV3 | Crop/Dataset cơ bản chạy được | Sửa resume/limit/validation, chốt đầu vào |

Chưa tự merge. Không dùng trạng thái unit test xanh thay cho xác nhận dữ liệu,
checkpoint, khả năng chạy tiếp và nghiệm thu chéo.
