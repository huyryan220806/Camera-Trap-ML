# TV4 W3 - Ket noi classifier va cache mo hinh

Ngay 18/10/2026. Branch co dinh: `feat/demo`. Nen TV1 W3: `7e9b194`.
Khong merge code W3 chua dat cua TV2/TV3. Khong train model moi.

## Ban giao

| Tieu chi | San pham |
| --- | --- |
| B0 chay that | MDv5a -> animal boxes -> crops -> ResNet18 B0 -> top 3 |
| Thay B1/B2 | Registry co 3 model ID, adapter ResNet18 va hop dong checkpoint ben duoi |
| Nhieu box | Top 3 rieng tung box, khong nhan ban mot du doan toan anh cho moi box |
| Cache | Model trong RAM, lazy load, lock giua request, LRU toi da 2 classifier |
| Diem du doan | Softmax class score, `scores_calibrated=false`, khong goi la xac suat da hieu chinh |
| Loi/khong phat hien | JSON co stage ro rang; khong fallback ngam, khong tra ket qua mot phan |

Luot kiem tra that dung **mot anh train v2**, khong chay tren test. Nhieu box
duoc test bang detector fixture va UI gia lap; khong khang dinh da kiem dinh
do chinh xac tren anh thuc dia nhieu ca the. B1/B2 duoc test bang state dict
gia lap dung kien truc; chua co checkpoint that duoc nghiem thu.

## Chay tren Windows

Tu goc repo, Python 3.12:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-tv4.txt
.venv/Scripts/python.exe scripts/prepare_tv4_demo.py
.venv/Scripts/python.exe scripts/prepare_tv4_classifier.py
.venv/Scripts/python.exe scripts/run_demo.py --port 8765
```

Neu da co B0 cua TV2, tranh tai lai:

```powershell
.venv/Scripts/python.exe scripts/prepare_tv4_classifier.py --source outputs/review_w2_round3/best_model.pth
```

Mo `http://127.0.0.1:8765`. Cong da duoc dung thi dung `--port 8766` (khong dung
tien trinh khac de chiem cong). Server chi bind loopback, anh upload giu trong
RAM, khong gui len cloud. Anh mau chi doc train v2; may moi co the upload anh
rieng ma khong tai 4000 anh. Neu can dung mau, chay downloader TV1 W2.

Giao dien mac dinh MegaDetector + B0. Gia lap la che do rieng, ca box va diem
loai deu gia lap, khong nap classifier that. "Chi detector" giu duong API cu.
B1/B2 bi khoa tren menu khi registry chua bat; goi API truc tiep voi model
chua san sang se bao loi classify khi co box, khong tu thay model.

## Luong suy luan

1. Kiem tra file, decode RGB khong xoay EXIF: toi da 16 MiB, 24 MP.
2. MDv5a CPU 1280, animal score >= nguong detector; person/vehicle chi dem rieng.
3. Moi box doi sang crop integer `round/clip`, padding 0, moi canh >= 8 px.
4. Kiem tra SHA/size checkpoint, class map va preprocessing. Nap model `eval`
   voi `weights_only=True`, khong tai ImageNet weights khi suy luan.
5. Crop duoc xu ly theo batch toi da 8, `torch.inference_mode`, softmax tren
   du 8 lop. Sap xep giam dan va lay 3 lop, khong renormalize top 3.
6. Top 1 duoi nguong review o bat ky box nao thi `needs_review`. Nguong mac
   dinh 0.70 chua duoc toi uu; `ok` chi la dat nguong demo, khong xac nhan loai.

Toi da 64 animal box/request. Box nho/hong, vuot gioi han, checkpoint sai,
logit khong huu han hoac loi giua cac batch: tra loi classify, detections rong.
Khong bo box am tham. Khong co box: `no_detection`, khong goi classifier;
khong dong nghia anh trong hoac checkpoint da duoc kiem tra thanh cong.

## Cache va thay checkpoint

`src/demo/classifier.py` dung mot cache chung cho server; khoa bao ve ca nap
lan dau va forward. Key gom model ID, registry entry va class map, nen doi
path/hash/preprocessing se khong dung nham model cu. SHA/size duoc kiem tra
lai moi request classify, ke ca khi RAM cache hit. File bi thay ma registry
khong doi se bi tu choi, khong van am tham chay model cu.

Toi da 2 classifier trong RAM; model it dung nhat bi loai. MegaDetector co
adapter/cache rieng. Cache mat khi restart server; lan dau load lai tu dia.
Cache khong luu anh hoac ket qua du doan cua nguoi dung. Registry duoc doc lai
moi request; refresh trang de cap nhat menu khi bat B1/B2. Chi sua registry
tu file local, khong co API cho upload checkpoint/chon duong dan tuy y.

## Hop dong checkpoint B1/B2

Sua `configs/demo_classifiers.json`, hoac tao registry moi va truyen
`scripts/run_demo.py --classifiers configs/demo_classifiers_local.json`.
Moi entry phai co `enabled`, checkpoint nam duoi `outputs/`, SHA-256 chinh
xac, `checkpoint_bytes`, `training_input`, va `preprocessing` du 5 truong:
resize_mode, resize_size, image_size, mean, std.

Chung: PyTorch dictionary an toan cho `weights_only=True`, `model_state_dict`,
`num_classes=8`, `idx_to_class` va `class_to_idx` khop chinh xac class map TV1.
Khong suy doan thu tu lop tu ten thu muc/file. SHA va kich thuoc do thanh vien
giao checkpoint cung cap, phai doi chieu truoc khi bat model.

