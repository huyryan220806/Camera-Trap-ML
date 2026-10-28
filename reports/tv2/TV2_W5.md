# TV2 tuần 5 đánh giá mô hình và tính tái lập

**W5 PARTIAL — đã kiểm định B2 và API TV4; DINO, phê duyệt protocol và browser
review còn BLOCKED.** Thực hiện28–29/10/2026 giờ Việt Nam, trên nhánh duy nhất
`feat/baseline`. Không nghiệm thu tuần6. Lịch28/10–03/11 là đề xuất của nhóm.

Commit trước đồng bộ `5fe9083367a78de8bf3ed652a6b58eb26a171e47`; nền triển khai
`60516f51fccbb85e6e266a022d94ea90d2239a11`. Kết quả Git cuối/PR được ghi trong
`w5_evidence/attempt_01/publication.json` sau push. Implementation của evaluator
và báo cáo đã có; technical verification B2 PASS; **reviewer approval chưa có,
PR chưa được tự merge**. Bốn trạng thái này không tương đương.

## 1. Đầu vào và quyết định phạm vi

Đã fetch origin và fast-forward TV2 tới nền tích hợp W4, trùng origin/main;
không cần merge main thêm, không conflict. Bốn tệp untracked người dùng giữ
nguyên, không stage. Không đổi nhánh/main/nhánh TV1/TV3/TV4. Không có AGENTS.md
trong inventory repo. [Source audit](w5_evidence/attempt_01/source_audit.json)
ghi nhánh/SHA, hash nguồn, checkpoint B0–B3 và tệp người dùng.

| Nguồn | Trạng thái đã kiểm tra |
| --- | --- |
| README/CONTRIBUTING/architecture/environment/experiment_protocol | Bản nền60516f5; giữ quy trình Test và Git |
| TV1 W3 và B1/B2 protocols/locks | Đã đọc, đối chiếu geometry và class order |
| TV1 W5 handoff/report/script/config/snapshot | Đủ ở `9abc9c572a9191e8a43a5abef05ebaf846b8356f`, verify-only trong snapshot riêng, chưa merge |
| TV4 return UI handoff | Ở snapshot TV1 W5, đã đối chiếu trạng thái thật PR8 |
| W5/W6 plan28/10 | Bản local và docs/plans của TV1 có cùng text; là kế hoạch mới, chưa phải approval chạy |
| Lịch sáu tuần DOCX | Đã đọc, trách nhiệm TV2 W5-02 là thực nghiệm+kiểm tra suy luận; kế hoạch mới thêm DINO/đối chứng |
| Trình bày27/10; reports/tv2/TV2_REVIEW.md | Không tìm thấy; không bịa tài liệu thay thế |
| TV3 DINO | Nhánh60516f5 chưa có W5 checkpoint/config/log/predictions/reload/adapter đủ điều kiện |
| PR7/PR8 | API GitHub: PR7 merged25/10; PR8 open, head fef2511, chưa merge |
| B2 checkpoint | Tồn tại, đúng89.548.866 bytes/SHA8787ffaf…, fresh-process kiểm lại |

Khác biệt với kế hoạch sáu tuần cũ: CSV/batch từng là sản phẩm dự kiến W5, nhưng
kế hoạch28/10 yêu cầu chỉ review nếu đã triển khai; PR8 chưa có CSV/batch, ghi
NOT_IMPLEMENTED. Không diễn giải thành nhóm đã miễn mọi sản phẩm về sau.
Không lấy mục tiêu88% hoặc ý tưởng DINO trong plan làm kết quả đã đạt.

## 2. Dữ liệu và phương pháp

`comparison_v1`: train2.800 ảnh/3.125 GT crop, val600 ảnh/680 GT crop, tám lớp
ID0–7, mỗi lớp val75 ảnh. SHA provenance
`d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`.
Đầy đủ hash manifest/class map và16 mục quy trình trong
[W5_PROTOCOL.md](W5_PROTOCOL.md). B2 dùng `b2/train.jsonl`, `b2/val.jsonl`.

[Metadata validation](w5_evidence/attempt_01/comparison.json):4.000 parent IDs,
không đổi split, B1/B2 cùng parent/nhãn/split, giao image_id/path/seq/location
giữa split đều0. Đây là integrity metadata, không chứng minh ảnh có trên máy.
[Train/Val pixel gate](w5_evidence/attempt_01/train_val_pixels.json): đủ3.400
ảnh được decode, đối chiếu kích thước/byte SHA/RGB SHA và metadata chất lượng.
B2 loader cũng kiểm file SHA2.800train+600val; inference đọc đủ680val crop.
Không kiểm perceptual/near-duplicate mới, không có xác nhận nhãn chuyên gia.

