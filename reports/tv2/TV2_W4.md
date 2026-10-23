# TV2 W4-02 — khóa đánh giá và tổng hợp Test

**W4-02 IMPLEMENTATION COMPLETE – PENDING TV1 REVIEW.** Official Test B2 đã hoàn tất một run; chưa có bằng chứng TV1 nghiệm thu.

## Quyết định mô hình

Nhóm đã chốt B2: **YES** qua chỉ thị người dùng, ghi [decision record](w4_evidence/continuation_02/team_b2_decision.json). Final model **LOCKED – B2**, b2_run01, ResNet18 crop classifier,epoch21; SHA `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5` (89,548,866 bytes). Quyết định chỉ dựa Validation. B2 independent Validation Macro-F1 **0.7454765175**, CM/error IDs khớp; đây không phải Test metrics.

Lock tạo lúc `2026-10-23T06:48:53.792415+00:00`, commit trước Test **`2a750c30c43d3b895577cf53d76f2d507321ec18`**, commit time `2026-10-23T13:49:30+07:00`. Official start `2026-10-23T06:52:10.160808+00:00`, complete `2026-10-23T06:54:23.871877+00:00`. [Pre-inference receipt](w4_evidence/continuation_02/pre_inference_receipt.json) và [consistency proof](w4_evidence/continuation_02/test_consistency.json) xác minh đúng thứ tự. Không backdate. Lock SHA `dbc7ea6e60175502607561eb2ba2107ebd965fa274b7542f123347c4737fcec7`; protocol SHA `0c0b184d79167575cc18ca5bc3dfd7047d9d9799c43daa3bdf6e44d531a91b19`. Hai hồ sơ giữ nguyên byte sau khóa.

B3 exact reference reproduction vẫn **FAIL / UNRESOLVED**: reference Macro-F1 0.7410465263; CPU0.7410527052 (khác2 prediction), CUDA0.7427341579 (khác1). Original runtime/training provenance chưa đầy đủ. Nhóm chấp nhận giới hạn cho lựa chọn B2, không biến B3 thành PASS. B3 không Test; không thêm B1/B3 vào comparison. Bằng chứng FAIL và blocker lịch sử giữ nguyên. [Review TV3](TV2_REVIEW_TV3_W4.md). TV1 chưa nghiệm thu.

## Dữ liệu và phương pháp

Dataset comparison_v1:600 parent images /680 GT crops /495 sequences /98 locations /8 classes /75 parents mỗi lớp. Kiểm tra SHA đầy đủ600/600 trước inference và sau run; không tải lại, không sửa split/label/box. Leakage audit giữ ID/path/site/sequence/fileSHA tách biệt giữa Train/Val/Test.

CPU Python3.12.14/torch2.8.0+cpu; crop batch tối đa32,threads4,seed42. RGB không EXIF rotation; crop integer frozen boxes, padding0; resize short256 → CenterCrop224 → ImageNet normalize. model.eval(), inference_mode(), no optimizer/gradient/random augmentation. Mean vector softmax **mọi crop hợp lệ** cùng image_id rồi argmax; đúng1 prediction/parent, tie ID nhỏ nhất. Không cutoff confidence. labels0–7, zero_division0, không làm tròn trước metric, macro không trọng số, CM hàng thật/cột dự đoán. Chỉ báo classification metrics, không Test loss.

Provenance SHA `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`. Dataset/crop/source manifests giữ nguyên; dữ liệu và checkpoint không đưa vào Git. Không train lại hoặc đổi config/code giữa official run. Gate mới chỉ giải quyết blocker B3 không còn áp dụng cho B2 selection; checksum B2, metadata, independent Validation, quyết định, commit, protocol, code và dữ liệu vẫn fail-closed.

## Test thực tế

| Metric Test | Giá trị |
|---|---:|
| Macro-F1 | 0.7263366903 |
| Macro-Precision | 0.7302792835 |
| Macro-Recall | 0.7300000000 |
| Accuracy | 0.7300000000 |
| Đúng / tổng | 438 / 600 |
| Sai | 162 |

Per-class và CM8×8 ở [Test report](TV2_W4_TEST_EVALUATION.md); tổng CM/support600, đúng1 prediction mỗi ảnh và680 crop được dùng. [Error analysis](TV2_W4_ERROR_ANALYSIS.md) gồm lớp khó, mọi cặp nhầm, subgroups bbox nhỏ/nhiều box và ví dụ có nguồn/hash.

## Integrity và kiểm thử

