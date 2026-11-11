# TV2 W6 — DATA EXPANSION OFFICIAL DATA EXPANSION APPROVAL

**Ngày lập:** 08/11/2026  
**Vai trò:** TV2 (Baseline & Evaluation)  
**Trạng thái đề xuất:** **`READY_FOR_TV2_APPROVAL`** *(Chờ người dùng xác nhận và ký duyệt)*  
**Kho nguồn:** `huyryan220806/Camera-Trap-ML` (Nhánh `feat/baseline`)  
**Commit nguồn TV1:** `11e451071f58146522df20e1890cc6fe6e488eb0`  
**Tập dữ liệu:** `train_expansion_w6_v1`  
**Release Provenance SHA-256:** `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`  

---

## 1. Kết quả kiểm tra 3 mẫu Cầy (Indices 44, 52, 59)

| Review Index | Image ID (Full UUID) | Nhãn nguồn Git | Quyết định TV1 | Phân tích thị giác TV2 & Diễn giải |
| :---: | :--- | :--- | :---: | :--- |
| 44 | `d814f364-8c29-11eb-bd78-000d3a74c7de` | `common_palm_civet` | `retain_metadata_label` | Nhãn nguồn là Cầy vòi hương (*Paradoxurus hermaphroditus*). Báo cáo cũ viết nhầm thành 'cầy vòi mốc' do lỗi diễn đạt tiếng Việt. TV1 ghi rõ: 'giữ nhãn nguồn, không kết luận phân loài'. Giữ nguyên nhãn nguồn. |
| 52 | `d2f341cf-8c29-11eb-83a1-000d3a74c7de` | `masked_palm_civet` | `retain_metadata_label` | Nhãn nguồn là Cầy vòi mốc (*Paguma larvata*). Báo cáo cũ viết nhầm thành 'cầy vòi hương' do lỗi diễn đạt tiếng Việt. TV1 ghi rõ: 'giữ nhãn nguồn'. Giữ nguyên nhãn nguồn. |
| 59 | `d4ea5bb4-8c29-11eb-9c1b-000d3a74c7de` | `masked_palm_civet` | `retain_metadata_label` | Nhãn nguồn là Cầy vòi mốc (*Paguma larvata*). Báo cáo cũ viết nhầm thành 'cầy vòi hương' do lỗi diễn đạt tiếng Việt. TV1 ghi rõ: 'giữ nhãn nguồn'. Giữ nguyên nhãn nguồn. |

> [!NOTE]
> **Kết luận chuyên môn TV2:** Đây hoàn toàn là **lỗi diễn đạt thuật ngữ tiếng Việt** trong bản nháp mô tả trước đây, không phải sự cố nghi ngờ nhãn hay sai sót metadata. Trong điều kiện ảnh bẫy hồng ngoại ban đêm, việc phân định chi tiết hai loài cầy khi không thấy rõ mặt nạ là rất khó khăn. Quyết định tuân thủ nghiêm ngặt nhãn gốc của TV1 là hoàn toàn chính xác theo hợp đồng W6.

---

## 2. Bảng tổng hợp trạng thái các cổng nghiệm thu (Gate Status)

| Cổng kiểm định | Bằng chứng gốc đối chiếu | Kết quả | Trạng thái |
| :--- | :--- | :---: | :---: |
| **RELEASE_PROVENANCE_SNAPSHOT** | `provenance.json` (SHA `a6ac693306...dda5`), 19 files metadata | Khớp 100% | **PASS** |
| **CANDIDATE_PARTITION_ACCOUNTING** | `summary.json`, `decisions.jsonl` (1.665), `additional_train.jsonl` (1.446), `excluded.jsonl` (219) | 1.446 giữ + 219 cách ly | **PASS** |
| **PROTECTED_SPLITS_PRESERVATION** | Git blobs `comparison_v1/val.jsonl` (600), `test.jsonl` (600) so với commit `cfcf006` | Khớp 100%, 0 test raster mở | **PASS** |
| **LEAKAGE_AND_QUARANTINE_AUDIT** | Giao cắt tập hợp Train vs Val/Test/Holdout; `features.jsonl` | Không rò rỉ; cách ly 5 exact, 191 near, 23 visual | **PASS** |
| **RETAINED_RASTER_DECODE_INTEGRITY** | Giải mã Pillow 1.446 ảnh mới từ `swg_train_expansion_w6_v1_additional.zip` | 1.446/1.446 ảnh hợp lệ, pixel SHA khớp | **PASS** |
| **VISUAL_REVIEW_OF_QUARANTINE** | 10 Contact Sheets + `zoom_64.jpg` từ `visual_review_contact_sheets.zip` (SHA `709fea5113...13b0`) | 80/80 mẫu khớp pixel template (MAE <= 0.50); 23 mẫu cách ly xác thực | **PASS** |
| **HOLDOUT_RASTER_AUDIT** | Tái tải độc lập 109 ảnh từ URL nguồn LILA; fresh-process decode, byte SHA-256 & RGB pixel SHA-256 | 109/109 PASS (63 MPO, 46 JPEG, 173.588.482 bytes, 0 rò rỉ, 0 inference) | **PASS** |
| **TV2_DATA_ACCEPTANCE (GATE R5/R6)** | Tổng hợp toàn diện 7 cổng độc lập trên | Đủ 100% bằng chứng kỹ thuật và raster theo protocol W6 | **READY_FOR_TV2_SIGNOFF** |