[TV1 verify-only](w5_evidence/attempt_01/candidates.json): nguồn31.589 ảnh,
train extension pool19.266, chọn1.665 ứng viên metadata; release SHA
`37db148ec716e5666431eca6f78a3440651f63c9359779dc456fd9decd26cd07`.
Không tải thêm ảnh, không dùng ứng viên để train. Holdout109 ảnh chưa đủ hỗ trợ
tám lớp, không phải Test mới được nghiệm thu. `training_ready/holdout_ready`
đều false theo snapshot đã kiểm. Nguồn handoff/hash trong
[handoff_sources.json](w5_evidence/attempt_01/handoff_sources.json).

B1 lịch sử: full-image ResNet18. B2: ResNet18 fine-tuned GT crops, RGB không
EXIF rotation, đúng bbox integer/padding0; Resize short256/CenterCrop224,
ImageNet mean/std, không augment khi val. Softmax từng crop → mean vector của
mọi crop cùng image_id → argmax. Đánh giá ở cấp ảnh, đủ manifest, không lọc score.
Macro-F1 là chính; accuracy top1 là phụ. Chọn checkpoint theo macro-F1; W5
seed/tie/budget còn DRAFT chờ TV3; chưa có lượt DINO chính thức.

TV2 bổ sung evaluator độc lập, hai schema crop/image JSONL, gate dữ liệu/class
order/hash/approval/artifact/reload, paired outcomes và recompute CM/metrics.
CLI **không nạp DINO**, không thay adapter TV4, không thể tự chứng minh approval
authorship. ARTIFACT_VERIFIED khác full inference acceptance; cần kiểm nội dung
và fresh-process adapter thật khi TV3 giao gói. DRAFT đã bị từ chối đúng trước
khi đọc predictions: [gate log](w5_evidence/attempt_01/candidate_draft_gate.log).

## 3. Kết quả validation thực tế

| Experiment | Model/nguồn | Train ảnh/crop | Val ảnh/crop | Accuracy top1 | Macro-F1 | Macro-P | Macro-R | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B2_W5_reference_attempt01 | ResNet18 IMAGENET1K_V1, seed42, epoch21 | 2800/3125 | 600/680 | 0,7466666667 | 0,7454765175 | 0,7484190017 | 0,7466666667 | PASS |
| N/A | DINO chưa bàn giao kiến trúc/checkpoint thực | N/A | N/A | N/A | N/A | N/A | N/A | BLOCKED |

Toàn bộ precision gốc trong
[experiment comparison](w5_evidence/attempt_01/validation_02/experiment_comparison.json).
Đối chứng B2 đúng448/600, sai152; checkpoint SHA
`8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`.
Không train lại B2. [600 raw predictions](w5_evidence/attempt_01/validation_02/b2_predictions.jsonl)
có đủ8scores, crop_count, experiment ID và SHA; schema/ID/nhãn/argmax được kiểm.
[Metrics recompute](w5_evidence/attempt_01/validation_02/b2_metrics.json) khớp
fresh-process verifier, CM và error IDs đã công bố của TV3, không sửa tham chiếu.

| ID / Loài | Precision | Recall | F1 | Support ảnh |
| --- | --- | --- | --- | --- |
| 0 large_antlered_muntjac | 0,565217 | 0,520000 | 0,541667 | 75 |
| 1 annamite_striped_rabbit | 0,731183 | 0,906667 | 0,809524 | 75 |
| 2 sambar | 0,691176 | 0,626667 | 0,657343 | 75 |
| 3 chinese_serow | 0,794521 | 0,773333 | 0,783784 | 75 |
| 4 common_palm_civet | 0,814286 | 0,760000 | 0,786207 | 75 |
| 5 masked_palm_civet | 0,698795 | 0,773333 | 0,734177 | 75 |
| 6 silver_pheasant | 0,985507 | 0,906667 | 0,944444 | 75 |
| 7 eurasian_wild_pig | 0,706667 | 0,706667 | 0,706667 | 75 |

[Per-class CSV](w5_evidence/attempt_01/validation_02/b2_per_class.csv).
Confusion matrix hàng thật/cột dự đoán; tổng600:

