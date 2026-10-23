# TV2 W4-02 — completed work

**W4-02 IMPLEMENTATION COMPLETE – PENDING TV1 REVIEW.** Chưa TV1 accepted.

| Công việc | Kết quả |
|---|---|
| Quyết định nhóm B2 bằng Validation | YES; decision record tạo trước khóa/Test |
| Final B2 lock / protocol | LOCKED; commit `2a750c30c43d3b895577cf53d76f2d507321ec18` |
| B2 checksum/metadata/independent Validation | PASS |
| B3 readable / exact reference | PASS readable; FAIL/UNRESOLVED reference, limitation accepted for selection |
| Dữ liệu |600 nguồn/680 crop/495 chuỗi/98 địa điểm;600 SHA PASS,0 download |
| Official Test | COMPLETE;W4_test_eval01,một run,438 đúng,162 sai |
| Metrics/per-class/CM8×8 | COMPLETE; tổng CM/support600 |
| Error analysis | COMPLETE; cặp nhầm, subgroups và ví dụ xác thực |
| Regression trước Test |347/347 PASS,78 W4 nằm trong suite |
| Consistency Test |PASS; prediction/CSV/CM/metric/hash/commit chronology |
| Post-Test regression |**347/347 PASS** sau Test (149.718s);78 W4 nằm trong suite; không forward lại Test |
| B0/B1/B2/B3, dữ liệu và lịch sử |Nguyên SHA/byte; xem integrity proof |
| TV3 W4-03 |B2 selection closed; B3 technical pending fix, không đổi FAIL |
| TV4 W4-04 |HANDOFF NOT VERIFIED; cần artifact W4 thật |
| GitHub |PASS push `41ebfbf8`; remote HEAD khớp; PR connector403, manual compare/body; không merge |
| TV1 nghiệm thu |PENDING REVIEW |

| Metric Test | Giá trị |
|---|---:|
| Macro-F1 | 0.7263366903 |
| Macro-Precision | 0.7302792835 |
| Macro-Recall | 0.7300000000 |
| Accuracy | 0.7300000000 |
| Đúng / tổng | 438 / 600 |
| Sai | 162 |

[Đánh giá Test và artifact](TV2_W4_TEST_EVALUATION.md), [phân tích lỗi](TV2_W4_ERROR_ANALYSIS.md), [decision](w4_evidence/continuation_02/team_b2_decision.json), [pre-inference receipt](w4_evidence/continuation_02/pre_inference_receipt.json), [consistency](w4_evidence/continuation_02/test_consistency.json). Model/protocol frozen giữ nguyên byte sau official run; không cập nhật kết quả vào lock hoặc dùng Test chọn lại mô hình.

[Post-Test regression log](w4_evidence/continuation_02/post_test_regression.txt), [final checks](w4_evidence/continuation_02/final_checks.json). Toàn bộ gate và byte khóa/code/evidence vẫn khớp commit trước Test.

## Biên nhận xuất bản

Commit khóa trước Test `2a750c30c43d3b895577cf53d76f2d507321ec18`; commit kết quả/Test report `41ebfbf8587994192fa1dad2f57642b8fa95418f` đã push lên origin/feat/baseline, `git ls-remote` khớp local HEAD. Connector tạo Draft PR trả403 Resource not accessible by integration; chưa có PR URL, không dùng credential/UI fallback. [Tạo PR thủ công](https://github.com/huyryan220806/Camera-Trap-ML/compare/main...feat%2Fbaseline?expand=1) với [nội dung đã chuẩn bị](w4_evidence/continuation_02/pr_draft.md). [Publication receipt](w4_evidence/continuation_02/publication.json) ghi SHA và danh sách file. Commit biên nhận tiếp theo chỉ cập nhật tài liệu/evidence xuất bản; không đổi code, final lock/protocol hoặc official artifacts. TV1 nghiệm thu vẫn PENDING REVIEW.
