# TV2 W3 B1 checkpoint

Trạng thái: **AVAILABLE LOCALLY – VERIFIED – UPLOAD PENDING**.

| Trường | Giá trị |
|---|---|
| Run | `B1_run01` |
| Kind | `OFFICIAL` |
| Model | ResNet18, ImageNet1K V1, full fine-tune, 8 lớp |
| Best epoch | 22 |
| Local path | `experiments/B1_run01/checkpoints/best_model.pth` |
| Size | 44.815.625 byte |
| SHA-256 | `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c` |
| Validation support | 600 ảnh |
| Reload trong training process | PASS |
| Reload process mới | PASS |
| Metric/loss/logit delta | 0 |
| Download URL | Chưa có |

Lệnh kiểm tra độc lập đã chạy thành công:

```powershell
python scripts/validate_b1.py --checkpoint experiments/B1_run01/checkpoints/best_model.pth --sha256 5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c
```

Checkpoint không được commit lên Git theo quy định repository. Trước khi TV4 dùng,
cần upload tới kho artifact do nhóm chỉ định, tải lại, kiểm đúng size/SHA-256 và
chạy validator trên bản tải. [Bằng chứng đầy đủ](w3_evidence/continuation_03/b1_run01_verification.json).
