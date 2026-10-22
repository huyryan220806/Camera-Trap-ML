# TV2 W4-02 handoff

Kết luận: **W4-02 BLOCKED**. Chưa đủ điều kiện final model lock và chưa chạy Test inference. Gói TV2 có evaluator, unit tests, audit/review, hồ sơ pre-Test cùng bằng chứng; không có metric Test giả, không đánh dấu REVIEWER ACCEPTED.

## 1. Mục tiêu và trách nhiệm

W4-02 khóa đánh giá và tổng hợp metric Test/Confusion Matrix, TV2 thực hiện, TV1 kiểm tra; phụ thuộc W3-02, W3-03, W4-03. TV2 còn review TV3 W4-03 và TV4 W4-04. Không mở rộng W5/W6.

Hai tài liệu thực tế có trong workspace là `Lich_trien_khai_6_tuan.docx` và `docs/Phan_cong_4_thanh_vien.xlsx` (không có hậu tố `(2)`). Đã đọc OOXML, đối chiếu phần Tuần 4 và sheet `Cong viec`, hàng 20–22: trách nhiệm/người review/phụ thuộc/sản phẩm khớp prompt. Trạng thái “Chưa bắt đầu” trong kế hoạch là ô kế hoạch, không phải bằng chứng runtime. [SHA và trích kế hoạch](w4_evidence/plans.json).

## 2. Git và nguồn bàn giao

Nhánh duy nhất `feat/baseline`. Bắt đầu `8a7c99c022fecec22778a6775428dc789a7becdd`; fetch toàn bộ remote; đọc main trước; HEAD là ancestor của main nên cập nhật fast-forward tới `0d822a91aa8cd694264c7af182434a91530e3fe2`. Không reset/rebase/force-push, không tự merge PR. Ba tệp cá nhân untracked được giữ nguyên.

| Nguồn | Commit audit | Trạng thái |
|---|---|---|
| main | 0d822a91aa8cd694264c7af182434a91530e3fe2 | W3 tích hợp, có audit B3 theo ảnh nguồn |
| TV1 metadata-split | 4bcf85cb07953d3a77cd916ec2895a6c6e6dfa6c | W4 inventory/lock nằm riêng, chưa trên main |
| TV2 baseline bắt đầu | 8a7c99c022fecec22778a6775428dc789a7becdd | W3 đã tích hợp main |
| TV3 crop-classifier | 65b99b9def6a147abe6a4d436c18a067f3f37dc4 | Quyết định B2 và B3 code/analysis W4 nằm riêng |
| TV4 demo | 254b40eab77b849647a2291aa0257c1b161b4da2 | Bàn giao W3 tích hợp main; W4 chưa xác minh |

Đã đọc CONTRIBUTING, experiment protocol, báo cáo tích hợp, bàn giao W3/W4. [Audit nguồn](w4_evidence/repository_audit.json) ghi FOUND/NOT FOUND theo exact commit và SHA. TV3 được kiểm thử ở thư mục ignored có nền main và chỉ overlay file W4 mới, không thay code thành viên khác. PR TV2 #4 đã merged; không có PR baseline mở trong truy vấn đầu phiên. Chi tiết xuất bản phiên này ở [publication](w4_evidence/publication.json).

## 3. Quyết định và khóa trước Test

TV3 giữ B2 `b2_run01` epoch21; checkpoint công bố 89,548,866 byte, SHA `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`. TV2 tính lại Macro-F1 Validation B2 0.7454765175 > B3 0.7410465263; không chọn lại bằng Test. [Review TV3](TV2_REVIEW_TV3_W4.md).

**FINAL MODEL LOCK PENDING**: thiếu file B2 local và artifact/provenance/checkpoint hash gốc B3; không thể giả nhận reload thật hay xác nhận run đầy đủ. [Model selection](TV2_W4_MODEL_SELECTION_LOCK.json) và [protocol](TV2_W4_EVALUATION_PROTOCOL.json) có SHA sidecar, trạng thái pending, `locked_utc=null`. Commit các bản pending không phải bằng chứng phương pháp đã khóa để mở Test. Lock gốc TV1 giữ nguyên trên nhánh TV1; trường `final_b2_b3_selection_closed=false` không bị ghi đè.

