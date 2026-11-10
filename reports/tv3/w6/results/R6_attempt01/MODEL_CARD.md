# R6_attempt01

Format: TV3_DINO_W6_V1. Recipe R2, pooling `x_norm_clstoken`,
feature dimension 384; seed 43. Full backbone + head.
Best epoch 13; completed 18 epochs.
Train: train_expansion_w6_v1; validation: comparison_v1, 600 images / 680 GT crops.
Accuracy 0.865; macro-F1 0.8641867348386344.

Checkpoint SHA-256: `24e3f51418dd7492a7537dff629794547c4540e8929bfe3e566105a6486581ef`.
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
