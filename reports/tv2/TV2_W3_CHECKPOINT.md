# TV2 W3 B1 checkpoint handoff

Trạng thái: **LOCAL AND GOOGLE DRIVE CHECKPOINT VERIFIED – RELOAD PASS**.

## Checkpoint identity

| Trường | Giá trị |
|---|---|
| Run | `B1_run01` |
| Kind | `OFFICIAL` |
| Model | ResNet18, `IMAGENET1K_V1`, full fine-tune, không dropout |
| Outputs | 8 lớp |
| Trainable / frozen parameters | 11.180.616 / 0 |
| Best epoch | 22 |
| Epoch hoàn thành | 29, early stopping patience 7 |
| Local path | `experiments/B1_run01/checkpoints/best_model.pth` |
| Google Drive | [best_model.pth](https://drive.google.com/file/d/19efNKKDz0IwhoUYGrBr5X9fI_CnQ-EPq/view?usp=sharing) |
| Local size | 44.815.625 byte |
| Drive download size | 44.815.625 byte |
| Local SHA-256 | `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c` |
| Drive download SHA-256 | `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c` |
| Bytes/hash comparison | PASS |
| Reload trong training process | PASS |
| Reload process mới trên bản local | PASS |
| Reload process mới trên bản Drive | PASS |
| Metric/loss/logit delta bản local | 0 |
| Metric/loss/logit delta bản Drive | 0 |

Bản Drive được tải vào thư mục tạm riêng, không ghi đè checkpoint local. Checkpoint
không được commit lên GitHub.

## Model input and preprocessing

- Input: ảnh nguồn đầy đủ, RGB.
- Train: resize 256, random crop 224, horizontal flip 0,5 và color jitter
  `(brightness=0.2, contrast=0.2, saturation=0.1, hue=0.05)`.
- Validation/inference: resize 256 rồi center crop 224.
- Normalize theo ImageNet: mean `[0.485, 0.456, 0.406]`, std
  `[0.229, 0.224, 0.225]`.
- Khi đánh giá, dùng một dự đoán cho mỗi ảnh nguồn. Không dùng tập test để chọn
  checkpoint hoặc so sánh trong W3.

## Class mapping

| ID | Class |
|---:|---|
| 0 | `large_antlered_muntjac` |
| 1 | `annamite_striped_rabbit` |
| 2 | `sambar` |
| 3 | `chinese_serow` |
| 4 | `common_palm_civet` |
| 5 | `masked_palm_civet` |
| 6 | `silver_pheasant` |
| 7 | `eurasian_wild_pig` |

Class-map SHA-256 trong frozen handoff:
`122c3a8c6b297c1d63c3b18db91cf6b3f279a2f979e6b3e77824dbdd086fc58e`.

## Validation result

| Metric | Giá trị |
|---|---:|
| Support | 600 ảnh |
| Macro-F1 | 0,5624506868 |
| Macro-precision | 0,5748610369 |
| Macro-recall | 0,565 |
| Accuracy | 0,565 |
| Validation loss | 1,3379992723 |

Lệnh xác minh độc lập:

```powershell
python scripts/validate_b1.py --checkpoint <downloaded-best_model.pth> --sha256 5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c
```

Bằng chứng local: [b1_run01_verification.json](w3_evidence/continuation_03/b1_run01_verification.json).
Bằng chứng tải và validator Drive: [remote checkpoint verification](w3_evidence/continuation_04/remote_checkpoint_verification.json)
và [fresh-process validator output](w3_evidence/continuation_04/remote_drive_validator.json).

## TV4 consumption contract

TV4 phải tải từ URL trên, kiểm đúng size và SHA-256 trước khi load, dùng đúng
class mapping và preprocessing nêu trên, rồi từ chối chạy nếu provenance hoặc
mapping không khớp. URL không thay thế kiểm tra hash. Trạng thái bàn giao chỉ là
checkpoint B1 đã xác minh; đây không phải phê duyệt chọn B1 thay B2.
