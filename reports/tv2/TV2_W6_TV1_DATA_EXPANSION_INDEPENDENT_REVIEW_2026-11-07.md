# TV2 W6 — Independent TV1 Data Expansion Review (`train_expansion_w6_v1`)

**Ngày kiểm định:** 07/11/2026
**Vai trò:** TV2 (Baseline & Evaluation)
**Nhánh làm việc:** `feat/baseline`
**Nhánh nguồn TV1:** `feat/metadata-split` (commit `11e451071f58146522df20e1890cc6fe6e488eb0`, nội dung `c1d2789fdc844ebd62074850034004aa5a43f5ae`)
**Release Provenance SHA-256:** `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`
**Gói dữ liệu ảnh bổ sung (Local ZIP):** `swg_train_expansion_w6_v1_additional.zip` (2.246.204.406 byte, SHA-256 `a88bfbf99aa25ac70637f35dca6056851e4c300dd89c3906185f943b13b3f659`)
**Trạng thái kiểm định TV2:** **PENDING REVIEW — BLOCKED** (Không cấp TV2 Approval; R5/R6 tiếp tục bị khóa)

---

## 1. Tóm tắt kết luận và trạng thái các cổng (Decision Gates)

| Cổng kiểm định | Trạng thái | Chi tiết đối soát độc lập của TV2 |
| :--- | :---: | :--- |
| **RELEASE_PROVENANCE_SNAPSHOT** | **PASS** | Khớp chính xác SHA-256 `a6ac693306...dda5` của `provenance.json`. Toàn bộ 19 file metadata snapshot trong Git khớp byte-for-byte với manifest và checksums. |
| **CANDIDATE_PARTITION_ACCOUNTING** | **PASS** | 1.665 ứng viên = 1.446 giữ + 219 cách ly. Train mở rộng = 4.246 ảnh / 4.729 crops. 8 lớp cố định. B1/B2 đồng nhất. |
| **PROTECTED_SPLITS_PRESERVATION** | **PASS** | Validation cũ giữ nguyên 600 ảnh / 680 crops / 75 ảnh mỗi lớp. Git blobs của Val và Test trong `comparison_v1` khớp 100% với commit nền `cfcf006`. Không mở raster Test W4. |
| **LEAKAGE_AND_QUARANTINE_AUDIT** | **PASS** | Không rò rỉ ID/path/seq_id/location hay byte/pixel SHA với Val, Test hay Holdout. 5 exact RGB, 191 suspected near-duplicates và 23 ambiguous samples được cách ly toàn diện. |
| **RETAINED_RASTER_DECODE_INTEGRITY** | **PASS** | 1.446/1.446 ảnh mới được giữ đã giải mã thành công trong process mới: kích thước, byte size, file SHA-256 và RGB pixel SHA-256 khớp 100% metadata. 0 ảnh Test giải mã. |
| **VISUAL_REVIEW_OF_QUARANTINE** | **PENDING** | 57/80 mẫu trực quan được giữ có raster và box hợp lệ trên đĩa. Tuy nhiên, 23/80 mẫu cách ly mơ hồ và toàn bộ 219 ảnh cách ly không có file raster/contact sheets trong gói bàn giao. |
| **TV2_DATA_ACCEPTANCE (GATE R5/R6)** | **PENDING** | Chưa đủ điều kiện nghiệm thu hoàn chỉnh do thiếu bằng chứng thị giác trực tiếp của các ảnh bị cách ly. **R5 và R6 tiếp tục bị khóa (CONDITIONAL/BLOCKED)**. |

---

## 2. Bước 1 — Kiểm tra hồ sơ bàn giao & Provenance

### 2.1. Tài liệu và commit đối chiếu
- **Protocol W6:** [`docs/experiment_protocol_w6.md`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/docs/experiment_protocol_w6.md) ghi nhận release provenance dự kiến: `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`.
- **Kế hoạch TV1:** `docs/plans/TV1_W6.md` (thuộc commit `c1d2789` trên nhánh `feat/metadata-split`) xác định phạm vi 1.665 ứng viên W5, tối đa 4.465 ảnh train, và quy tắc cách ly không nới lỏng.
- **Báo cáo TV1:** `reports/tv1_w6/REPORT.md` (thuộc commit `c1d2789`) và file bàn giao `docs/handoff_tv1_w6.md`.
- **Registry hiện hành:** [`experiments/w6/registry.json`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/experiments/w6/registry.json) duy trì `data_review.status = PENDING`.

