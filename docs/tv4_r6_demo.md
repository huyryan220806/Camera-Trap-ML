# R6 candidate integration — TV4 W6

R6 is an explicit candidate, pending the group's final checkpoint decision. B2
remains the default. R5 failed and is not registered. Existing R1-R4 remain
available with their original native implementation and package pins.

Merged integration, 12/11/2026: R1-R4 use the byte-identical snapshot
`src/training/dino_w6_r1_r4.py`, while R6 keeps `dino_w6_r6.py`.
The canonical `dino_w6.py` remains TV3's current training/CLI implementation.
See [week-six integration](integration_week6.md) for tests and merge scope.

## Local setup

Use the existing demo environment, approved B2/MegaDetector weights and the clean
DINOv3 architecture checkout pinned by the registry. Model packages are local
artifacts, not committed weights. From the repository root:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/prepare_tv4_r6.py --zip C:/Users/lequy/OneDrive/Desktop/R6_attempt01.zip --receipt C:/Users/lequy/Downloads/R6_attempt01.sha256.json --output outputs/tv4/w6/r6_intake
.venv\Scripts\python.exe -X utf8 scripts/run_demo.py --port 8766 --dino-package outputs/tv4/w5/intake_20261102/DINOv3_LP_run01 --dino-repo outputs/tv4/w5/dinov3_architecture --w6-registry configs/demo_w6_r6.json
```

Select `DINO_W6_R6` explicitly in the UI. The original `configs/demo_w6.json`
still exposes only R1-R4. The augmented registry also records TV2's independent
acceptance commit `96d202563c63b47d4d3d6773c3d4b5a2a29c3c7a`.

R6 uses `train_expansion_w6_v1`, CLS features of dimension 384, square 256 RGB
preprocessing and its own exact native snapshot `src/training/dino_w6_r6.py`.
The snapshot supports R6's three-hour training configuration; this integration
does not train or resume the model. Checkpoint, config, mapping, preprocessing,
source index, handoff, native source and architecture are checked before use.
Failures are reported explicitly without switching to another classifier.

## Reproduce checks

```powershell
.venv\Scripts\python.exe -X utf8 scripts/verify_tv4_w6.py --registry configs/demo_w6_r6.json --models DINO_W6_R6 DINO_W6_R2 --output outputs/tv4/w6/r6_equivalence_repeat
.venv\Scripts\python.exe -X utf8 scripts/benchmark_tv4_w6.py --registry configs/demo_w6_r6.json --models DINOv3_LP_run01 DINO_W6_R2 DINO_W6_R6 --output outputs/tv4/w6/r6_benchmark_repeat
```

Choose a new output directory for each run. Native equivalence compares logits
and softmax exactly on the same CPU, crops and batching, including batches 8+1,
one crop, per-box top-3 and cache replacement. This is not a GPU replay or a
validation accuracy measurement.

The benchmark reuses the locked 24 original train images: two warm rounds per
model, 48 requests each. It measures cold classifier initialization plus a crop,
cold detector pipeline, warm detector/classifier/pipeline timings and memory.
Run it without other inference or test processes. Pipeline timings exclude
HTTP, upload, browser rendering, disk input verification and review persistence.
No official Test W4 is used. Historical R1-R4 benchmark evidence remains intact;
R6's separate report includes contemporaneous W5 and R2 reference measurements.
