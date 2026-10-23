# Prepared TV2 W4 continuation PR

Destination: `huyryan220806/Camera-Trap-ML`, `feat/baseline` → `main`, **Draft**.

Title: `feat(tv2): verify delivered B2/B3 and retain strict W4 evaluation gate`

## Description

W4-02 tiếp tục từ a66f41c. Đã có file B2 và B3; không còn blocker checkpoint missing. B2 khớp SHA đã công bố, fresh-process CPU Validation tái lập đúng CM/error IDs và các metrics. B3 safe-load/forward/metadata/config/mapping/provenance khai báo đạt, nhưng Validation reference reproduction **FAIL trên cả CPU và CUDA**.

B3 reference Macro-F1 0.7410465263; CPU reload 0.7410527052 (446/600 đúng), CUDA reload 0.7427341579 (447/600 đúng). CPU khác hai ID, CUDA còn khác một so với reference. Tensor đầu vào tại các ID bất đồng giống hệt giữa hai môi trường; chưa giải thích được reference gốc. Giữ toàn bộ FAIL evidence, không nới tolerance hoặc chọn runtime để lấy điểm đẹp hơn. Cần TV3 cung cấp runtime/log/predictions gốc và reconcile trước khi final model lock được đóng.

Final lock/protocol vẫn PENDING, locked_utc=null; chưa model inference Test, không có Test metrics/CM giả. 600 ảnh Test đã khôi phục từ phiên trước vẫn đúng SHA, không download lại. Không train lại hoặc sửa checkpoint/labels/code nhánh thành viên khác.

Thêm verifier Train/Val-only và unit tests metadata/class weights/reference checks. Regression cuối và W4 tests xem `reports/tv2/w4_evidence/continuation_01/checks_summary.json`; đây là software PASS, không thay thế B3 reference reproduction FAIL. B0/B1/B2/B3 và bằng chứng W4 cũ giữ nguyên; chỉ cập nhật báo cáo canonical TV2 và thêm evidence mới.

TV3 W4-03: PENDING FIX. TV4 W4-04: HANDOFF NOT VERIFIED, remote vẫn254b40e. TV1 chưa nghiệm thu; không tự merge. Báo cáo chính: `reports/tv2/TV2_W4.md`.
