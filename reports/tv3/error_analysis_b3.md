# Báo cáo Phân tích Lỗi — Mô hình B3

> **Checkpoint:** `C:\Users\Admin\OneDrive\Documents\VLU\Năm 3\HK1nam3\Học máy và ứng dụng\Project ML\outputs\b3_class_weighted\b3_run01\best_model.pt`
> **Thời gian tạo:** 2026-10-22 12:25:02 UTC
> **Tập đánh giá:** Validation (KHÔNG dùng test set)

## 1. Tổng quan

| Chỉ số | Giá trị |
| :--- | :---: |
| Tổng số ảnh | 600 |
| Số ảnh phân loại sai | 154 |
| Độ chính xác tổng thể (Image-level) | 74.33% |
| Tỷ lệ lỗi tổng thể | 25.67% |

## 2. Top-10 cặp lớp bị nhầm lẫn nhiều nhất

| # | Lớp thật | Dự đoán sai thành | Số lần | Hướng |
| :---: | :--- | :--- | :---: | :--- |
| 1 | large_antlered_muntjac | sambar | 13 | large_antlered_muntjac → sambar |
| 2 | large_antlered_muntjac | eurasian_wild_pig | 11 | large_antlered_muntjac → eurasian_wild_pig |
| 3 | eurasian_wild_pig | large_antlered_muntjac | 10 | eurasian_wild_pig → large_antlered_muntjac |
| 4 | sambar | large_antlered_muntjac | 9 | sambar → large_antlered_muntjac |
| 5 | masked_palm_civet | common_palm_civet | 8 | masked_palm_civet → common_palm_civet |
| 6 | chinese_serow | sambar | 7 | chinese_serow → sambar |
| 7 | eurasian_wild_pig | masked_palm_civet | 7 | eurasian_wild_pig → masked_palm_civet |
| 8 | sambar | eurasian_wild_pig | 6 | sambar → eurasian_wild_pig |
| 9 | large_antlered_muntjac | annamite_striped_rabbit | 5 | large_antlered_muntjac → annamite_striped_rabbit |
| 10 | sambar | masked_palm_civet | 5 | sambar → masked_palm_civet |

## 3. Các cặp lớp nhầm lẫn hai chiều (A ↔ B)

| Lớp A | Lớp B | A→B | B→A | Tổng nhầm |
| :--- | :--- | :---: | :---: | :---: |
| large_antlered_muntjac | sambar | 13 | 9 | 22 |
| large_antlered_muntjac | eurasian_wild_pig | 11 | 10 | 21 |
| masked_palm_civet | common_palm_civet | 8 | 0 | 8 |
| chinese_serow | sambar | 7 | 0 | 7 |
| eurasian_wild_pig | masked_palm_civet | 7 | 0 | 7 |
| sambar | eurasian_wild_pig | 6 | 0 | 6 |
| large_antlered_muntjac | annamite_striped_rabbit | 5 | 0 | 5 |
| sambar | masked_palm_civet | 5 | 0 | 5 |

## 4. Phân tích lỗi theo từng lớp

| Lớp | Tổng ảnh | Số lỗi | Tỷ lệ lỗi | Nhầm nhiều nhất sang |
| :--- | :---: | :---: | :---: | :--- |
| large_antlered_muntjac | 75 | 34 | 45.33% | sambar (13) |
| eurasian_wild_pig | 75 | 29 | 38.67% | large_antlered_muntjac (10) |
| sambar | 75 | 28 | 37.33% | large_antlered_muntjac (9) |
| masked_palm_civet | 75 | 19 | 25.33% | common_palm_civet (8) |
| chinese_serow | 75 | 17 | 22.67% | sambar (7) |
| common_palm_civet | 75 | 16 | 21.33% | chinese_serow (5) |
| silver_pheasant | 75 | 6 | 8.00% | large_antlered_muntjac (2) |
| annamite_striped_rabbit | 75 | 5 | 6.67% | common_palm_civet (2) |

## 5. Các lớp có hiệu suất kém nhất

1. **large_antlered_muntjac** — Tỷ lệ lỗi: 45.33% (34/75 ảnh sai), hay nhầm với: *sambar*
2. **eurasian_wild_pig** — Tỷ lệ lỗi: 38.67% (29/75 ảnh sai), hay nhầm với: *large_antlered_muntjac*
3. **sambar** — Tỷ lệ lỗi: 37.33% (28/75 ảnh sai), hay nhầm với: *large_antlered_muntjac*
4. **masked_palm_civet** — Tỷ lệ lỗi: 25.33% (19/75 ảnh sai), hay nhầm với: *common_palm_civet*
5. **chinese_serow** — Tỷ lệ lỗi: 22.67% (17/75 ảnh sai), hay nhầm với: *sambar*

## 6. Confusion Matrix

| True \ Pred | large_antler | annamite_str | sambar | chinese_sero | common_palm_ | masked_palm_ | silver_pheas | eurasian_wil |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| large_antler | **41** | _5_ | _13_ | 0 | _2_ | _2_ | _1_ | _11_ |
| annamite_str | 0 | **70** | 0 | _1_ | _2_ | _2_ | 0 | 0 |
| sambar | _9_ | _2_ | **47** | _4_ | _1_ | _5_ | _1_ | _6_ |
| chinese_sero | 0 | _1_ | _7_ | **58** | _2_ | _2_ | 0 | _5_ |
| common_palm_ | _1_ | _4_ | _3_ | _5_ | **59** | _3_ | 0 | 0 |
| masked_palm_ | _4_ | _4_ | _2_ | _1_ | _8_ | **56** | 0 | 0 |
| silver_pheas | _2_ | 0 | 0 | _2_ | 0 | 0 | **69** | _2_ |
| eurasian_wil | _10_ | 0 | _3_ | _4_ | _4_ | _7_ | _1_ | **46** |

