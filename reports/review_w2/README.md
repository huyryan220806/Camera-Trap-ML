# Week-2 Review Evidence

Review date: 2026-10-09. No member branch code or experiment data was changed.

| Checkout | Commit | Unit tests |
|---|---|---:|
| TV2 `feat/baseline` | `8a48b86c7dfde00beba0fe21aea8394260cf9e56` | 29 passed |
| TV3 `feat/crop-classifier` | `a63d9b35a17a40bf3dd65e28c11a27eae1929c34` | 51 passed |
| TV4 `codex/tv4-week2-demo-detector` | `c69283a659c27498d1e9ec43781777af4dc37282` | 91 passed |

Review environment: Windows, Python 3.12.10, torch 2.8.0+cpu,
torchvision 0.23.0+cpu. Each suite was run from its own checkout with the shared
Python interpreter: `python -X utf8 -m unittest discover -s tests`.

- `artifact_audit.json`: read-only manifest identity, split and class checks;
  arithmetic verification of metrics from the committed confusion matrix.
- `tv2_reproduction.json`: synthetic run-manifest mutation and a real validation
  invocation that accepts a changed image ID despite a saved hash mismatch.
- `tv3_reproduction.json`: synthetic failed/missing crop resume, repeated limit,
  and inconsistent split/class/hash input accepted by CropDataset.

The probes describe defects at the reviewed commits; they are not passing
acceptance tests. They create and remove temporary fixtures, do not download
datasets or pretrained weights, and do not modify existing run artifacts.
After fixes, rejection of a bad fixture may cause an intentional nonzero exit;
members should add proper regression tests for the intended behavior.

From this handoff checkout, replace paths below with existing local checkouts:

```powershell
python reports/review_w2/audit_artifacts.py --tv1 . --tv2 C:/path/to/tv2 --tv3 C:/path/to/tv3 --output outputs/artifact-audit.json
python reports/review_w2/reproduce_tv2.py --repo C:/path/to/tv2 --output outputs/tv2-probes.json
python reports/review_w2/reproduce_tv3.py --repo C:/path/to/tv3 --output outputs/tv3-probes.json
```

The TV1 path must contain the frozen v1 and v2 manifests. TV2/TV3 must point to
separate checkouts with the appropriate member's code. Use outputs outside this
evidence directory to preserve the original review snapshot.

Actual B0 checkpoint reload, full retraining, crop-pixel inspection, and an
integrated post-merge suite were **not** performed. Neither member branch was
merged. See the Vietnamese reports for findings and remediation checklists.
