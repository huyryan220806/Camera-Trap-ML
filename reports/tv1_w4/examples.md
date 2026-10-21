# TV1 W4 - Test Data Quality Examples

No predictions were used. No labels/splits were changed. Keep all samples.
Only exact RGB duplicates are confirmed issues. Small/border boxes are review candidates, not label errors.
Do not use these test examples to tune B3. Multiple boxes alone are not an error.

## c7f5e6b8-8c29-11eb-9993-000d3a74c7de
- Class: `common_palm_civet`
- Flags: candidate_box_touches_border
- Image: `data/images/swg_pilot_v2/public/lao/loc_0011/2017/11/image_00018.jpg`
- Boxes (xyxy): `[[2687, 1672, 3264, 2211]]`
- Action: retain unchanged.

## c7f5e709-8c29-11eb-8efc-000d3a74c7de
- Class: `large_antlered_muntjac`
- Flags: candidate_box_touches_border
- Image: `data/images/swg_pilot_v2/public/lao/loc_0011/2017/10/image_00057.jpg`
- Boxes (xyxy): `[[0, 1132, 1043, 2218]]`
- Action: retain unchanged.

## c7faae16-8c29-11eb-811b-000d3a74c7de
- Class: `silver_pheasant`
- Flags: candidate_box_touches_border, candidate_small_box_under_1pct, multiple_boxes_not_an_error
- Image: `data/images/swg_pilot_v2/public/lao/loc_0012/2017/10/image_00614.jpg`
- Boxes (xyxy): `[[0, 1482, 481, 2074], [1263, 1398, 1448, 1740]]`
- Action: retain unchanged.

## c85a0b3c-8c29-11eb-962d-000d3a74c7de
- Class: `annamite_striped_rabbit`
- Flags: candidate_small_box_under_1pct
- Image: `data/images/swg_pilot_v2/public/lao/loc_0032/2017/09/image_00015.jpg`
- Boxes (xyxy): `[[1668, 1164, 1927, 1330]]`
- Action: retain unchanged.

## c85a0bac-8c29-11eb-97a5-000d3a74c7de
- Class: `large_antlered_muntjac`
- Flags: candidate_box_touches_border
- Image: `data/images/swg_pilot_v2/public/lao/loc_0032/2018/03/image_00189.jpg`
- Boxes (xyxy): `[[0, 0, 1096, 550]]`
- Action: retain unchanged.

## c85f9078-8c29-11eb-9c81-000d3a74c7de
- Class: `sambar`
- Flags: multiple_boxes_not_an_error
- Image: `data/images/swg_pilot_v2/public/lao/loc_0035/2017/09/image_00067.jpg`
- Boxes (xyxy): `[[700, 681, 1307, 1276], [1140, 478, 1866, 1425], [1724, 658, 2560, 1342]]`
- Action: retain unchanged.

## c87dd57b-8c29-11eb-b19b-000d3a74c7de
- Class: `annamite_striped_rabbit`
- Flags: candidate_small_box_under_1pct
- Image: `data/images/swg_pilot_v2/public/lao/loc_0047/2017/09/image_00026.jpg`
- Boxes (xyxy): `[[1114, 874, 1269, 1093]]`
- Action: retain unchanged.

## c8a3f425-8c29-11eb-9296-000d3a74c7de
- Class: `annamite_striped_rabbit`
- Flags: candidate_small_box_under_1pct
- Image: `data/images/swg_pilot_v2/public/lao/loc_0072/2018/01/image_00009.jpg`
- Boxes (xyxy): `[[1058, 527, 1220, 632]]`
- Action: retain unchanged.

## c8a3f4ce-8c29-11eb-ba36-000d3a74c7de
- Class: `sambar`
- Flags: multiple_boxes_not_an_error
- Image: `data/images/swg_pilot_v2/public/lao/loc_0072/2017/11/image_00041.jpg`
- Boxes (xyxy): `[[378, 877, 1591, 1502], [522, 5, 993, 464], [792, 706, 1736, 1191]]`
- Action: retain unchanged.

## c8a3f4e5-8c29-11eb-a18c-000d3a74c7de
- Class: `sambar`
- Flags: multiple_boxes_not_an_error
- Image: `data/images/swg_pilot_v2/public/lao/loc_0072/2017/12/image_00033.jpg`
- Boxes (xyxy): `[[351, 92, 1051, 483], [419, 420, 1037, 1280], [684, 939, 1653, 1910]]`
- Action: retain unchanged.

## d86f91b0-8c29-11eb-8c2e-000d3a74c7de
- Class: `common_palm_civet`
- Flags: confirmed_exact_rgb_duplicate
- Image: `data/images/swg_pilot_v2/public/vietnam/loc_0851/2019/03/image_00081.jpg`
- Boxes (xyxy): `[[1782, 1318, 2912, 2437]]`
- Action: retain unchanged.

## d86f91b6-8c29-11eb-94af-000d3a74c7de
- Class: `common_palm_civet`
- Flags: confirmed_exact_rgb_duplicate
- Image: `data/images/swg_pilot_v2/public/vietnam/loc_0851/2019/03/image_00087.jpg`
- Boxes (xyxy): `[[1834, 1323, 2923, 2435]]`
- Action: retain unchanged.
