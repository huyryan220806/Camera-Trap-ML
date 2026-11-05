# TV3 W6 — DINOv3 pooling và partial fine-tuning

**05/11/2026: CODE PREPARED, EXECUTION PENDING.** Chưa chạy tests/GPU trong
lượt triển khai này, chưa có checkpoint hoặc kết quả W6. Hướng dẫn thực thi:
`docs/handoff_tv3_w6.md`; nhật ký: `docs/progress_tv3_w6.md`.

Đã kiểm tra cú pháp tĩnh Python/JSON/PowerShell và đối chiếu contract source TV2;
chưa thực thi unit tests hoặc chứng minh hành vi CUDA. Không dùng kiểm tra cú pháp
thay cho smoke, resume test hoặc fresh-process reload thực tế.

## Đối chiếu nguồn và phạm vi

Yêu cầu mới: `TV3_W6.md` người dùng cung cấp, thay phần W6 của `TV3_W5_W6`.
Plan TV1: [commit11e4510](https://github.com/huyryan220806/Camera-Trap-ML/blob/11e451071f58146522df20e1890cc6fe6e488eb0/docs/plans/TV3_W6.md).
TV2: [protocol DRAFT tại b91476d](https://github.com/huyryan220806/Camera-Trap-ML/blob/b91476d3d9658e006027225cfc93008125536c0f/docs/experiment_protocol_w6.md).
TV2 đã xong D1 chuẩn bị; chưa approval, chưa có thí nghiệm W6. W5 đã tích hợp.

## Code được bổ sung

- R1: backbone W5 frozen/eval, CLS384 + mean patch384, bỏ storage/register
  tokens khỏi pooling, head768 mới; SGD recipe giữ theo TV2.
- R2: full W5 init, chỉ hai block cuối + final norm + head; AdamW tách lr,
  bias/norm no-decay; LayerScale vẫn decay. Warmup `.5×lr,1×lr` ở epoch1/2,
  cosine về0 ở epoch20; đây là đề xuất phải được TV2 review trước freeze.
- Train loss mean crop CE/parent rồi mean parent; microbatch cắt ngang group
  vẫn đúng mẫu số actual parent count, kể cả batch cuối. Flip train p.5 chỉ R2.
- Cache W6 riêng, khóa pooling/dim/source/init/data/order/preprocess/runtime;
  R2 không dùng frozen cache. Val dùng mean softmax theo ảnh, đủ600/680.
- Last checkpoint đủ full model/best/optimizer/scheduler/RNG/sampler/patience;
  resume từ epoch hoàn tất, không reset early stop. Run lỗi giữ lịch sử/budget.
- Gate TV2/TV3 approval + committed config/source/receipt + matching smoke/runtime;
  expansion cần review PASS. Không thay file W5 hay nạp checkpoint W6 bằng W5 loader.
- Handoff đúng contract TV2; full-backbone best/last, source snapshot,
  raw/canonical config SHA, vectors/metrics/CM, exact fresh-process reload,
  ZIP kiểm CRC + payload SHA và bản report không weights.

## Bảng kết quả (chỉ điền số thật sau khi chạy)

| Run | Recipe | Seed | Train | Accuracy | Macro-F1 | Trạng thái |
|---|---|---:|---|---:|---:|---|
| R0 W5 | CLS frozen |42| comparison_v1 |0.845|0.8444008279545706| Reference đã được TV2 kiểm định |
| R1 | CLS + mean patch frozen |42| comparison_v1 |—|—| NOT RUN |
| R2 | FT2 + norm + head |42| comparison_v1 |—|—| NOT RUN |
| R3 | Chờ TV2 chọn |43| comparison_v1 |—|—| CONDITIONAL |
| R4 | Chờ TV2 chọn |44| comparison_v1 |—|—| CONDITIONAL |
| R5 | Recipe chọn/R0 fallback |42| expansion |—|—| BLOCKED |
| R6 | Như R5 |43| expansion |—|—| BLOCKED |

Giá trị R0 ở bảng dùng số tính độc lập của TV2; metric producer W5 có macro-F1
0.8444008279545705, lệch ~1e-16 do số học, không sửa dữ liệu W5.

Khi hoàn thành, đính kèm bảng từng attempt (kể cả FAILED/OOM/STOPPED), thời gian,
checkpoint/ZIP SHA, seed42 headline và mean/sample SD từng nhóm recipe/dataset,
paired outcomes so R0, civet/muntjac-sambar và lớp giảm≥4 ảnh đúng; kèm quyết định
reviewer cho regression. Artifact audit, producer reload, independent TV2 replay
và TV4 adapter là bốn kết luận khác nhau; không thay lẫn nhau.

Mục tiêu88% chưa được xác nhận. Không thử thêm ensemble/TTA/model lớn, không
lọc ảnh khó, không mở Test. Validation được tái dùng; GT-box classification
khác detector end-to-end, score chưa calibrated, không suy ra SOTA.