- **B0:** `model_name=resnet18`, `freeze_backbone=true`; mapping/config goc cua
  checkpoint TV2. Preprocessing khop validation config: Resize(256),
  CenterCrop(224), ImageNet mean/std. SHA da pin:
  `d1ba497f1c21a5a259a99f55335d47288ee047f7f1c6236ec8b8dfa439649680`.
- **B1:** nhu format TV2 hien tai: `kind=OFFICIAL`, `model_name=resnet18`,
  `freeze_backbone=false`. Nhanh adapter dung linear fc va validation config
  trong checkpoint; moi gia tri phai khop registry, khong doi transform ngam.
- **B2:** format TV3 ResNet18 wrapper (`backbone.*`, `classifier.1.weight/bias`),
  `config.model.backbone=resnet18`, `kind=OFFICIAL`, mapping hai chieu va
  `inference_preprocessing` khop registry. Adapter doi key sang ResNet18 fc;
  Dropout la identity o eval. Chua ho tro ResNet50/MobileNet o adapter demo.

Checkpoint B2 draft hien tai chua luu mapping va preprocessing suy luan day
du. TV3 phai ban giao nhung metadata nay tu run that, kem SHA. Khong tu gan
`OFFICIAL` cho checkpoint smoke, khong lay class map bat ky de lap cho trong.
Neu format mo hinh khac, them adapter + regression truoc khi bat registry.
Bat entry khong phai bang chung model da duoc nghiem thu khoa hoc.

## Hop dong JSON/API

`POST /api/analyze` nhan anh base64 hoac sample_id, mode, detector threshold,
classifier (`B0`, `B1`, `B2`, `none`) va review_threshold. Khong gui classifier
thi giu API detector-only cu. Upload va inference van local-only.

Voi classifier, response gom `result`, `preview`, `classification`. Truong
`classification` la envelope duoc xuat thanh JSON:

```json
{
  "schema_version": "classifier-demo-1.0",
  "result": {"schema_version": "1.0.0"},
  "provenance": {"score_kind": "softmax_class_score", "scores_calibrated": false}
}
```

Day chi la khung rut gon, khong phai JSON mau day du. `result` giu hop dong
`inference_result.schema.json` v1; envelope duoc validate boi schema moi
`classifier_demo.schema.json` va validator ngu nghia cu. Provenance ghi model
SHA, transform, nguon input huan luyen/suy luan, cache hit/load count, detector
version/hash va canh bao. Dung `src.demo.inference.validate_envelope` de kiem
tra file export, khong truyen nguyen envelope vao validator v1 cu.

## Gioi han khoa hoc

- Diem detector va diem classifier la hai dai luong khac nhau. Diem softmax
  chi de xep hang cac lop da hoc; chua hieu chinh, khong phat hien open-set.
- B0 va B1 hoc toan anh; dung detector crop la thay doi phan bo. Ket qua demo
  khong phai metric cua B2, khong thay cho so sanh B1/B2 tren comparison_v1.
- Moi box trong app co the la loai khac nhau. Khong lay trung binh tat ca box
  trong anh thanh mot loai; quy tac image-level aggregation cua benchmark
  comparison_v1 la mot luong danh gia rieng tren anh dong nhan da khoa.
- MDv5a da dung SWG khi huan luyen. Chia location khong loai bo training overlap
  cua detector. Chua hieu chinh nguong, chua danh gia end-to-end doc lap.

## Kiem tra va tiep tuc sau gian doan

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p test_tv4_classifier.py -v
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/verify_tv4_classifier.py
node scripts/qa_tv4_w3.cjs
```

Browser QA can Playwright va Edge; dung `PLAYWRIGHT_MODULE`, `PLAYWRIGHT_CHANNEL`,
`DEMO_URL` de doi runtime/browser/URL. Phai mo server truoc. Script smoke thuc
chi dung anh train va ghi vao outputs, khong ghi de experiment B0 cua TV2.

Doc `docs/progress_tv4_w3.md` va git status truoc khi tiep tuc. Setup B0 dung
lock OS, file `.part`, xac minh checksum truoc khi cong bo va progress atomic
o `outputs/tv4/classifier_setup/progress.json`. Chay lai se tai su dung file
hoan tat; file tai dang do duoc tai lai tu dau, khong resume theo byte.
Smoke co checkpoint atomic o `outputs/tv4/w3/smoke.json`; chay lai de xac minh
cache moi, khong train. Khong xoa cache/weights khi quota hoi thoai het.

## Nguoi kiem tra TV2

- [ ] Pull dung branch, setup/reuse B0, run server va thu upload.
- [ ] Chay MD+B0 hai lan; top 3 giong nhau, lan sau cache hit/load count 1.
- [ ] Thu gia lap nhieu box, empty, read/detect/classify errors, JSON export.
- [ ] Doi classifier/threshold thi ket qua cu bi xoa; B1/B2 chua ban giao bi khoa.
- [ ] Doc canh bao softmax, SWG va B0 crop; kiem tra mobile.
- [ ] Chi bat B1/B2 sau khi xac minh checkpoint, mapping, transform va SHA.

Bang chung nguoi trien khai: `reports/tv4_w3/REPORT.md`. Checklist nay khong
thay cho xac nhan nghiem thu doc lap cua TV2.
