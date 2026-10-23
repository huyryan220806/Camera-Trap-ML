# TV2 W4-02 — bàn giao tiếp nối 23/10/2026

**W4-02 BLOCKED**. Đã tìm thấy và xác minh B2 thật; B3 thật đọc/forward được nhưng không tái lập chính xác Validation reference trên CPU hoặc CUDA. Final lock còn PENDING, `locked_utc=null`, **chưa model inference Test**. Không có Test metrics/Confusion Matrix giả và không có TV1 acceptance.

## 1. Phạm vi và trạng thái kế thừa

TV2 thực hiện W4-02, TV1 nghiệm thu; TV2 review TV3 W4-03 và TV4 W4-04. Tiếp tục từ `a66f41cb7f966f17de7e132e1433103958c1af72` trên `feat/baseline`, không làm lại evaluator/600 ảnh đã khôi phục. Bằng chứng lịch sử22/10 giữ nguyên trong `w4_evidence/`; evidence mới chỉ ghi `w4_evidence/continuation_01/`. Hai kế hoạch local và audit trước được tái sử dụng, không giả đọc tài liệu mới. Không W5/W6, không train lại, không sửa checkpoint/labels/nhánh thành viên khác.

## 2. Git và nguồn

Fetch mới xác nhận: main`0d822a91`, TV1`4bcf85cb`, TV2 đầu phiên`a66f41c`, TV3`65b99b9`, TV4`254b40e`. Main vẫn W3 tích hợp; W4 TV1/TV3 riêng, TV4 chưa W4. Không reset/rebase/force-push/merge PR hoặc merge main. Ba tệp cá nhân untracked giữ nguyên. [Audit commit/SHA](w4_evidence/continuation_01/repository_audit.json), [protected baseline528 file](w4_evidence/continuation_01/protected_before.json).

## 3. Checkpoint B2 và B3

| Thuộc tính | B2 | B3 |
|---|---|---|
| File local | experiments/B2_run01/checkpoints/best_model.pt | experiments/B3_run01/checkpoints/best_model.pt |
| Bytes |89,548,866|89,548,994|
| Epoch trong checkpoint |21|14|
| Safe load/finite tensors/native strict state |PASS|PASS|
| Mapping/config/preprocessing/provenance khai báo |PASS|PASS|
| Fresh Validation reference |PASS CPU|FAIL CPU và CUDA|

B2 SHA`8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5` khớp công bố TV3/TV1. B3 SHA`93ae48dd4b42fa6062daed3a9a1869d620bd7ba9e7ae2aa274085b061f76300b` được tính từ file người dùng, chưa có independent checksum gốc TV3 để đối chiếu. B3 metadata marked official, nhưng không embedded run ID/training commit. Epoch dừng cuối28/21 chỉ theo báo cáo, không tự nhận xác minh khi thiếu full log.

Các verifier mở riêng từng checkpoint trong fresh process, chỉ Train/Val; SHA nguồn2.800 Train+600Val khớp; cùng Validation IDs/680 crop và mapping0–7. Native/adapter max logit delta0 trên toàn bộ crop trong từng runtime. [B2](w4_evidence/continuation_01/b2_validation/verification.json), [B3 inspection](w4_evidence/continuation_01/b3_checkpoint_inspection.json).

## 4. Validation và quyết định

| Nguồn Validation | Macro-F1 | Macro-Precision | Macro-Recall | Accuracy |
|---|---:|---:|---:|---:|
| B1 artifact gốc |0.5624506868|0.5748610369|0.5650000000|0.5650000000|
| B2 fresh CPU |0.7454765175|0.7484190017|0.7466666667|0.7466666667|
| B3 reference TV3 |0.7410465263|0.7406316201|0.7433333333|0.7433333333|
| B3 reload CPU |0.7410527052|0.7408712201|0.7433333333|0.7433333333|
| B3 reload CUDA |0.7427341579|0.7424361314|0.7450000000|0.7450000000|