### 2.2. Kiểm tra tính toàn vẹn của Release Manifest
- Đã đọc trực tiếp 19 file metadata snapshot từ Git commit `11e451071f58146522df20e1890cc6fe6e488eb0`:
  1. `additional_train.jsonl` (1.446 dòng)
  2. `audit.json`
  3. `b1/train.jsonl` (4.246 dòng)
  4. `b2/train.jsonl` (4.729 dòng)
  5. `baseline_references.json`
  6. `class_map.json` (8 lớp)
  7. `decisions.jsonl` (1.665 dòng)
  8. `exact_duplicates.json`
  9. `excluded.jsonl` (219 dòng)
  10. `features.jsonl` (5.774 dòng)
  11. `holdout_quality.jsonl` (109 dòng)
  12. `near_duplicates.json` (347 cặp)
  13. `policy.json`
  14. `preserved_original_duplicates.json`
  15. `provenance.json` (SHA-256 = `a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`)
  16. `summary.json`
  17. `train.jsonl` (4.246 dòng)
  18. `visual_queue.jsonl` (80 dòng)
  19. `visual_review.json` (80 dòng đánh giá)
- Toàn bộ 19 file đều khớp mã băm SHA-256 đã công bố trong `provenance.json`.

### 2.3. Bằng chứng và file còn thiếu (Missing Artifacts)
1. **Thiếu gói Contact Sheets:** `outputs/tv1_w6/visual_review_contact_sheets.zip` (chứa 10 contact sheets `sheet_01.jpg` đến `sheet_10.jpg` và `zoom_64.jpg`) không có trong workspace và không có trong Git.
2. **Thiếu raster của 219 ảnh cách ly:** Gói `swg_train_expansion_w6_v1_additional.zip` chỉ chứa 1.446 ảnh được giữ và 19 file snapshot. Không có file ảnh raster của 219 ảnh cách ly (gồm 23 ảnh mơ hồ nghi nhãn sai và 191 ảnh nghi trùng).

---

## 3. Bước 2 — Đối soát dữ liệu & Contract W6

### 3.1. Phân chia ứng viên & Tập huấn luyện mở rộng
- **Ứng viên:** Tổng số 1.665 ảnh ứng viên từ `w5_candidates_v1/train_extension_candidates.jsonl`.
  - Giữ lại (`additional_train.jsonl`): **1.446 ảnh**.
  - Cách ly (`excluded.jsonl`): **219 ảnh**.
  - Đối soát tập hợp: $\text{Retained} \cap \text{Quarantined} = \emptyset$ và $\text{Retained} \cup \text{Quarantined} = \text{Candidates}$ (khớp 100%).
  - Mọi thuộc tính gốc (`label`, `split`, `boxes`) từ ứng viên sang snapshot giữ nguyên.
- **Tập Train tổng hợp:**
  - Tập Train cũ (`comparison_v1/train.jsonl`): **2.800 ảnh / 3.125 crops**. Toàn bộ 2.800 ảnh cũ được giữ nguyên 100% không suy suyển.
  - Tập Train mở rộng (`train.jsonl` & `b1/train.jsonl`): $2.800 + 1.446 =$ **4.246 ảnh**.
  - Crop Ground-Truth (`b2/train.jsonl`): $3.125 + 1.604 =$ **4.729 crops**.

### 3.2. Phân bố 8 lớp và Cảnh báo mất cân bằng (Class Imbalance)
Class map cố định đúng chuẩn 8 lớp của W5/W6:

