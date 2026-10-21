# TV2 W3 B1/B2 comparison

Trạng thái: **B1/B2 COMPARISON PENDING – OFFICIAL B2 RESULTS REQUIRED**.

## Eligibility gate

| Điều kiện công bằng | B1 | B2 | Kết luận |
|---|---|---|---|
| Dataset TV1 `comparison_v1` | PASS | Chưa có official run | PENDING |
| Cùng 600 parent validation images | PASS | Chưa có bằng chứng run | PENDING |
| Cùng class mapping 8 lớp | PASS | Config/code có hỗ trợ; run N/A | PENDING |
| Không data leakage | PASS theo frozen provenance | Chưa có run evidence | PENDING |
| Evaluation unit cấp ảnh | Một dự đoán/ảnh | Mean probability mọi crop/`image_id` trong code | PENDING RUN |
| Crop padding | N/A | Protocol yêu cầu 0 | PENDING RUN |
| Protocol/hyperparameters chung | PASS | Còn bốn lỗi triển khai P1 | FAIL |
| Official checkpoint + reload | PASS | Không có | FAIL |
| Không dùng test để selection | PASS | Chưa có run | PENDING |

## Metric table

| Metric | B1 full image | B2 crop | Chênh lệch B2 − B1 |
|---|---:|---:|---:|
| Validation Macro-F1 | **0,5624506868** | N/A | N/A |
| Macro-Precision | **0,5748610369** | N/A | N/A |
| Macro-Recall | **0,565** | N/A | N/A |
| Accuracy | **0,565** | N/A | N/A |
| Validation loss | **1,3379992723** | N/A | N/A |
| Best epoch | **22** | N/A | N/A |
| Epoch hoàn thành | **29** | N/A | N/A |
| Tổng thời gian train/run | **14.805,386 giây** | N/A | N/A |
| Thời gian train | **11.409,952 giây** | N/A | N/A |
| Peak GPU memory | **895.525.376 byte** | N/A | N/A |
| Số tham số trainable | **11.180.616** | N/A | N/A |
| Validation support | **600 parent images** | N/A | N/A |
| Checkpoint reload | **PASS** | NOT TESTED | N/A |

B1 đã có confusion matrix, learning curves và per-class precision/recall/F1 trong
`experiments/B1_run01/results/`. B2 chưa có các artifact tương ứng nên chưa thể
đặt hai biểu đồ cạnh nhau, phân tích loài cải thiện/suy giảm hoặc kết luận tác
động của crop. Không dùng synthetic metrics hay crop-level metrics để điền chỗ
trống.

## Blocker

TV3 commit `c01a751` PASS 23/23 test cô lập nhưng vẫn tắt source hash preflight,
tính grouped loss trong từng shuffled batch, cho phép ghi đè official output và
không có fresh-process reload. Nhánh cũng chưa có official B2 artifacts. Chi tiết:
[review TV3](TV2_REVIEW_TV3_W3.md).

Chỉ tính chênh lệch và chọn mô hình theo validation Macro-F1 sau khi TV3 cung cấp
run B2 đáp ứng toàn bộ eligibility gate. Tập test không được dùng trong W3.
