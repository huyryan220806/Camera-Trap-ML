# Tích hợp tuần 5 — 03/11/2026

Theo yêu cầu TV1: push báo cáo kiểm tra, gộp phần W5 của cả nhóm vào main và hướng dẫn chạy/test. TV1 đã kiểm độc lập ngày02/11 và cho phép merge ngày03/11. Không tạo approval dưới tên TV2/TV3/TV4.

## Các phần đã tích hợp

| Phần | Đầu nhánh đã review | Merge commit |
| --- | --- | --- |
| TV1: dữ liệu ứng viên + báo cáo review | `33aba1f` (review được push trên nền `9abc9c5`) | `fb1b08e` |
| TV2: protocol/đối chứng/nghiệm thu DINO | `df31029` | `ef4636e` |
| TV3: DINO linear probe/checkpoint/handoff | `5734d38` | `ce78288` |
| TV4: adapter/UI/lô nhỏ/CSV | `8d4a255` | `fc12408` |

Fetch ngày03/11 xác nhận không có cập nhật so với các đầu nhánh đã review. Gộp không conflict, giữ lịch sử và bốn nhánh cố định. Mã tích hợp `fc12408` đã được công bố lên `origin/main` cùng hướng dẫn tại `cb2b0f8`; đã xác minh SHA remote bằng local.

## Kiểm định

- [Review tổng hợp](../reports/review_w5_2026-11-02/REPORT.md) và ba biên bản TV2/TV3/TV4 đã được push tại `33aba1f`.
- Cây kết hợp `33e3be4c9cce0ab98196b67ff17325eda4a0cbe6` đã qua **440/440 tests**,71,972giây; native/adapter exact, browser MD+DINO/B2, sửa/lưu/JSON/CSV/lô/error/mobile PASS.
- Sau merge, đối chiếu `app/`, `src/`, `scripts/`, `tests/`, `configs/`, `contracts/`, `data/` và các requirements với cây trên: **không khác byte mã/dữ liệu**. Không lặp toàn bộ suite chỉ vì đổi tài liệu. Lượt này kiểm thêm cách khởi động bằng package/repo DINO ở đường dẫn local chính thức: B2 và DINO thật đều PASS trên ảnh train. [Smoke](../reports/integration_w5/demo_smoke.json), [đối chiếu cây mã](../reports/integration_w5/integration_audit.json), [package local](../reports/integration_w5/local_dino_setup.json).
- Không thay manifest/nhãn/split, checkpoint, protocol hoặc dự đoán đã khóa; giữ nguyên byte evidence theo SHA. Không train hoặc chạy lại official Test.
- Biên bản review ngày02/11 và các báo cáo cũ là snapshot lịch sử; “chưa push/chờ adapter/chờ TV2” trong đó không thay trạng thái tích hợp mới nhất ở đây.

## Cách chạy và kết quả

[Hướng dẫn chạy/test](run_and_test_w5.md), [README](../README.md), [môi trường](environment.md).
Máy TV1 đã chuẩn bị package `outputs/tv4/w5/intake_20261102/DINOv3_LP_run01` và checkout `outputs/tv4/w5/dinov3_architecture` đúng pin. Binary không đưa lên Git; thành viên khác nhận gói ngoài Git theo hướng dẫn.

DINO accuracy84,50%,macro-F184,44% trên600ảnh/680GTcrop validation; B2 accuracy74,67%,macro-F174,55% cùng tập. Chưa đạt88%, chưa có test DINO độc lập. B2 vẫn mặc định, DINO opt-in CPU; score không phải xác suất đã hiệu chỉnh. B3 cũ còn UNRESOLVED, ngoài Test/demo.

## Kế hoạch đã ghi nhận

TV1 dự kiến triển khai tuần6 tối03/11/2026. Giảng viên đã cho thêm vài tuần; **hạn mới chưa cụ thể**. Lượt này chỉ ghi nhớ, không triển khai W6, mở thêm lượt train hay tự đặt hạn mới. Các plan W5/W6 cũ vẫn là kế hoạch ban đầu, cần điều chỉnh khi nhóm có lịch chính thức.

Chi tiết triển khai và tình trạng push: [progress](progress_integration_w5_2026-11-03.md). Các thư mục output và phiên QA local được giữ để tiếp tục nếu bị gián đoạn.

## Công bố đã xác minh

- Báo cáo review đã có trên GitHub từ `33aba1f`; toàn bộ W5 và hướng dẫn đã có trên main tại `cb2b0f8`.
- [PR TV4 #8](https://github.com/huyryan220806/Camera-Trap-ML/pull/8) được GitHub ghi nhận **merged**, merge commit `fc12408`. Không tạo approval thay thành viên.
- [Receipt GitHub/remote](../reports/integration_w5/publication_initial.json). Các commit tài liệu sau đó chỉ ghi trạng thái công bố, không thay mã/model/dữ liệu đã review.
- Giữ bốn branch cố định, đồng bộ bằng fast-forward và không force-push. Máy thành viên dùng `git fetch origin`, về branch của mình, rồi `git merge origin/main`; nếu có việc local chưa commit thì commit/cất giữ trước, không reset.
- Đã dừng server smoke sau khi B2/DINO PASS; cổng8765 được trả lại để TV1 chạy lệnh hướng dẫn. Phiên QA/log/model local được giữ nguyên.