B3 CPU khác hai prediction so với reference; CUDA còn khác một. Cả hai không đạt exact CM/error-ID checks đã công bố. Hai môi trường có RGB/tensor đầu vào giống hệt tại các ID bất đồng. Có runtime sensitivity, chưa giải thích đầy đủ reference gốc; không nới tolerance, đổi weights/preprocessing hoặc chọn runtime có điểm đẹp hơn. Giữ mọi FAIL log/artifact. [So sánh machine-readable](w4_evidence/continuation_01/b3_runtime_comparison.json).

TV3 quyết định giữ B2 tại commit65b99b9 trước Test; B2 vẫn cao hơn các kết quả B3 local. Tuy nhiên điều đó không tự đóng được blocker provenance/reference của W4-03. [Review TV3](TV2_REVIEW_TV3_W4.md) là PENDING FIX; cần log/Validation predictions/runtime/attestation gốc. Train350 parent ảnh/lớp; weights B3 theo crop counts, không phải bằng chứng image-level imbalance. B1 precision0.5688 trong bảng TV3 là sai, nguồn chuẩn0.5748610369. Không lấy softmax làm calibrated probability hay chọn threshold0.50/0.70 nếu chưa có Validation objective.

## 5. Model lock và evaluation protocol

[Selection lock](TV2_W4_MODEL_SELECTION_LOCK.json) cập nhật B2 verification thật và B3 partial verification, nhưng status vẫn FINAL MODEL LOCK PENDING, `final_selection_closed=false`, `locked_utc=null`. [Protocol](TV2_W4_EVALUATION_PROTOCOL.json) pending, liên kết SHA lock và sidecars cập nhật. Bản pending cũ được copy byte-exact trong continuation_01 và còn trong commit a66f41c. Lock gốc TV1 không sửa.

Không bịa timestamp/phê duyệt. User cho phép chạy sau đủ gate; CONTRIBUTING yêu cầu peer review trước merge main, không ghi thêm TV1 pre-Test signoff; TV1 acceptance W4 vẫn pending. Blocker thực tế là B3 reference/provenance chưa giải quyết, không phải thủ tục tự đặt thêm. Chỉ B2 dự kiến Test; B1 NOT EVALUATED BY FROZEN PLAN, B3 không Test. Threshold chưa chọn, argmax toàn bộ ảnh.

## 6. Test và integrity dữ liệu

Test vẫn600 ảnh/680 crop/495 chuỗi/98 địa điểm/75 ảnh mỗi lớp. Kiểm tra lại SHA600/600 khớp,0 download; manifests/provenance không đổi, không giao ID/file/location/sequence/file SHA giữa split theo metadata đã kiểm chứng. Giữ cặp RGB trùng, ảnh khó/multi-box/box nhỏ/sát mép. [Integrity](w4_evidence/continuation_01/integrity_before_finalization.json).

Không có official marker/run hoặc Test prediction. Macro-F1, Macro-Precision, Macro-Recall, Accuracy, per-class và CM Test **NOT RUN/NOT GENERATED**. [Báo cáo Test](TV2_W4_TEST_EVALUATION.md), [error analysis](TV2_W4_ERROR_ANALYSIS.md). Các CM trong continuation_01 thuộc Validation.

Giữ phương pháp evaluator: all-crop mean softmax theo imageID → argmax một prediction/ảnh, fixed0–7, zero_division0, no pre-average rounding; CPU/batch<=32/seed42; không train/augmentation/threshold exclusion. Script `scripts/evaluate_w4_test.py` giữ nguyên; pending gate chặn trước inference. Không đổi run ID hoặc xóa marker để chạy lại.

## 7. Cross-review và giới hạn

TV3 W4-03 **PENDING FIX**, chi tiết discrepancy và tài liệu cần bổ sung đã chỉ rõ. TV4 W4-04 **HANDOFF NOT VERIFIED** sau fetch; không dùng W3 thay W4, không sửa TV4. [Review TV4](TV2_REVIEW_TV4_W4.md).

600 ảnh không độc lập hoàn toàn theo495 chuỗi/98 địa điểm, mỗi lớp75 ảnh và một cặp RGB trùng; cân bằng lớp không đại diện tần suất tự nhiên. Chỉ closed-set8 lớp, GT-box classification khác MegaDetector demo; một số phiên bản detector dùng SWG khi train. Softmax chưa calibration, không suy ra loài lạ hay số cá thể từ điểm/số ảnh. Chưa có Test errors để khẳng định lớp khó/cặp nhầm/ảnh đêm; không đổi nhãn để tăng điểm.

