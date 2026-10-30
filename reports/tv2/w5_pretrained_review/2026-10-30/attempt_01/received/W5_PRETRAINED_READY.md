# TV3: pretrained DINOv3 thực, 29/10/2026

Đã nhận weights do người dùng tải từ liên kết Meta cấp qua email. Không lưu URL
ký số vào repo. File 86.531.063 bytes, SHA-256:
`08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d`.
Kiến trúc chính thức facebookresearch/dinov3 tại commit
`6876159a11b4df116f30f667f8c9888617df0751`.

Config pin: `configs/dinov3_lp_w5.local.json`; receipt đi kèm vẫn DRAFT.
Experiment đề xuất `DINOv3_LP_run01`, frozen CLS384 + Linear8, SGD lr0.01,
momentum0.9, wd0.0001, cosine50, seed42, max50 epoch, patience7, FP32.
Effective batch32 ảnh nguồn, loss mean crop CE trong ảnh rồi mean ảnh, giữ
batch cuối. Feature extraction batch32 crop; không gradient accumulation vì
backbone đóng băng và head học trên cache. Mean softmax cấp ảnh, hòa class ID
nhỏ nhất; chọn image macro-F1, hòa giữ epoch sớm hơn.

Smoke thực đã PASS: strict load weights ViT-S/16, backbone frozen/eval,
32 crop train thật → features `[32,384]`, hữu hạn, chạy RTX4060 Laptop CUDA.
Peak allocated của phép thử: 299.583.488 bytes; không đại diện peak của cả
lượt training hoặc tiến trình khác. Bằng chứng: `pretrained_2026-10-29/`.
Smoke chỉ kiểm tra metadata frozen và SHA byte của các ảnh mẫu, không đo
validation, không tạo feature cache chính thức hay checkpoint đã học 8 lớp.

Lệnh preflight đầu đã hoàn tất vòng kiểm tra dữ liệu nhưng thất bại ở import
model: hubconf upstream kéo thêm segmentation phụ thuộc torchmetrics chưa có.
Không có report model-preflight PASS của attempt đó. Loader được đổi sang
gọi trực tiếp factory `dinov3.hub.backbones.dinov3_vits16(pretrained=False)`
của cùng checkout chính thức, kiểm tra nguồn module; không sửa vendor hay
cài thêm thư viện segmentation. Sau đó smoke thực phía trên thành công.
Data preflight PASS có lưu đầy đủ của ngày28 vẫn là evidence lịch sử riêng.

Chờ TV2/TV3 xác nhận cấu hình cuối và receipt có nguồn truy vết trước chạy.
Chưa train, chưa có checkpoint DINO cho TV4, chưa commit/push.
