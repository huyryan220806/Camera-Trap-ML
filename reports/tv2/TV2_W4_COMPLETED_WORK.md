# TV2 W4-02 — B2 đã khóa, chuẩn bị official Test

Quyết định nhóm được người dùng thông báo và lưu tại [decision record](w4_evidence/continuation_02/team_b2_decision.json). Chỉ B2 b2_run01 / epoch21 được chọn bằng Validation; SHA `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`. Final model **LOCKED – B2**, thời điểm UTC thực tế `2026-10-23T06:48:53.792415+00:00`.

B2 independent Validation PASS; B3 exact reference reproducibility vẫn FAIL/UNRESOLVED, nhóm chấp nhận giới hạn cho lựa chọn mô hình. Không Test B1/B3, không threshold hoặc tuning Test. Hồ sơ pending và tất cả FAIL lịch sử giữ nguyên trong evidence/commits. TV1 chưa nghiệm thu.

Protocol: comparison_v1, 600 ảnh / 680 crop / 495 chuỗi / 98 địa điểm / 75 ảnh mỗi lớp. Mean softmax đủ crop theo parent rồi argmax; CPU Python3.12, batch32, threads4, seed42, zero_division0. 600/600 nguồn đúng SHA, không tải lại; không có official marker trước khóa.

[Lock](TV2_W4_MODEL_SELECTION_LOCK.json), [protocol](TV2_W4_EVALUATION_PROTOCOL.json), [pre-Test integrity](w4_evidence/continuation_02/pre_test_integrity.json), [regression](w4_evidence/continuation_02/final_pre_test_regression.txt). Gate yêu cầu tất cả byte khóa/code/evidence đã commit; protocol được ràng buộc hai chiều bằng hash. Chưa inference Test tại commit khóa này; sẽ chạy một official run sau khi HEAD gate PASS. Kết quả sẽ nằm ở commit sau riêng biệt.

TV3 cần reconcile original runtime/provenance; TV4 W4-04 HANDOFF NOT VERIFIED tại254b40e, độc lập với Test B2. Không tự công nhận peer acceptance.
