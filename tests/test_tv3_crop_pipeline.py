"""Tests cho TV3 Tuần 2: crop pipeline và CropDataset.

Chạy:
    python -m unittest tests.test_tv3_crop_pipeline -v

Không tải ảnh từ Internet, không dùng ảnh test, chỉ dùng dữ liệu tổng hợp.
"""

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# PIL và torchvision cần thiết cho DataLoader tests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


# ─────────────────────────── helpers ───────────────────────────────

def make_fake_jpeg(w: int = 120, h: int = 80) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color=(100, 150, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def make_record(image_id="img001", label="sambar", split="train",
                width=120, height=80, boxes=None, url="http://example.com/a.jpg"):
    if boxes is None:
        boxes = [{"annotation_id": "ann1", "label": label, "bbox_xywh": [10, 5, 50, 40]}]
    return {
        "image_id": image_id, "label": label, "split": split,
        "width": width, "height": height, "boxes": boxes, "url": url,
    }


# ─────────────────────────── clamp_box ─────────────────────────────

class ClampBoxTests(unittest.TestCase):
    def setUp(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from crop_dataset import clamp_box
        self.clamp = clamp_box

    def test_normal_box(self):
        self.assertEqual(self.clamp(10, 5, 50, 40, 120, 80), (10, 5, 60, 45))

    def test_box_clamped_at_boundary(self):
        # box tràn một chút ở cạnh phải/dưới → clamp về kích thước ảnh
        result = self.clamp(110, 70, 20, 20, 120, 80)
        self.assertEqual(result, (110, 70, 120, 80))

    def test_negative_x_clamped_to_zero(self):
        result = self.clamp(-5, 0, 30, 20, 120, 80)
        self.assertEqual(result, (0, 0, 25, 20))

    def test_box_completely_outside_returns_none(self):
        self.assertIsNone(self.clamp(200, 200, 10, 10, 120, 80))

    def test_zero_width_after_clamp_returns_none(self):
        self.assertIsNone(self.clamp(119, 0, 2, 80, 120, 80))  # 1px rộng < MIN_SIDE

    def test_too_small_crop_returns_none(self):
        # box 4×4 < MIN_SIDE=8
        self.assertIsNone(self.clamp(10, 10, 4, 4, 120, 80))

    def test_one_pixel_box_returns_none(self):
        self.assertIsNone(self.clamp(10, 10, 1, 1, 120, 80))


# ─────────────────────────── process_record ────────────────────────

class ProcessRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=ROOT / "data"))
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from crop_dataset import process_record
        self.process = process_record
        
        # Patch requests.get using unittest.mock to properly mock fetch_image
        import unittest.mock as mock
        self.patcher = mock.patch("scripts.crop_dataset.requests.get")
        self.mock_get = self.patcher.start()
        
        # Setup mock response
        mock_resp = mock.Mock()
        mock_resp.content = make_fake_jpeg()
        mock_resp.raise_for_status = mock.Mock()
        self.mock_get.return_value = mock_resp

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fetch_fail(self):
        self.mock_get.side_effect = ConnectionError("simulated network error")

    # ── happy path ──────────────────────────────────────────────────

    def test_normal_record_produces_one_crop_row(self):
        class_map = {"sambar": 0, "eurasian_wild_pig": 1}
        rows, errors = self.process(make_record(), self.tmp, "train", class_map)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["label"], "sambar")
        self.assertEqual(rows[0]["split"], "train")
        self.assertEqual(rows[0]["class_id"], 0)
        self.assertIn("image_id", rows[0])
        self.assertIn("annotation_id", rows[0])
        self.assertIn("file_path", rows[0])
        self.assertIn("sha256", rows[0])
        self.assertTrue(Path(ROOT / rows[0]["file_path"]).exists())
        self.assertEqual(errors, [])

    def test_split_is_inherited_from_manifest_not_box(self):
        class_map = {"sambar": 0}
        rows, errors = self.process(make_record(split="val"), self.tmp, "val", class_map)
        self.assertEqual(rows[0]["split"], "val")

    def test_multi_animal_image_uses_box_label_not_image_label(self):
        """Ảnh có nhiều loài: mỗi box dùng nhãn riêng của box đó."""
        boxes = [
            {"annotation_id": "a1", "label": "sambar", "bbox_xywh": [5, 5, 40, 30]},
            {"annotation_id": "a2", "label": "eurasian_wild_pig", "bbox_xywh": [60, 5, 40, 30]},
        ]
        record = make_record(label="sambar", boxes=boxes)  # label ảnh = sambar
        class_map = {"sambar": 0, "eurasian_wild_pig": 1}
        rows, errors = self.process(record, self.tmp, "train", class_map)
        labels = {r["label"] for r in rows}
        self.assertEqual(len(rows), 2)
        self.assertIn("sambar", labels)
        self.assertIn("eurasian_wild_pig", labels)

    # ── error handling ───────────────────────────────────────────────

    def test_download_failure_logged_not_raised(self):
        self._fetch_fail()
        class_map = {"sambar": 0}
        rows, errors = self.process(make_record(), self.tmp, "train", class_map)
        self.assertEqual(rows, [])
        self.assertEqual(errors[0]["reason"], "download_failed")

    def test_record_without_boxes_is_skipped(self):
        class_map = {"sambar": 0}
        rows, errors = self.process(make_record(boxes=[]), self.tmp, "train", class_map)
        self.assertEqual(rows, [])
        self.assertEqual(errors[0]["reason"], "no_boxes")

    def test_box_without_label_is_skipped(self):
        boxes = [{"annotation_id": "a1", "label": "", "bbox_xywh": [10, 5, 50, 40]}]
        class_map = {"sambar": 0}
        rows, errors = self.process(make_record(boxes=boxes), self.tmp, "train", class_map)
        self.assertEqual(rows, [])
        self.assertEqual(errors[0]["reason"], "missing_box_label")

    def test_invalid_geometry_box_is_skipped(self):
        # tọa độ nằm hoàn toàn ngoài ảnh 120×80
        boxes = [{"annotation_id": "a1", "label": "sambar", "bbox_xywh": [200, 200, 10, 10]}]
        class_map = {"sambar": 0}
        rows, errors = self.process(make_record(boxes=boxes), self.tmp, "train", class_map)
        self.assertEqual(rows, [])
        self.assertEqual(errors[0]["reason"], "invalid_box_geometry")

    def test_one_bad_box_does_not_block_other_good_boxes(self):
        boxes = [
            {"annotation_id": "a_bad",  "label": "sambar", "bbox_xywh": [300, 300, 10, 10]},
            {"annotation_id": "a_good", "label": "sambar", "bbox_xywh": [5, 5, 40, 30]},
        ]
        class_map = {"sambar": 0}
        rows, errors = self.process(make_record(boxes=boxes), self.tmp, "train", class_map)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["annotation_id"], "a_bad")

    def test_decode_failure_logged(self):
        import unittest.mock as mock
        mock_resp = mock.Mock()
        mock_resp.content = b"not an image"
        mock_resp.raise_for_status = mock.Mock()
        self.mock_get.return_value = mock_resp
        class_map = {"sambar": 0}
        rows, errors = self.process(make_record(), self.tmp, "train", class_map)
        self.assertEqual(rows, [])
        self.assertEqual(errors[0]["reason"], "decode_failed")


