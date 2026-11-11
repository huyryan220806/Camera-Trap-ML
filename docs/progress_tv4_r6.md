# TV4 — R6 bổ sung, 11/11/2026

- Branch `feat/demo`, nền `3771ee4`; R1-R4 đã bàn giao ở PR#9.
- Theo yêu cầu TV4, bỏ R5 FAILED; chỉ thêm R6 seed43. Không đổi mặc định.
- TV2 acceptance commit `96d202563c63b47d4d3d6773c3d4b5a2a29c3c7a` đã đọc.
- ZIP267959559bytes SHA `fcb6118cd89c1a825d02e6d1c0a7bd19b983bac7bebaf863b959c0dd8854144e`;
  checkpoint86851190bytes SHA `24e3f51418dd7492a7537dff629794547c4540e8929bfe3e566105a6486581ef`;
  CRC/path và36payload PASS tại `outputs/tv4/w6/r6_intake`.
- Native R6 giữ nguyên byte source snapshot TV3 trong `src/training/dino_w6_r6.py`;
  không sửa native W5 hoặc R1-R4. Registry opt-in mới `configs/demo_w6_r6.json`.
- R6 và R2 native/adapter exact logits+softmax delta0; batch1/8+1,
  crop train/RGB/grayscale, portrait2box/top3 và cache swap PASS.
- Benchmark `r6_benchmark01` COMPLETE: W5,R2,R6 ×48warmrequest =144request,
  24ảnh train cũ SHA `d2b0f1d6b05a02a3a192c5748099a76f9bfb4688ef49c887be1a2758726f4077`.
  48/48paired detector geometry/scores giống nhau; mỗi model4no_detection/50box.
  R6 pipeline mean/p50/p95 10.961/10.315/13.591s, CPU4threads/1interop FP32;
  GPU0giờ. Không dùng Test hoặc chạy huấn luyện đồ án.
- `r6_browser01`, `r6_errors01` PASS: R6 thật/B2/W5, lưu/sửa/reload/export409,
  desktop/mobile320/390, a11y, batch good/corrupt/good, drafts và CSV/JSON;
  checkpoint QA lỗi thật báo classify error, không box/fallback.
- 60/60focused và453/453full regression PASS; environment,6JSONexamples,
  JSsyntax và CSVroundtrip PASS. Full suite có synthetic smoke training cũ,
  không huấn luyện lại model đồ án.
- Báo cáo/evidence riêng: [R6 REPORT](../reports/tv4_w6_r6/REPORT.md);
  [chạy và tái kiểm](tv4_r6_demo.md). Báo cáo R1-R4 trước giữ nguyên.
- Đã push code/evidence commit `bd5b740cfa4e0efc9ac7502e57a929f781dd8d04`
  lên `origin/feat/demo` và cập nhật [PR#9](https://github.com/huyryan220806/Camera-Trap-ML/pull/9)
  cho R1-R4+R6. PR vẫn OPEN, chờ TV2/TV3 review tích hợp và nhóm chốt checkpoint.
  Không tự merge hoặc đổi B2 mặc định; QA servers đã dừng.
