# Báo cáo Phân tích Lỗi — Mô hình B2

> **Checkpoint:** `C:\Users\Admin\OneDrive\Documents\VLU\Năm 3\HK1nam3\Học máy và ứng dụng\Project ML\outputs\b2_crop_classifier\b2_run01\best_model.pt`
> **Thời gian tạo:** 2026-10-22 11:48:21 UTC
> **Tập đánh giá:** Validation (KHÔNG dùng test set)

## 1. Tổng quan

| Chỉ số | Giá trị |
| :--- | :---: |
| Tổng số ảnh | 600 |
| Số ảnh phân loại sai | 152 |
| Độ chính xác tổng thể (Image-level) | 74.67% |
| Tỷ lệ lỗi tổng thể | 25.33% |

## 2. Top-10 cặp lớp bị nhầm lẫn nhiều nhất

| # | Lớp thật | Dự đoán sai thành | Số lần | Hướng |
| :---: | :--- | :--- | :---: | :--- |
| 1 | large_antlered_muntjac | sambar | 13 | large_antlered_muntjac → sambar |
| 2 | sambar | large_antlered_muntjac | 12 | sambar → large_antlered_muntjac |
| 3 | large_antlered_muntjac | eurasian_wild_pig | 10 | large_antlered_muntjac → eurasian_wild_pig |
| 4 | common_palm_civet | annamite_striped_rabbit | 10 | common_palm_civet → annamite_striped_rabbit |
| 5 | eurasian_wild_pig | large_antlered_muntjac | 9 | eurasian_wild_pig → large_antlered_muntjac |
| 6 | eurasian_wild_pig | masked_palm_civet | 8 | eurasian_wild_pig → masked_palm_civet |
| 7 | chinese_serow | eurasian_wild_pig | 7 | chinese_serow → eurasian_wild_pig |
| 8 | sambar | masked_palm_civet | 6 | sambar → masked_palm_civet |
| 9 | masked_palm_civet | annamite_striped_rabbit | 6 | masked_palm_civet → annamite_striped_rabbit |
| 10 | large_antlered_muntjac | annamite_striped_rabbit | 5 | large_antlered_muntjac → annamite_striped_rabbit |

## 3. Các cặp lớp nhầm lẫn hai chiều (A ↔ B)

| Lớp A | Lớp B | A→B | B→A | Tổng nhầm |
| :--- | :--- | :---: | :---: | :---: |
| large_antlered_muntjac | sambar | 13 | 12 | 25 |
| large_antlered_muntjac | eurasian_wild_pig | 10 | 9 | 19 |
| common_palm_civet | annamite_striped_rabbit | 10 | 0 | 10 |
| eurasian_wild_pig | masked_palm_civet | 8 | 0 | 8 |
| chinese_serow | eurasian_wild_pig | 7 | 0 | 7 |
| sambar | masked_palm_civet | 6 | 0 | 6 |
| masked_palm_civet | annamite_striped_rabbit | 6 | 0 | 6 |
| large_antlered_muntjac | annamite_striped_rabbit | 5 | 0 | 5 |

## 4. Phân tích lỗi theo từng lớp

| Lớp | Tổng ảnh | Số lỗi | Tỷ lệ lỗi | Nhầm nhiều nhất sang |
| :--- | :---: | :---: | :---: | :--- |
| large_antlered_muntjac | 75 | 36 | 48.00% | sambar (13) |
| sambar | 75 | 28 | 37.33% | large_antlered_muntjac (12) |
| eurasian_wild_pig | 75 | 22 | 29.33% | large_antlered_muntjac (9) |
| common_palm_civet | 75 | 18 | 24.00% | annamite_striped_rabbit (10) |
| chinese_serow | 75 | 17 | 22.67% | eurasian_wild_pig (7) |
| masked_palm_civet | 75 | 17 | 22.67% | annamite_striped_rabbit (6) |
| annamite_striped_rabbit | 75 | 7 | 9.33% | common_palm_civet (4) |
| silver_pheasant | 75 | 7 | 9.33% | eurasian_wild_pig (2) |

## 5. Các lớp có hiệu suất kém nhất

1. **large_antlered_muntjac** — Tỷ lệ lỗi: 48.00% (36/75 ảnh sai), hay nhầm với: *sambar*
2. **sambar** — Tỷ lệ lỗi: 37.33% (28/75 ảnh sai), hay nhầm với: *large_antlered_muntjac*
3. **eurasian_wild_pig** — Tỷ lệ lỗi: 29.33% (22/75 ảnh sai), hay nhầm với: *large_antlered_muntjac*
4. **common_palm_civet** — Tỷ lệ lỗi: 24.00% (18/75 ảnh sai), hay nhầm với: *annamite_striped_rabbit*
5. **chinese_serow** — Tỷ lệ lỗi: 22.67% (17/75 ảnh sai), hay nhầm với: *eurasian_wild_pig*

## 6. Confusion Matrix

| True \ Pred | large_antler | annamite_str | sambar | chinese_sero | common_palm_ | masked_palm_ | silver_pheas | eurasian_wil |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| large_antler | **39** | _5_ | _13_ | _1_ | _2_ | _5_ | 0 | _10_ |
| annamite_str | _1_ | **68** | 0 | _1_ | _4_ | _1_ | 0 | 0 |
| sambar | _12_ | _2_ | **47** | _3_ | _1_ | _6_ | _1_ | _3_ |
| chinese_sero | _1_ | _2_ | _5_ | **58** | _1_ | _1_ | 0 | _7_ |
| common_palm_ | _1_ | _10_ | 0 | _4_ | **57** | _3_ | 0 | 0 |
| masked_palm_ | _5_ | _6_ | _1_ | _1_ | _4_ | **58** | 0 | 0 |
| silver_pheas | _1_ | 0 | _1_ | _2_ | 0 | _1_ | **68** | _2_ |
| eurasian_wil | _9_ | 0 | _1_ | _3_ | _1_ | _8_ | 0 | **53** |