Ngưỡng 0.50 của TV3 và demo 0.70 chưa có bằng chứng tối ưu Validation. Không chọn threshold; đề xuất argmax toàn bộ ảnh vẫn hợp lệ khi model được khóa thực sự.

## 4. Dữ liệu, phương pháp và kết quả

Test manifest khớp 600 ảnh / 680 crop / 495 chuỗi / 98 địa điểm, 75 ảnh/lớp. Provenance và các frozen views đúng SHA. Đã đối chiếu 600 quality record TV1, 599 RGB duy nhất; ban đầu local thiếu 600 file Test; đã khôi phục và kiểm tra đủ 600/600 file bằng SHA/byte size/pixel hash/kích thước. [Restoration](w4_evidence/test_source_restoration.json). Có decode phục vụ QA dữ liệu, chưa có model forward trên Test. Không giao ID/file/location/sequence/file SHA giữa split theo metadata; kết quả source hash Train/Val riêng ở [hash audit](w4_evidence/train_val_source_hashes.json).

Một prediction mỗi ảnh: trung bình đủ softmax vector crop rồi argmax, class order 0–7, zero_division=0, không làm tròn trước macro. [Test evaluation](TV2_W4_TEST_EVALUATION.md) nêu exact hashes, preprocessing, chính sách một run và artifact. **Test Macro-F1/Precision/Recall/Accuracy, per-class metrics và CM: NOT RUN/NOT GENERATED**. B1 không nằm trong kế hoạch Test; không so B0 pilot với Test này.

## 5. Phân tích lỗi và giới hạn

[Error analysis](TV2_W4_ERROR_ANALYSIS.md) phân biệt cờ dữ liệu TV1, kết quả Validation và lỗi Test chưa có. Chưa đưa ví dụ Test sai khi chưa inference. Giữ cặp RGB duplicate, box nhỏ/sát mép/multi-box. 600 ảnh không độc lập hoàn toàn; dữ liệu cân bằng không đại diện tần suất tự nhiên; closed-set 8 lớp; box chuẩn khác demo MegaDetector; SWG có thể đã nằm trong nguồn train detector; softmax chưa calibration; không suy ra số cá thể.

## 6. Cross-review

- TV3 W4-03: **PENDING FIX**, đủ code/metric thứ cấp để kiểm tra nhưng thiếu artifact gốc và checkpoint provenance. Cần giải thích weighting theo crop khi parent images cân bằng và sửa bảng B1 precision. [Review](TV2_REVIEW_TV3_W4.md).
- TV4 W4-04: **PENDING FIX — W4-04 HANDOFF NOT VERIFIED**. Chỉ thấy W3. Chưa nghiệm thu màn hình sửa nhãn/export và benchmark W4. [Review](TV2_REVIEW_TV4_W4.md).

## 7. Kiểm thử và tái lập

Python 3.12.14 / torch 2.8.0+cpu / torchvision 0.23.0+cpu, CPU Intel64 Family6 Model186 Stepping2, GenuineIntel; CUDA runtime không khả dụng trong môi trường này. Máy có RTX4060 Laptop, môi trường CUDA cũ Python3.11.9/torch2.8.0+cu126/CUDA12.6 được phát hiện nhưng không dùng làm môi trường kiểm thử cuối. [Môi trường](w4_evidence/environment.json).

Môi trường 3.11 ban đầu thiếu requests và không có Path.is_junction; temp sandbox cũng chặn atomic rename. Giữ log lỗi ban đầu để minh bạch. Chuyển TEMP/TMP vào workspace và dùng Python3.12 đã có, `check_environment.py` PASS đúng pins; không sửa script chung hay làm nhẹ assertion. [Log cuối](w4_evidence/regression_tests_final.txt), [W4](w4_evidence/w4_tests_py312.txt), [contract](w4_evidence/contracts.txt), [dataset metadata](w4_evidence/comparison_validation_py312.json), [pip](w4_evidence/pip_check_py312.txt), [summary](w4_evidence/checks_summary.json).

