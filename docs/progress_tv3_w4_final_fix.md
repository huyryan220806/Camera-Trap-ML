# TV3 W4 final fixes - 2026-10-25

User explicitly authorized fixing TV3, then implementing TV4 W4 after checks.
Working branch feat/crop-classifier, base 4b4a691. No push/main merge requested.

Implemented exact prediction/CM replay with immutable evidence and failure,
mandatory frozen data/source checks in error analysis, native checkpoint sample,
and explicit historical B3 reproduction limitation. Original checkpoints, logs,
reports and comparison manifests are unchanged. No official training or Test.

Fresh B2/B3 validation completed: 600 images / 680 crops each with mandatory
SHA checks. B2 CM matches the prior PASS; B3 CM matches the prior CPU diagnostic,
not its historical reference. Original B3 reproduction remains UNRESOLVED.
Evidence on user machine: outputs/review_w4_2026-10-25/fixed_validation/.
Final full suite: 109/109 PASS (25.391 seconds), including scalar mismatch,
prediction/CM mismatch, default hash enforcement and safe artifact checks.
Technical fixes permit TV4 to continue using B2,
not B3. No official Test rerun or model change.
