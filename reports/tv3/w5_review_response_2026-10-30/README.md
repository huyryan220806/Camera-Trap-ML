# Trả lời B1–B3 cho TV2 — 30/10/2026

TV3 đã xác nhận config. Gói này đề nghị TV2 kiểm tra và khóa protocol;
**chưa APPROVED chung, chưa official training, chưa checkpoint phân loại DINO**.
Phản hồi dựa trên review TV2 tại nhánh feat/baseline commit `9f528d2`.
Không thay hyperparameter, chạy lại smoke, huấn luyện hoặc truy cập Test.

## B1 — Bản chuẩn và hai cách tính SHA

File chuẩn là `configs/dinov3_lp_w5.local.json`, giữ nguyên **1063 bytes** của
bản đã gửi TV2, SHA-256:
`e9303ba38aeaec37fba2e7dd1829829a5a128abde8beb75c916b6cae62822dce`.

Smoke lưu hash do hàm `digest` trong `src/training/dino_probe.py` tính bằng:

```python
hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False,
                         allow_nan=False).encode('utf-8')).hexdigest()
```

Python dùng dấu phân cách mặc định **`, ` và `: `**, không phải compact JSON
(`,` và `:`), không indent và không newline cuối. Vì vậy hash này không bằng
hash raw file, hash đổi CRLF/LF hoặc hash sorted-compact TV2 đã thử.
Kết quả chính xác:
`32071801dc6eb6408310e6393f73acda9bd9902303236836e4bf8d8a4cb6d6e8`.

`config.digest-input.txt` chứa đúng byte đầu vào của phép tính này để TV2
rehash độc lập. **Đây không phải config chuẩn thứ hai**; chỉ là serialization
trung gian của cùng nội dung config. `verification.json` chứng minh JSON trong
smoke bằng toàn bộ config chuẩn, raw SHA và digest đều khớp. Giữ nguyên smoke
SHA `52c635be70f6f4a5466a7a816d9fc425036924f350ed9b6ea0a7a99e94549043`.

Preflight ngày28 chạy template chưa pin, digest `2c510c31…`; khác config chuẩn
chỉ ba trường `model.repo_commit`, `model.weights_sha256`, `model.weights_source`.
Verification liệt kê giá trị trước/sau và xác minh các tham số còn lại bằng
nhau, cùng provenance, cùng manifest. Preflight là bằng chứng dữ liệu lịch sử,
không được đổi tên thành smoke model hoặc full pixel verification ngày30.

## B2 — Xác nhận TV3

`TV3_APPROVAL.json` ghi config raw SHA, digest, experiment, ngân sách tối đa
một lượt và điều kiện TV2 APPROVED trước train. Người dùng TV3 đã xác nhận
gửi B2 và cho phép commit/push trong chat ngày30/10. Receipt ghi nguyên câu
xác nhận, ngữ cảnh và giới hạn xác thực; không giả chữ ký hay lời TV2.
Protocol local giữ DRAFT, experiments rỗng, chưa coi là đăng ký chính thức.

## B3 — Gói kiểm chứng và source

- `src/training/dino_probe.py` giữ đúng byte SHA trong smoke:
  `8529891d6cd213f4cc186de104b31d58d539782e2003fa6c475eb4000cdcb988`.
  Mã gồm đúng factory backbone, `load_state_dict(strict=True)`, frozen/eval,
  `weights_only=True`, hash/commit checks, RGB/no EXIF/padding0, transform
  uint8 square256 bilinear antialias → float32 scale → ImageNet normalize.
- `groups_for`, `image_balanced_loss`, `train_head`: gom đủ crop cùng parent,
  mean CE mỗi parent rồi mean batch32 parent, không nhân1/n hai lần, giữ batch
  cuối; SGD/cosine T_max50, step sau validation; best macro-F1, hòa giữ cũ.
  Cache32 crop là batch trích đặc trưng, khác batch32 ảnh huấn luyện head;
  backbone đóng băng nên không gradient accumulation qua crop microbatch.
- `scripts/dino_w5.py`, `src/training/dino_handoff.py`: protocol gate, export,
  checkpoint/config/class map, standalone load và fresh-process reload.
- `reports/tv3/pretrained_2026-10-29/`: smoke gốc và log16tests sau sửa loader.
- `reports/tv3/w5_evidence/`: preflight28 đầy đủ3400 ảnh, lịch sử kiểm thử,
  và kiểm thử tương thích bằng code TV2 nguyên bản tại3f76643.
- `verification.json`: rehash weights thực ngày30, kiểm checkout upstream sạch
  đúng commit6876159…, hash factory, metadata frozen và SHA ảnh mẫu hiện tại.
  **Không chạy lại smoke/forward/strict-load**: strict-load evidence là smoke
  PASS gốc liên kết source đúng hash có strict=True; không có log riêng
  missing/unexpected keys được ghi ngày29. Không tự tạo log đó bây giờ.
- Danh sách32 crop được dựng lại từ recipe đã thực thi `rows['train'][:32]`
  trên manifest frozen, kèm ID/path/bbox/byte SHA/RGB SHA kỳ vọng. Receipt ngày30
  chỉ rehash byte ảnh mẫu; không gọi đó là RGB decode mới hoặc log mẫu ghi
  đồng thời với smoke. `verified_source_images=0` trong smoke là counter của
  `read_release(verify_images=False)`, không đếm SHA mẫu do `crop_tensor` kiểm.

Tái kiểm B1 và hash metadata/source (không cần GPU/weights):

```powershell
python -X utf8 scripts/verify_tv3_w5_bundle.py
```

Nếu có vendor/weights/ảnh local, rehash thêm và xuất attempt mới:

```powershell
python -X utf8 scripts/verify_tv3_w5_bundle.py --local-assets --output outputs/tv3_w5/review_recheck_01.json
```

`artifact_index.json` ghi SHA/bytes và Git blob ID của source/config/evidence
trong gói; không tự hash chính nó. `publication.json` (bổ sung sau commit
source) ghi commit chứa source để TV2 truy vết mà không tạo self-reference.
Không đưa weights/vendor/ảnh/URL ký số vào Git.