> **Ghi chú:** Số in đậm = phân loại đúng (diagonal). Số in nghiêng = phân loại sai.

## 7. Ảnh bị phân loại sai (sắp xếp theo confidence tăng dần)

Tổng: **154** ảnh bị phân loại sai.

Hiển thị top 30 ảnh uncertain nhất:

| # | Image ID | Nhãn thật | Dự đoán | Confidence |
| :---: | :--- | :--- | :--- | :---: |
| 1 | `c8a191da-8c29-11eb-80b4-000d3a74c7de` | sambar | chinese_serow | 20.1% |
| 2 | `cf09b702-8c29-11eb-a276-000d3a74c7de` | common_palm_civet | sambar | 22.4% |
| 3 | `dc483d23-8c29-11eb-9dc7-000d3a74c7de` | chinese_serow | sambar | 22.9% |
| 4 | `d1167081-8c29-11eb-8085-000d3a74c7de` | sambar | large_antlered_muntjac | 23.2% |
| 5 | `d0ad8884-8c29-11eb-b9a9-000d3a74c7de` | large_antlered_muntjac | common_palm_civet | 23.5% |
| 6 | `cd38fbf6-8c29-11eb-809c-000d3a74c7de` | common_palm_civet | sambar | 23.8% |
| 7 | `d0ad88d8-8c29-11eb-bfce-000d3a74c7de` | large_antlered_muntjac | masked_palm_civet | 24.6% |
| 8 | `cd0e1864-8c29-11eb-b11b-000d3a74c7de` | annamite_striped_rabbit | chinese_serow | 29.5% |
| 9 | `d22d5fac-8c29-11eb-a106-000d3a74c7de` | silver_pheasant | eurasian_wild_pig | 29.8% |
| 10 | `d4bf5949-8c29-11eb-aa3e-000d3a74c7de` | eurasian_wild_pig | large_antlered_muntjac | 30.2% |
| 11 | `d1166c73-8c29-11eb-ac4c-000d3a74c7de` | sambar | silver_pheasant | 31.0% |
| 12 | `d5c35481-8c29-11eb-9c0f-000d3a74c7de` | common_palm_civet | chinese_serow | 31.3% |
| 13 | `d83d8012-8c29-11eb-a0a5-000d3a74c7de` | common_palm_civet | chinese_serow | 32.0% |
| 14 | `d3019260-8c29-11eb-b090-000d3a74c7de` | eurasian_wild_pig | large_antlered_muntjac | 32.0% |
| 15 | `c819ae51-8c29-11eb-bc7d-000d3a74c7de` | eurasian_wild_pig | silver_pheasant | 32.7% |
| 16 | `d5b2a18d-8c29-11eb-8dce-000d3a74c7de` | chinese_serow | sambar | 32.7% |
| 17 | `d1f8ef1c-8c29-11eb-9472-000d3a74c7de` | sambar | annamite_striped_rabbit | 33.0% |
| 18 | `cae9b987-8c29-11eb-9522-000d3a74c7de` | common_palm_civet | masked_palm_civet | 33.3% |
| 19 | `c8233778-8c29-11eb-91cb-000d3a74c7de` | large_antlered_muntjac | eurasian_wild_pig | 33.4% |
| 20 | `cc246b06-8c29-11eb-9781-000d3a74c7de` | large_antlered_muntjac | eurasian_wild_pig | 35.3% |
| 21 | `d9dc68c1-8c29-11eb-8e12-000d3a74c7de` | silver_pheasant | large_antlered_muntjac | 35.6% |
| 22 | `c87143e9-8c29-11eb-98ff-000d3a74c7de` | chinese_serow | masked_palm_civet | 36.7% |
| 23 | `c87143ea-8c29-11eb-88d1-000d3a74c7de` | chinese_serow | eurasian_wild_pig | 36.9% |
| 24 | `d0be3733-8c29-11eb-b4ad-000d3a74c7de` | sambar | eurasian_wild_pig | 37.3% |
| 25 | `d2f5a73b-8c29-11eb-a260-000d3a74c7de` | eurasian_wild_pig | masked_palm_civet | 37.6% |
| 26 | `d0e6bb26-8c29-11eb-a906-000d3a74c7de` | common_palm_civet | chinese_serow | 38.8% |
| 27 | `c82a64d7-8c29-11eb-a98d-000d3a74c7de` | large_antlered_muntjac | sambar | 39.1% |
| 28 | `cc0a314e-8c29-11eb-9392-000d3a74c7de` | large_antlered_muntjac | annamite_striped_rabbit | 39.6% |
| 29 | `cc293eb4-8c29-11eb-81b9-000d3a74c7de` | sambar | eurasian_wild_pig | 39.6% |
| 30 | `cf09b707-8c29-11eb-8bff-000d3a74c7de` | common_palm_civet | sambar | 40.6% |

---
*Báo cáo được tạo tự động bởi `scripts/error_analysis.py` — TV3*