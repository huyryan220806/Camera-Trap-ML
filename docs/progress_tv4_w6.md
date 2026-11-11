# TV4 W6 — R1-R4, bắt đầu 08/11/2026

**Bổ sung 11/11:** R6 được tiếp nhận sau nghiệm thu TV2; xem
[tiến độ R6](progress_tv4_r6.md). Các mốc bên dưới giữ nguyên lịch sử R1-R4.
R5 FAILED được bỏ qua theo yêu cầu TV4. B2 vẫn mặc định.

- Branch `feat/demo`, nền `cfcf006`; R5/R6 ngoài phạm vi theo yêu cầu TV4.
- Đã xác minh4ZIP và145payload theo receipt, giữ checkpoint ngoài Git.
- Registry riêng `configs/demo_w6.json`; native W6 giữ nguyên byte source TV3,
  không sửa loader W5 đã khóa. B2 vẫn mặc định.
- Benchmark fixture đã khóa24ảnh train (3/lớp,seed42) trước inference,
  đủ hash byte/RGB; đường dẫn `outputs/tv4/w6/benchmark_fixture/`.
- Đã hoàn thành adapter/cache/equivalence, UI version/dataset và benchmarkCPU.
- Native4model exact logits/softmax delta0 trên crop train/RGB/grayscale,
  batch1 và8+1; portrait nhiều vùng và cache swap PASS.
- Benchmark01 hoàn tất5model ×48warmrequest trên24ảnh cố định, mỗi model fresh
  process; đủ mean/p50/p95, cold load, detector/classifier/pipeline, peak RAM,
  trạng thái và50box/model. GPU0giờ; R5/R6 chưa thực hiện.
- Browser01 +browser_errors01 PASS: real R1-R4, B2/W5 giữ được, defaultB2,
  lưu/reload/export/409, batch/corrupt/drafts/CSV và3viewport; lỗi model thật
  không fallback. CSV version/dataset và UTF8/formula roundtrip PASS.
- 10/10unit W6 và450/450full suite PASS sau sửa2fixture test thiếu class_map;
  giữ log failed01 vàpass02 riêng. Không đổi native checkpoint/source/tolerance.
- Báo cáo/bằng chứng: `reports/tv4_w6/REPORT.md`, `benchmark.json`, `evidence/`.
  Config/source SHA: `reports/tv4_w6/configuration.json`; hướng dẫn
  `docs/tv4_w6_demo.md`; scripts đã version-control.
- Bước tiếp: TV2/TV3 review PR đúng commit trước quyết định mặc định.
  Khi nhận R5/R6: kiểm `git status`, tiến trình/cổng và thêm package pins riêng;
  không ghi đè benchmark01, intake hoặc sessions W4/W5/W6.
- Không có training, official Test hoặc GPU job trong kế hoạch thực thi này.

## Delivery

- Code + benchmark + evidence đã push: `52fa734c22913912a4e9ea9071175d49fc6f781d`.
- PR [#9](https://github.com/huyryan220806/Camera-Trap-ML/pull/9),
  `feat/demo` → `main`, chờ TV2/TV3 kiểm tra chéo; chưa merge.
- Server QA8766/8767 được dừng sau kiểm thử; giữ toàn bộ sessions và output.
- R5/R6 chưa đăng ký/chạy, bổ sung sau khi TV4 gửi package mới.
