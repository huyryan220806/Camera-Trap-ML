# Lịch sử dụng GPU chung

Múi giờ: **Asia/Ho_Chi_Minh (UTC+07:00)**. Tuần 1 không cần GPU cho EDA/schema; TV2 chỉ kiểm tra thiết bị. Cấu hình GPU, chủ máy và ngày bắt đầu chưa được xác nhận, nên các khung dưới đây là **lịch đề xuất**, chưa phải đặt chỗ đã được duyệt.

## Khung ưu tiên từ tuần 2 đến tuần 4

| Ngày trong tuần | Giờ Việt Nam | Ưu tiên | Mục đích |
|---|---|---|---|
| Thứ Hai | 19:00 đến 22:00 | TV2 | Baseline và toàn ảnh |
| Thứ Ba | 19:00 đến 22:00 | TV3 | Vùng cắt |
| Thứ Tư | 19:00 đến 22:00 | TV2 | Thí nghiệm toàn ảnh |
| Thứ Năm | 19:00 đến 22:00 | TV3 | Thí nghiệm vùng cắt |
| Thứ Sáu | 19:00 đến 22:00 | TV2 và TV3 luân phiên | Chạy bù theo đăng ký được duyệt |
| Thứ Bảy | 09:00 đến 12:00 | TV4 | Tích hợp và đo tốc độ |
| Chủ nhật | 09:00 đến 12:00 | Nhóm | Dự phòng; cần một người đứng tên |

Tuần 5 ưu tiên TV4 kiểm thử ứng dụng; tuần 6 chỉ đặt lịch cho kiểm tra tái lập và quay demo. Colab của từng người là tài nguyên riêng theo phiên, không mặc định thay thế được GPU local hoặc sẵn sàng liên tục.

## Sổ đăng ký thực tế

Nguồn thống nhất là `coordination/gpu_bookings.json`, ban đầu chưa có đặt chỗ. Mỗi lượt thêm vào `reservations`:

```json
{
  "booking_id": "GPU-001",
  "resource_id": "local-01",
  "member": "TV2",
  "start": "2026-10-05T19:00:00+07:00",
  "end": "2026-10-05T22:00:00+07:00",
  "purpose": "B0 smoke test",
  "status": "requested",
  "commit": null,
  "run_path": null
}
```

Đây chỉ là mẫu cú pháp ngày giờ, không phải lịch đã đặt. Khi có ngày thực tế, người dùng GPU thêm lượt `requested` qua PR; chủ tài nguyên xác nhận cấu hình và chuyển `confirmed`. Một GPU chỉ có một lượt `confirmed` hoặc `running` tại cùng thời điểm. Cập nhật repo trước khi xác nhận để tránh hai người đặt chồng.

Trạng thái lượt chạy: `requested`, `confirmed`, `running`, `completed`, `cancelled`. Các khoảng thời gian tính theo `[start, end)`: lượt kết thúc 22:00 có thể nối ngay lượt bắt đầu 22:00.

Trước khi commit thay đổi lịch, chạy `.venv/Scripts/python.exe scripts/validate_gpu_schedule.py`. Lệnh kiểm tra ID tài nguyên, múi giờ, thứ tự thời gian và các lượt đã xác nhận/chạy bị chồng; không đặt chỗ trên dịch vụ bên ngoài hoặc kiểm tra máy đang thực sự rảnh.

Trước khi chạy, ghi commit và đường dẫn log. Trong khi chạy, lưu checkpoint định kỳ; trước khi hết giờ, bàn giao GPU hoặc xin gia hạn nếu không ảnh hưởng lượt sau. Không dừng tiến trình của thành viên khác để giành GPU. Nếu Colab mất phiên, ghi sự cố và đăng ký lại phần còn thiếu.

## Người phụ trách

TV1 điều phối ưu tiên và cập nhật mốc tuần; chủ máy duyệt lượt local; TV2 kiểm tra môi trường GPU; mỗi thành viên tự cập nhật trạng thái lượt của mình. Mã thành viên là TV1 đến TV4, sẽ đổi tên hiển thị khi nhóm thống nhất danh sách.
