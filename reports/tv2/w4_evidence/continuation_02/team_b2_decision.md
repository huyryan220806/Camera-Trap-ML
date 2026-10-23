# Quyết định nhóm chọn B2 — bản ghi từ chỉ thị người dùng

Ghi nhận thực tế lúc 2026-10-23T06:43:22.151010+00:00. Nguồn là chỉ thị mới trong chat này; không suy ra thời điểm họp, chữ ký hoặc cá nhân phê duyệt.

> TÔI XÁC NHẬN: NHÓM ĐÃ THỐNG NHẤT CHỐT MÔ HÌNH B2 (`b2_run01`) LÀM MÔ HÌNH PHÂN LOẠI CUỐI CÙNG CỦA DỰ ÁN CAMERA-TRAP-ML.

> Nhóm chấp nhận ghi nhận sai lệch tái lập Validation B3 trên CPU/CUDA như một giới hạn thực nghiệm chưa được giải thích đầy đủ.

Nhóm chọn B2 b2_run01 / epoch21 bằng Validation, không dùng Test. B3 không được chọn cho Test. B3 CPU khác hai prediction, CUDA khác một prediction so với reference; exact reproducibility vẫn FAIL/UNRESOLVED, original runtime/training provenance chưa đầy đủ. Nhóm chấp nhận giới hạn này cho quyết định lựa chọn, không công nhận B3 kỹ thuật PASS.

B2 có bằng chứng fresh-process Validation PASS độc lập. Gate vẫn yêu cầu hash checkpoint, dữ liệu, protocol và commit khóa trước Test. Argmax sau mean softmax đủ crop, không confidence cutoff. Không thêm B1/B3 vào Test.

Quyết định TV3 trước đó tại 65b99b9 được lưu nguyên byte trong continuation_01/tv3_decision_source.md. Hồ sơ và FAIL lịch sử không bị ghi đè. TV1 chưa nghiệm thu W4-02.

Bản machine-readable: [team_b2_decision.json](team_b2_decision.json).
