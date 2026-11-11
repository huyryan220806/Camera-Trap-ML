# TV2 W6 — peer review release dữ liệu TV1

**PENDING REVIEW — không mở R5/R6.** Review metadata độc lập ngày04/11/2026;
không phải acceptance toàn release và không ghi approval vào snapshot TV1.

Release commit `11e451071f58146522df20e1890cc6fe6e488eb0` trên
`feat/metadata-split`, nội dung phát hành tại `c1d2789`, nền W5 `cfcf006`.
Provenance SHA256
`a6ac6933062b51280ad66dbca07853005007cc8da09848adcbe84ed83be9dda5`.
Metadata đọc bằng `git show` commit cố định, không merge hoặc sửa snapshot.
`quality_ready=true`, producer `peer_review_status=pending_TV2` được giữ nguyên.

## Phạm vi đã kiểm tra

Lệnh có log/source hashes trong evidence:

```powershell
python -X utf8 scripts/review_tv1_w6.py --output outputs/tv2_w6/d1_20261104_01/tv1_metadata_02
```

Môi trường thực: Python3.14.3, Windows11 build26200. Không thay môi trường dữ
liệu TV1 (Python3.12.10) hoặc runtime mô hình W5. Metadata/hình học dùng số học
Python chuẩn; Pillow chỉ dùng khi kiểm ZIP ảnh train mới. Không gọi wrapper
TV1 `verify --check-images` vì wrapper đó có phạm vi gồm raster Test.

| Kiểm tra | Kết quả thực |
| --- | --- |
| Provenance và19file snapshot, SHA raw Git bytes | PASS |
| 1665ứng viên =1446giữ+219cách ly, đủ quyết định | PASS |
| Train4246, GTcrop4729, B1/B2 cùng parent | PASS |
| 2800parent train cũ giữ nguyên mọi field | PASS |
| Nhãn/split/box nguồn ứng viên giữ nguyên | PASS |
| Classmap8lớp, bbox round-half-even/clip/min8/coverage | PASS |
| Parent crop count và weight1/N | PASS |
| Train so val/holdout ID/path/sequence/location | PASS theo metadata |
| Train so metadata fingerprint Test ID/sequence/location | PASS; không đọc Test manifest |
| Test path leakage độc lập | NOT VERIFIED; producer attestation, không mở manifest Test |
| SHA byte/RGB ảnh mới giữ so fingerprint nguồn và nội bộ | PASS theo producer metadata; không gọi là full raster audit độc lập |
| Val/Test main/b1/b2 Git object so cfcf006 | PASS cả6 blob; không mở Test manifest |
| Test raster bytes/decode hoặc model inference | NOT RUN; không được dùng phát triển W6 |

Train per-class images/crops:

| Class ID | Ảnh | Crop |
| --- | ---: | ---: |
| 0 | 584 | 602 |
| 1 | 360 | 360 |
| 2 | 572 | 666 |
| 3 | 514 | 529 |
| 4 | 536 | 539 |
| 5 | 521 | 528 |
| 6 | 570 | 735 |
| 7 | 589 | 770 |

Train mở rộng không cân bằng. Không thêm class weight/sampler trong cùng
lượt được mô tả là chỉ thay dữ liệu. Val vẫn cùng600/680/75ảnh mỗi lớp.

## Rà219ảnh cách ly

- **5 exact RGB:** lý do chính `exact_duplicate_pixel_sha256`, không ảnh nào
  lọt vào manifest mới. Metadata exact groups giữ nguyên ảnh cũ.
- **191 suspected near:** lý do `near_duplicate_pending_review`; kiểm347cặp
  và tính lại khoảng cách Hamming từ pHash/dHash đã xuất:≤4/≤8, tất cả train/train.
  Tổng193new IDs bị gắn cờ, trong đó2đã thuộc exact;193không phải số lý do chính191.
  Toàn bộ flagged IDs nằm trong219cách ly. Không coi nghi trùng là chắc chắn trùng.
- **23 mơ hồ:** `visual_ambiguity_pending_expert`; kiểm accounting80mẫu,
  57giữ/23cách ly và nhật ký quan sát TV1. Chưa nhận gói contact sheets hoặc
  byte ảnh cách ly, nên **không nhận là TV2 đã xem lại bằng mắt23ảnh**.

Metadata fingerprint chứa thông tin bảo vệ các split (gồm Test); đọc các hash
đã công bố khác việc mở ảnh/manifest Test. Các so sánh fingerprint dựa evidence
TV1, chưa phải TV2 tự rehash toàn bộ5774ảnh. Không chạy classifier hoặc lựa
chọn theo confidence, không tự sửa nhãn hoặc khôi phục ảnh cách ly.

## Gói ảnh và điều kiện còn thiếu

ZIP local `swg_train_expansion_w6_v1_additional.zip`, kích thước báo cáo
2.246.204.406byte, SHA báo cáo
`a88bfbf99aa25ac70637f35dca6056851e4c300dd89c3906185f943b13b3f659`.
Gói chỉ có1446ảnh giữ và19snapshot, không có219ảnh cách ly/109holdout.
Lượt kiểm `tv1_review_01` đã **exit0/PASS**: TV2 đo đúng SHA/kích thước trên,
kiểm đủ1465entries (19snapshot khớp Git), CRC, byte/RGB/dimensions/decode
**1446/1446ảnh train mới**, 0Testdecode. Pillow thực12.3.0, khác pin12.2.0
TV1; kết quả RGB vẫn khớp toàn bộ. Đây là kiểm pixels mới thực hiện tại TV2,
khác phần fingerprint metadata và không thay full audit các ảnh chưa kiểm.
Metadata được kiểm lại ở `tv1_metadata_final` với source SHA cuối; logic function
kiểm package không đổi. Evidence giữ cả hai receipt/lệnh/thời gian, không dùng
kết quả producer thay byte measurement TV2.

Để kết luận PASS cần đối chiếu các byte còn thiếu trong phạm vi cho phép,
nhận/rà bằng chứng thị giác và review leakage/quality toàn release. Với Test,
chỉ dùng attestation/hash đã khóa, không mở raster để làm W6. Nếu cần thay
chính sách hoặc nhận lại ảnh cách ly thì TV1 phát hành version mới.

Quy tắc quyết định: checksum/membership/geometry/leakage sai→FAIL; phần bắt
buộc chưa xác minh→PENDING; chỉ PASS sau đủ kiểm tra, có biên bản TV2 dẫn
SHA release. Hiện metadata PASS trong phạm vi trên nhưng overall **PENDING**.
Registry data_review vẫn PENDING, approvals TV2/TV3 null và R5/R6 CONDITIONAL.