# ─────────────────────────── CropDataset ───────────────────────────

class CropDatasetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir=ROOT / "data"))
        self.class_map_path = self.tmp / "class_map.json"
        self.class_map_path.write_text(
            json.dumps({"0": "sambar", "1": "eurasian_wild_pig"}), encoding="utf-8"
        )
        # tạo 3 crop giả
        self.crops_dir = self.tmp / "crops"
        species_dir = self.crops_dir / "train" / "sambar"
        species_dir.mkdir(parents=True)
        for i in range(3):
            path = species_dir / f"img00{i}_ann{i}.jpg"
            Image.new("RGB", (60, 50)).save(path)

        # manifest
        rows = [
            {
                "crop_id": f"img00{i}_ann{i}", "image_id": f"img00{i}",
                "annotation_id": f"ann{i}", "split": "train",
                "label": "sambar", "class_id": 0,
                "file_path": (species_dir / f"img00{i}_ann{i}.jpg").relative_to(ROOT).as_posix(),
                "source_url": "http://x", "bbox_xywh_original": [5,5,50,40],
                "bbox_xyxy_clamped": [5,5,55,45], "crop_w": 50, "crop_h": 40,
                "image_w": 120, "image_h": 80, "sha256": "abc",
            }
            for i in range(3)
        ]
        manifest = self.crops_dir / "crop_manifest_train.jsonl"
        with open(manifest, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_dataset_length(self):
        from src.data.crop_dataset import CropDataset
        ds = CropDataset("train", crop_dir=self.crops_dir,
                         class_map_path=self.class_map_path, root=ROOT)
        self.assertEqual(len(ds), 3)

    def test_getitem_returns_tensor_and_int(self):
        import torch
        from src.data.crop_dataset import CropDataset
        ds = CropDataset("train", crop_dir=self.crops_dir,
                         class_map_path=self.class_map_path, root=ROOT)
        img_tensor, label = ds[0]
        self.assertIsInstance(img_tensor, torch.Tensor)
        self.assertEqual(img_tensor.shape[0], 3)     # RGB channels
        self.assertIsInstance(label, int)
        self.assertEqual(label, 0)                   # sambar → class 0

    def test_class_counts(self):
        from src.data.crop_dataset import CropDataset
        ds = CropDataset("train", crop_dir=self.crops_dir,
                         class_map_path=self.class_map_path, root=ROOT)
        counts = ds.class_counts()
        self.assertEqual(counts["sambar"], 3)

    def test_missing_manifest_raises_filnotfound(self):
        from src.data.crop_dataset import CropDataset
        with self.assertRaises(FileNotFoundError):
            CropDataset("val", crop_dir=self.crops_dir,
                        class_map_path=self.class_map_path, root=ROOT)


if __name__ == "__main__":
    unittest.main()