> **Ghi chú:** Số in đậm = phân loại đúng (diagonal). Số in nghiêng = phân loại sai.

## 7. Ảnh bị phân loại sai (sắp xếp theo confidence tăng dần)

Tổng: **152** ảnh bị phân loại sai.

Hiển thị top 30 ảnh uncertain nhất:

| # | Image ID | Nhãn thật | Dự đoán | Confidence |
| :---: | :--- | :--- | :--- | :---: |
| 1 | `d4bf5949-8c29-11eb-aa3e-000d3a74c7de` | eurasian_wild_pig | large_antlered_muntjac | 22.6% |
| 2 | `d3019260-8c29-11eb-b090-000d3a74c7de` | eurasian_wild_pig | large_antlered_muntjac | 26.0% |
| 3 | `d9dc68c1-8c29-11eb-8e12-000d3a74c7de` | silver_pheasant | masked_palm_civet | 27.5% |
| 4 | `cc07cffd-8c29-11eb-ba6d-000d3a74c7de` | large_antlered_muntjac | eurasian_wild_pig | 27.7% |
| 5 | `d5c35481-8c29-11eb-9c0f-000d3a74c7de` | common_palm_civet | annamite_striped_rabbit | 28.6% |
| 6 | `d2f5a73b-8c29-11eb-a260-000d3a74c7de` | eurasian_wild_pig | sambar | 28.8% |
| 7 | `d0ad88d8-8c29-11eb-bfce-000d3a74c7de` | large_antlered_muntjac | chinese_serow | 28.8% |
| 8 | `d5b2a18d-8c29-11eb-8dce-000d3a74c7de` | chinese_serow | large_antlered_muntjac | 28.8% |
| 9 | `c8233778-8c29-11eb-91cb-000d3a74c7de` | large_antlered_muntjac | eurasian_wild_pig | 30.0% |
| 10 | `c87143ea-8c29-11eb-88d1-000d3a74c7de` | chinese_serow | eurasian_wild_pig | 30.2% |
| 11 | `d2f5a3ff-8c29-11eb-b3e5-000d3a74c7de` | masked_palm_civet | annamite_striped_rabbit | 30.5% |
| 12 | `d1f8ef38-8c29-11eb-a8b5-000d3a74c7de` | sambar | masked_palm_civet | 30.7% |
| 13 | `c87143e9-8c29-11eb-98ff-000d3a74c7de` | chinese_serow | annamite_striped_rabbit | 31.0% |
| 14 | `c8a191da-8c29-11eb-80b4-000d3a74c7de` | sambar | annamite_striped_rabbit | 32.5% |
| 15 | `d0e922ab-8c29-11eb-a5e7-000d3a74c7de` | large_antlered_muntjac | eurasian_wild_pig | 32.5% |
| 16 | `d3019234-8c29-11eb-ac6a-000d3a74c7de` | eurasian_wild_pig | masked_palm_civet | 32.7% |
| 17 | `c96adc33-8c29-11eb-8bb5-000d3a74c7de` | common_palm_civet | masked_palm_civet | 33.7% |
| 18 | `d83d8012-8c29-11eb-a0a5-000d3a74c7de` | common_palm_civet | chinese_serow | 34.5% |
| 19 | `cdb29149-8c29-11eb-bb49-000d3a74c7de` | silver_pheasant | large_antlered_muntjac | 34.7% |
| 20 | `cff13df1-8c29-11eb-b1d8-000d3a74c7de` | sambar | large_antlered_muntjac | 35.6% |
| 21 | `cf301233-8c29-11eb-ba3f-000d3a74c7de` | annamite_striped_rabbit | large_antlered_muntjac | 36.2% |
| 22 | `d1f8ef1c-8c29-11eb-9472-000d3a74c7de` | sambar | annamite_striped_rabbit | 36.6% |
| 23 | `c911a9f5-8c29-11eb-b2a4-000d3a74c7de` | masked_palm_civet | annamite_striped_rabbit | 37.9% |
| 24 | `c97a9807-8c29-11eb-8a05-000d3a74c7de` | eurasian_wild_pig | chinese_serow | 38.1% |
| 25 | `cc246b06-8c29-11eb-9781-000d3a74c7de` | large_antlered_muntjac | masked_palm_civet | 38.2% |
| 26 | `d82344ee-8c29-11eb-9b29-000d3a74c7de` | common_palm_civet | large_antlered_muntjac | 38.9% |
| 27 | `d210c1e5-8c29-11eb-97c4-000d3a74c7de` | large_antlered_muntjac | eurasian_wild_pig | 39.0% |
| 28 | `dc5428e3-8c29-11eb-b92d-000d3a74c7de` | chinese_serow | eurasian_wild_pig | 39.0% |
| 29 | `d095acc5-8c29-11eb-9b5d-000d3a74c7de` | eurasian_wild_pig | masked_palm_civet | 39.1% |
| 30 | `cc07cf29-8c29-11eb-bcb5-000d3a74c7de` | large_antlered_muntjac | annamite_striped_rabbit | 39.2% |

---
*Báo cáo được tạo tự động bởi `scripts/error_analysis.py` — TV3*