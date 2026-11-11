# CameraTrapML — TV2 W6 technical approval receipt (R1/R2)

**Date:** 2026-11-06 (Asia/Ho_Chi_Minh)  
**Role:** TV2 — Baseline & Evaluation  
**Status:** TV2 technical approval recorded; TV3 approval PENDING; W6 protocol remains DRAFT; official training NOT AUTHORIZED.

## Exact decision stated by TV2

> Tôi đã đọc biên bản review TV2 W6 D2 ngày 06/11/2026. Tôi đồng ý chấp thuận về mặt kỹ thuật đối với R1 và R2 theo cấu hình frozen đã được kiểm định, với điều kiện TV3 xác nhận approval riêng và protocol được khóa hợp lệ trước official training.

This is the TV2 decision given by the user directly in the project conversation, not a cryptographic signature or a TV3 approval.

## Frozen evidence binding

| Evidence | SHA / path |
| --- | --- |
| TV2 review | `reports/tv2/TV2_W6_TV3_PRETRAIN_REVIEW_2026-11-06.md` — `READY_FOR_TV2_DECISION` |
| TV3 handoff commit | `8cd97538390a3f55c66193d79e637dfd73ace770` |
| TV3 source commit | `127cac5b64d37fdda630a2f84b006a8e420dc9ed` |
| ZIP raw SHA-256 | `030093e92f07fcbe9a2a7ed39eb60919d66250181cd6c0dd9278106927e21ce7` |
| R1 frozen config canonical SHA-256 | `2ab03b7e13d798b8aace5e4b3542a189389c43c7630f4132303b9200fced63bf` |
| R2 frozen config canonical SHA-256 | `55dea8ab328e43581642deb964631d391a5b88596feb191a5fa5911a7a94acb7` |
| Runtime lock canonical SHA-256 | `7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a` |
| R1 smoke receipt raw SHA-256 | `9d5418745cf2cd45519415935246cb3be6ee6b5f0349341b9accb821b2cca1f6` |
| R2 smoke receipt raw SHA-256 | `6b7ead35a2bfbfb002154db14d992c2fd3ececfe3bf3c546be6bdb62433279e5` |

## Prerequisites to official R1/R2

1. TV3 explicitly confirms **its own** approval of the same frozen R1/R2 config, source, runtime and smoke evidence, with a traceable receipt. Neither TV2 nor any agent may approve on TV3's behalf.
2. After both approvals, Codex/TV2 validates immutable SHA bindings, updates the W6 protocol and registry to `APPROVED`, tests gates, commits and pushes the freeze on `feat/baseline`. Before this, status stays `DRAFT` and no official run is authorized.
3. TV3 verifies the actual GPU slot, runtime environment, memory and real usage budget before training. Short smoke PASS does not guarantee a full run within 2 GPU hours.
4. Any changes to algorithmic fields, source, frozen configs or runtime require re-review and, as appropriate, new smoke evidence.
5. R1/R2 use old `comparison_v1`; R5/R6 remain blocked until independent TV2 acceptance of the TV1 expansion release.
6. Official W4 Test must not be accessed for W6 development/model selection.

## Publication status

This receipt was generated for the user in the current conversation but **not committed or pushed** to GitHub. The GitHub connection returned `403 Resource not accessible by integration` when trying to create `reports/tv2/TV2_W6_TV2_TECHNICAL_APPROVAL_2026-11-06.md` on `feat/baseline`.

The user may ask Codex to add this receipt on `feat/baseline`, preserving its contents exactly, and to leave protocol/registry DRAFT until TV3's separate approval arrives.