| Class ID | Tên loài | Ảnh Train cũ | Ảnh bổ sung | Tổng ảnh Train W6 | Tổng Crop W6 | Tỷ lệ ảnh |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 0 | `large_antlered_muntjac` (Hoẵng lớn) | 350 | 234 | 584 | 602 | 13.75% |
| 1 | `annamite_striped_rabbit` (Thỏ vằn) | 347 | **13** | **360** | **360** | **8.48%** |
| 2 | `sambar` (Nai) | 350 | 222 | 572 | 666 | 13.47% |
| 3 | `chinese_serow` (Sơn dương) | 350 | 164 | 514 | 529 | 12.11% |
| 4 | `common_palm_civet` (Cầy vòi hương) | 350 | 186 | 536 | 539 | 12.62% |
| 5 | `masked_palm_civet` (Cầy vòi mốc) | 350 | 171 | 521 | 528 | 12.27% |
| 6 | `silver_pheasant` (Gà lôi trắng) | 353 | 217 | 570 | 735 | 13.42% |
| 7 | `eurasian_wild_pig` (Lợn rừng) | 350 | 239 | 589 | 770 | 13.87% |
| **Tổng** | **8 lớp** | **2.800** | **1.446** | **4.246** | **4.729** | **100.0%** |

> [!WARNING]
> **Mất cân bằng dữ liệu nghiêm trọng ở loài Thỏ vằn (Annamite Striped Rabbit):** Loài thỏ vằn chỉ có thêm đúng 13 ảnh mới (tổng 360 ảnh), thấp hơn nhiều so với các loài khác (~520–589 ảnh). Train mở rộng không được gán thêm class weights hay sampler mới trong protocol W6 (để cô lập tác động dữ liệu thuần túy).

### 3.3. Hình học, Crop và Trọng số mẫu (Geometry & Contract)
- Tọa độ bounding box: Integer XYXY, right/bottom exclusive, round-half-even theo TV1, padding 0.
- Bounding box filtering: Các box có cạnh $< 8$ px bị bỏ qua theo đúng contract; mọi box $\ge 8$ px được giữ đầy đủ.
- Trọng số mẫu parent: $\text{sample\_weight} = 1 / N$ với $N = \text{parent\_crop\_count}$, sai số tuyệt đối $\le 10^{-12}$.
- Tập Validation cũ: Giữ nguyên tuyệt đối 600 ảnh / 680 crops / 75 ảnh mỗi lớp.

---

## 4. Bước 3 — Rà soát Leakage & Kiểm tra Quarantine

### 4.1. Kiểm tra Leakage đa chiều
TV2 đã kiểm tra giao cắt độc lập giữa tập Train mở rộng (4.246 ảnh) với các tập bảo vệ:
1. **Metadata Leakage (ID, File Name, Seq ID, Location):**
   - $\text{Train} \cap \text{Val} = \emptyset$ (0 ảnh trùng).
   - $\text{Train} \cap \text{Holdout} = \emptyset$ (0 ảnh trùng).
   - Địa điểm (`location`) giữa Train cũ và Train mới có thể trùng, nhưng chuỗi ảnh (`seq_id`) của Train mới hoàn toàn mới.
2. **Protected Split Fingerprint Leakage (Không mở raster Test W4):**
   - Đối chiếu với 5.774 bản ghi fingerprint trong `features.jsonl` (chỉ sử dụng Git metadata và hash công bố):
   - $\text{Train} \cap \text{Protected Splits (Val/Test/Holdout)} = \emptyset$ trên các trường `image_id`, `seq_id`, `location`.
3. **Exact Content Leakage (SHA-256 byte và RGB pixel SHA-256):**
   - 1.446 ảnh mới có mã SHA-256 byte và pixel SHA-256 hoàn toàn độc nhất, không trùng lặp nội bộ và không trùng lặp với bất kỳ ảnh nào trong các tập bảo vệ.
4. **Bảo toàn Test W4:**
   - Git blobs của `val.jsonl`, `b1/val.jsonl`, `b2/val.jsonl`, `test.jsonl`, `b1/test.jsonl`, `b2/test.jsonl` trong `comparison_v1` khớp 100% với commit gốc `cfcf006`.
   - **0 ảnh Test raster bị mở, giải mã hay suy luận.**

### 4.2. Kiểm tra phân loại 219 ảnh cách ly (Quarantine Breakdown)
Toàn bộ 219 ảnh cách ly trong `excluded.jsonl` được phân chia rõ ràng theo 3 nhóm lý do:
1. **5 ảnh trùng lặp tuyệt đối (Exact RGB Duplicates):**
   - Lý do chính: `exact_duplicate_pixel_sha256`.
   - 5 Image ID: `da027a9f...`, `da027b62...`, `d86f9058...`, `d9c6e567...`, `d9c6e571...`.
   - Các ảnh này trùng lặp với ảnh cũ hoặc trùng lặp lẫn nhau và đã được loại bỏ hoàn toàn khỏi Train.
