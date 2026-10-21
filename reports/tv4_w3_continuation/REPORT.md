# TV4 W3 - Hoan tat ket noi B1/B2

Kiem dinh thuc te 20/10/2026; hoan thien ban giao 21/10/2026.
Branch: `feat/demo`. Khong merge main, khong train lai, khong chay test inference.

## Ket luan

- TV1 W3 dat: comparison_v1 giu 4000 anh; B1/B2 cung parent ID va nhan;
  khong doi split, khong trung ID/chuoi/dia diem qua cac split.
- TV3 W3 dat de ban giao B2: checkpoint thuc khop SHA/size, 93/93 tests
  tren commit `7cc87e8`, validation doc lap khop cac chi so phan loai.
- TV4 W3 dat ve trien khai: chay duoc B0/B1/B2, nhieu box, top 3, cache,
  JSON va canh bao diem chua hieu chinh. Can TV2 review doc lap theo checklist.
- B2 duoc khoa theo quyet dinh nguoi dung; B3 van thu nghiem trong W4.
  Kiem ke chat luong test khac voi danh gia du doan tren test.

## Checkpoint va kiem dinh

| Model | Bytes | SHA-256 |
| --- | ---: | --- |
| B1 | 44815625 | `5a44c6a82aba7458dcd7d436ba88d76dfeafdae5aa647b7100ccd5b1a8d1328c` |
| B2 | 89548866 | `8787ffaf1e56e6316a137e2f94f81b0a21608910bb3198fe6724c129242127e5` |

B2 `b2_run01`, best epoch 21, ResNet18, 8 lop. Nguon local TV3:
`outputs/tv3/best_model.pt`; ban da cai: `outputs/tv4/models/b2_approved.pth`.
Khong sua checkpoint; chi chuyen metadata/state-dict trong RAM. Preprocessing
Resize256 -> CenterCrop224 -> ImageNet normalize khop native TV3.

Fresh process CPU kiem tra SHA 3400 anh train/val, frozen manifests/provenance,
600 anh val / 680 crop. Tensor preprocessing khop, max logit delta voi wrapper
native = 0 tren mau doi chieu. Khong mo test trong kiem dinh nay.

| Validation | Accuracy | Macro F1 | Don vi |
| --- | ---: | ---: | --- |
| B2 image-level | 0.7467 | 0.7455 | 600 anh, mean vector softmax cac crop cung anh |
| B2 crop-level | 0.7294 | 0.7254 | 680 crop |

Ma tran nham lan, per-class, precision/recall/accuracy/F1 khop **chinh xac**
bao cao TV3 va checkpoint. Loss tai lap 0.8177, TV3 0.8178. Lan so sanh
dict tuyet doi dau tien FAIL; giu lai `b2_validation_exact_comparison.json`.
Validator cho phep rieng loss lech toi da 0.0001 (mot don vi lam tron 4 so),
khong noi long chi so phan loai. Nguyen nhan lech loss giua runtime chua duoc
chung minh; khong khang dinh loss trung tuyet doi. Xem `b2_validation.json`.

## Bang chung demo

- `b1_smoke.json`, `b2_smoke.json`: MDv5a that + classifier that, mot anh train,
  cold/warm top 3 trung nhau, lan sau khong nap lai model.
- `browser_verification.json`: B0/B1/B2, JSON export, cache, mock nhieu box,
  anh loi/khong phat hien, 1440x1100 / 390x844 / 320x740, khong browser error.
- JSON export B0/B1/B2 da qua schema va semantic validator.
- Kiem tra lai ngay 21/10: `browser_verification_2026-10-21.json`, ca ba
  model va ba viewport PASS; JSON export lai van PASS. Full suite **199/199**
  PASS (20.543s), xem `tests.txt`.
- Screenshot goc: `outputs/tv4/w3_continuation/browser/` (local, khong phai anh test).
- So sanh metadata TV1: `comparison_metadata.json`.

## Gioi han va viec tiep theo

- Day khong phai diem end-to-end: benchmark B2 dung ground-truth crop;
  demo dung detector crop. Nhieu box that duoc kiem thu logic bang fixture,
  chua phai nghiem thu do chinh xac tren bo anh nhieu ca the ngoai thuc dia.
- MDv5a da dung SWG khi huan luyen; khong goi SWG la test detector doc lap.
  B0/B1 hoc toan anh, demo crop co distribution shift. Softmax chua hieu chinh.
- TV3 config cu de preflight_hash_check=false; luot doc lap nay da bu hash
  kiem tra train/val. Run B3 moi nen bat preflight hash check ngay tu dau.
- B1/B2 co cung anh va transform, nhung grouped batch B2 gioi han theo crop,
  khong phai cung so parent/update; can mo ta khac biet ngan sach tinh toan.
- TV3 nen sua macro precision B1 trong bang so sanh: bao cao B1 goc
  0.5748610369, khong phai 0.5688. Khong anh huong trong so B2.
- TV2 review doc lap giao dien; TV3 cung cap kenh tai checkpoint ngoai Git
  cho ca nhom. B3 chi train/val; khoa lua chon truoc danh gia test so sanh.

Lenh setup/kiem tra va huong dan tiep tuc: `docs/handoff_tv4_w3.md`,
`docs/progress_tv4_w3_continuation.md`. Khong xoa outputs khi het quota.
