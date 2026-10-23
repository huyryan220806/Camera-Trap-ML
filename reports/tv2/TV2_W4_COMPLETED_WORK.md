# TV2 W4 completed work — tiếp nối 23/10/2026

**W4-02 BLOCKED** tại bước đóng final selection, do reference B3 chưa tái lập được. Không còn blocker “không có B2 local” hoặc “không có B3 local”.

| Công việc | Trạng thái |
|---|---|
| Fetch/audit main và TV1/2/3/4 | DONE; remote heads không đổi, xem continuation_01/repository_audit.json |
| Tái sử dụng 600 Test ảnh đã khôi phục | DONE;600/600 SHA đúng,0 download |
| B2 file/hash/size/epoch/mapping/config/provenance | PASS |
| B2 fresh-process Validation, CM/error IDs, native adapter | PASS |
| B3 safe load/forward, mapping/config/provenance khai báo | PASS; SHA lần đầu ghi từ file người dùng |
| B3 reference reproduction CPU và CUDA | FAIL; evidence giữ nguyên, cần TV3 reconcile |
| Review TV3 W4 | PENDING FIX; blocker mới được chỉ rõ theo ID và runtime |
| Review TV4 W4 | HANDOFF NOT VERIFIED; branch vẫn254b40e |
| Model lock / evaluation protocol | UPDATED PENDING; locked_utc vẫnnull, chưa đóng giả |
| Test inference / metrics / CM / Test error analysis | BLOCKED; không có official run |
| Verifier và tests TV2 mới | DONE; không viết lại evaluator đã có |
| Regression/integrity/JSON/links/diff | Xem continuation_01/checks_summary.json và logs |
| Commit/push/PR | Xem continuation_01/publication.json; không tự nhận PR đã tạo |
| TV1 nghiệm thu | PENDING; chưa có acceptance |

TV3 cần cung cấp artifact Validation/log/runtime gốc và giải thích hai ID bất đồng trước khi TV2 khóa final method; không yêu cầu train lại hoặc đổi checkpoint. TV4 cần code/export sửa nhãn và benchmark W4 thật. Sau khi các gate thực sự PASS, commit immutable final lock/protocol trước Test, dùng đúng candidate run ID và không chạy lại official run. Không mở rộng W5/W6.