2. **191 ảnh nghi ngờ trùng lặp gần (Suspected Near-Duplicates):**
   - Lý do chính: `near_duplicate_pending_review`.
   - Phát hiện qua 347 cặp pHash/dHash ($\text{pHash distance} \le 4$, $\text{dHash distance} \le 8$).
   - Có 193 ID mới bị gắn cờ; trong đó 2 ID đã thuộc nhóm Exact Duplicates $\implies$ còn đúng 191 ID có lý do chính là near-duplicate.
   - *Lưu ý quy tắc TV2:* Không coi suspected near-duplicate là duplicate đã xác nhận (nền camera tĩnh có thể gây dương tính giả), nhưng việc cách ly chúng khỏi Train là hành động an toàn và hợp lệ.
3. **23 ảnh mơ hồ về mặt thị giác (Visual Ambiguity):**
   - Lý do chính: `visual_ambiguity_pending_expert`.
   - Được phát hiện qua mẫu rà soát trực quan 80 ảnh (xem chi tiết ở Bước 4).

### 4.3. Hồ sơ 109 Holdout Candidates
- File `holdout_quality.jsonl` ghi nhận đủ 109 ảnh holdout với đầy đủ kích thước, định dạng, file SHA-256 và pixel SHA-256.
- 109 ảnh này chỉ phục vụ đối soát trùng lặp và chất lượng; không có ảnh nào bị rò rỉ vào tập Train; không dùng để inference hay chọn mô hình.

---

## 5. Bước 4 — Kiểm tra trực quan mẫu (Visual Sample Review)

TV2 đã đối soát danh sách mẫu trực quan cố định tại `visual_queue.jsonl` và `visual_review.json` (chọn theo random seed 42, đúng 10 ảnh mỗi lớp $\times$ 8 lớp = 80 ảnh):

### 5.1. 57 ảnh được giữ lại (Retained Visual Samples)
- **Thực tế kiểm tra:** Cả 57 file ảnh đều có mặt trong `swg_train_expansion_w6_v1_additional/data/images/`.
- TV2 đã tải thực tế từng file ảnh, kiểm tra kích thước gốc, thực hiện cắt crop theo đúng tọa độ bounding box:
  - Tất cả các box đều nằm trọn trong ranh giới ảnh ($0 \le x_1 < x_2 \le W$, $0 \le y_1 < y_2 \le H$).
  - Kích thước crop đều $\ge 8 \times 8$ px.
  - Hình ảnh động vật, góc chụp, ánh sáng IR/ban ngày và bối cảnh phù hợp với nhãn metadata nguồn.
  - Xác nhận: **57/57 ảnh được giữ PASS kiểm tra hình học và raster thực tế**.

### 5.2. 23 ảnh bị gắn cờ cách ly (Quarantined Samples)
- 23 ảnh mang các chỉ số review: `[4, 9, 10, 15, 25, 30, 31, 34, 35, 38, 40, 42, 45, 48, 54, 56, 58, 60, 66, 68, 75, 76, 80]`.
- Nhật ký TV1 ghi nhận các lý do: vật thể bị che khuất gần hết bởi cành lá, thiếu phần đầu/chân, ảnh quá tối (underexposed), quá mờ, lóa sương trắng (overexposed), hoặc box bị cắt sát mép.
- **Vấn đề tồn đọng:** Toàn bộ 23 file ảnh này **KHÔNG CÓ MẶT** trong gói `swg_train_expansion_w6_v1_additional.zip`, và file `visual_review_contact_sheets.zip` không được bàn giao trong workspace.
- Do đó, TV2 chỉ có thể đối soát qua nhật ký mô tả và metadata của TV1, **chưa thể trực tiếp nhìn thấy các pixel ảnh thật của 23 ảnh cách ly này**.
- Theo quy định giao thức W6: *"Nếu thiếu ảnh hoặc không thể thực sự xem bằng chứng thị giác, ghi PENDING. Không tự sửa nhãn từ dự đoán mô hình."*

