# Tài liệu CameraTrapML

Trạng thái hiện tại: [README dự án](../README.md). Mở web/cài máy mới:
[môi trường](environment.md). Sơ đồ xử lý: [kiến trúc](architecture.md).

**TV4 tiếp nhận lại công việc:** [Bàn giao toàn bộ tuần 1–4 và checklist chỉnh giao diện](handoff_tv4_return_ui.md).

## Tuần 5–6: kế hoạch đã cập nhật

- **TV1 W5:** [Bàn giao](handoff_tv1_w5.md), [kiểm kê và manifest ứng viên](../reports/tv1_w5/REPORT.md),
  [phần dữ liệu báo cáo](../reports/tv1_w5/DATA_CHAPTER.md), [progress](progress_tv1_w5.md).
- **Ba kế hoạch riêng:** [TV2: đánh giá](plans/TV2_W5_W6.md),
  [TV3: DINO và checkpoint](plans/TV3_W5_W6.md), [TV4: UI và ứng dụng](plans/TV4_W5_W6.md).
- Lượt mô hình đầu dùng `comparison_v1`; 1.665 ảnh train bổ sung mới là ứng viên
  metadata. Nguồn holdout mới chỉ có 109 ảnh, chưa đủ hỗ trợ 8 lớp; chưa phát
  hành test mới. Xem báo cáo TV1 trước khi mở rộng train hoặc gọi kết quả độc lập.

## Tuần 4 đang dùng

| Phần | Hướng dẫn / báo cáo | Tiếp tục sau gián đoạn |
| --- | --- | --- |
| TV1: kiểm kê test | [Bàn giao](handoff_tv1_w4.md), [báo cáo](../reports/tv1_w4/REPORT.md) | [Progress](progress_tv1_w4.md) |
| TV2: Test B2 | [Kết quả](../reports/tv2/TV2_W4_TEST_EVALUATION.md), [lỗi](../reports/tv2/TV2_W4_ERROR_ANALYSIS.md) | Đã hoàn thành; không chạy lại Test |
| TV3: kiểm định B2/B3 | [Bản sửa](../reports/tv3/W4_FINAL_FIX.md), [quyết định](../reports/tv3/TV3_W4_DECISION.md) | [Progress](progress_tv3_w4_final_fix.md) |
| TV4: duyệt và log | [Bàn giao](handoff_tv4_w4.md), [kiểm thử/tốc độ](../reports/tv4_w4/REPORT.md) | [Progress](progress_tv4_w4.md) |
| Tích hợp chung | [Biên bản tuần 4](integration_week4.md) | Đọc trạng thái công bố trong biên bản |

Progress/báo cáo của từng lượt là hồ sơ tại thời điểm chạy; dòng “chưa push”,
“chờ review” trong hồ sơ cũ không thay thế trạng thái tích hợp mới nhất.

## Dữ liệu và mô hình

- [Tải 4.000 ảnh, manifest v2 và resume](handoff_tv1_w2.md).
- [Khóa comparison_v1 cho B1/B2](handoff_tv1_w3.md); [class map](../data/processed/comparison_v1/class_map.json).
- [Checkpoint B1](../reports/tv2/TV2_W3_CHECKPOINT.md),
  [checkpoint B2](../reports/tv3/TV3_W3_CHECKPOINT.md),
  [adapter/cache B0/B1/B2](handoff_tv4_w3.md).
- [Đề cương thí nghiệm](experiment_protocol.md), [hợp đồng đầu ra](result_contract.md).

Ảnh, trọng số và các kết quả local trong outputs không có trên GitHub. B2 cần
nhận file từ TV3, không tạo checkpoint mới hoặc dùng ngầm model khác khi thiếu file.

## Hồ sơ các tuần trước

| Tuần | Tài liệu chính |
| --- | --- |
| 1 | [EDA TV1](../reports/eda/EDA_member1.md), [TV2](handoff_tv2_w1.md), [TV3](handoff_tv3_w1.md), [TV4](handoff_tv4_w1.md) |
| 2 | [TV1 tải ảnh](handoff_tv1_w2.md), [TV2 B0](../reports/tv2/TV2_W2.md), [TV4 detector](handoff_tv4_w2.md), [bàn giao nhóm](handoff_team_w2.md), [tích hợp](integration_week2.md) |
| 3 | [TV1 khóa dữ liệu](handoff_tv1_w3.md), [TV2 B1](../reports/tv2/TV2_W3.md), [TV3 B2](../reports/tv3/TV3_W3_CHECKPOINT.md), [TV4 suy luận](handoff_tv4_w3.md), [tích hợp](integration_week3.md) |

## Quy ước chung

[Git/PR và nhánh cố định](../CONTRIBUTING.md) · [GPU](gpu_schedule.md) ·
[JSON Schema](../contracts/inference_result.schema.json).

Khi bị gián đoạn: đọc progress đúng phần việc, kiểm tra `git status`, kiểm tra
tiến trình/log còn đang chạy, rồi dùng lệnh resume đã ghi. Không xóa state hay
ghi đè dữ liệu/thí nghiệm đã khóa để bắt đầu lại.
