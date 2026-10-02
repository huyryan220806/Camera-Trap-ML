"""Create the Member 1 handoff report and reproducible EDA notebook."""
from collections import Counter
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from prepare_swg import ROOT

REPORT=ROOT/'reports/eda'
PROCESSED=ROOT/'data/processed/v1'


def read(path): return json.loads(path.read_text(encoding='utf-8'))
def n(value): return f'{value:,}'


def main():
    summary=read(REPORT/'summary.json'); classes=read(REPORT/'class_statistics.json')
    selected=read(ROOT/'configs/split_v1.json')['classes']
    split=read(PROCESSED/'split_statistics.json'); audit=read(PROCESSED/'audit.json'); provenance=read(PROCESSED/'provenance.json')
    lookup={c['name']:c for c in classes}
    reasons={
        'large_antlered_muntjac':'Ứng viên trọng tâm; nhiều ảnh có box và nhiều địa điểm.',
        'annamite_striped_rabbit':'Ứng viên trọng tâm; ít mẫu hơn nhưng có đủ chuỗi và địa điểm cho ba tập.',
        'sambar':'Lớp thú móng guốc để so sánh với mang và sơn dương.',
        'chinese_serow':'Kiểm tra khả năng phân biệt thú móng guốc; đã gộp hai cách viết cùng nhãn.',
        'common_palm_civet':'Lớp đối chứng trong nhóm cầy.',
        'masked_palm_civet':'Lớp dễ nhầm với common_palm_civet, hữu ích cho phân tích lỗi.',
        'silver_pheasant':'Bổ sung nhóm chim cho tập phân loại.',
        'eurasian_wild_pig':'Lớp phổ biến để quan sát mất cân bằng và làm đối chứng.'
    }
    selected_records=[{**lookup[c],'class_id':i,'selection_reason':reasons[c],'conservation_status':'not_assessed'} for i,c in enumerate(selected)]
    (PROCESSED/'selected_classes.json').write_text(json.dumps(selected_records,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':160})
    fig,axs=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    labels=[c.replace('_',' ') for c in selected]; y=np.arange(len(selected))
    axs[0].barh(y-.18,[lookup[c]['public_images'] for c in selected],height=.35,color='#436B95',label='Public image labels')
    axs[0].barh(y+.18,[lookup[c]['boxed_images'] for c in selected],height=.35,color='#568746',label='Eligible boxed images')
    axs[0].set_yticks(y,labels); axs[0].invert_yaxis(); axs[0].set_xscale('log'); axs[0].set_xlabel('Images (log scale)'); axs[0].legend(loc='lower left',bbox_to_anchor=(0,1.01),fontsize=8,ncol=2,frameon=False)
    axs[0].set_title('Image labels versus usable box coverage',pad=32)
    axs[1].barh(y,[lookup[c]['boxed_locations'] for c in selected],color='#8474A1')
    axs[1].set_yticks(y,labels); axs[1].invert_yaxis(); axs[1].set_xlabel('Distinct camera locations'); axs[1].set_title('Spatial support for selected classes')
    fig.savefig(REPORT/'class_coverage.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(12,5),layout='constrained')
    bottom=np.zeros(len(selected))
    for part,color in [('train','#436B95'),('val','#D49A3E'),('test','#568746')]:
        vals=np.array([next(r['sequences'] for r in split if r['label']==c and r['split']==part) for c in selected])
        ax.bar(np.arange(len(selected)),vals,bottom=bottom,label=part,color=color); bottom+=vals
    ax.set_xticks(np.arange(len(selected)),labels,rotation=35,ha='right'); ax.set_ylabel('Distinct sequences per class'); ax.set_title('Sequence support after location-held-out split'); ax.legend()
    fig.savefig(REPORT/'split_sequences.png'); plt.close(fig)
    counts={s:sum(r['images'] for r in split if r['split']==s) for s in ['train','val','test']}
    total=sum(counts.values())
    lines=[
      '# EDA và manifest v1 cho thành viên 1','',
      '## Kết quả bàn giao','',
      f'Đã đọc metadata gốc, thống kê toàn bộ nhãn và chọn đề xuất 8 lớp cho bài toán so sánh toàn ảnh với vùng cắt. Manifest chính có **{n(total)} ảnh**, pilot có **{n(audit["pilot"]["rows"])} ảnh**. Chưa tải ảnh thực tế và chưa huấn luyện mô hình.','',
      'Đây là tập đề xuất dựa trên mức hỗ trợ dữ liệu, chưa phải danh sách xác nhận tình trạng bảo tồn. Hai ứng viên trọng tâm là `large_antlered_muntjac` và `annamite_striped_rabbit`; các lớp còn lại tạo bài toán đối chứng và phân biệt loài.','',
      '## Thống kê metadata gốc','',
      '| Chỉ tiêu | Số lượng |','|---|---:|',
    ]
    for label,key in [('Bản ghi ảnh','images_metadata'),('Chuỗi ảnh','sequences_metadata'),('Địa điểm camera','locations_metadata'),('Nhãn gốc','categories_raw'),('Nhãn sau chuẩn hóa','categories_normalized'),('Bản ghi nhãn ảnh','annotations'),('Đường dẫn public','public_images'),('Đường dẫn private','private_images'),('Ảnh đánh dấu corrupt','corrupt_images'),('Ảnh có nhiều nhãn chuẩn hóa','multi_label_images'),('Annotation ở cấp chuỗi','sequence_level_annotations'),('Bản ghi trong file annotation box','box_annotations'),('Box hợp lệ theo kiểm tra tọa độ','valid_boxes'),('Ảnh có ít nhất một box hợp lệ','valid_box_images')]:
        lines.append(f'| {label} | {n(summary[key])} |')
    lines+=['',f'File box chứa {n(summary["box_validation"].get("no_bbox",0))} annotation không có tọa độ, và {n(summary["box_validation"].get("outside_or_nonpositive_bbox",0))} box vượt biên hoặc có kích thước không hợp lệ. Vì vậy số annotation trong file không đồng nghĩa với số bounding box sử dụng được.',
      '', 'Tên bộ dữ liệu trên trang giới thiệu không được dùng thay cho kiểm kê dữ liệu tải về. Bản metadata 1.1 tải trong lần này được ghi nhận bằng URL, ETag, thời điểm tải và SHA-256 trong `data/raw/sources.json`.',
      '', '### Phạm vi quốc gia và thời gian','', '| Quốc gia theo đường dẫn | Public | Ảnh | Địa điểm |','|---|---|---:|---:|']
    for r in summary['country_counts']: lines.append(f'| {r["country"]} | {bool(r["is_public"])} | {n(r["images"])} | {n(r["locations"])} |')
    lines+=['','Số địa điểm ở các hàng public/private có thể chồng lặp, không cộng các hàng này thành tổng địa điểm.', '',
            'Phân bố năm trong metadata: '+', '.join(f'{r["year"]}: {n(r["images"])} ảnh' for r in summary['year_counts'])+'.', '',
      '## Quy tắc làm sạch','',
      '1. Chuẩn hóa chữ thường, khoảng trắng và dấu gạch dưới. Gộp `chinese serow` với `chinese_serow`; lưu nhãn gốc và không gộp các loài khác nhau.',
      '2. Loại `empty`, `ignore`, `problem`, `blurred`, `human`, `vehicle`, động vật nuôi và các nhãn `unidentified*` khỏi ứng viên phân loại loài. Các nhóm chưa rõ loài như `pangolin`, `ferret_badger`, `roosevelts_muntjac_group` được đánh dấu cần xem xét taxonomy.',
      '3. Manifest chỉ lấy đường dẫn public, không đánh dấu corrupt, có kích thước ảnh dương, seq_id và location đầy đủ, đúng một nhãn ảnh chuẩn hóa thuộc lớp đã chọn.',
      '4. Tọa độ dùng dạng COCO pixel `[x, y, width, height]`. Loại box không hữu hạn, kích thước không dương, vượt biên hơn 1 pixel hoặc annotation box cấp chuỗi. Sai lệch biên tối đa 1 pixel được cắt về mép ảnh.',
      '5. Mỗi ảnh cần có ít nhất một box hợp lệ, mọi annotation box của ảnh phải hợp lệ và đồng ý với nhãn ảnh. Nhờ đó B1 và B2 dùng cùng ảnh có nhãn nhất quán. Các trường hợp nhiều loài hoặc xung đột nhãn được loại khỏi tập so sánh.',
      '6. Annotation ảnh có thể ở cấp chuỗi; manifest giữ cờ này. Với tập so sánh, box cấp ảnh là nguồn xác nhận bổ sung, nhưng vẫn cần kiểm tra ảnh trực quan ở tuần 1 và tuần 2.', '',
      '## Danh sách lớp đề xuất','',
      '| Class ID | Nhãn | Ảnh public theo nhãn | Ảnh đủ điều kiện | Chuỗi | Địa điểm |','|---:|---|---:|---:|---:|---:|']
    for i,c in enumerate(selected):
        r=lookup[c]; lines.append(f'| {i} | {c} | {n(r["public_images"])} | {n(r["boxed_images"])} | {n(r["boxed_sequences"])} | {n(r["boxed_locations"])} |')
    lines+=['','![Độ phủ nhãn và địa điểm](class_coverage.png)','']
    for c in selected: lines.append(f'- `{c}`: {reasons[c]}')
    lines+=['','Các lớp ít mẫu cần giữ ở phần thảo luận, không tự hứa mô hình sẽ nhận dạng tốt:','', '| Nhãn | Ảnh đủ điều kiện | Chuỗi | Địa điểm |','|---|---:|---:|---:|']
    for c in ['owstons_civet','asiatic_black_bear','red_shanked_douc','sun_bear']:
        r=lookup[c]; lines.append(f'| {c} | {r["boxed_images"]} | {r["boxed_sequences"]} | {r["boxed_locations"]} |')
    lines+=['','## Thiết kế split','',
      'Seed = **42**. Nhóm theo `location`, mục tiêu 70% train, 15% validation, 15% test theo số địa điểm. Dùng 2.000 hoán vị PCG64 và chọn phương án giảm sai lệch tỷ lệ ảnh và chuỗi từng lớp. Chỉ dùng metadata nhãn, không dùng kết quả mô hình để chọn split.',
      'Mỗi lớp phải có ít nhất 10 chuỗi và 2 địa điểm trong từng tập. Do nhóm theo địa điểm, tỷ lệ ảnh thực tế không cần đúng tuyệt đối 70/15/15. Đây là ngưỡng kiểm tra khả thi, không bảo đảm độ tin cậy thống kê cao cho lớp ít mẫu.','',
      '| Tập | Ảnh | Tỷ lệ ảnh |','|---|---:|---:|']
    for s,count in counts.items(): lines.append(f'| {s} | {n(count)} | {count/total:.2%} |')
    lines+=['','| Nhãn | Train ảnh / chuỗi | Val ảnh / chuỗi | Test ảnh / chuỗi |','|---|---:|---:|---:|']
    for c in selected:
        vals=[next(r for r in split if r['label']==c and r['split']==s) for s in ['train','val','test']]
        lines.append('| '+c+' | '+' | '.join(f'{r["images"]} / {r["sequences"]}' for r in vals)+' |')
    lines+=['','![Số chuỗi theo split](split_sequences.png)','',
      'Pilot lấy tối đa 500 ảnh mỗi lớp theo tỷ lệ mục tiêu, giữ nguyên split của manifest chính. Pilot chỉ dùng để thử đọc ảnh và chạy code; không thay thế tập test chính và không đại diện cho phân bố thực địa. Không dùng nhãn pilot test để tinh chỉnh mô hình.','',
      '## Kiểm tra rò rỉ và trùng lặp','',
      f'- Image ID trùng trong manifest: {audit["duplicate_image_ids"]}. Đường dẫn ảnh trùng: {audit["duplicate_file_paths"]}.']
    for k,v in audit['cross_split_overlap'].items(): lines.append(f'- Giá trị `{k}` xuất hiện ở nhiều split: {v}.')
    lines += [f'- Sai khác metadata ảnh giữa hai nguồn: {summary["box_image_metadata_mismatches"]}; ảnh nguồn box không tìm thấy trong nguồn chính: {summary["box_images_missing_main"]}.',
      '- Kiểm tra trên toàn bộ metadata: '+', '.join(f'{k}={summary[k]}' for k in ['duplicate_file_paths','sequences_spanning_locations','annotations_missing_image','annotations_unknown_category','images_without_label'])+'.',
      '- **Chưa kiểm tra trùng nội dung ảnh** bằng SHA-256 hoặc perceptual hash vì chưa tải ảnh. Cũng chưa xác nhận URL còn tải được, file giải mã được hay box chính xác về mặt thị giác. Đây là phần kiểm tra tiếp theo của TV1 và TV3, không coi là đã hoàn thành.',
      '', '## Tệp bàn giao và cách sử dụng','',
      '- `reports/eda/class_statistics.json`: thống kê mọi nhãn, cả nhãn bị loại; `summary.json`: tổng quan và kiểm tra dữ liệu.',
      '- `data/processed/v1/selected_classes.json`: danh sách lớp và lý do; `class_map.json`: ánh xạ class ID dùng chung.',
      '- `manifest_v1.jsonl`: mỗi dòng là một ảnh, có ID, đường dẫn, chuỗi, địa điểm, nhãn, split, kích thước và danh sách box.',
      '- `train.jsonl`, `val.jsonl`, `test.jsonl`: bản tách sẵn của cùng manifest; `pilot_v1.jsonl`: tập thử nhỏ.',
      '- `location_split.json`, `provenance.json`, `audit.json`: lưu phân nhóm, cấu hình, seed, nguồn và kết quả kiểm tra.',
      '- `notebooks/01_metadata_eda.ipynb`: notebook đọc các thống kê đã xuất, có thể dùng để trình bày EDA.',
      '', 'TV2 và TV3 phải dùng cùng manifest và class_map. Không tự random lại ảnh. Khi dữ liệu hoặc quy tắc thay đổi, tạo phiên bản v2 và giữ v1 để so sánh; sau khi khóa thí nghiệm, chỉ dùng validation để chọn mô hình và ngưỡng.',
      '', '## Giới hạn cần trình bày','',
      'Kết quả split chỉ chứng minh tách biệt các mã địa điểm trong SWG; không chứng minh hai vị trí gần nhau ngoài thực địa độc lập. Tập có box là một tập con được gán nhãn chọn lọc, không đại diện ngẫu nhiên cho toàn bộ ảnh SWG. Nhãn ưu tiên bảo tồn cần được kiểm chứng riêng bằng nguồn chuyên môn; số mẫu ít không đồng nghĩa với tình trạng nguy cấp.',
      '', '## Nguồn','',
      '- SWG (2021), Northern and Central Annamites Camera Traps 2.0: https://lila.science/datasets/swg-camera-traps',
      '- COCO Camera Traps và quy ước annotation: https://github.com/agentmorris/MegaDetector/blob/main/megadetector/data_management/README.md#coco-camera-traps-format',
      '- URL và checksum của hai gói tải về: `data/raw/sources.json`.',
      '', f'SHA-256 manifest chính: `{provenance["manifest_sha256"]}`',''
    ]
    (REPORT/'EDA_member1.md').write_text('\n'.join(lines),encoding='utf-8')
    def md(text): return {'cell_type':'markdown','metadata':{},'source':text.splitlines(keepends=True)}
    def code(text): return {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':text.splitlines(keepends=True)}
    cells=[md('# EDA metadata SWG\nNotebook cho TV1. Chạy pipeline trong README trước; notebook đọc kết quả kiểm kê, không tải 2 triệu ảnh.\n'),
      code("from pathlib import Path\nimport json\nfrom IPython.display import display, Markdown, Image\nROOT = Path.cwd()\nif not (ROOT / 'reports/eda/summary.json').exists():\n    ROOT = ROOT.parent\nassert (ROOT / 'reports/eda/summary.json').exists(), 'Chạy pipeline trong README trước'\ndef read(name):\n    return json.loads((ROOT / name).read_text(encoding='utf-8'))\nsummary = read('reports/eda/summary.json')\nsummary\n"),
      md('## Tất cả nhãn và chính sách làm sạch\n`images` là số ảnh có nhãn; `boxed_images` là số ảnh đạt bộ lọc so sánh B1/B2. Không nhầm số ảnh với số chuỗi.\n'),
      code("classes = read('reports/eda/class_statistics.json')\nclasses[:15]\n"),
      md('## Lớp đề xuất\nTình trạng bảo tồn chưa được suy ra từ metadata.\n'),
      code("read('data/processed/v1/selected_classes.json')\n"),
      code("display(Image(filename=str(ROOT / 'reports/eda/class_coverage.png')))\n"),
      md('## Chia theo địa điểm\nSeed 42, mục tiêu 70/15/15; không chia ngẫu nhiên từng ảnh.\n'),
      code("read('data/processed/v1/split_statistics.json')\n"),
      code("display(Image(filename=str(ROOT / 'reports/eda/split_sequences.png')))\n"),
      md('## Kiểm tra trùng lặp\nKiểm tra ID, đường dẫn, chuỗi và địa điểm; chưa kiểm tra hash nội dung ảnh.\n'),
      code("audit = read('data/processed/v1/audit.json')\nassert audit['metadata_leakage_check_passed']\naudit\n"),
      code("with (ROOT / 'data/processed/v1/manifest_v1.jsonl').open(encoding='utf-8') as f:\n    sample = json.loads(next(f))\nsample\n")]
    folder=ROOT/'notebooks'; folder.mkdir(exist_ok=True)
    for i,cell in enumerate(cells): cell['id']=f'cell-{i+1:02d}'
    (folder/'01_metadata_eda.ipynb').write_text(json.dumps({'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}},'nbformat':4,'nbformat_minor':5},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Report and notebook written:',REPORT/'EDA_member1.md')


if __name__=='__main__': main()