Regression cuối trước Test **347/347 PASS**, gồm **78/78 W4**. [Regression log](w4_evidence/continuation_02/final_pre_test_regression.txt), [focused W4 log](w4_evidence/continuation_02/frozen_policy_tests.txt). Có regression cho B3 FAIL giữ nguyên nhưng B2 được lock khi có acceptance; thiếu acceptance/decision, B2hash sai/Validationfail, lockchưa commit, protocol sửa, thêm B1/B3, run tồn tại, cropaggregation đều bị chặn. Synthetic export chỉ dùng pixels giả, không rerun SWG Test. [Consistency proof](w4_evidence/continuation_02/test_consistency.json) kiểm tra toàn bộ600 prediction, CSV, macro/perclass/CM, artifact hash và thời gian commit trước forward. Post-Test regression/checks được ghi trong [completed work](TV2_W4_COMPLETED_WORK.md).

581 file ban đầu được hash; chỉ code/report TV2 thuộc phạm vi được sửa. B0/B1/B2/B3 nguyên SHA, frozen manifests và600 ảnh đúng SHA; mọi FAIL/history W1/W2/W3 và W4 evidence trước giữ nguyên. Ba file cá nhân untracked giữ nguyên. Environment và6 contract examples PASS.

## Cross-review

[TV3 W4-03](TV2_REVIEW_TV3_W4.md): chọn B2 được nhóm thông qua; B2 independent PASS; B3 readable PASS, exact reference FAIL/UNRESOLVED, original evidence partial; limitation accepted cho selection, chưa công nhận toàn diện TV3. [TV4 W4-04](TV2_REVIEW_TV4_W4.md): HANDOFF NOT VERIFIED, remote254b40e chưa W4. Cần sửa nhãn/export, lowconfidence/detector miss tests, hardware/batch/latency benchmark. Không phụ thuộc Test B2.

## Giới hạn khoa học

600 ảnh Test thuộc495 chuỗi và98 địa điểm, không phải600 quan sát độc lập hoàn toàn. Mỗi lớp75 ảnh, mẫu cân bằng không phản ánh tần suất loài ngoài tự nhiên. Một cặp trùng nội dung RGB cùng Test tại loc_0851 vẫn giữ nguyên (`d86f91b0-8c29-11eb-8c2e-000d3a74c7de`, `d86f91b6-8c29-11eb-94af-000d3a74c7de`); không lọc theo kết quả. Chỉ closed-set8 lớp. Ground-truth box classification không tương đương box detector dự đoán hoặc MegaDetector end-to-end demo; một số phiên bản MegaDetector đã dùng dữ liệu SWG khi huấn luyện, phải kiểm tra detector/version trước đánh giá end-to-end. Softmax chưa calibration; confidence thấp không chứng minh loài lạ. Số ảnh hoặc chuỗi không suy ra số cá thể. Phân nhóm box nhỏ/nhiều crop là mô tả quan sát, không chứng minh nguyên nhân lỗi. Không dùng lỗi Test để đổi B2, checkpoint, preprocessing, threshold hoặc nhãn.

## GitHub và bàn giao

Branch feat/baseline; commit khóa `2a750c30c43d3b895577cf53d76f2d507321ec18` có trước Test. Kết quả/report/evidence được commit riêng sau Test, push và kiểm tra remote HEAD; publication receipt trong continuation_02 ghi các SHA xuất bản. Không reset/rebase/force-push/merge nhánh khác, không tự merge. PR chỉ dùng connector nếu có quyền; nếu403 cung cấp compare link và PR draft, không credential/UI fallback. [PR body](w4_evidence/continuation_02/pr_draft.md), [publication](w4_evidence/continuation_02/publication.json). TV1 cần review báo cáo/metric/CM/hash/tests trước khi xác nhận nghiệm thu.

## Biên nhận xuất bản

Commit khóa trước Test `2a750c30c43d3b895577cf53d76f2d507321ec18`; commit kết quả/Test report `41ebfbf8587994192fa1dad2f57642b8fa95418f` đã push lên origin/feat/baseline, `git ls-remote` khớp local HEAD. Connector tạo Draft PR trả403 Resource not accessible by integration; chưa có PR URL, không dùng credential/UI fallback. [Tạo PR thủ công](https://github.com/huyryan220806/Camera-Trap-ML/compare/main...feat%2Fbaseline?expand=1) với [nội dung đã chuẩn bị](w4_evidence/continuation_02/pr_draft.md). [Publication receipt](w4_evidence/continuation_02/publication.json) ghi SHA và danh sách file. Commit biên nhận tiếp theo chỉ cập nhật tài liệu/evidence xuất bản; không đổi code, final lock/protocol hoặc official artifacts. TV1 nghiệm thu vẫn PENDING REVIEW.