| True/Pred | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 39 | 5 | 13 | 1 | 2 | 5 | 0 | 10 |
| 1 | 1 | 68 | 0 | 1 | 4 | 1 | 0 | 0 |
| 2 | 12 | 2 | 47 | 3 | 1 | 6 | 1 | 3 |
| 3 | 1 | 2 | 5 | 58 | 1 | 1 | 0 | 7 |
| 4 | 1 | 10 | 0 | 4 | 57 | 3 | 0 | 0 |
| 5 | 5 | 6 | 1 | 1 | 4 | 58 | 0 | 0 |
| 6 | 1 | 0 | 1 | 2 | 0 | 1 | 68 | 2 |
| 7 | 9 | 0 | 1 | 3 | 1 | 8 | 0 | 53 |

[CM CSV](w5_evidence/attempt_01/validation_02/b2_confusion_matrix.csv).
Checkpoint nạp bằng weights_only trong tiến trình sạch, strict model state,
preprocessing/mapping khớp; native và demo adapter forward đủ680crops có max
logit delta **0,0**. [Verification](w5_evidence/attempt_01/b2_validation/verification.json).

CPU i7-13620H, RAM15,71GiB, threads4, batch32crop, workers0, Python3.12.14/
torch2.8.0+cpu. Model load0,307541s; validation wall65,793552s, toàn command
138,733359s. Validation wall chạy **cả native lẫn adapter**, gồm bước metric/
reference sau forward, không phải benchmark throughput thuần và không dùng
so tốc độ DINO khi chưa có cùng phép đo. Train/val hash preflight ở trước scope.
GPU không dùng. Original train log chưa có, checkpoint thiếu embedded run_id/
git_commit; nguồn train commit lấy từ handoff/lock, không tự bổ sung vào weights.

## 4. Phân tích và giới hạn

B2 mới kiểm định khớp kết quả validation lịch sử. Chưa có cải thiện DINO để
giải thích; delta accuracy/macro-F1, paired B2 đúng-DINO sai/ngược lại, runtime
DINO và biến động seed đều **N/A do thiếu artifact**. Không suy luận cải thiện
từ tên kiến trúc hoặc mục tiêu88%. Giữ B2 làm demo fallback, không thay weights TV4.

Trên validation này, lớp0 khó nhất(F1~0,542), tiếp theo lớp2(~0,657); nhầm0→2
13ảnh và2→0 12ảnh,0→7 và4→1 mỗi10ảnh. Lớp6 tốt nhất(F1~0,944). Đây là mẫu
nhầm quan sát được, chưa chứng minh nguyên nhân thị giác/nhãn. Validation cân
bằng75/lớp; không gọi lớp nào là ít mẫu trong val, còn dữ liệu mở rộng có hỗ trợ
không đều. Pilot được chọn có chủ đích, nhãn SWG nguồn cấp chuỗi; một seed và
val đã dùng phát triển không chứng minh khả năng khái quát ra địa điểm mới.

B1 lịch sử từ artifact thật: accuracy0,565, macro-F1 0,5624506868, epoch22.
B0 dùng pilot khác, ngoài bảng thắng/thua comparison_v1. B3 còn
**FAIL/UNRESOLVED** tái lập tham chiếu, không được đổi thành PASS.

Test B2 W4 chỉ dẫn từ [báo cáo đã khóa](TV2_W4_TEST_EVALUATION.md):
accuracy0,7300000000, macro-F1 0,7263366903, macro-P0,7302792835,
macro-R0,7300000000,438/600đúng,162sai,680GTcrops. Protocol/model khóa trước Test
tại `2a750c30c43d3b895577cf53d76f2d507321ec18`. Không phải metric mới W5, không
đưa vào chọn ứng viên. Không chạy official Test hoặc huấn luyện W5.

GT-box classifier khác detector-generated boxes và end-to-end performance.
MegaDetector đã dùng SWG khi train theo tài liệu dự án; demo SWG không phải
đánh giá detector độc lập. Softmax scores chưa calibrated; confidence thấp
không chứng minh detector sai hoặc loài lạ. Kiểm thử phần mềm không thay chất
lượng nhận dạng. API cold/warm chỉ1train ảnh/2request, không suy rộng mọi máy.

**Sai lệch cần reviewer xem:** đã gọi nhầm validator raster toàn snapshot rồi
dừng Ctrl+C(last progress750/4000, số/IDdecode thực không xác định). Scope gồm
Test; không model forward/metric/selection trên Test. Giữ log, không nhận PASS;
đã chạy gate train/val riêng3400PASS. Không tuyên bố toàn session không truy cập
raster Test. [Deviations](w5_evidence/attempt_01/deviations.json) giữ sự cố này
cùng các lỗi môi trường TEMP/socket và browser timeout. Tất cả đầu ra W1–W4,
split/nhãn và checkpoint giữ nguyên; không dùng reset/force-push.

