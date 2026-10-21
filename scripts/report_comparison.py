"""Render the comparison handoff report from verified frozen artifacts."""
import argparse
from pathlib import Path

from comparison_data import ROOT, DEFAULT_OUTPUT, DEFAULT_REPORT, require
from download_subset import load_json, sha256
from validate_comparison import validate


def render(folder, verification):
    validate(folder, check_images=False)
    result = load_json(verification)
    require(result.get('passed') and result.get('local_images_redecoded'), 'Full image verification must pass first')
    require(result['provenance_sha256'] == sha256(folder / 'provenance.json'), 'Verification belongs to another snapshot')
    summary = load_json(folder / 'summary.json')
    audit = load_json(folder / 'audit.json')
    provenance = load_json(folder / 'provenance.json')
    rows = [
        '# TV1 tuần 3 - Kết quả khóa dữ liệu so sánh', '',
        f"Dataset: `{provenance['dataset_version']}`. Kiểm định ảnh hoàn tất lúc `{result['checked_utc']}`.", '',
        '## Kết Luận', '',
        f"Đã khóa **{summary['retained']:,} ảnh**, loại **{summary['excluded']:,}/{summary['requested']:,} ảnh** từ pilot v2.",
        f"B1/B2 dùng cùng image ID, nhãn và split; B2 có **{summary['b2_crops']:,} crop specification**.",
        'Không thay split, lấy mẫu lại hoặc bù ảnh. Chưa huấn luyện/chọn mô hình.', '',
        '## Theo Split', '',
        '| Split | Nguồn | Giữ | Loại | B1 ảnh | B2 crop | Chuỗi | Địa điểm |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for r in summary['by_split']:
        values = [r[k] for k in ('requested', 'retained', 'excluded', 'b1_samples', 'b2_crops', 'sequences', 'locations')]
        rows.append('| ' + r['split'] + ' | ' + ' | '.join(f'{v:,}' for v in values) + ' |')
    rows += ['', '## Theo Lớp', '',
             'Mỗi ô ảnh dưới đây là giữ/loại; số crop tính riêng vì một ảnh có thể có nhiều cá thể cùng loài.', '',
             '| Loài | Train ảnh | Val ảnh | Test ảnh | Train crop | Val crop | Test crop |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for label in load_json(folder / 'class_map.json').values():
        group = [r for r in summary['by_class_split'] if r['label'] == label]
        rows.append('| ' + label + ' | ' + ' | '.join(f"{r['retained']}/{r['excluded']}" for r in group)
                    + ' | ' + ' | '.join(str(r['b2_crops']) for r in group) + ' |')
    rows += ['', '## Giữ Và Loại', '',
             '- Một nhãn loài trong class map và mọi box cấp ảnh đồng ý với nhãn ảnh.',
             '- Mọi box hữu hạn, trong biên; sau round/clip có cạnh ít nhất 8 px. Padding = 0.',
             '- Một box lỗi làm loại cả ảnh khỏi B1/B2; không chỉ bỏ crop lỗi ở B2.',
             '- `excluded.jsonl` lưu dòng gốc và từng lý do. `summary.json` thống kê theo split/lớp.',
             f"- Lý do loại thực tế: `{summary['exclusion_reasons']}`.",
             '- Kết quả 0 loại (nếu có) là do nguồn đã được làm sạch, không phải bỏ qua bộ lọc.', '',
             '## Kiểm Tra Chia Tập', '',
             f"- Giao nhau qua split: `{audit['cross_split_overlap']}`.",
             f"- ID trùng: {audit['duplicate_image_ids']}; đường dẫn trùng: {audit['duplicate_file_paths']}.",
             f"- Có {audit['unique_sequences']:,} chuỗi và {audit['unique_locations']:,} địa điểm giữ lại.",
             '- Kiểm tra cả nguồn trước lọc và đầu ra sau lọc; không che rò rỉ bằng cách lọc mất bằng chứng.',
             f"- Có {audit['exact_duplicate_groups']} nhóm trùng RGB cùng split/cùng nhãn; giữ và báo cáo trong `duplicates.json`.",
             f"- Tổng nội dung pixel khác nhau: {audit['unique_pixel_contents']:,}. Không phát hiện trùng RGB qua split.",
             '- Chưa tìm ảnh gần giống/perceptual duplicate. Không khẳng định toàn bộ SWG không rò rỉ.', '',
             '## Tính Toàn Vẹn', '',
             '- Đã giải mã và đối chiếu byte/pixel SHA-256 của toàn bộ ảnh nguồn trên máy TV1.',
             '- Validator tái dựng danh sách đủ điều kiện, đối chiếu từng field nguồn và mọi view B1/B2.',
             '- Hash nguồn, cấu hình và các file snapshot nằm trong `provenance.json`.',
             f"- SHA-256 provenance: `{result['provenance_sha256']}`.",
             '- Ảnh gốc tái sử dụng tại `data/images/swg_pilot_v2`, không upload ảnh lên Git.', '',
             '## Bàn Giao', '',
             '- Snapshot: `data/processed/comparison_v1/`.',
             '- TV2: `b1/train.jsonl`, `b1/val.jsonl`; một dòng/ảnh.',
             '- TV3: `b2/train.jsonl`, `b2/val.jsonl`; cắt ảnh gốc theo `bbox_xyxy`, không phải JPEG crop đã xuất.',
             '- Giữ nguyên `image_id`, nhãn, split và class map; không dùng crop run `v1_run03` thay thế.',
             '- B2 lấy trung bình loss theo ảnh khi train, trung bình xác suất crop theo ảnh khi đánh giá.',
             '- Test chỉ kiểm tra kỹ thuật; chưa dùng để chọn mô hình hoặc ngưỡng.',
             '- Hướng dẫn: [handoff_tv1_w3.md](../../docs/handoff_tv1_w3.md).',
             '- Tiếp tục: `.venv/Scripts/python.exe scripts/freeze_comparison.py`.', '',
             '## Bằng Chứng Bổ Sung', '',
             '- `verification.json`: đối chiếu snapshot và toàn bộ ảnh nguồn.',
             '- `tests.json`: kết quả unit suite, gồm các trường hợp lỗi và resume.',
             '- `crop_compatibility.json`: đối chiếu hình học với pipeline TV3 và smoke crop trên train.',
             '- `tv2_loader_compatibility.json`: reader TV2 đọc đủ B1, nạp 8 ảnh train thành tensor.',
             '- Không xem các kiểm tra kỹ thuật này là điểm số phân loại/phát hiện.', '',
             '## Giới Hạn', '',
             'Đây là pilot có chọn mẫu/cân bằng lớp từ tuần 1, không phải toàn bộ 31.589 ảnh có box.',
             'Một loài được xác nhận bằng tính nhất quán metadata, không phải thẩm định lại bởi chuyên gia.',
             'B2 dùng box ground truth; không phải đánh giá phát hiện của MegaDetector.',
             'Chưa train B1/B2, không có điểm số mô hình. Việc tích hợp loader của TV3 là bước tiếp theo.', '']
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--verification', type=Path, default=DEFAULT_REPORT)
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/tv1_w3/REPORT.md')
    args = parser.parse_args()
    require(not args.output.resolve().is_relative_to(args.folder.resolve()), 'Report must stay outside frozen snapshot')
    text = render(args.folder, args.verification)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
