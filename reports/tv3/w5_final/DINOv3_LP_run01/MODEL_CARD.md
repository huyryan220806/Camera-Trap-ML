# DINOv3_LP_run01

Frozen dinov3_vits16 + Linear(384,8), seed 42; best epoch 9.

comparison_v1: 2,800 source train images / 3,125 GT crops; 600 validation images / 680 GT crops. Geometry/padding fixed by TV1. One deterministic feature per crop; no stochastic augmentation. Loss averages crop CE within images then averages images. Validation averages crop softmax vectors per source image.

Validation accuracy: 0.845; macro-F1: 0.8444008279545705.

Intended use: research classification of eight SWG classes. Scores are not calibrated; GT crops differ from detector crops. This run does not establish independent Test performance, geographic transfer, 88% independent accuracy or seed stability. B3 reference remains unresolved. Demo predictions must remain separate per detection box.

Pretrained source: facebookresearch/dinov3:LVD-1689M:ViT-S16

Pretrained SHA-256: 08c60483bc63c04f533611e34bf70b120eedb7240f469bc16e9e20bf344b941d

Checkpoint SHA-256: acbe32252af4db420b7d6be4124b5273eadd81fff59620678d1f472413c0fbc3

See config.json, binding.json, validation.json, validation_comparison.json and reload report. Do not treat this package as reproduced until the fresh reload report passes.