---

## 3. Các hạn chế và lưu ý quan trọng (Constraints & Limitations)

2. **Phạm vi xác thực nhãn (Label Verification Scope):**
   - Đợt kiểm định thị giác của TV2 chỉ thực hiện trên mẫu phân tầng cố định **80 ảnh** (10 ảnh/loài) theo Seed 42.
   - **Receipt KHÔNG khẳng định toàn bộ 1.446 ảnh mở rộng đã được chuyên gia sinh học xác nhận nhãn**; 1.446 ảnh này kế thừa nhãn metadata gốc từ đơn vị khảo sát sau khi vượt qua các bộ lọc tự động về độ phân giải, định dạng và tính toàn vẹn pixel.
   - **191 ảnh nghi near-duplicate tiếp tục là diện nghi vấn bị cách ly bảo thủ**, không tuyên bố chúng là ảnh trùng lặp đã xác thực.

1. **Mất cân bằng dữ liệu ở loài Thỏ vằn:**
   - Loài thỏ vằn (`annamite_striped_rabbit`) chỉ được bổ sung thêm đúng **10 ảnh** (tổng Train là 360 ảnh), trong khi các loài khác có từ 514 đến 589 ảnh.
   - Theo giao thức W6, không áp dụng trọng số lớp mới hay kỹ thuật oversampling trong đợt huấn luyện R5/R6 để đánh giá chính xác tác động thuần túy của dữ liệu mở rộng.
2. **Trạng thái 191 ảnh nghi near-duplicate:**
   - Được cách ly bảo thủ theo cụm pHash/dHash và timestamp.
   - **Không tuyên bố chúng là ảnh trùng lặp đã xác nhận**, mà coi đây là biện pháp phòng ngừa rò rỉ an toàn.
3. **Bảo toàn Test W4:**
   - Toàn bộ 600 ảnh raster của Official Test W4 được giữ nguyên vẹn, không mở, không giải mã, không rò rỉ.
4. **Kỷ luật khóa huấn luyện R5/R6:**
   - Bản nháp này **KHÔNG tự cấp quyền huấn luyện R5/R6**.
   - Lượt chạy R5 và R6 tiếp tục bị khóa (**`CONDITIONAL / BLOCKED`**) trong registry cho đến khi người dùng chính thức ký duyệt.

---

## 4. Hồ sơ bằng chứng và kiểm thử đã thực hiện

- Draft Receipt: [`reports/tv2/TV2_W6_DATA_EXPANSION_APPROVAL_RECEIPT.json`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/reports/tv2/TV2_W6_DATA_EXPANSION_APPROVAL_RECEIPT.json)
- Báo cáo rà soát trực quan: [`reports/tv2/TV2_W6_TV1_VISUAL_REVIEW_INDEPENDENT_AUDIT_2026-11-08.md`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/reports/tv2/TV2_W6_TV1_VISUAL_REVIEW_INDEPENDENT_AUDIT_2026-11-08.md)
- Bằng chứng 80 mẫu máy đọc: [`outputs/tv2_w6/visual_review_20261108/official_80_audit_reconciliation.json`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/visual_review_20261108/official_80_audit_reconciliation.json)
- Bằng chứng 53 sai lệch cũ: [`outputs/tv2_w6/visual_review_20261108/mismatches_53.json`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/visual_review_20261108/mismatches_53.json)
- Nhật ký kiểm thử tự động:
  - [`outputs/tv2_w6/final_data_approval_prep_20261108/test_w6_validation.log`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/final_data_approval_prep_20261108/test_w6_validation.log) (51 tests PASS)
  - [`outputs/tv2_w6/final_data_approval_prep_20261108/test_w5_validation.log`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/final_data_approval_prep_20261108/test_w5_validation.log) (32 tests PASS)
  - [`outputs/tv2_w6/final_data_approval_prep_20261108/test_contracts_and_evaluation.log`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/final_data_approval_prep_20261108/test_contracts_and_evaluation.log) (22 tests PASS)
