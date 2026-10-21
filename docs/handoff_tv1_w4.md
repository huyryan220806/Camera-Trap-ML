# Ban giao TV1 tuan 4

Ngay 21/10/2026. Nguoi thuc hien: TV1. Branch co dinh: `feat/metadata-split`.

## File gui nhom

1. `reports/tv1_w4/REPORT.md`: phan bo 600 anh test / 495 chuoi / 98 dia diem,
   han che mau it va quy tac khong sua nhan/split de tang diem.
2. `configs/model_locks/b2_w3.json`: khoa B2 b2_run01, SHA checkpoint/du lieu;
   B3 van thu nghiem W4 tren train/val. Chua cho phep test model inference.
3. `reports/tv1_w4/inventory.json`, `resume_inventory.json`,
   `quality_checks.json`: kiem ke va log chat luong 600 anh.
4. `reports/tv1_w4/examples.md`, `examples.json`: 12 vi du du lieu, co ID,
   SHA, box, ly do va hanh dong giu nguyen. Khong phai danh sach model sai.

TV2/TV3 co the doc phan bo va chinh sach. Nguoi dang thu B3 khong dung bo
vi du test de chon augmentation, checkpoint, nguong hay quy tac crop.
Tinh sai/nham loai tren test chi lam sau khi khoa lua chon model cuoi.

## Chay lai va tiep tuc sau het quota

Tu goc checkout TV1, da cai dependencies cua du lieu (Pillow):

```powershell
.venv/Scripts/python.exe scripts/inventory_tv1_w4.py
.venv/Scripts/python.exe -m unittest tests.test_inventory_tv1_w4 -v
```

Neu anh nam o checkout khac, khong can sao chep 6.28 GB:

```powershell
D:/VLU/261/ML/CameraTrapML/.venv/Scripts/python.exe scripts/inventory_tv1_w4.py --data-root D:/VLU/261/ML/CameraTrapML --output D:/VLU/261/ML/CameraTrapML/outputs/tv1/w4
```

Command thu hai hien chay trong worktree
`C:/Users/loval/.codex/worktrees/review-tv2-week2/CameraTrapML`;
ten thu muc cu nhung branch hien la `feat/metadata-split`, khong phai TV2.
May khac dung duong dan Python/data-root cua may do.

Script tu choi neu lock/proof hoac frozen snapshot doi. Ket qua ghi vao
outputs, khong ghi vao data. `outputs/tv1/w4/state/<image_id>.json` luu
atomic sau tung anh, OS lock tranh hai tien trinh cung ghi. Chay lai cung
lenh de tiep tuc; bam file lai, chi bo qua decode khi checksum/metadata khop.
Khong xoa state khi quota chat het. Anh thieu/hong duoc ghi loi, lenh tra
exit code khac 0; khoi phuc dung anh goc, khong loai mau hay tu doi split.

Mo `outputs/tv1/w4/examples.local.html` trong trinh duyet de xem anh + box.
HTML tham chieu anh local, khong upload anh, khong can server. Tao lai tren
may moi de cap nhat duong dan. Khong dua HTML co duong dan may ca nhan vao Git.
Bo JSON/MD de ban giao nam trong reports; anh, weights, cache chi o local.

## Nghiem thu

- [x] Khoa B2 truoc kiem ke, gan SHA va bang chung validation.
- [x] Thong ke anh/chuoi/dia diem/crop tung lop, doi chieu frozen summary.
- [x] Kiem tra lai 600 anh; ghi nhan duplicate/candidate, khong sua nhan.
- [x] Bo vi du du lieu co truy vet va ghi ro dieu gi chua xac nhan.
- [x] Mo ta gioi han mau it va cum chuoi/dia diem.
- [x] Resume da thu that va co regression cho gian doan/thay/mat file.
- [ ] TV2/TV3 xac nhan doc ban giao; day la review dong doi, khong tu danh dau.
