# Thực nghiệm phân loại động vật bằng vùng cắt GT

Phần này mô tả kết quả kiểm định TV2 W5 ngày28–29/10/2026. B2 được tái lập
trên validation; DINO chưa có gói thực nghiệm đủ điều kiện. Không có kết quả
DINO hoặc Test mới trong chương này. Nguồn số liệu và raw predictions:
[TV2_W5.md](TV2_W5.md), [evidence](w5_evidence/attempt_01/artifact_index.json).

## Dữ liệu và phương pháp

comparison_v1 có tám lớp, train2.800 ảnh/3.125crops và validation600 ảnh/680crops;
validation75ảnh/lớp. Chia tập theo địa điểm, mỗi chuỗi nằm trong một split;
ID/path/sequence/location giữa split không giao nhau theo metadata validator.
Hash ảnh/RGB/kích thước của train và validation được đối chiếu lại. Nhãn xuất
phát từ metadata SWG cấp chuỗi; chưa có xác nhận chuyên gia/near-duplicate audit.

B1 fine-tune ResNet18 toàn ảnh; B2 fine-tune ResNet18 trên GT crops cùng parent
population, dùng pretrained ImageNet1K_V1. B2 cắt đúng bbox khóa/padding0,
Resize short256→CenterCrop224→ImageNet normalization khi validation. Mọi crop
cùng ảnh được softmax riêng rồi trung bình vector, argmax tạo một dự đoán/ảnh.
Không lọc ảnh theo confidence, không so metric cấp crop với metric cấp ảnh.

Macro-F1 cấp ảnh là metric chính, accuracy top1 là phụ; precision/recall/F1
đủ tám lớp với zero_division0. DINOv3 ViT-S/16 là hướng thử của TV3; chưa nhận
kiến trúc/pretrained/config/checkpoint/preprocessing thực để kiểm định. Protocol
W5 vẫn DRAFT chờ chốt seed/tie/ngân sách; không dùng cấu hình kế hoạch như
approval. Dữ liệu mở rộng1.665 ảnh chỉ là ứng viên metadata, chưa qua quality
gate nên không train. Holdout109 ảnh chưa đủ hỗ trợ độc lập tám lớp.

## Kết quả và tái lập

| Mô hình | Nguồn kết quả | Accuracy | Macro-F1 |
| --- | --- | --- | --- |
| B1 full-image | Validation lịch sử,epoch22 | 0,5650000000 | 0,5624506868 |
| B2 GT crops | Fresh-process validation W5,epoch21 | 0,7466666667 | 0,7454765175 |
| DINO | Chưa có artifact hợp lệ | N/A | N/A |

B2 macro-precision0,7484190017, macro-recall0,7466666667, đúng448/600.
Checkpoint SHA8787ffaf…2127e5 được kiểm đủ64ký tự trong raw evidence. Tính lại
metrics từ600 predictions/vector8lớp khớp verifier, CM và error IDs đã công bố.
Model gốc và demo adapter forward đủ680crops có max logit delta0,0 khi nạp trong
tiến trình sạch. Chưa có original training log và embedded run_id/git_commit
trong checkpoint; kiểm định suy luận không chứng minh đầy đủ provenance train.

Per-class P/R/F1/support và CM8×8 nằm trong báo cáo TV2 W5/CSV đi kèm. Lớp
large_antlered_muntjac có F1 thấp nhất0,541667; sambar0,657343, silver_pheasant
cao nhất0,944444. Nhầm0→2 có13ảnh,2→0 có12ảnh. Đây là mẫu nhầm quan sát, chưa
đủ giải thích nguyên nhân bằng thị giác/nhãn. Validation cân bằng nhưng pilot
được chọn có chủ đích, không đại diện phân bố tự nhiên hoặc địa điểm mới.

CPU i7-13620H/RAM15,71GiB, torch2.8.0+cpu,4threads,batch32crop. Lượt validation
65,793552s chạy cả native và adapter, không phải throughput thuần. API MD+B2
riêng trên1ảnh train: cold11,713562s/warm2,038520s inference wall; batchảnh1,
maxcrop8, actual1crop. N nhỏ và scope khác nên không suy rộng mọi máy hoặc so
với DINO chưa đo. Chưa có delta DINO, paired outcomes hoặc biến động giữa seed.

## Giới hạn và kết luận

Test B2 lịch sử W4 accuracy0,73/macro-F1 0,7263366903 (438/600ảnh,680GTcrops),
khóa trước suy luận tại2a750c3, được giữ nguyên; không dùng để chọn W5. B0 có
pilot khác nên ngoài phép thắng/thua trực tiếp; B3 còn FAIL/UNRESOLVED về tham
chiếu gốc. Một validator integrity raster toàn snapshot bị gọi nhầm rồi dừng
trước hoàn tất trong W5; scope gồm Test, không có inference/metric/selection
Test. Sự cố được công khai trong deviations, không nhận PASS cho lượt đó.

GT-box accuracy không phải end-to-end MegaDetector+classifier. MegaDetector
đã dùng SWG khi train nên demo SWG không là đánh giá detector độc lập. Score
softmax chưa calibrated; nhãn người dùng sửa trong fixture QA không phải GT
chuyên gia. Test phần mềm409PASS và API15PASS không đo chất lượng nhận dạng;
UI trực quan1440/390/320 và browser export vẫn BLOCKED vì môi trường.

Giữ B2 làm fallback. Mục tiêuaccuracy≥88% chưa được chứng minh; chưa kết luận
DINO tốt hơn hoặc đạt SOTA. Trạng tháiW5 PARTIAL, cần TV3 giao model/protocol
đã thống nhất và hoàn tất review browser trước nghiệm thu toàn bộ.