## 8. Code, kiểm thử và tái lập

Thêm `scripts/verify_w4_checkpoints.py` (Train/Val only, strict metadata/CM/error IDs, lưu cả FAIL), `tests/test_w4_checkpoint_verification.py`. Không viết lại evaluator hay train. Các test mới kiểm tra marker official, mapping/provenance/config/preprocessing, crop-vs-parent weights, exact CM và error IDs ngay cả khi macro làm tròn giống nhau.

Regression cuối **335/335 PASS**; [66/66 W4 tests](w4_evidence/continuation_01/final_w4_tests.txt) là tập con nằm trong suite đầy đủ. [Log regression](w4_evidence/continuation_01/regression_tests_final.txt). Unit PASS không có nghĩa B3 reference PASS. Environment check UTF8, contract6/6, pip check và metadata validator đều PASS với log mới. Lỗi encoding CP1258 ở lần environment đầu được giữ, chạy lại UTF8 không sửa code chung.

```powershell
$py = 'outputs/w2_final_handoff/tv4_env/Scripts/python.exe'
$env:PYTHONIOENCODING = 'utf-8'
$env:TEMP = (Resolve-Path outputs/tv2_w4/test_tmp).Path
$env:TMP = $env:TEMP
& $py -m unittest discover -s tests -v
& $py scripts/verify_w4_checkpoints.py --model B2 --checkpoint experiments/B2_run01/checkpoints/best_model.pt --output outputs/tv2_w4/new_B2_verification
& $py scripts/verify_w4_checkpoints.py --model B3 --checkpoint experiments/B3_run01/checkpoints/best_model.pt --output outputs/tv2_w4/new_B3_verification
& $py scripts/evaluate_w4_test.py --checkpoint experiments/B2_run01/checkpoints/best_model.pt
```

Output verifier không overwrite; B3 lệnh reference hiện exit1 và lưu FAIL evidence. CPU Python3.12.14/torch2.8.0+cpu/Pillow12.2; CUDA diagnostic Python3.11.9/torch2.8.0+cu126/CUDA12.6/Pillow12.3 trên RTX4060Laptop; deterministic cuDNN true, benchmark false, cuDNN TF32 true, matmul TF32 false. Không dùng CUDA diagnostic để đổi Test plan.

## 9. Bảo vệ và xuất bản

528 file/weights/tài liệu trước phiên được hash, chỉ8 report/2 SHA sidecars canonical TV2 được cập nhật theo yêu cầu. B0/B1/B2/B3 weights nguyên byte; không sửa dữ liệu/nhãn, không ghi đè bằng chứng W4 lịch sử. JSON parse, links, staged scope/secrets/large files và diff check ở [summary](w4_evidence/continuation_01/checks_summary.json). Không stage ảnh, weights, environment hoặc ba tài liệu untracked.

Commit/push/remote equality và PR xem [publication](w4_evidence/continuation_01/publication.json). Tạo/cập nhật PR chỉ qua connector nếu có quyền; nếu403 thì dừng, không đọc credential/đi vòng bằng UI, cung cấp manual compare URL và prepared body. Không force push, tự merge hay đánh REVIEWER ACCEPTED.

## 10. Kết luận và điều kiện tiếp tục

[Completed work](TV2_W4_COMPLETED_WORK.md) ghi các phần DONE/PENDING/FAIL. B2 missing đã giải quyết, B3 missing đã giải quyết về file/metadata; blocker còn lại là B3 reference reproduction và original runtime/run evidence. Cần TV3 bàn giao/reconcile chính xác các ID, không yêu cầu train lại hoặc dùng Test. Chỉ khi đủ bằng chứng và final lock/protocol thực sự committed/gates PASS mới chạy Test một lần.

**W4-02 BLOCKED**. Chưa đủ Test metrics/CM để nghiệm thu, chưa có TV1 acceptance.
