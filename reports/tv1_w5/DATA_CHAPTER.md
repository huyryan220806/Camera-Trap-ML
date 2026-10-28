# Phần dữ liệu và thiết kế đánh giá — bản cập nhật tuần 5

**Ngày cập nhật:** 28/10/2026. Nội dung dùng cho báo cáo nhóm; số liệu đo của
mô hình giữ theo các artifact đã khóa. Phần mở rộng là khảo sát metadata.

## 1. Nguồn, phạm vi và ghi nhận dữ liệu

Đồ án sử dụng SWG Camera Traps từ LILA, gồm ảnh bẫy camera ở Việt Nam và Lào,
phù hợp phạm vi Trường Sơn xuyên biên giới. Trang dữ liệu công bố giấy phép
Community Data License Agreement, bản permissive. Nhóm ghi nguồn SWG/LILA
khi dùng ảnh và dùng tên trích dẫn do bên cung cấp hướng dẫn; không tải các
đường dẫn private hoặc ảnh người đã bị gỡ. Nguồn: [SWG trên LILA](https://lila.science/datasets/swg-camera-traps).

Bản metadata nhóm khảo sát có 2.039.657 bản ghi ảnh. Sau kiểm tra tọa độ,
101.384 bounding box được xác định hợp lệ; con số này là kết quả kiểm kê nội
bộ, khác số box được công bố trên trang giới thiệu. URL, thời điểm lấy và SHA
các archive được lưu trong [provenance v1](../../data/processed/v1/provenance.json).
Nhóm chỉ dùng tập con; không tuyên bố đã tải hoặc huấn luyện toàn bộ hơn hai
triệu ảnh. Chi tiết làm sạch: [EDA tuần 1](../eda/EDA_member1.md).

Phạm vi phân loại gồm tám lớp: large_antlered_muntjac, annamite_striped_rabbit,
sambar, chinese_serow, common_palm_civet, masked_palm_civet, silver_pheasant,
`eurasian_wild_pig`. Class ID 0–7
được giữ nguyên; việc chọn lớp dựa trên hỗ trợ nhãn/box và phạm vi nghiên cứu,
không chứng minh tất cả có cùng mức độ quý hiếm.

## 2. Làm sạch và chia tập

Nguồn v1 có 31.589 ảnh đáp ứng các điều kiện: đường dẫn công khai, metadata
không đánh dấu hỏng, một nhãn thuộc tám lớp, có box hợp lệ và nhãn box nhất
quán với nhãn ảnh, có ID chuỗi và địa điểm. Nhãn ảnh có nguồn gốc cấp chuỗi;
box/nhãn nhất quán chưa thay thế kiểm định từng cá thể bởi chuyên gia.

Nhóm chia theo địa điểm camera bằng seed 42, kiểm tra không giao ID ảnh,
đường dẫn, chuỗi và địa điểm giữa các tập. Pilot được chọn có chủ đích gồm
4.000 ảnh: 2.800 train, 600 validation, 600 Test; mỗi lớp tương ứng 350/75/75.
Mọi crop kế thừa split của ảnh gốc. Quy tắc khóa crop là padding 0, round theo
Python rồi clip biên ảnh, cạnh tối thiểu 8 px. B1/B2 dùng cùng danh sách ảnh.

`comparison_v1` gồm 3.125/680/680 crop cho train/val/Test. Đánh giá B2 lấy trung
bình vector softmax các crop của một ảnh rồi dự đoán lớp và tính metric cấp
ảnh. Demo sử dụng box do MegaDetector sinh nên không đồng nhất với đánh giá
classifier dùng GT boxes. MegaDetector đã dùng SWG khi huấn luyện, vì vậy
không gọi demo trên SWG là kiểm định detector độc lập.

## 3. Kết quả kiểm kê mở rộng tuần 5

Trong 31.589 ảnh nguồn, có 19.266 ảnh ngoài pilot thuộc train v1 đạt thêm điều
kiện geometry của bản so sánh. Chín ảnh nguồn có crop dưới 8 px được loại khỏi
ứng viên W5, gồm bảy train và hai validation; không sửa hoặc loại ảnh của
baseline đã khóa.

Để giới hạn chi phí và giảm lặp chuỗi, nhóm lập danh sách 1.665 ứng viên:
một ảnh trên một chuỗi chưa có trong pilot, tối đa 250 ảnh/lớp, phân bổ qua
địa điểm theo thứ tự hash với seed 42. Snapshot `w5_candidates_v1` ghi quyết
định với mọi ID nguồn và checksum để có thể tái lập. Đặc biệt, thỏ vằn chỉ còn
47 ảnh train ngoài pilot và 13 chuỗi mới; mở rộng số lượng không giải quyết
đồng đều thiếu dữ liệu ở mọi lớp.

Các ảnh ứng viên chưa được tải và kiểm định nội dung trong công việc W5 này.
Nếu toàn bộ đạt quality gate, số train dự kiến là 4.465 ảnh; không trình bày
con số đó như tập đã dùng huấn luyện. Lượt DINO đầu dùng nguyên train/val của
`comparison_v1`. Thử train mở rộng phải là experiment khác và ghi rõ thay
đổi dữ liệu, không quy toàn bộ cải thiện cho kiến trúc.

## 4. Đánh giá trong hai tuần cuối

Test B2 đã được mở và phân tích ở tuần 4. Kết quả lịch sử là accuracy 73,00%
và macro-F1 72,63% trên 600 ảnh với GT boxes. Các ứng viên mới được phát triển
bằng train/validation; không dùng Test cũ để chọn checkpoint, augmentation
hoặc ngưỡng duyệt. Mục tiêu accuracy ≥88% là mục tiêu nghiên cứu, chưa có
kết quả DINO của nhóm để xác nhận.

Trong phạm vi tám lớp có GT box của v1, loại các địa điểm đã có trong lịch sử
B0/crop/pilot chỉ còn 109 ảnh test ở 21 địa điểm. Thỏ vằn có một ảnh, cầy vòi
hương có ba ảnh. Nguồn này chưa đủ hỗ trợ để công bố một test mới cho cả tám
lớp. Vì vậy phương án hiện tại là báo kết quả validation của ứng viên và giữ
Test B2 làm kết quả lịch sử. Nếu có nguồn mới đủ điều kiện, phải khóa tập và
protocol trước lựa chọn ứng viên, khóa model bằng validation rồi mới mở đánh
giá; B2 và ứng viên cần được đo trên cùng tập mới.

## 5. Giới hạn và khả năng tái lập

Pilot cân bằng có chủ đích, không phản ánh tần suất loài trong tự nhiên.
Các ảnh cùng chuỗi/địa điểm có tương quan, vì vậy số ảnh không bằng số quan
sát độc lập. Một cặp trùng RGB trong Test cũ được giữ nguyên và công khai,
không bỏ sau khi đã khóa để tăng điểm. Kiểm tra hash RGB trước đây không
thay thế quét near-duplicate; với ảnh W5 mới, cả decode/hash và rà nhãn còn
là điều kiện trước phát hành. Chưa có bằng chứng loại trừ mọi trùng lặp với
dữ liệu tiền huấn luyện của mô hình nền tảng.

Nguồn/config/seed, ánh xạ lớp và các quyết định giữ/loại được lưu có phiên
bản. Script W5 tái lập cùng manifest, không ghi đè bản đã khóa và có staging
để tiếp tục khi bị ngắt. Toàn bộ kết quả chi tiết, bảng từng lớp và giới hạn
nằm trong [báo cáo kiểm kê W5](REPORT.md); bộ kiểm thử phần mềm không phải tỷ lệ
nhận dạng đúng của mô hình.
