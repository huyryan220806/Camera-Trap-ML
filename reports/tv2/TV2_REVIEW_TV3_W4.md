# TV2 review TV3 W4-03 — quyết định nhóm chọn B2

**MODEL SELECTION: B2 SELECTED BY TEAM. B3 TECHNICAL REVIEW: PENDING FIX / UNRESOLVED.** Người dùng đã thông báo nhóm chính thức chọn B2 bằng Validation và chấp nhận giới hạn tái lập của thử nghiệm B3 không được chọn. [Decision record](w4_evidence/continuation_02/team_b2_decision.json) ghi thời điểm tạo thực tế, không bịa chữ ký hoặc TV1 acceptance. Quyết định TV3 gốc tại65b99b9 vẫn được lưu nguyên byte trong [bản nguồn](w4_evidence/continuation_01/tv3_decision_source.md).

| Nội dung | Kết quả |
|---|---|
| B2 independent Validation reproducibility | PASS:600 parents/680 crops, CM và152 error IDs khớp |
| B3 checkpoint readable/safe load/forward | PASS |
| B3 exact reference reproducibility | FAIL / UNRESOLVED trên CPU và CUDA |
| B3 selected for Test | NO |
| Reproducibility limitation | ACCEPTED FOR MODEL SELECTION BY TEAM |
| TV3 original evidence completeness | PARTIAL: chưa có full log/run identity/training commit/runtime provenance gốc |
| TV3 toàn diện / TV1 W4-02 acceptance | Chưa được xác nhận |

B2 SHA `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5`,89,548,866 byte,epoch21. B3 SHA `93ae48dd4b42fa6062daed3a9a1869d620bd7ba9e7ae2aa274085b061f76300b`,89,548,994 byte,epoch14. B3 SHA được tính từ file người dùng, không giả có independent checksum gốc. Embedded config/mapping/preprocessing/provenance khớp snapshot; không đồng nghĩa xác minh đầy đủ original run. B2 fresh process [PASS](w4_evidence/continuation_01/b2_validation/verification.json), B3 [CPU FAIL](w4_evidence/continuation_01/b3_validation_diagnostic/verification.json), [CUDA FAIL](w4_evidence/continuation_01/b3_validation_cuda_diagnostic/verification.json).

## Validation — không phải Test

| Nguồn | Macro-F1 | Macro-Precision | Macro-Recall | Accuracy |
|---|---:|---:|---:|---:|
| B2 fresh CPU |0.7454765175|0.7484190017|0.7466666667|0.7466666667|
| B3 reference TV3 |0.7410465263|0.7406316201|0.7433333333|0.7433333333|
| B3 CPU |0.7410527052|0.7408712201|0.7433333333|0.7433333333|
| B3 CUDA |0.7427341579|0.7424361314|0.7450000000|0.7450000000|

CPU khác reference hai ID: `cc293eb4-8c29-11eb-81b9-000d3a74c7de` (GT sambar, reference wild_pig, local sambar), `cbdf50b3-8c29-11eb-a63b-000d3a74c7de` (GT common_palm_civet, reference đúng, CPU rabbit). CUDA còn khác ID thứ nhất. RGB/crop/tensor tại hai ID khớp giữa môi trường; native/adapter max delta0 trong từng runtime. Có runtime sensitivity, chưa giải thích đầy đủ reference gốc. [Bảng so sánh](w4_evidence/continuation_01/b3_runtime_comparison.json). Không nới tolerance, chọn runtime theo điểm, sửa metric hoặc chuyển FAIL thành PASS.

Train350 parent/lớp; crop counts359,350,421,360,352,353,450,480. B3 weights là inverse crop frequency normalized mean1, không chứng minh mất cân bằng ảnh. Train objective weighted crop CE → mean trong parent → mean parents; Validation loss unweighted parent-mean crop CE. B2 CPU loss0.8177321676 so với checkpoint0.8178, không gọi loss exact. B1 Macro-Precision chuẩn0.5748610369; bảng TV3 ghi0.5688 là sai. Margin+0.005 chưa xác minh preregistration; B2 cao hơn B3 theo các nguồn Validation hiện có. Khuyến nghị threshold0.50 chưa có Validation objective, không dùng trong official Test.

TV3 còn cần full log, unrounded original predictions/logits, runtime/GPU/cuDNN/TF32/determinism, SHA/source attestation và training commit/run identity để reconcile B3. Không yêu cầu train lại. Những việc này vẫn pending review W4-03, nhưng sau quyết định nhóm chúng không chặn Test B2 đã xác minh độc lập. Không sửa nhánh TV3; mọi bằng chứng thất bại và blocker lịch sử giữ nguyên.
