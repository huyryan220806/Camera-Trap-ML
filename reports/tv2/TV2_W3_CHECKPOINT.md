# TV2 W3 B1 checkpoint — NOT CREATED

W3-02 chưa train chính thức vì W3-01 và protocol chưa khóa, máy không có CUDA.

| Trường | Trạng thái |
|---|---|
| Official file | Chưa tồn tại; dự kiến experiments/B1_run01/checkpoints/best_model.pth |
| Size / SHA-256 / best epoch | N/A |
| Reload official / metric differences | NOT TESTED / N/A |
| Download URL | Chưa có |
| Upload | PENDING ARTIFACT UPLOAD — chỉ sau khi có checkpoint thật |
| TV4 handoff | BLOCKED — chưa có classifier B1 thật |

Checkpoint synthetic smoke chỉ sống trong TemporaryDirectory và bị xóa sau
kiểm thử. Hash/size trong smoke.txt **không phải checkpoint B1 để tải/bàn giao**.
B0 checkpoint W2 giữ nguyên.

Sau official training, lấy hash/size từ status.json và reload_validation.json,
kiểm lại byte file trước upload, rồi ghi URL tải thực và xác minh bản tải độc lập.
Lệnh đọc-only:

```powershell
python -X utf8 scripts/validate_b1.py --checkpoint <actual-B1-file.pth> --sha256 <actual-sha256>
```

Expected: provenance PASS, reload PASS, đúng class map và sample count của
freeze receipt, metric delta ≤1e-9, loss delta ≤1e-6, logits allclose với
atol1e-6/rtol1e-5. Giá trị metric thật chỉ được điền sau official run.
TV4 nhận model ResNet18, state dict, mapping, preprocessing/version/hash;
TV4 tự thực hiện W3-04, TV2 không sửa adapter hoặc hợp đồng ứng dụng.
