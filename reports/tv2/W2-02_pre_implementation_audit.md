# W2-02 PRE-IMPLEMENTATION AUDIT

Audit date: 2026-10-08. Completed before implementation on the current working branch.

## Git

- Current branch: `feat/baseline` at `fb51b41`.
- Main branch read: `origin/main` at `4e7ad47` after `git fetch origin --prune`.
- Branches detected: `main`, `feat/baseline` (TV2), `feat/metadata-split` (TV1), `feat/crop-classifier` (TV3), `feat/demo` (TV4), plus local archived TV2 fix worktrees.
- Pre-existing untracked files: `Lich_trien_khai_6_tuan.docx`, `docs/Phan_cong_4_thanh_vien.xlsx`, `review_TV2_W1_round2_2026-10-02.md`, temporary Word lock file. These will not be modified.
- No `main.py` or training entry point exists on main or the working branch.

## Week 1 TV2 files found and reviewed

- `docs/experiment_protocol.md`, `docs/handoff_tv2_w1.md`, `notebooks/TV2_baseline_evaluation.ipynb`, `src/evaluation/metrics.py`, `tests/test_evaluation.py`, `requirements-tv2.txt`, `reports/tv2/environment_report.txt`.
- Decisions to inherit: seed 42; ResNet18 ImageNet weights; full image, frozen backbone and only final FC trainable; 224 image crop after resize 256; train RandomCrop, HorizontalFlip and ColorJitter; validation CenterCrop, no random transform; ImageNet normalization; Adam lr 0.001, weight decay 0.0001, batch size 32, up to 30 epochs; validation macro-F1 for checkpoint, early stopping patience 5 for B0; macro precision/recall/F1 over all eight classes with `zero_division=0`; test held until week 4.
- Experiment artifacts convention: `experiments/B0_run01/{config.yaml,checkpoints/best_model.pth,logs/train_log.csv,results/val_metrics.json}`. TV4 also reserves local `runs` for logs and checkpoints; the TV2 experiment protocol is more specific for B0.

## Other branches reviewed (read only)

- TV1 `origin/feat/metadata-split`: `configs/split_v1.json`, `data/processed/v1/{class_map.json,manifest_v1.jsonl,pilot_v1.jsonl,train.jsonl,val.jsonl,test.jsonl,split_statistics.json,provenance.json}`. The same v1 files already exist on the TV2 branch; no copy needed.
- TV3 `origin/feat/crop-classifier`: `docs/handoff_tv3_w1.md`, `scripts/tv3_crop_eda.py`, sample audit/image listing. TV3's 80 annotated preview images are not suitable as B0 full-image training data; original image bytes are local-only on TV3's machine.
- TV4 `origin/feat/demo`: `docs/architecture.md`, `docs/environment.md`, `docs/handoff_tv4_w1.md`, `CONTRIBUTING.md`; these establish repository/output conventions and confirm no existing live classifier or `main.py`.
- Main `origin/main`: README, tree, requirements, docs, scripts/src/tests, class map/manifests, project conventions. Main contains integrated week-one work but no B0 implementation.

## Dataset inventory

- Authoritative manifest: `data/processed/v1/manifest_v1.jsonl`; fixed subsets `train.jsonl` and `val.jsonl`. Week-one pilot: `pilot_v1.jsonl` (4,000 rows).
- Main v1 metadata counts: train 22,073; validation 4,835; test 4,681. Pilot metadata counts: train 2,800; validation 600; test 600. Pilot train has 350/class and validation 75/class. These are metadata counts, not verified local image counts.
- Number of classes: 8. Mapping in `data/processed/v1/class_map.json`: 0 large_antlered_muntjac; 1 annamite_striped_rabbit; 2 sambar; 3 chinese_serow; 4 common_palm_civet; 5 masked_palm_civet; 6 silver_pheasant; 7 eurasian_wild_pig.
- Dataset image root: `data/images/` by TV4 convention, currently absent. Each manifest row supplies the exact source URL and `file_name`; no image path is guessed.
- Image availability: zero original images in the workspace. Missing/corrupt image counts for a future selected training subset must be established after download and decoding. Test image bytes will not be downloaded.

## Existing reusable code and missing components

- Reuse `src/evaluation/metrics.py` for all metrics and class-map parsing. Reuse TV1 manifest and class mapping as-is. No Dataset/DataLoader, model builder, training loop, checkpoint utility, or B0 config exists.
- Runtime detected: Python 3.14.3, torch 2.13.0+cpu, torchvision 0.28.0+cpu, no CUDA. Pretrained weight cache not found. Public SWG URL responded HTTP 200 when network permission was granted.
- Missing: original train/validation image bytes; ImageNet weights; B0 code/config; smoke test; log, checkpoint, validation output, reload check and report.

## Planned files on TV2 branch

- Modify: `requirements-tv2.txt` only if torchvision/YAML dependencies need explicit declaration; `README.md` for B0 run instructions.
- Create: `configs/b0.yaml`; `src/data/b0_dataset.py`; `src/models/b0.py`; `src/training/b0.py`; `scripts/train_b0.py`; `scripts/validate_b0.py`; focused tests; `reports/tv2/TV2_W2.md`.
- Local run artifacts: `experiments/B0_run01/` for resolved config, fixed train/val subset manifest, logs, results and actual checkpoint; `data/images/` for downloaded original images. These are not changes to any other branch.
- Files copied from other branches: none anticipated. Manifest/class map needed from TV1 are already present locally, and reusable evaluation code from TV2 week 1 is already present.

## Execution decision

Use only the existing TV1 pilot's `train` and `val` rows for an explicitly recorded, deterministic balanced image subset if downloading and training all 3,400 pilot train/validation images exceeds this CPU-only environment. Keep original split labels and image IDs unchanged; record exact chosen IDs and all exclusions. Never use pilot test for model selection or hyperparameter tuning. Any measured result must be labeled with its actual evaluated subset size.
