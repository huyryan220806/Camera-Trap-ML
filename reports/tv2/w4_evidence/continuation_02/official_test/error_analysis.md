# Official B2 Test errors

All predictions retained. No model/threshold changes permitted.

| Class | Precision | Recall | Errors / support |
|---|---:|---:|---:|
| large_antlered_muntjac | 0.630769 | 0.546667 | 34 / 75 |
| annamite_striped_rabbit | 0.770833 | 0.986667 | 1 / 75 |
| sambar | 0.642857 | 0.600000 | 30 / 75 |
| chinese_serow | 0.733333 | 0.733333 | 20 / 75 |
| common_palm_civet | 0.762712 | 0.600000 | 30 / 75 |
| masked_palm_civet | 0.600000 | 0.680000 | 24 / 75 |
| silver_pheasant | 0.929577 | 0.880000 | 9 / 75 |
| eurasian_wild_pig | 0.772152 | 0.813333 | 14 / 75 |

## Directed confusion pairs

- common_palm_civet → masked_palm_civet: 18
- large_antlered_muntjac → sambar: 12
- sambar → large_antlered_muntjac: 11
- chinese_serow → sambar: 8
- common_palm_civet → annamite_striped_rabbit: 7
- sambar → chinese_serow: 7
- large_antlered_muntjac → masked_palm_civet: 7
- masked_palm_civet → common_palm_civet: 6
- masked_palm_civet → annamite_striped_rabbit: 6
- chinese_serow → eurasian_wild_pig: 6
- eurasian_wild_pig → large_antlered_muntjac: 5
- sambar → eurasian_wild_pig: 5
- sambar → masked_palm_civet: 5
- large_antlered_muntjac → eurasian_wild_pig: 5
- large_antlered_muntjac → annamite_striped_rabbit: 5
- silver_pheasant → common_palm_civet: 4
- masked_palm_civet → sambar: 4
- eurasian_wild_pig → chinese_serow: 3
- masked_palm_civet → large_antlered_muntjac: 3
- common_palm_civet → chinese_serow: 3
- large_antlered_muntjac → chinese_serow: 3
- eurasian_wild_pig → annamite_striped_rabbit: 2
- silver_pheasant → chinese_serow: 2
- silver_pheasant → large_antlered_muntjac: 2
- masked_palm_civet → silver_pheasant: 2
- masked_palm_civet → chinese_serow: 2
- common_palm_civet → large_antlered_muntjac: 2
- chinese_serow → masked_palm_civet: 2
- chinese_serow → annamite_striped_rabbit: 2
- eurasian_wild_pig → silver_pheasant: 1
- eurasian_wild_pig → masked_palm_civet: 1
- eurasian_wild_pig → common_palm_civet: 1
- eurasian_wild_pig → sambar: 1
- silver_pheasant → eurasian_wild_pig: 1
- masked_palm_civet → eurasian_wild_pig: 1
- chinese_serow → common_palm_civet: 1
- chinese_serow → large_antlered_muntjac: 1
- sambar → silver_pheasant: 1
- sambar → common_palm_civet: 1
- annamite_striped_rabbit → masked_palm_civet: 1
- large_antlered_muntjac → silver_pheasant: 1
- large_antlered_muntjac → common_palm_civet: 1

## Manifest geometry subgroups

Flags use frozen integer pixel crop boxes; groups may overlap. No samples excluded.

| Subgroup | Images | Errors | Error rate |
|---|---:|---:|---:|
| multiple_crops | 57 | 9 | 0.15789474 |
| box_area_below_1_percent | 70 | 18 | 0.25714286 |
| box_within_1_pixel_of_edge | 171 | 56 | 0.32748538 |

## Verifiable error examples

