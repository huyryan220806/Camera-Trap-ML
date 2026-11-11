# R4_attempt01

Format: TV3_DINO_W6_V1. Recipe R2, pooling `x_norm_clstoken`,
feature dimension 384; seed 44. Full backbone + head.
Best epoch 6; completed 11 epochs.
Train: comparison_v1; validation: comparison_v1, 600 images / 680 GT crops.
Accuracy 0.8516666666666667; macro-F1 0.850644765168246.

Checkpoint SHA-256: `7eaa034773ebed9f513493eca6dda3c9e8f0bcc6d2c814ad357026e6a9656ce8`.
Use `src.training.dino_w6.load_package`, not the locked W5 loader.
RGB, square 256 uint8 bilinear antialias, ImageNet normalization, no EXIF.
Training loss averages within parent then across parents; validation averages
crop softmax vectors. Full-precision vectors and per-class metrics are in validation.json.

Fresh-process reload, independent TV2 model replay and TV4 adapter equivalence
are separate acceptance steps; see handoff.json and the actual receipts.
No Test evaluation. Validation reuse, one reference seed, GT boxes and balanced
classes limit generalization claims. Scores are not calibrated. R2 changes
optimizer and augmentation too; no isolated two-block causal claim or SOTA claim.
Seed42 stays headline; never replace it by a better seed43/44. No guarantee of 88%.
