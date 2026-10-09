# TV2 cross-review TV4 W2 – PENDING

Read-only source: `origin/codex/tv4-week2-demo-detector`, `docs/handoff_tv4_w2.md`, accessed 2026-10-09. No TV4 files or branch were modified.

The checklist is available and was read. Independent runtime/UI review has **NOT BEEN EXECUTED** in this TV2 checkout. TV4's own recorded results are not substituted for TV2 cross-review. Follow-up requires the TV4 environment, detector weights and a running local demo.

Pending checklist:

- Run TV4's complete unittest suite, `pip check`, and detector smoke.
- Upload image/preview; distinguish mock and real detector modes.
- Verify real boxes and exported JSON model version, threshold, hash.
- Check no-detection, invalid file and detector errors; no implicit mock fallback.
- Verify changing image/mode/threshold clears stale results.
- Verify SWG warning and classifier-not-available disclosure in JSON.
- Check small-screen layout and box alignment.

Status: **PENDING**, no approval or PASS claimed. This follow-up is separate from the two TV2 P2 fixes and does not require modifying TV4's branch.