## 5. TV4 và kiểm thử

[Review độc lập](TV2_W5_TV4_REVIEW.md): đúng head PR8 fef2511,15API assertions
PASS trên B2 thật và mock được gắn nhãn; revision riêng, original immutable,
GET reload khớp, stale409, corrupt read error, synthetic detector-miss riêng.
Browser1440/390/320, click box/hàng và browser JSON export **BLOCKED** do
localhost/browser app permission timeout; không có screenshot độc lập.
CSV/batch chưa trong PR8. Chưa APPROVE/merge PR8.

| Check | PASS | FAIL/ERROR | SKIP | Evidence |
| --- | --- | --- | --- | --- |
| Final full unittest | 409 | 0 | 0 | regression_03.log; unittest48,218s, runner53,600s |
| Trong đó W5 mới | 32 | 0 | 0 | Các test_w5_validation trong full log |
| Exact TV4 snapshot suite | 44 | 0 | 0 | tv4_tests_02.log;8,534s |
| TV1 W5 snapshot suite | 12 | 0 | 0 | tv1_tests.log;0,038s |
| check_environment.py | PASS | 0 | 0 | environment_final.log |
| validate_results.py | 6 fixtures | 0 | 0 | contracts_final.log |
| Data metadata/candidates/Train-Val pixels | PASS | 0 | 0 | comparison/candidates/train_val_pixels JSON |
| B2 independent validation/reload/native-adapter | PASS | 0 | 0 | b2_validation/verification.json |
| DRAFT gate rejection | Expected BLOCKED | Exit1 intended | N/A | candidate_draft_gate.log |

Lệnh regression: interpreter đã nêu, `-X utf8 -m unittest discover -s tests -v`.
Log ghi commit nền60516f5 và source hashes bản W5 trong
[checks_summary.json](w5_evidence/attempt_01/checks_summary.json). Các lượt lỗi
trước vẫn giữ: sandbox socket10013; defaultTEMP access denied; TEMP dưới
repo/outputs khiến một path guard test sai điều kiện. Đổi sang writableTEMP
ngoài repo rồi409PASS, không sửa/bỏ test hoặc thêm proof giả. `git diff --check`
được kiểm trước commit; publication ghi kết quả cuối. Bằng chứng có
[SHA index](w5_evidence/attempt_01/artifact_index.json).

## 6. Tiến độ và bàn giao

| Task | Đã làm | Trạng thái còn lại |
| --- | --- | --- |
| W5-01 | Đối chiếu data/hash/pixels, review TV1 W5, protocol đầy đủ | DRAFT chờ TV3 chốt tie/seed/budget và TV1 đối chiếu |
| W5-02 | B2 positive control, schema/evaluator/independent metrics/table thật | DINO BLOCKED; chưa có so sánh ứng viên |
| W5-03 | Exact PR8/API15PASS/unit44PASS/static review | Browser UI acceptance BLOCKED |
| W5-04 | B2 hash/fresh reload/native-adapter delta0 | DINO adapter/reload BLOCKED; giữ B2 |
| W5-05 | Báo cáo/chương thực nghiệm, evidence,409testsPASS | Gửi reviewer, chưa có reviewer approval |

Danh mục file/code/lệnh tiếp tục ở [handoff](../../docs/handoff_tv2_w5.md) và
[progress](../../docs/progress_tv2_w5_w6.md). Chương tích hợp báo cáo chung:
[W5_EXPERIMENT_CHAPTER.md](W5_EXPERIMENT_CHAPTER.md).

TV1: đối chiếu data và quality release nếu mở rộng. TV3: chốt protocol và bàn
giao model/log/predictions/code thật. TV4: hỗ trợ browser retest, chỉ sửa lỗi
được tái hiện trên nhánh họ. TV2: hoàn tất kiểm chứng ứng viên/browser và cập
nhật so sánh sau đầu vào hợp lệ. Đủ điều kiện gửi **review phần đã triển khai**;
chưa đủ nghiệm thu W5 COMPLETE hoặc chuyển sang nghiệm thu W6. Không bắt buộc
đạt88%, nhưng cần protocol được phê duyệt, input/model được xác minh và review
UI có bằng chứng trước khi kết luận hoàn tất toàn bộ.