```powershell
$py = 'outputs/w2_final_handoff/tv4_env/Scripts/python.exe'
$env:TEMP = (Resolve-Path outputs/tv2_w4/test_tmp).Path
$env:TMP = $env:TEMP
& $py -m unittest discover -s tests -v
& $py scripts/check_environment.py
& $py scripts/validate_results.py
& $py scripts/validate_comparison.py --metadata-only --report outputs/tv2_w4/comparison.json
& $py scripts/evaluate_w4_test.py
```

W4 tests kiểm tra aggregation, 1 prediction/ảnh, fixed class order/CM/macro metrics, SHA checkpoint, leakage, lock pending trước Test, lock/code chưa commit hoặc bị sửa, plan/threshold/đổi model bị chặn, một run và xuất artifact synthetic. Synthetic không dùng SWG hay model thật; không train lại baseline chính thức.

Kết quả cuối: **311/311 regression PASS**, gồm 48 test W4; thêm **6/6 test source restoration PASS** và **6/6 test TV3 W4 cô lập PASS**. Tổng 317 test local độc lập (48 W4 nằm trong 311), cộng 6 test TV3 cô lập. Suite HTTP cần cho phép socket loopback ngoài sandbox; log 300 test trước đó có 5 lỗi socket được giữ, không sửa assertion. Contract 6/6, check_environment Python3.12, pip check và dataset metadata validator PASS.

## 8. Integrity, xuất bản và nghiệm thu

[Protected baseline](w4_evidence/protected_baseline.json) khóa toàn bộ file main đầu phiên, B0/B1 weights local và ba tệp cá nhân; [after](w4_evidence/protected_after.json) ghi so sánh. B0 hash `d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680`, B1 hash `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c` khớp. B2 chưa có local nên verification là NOT FOUND, không PASS.

Chỉ stage mã TV2 và báo cáo/evidence W4; không ảnh, weights, secrets, môi trường hay tệp cá nhân. JSON parse, links, artifact hashes và diff check ghi ở checks_summary. Commit/push và remote equality phải xem publication thực tế, không suy từ tài liệu. PR chờ review TV1; chưa có bằng chứng TV1 phê duyệt.

## 9. DONE/PENDING/BLOCKED và kết luận

[Completed work](TV2_W4_COMPLETED_WORK.md) ghi việc đã làm và điều kiện tiếp tục. Chưa đạt sản phẩm bắt buộc metric Test + CM nên chưa đủ nghiệm thu W4-02. Blocker chính còn lại: checkpoint B2 truy cập được và hồ sơ run B3 gốc đủ provenance. Đủ 600 ảnh Test đúng SHA đã được khôi phục. TV4 W4 là công việc review riêng đang pending. Chưa sử dụng Test để tuning, chưa train lại model, chưa sửa dữ liệu/checkpoint/nhãn.

**W4-02 BLOCKED.**

## 10. Bằng chứng xuất bản cuối phiên

Implementation commit `eff4b1ddd74a94bd6fe54ca7c8078cff7100be50` đã push lên `origin/feat/baseline`; lệnh `git ls-remote` xác minh remote HEAD khớp local. Commit tài liệu tiếp theo ghi nhận biên nhận này; xem [publication](w4_evidence/publication.json).

**PR NOT CREATED**: GitHub connector trả `403 Resource not accessible by integration`. Automatic approval review từ chối đọc credential Git cho API và cũng từ chối mở giao diện tạo PR sau lỗi connector; các thao tác đó không được thực hiện. Cần người dùng phê duyệt trước một lần thử tạo PR tiếp theo. [Mô tả Draft PR đã chuẩn bị](w4_evidence/pr_draft.md). Không có phê duyệt TV1 hoặc tự merge.

Khôi phục dữ liệu dùng `scripts/prepare_w4_test_sources.py`: lượt đầu 599/600, một lỗi chuẩn hóa đường dẫn khi tạo thư mục song song; đã sửa trong code TV2 và chạy lại đạt 600/600. Giữ [log lượt đầu](w4_evidence/test_source_restoration_attempt01.json) và [kết quả cuối](w4_evidence/test_source_restoration.json). Dùng nguyên hàm kiểm tra RGB TV1, không tự đổi định nghĩa checksum. Ảnh chỉ nằm trong data/images ignored, không được stage.
