# Tích hợp tuần 6 — 12/11/2026

Người dùng xác nhận các thành viên đã hoàn thành bàn giao, yêu cầu gộp cả bốn
nhánh vào main. Lượt tích hợp bắt đầu 11/11 và tiếp tục 12/11 sau khi hết quota.
Giữ bốn nhánh cố định, lịch sử commit và toàn bộ bằng chứng của các lượt chạy.

## Phạm vi và đầu nhánh

| Thành viên | Nhánh | Đầu nhánh được tích hợp | Đầu ra |
| --- | --- | --- | --- |
| TV1 | feat/metadata-split | `11e451071f58146522df20e1890cc6fe6e488eb0` | Train mở rộng 4.246 ảnh / 4.729 crop, kế hoạch và bàn giao |
| TV2 | feat/baseline | `96d202563c63b47d4d3d6773c3d4b5a2a29c3c7a` | Protocol, duyệt dữ liệu, independent replay R1–R4/R6 |
| TV3 | feat/crop-classifier | `450f15bde6899faffac3c9389156d04c15196568` | Training/CLI, hồ sơ R1–R4/R6 và sự cố R5 |
| TV4 | feat/demo | `bbbccf979f437ebb80963a4067214f24ed31f639` | Adapter R1–R4/R6, kiểm giao diện, cache và benchmark |

Main ban đầu `cfcf006`. Fetch lại 12/11 xác nhận các đầu nhánh trên không đổi.
Không tạo chữ ký/approval thay thành viên; quyết định merge theo yêu cầu người dùng.

## Xử lý xung đột khi tích hợp

TV1, TV2, TV3 gộp không conflict. TV4 có một conflict add/add ở
`src/training/dino_w6.py`: source R1–R4 đã khóa khác validator cho R6 3 giờ.

- Giữ canonical `dino_w6.py` nguyên byte của TV3 để CLI/training còn hỗ trợ R6.
- Giữ source R1–R4 nguyên byte tại `dino_w6_r1_r4.py`, SHA-256
  `56f99e6ea2deed71f3281c531dc7d40a1a1e21f0d60faa8aae1c493ddb362fbc`.
- Giữ snapshot R6 `dino_w6_r6.py` của TV4, SHA-256
  `46e7a5364ad5685d84a3e48e7a6bffe1d9bfedba9547ac0037ce812dae6e79e9`.
- Adapter chọn đúng snapshot theo family. Không thay pins, class map,
  preprocessing, checkpoint hoặc source snapshot trong các gói kết quả.

## Kiểm định bản kết hợp

**551/551 kiểm thử PASS**, 110,221 giây theo unittest; command và thời gian
shell được lưu trong [receipt](../reports/integration_w6/full_tests_receipt.json).
[Log toàn bộ](../reports/integration_w6/full_tests.txt). Lượt này đã hoàn tất
trước khi quota ngắt; không chạy lại chỉ vì cập nhật tài liệu.

Hai kiểm thử tích hợp mới nạp metadata thật của R1/R2/R3/R4/R6, kiểm source
đúng hash và cấu hình R6 3 giờ. Phần checkpoint ở test này là fixture, không
phải tái suy luận toàn bộ validation. Full suite dùng CPU/fixture, có smoke
training tổng hợp cũ, không huấn luyện lại mô hình đồ án hoặc mở Official Test.

[Audit tích hợp](../reports/integration_w6/integration_audit.json) ghi các
kiểm tra bổ sung, source và dữ liệu được bảo toàn. Checkpoint W6 chưa có ở
workspace TV1 trong lượt này nên không tuyên bố đã chạy mới inference R6 thật
trên máy TV1. Kết quả model dựa trên [replay TV2](../reports/tv2/TV2_W6_R6_INDEPENDENT_MODEL_REPLAY_2026-11-10.md);
equivalence, benchmark và browser thực tế dựa trên [hồ sơ TV4](../reports/tv4_w6_r6/REPORT.md).

## Kết quả và giới hạn

- R0/W5: accuracy 84,50%, macro-F1 84,44%, 507/600 ảnh validation đúng.
- Recipe R2, seed 42/43/44: accuracy trung bình 84,89% ±0,48 điểm phần trăm;
  macro-F1 84,80% ±0,46 điểm phần trăm (SD mẫu).
- R6, seed 43, train mở rộng: **519/600**, accuracy **86,50%**, macro-F1
  **86,41867348%**. TV2 replay khớp tuyệt đối. Đây là thí nghiệm dữ liệu mở rộng
  một seed, không thay headline seed 42 của recipe R2 hay kết quả nhiều seed.
- R5 giữ FAILED, không đưa metric trung gian hoặc coi là seed hoàn thành.
- Chưa đạt 88%, chưa có Test độc lập cho DINOv3. Các số trên dùng GT boxes và
  cùng validation đã dùng chọn model; không phải accuracy toàn luồng detector.

**B2 vẫn là mặc định.** R1–R4/R6 là tùy chọn tường minh, chưa chọn lại model
mặc định trong yêu cầu merge này. MegaDetector đã dùng SWG, softmax chưa hiệu
chỉnh; ảnh không có detection vẫn cần được xem xét khi phân tích lỗi.

## Chạy và đồng bộ

Đã push bản kết hợp tại [`b9cebbb`](https://github.com/huyryan220806/Camera-Trap-ML/commit/b9cebbb66b10968739ba80b8fb3164de98076ca7),
xác nhận remote main chứa cả bốn đầu nhánh. [PR #9](https://github.com/huyryan220806/Camera-Trap-ML/pull/9)
đã được GitHub ghi nhận merged. [Receipt GitHub/remote](../reports/integration_w6/publication.json).

Lệnh mở demo W5 đang dùng vẫn giữ được. Sau khi nhận/kiểm gói W6 ngoài Git,
thêm `--w6-registry configs/demo_w6_r6.json` và chọn model trong giao diện.
[Hướng dẫn R1–R4](tv4_w6_demo.md), [hướng dẫn R6](tv4_r6_demo.md).
GitHub không chứa trọng số hoặc ảnh gốc; merge không tự tải các gói này.

Mỗi thành viên giữ nhánh cố định của mình. Sau khi commit/cất giữ việc local,
chạy `git fetch origin` rồi `git merge origin/main` trên nhánh đó trước việc
mới. Không reset hoặc force-push để đồng bộ.

Trạng thái công bố và cách tiếp tục nếu ngắt: [progress](progress_integration_w6_2026-11-11.md).
Các hồ sơ cũ có chữ pending/not run giữ đúng snapshot lịch sử; dùng biên bản
này cùng các receipt mới để xem trạng thái hiện tại.
