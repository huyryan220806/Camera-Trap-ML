# Đề xuất TV3 gửi TV2 — W5

28/10/2026. **PROPOSED / PENDING TV2 AGREEMENT.** Không có xác nhận thay TV2.

Theo plan TV1 `9abc9c5`, lượt đầu dùng comparison_v1 2.800/600 ảnh, cùng GT crop
với B2 (3.125/680); không dùng ứng viên metadata hay Test đã phân tích W4.

Đề nghị một lượt seed 42 với DINOv3 ViT-S/16 LVD-1689M đóng băng; nếu ngày 1
không nhận được weights thì chọn DINOv2 ViT-S/14 LVD-142M và ID riêng. CLS 384
chiều, Linear 8 lớp, SGD lr0.01/momentum0.9/wd0.0001, cosine50, tối đa50 epoch,
patience7, 32 ảnh nguồn/batch; cùng FP32, không AMP. Loss mean crop trong ảnh
rồi mean ảnh; validation mean softmax trong ảnh; chọn macro-F1, hòa giữ best cũ.
Accuracy 88% chỉ là mục tiêu; không chọn threshold hoặc bỏ ảnh điểm thấp.

Chi tiết transform khác nhau theo backbone và lệnh pin SHA nằm trong
`docs/handoff_tv3_w5.md`. Cache có một view xác định/crop; không augmentation
ngẫu nhiên trong linear probe. So với B2, đây là đổi cả pretrained/kiến trúc/
recipe, không tuyên bố cùng compute hay suy ra nguyên nhân duy nhất từ điểm số.

TV2 cần xác nhận trước lượt thật: backbone và SHA đã pin, cấu hình cụ thể,
budget GPU/số lượt, metric/hòa điểm, dữ liệu và đơn vị gộp. File receipt sinh
bằng lệnh `pin` gắn với hash cấu hình cuối; evidence tham chiếu đồng thuận thật.
Không gửi thông điệp cho TV2 từ lượt làm việc này.

Cập nhật 29/10: TV2 `3f76643` cũng đề xuất seed42, hòa giữ epoch sớm và
argmax chọn class ID nhỏ nhất; ngân sách vẫn chưa chốt. Receipt mới do `pin`
sinh dùng DRAFT/APPROVED cùng schema TV2, kèm config_sha256 để ràng buộc recipe
TV3. Người dùng đã gửi đề xuất cho TV2; chưa nhận nội dung đồng thuận nên chưa
điền approval. Chi tiết tích hợp: `W5_TV2_COMPATIBILITY.md`.

Chưa đăng ký seed khác/grid/fine-tune/extended train. Mỗi mở rộng cần config,
ID, kế hoạch riêng trước khi xem kết quả mới. Một seed chưa chứng minh ổn định.
