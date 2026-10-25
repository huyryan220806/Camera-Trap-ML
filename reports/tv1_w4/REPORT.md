# TV1 W4 - Kiem ke test va phan tich loi du lieu

Ngay 21/10/2026. Branch `feat/metadata-split`. Dataset `comparison_v1`.

## Pham vi va khoa mo hinh

Nguoi dung da yeu cau khoa **B2 b2_run01**, best epoch 21; B3 se lam trong
tuan 4. Ho so khoa: `configs/model_locks/b2_w3.json`, gan SHA checkpoint,
provenance du lieu va bang chung validation doc lap truoc khi kiem ke test.
Validation B2: 600 anh/680 crop, image macro-F1 0.7455. Loss lech 0.0001
duoc cong khai trong `b2_validation.json`; khong phai metric test.

Cong viec nay **chi kiem ke va kiem tra chat luong du lieu**, khong nap model,
khong tinh diem test, khong chon vi du bang du doan sai. B3 chi duoc train va
lua chon tren train/val; khong dung cac vi du test nay de sua augmentation,
nguong, crop policy hay sieu tham so. Can khoa quyet dinh B2/B3 rieng truoc
khi danh gia test so sanh cuoi cung.

## Phan bo test

| Lop | Anh | Chuoi | Dia diem | Crop | Noi dung RGB khac nhau |
| --- | ---: | ---: | ---: | ---: | ---: |
| large_antlered_muntjac | 75 | 70 | 28 | 77 | 75 |
| annamite_striped_rabbit | 75 | 50 | 11 | 75 | 75 |
| sambar | 75 | 69 | 26 | 92 | 75 |
| chinese_serow | 75 | 61 | 24 | 78 | 75 |
| common_palm_civet | 75 | 62 | 26 | 75 | 74 |
| masked_palm_civet | 75 | 55 | 33 | 75 | 75 |
| silver_pheasant | 75 | 56 | 17 | 102 | 75 |
| eurasian_wild_pig | 75 | 72 | 27 | 106 | 75 |
| **Tong duy nhat** | **600** | **495** | **98** | **680** | **599** |

Khong cong so dia diem cac lop de suy ra tong, vi cung dia diem co nhieu lop.
Thong ke duoc tinh lai tu manifest test/B2 va doi chieu summary da khoa.

## Chat luong va bo vi du

- **600/600 anh** ton tai, decode day du, dung kich thuoc, SHA file va SHA
  pixel RGB. Khong co file thieu/hong/thay doi trong lan kiem tra nay.
- Khong co giao ID, ten file, chuoi, dia diem giua train/val/test. B1/B2
  cung parent IDs, nhan va split. Snapshot 4000 anh khong doi mot byte.
- **1 cap trung RGB (2 anh)**: common_palm_civet, cung test va loc_0851.
  ID `d86f91b0-8c29-11eb-8c2e-000d3a74c7de` va
  `d86f91b6-8c29-11eb-94af-000d3a74c7de`. Day la trung noi dung da duoc ghi
  nhan tu W3, khong phai ro ri qua split. Giu nguyen ca hai, khong bo sau
  khi khoa de lam diem dep hon; neu bao cao metric sau nay, neu ro han che nay.
- **70 anh** co it nhat mot box nho hon 1% dien tich anh; **171 anh** co box
  sat mep (<=1 px). Day la quy tac gan co metadata, **khong phai 241 anh sai
  nhan**; cac nhom co the giao nhau. Khong du bang chung de ket luan sai loai.
- **57 anh** co nhieu box. Day la tinh huong can ho tro, khong tu no la loi.
- Bo vi du gom **12 anh**: cap trung va toi da 4 anh/co dieu kien, chon ID
  tang dan co dinh, khong chon theo diem mo hinh. Xem `examples.json` va
  `examples.md`. Ban HTML local hien anh goc va box; khong tao anh crop moi.

Moi vi du co ID, lop, chuoi/dia diem, file, SHA, box, ly do va hanh dong
`retain_unchanged`. **0 sua nhan, 0 doi split, 0 loai mau**. Chua thuc hien
tham dinh loai bang chuyen gia; khong goi co du lieu la nhan sai da xac nhan.

## Gioi han lop it mau

Pilot nay duoc can bang 75 anh/lop, khong phan anh tan suat loai trong tu
nhien. Moi loi them lam recall lop doi khoang 1/75 = **1.33 diem phan tram**.
75 anh khong tuong duong 75 quan sat doc lap: annamite_striped_rabbit chi
co 50 chuoi/11 dia diem, silver_pheasant 56 chuoi/17 dia diem. Ket qua tren
mot vai boi canh camera co the chi phoi diem lop. masked_palm_civet co 55
chuoi du co 75 anh. common_palm_civet co 74 noi dung RGB cho 75 dong.

Khi bao cao test sau nay, luon kem support theo lop/chuoi; khong ket luan
khac biet nho la uu the chac chan. Neu tinh khoang tin cay, can xet cum
chuoi/dia diem, khong gia dinh moi crop hay moi anh deu doc lap. Day la
closed-set 8 lop, khong suy rong cho tat ca dong vat quy hiem Truong Son.
Nhan goc cap chuoi va ground-truth box khong thay cho tham dinh loai tung
ca the. Hash RGB chi tim trung chinh xac, chua quet near-duplicate.

## Kiem thu va tai lap

- `inventory.json`: lan decode dau, 600 valid, reused_decodes=0.
- `resume_inventory.json`: chay lai, 600 valid, reused_decodes=600; van bam
  lai tat ca file truoc khi tai su dung ket qua decode.
- `quality_checks.json`: ket qua tung anh, checksum va thoi diem decode.
- Bo test nhanh bao phu count theo chuoi, duplicate, box loi, lock/proof,
  duong dan ngoai data, thay file/mat file va KeyboardInterrupt/continue.
- Full suite **178/178 PASS** (17.637s), `tests.txt`. Gallery QA nap du 12
  anh, box nam dung trong anh, khong tran ngang tai 1280x960 va 390x844;
  xem `gallery_verification.json`. Da xem screenshot cua ca hai kich thuoc.
- Lenh va vi tri state: `docs/handoff_tv1_w4.md`.

**Hoan thanh pham vi TV1 W4 ve du lieu.** Khong tuyen bo da hoan thanh danh
gia model tren test hay review nhan bang chuyen gia. Khong thay version
`comparison_v1`, khong gop main trong cong viec nay.
