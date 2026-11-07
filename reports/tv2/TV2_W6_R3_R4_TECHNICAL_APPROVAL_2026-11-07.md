# TV2 W6 — Technical approval R3/R4

Date: 2026-11-07. Decision: **TECHNICALLY_APPROVED_BY_TV2_FOR_PROTOCOL_LOCK**.

TV2 has reviewed the R3/R4 handoff from commit `8c53db892bcf7700f9ac74a6f5bac3a2ffc91906`, including the R2 recipe selection from `ea3cad3eb9aa822ffc098aa927d5fe19a9508add`, exact frozen-config SHA and smoke bindings, unchanged training/evaluation source files from `127cac5b64d37fdda630a2f84b006a8e420dc9ed` to `95652c2d770cac464633eef0149bd27f4d859ece`, and the inherited two official attempts / GPU budget.

Scope: R3 seed 43 and R4 seed 44, recipe R2, dataset `comparison_v1`, source `95652c2d770cac464633eef0149bd27f4d859ece`, runtime lock `7ae3631e33e38e13e848d1be46c8e131bbaca25bc3191ba2a0a300e4a701527a`.

TV3 independently approved both runs at `6cbe8522b873dcbb2c5783baa3364f449cc62da6`, receipt `reports/tv3/w6/approvals/TV3_R3_R4.json`.

| Run | Frozen canonical SHA-256 | Frozen raw SHA-256 | Smoke SHA-256 |
|---|---|---|---|
| R3 | `dec76442a22f55043ccf1f1784cd303d0d944fd37e433271966642f181c5234d` | `4c52a6521a083a62122924e080716015310560f2a6544085ab7aef9acf2e8078` | `8210d1fb013fa7a220a577283627ff638c9b79a7abf1d68cc35f5c2025cd3bd2` |
| R4 | `839061f577cc374a8e105c5e41312b1919ea4efffd3c0e0c9b9c6a93a3ac3ff5` | `8e1ee676431166082cf9f0efa4d25b41424517f443282b7b8c13b614a67fe53d` | `af69ce7ac2645127e43936b4afe185b03026df1f654ed74e0bd5d56c7079deb8` |

Before official training, TV3 must check the committed registry, exact runtime, usage ledger (2/6 official attempts already used), local validator and test suite; individual attempts must remain <=2 GPU hours and total TV3 budget <=12 GPU hours, including smoke/reload.

This approval is not permission to run R5/R6, open Official Test W4, or change demo defaults. No personal signature, training results or new metrics are claimed by this file.
