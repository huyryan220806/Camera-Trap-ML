# Progress TV1 tuan 3

Yeu cau: khoa du lieu so sanh B1/B2, mot loai xac dinh, khong ro ri chuoi/dia
diem, thong ke giu/loai. Ngay 18/10/2026 chu repo yeu cau commit/push phan W3
len feat/metadata-split. Khong train hay merge vao main trong lan cong bo nay.

- Branch hien tai: `feat/metadata-split`, nen `468d81f` (main da tich hop W2).
  Nhanh cu `codex/tv1-week3-comparison-lock` tu `f61ca6d` da duoc xoa theo
  yeu cau ngay 16/10/2026; khong tao lai nhanh codex theo tuan.
- Truoc ngay 18/10, cong viec W3 van local/chua commit, da khoi phuc tren branch co dinh sau
  merge W2. 31 file untracked W3 doi chieu Git content hash voi ban backup dat.
  Backup stash `3c02f93da07edbc10769a069b4315a934e7e31a1` van duoc giu;
  da apply thanh cong, khong apply lan nua vao working tree hien tai.
- Nguon: pilot 4.000 anh da kiem dinh `data/processed/v2`, giu split/seed 42.
- Dich: `data/processed/comparison_v1`, khong ghi de v1/v2 tuan truoc.
- Policy: tat ca box cung loai; crop toi thieu 8 px theo TV3, round/clip giong
  pipeline da review; khong padding trong ban chuan nay. Mot box khong dat thi
  loai ca anh khoi B1 va B2. Thay policy phai tao version moi.
- Da trien khai builder, validator, resume checkpoint, 23 test va huong dan.
- Metadata: giu 4.000, loai 0; train 2.800/3.125 crop, val 600/680,
  test 600/680. Moi lop giu 350/75/75 anh. Khong doi split/seed.
- Test cuoi sau toi uu 4 luong: 114/114 toan repo PASS, 14.879 giay,
  gom 23 test comparison. Chi tiet `reports/tv1_w3/tests.json`.
- Da chay xong `scripts/freeze_comparison.py`, checkpoint/receipt o interim.
  Da chu dong dung tien trinh dau (sau hon 900 anh) de toi uu 4 luong, sau do
  resume thanh cong: lock cu duoc luu lich su, khong xoa cache/receipt.
- Snapshot da cong bo va kiem dinh doc lap day du 4.000 anh: PASS,
  `2026-10-14T09:48:10+00:00`; task_state da `complete`, tien trinh da ket thuc.
- 0 giao nhau image/file/sequence/location qua split, 3.280 chuoi, 658 dia diem.
  1 cap trung RGB cung test/cung nhan duoc giu va bao cao; 3.999 noi dung pixel.
- Doi chieu 4.485 toa do voi ham clamp_box cua TV3 commit `2c3c992`: deu khop;
  8 crop train (1/lop) decode trong RAM dat. `reports/tv1_w3/crop_compatibility.json`.
- Reader TV2 `8988d28`: doc du metadata B1, nap 8 anh train thanh tensor dat;
  bang chung `reports/tv1_w3/tv2_loader_compatibility.json`.
- Resume sau dung tien trinh da thu tren du lieu that; resume snapshot khong
  thay byte, tampering/failure/concurrency duoc test bang fixture.
- Bao cao sinh bang `scripts/report_comparison.py`: `reports/tv1_w3/REPORT.md`.
- Huong dan giao TV2/TV3: `docs/handoff_tv1_w3.md`; README da co lien ket.
- Hoan tat pham vi TV1 W3; ngay 18/10 dong goi de cong bo tren branch co dinh.
  Kiem tra truoc push: 173/173 unittest PASS (19.435 giay), metadata validator
  PASS 4000 anh, SHA snapshot khong doi. Khong sua code TV2/TV3.
- Chua tim near-duplicates, chua xac nhan loai bang chuyen gia. B2 ban giao crop
  specs, TV3 can adapter/cache moi; khong dung JPEG run v1_run03 thay the.
- Anh goc tai `data/images/swg_pilot_v2` duoc tai su dung, khong can copy/doi ten.
- Khong dung run TV3 `v1_run03` lam tap so sanh: do la danh sach anh khac pilot.

Tiep tuc sau quota: doc file nay, git status, `data/interim/comparison_v1/`
va `reports/tv1_w3/`. Khong xoa cache, source hay snapshot da khoa.
Lenh kiem tra/chay lai: `.venv/Scripts/python.exe scripts/freeze_comparison.py`.
Snapshot `comparison_v1` da co thi chi validate, khong build lai/ghi de.
SHA provenance: `d9fd5461e47be8b75cb214b988632405bcf3e629e258e35066115470b84b0a5f`.