- c7f5e6b1-8c29-11eb-820b-000d3a74c7de: true=common_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.59277850, crops=1; source=frozen manifest; raster not visually adjudicated.
- c7f5e6b8-8c29-11eb-9993-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.92323661, crops=1; source=frozen manifest; raster not visually adjudicated.
- c7f5e709-8c29-11eb-8efc-000d3a74c7de: true=large_antlered_muntjac, predicted=eurasian_wild_pig, softmax_score=0.31653610, crops=1; source=frozen manifest; raster not visually adjudicated.
- c85a0bac-8c29-11eb-97a5-000d3a74c7de: true=large_antlered_muntjac, predicted=chinese_serow, softmax_score=0.86575532, crops=1; source=frozen manifest; raster not visually adjudicated.
- c85f6991-8c29-11eb-b907-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.65016848, crops=1; source=frozen manifest; raster not visually adjudicated.
- c87dd580-8c29-11eb-93d7-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.43485993, crops=1; source=frozen manifest; raster not visually adjudicated.
- c8927386-8c29-11eb-916f-000d3a74c7de: true=common_palm_civet, predicted=large_antlered_muntjac, softmax_score=0.29948688, crops=1; source=frozen manifest; raster not visually adjudicated.
- c8a3f43c-8c29-11eb-b8df-000d3a74c7de: true=chinese_serow, predicted=eurasian_wild_pig, softmax_score=0.31676853, crops=1; source=frozen manifest; raster not visually adjudicated.
- c8a3f440-8c29-11eb-a2f7-000d3a74c7de: true=chinese_serow, predicted=eurasian_wild_pig, softmax_score=0.94601542, crops=1; source=frozen manifest; raster not visually adjudicated.
- c8a3f44c-8c29-11eb-9328-000d3a74c7de: true=chinese_serow, predicted=eurasian_wild_pig, softmax_score=0.83061230, crops=1; source=frozen manifest; raster not visually adjudicated.
- c8a3f4e5-8c29-11eb-a18c-000d3a74c7de: true=sambar, predicted=eurasian_wild_pig, softmax_score=0.51019928, crops=3; source=frozen manifest; raster not visually adjudicated.
- c9166e15-8c29-11eb-b585-000d3a74c7de: true=common_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.34499535, crops=1; source=frozen manifest; raster not visually adjudicated.
- c9167072-8c29-11eb-b276-000d3a74c7de: true=eurasian_wild_pig, predicted=masked_palm_civet, softmax_score=0.42841369, crops=1; source=frozen manifest; raster not visually adjudicated.
- c93563ab-8c29-11eb-a9c7-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.76532298, crops=1; source=frozen manifest; raster not visually adjudicated.
- c9356453-8c29-11eb-90ae-000d3a74c7de: true=common_palm_civet, predicted=chinese_serow, softmax_score=0.26278406, crops=1; source=frozen manifest; raster not visually adjudicated.
- c981b6fd-8c29-11eb-ad9c-000d3a74c7de: true=eurasian_wild_pig, predicted=chinese_serow, softmax_score=0.70213908, crops=1; source=frozen manifest; raster not visually adjudicated.
- c98674b7-8c29-11eb-ab77-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.34540704, crops=1; source=frozen manifest; raster not visually adjudicated.
- c98675f8-8c29-11eb-9837-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.93231225, crops=1; source=frozen manifest; raster not visually adjudicated.
- c98676db-8c29-11eb-aeea-000d3a74c7de: true=masked_palm_civet, predicted=silver_pheasant, softmax_score=0.49839151, crops=1; source=frozen manifest; raster not visually adjudicated.
- c98676dc-8c29-11eb-ba63-000d3a74c7de: true=masked_palm_civet, predicted=eurasian_wild_pig, softmax_score=0.38977173, crops=1; source=frozen manifest; raster not visually adjudicated.
- c98676dd-8c29-11eb-ba72-000d3a74c7de: true=masked_palm_civet, predicted=sambar, softmax_score=0.60609788, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca2fbfa4-8c29-11eb-8664-000d3a74c7de: true=common_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.85743111, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca321b14-8c29-11eb-b20c-000d3a74c7de: true=masked_palm_civet, predicted=common_palm_civet, softmax_score=0.87944645, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca3480d7-8c29-11eb-bfd1-000d3a74c7de: true=common_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.57122654, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca42d18c-8c29-11eb-996d-000d3a74c7de: true=masked_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.32965574, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca42d190-8c29-11eb-abc2-000d3a74c7de: true=masked_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.43591455, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca42d191-8c29-11eb-bd28-000d3a74c7de: true=masked_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.23558460, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca727d28-8c29-11eb-b32a-000d3a74c7de: true=masked_palm_civet, predicted=sambar, softmax_score=0.36884907, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca727d2a-8c29-11eb-b9f6-000d3a74c7de: true=masked_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.22057478, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca727e23-8c29-11eb-9327-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.59818935, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca727e24-8c29-11eb-9405-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.84132773, crops=1; source=frozen manifest; raster not visually adjudicated.
- ca74de0c-8c29-11eb-8a63-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.50146174, crops=1; source=frozen manifest; raster not visually adjudicated.
- cad442b2-8c29-11eb-8266-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.51189840, crops=1; source=frozen manifest; raster not visually adjudicated.
- cad442b3-8c29-11eb-89a9-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.64787042, crops=1; source=frozen manifest; raster not visually adjudicated.
- cad443c8-8c29-11eb-8a53-000d3a74c7de: true=sambar, predicted=silver_pheasant, softmax_score=0.37469381, crops=1; source=frozen manifest; raster not visually adjudicated.
- cb196c86-8c29-11eb-9672-000d3a74c7de: true=common_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.58064580, crops=1; source=frozen manifest; raster not visually adjudicated.
- cbd827ce-8c29-11eb-8fee-000d3a74c7de: true=common_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.74144036, crops=1; source=frozen manifest; raster not visually adjudicated.
- cbd82817-8c29-11eb-bbb6-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.78003573, crops=1; source=frozen manifest; raster not visually adjudicated.
- cbda8894-8c29-11eb-bb7f-000d3a74c7de: true=eurasian_wild_pig, predicted=common_palm_civet, softmax_score=0.69915771, crops=1; source=frozen manifest; raster not visually adjudicated.
- cc6730ec-8c29-11eb-b628-000d3a74c7de: true=masked_palm_civet, predicted=sambar, softmax_score=0.51335460, crops=1; source=frozen manifest; raster not visually adjudicated.
- cc6730ee-8c29-11eb-91ef-000d3a74c7de: true=masked_palm_civet, predicted=silver_pheasant, softmax_score=0.97394967, crops=1; source=frozen manifest; raster not visually adjudicated.
- cc698a15-8c29-11eb-af4c-000d3a74c7de: true=masked_palm_civet, predicted=large_antlered_muntjac, softmax_score=0.77323413, crops=1; source=frozen manifest; raster not visually adjudicated.
- ccbf6fb0-8c29-11eb-a0d8-000d3a74c7de: true=large_antlered_muntjac, predicted=chinese_serow, softmax_score=0.80455607, crops=1; source=frozen manifest; raster not visually adjudicated.
- cccb57a5-8c29-11eb-a4d2-000d3a74c7de: true=masked_palm_civet, predicted=large_antlered_muntjac, softmax_score=0.35982502, crops=1; source=frozen manifest; raster not visually adjudicated.
- ccd9a19c-8c29-11eb-b991-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.33116263, crops=1; source=frozen manifest; raster not visually adjudicated.
- cd6fcdac-8c29-11eb-88f7-000d3a74c7de: true=sambar, predicted=chinese_serow, softmax_score=0.89217687, crops=1; source=frozen manifest; raster not visually adjudicated.
- cd6fcdca-8c29-11eb-92b8-000d3a74c7de: true=sambar, predicted=chinese_serow, softmax_score=0.60139608, crops=1; source=frozen manifest; raster not visually adjudicated.
- cd795c25-8c29-11eb-9d41-000d3a74c7de: true=large_antlered_muntjac, predicted=masked_palm_civet, softmax_score=0.94230318, crops=1; source=frozen manifest; raster not visually adjudicated.
- cda90d32-8c29-11eb-b969-000d3a74c7de: true=common_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.76191652, crops=1; source=frozen manifest; raster not visually adjudicated.
- cdab6bed-8c29-11eb-b533-000d3a74c7de: true=large_antlered_muntjac, predicted=masked_palm_civet, softmax_score=0.39491758, crops=1; source=frozen manifest; raster not visually adjudicated.
- cdadccc5-8c29-11eb-99ea-000d3a74c7de: true=large_antlered_muntjac, predicted=eurasian_wild_pig, softmax_score=0.41974071, crops=3; source=frozen manifest; raster not visually adjudicated.
- cdb02e48-8c29-11eb-b9b6-000d3a74c7de: true=silver_pheasant, predicted=large_antlered_muntjac, softmax_score=0.64199466, crops=1; source=frozen manifest; raster not visually adjudicated.
- cdb03133-8c29-11eb-b63f-000d3a74c7de: true=masked_palm_civet, predicted=common_palm_civet, softmax_score=0.46539003, crops=1; source=frozen manifest; raster not visually adjudicated.
- cdb03217-8c29-11eb-8c97-000d3a74c7de: true=silver_pheasant, predicted=chinese_serow, softmax_score=0.38860697, crops=1; source=frozen manifest; raster not visually adjudicated.
- ce440a48-8c29-11eb-8e10-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.58945823, crops=1; source=frozen manifest; raster not visually adjudicated.
- ce440ab4-8c29-11eb-90cb-000d3a74c7de: true=large_antlered_muntjac, predicted=masked_palm_civet, softmax_score=0.36357492, crops=1; source=frozen manifest; raster not visually adjudicated.
- ce6c8c86-8c29-11eb-a05c-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.48966843, crops=1; source=frozen manifest; raster not visually adjudicated.
- ce73b586-8c29-11eb-bd3f-000d3a74c7de: true=large_antlered_muntjac, predicted=common_palm_civet, softmax_score=0.39966702, crops=1; source=frozen manifest; raster not visually adjudicated.
- ceaced92-8c29-11eb-b720-000d3a74c7de: true=large_antlered_muntjac, predicted=annamite_striped_rabbit, softmax_score=0.54759574, crops=1; source=frozen manifest; raster not visually adjudicated.
- ceaf4fb5-8c29-11eb-9553-000d3a74c7de: true=sambar, predicted=eurasian_wild_pig, softmax_score=0.42531323, crops=1; source=frozen manifest; raster not visually adjudicated.
- ceb1af92-8c29-11eb-a389-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.51555165, crops=2; source=frozen manifest; raster not visually adjudicated.
- ceb1b17d-8c29-11eb-86be-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.96148127, crops=1; source=frozen manifest; raster not visually adjudicated.
- cec26038-8c29-11eb-b93e-000d3a74c7de: true=large_antlered_muntjac, predicted=annamite_striped_rabbit, softmax_score=0.99496680, crops=1; source=frozen manifest; raster not visually adjudicated.
- ced57dc7-8c29-11eb-94d9-000d3a74c7de: true=masked_palm_civet, predicted=common_palm_civet, softmax_score=0.27755919, crops=1; source=frozen manifest; raster not visually adjudicated.
- ced57de0-8c29-11eb-a485-000d3a74c7de: true=masked_palm_civet, predicted=chinese_serow, softmax_score=0.25652874, crops=1; source=frozen manifest; raster not visually adjudicated.
- ced57dfa-8c29-11eb-ac47-000d3a74c7de: true=sambar, predicted=eurasian_wild_pig, softmax_score=0.54233301, crops=1; source=frozen manifest; raster not visually adjudicated.
- cf18d255-8c29-11eb-ac59-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.45349985, crops=1; source=frozen manifest; raster not visually adjudicated.
- cf1af53f-8c29-11eb-9709-000d3a74c7de: true=sambar, predicted=common_palm_civet, softmax_score=0.30922249, crops=1; source=frozen manifest; raster not visually adjudicated.
- cff39b0e-8c29-11eb-9eb5-000d3a74c7de: true=large_antlered_muntjac, predicted=eurasian_wild_pig, softmax_score=0.71178585, crops=1; source=frozen manifest; raster not visually adjudicated.
- cff5fb0b-8c29-11eb-800b-000d3a74c7de: true=sambar, predicted=eurasian_wild_pig, softmax_score=0.75907642, crops=1; source=frozen manifest; raster not visually adjudicated.
- d00dc9bd-8c29-11eb-be14-000d3a74c7de: true=masked_palm_civet, predicted=large_antlered_muntjac, softmax_score=0.36974671, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0102cb9-8c29-11eb-8e17-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.32054791, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0280166-8c29-11eb-aa15-000d3a74c7de: true=sambar, predicted=chinese_serow, softmax_score=0.93079197, crops=1; source=frozen manifest; raster not visually adjudicated.
- d028023c-8c29-11eb-ad70-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.94606543, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0744e31-8c29-11eb-ad4a-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.47647759, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0744e4e-8c29-11eb-8530-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.87415743, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0744f26-8c29-11eb-b106-000d3a74c7de: true=large_antlered_muntjac, predicted=eurasian_wild_pig, softmax_score=0.50233978, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0744f9e-8c29-11eb-8eb1-000d3a74c7de: true=large_antlered_muntjac, predicted=masked_palm_civet, softmax_score=0.53283739, crops=1; source=frozen manifest; raster not visually adjudicated.
- d076ae76-8c29-11eb-bf32-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.55748081, crops=1; source=frozen manifest; raster not visually adjudicated.
- d076af4e-8c29-11eb-b46a-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.51800215, crops=1; source=frozen manifest; raster not visually adjudicated.
- d076afb7-8c29-11eb-974d-000d3a74c7de: true=large_antlered_muntjac, predicted=silver_pheasant, softmax_score=0.39448562, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0791282-8c29-11eb-bbf4-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.44838735, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0791397-8c29-11eb-908e-000d3a74c7de: true=sambar, predicted=chinese_serow, softmax_score=0.52579719, crops=1; source=frozen manifest; raster not visually adjudicated.
- d07913c6-8c29-11eb-866b-000d3a74c7de: true=sambar, predicted=masked_palm_civet, softmax_score=0.99059707, crops=1; source=frozen manifest; raster not visually adjudicated.
- d07913d8-8c29-11eb-895c-000d3a74c7de: true=sambar, predicted=masked_palm_civet, softmax_score=0.60801834, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0791401-8c29-11eb-baf9-000d3a74c7de: true=sambar, predicted=masked_palm_civet, softmax_score=0.86575198, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0791407-8c29-11eb-b1b9-000d3a74c7de: true=sambar, predicted=masked_palm_civet, softmax_score=0.98038405, crops=1; source=frozen manifest; raster not visually adjudicated.
- d0791454-8c29-11eb-b918-000d3a74c7de: true=sambar, predicted=eurasian_wild_pig, softmax_score=0.55941463, crops=1; source=frozen manifest; raster not visually adjudicated.
- d08c31e4-8c29-11eb-acb8-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.46165860, crops=1; source=frozen manifest; raster not visually adjudicated.
- d08c32c4-8c29-11eb-8188-000d3a74c7de: true=sambar, predicted=masked_palm_civet, softmax_score=0.38169068, crops=1; source=frozen manifest; raster not visually adjudicated.
- d11da163-8c29-11eb-96db-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.76907986, crops=1; source=frozen manifest; raster not visually adjudicated.
- d11fff27-8c29-11eb-999a-000d3a74c7de: true=large_antlered_muntjac, predicted=annamite_striped_rabbit, softmax_score=0.92991066, crops=1; source=frozen manifest; raster not visually adjudicated.
- d11fff95-8c29-11eb-811f-000d3a74c7de: true=large_antlered_muntjac, predicted=masked_palm_civet, softmax_score=0.36239040, crops=1; source=frozen manifest; raster not visually adjudicated.
- d120009b-8c29-11eb-81a1-000d3a74c7de: true=large_antlered_muntjac, predicted=eurasian_wild_pig, softmax_score=0.63433290, crops=1; source=frozen manifest; raster not visually adjudicated.
- d12263b4-8c29-11eb-a746-000d3a74c7de: true=large_antlered_muntjac, predicted=annamite_striped_rabbit, softmax_score=0.92723429, crops=1; source=frozen manifest; raster not visually adjudicated.
- d12263c8-8c29-11eb-8e01-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.50699019, crops=1; source=frozen manifest; raster not visually adjudicated.
- d1226401-8c29-11eb-bd10-000d3a74c7de: true=large_antlered_muntjac, predicted=masked_palm_civet, softmax_score=0.54081607, crops=1; source=frozen manifest; raster not visually adjudicated.
- d1226402-8c29-11eb-a3a2-000d3a74c7de: true=large_antlered_muntjac, predicted=masked_palm_civet, softmax_score=0.83978188, crops=1; source=frozen manifest; raster not visually adjudicated.
- d12e4d23-8c29-11eb-9978-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.69210237, crops=1; source=frozen manifest; raster not visually adjudicated.
- d12e4db0-8c29-11eb-8b81-000d3a74c7de: true=large_antlered_muntjac, predicted=annamite_striped_rabbit, softmax_score=0.94876564, crops=1; source=frozen manifest; raster not visually adjudicated.
- d13f03ab-8c29-11eb-b87d-000d3a74c7de: true=annamite_striped_rabbit, predicted=masked_palm_civet, softmax_score=0.40301254, crops=1; source=frozen manifest; raster not visually adjudicated.
- d141615b-8c29-11eb-9522-000d3a74c7de: true=silver_pheasant, predicted=common_palm_civet, softmax_score=0.41318485, crops=1; source=frozen manifest; raster not visually adjudicated.
- d141624d-8c29-11eb-9a90-000d3a74c7de: true=eurasian_wild_pig, predicted=chinese_serow, softmax_score=0.41730165, crops=1; source=frozen manifest; raster not visually adjudicated.
- d1af07bd-8c29-11eb-bfd6-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.86948609, crops=1; source=frozen manifest; raster not visually adjudicated.
- d1b165c8-8c29-11eb-acc8-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.97928602, crops=1; source=frozen manifest; raster not visually adjudicated.
- d1b1669f-8c29-11eb-97ea-000d3a74c7de: true=sambar, predicted=large_antlered_muntjac, softmax_score=0.42023945, crops=1; source=frozen manifest; raster not visually adjudicated.
- d1b88c0f-8c29-11eb-a905-000d3a74c7de: true=sambar, predicted=chinese_serow, softmax_score=0.80134720, crops=1; source=frozen manifest; raster not visually adjudicated.
- d1dc4d72-8c29-11eb-8e61-000d3a74c7de: true=sambar, predicted=chinese_serow, softmax_score=0.33921530, crops=2; source=frozen manifest; raster not visually adjudicated.
- d20999d5-8c29-11eb-8770-000d3a74c7de: true=large_antlered_muntjac, predicted=chinese_serow, softmax_score=0.47875696, crops=1; source=frozen manifest; raster not visually adjudicated.
- d20bfd5a-8c29-11eb-9d04-000d3a74c7de: true=eurasian_wild_pig, predicted=sambar, softmax_score=0.89639646, crops=1; source=frozen manifest; raster not visually adjudicated.
- d20c0053-8c29-11eb-a5d4-000d3a74c7de: true=large_antlered_muntjac, predicted=sambar, softmax_score=0.61709064, crops=1; source=frozen manifest; raster not visually adjudicated.
- d20e605f-8c29-11eb-b113-000d3a74c7de: true=sambar, predicted=chinese_serow, softmax_score=0.61138153, crops=1; source=frozen manifest; raster not visually adjudicated.
- d2db75da-8c29-11eb-9bd4-000d3a74c7de: true=masked_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.68451840, crops=1; source=frozen manifest; raster not visually adjudicated.
- d2ff2d1a-8c29-11eb-838e-000d3a74c7de: true=eurasian_wild_pig, predicted=large_antlered_muntjac, softmax_score=0.56731731, crops=2; source=frozen manifest; raster not visually adjudicated.
- d38252a9-8c29-11eb-90d1-000d3a74c7de: true=chinese_serow, predicted=masked_palm_civet, softmax_score=0.33596316, crops=1; source=frozen manifest; raster not visually adjudicated.
- d397d5ec-8c29-11eb-b3e4-000d3a74c7de: true=masked_palm_civet, predicted=sambar, softmax_score=0.33632964, crops=1; source=frozen manifest; raster not visually adjudicated.
- d4d9a48e-8c29-11eb-a1d1-000d3a74c7de: true=eurasian_wild_pig, predicted=annamite_striped_rabbit, softmax_score=0.43425655, crops=2; source=frozen manifest; raster not visually adjudicated.
- d4e0db1a-8c29-11eb-bf95-000d3a74c7de: true=eurasian_wild_pig, predicted=large_antlered_muntjac, softmax_score=0.82081062, crops=1; source=frozen manifest; raster not visually adjudicated.
- d4e337b6-8c29-11eb-b814-000d3a74c7de: true=eurasian_wild_pig, predicted=large_antlered_muntjac, softmax_score=0.93452555, crops=1; source=frozen manifest; raster not visually adjudicated.
- d4e339da-8c29-11eb-8fec-000d3a74c7de: true=eurasian_wild_pig, predicted=large_antlered_muntjac, softmax_score=0.58138633, crops=1; source=frozen manifest; raster not visually adjudicated.
- d56fdd78-8c29-11eb-bd6d-000d3a74c7de: true=chinese_serow, predicted=masked_palm_civet, softmax_score=0.70101142, crops=1; source=frozen manifest; raster not visually adjudicated.
- d66c920e-8c29-11eb-bf43-000d3a74c7de: true=chinese_serow, predicted=eurasian_wild_pig, softmax_score=0.96147764, crops=1; source=frozen manifest; raster not visually adjudicated.
- d6893e09-8c29-11eb-aba7-000d3a74c7de: true=chinese_serow, predicted=sambar, softmax_score=0.88367683, crops=1; source=frozen manifest; raster not visually adjudicated.
- d772e17c-8c29-11eb-bd6f-000d3a74c7de: true=eurasian_wild_pig, predicted=silver_pheasant, softmax_score=0.99234712, crops=1; source=frozen manifest; raster not visually adjudicated.
- d7fab9d2-8c29-11eb-abfe-000d3a74c7de: true=masked_palm_civet, predicted=annamite_striped_rabbit, softmax_score=0.75810897, crops=1; source=frozen manifest; raster not visually adjudicated.
- d7fab9d4-8c29-11eb-ba40-000d3a74c7de: true=masked_palm_civet, predicted=common_palm_civet, softmax_score=0.88163453, crops=1; source=frozen manifest; raster not visually adjudicated.
- d82341d3-8c29-11eb-baf1-000d3a74c7de: true=silver_pheasant, predicted=common_palm_civet, softmax_score=0.39585188, crops=1; source=frozen manifest; raster not visually adjudicated.
- d82a6e79-8c29-11eb-85b7-000d3a74c7de: true=common_palm_civet, predicted=large_antlered_muntjac, softmax_score=0.64423281, crops=1; source=frozen manifest; raster not visually adjudicated.
- d82a6e84-8c29-11eb-ad50-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.48070198, crops=1; source=frozen manifest; raster not visually adjudicated.
- d8496eb4-8c29-11eb-9b6e-000d3a74c7de: true=eurasian_wild_pig, predicted=annamite_striped_rabbit, softmax_score=0.80930841, crops=1; source=frozen manifest; raster not visually adjudicated.
- d8496eba-8c29-11eb-b616-000d3a74c7de: true=eurasian_wild_pig, predicted=large_antlered_muntjac, softmax_score=0.68378741, crops=1; source=frozen manifest; raster not visually adjudicated.
- d84bcbfa-8c29-11eb-8157-000d3a74c7de: true=chinese_serow, predicted=eurasian_wild_pig, softmax_score=0.92308450, crops=1; source=frozen manifest; raster not visually adjudicated.
- d85a1ff4-8c29-11eb-a88f-000d3a74c7de: true=chinese_serow, predicted=sambar, softmax_score=0.71149063, crops=1; source=frozen manifest; raster not visually adjudicated.
- d85a2031-8c29-11eb-8070-000d3a74c7de: true=chinese_serow, predicted=sambar, softmax_score=0.52193421, crops=1; source=frozen manifest; raster not visually adjudicated.
- d86f9195-8c29-11eb-9382-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.39386192, crops=1; source=frozen manifest; raster not visually adjudicated.
- d86f9197-8c29-11eb-9a26-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.33866188, crops=1; source=frozen manifest; raster not visually adjudicated.
- d86f91ad-8c29-11eb-83cd-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.70470679, crops=1; source=frozen manifest; raster not visually adjudicated.
- d86f91b0-8c29-11eb-8c2e-000d3a74c7de: true=common_palm_civet, predicted=chinese_serow, softmax_score=0.70430136, crops=1; source=frozen manifest; raster not visually adjudicated.
- d86f91b6-8c29-11eb-94af-000d3a74c7de: true=common_palm_civet, predicted=chinese_serow, softmax_score=0.60033685, crops=1; source=frozen manifest; raster not visually adjudicated.
- d86f91d2-8c29-11eb-9314-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.29171219, crops=1; source=frozen manifest; raster not visually adjudicated.
- d876b4b4-8c29-11eb-a43d-000d3a74c7de: true=chinese_serow, predicted=sambar, softmax_score=0.37736532, crops=1; source=frozen manifest; raster not visually adjudicated.
- d890f146-8c29-11eb-8c31-000d3a74c7de: true=chinese_serow, predicted=large_antlered_muntjac, softmax_score=0.74892646, crops=1; source=frozen manifest; raster not visually adjudicated.
- d890f178-8c29-11eb-95e5-000d3a74c7de: true=chinese_serow, predicted=eurasian_wild_pig, softmax_score=0.50151200, crops=2; source=frozen manifest; raster not visually adjudicated.
- d890f1c4-8c29-11eb-bfb2-000d3a74c7de: true=chinese_serow, predicted=sambar, softmax_score=0.70323658, crops=1; source=frozen manifest; raster not visually adjudicated.
- d890f21d-8c29-11eb-9adb-000d3a74c7de: true=chinese_serow, predicted=annamite_striped_rabbit, softmax_score=0.53343117, crops=1; source=frozen manifest; raster not visually adjudicated.
- d890f21e-8c29-11eb-89af-000d3a74c7de: true=chinese_serow, predicted=sambar, softmax_score=0.86140931, crops=1; source=frozen manifest; raster not visually adjudicated.
- d890f21f-8c29-11eb-93b0-000d3a74c7de: true=chinese_serow, predicted=sambar, softmax_score=0.78699434, crops=1; source=frozen manifest; raster not visually adjudicated.
- d890f24d-8c29-11eb-9974-000d3a74c7de: true=chinese_serow, predicted=annamite_striped_rabbit, softmax_score=0.84904873, crops=1; source=frozen manifest; raster not visually adjudicated.
- d98b44a9-8c29-11eb-bacf-000d3a74c7de: true=silver_pheasant, predicted=chinese_serow, softmax_score=0.37937060, crops=2; source=frozen manifest; raster not visually adjudicated.
- d98b44b1-8c29-11eb-93ed-000d3a74c7de: true=silver_pheasant, predicted=common_palm_civet, softmax_score=0.35577613, crops=1; source=frozen manifest; raster not visually adjudicated.
- d98b451f-8c29-11eb-bc09-000d3a74c7de: true=silver_pheasant, predicted=common_palm_civet, softmax_score=0.62782383, crops=1; source=frozen manifest; raster not visually adjudicated.
- d9d2cd91-8c29-11eb-b239-000d3a74c7de: true=silver_pheasant, predicted=large_antlered_muntjac, softmax_score=0.47280711, crops=2; source=frozen manifest; raster not visually adjudicated.
- d9d2cdb1-8c29-11eb-97e8-000d3a74c7de: true=silver_pheasant, predicted=eurasian_wild_pig, softmax_score=0.48038495, crops=1; source=frozen manifest; raster not visually adjudicated.
- dbafa991-8c29-11eb-97ff-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.86051929, crops=1; source=frozen manifest; raster not visually adjudicated.
- dbdcf00e-8c29-11eb-8732-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.82180375, crops=1; source=frozen manifest; raster not visually adjudicated.
- dbdcf00f-8c29-11eb-b5a9-000d3a74c7de: true=common_palm_civet, predicted=masked_palm_civet, softmax_score=0.66407555, crops=1; source=frozen manifest; raster not visually adjudicated.
- dbeda072-8c29-11eb-bdbc-000d3a74c7de: true=chinese_serow, predicted=sambar, softmax_score=0.56378758, crops=1; source=frozen manifest; raster not visually adjudicated.
- dc11742d-8c29-11eb-9130-000d3a74c7de: true=eurasian_wild_pig, predicted=chinese_serow, softmax_score=0.35849929, crops=1; source=frozen manifest; raster not visually adjudicated.
- dc1fb54f-8c29-11eb-bc36-000d3a74c7de: true=chinese_serow, predicted=common_palm_civet, softmax_score=0.45008206, crops=1; source=frozen manifest; raster not visually adjudicated.
- dc39eede-8c29-11eb-aabf-000d3a74c7de: true=masked_palm_civet, predicted=common_palm_civet, softmax_score=0.34412307, crops=1; source=frozen manifest; raster not visually adjudicated.
- dc4d00d4-8c29-11eb-88c1-000d3a74c7de: true=masked_palm_civet, predicted=chinese_serow, softmax_score=0.73708123, crops=1; source=frozen manifest; raster not visually adjudicated.
- dc4d00e3-8c29-11eb-85fa-000d3a74c7de: true=masked_palm_civet, predicted=common_palm_civet, softmax_score=0.81445855, crops=1; source=frozen manifest; raster not visually adjudicated.

No night/visibility or detector-miss claim follows from this closed-set ground-truth-box evaluation.
Images share sequences/locations; class-balanced sample is not natural prevalence; one known within-Test RGB duplicate pair retained.
Softmax is uncalibrated; image counts do not estimate animal individuals. MegaDetector demo is a separate evaluation.