---

## 6. Bước 5 — Kết luận & Khuyến nghị giao thức

### 6.1. Bảng tổng hợp hiện trạng kiểm định

| Hạng mục kiểm tra | Phạm vi thực hiện | Kết quả thực tế | Trạng thái cổng |
| :--- | :--- | :---: | :---: |
| **Release Provenance & SHA-256** | 19 snapshot files | Khớp tuyệt đối `a6ac693306...dda5` | **PASS** |
| **Partition 1.665 ứng viên** | 1.446 giữ + 219 cách ly | Khớp 100% | **PASS** |
| **Train mở rộng (4.246 ảnh / 4.729 crops)** | 8 lớp, class map W5/W6 | Đúng contract W6 | **PASS** |
| **Bảo toàn Validation (600 ảnh / 680 crops)** | Git blob comparison_v1 | Nguyên vẹn so với W5 | **PASS** |
| **Bảo toàn Test W4 (600 ảnh)** | Git blob comparison_v1 | Không mở raster, blob khớp 100% | **PASS** |
| **Leakage Metadata & Fingerprints** | Train vs Val/Test/Holdout | Giao cắt bằng rỗng (0 rò rỉ) | **PASS** |
| **Quarantine 219 ảnh (5 exact, 191 near, 23 visual)** | Toàn bộ bị loại khỏi Train | Hợp lệ theo metadata | **PASS** |
| **Decode 1.446 ảnh Train mới** | Fresh Pillow decode | 1.446/1.446 ảnh hợp lệ, pixel SHA khớp | **PASS** |
| **Kiểm tra trực quan 57 ảnh giữ** | Bbox crop & resolution | 57/57 ảnh hợp lệ trên đĩa | **PASS** |
| **Kiểm tra trực quan 23 ảnh cách ly** | Thiếu file raster/contact sheets | Không thể xem pixel trực tiếp | **PENDING** |
| **Tổng thể Data Expansion Review** | TV2 Independent Gate | **PENDING REVIEW** | **PENDING** |

### 6.2. Quyết định của TV2 (TV2 Technical Recommendation)
1. **Khuyến nghị:** **BLOCKED / PENDING**.
2. **Không cấp `READY_FOR_TV2_APPROVAL`:** TV2 không thể ký duyệt chấp thuận kỹ thuật (Approval) cho release này chừng nào TV1 chưa bàn giao gói contact sheets hoặc file ảnh của các mẫu cách ly để TV2 rà soát trực quan độc lập.
3. **Trạng thái R5 và R6:** Tiếp tục giữ ở trạng thái **CONDITIONAL / BLOCKED** trong registry. TV3 tuyệt đối không được phép khởi chạy training trên tập `train_expansion_w6_v1`.
4. **Bảo toàn kỷ luật:**
   - Không sửa đổi snapshot TV1 hay gán approval giả mạo.
   - Không tự động đưa các ảnh nghi trùng trở lại tập Train.
   - Không mở hay giải mã tập Test Official W4.
   - Giữ nguyên toàn bộ cấu hình frozen R0–R4 và các mốc W1–W5.

---

## 7. Hồ sơ bằng chứng máy đọc được (Evidence Directory)

Toàn bộ script và bằng chứng đối soát độc lập của TV2 đã được lưu trữ tại:
[`outputs/tv2_w6/tv1_data_review_20261107/`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/tv1_data_review_20261107/):
- [`review.json`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/tv1_data_review_20261107/review.json): Kết quả chạy độc lập của `scripts/review_tv1_w6.py` đối soát 19 snapshot và giải mã 1.446 ảnh ZIP.
- [`visual_review_audit.json`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/tv1_data_review_20261107/visual_review_audit.json): Chi tiết audit từng mẫu trong 80 mẫu trực quan (57 mẫu xác minh trên đĩa, 23 mẫu thiếu raster).
- [`tv1_expansion_audit_summary.json`](file:///d:/Năm%203/HK1_2026/Học%20máy%20và%20ứng%20dụng/Do_an/outputs/tv2_w6/tv1_data_review_20261107/tv1_expansion_audit_summary.json): Tổng hợp máy đọc được của toàn bộ 5 bước đối soát.
