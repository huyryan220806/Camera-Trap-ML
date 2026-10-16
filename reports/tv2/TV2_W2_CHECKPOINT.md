# TV2 W2 B0 Checkpoint

- Model: ResNet18 B0, ImageNet pretrained, frozen backbone, final classifier only.
- Run: `B0_run01`; best epoch 4; seed 42; 8 classes.
- Checkpoint filename: `best_model.pth`.
- Local location: `experiments/B0_run01/checkpoints/best_model.pth`.
- Size: **44,837,567 bytes**.
- Actual SHA-256, recomputed locally on 2026-10-11: `d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680`.
- Review SHA-256: `d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680`.
- MATCH: **YES**.

## Download

**READY — local validation and independent external download verified on 2026-10-11.**

Official user-provided [Google Drive download](https://drive.google.com/file/d/18ESoOAV8KqvSV2StS808BvKkcWaNSpUr/view?usp=drive_link).

TV2 opened the file in a browser showing the sign-in option, downloaded `best_model.pth` without signing in, and independently checked the downloaded copy: **44,837,567 bytes**, SHA-256 exactly matching the local checkpoint above. External download permission independently verified: **YES**. Google Drive displayed its large-file virus-scan notice before download. The downloaded copy did not replace the original checkpoint. Weights remain outside Git.

## Fresh checkout

1. Checkout the TV2 review-fix commit and install `requirements-tv2.txt` using Python 3.12, or reproduce the original environment recorded in `experiments/B0_run01/config.yaml` (Python 3.14.3, torch 2.13.0+cpu, torchvision 0.28.0+cpu). Exact numeric agreement across versions is not guaranteed.
2. Download `best_model.pth` from the official link. Run `Get-FileHash .\best_model.pth -Algorithm SHA256` and `(Get-Item .\best_model.pth).Length`; require the exact hash and byte size above before loading. Store it at the local location above or pass its path explicitly.
3. Supply the 64 original full validation images listed in `experiments/B0_run01/used_val.jsonl`. Each row records its public `url` and `file_name`; store the image under `data/images/<file_name>`. Keep the committed source pilot, class map and used manifest byte-identical. Do not run preparation/training into B0_run01 to restore images.
4. From the repository root:

```powershell
Get-FileHash experiments/B0_run01/checkpoints/best_model.pth -Algorithm SHA256
py scripts/validate_b0.py --checkpoint experiments/B0_run01/checkpoints/best_model.pth
# An externally stored checkpoint is also accepted:
py scripts/validate_b0.py --checkpoint <path-to-best_model.pth>
```

**No retraining is required to validate the checkpoint.**

## Expected validation

| Item | Expected |
|---|---:|
| Best epoch | 4 |
| Validation samples | 64 |
| Macro-F1 | 0.3616866793337382 |
| Macro-Precision | 0.46773504273504274 |
| Macro-Recall | 0.375 |
| Accuracy | 0.375 |
| Main metric differences | 0 |
| Provenance verification | PASS |
| Checkpoint reload | PASS |

Independent local validation on 2026-10-11 reproduced every value above with absolute differences **0** for all four main metrics, using the original Python 3.14.3 / torch 2.13.0+cpu / torchvision 0.28.0+cpu environment. Evidence: [final_handoff/b0_validation.json](final_handoff/b0_validation.json). No retraining was performed. `B0_run01` is an immutable historical experiment; the test set was not used for model selection.

The validator aborts before inference when frozen source/validation/class-map hashes, mappings, or row provenance differ. Pilot v1 did not freeze per-image SHA-256 at training time: decoding and manifest provenance can be verified, but historical image-byte identity cannot be claimed. For future manifests with `quality.local_path`/`quality.sha256`, image bytes are verified too. These are results on a small subset, not final system performance. Test is not used.
