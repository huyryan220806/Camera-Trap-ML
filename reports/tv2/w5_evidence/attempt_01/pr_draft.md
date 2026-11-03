# TV2 W5 validation audit and partial TV4 review

GitHub creation attempted through connector: **403 Resource not accessible by integration**.
No W5 PR was created. Compare URL: https://github.com/huyryan220806/Camera-Trap-ML/compare/main...feat/baseline?expand=1

Suggested title: TV2 W5: validation audit, verified B2 reference and partial TV4 review

Base: main. Head: feat/baseline. Draft: yes. Suggested reviewers: dohoangphuc2006 (TV3), huyryan220806 (TV1).

## Body

TV2 W5 có evaluator validation-only, schema dự đoán, protocol DRAFT và bằng chứng kiểm định B2/API TV4. Trạng thái **PARTIAL**, chưa nghiệm thu W5 hoặc W6.

Dữ liệu giữ nguyên comparison_v1: train 2.800 ảnh/3.125 GT crops, validation 600 ảnh/680 crops; provenance SHA d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f. Nền triển khai 60516f51fccbb85e6e266a022d94ea90d2239a11. Gói TV1 W5 9abc9c5 được verify-only trong snapshot độc lập; 1.665 ứng viên chưa qua quality gate, không dùng train.

B2 fresh-process checkpoint SHA 8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5: validation accuracy 0.7466666666666667, macro-F1 0.7454765175212033, macro-P 0.7484190016985997, macro-R 0.7466666666666667. Lưu đủ 600 predictions/vector8, per-class/CM; recompute độc lập khớp. Native/adapter logits trên 680 crops max delta 0.0. Giữ giới hạn thiếu original training log/embedded run provenance.

Kiểm tra: 409/409 unittest PASS (32 test W5 mới), 0 FAIL/SKIP; environment PASS; 6 contract fixtures PASS; Train/Val 3.400 raster/hash PASS; TV1 W5 subset 12 PASS. TV4 PR #8 tại fef2511b571b23be3d4e2cf6c1ccedd659097b6f: 44/44 unit PASS, 15 API assertions PASS với B2 thật và fixtures ghi nhãn. Browser responsive1440/390/320, chọn box/hàng và export chưa kiểm được do localhost/Edge approval timeout; không tự APPROVE PR8.

Sai lệch công khai: đã khởi chạy nhầm validator raster toàn snapshot rồi Ctrl+C (last progress750/4000, scope gồm Test; số/IDdecode thực không xác định). Không chạy model/metric/selection trên Test; không official Test rerun. Log giữ nguyên, không nhận PASS cho lượt đó; đã thay bằng Train/Val-only gate. Các lỗi socket/TEMP trước khi final409PASS cũng được giữ. Không sửa kết quả W1–W4, checkpoint hay test để che lỗi.

Còn thiếu: TV3 xác nhận seed/tie/ngân sách trước lượt ứng viên và bàn giao DINO checkpoint/config/preprocessing/log/predictions/reload/adapter thật. DINO metrics=N/A; chưa đạt mục tiêu88% theo bằng chứng. B3 vẫn FAIL/UNRESOLVED; B2 là demo fallback. Không thay weights sản xuất TV4.

Nhờ @dohoangphuc2006 review evaluator/protocol và cung cấp gói mô hình; @huyryan220806 đối chiếu dữ liệu. Đây là review phần triển khai, không phải xác nhận W5 COMPLETE. Điều kiện nghiệm thu tiếp theo: protocol approved, ứng viên đủ artifact được kiểm định validation/reload, browser QA có screenshot thật, reviewer xác nhận.

Báo cáo: reports/tv2/TV2_W5.md; W5_PROTOCOL.md; TV2_W5_TV4_REVIEW.md; W5_EXPERIMENT_CHAPTER.md. Handoff: docs/handoff_tv2_w5.md, docs/progress_tv2_w5_w6.md. Raw evidence và SHA index: reports/tv2/w5_evidence/attempt_01/. Chỉ push feat/baseline; không tự merge.
