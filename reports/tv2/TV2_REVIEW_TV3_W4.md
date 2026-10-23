# TV2 review TV3 W4-03 — tiếp nối 23/10/2026

Kết luận: **PENDING FIX**. B2 đã được xác minh thật; B3 đọc/reload/forward được nhưng **không tái lập chính xác Validation reference** trên CPU hoặc CUDA. Không đổi tiêu chí PASS, không sửa weights/code TV3, không mở Test.

## Bằng chứng mới và blocker cũ đã giải quyết

- B2 local `experiments/B2_run01/checkpoints/best_model.pt`: 89,548,866 byte, SHA `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`, epoch21. Fresh process CPU tái lập đúng CM, 152 error IDs/labels và mọi metric phân loại; native/adapter max logit delta = 0 trên toàn bộ 680 crop. [Verification](w4_evidence/continuation_01/b2_validation/verification.json).
- B3 user-delivered `experiments/B3_run01/checkpoints/best_model.pt`: 89,548,994 byte, SHA `93ae48dd4b42fa6062daed3a9a1869d620bd7ba9e7ae2aa274085b061f76300b`, epoch14. Safe load `weights_only=True`, finite tensors, ResNet18/8 classes, mapping, preprocessing và embedded config khớp TV3 `65b99b9`. Embedded provenance khớp `comparison_v1`. [Inspection](w4_evidence/continuation_01/b3_checkpoint_inspection.json).
- B2/B3 dùng đúng cùng 600 Validation IDs / 680 crop, SHA nguồn Train 2.800 ảnh và Val 600 ảnh được kiểm tra. Không suy ra cùng population chỉ từ support. Không đọc Test trong các verifier checkpoint.
- Metadata B3 đánh dấu official, nhưng không có `run_id`/training commit; nguồn user + config/epoch/report phù hợp B3_run01, chưa chứng minh đầy đủ identity/runtime gốc. Best epoch14 được xác nhận trong file; early-stop epoch21 mới là báo cáo TV3, chưa kiểm chứng từ full log.

## Sai lệch Validation B3 còn tồn tại

| Nguồn | Macro-F1 | Macro-Precision | Macro-Recall | Accuracy | Đúng |
|---|---:|---:|---:|---:|---:|
| TV3/checkpoint reference | 0.7410465263 | 0.7406316201 | 0.7433333333 | 0.7433333333 | 446/600 |
| Reload CPU | 0.7410527052 | 0.7408712201 | 0.7433333333 | 0.7433333333 | 446/600 |
| Reload CUDA | 0.7427341579 | 0.7424361314 | 0.7450000000 | 0.7450000000 | 447/600 |

CPU khác reference hai ảnh: `cc293eb4-8c29-11eb-81b9-000d3a74c7de` (GT sambar: reference wild_pig, reload sambar), `cbdf50b3-8c29-11eb-a63b-000d3a74c7de` (GT common_palm_civet: reference đúng, CPU annamite_striped_rabbit). CUDA còn khác reference ảnh `cc293eb4...`; không có lỗi khác bị che giấu. Xem [runtime comparison](w4_evidence/continuation_01/b3_runtime_comparison.json), [CPU FAIL](w4_evidence/continuation_01/b3_validation_diagnostic/verification.json), [CUDA FAIL](w4_evidence/continuation_01/b3_validation_cuda_diagnostic/verification.json).

SHA ảnh, RGB crop và tensor normalized tại hai ID giống hệt giữa CPU env (Python3.12.14/torch2.8.0+cpu/Pillow12.2) và CUDA env (Python3.11.9/torch2.8.0+cu126/Pillow12.3, RTX4060 Laptop). Native/adapter logit delta bằng 0 trong từng runtime. Quan sát được độ nhạy runtime trên một dự đoán sát điểm; **chưa chứng minh nguyên nhân toàn bộ sai lệch với runtime TV3 gốc**. Không chọn runtime cho điểm đẹp hơn, không nới tolerance CM hoặc sửa metric bằng tay. Các lần chạy đều là Validation diagnostics, không Test official runs.

## Trọng số và giới hạn khoa học

Train vẫn 350 parent images/lớp; crop counts 359,350,421,360,352,353,450,480. TV3 code tính `u_c=3125/(8*n_crop_c)`, rồi normalize arithmetic mean=1. Trọng số khoảng 1.072638,1.100220,0.914673,1.069659,1.093969,1.090870,0.855727,0.802244, khớp định nghĩa công bố. Loss train: weighted CE theo crop → mean trong parent → mean qua parent. Nếu tính frequency theo parent thì mọi trọng số là 1. B2 đã cân bằng tổng ảnh nên B3 là tái trọng số các lớp theo crop, không phải chứng minh image-level imbalance.

Validation CE lưu trong checkpoint là **unweighted parent-mean crop CE**, không phải weighted training objective B3. B2 CPU CE 0.8177321676 vs checkpoint 0.8178; B3 CPU 0.7961626964 vs 0.7962. Không trộn loss khác định nghĩa; không gọi loss B2 là trùng tuyệt đối. Class weights thực tế không được serialize riêng; tái dựng từ config/code và frozen Train, chưa kiểm tra được log train gốc. `preflight_hash_check=false` là giới hạn lịch sử, không thay config để hợp thức hóa run cũ.

Quyết định TV3 giữ B2 ở commit `65b99b9` có trước mọi Test inference và B2 vẫn cao hơn các kết quả B3 local. Tuy nhiên không chuyển final lock sang LOCKED khi reference B3 chưa được đối chiếu đầy đủ. Margin +0.005/basis crop chưa có bằng chứng preregistration; không tự sửa. Bảng B1 Macro-Precision TV3 vẫn sai 0.5688; nguồn B1 TV2 là **0.5748610369**. Khuyến nghị threshold0.50 chưa được tối ưu Validation; softmax chưa calibration.

## TV3 cần bàn giao

Full log B3 gốc, standalone validation artifact, unrounded predictions/logits theo image/crop ID, runtime/GPU/cuDNN/TF32/determinism gốc, SHA/source attestation và training commit/run identity; giải thích/reconcile hai ảnh bất đồng. Không yêu cầu train lại hay đổi checkpoint/nhãn. Sáu test TV3 fixture W4 cũ vẫn là bằng chứng code, không thay thế việc kiểm định checkpoint thật. [Review machine-readable](w4_evidence/continuation_01/tv3_review.json).
