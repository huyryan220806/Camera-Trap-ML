# R1_attempt01

Format: TV3_DINO_W6_V1. Recipe R1, pooling `concat_x_norm_clstoken_mean_x_norm_patchtokens`,
feature dimension 768; seed 42. Full backbone + head.
Best epoch 3; completed 10 epochs.
Train: comparison_v1; validation: comparison_v1, 600 images / 680 GT crops.
Accuracy 0.835; macro-F1 0.8338641693401928.

Checkpoint SHA-256: `86b1c7460b300f27b2f8d5efe426def51750478e2bf195ffa61df1213f646f79`.
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
