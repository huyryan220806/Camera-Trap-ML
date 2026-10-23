# TV2 W4-02 — phân tích lỗi Test B2

Official run W4_test_eval01 có **162 lỗi /600 ảnh**, đúng438. Macro-F1 `0.7263366903`; không lấy Validation làm Test. B2 được khóa trước run; không dùng các lỗi này để chỉnh model/labels/threshold.

## Lớp khó

| ID | Loài | Precision | Recall | F1 | Support | Sai |
|---:|---|---:|---:|---:|---:|---:|
| 0 | large_antlered_muntjac | 0.630769 | 0.546667 | 0.585714 | 75 | 34 |
| 1 | annamite_striped_rabbit | 0.770833 | 0.986667 | 0.865497 | 75 | 1 |
| 2 | sambar | 0.642857 | 0.600000 | 0.620690 | 75 | 30 |
| 3 | chinese_serow | 0.733333 | 0.733333 | 0.733333 | 75 | 20 |
| 4 | common_palm_civet | 0.762712 | 0.600000 | 0.671642 | 75 | 30 |
| 5 | masked_palm_civet | 0.600000 | 0.680000 | 0.637500 | 75 | 24 |
| 6 | silver_pheasant | 0.929577 | 0.880000 | 0.904110 | 75 | 9 |
| 7 | eurasian_wild_pig | 0.772152 | 0.813333 | 0.792208 | 75 | 14 |

Precision thấp nhất: masked_palm_civet (0.600000), large_antlered_muntjac (0.630769), sambar (0.642857). Recall thấp nhất: large_antlered_muntjac (0.546667), sambar (0.600000), common_palm_civet (0.600000). Precision mô tả độ đúng của prediction mang nhãn đó; Recall mô tả tỷ lệ ảnh của loài được nhận ra. Mẫu75/lớp, mỗi lỗi thay Recall khoảng1.33 điểm phần trăm. Không suy ra hiệu năng ngoài tự nhiên từ thứ hạng mẫu này.

## Các cặp nhầm có hướng

| GT → Prediction | Số ảnh |
|---|---:|
| common_palm_civet → masked_palm_civet | 18 |
| large_antlered_muntjac → sambar | 12 |
| sambar → large_antlered_muntjac | 11 |
| chinese_serow → sambar | 8 |
| large_antlered_muntjac → masked_palm_civet | 7 |
| sambar → chinese_serow | 7 |
| common_palm_civet → annamite_striped_rabbit | 7 |
| chinese_serow → eurasian_wild_pig | 6 |
| masked_palm_civet → annamite_striped_rabbit | 6 |
| masked_palm_civet → common_palm_civet | 6 |
| large_antlered_muntjac → annamite_striped_rabbit | 5 |
| large_antlered_muntjac → eurasian_wild_pig | 5 |
| sambar → masked_palm_civet | 5 |
| sambar → eurasian_wild_pig | 5 |
| eurasian_wild_pig → large_antlered_muntjac | 5 |
| masked_palm_civet → sambar | 4 |
| silver_pheasant → common_palm_civet | 4 |
| large_antlered_muntjac → chinese_serow | 3 |
| common_palm_civet → chinese_serow | 3 |
| masked_palm_civet → large_antlered_muntjac | 3 |
| eurasian_wild_pig → chinese_serow | 3 |
| chinese_serow → annamite_striped_rabbit | 2 |
| chinese_serow → masked_palm_civet | 2 |
| common_palm_civet → large_antlered_muntjac | 2 |
| masked_palm_civet → chinese_serow | 2 |
| masked_palm_civet → silver_pheasant | 2 |
| silver_pheasant → large_antlered_muntjac | 2 |
| silver_pheasant → chinese_serow | 2 |
| eurasian_wild_pig → annamite_striped_rabbit | 2 |
| large_antlered_muntjac → common_palm_civet | 1 |
| large_antlered_muntjac → silver_pheasant | 1 |
| annamite_striped_rabbit → masked_palm_civet | 1 |
| sambar → common_palm_civet | 1 |
| sambar → silver_pheasant | 1 |
| chinese_serow → large_antlered_muntjac | 1 |
| chinese_serow → common_palm_civet | 1 |
| masked_palm_civet → eurasian_wild_pig | 1 |
| silver_pheasant → eurasian_wild_pig | 1 |
| eurasian_wild_pig → sambar | 1 |
| eurasian_wild_pig → common_palm_civet | 1 |
| eurasian_wild_pig → masked_palm_civet | 1 |
| eurasian_wild_pig → silver_pheasant | 1 |

Mỗi lỗi thuộc đúng một ô ngoài đường chéo; tổng các cặp bằng162. Không gộp hai hướng thành một nếu chưa cộng rõ.

## Box nhỏ và nhiều box

| Nhóm theo manifest integer boxes | Ảnh | Sai | Tỷ lệ sai | Sai / ảnh còn lại |
|---|---:|---:|---:|---:|
| multiple_crops | 57 | 9 | 0.157895 | 153 / 543 (0.281768) |
| box_area_below_1_percent | 70 | 18 | 0.257143 | 144 / 530 (0.271698) |
| box_within_1_pixel_of_edge | 171 | 56 | 0.327485 | 106 / 429 (0.247086) |

