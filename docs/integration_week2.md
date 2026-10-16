# Tich hop tuan 2 - 16/10/2026

## Pham vi

Theo yeu cau cua chu repo: moi thanh vien dung mot branch co dinh, dua phan
tuan 2 da review vao main va xoa cac branch codex/* cu. Khong force-push,
khong sua split, khong thay byte manifest va khong dua code tuan 3 chua dat
vao ban tich hop tuan 2.

| Thanh vien | Branch co dinh | Commit tuan 2 duoc chon |
| --- | --- | --- |
| TV1 | feat/metadata-split | b9a92b9 |
| TV2 | feat/baseline | 8988d28 |
| TV3 | feat/crop-classifier | 2c3c992 |
| TV4 | feat/demo | f61ca6d (gom c69283a va nen TV1) |

Main truoc tich hop: `4e7ad47`. Merge TV2: `ad4faa3`; merge TV3: `4cb4778`.
Chi co mot conflict add/add tai `src/data/__init__.py`: hop nhat docstring
cho reader toan anh va crop; khong sua logic cua hai thanh vien.

TV2 `8c0039e` va TV3 `d08eba7` la phan tuan 3, van duoc giu tren branch
thanh vien, khong nam trong main tuan 2. Khong reset branch TV2/TV3 ve commit
cu. TV1 comparison_v1 tuan 3 van la cong viec local, khong thuoc lan merge nay.

## Kiem tra sau merge

- Toan bo 150 unittest PASS, 0 failure/error/skip, CPU, Python 3.12.10,
  torch 2.8.0+cpu, 21.812 giay; commit code `4cb4778`.
- `scripts/check_environment.py`: PASS cac dependency chung da pin.
- `scripts/validate_results.py`: PASS ca 6 JSON ket qua mau.
- `scripts/validate_manifest_v2.py --metadata-only`: PASS 4.000 anh,
  train/val/test = 2.800/600/600, loai 0, doi split 0, SHA snapshot khop.
- Chi test tich hop va metadata; khong train lai B0, khong suy luan tren test,
  khong chay lai toan bo detector/GPU hay tai tao toan bo JPEG crop.
- Artifact B0 va crop v1_run03 duoc giu nguyen byte tu commit da review.
- CRLF trong manifest JSONL cua TV2 duoc giu nguyen de bao toan checksum;
  khong format lai de xoa canh bao whitespace. Ba dong whitespace trong
  reader crop va mot dong trang cuoi test TV3 la noi dung cu da review.

Bang chung: [reports/integration_w2_2026-10-16](../reports/integration_w2_2026-10-16/README.md).

## Cach lam viec tiep

Doc [CONTRIBUTING](../CONTRIBUTING.md). Fetch, vao branch co dinh cua minh,
cap nhat branch remote roi merge origin/main sau khi da cat giu thay doi.
Khong xoa bon branch thanh vien sau PR; khong tao branch moi theo tung tuan.

Nhanh codex/* chi duoc xoa sau khi commit cua chung da nam trong main va cac
branch TV1/TV4 co dinh da push thanh cong. Ban sao du phong cong viec TV1 W3
duoc giu trong Git stash local; anh, cache, weights va bao cao local khac
khong bi xoa hay dua vao commit tich hop.
