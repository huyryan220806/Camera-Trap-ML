# TV3 W6 — progress

05/11/2026, nhánh `feat/crop-classifier`.

## Trạng thái thực tế

- Đã đọc yêu cầu mới `TV3_W6.md`, TV2 W6 tại
  `b91476d3d9658e006027225cfc93008125536c0f`, TV1 tại
  `11e451071f58146522df20e1890cc6fe6e488eb0` qua Git fetch/show.
- W5 đã tích hợp main `cfcf00615847d52fba73ee3e44fe0e6076bb840c`;
  local chưa merge, vẫn `5734d38c3af2fe052cf04c4c33d940e8f186306d` khi viết code.
- Đã viết module/CLI W6 riêng, candidate R1/R2, smoke/freeze/gate, cache768,
  fine-tune, resume, reload, package, tests và hướng dẫn.
- **Chưa chạy unit tests, smoke, training, reload, artifact audit; chưa commit/push.**
  Theo yêu cầu người dùng, các lệnh chạy/push được hướng dẫn để người dùng thực hiện.
- Rà tĩnh: parse AST các file Python mới và parse JSON candidate thành công;
  PowerShell parser không báo lỗi ở script checks. Đây không phải test PASS.
- Registry TV2 vẫn DRAFT, approval null; expansion TV2 vẫn PENDING.
  Không tạo hoặc ngụ ý có checkpoint/metric W6 hay approval của thành viên khác.
- Giữ nguyên các file W5 đã khóa và thay đổi notebook/EDA/tài liệu riêng có sẵn.

## Việc tiếp tục

Theo `docs/handoff_tv3_w6.md`: merge W5/TV2 → checks → commit source →
preflight/smoke train-only → freeze proposal → TV2 APPROVED → R1/R2 →
reload/audit/package → TV2 chọn recipe → các lượt có điều kiện.

Không chạy lại R0, không mở Test W4. Tối đa6 official attempts gồm lỗi/dừng,
12GPUh tổng gồm smoke/extraction, ≤2h/attempt; ledger ở `outputs/tv3_w6/usage.json`.
Khi chuyển máy phải mang ledger và toàn bộ các attempt, không reset lịch sử.

## Nhật ký để người thực thi điền sau mỗi bước

| Mục | Trạng thái | Run / epoch | Evidence / command |
|---|---|---|---|
| Tests | NOT RUN | — | `scripts/check_tv3_w6.ps1 -FullSuite` |
| Preflight R1/R2 | NOT RUN | — | `outputs/tv3_w6/preflight_R*_01.json` sau khi chạy |
| Smoke R1/R2 | NOT RUN | — | `outputs/tv3_w6/smoke/` sau khi chạy |
| Freeze/approval | PENDING TV2 | — | proposal/receipt thật sau review |
| Official R1 | NOT RUN | — | `outputs/tv3_w6/runs/R1_attempt01` dự kiến |
| Official R2 | NOT RUN | — | `outputs/tv3_w6/runs/R2_attempt01` dự kiến |
| R3/R4 | CONDITIONAL | — | chờ recipe vượt R0 |
| R5/R6 | BLOCKED | — | chờ release được TV2 chấp nhận |
| TV2 independent replay | NOT RUN | — | chờ checkpoint W6 |
| TV4 adapter verification | NOT RUN | — | chờ checkpoint/contract W6 |

Ghi đúng argv, source/config/receipt SHA, thời gian, GPU, epoch cuối và path thật.
Đừng đổi NOT RUN thành PASS từ việc chỉ đọc source hoặc tạo file rỗng.