Nhóm có thể giao nhau; định nghĩa được khóa trong code trước Test: có ít nhất một crop diện tích<1% nguồn, hoặc box cách mép<=1px, hoặc nhiều crop. Đây là geometry integer pixel dùng để inference, không tự thay thế QA raw normalized boxes của TV1. Đối chiếu QA TV1:57 multi-box,70 box nhỏ,171 sát mép; cả ba tổng đều khớp. Mọi parent vẫn mean đủ crop rồi cho đúng1 prediction. Chênh lệch tỷ lệ mô tả tập con, chưa kiểm soát loài/sequence/location; không kết luận bbox là nguyên nhân.

## Ví dụ xác thực

| Image ID | GT → Prediction | Softmax score | Crop |
|---|---|---:|---:|
| c7f5e6b8-8c29-11eb-9993-000d3a74c7de | common_palm_civet → masked_palm_civet | 0.92323661 | 1 |
| c85f6991-8c29-11eb-b907-000d3a74c7de | large_antlered_muntjac → sambar | 0.65016848 | 1 |
| ca727e23-8c29-11eb-9327-000d3a74c7de | sambar → large_antlered_muntjac | 0.59818935 | 1 |
| d6893e09-8c29-11eb-aba7-000d3a74c7de | chinese_serow → sambar | 0.88367683 | 1 |
| cd795c25-8c29-11eb-9d41-000d3a74c7de | large_antlered_muntjac → masked_palm_civet | 0.94230318 | 1 |

Quy tắc lấy ví dụ: chọn5 cặp nhầm nhiều nhất (số giảm dần, tie ID lớp tăng dần), lấy image_id đầu tiên theo thứ tự tăng trong mỗi cặp. Không chọn ảnh để làm đẹp báo cáo. [error_statistics.json](w4_evidence/continuation_02/error_statistics.json) ghi nguồn local, SHA, boxes/kích thước và vectorsoftmax; [journal600 ảnh](w4_evidence/continuation_02/official_test/progress.jsonl) và [toàn bộ lỗi](w4_evidence/continuation_02/official_test/error_analysis.md) cho phép kiểm tra. Không suy ra ảnh đêm, che khuất, GT sai hoặc detector miss chỉ từ dự đoán.

## Đối chiếu dữ liệu và giới hạn

600 ảnh Test thuộc495 chuỗi và98 địa điểm, không phải600 quan sát độc lập hoàn toàn. Mỗi lớp75 ảnh, mẫu cân bằng không phản ánh tần suất loài ngoài tự nhiên. Một cặp trùng nội dung RGB cùng Test tại loc_0851 vẫn giữ nguyên (`d86f91b0-8c29-11eb-8c2e-000d3a74c7de`, `d86f91b6-8c29-11eb-94af-000d3a74c7de`); không lọc theo kết quả. Chỉ closed-set8 lớp. Ground-truth box classification không tương đương box detector dự đoán hoặc MegaDetector end-to-end demo; một số phiên bản MegaDetector đã dùng dữ liệu SWG khi huấn luyện, phải kiểm tra detector/version trước đánh giá end-to-end. Softmax chưa calibration; confidence thấp không chứng minh loài lạ. Số ảnh hoặc chuỗi không suy ra số cá thể. Phân nhóm box nhỏ/nhiều crop là mô tả quan sát, không chứng minh nguyên nhân lỗi. Không dùng lỗi Test để đổi B2, checkpoint, preprocessing, threshold hoặc nhãn.

Cặp RGB trùng vẫn được giữ theo protocol và dữ liệu khóa; không có cross-split overlap theo các chiều đã audit. Độ phụ thuộc giữa ảnh cùng chuỗi/địa điểm hạn chế suy luận thống kê; không báo confidence interval giả định600 ảnh IID. MegaDetector miss/no_detection và sửa nhãn trong demo cần evidence W4-04 TV4 riêng. B3 reproducibility vẫn unresolved, được nhóm chấp nhận cho selection, không được dùng trên Test.

## Kiểm tra trực quan ví dụ đã chọn

Hai ví dụ đầu được xem theo đúng quy tắc chọn đã nêu, không thay thế ví dụ sau khi xem ảnh. Ảnh `c7f5e6b8-8c29-11eb-9993-000d3a74c7de` có vùng bbox góc phải dưới rất tối, ít chi tiết trong bản hiển thị; chưa đủ để độc lập xác minh hình thái loài. Prediction sai vẫn có softmax0.9232366085, nên điểm lớn không bảo đảm đúng. Ảnh `c85f6991-8c29-11eb-b907-000d3a74c7de` có nhiều vùng đầu/thân con vật tiền cảnh sáng bệt, chi tiết khó quan sát. Đây là quan sát raster, chưa chứng minh nguyên nhân lỗi; không sửa GT hoặc dùng Test chọn ngưỡng. [Biên bản trực quan](w4_evidence/continuation_02/visual_error_review.json) giữ SHA nguồn. Không commit ảnh nguồn.
