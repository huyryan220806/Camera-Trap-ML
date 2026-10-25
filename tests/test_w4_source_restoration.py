"""Checksum-bound source restoration on synthetic JPEG bytes; no external network."""
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from scripts import prepare_w4_test_sources as restore
from scripts.download_subset import BASE


class Response:
    status_code = 200
    def __init__(self, content):
        self.content = content
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def iter_content(self, size):
        yield self.content


class SourceRestorationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(restore, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        memory = io.BytesIO()
        Image.new("RGB", (20, 20), (10, 20, 30)).save(memory, format="JPEG")
        self.content = memory.getvalue()
        with Image.open(io.BytesIO(self.content)) as image:
            pixel_sha = hashlib.sha256(b"RGB:20:20:" + image.convert("RGB").tobytes()).hexdigest()
        self.row = {"image_id": "synthetic", "file_name": "public/fixture.jpg", "url": BASE + "public/fixture.jpg",
                    "width": 20, "height": 20, "boxes": [], "split": "test", "label": "synthetic_species",
                    "quality": {"local_path": "data/images/swg_pilot_v2/public/fixture.jpg", "bytes": len(self.content),
                                "sha256": hashlib.sha256(self.content).hexdigest(), "pixel_sha256": pixel_sha}}
        self.dest = self.root / self.row["quality"]["local_path"]

    def test_restore_exact_bytes_preserves_label_and_split(self):
        before = copy.deepcopy(self.row)
        with patch("requests.get", return_value=Response(self.content)):
            result = restore.restore_one(self.row)
        self.assertEqual(result["status"], "restored_verified")
        self.assertEqual(self.dest.read_bytes(), self.content)
        self.assertEqual(self.row, before)

    def test_existing_correct_image_never_downloaded_or_replaced(self):
        self.dest.parent.mkdir(parents=True)
        self.dest.write_bytes(self.content)
        with patch("requests.get", side_effect=AssertionError("network should not be called")):
            self.assertEqual(restore.restore_one(self.row)["status"], "verified_existing")

    def test_existing_changed_image_preserved_and_rejected(self):
        self.dest.parent.mkdir(parents=True)
        self.dest.write_bytes(b"preserve these bytes")
        with self.assertRaisesRegex(ValueError, "preserve it"):
            restore.restore_one(self.row)
        self.assertEqual(self.dest.read_bytes(), b"preserve these bytes")

    def test_downloaded_wrong_sha_never_published(self):
        self.row["quality"]["sha256"] = "0" * 64
        with patch("requests.get", return_value=Response(self.content)):
            self.assertEqual(restore.restore_one(self.row)["status"], "FAILED")
        self.assertFalse(self.dest.exists())

    def test_downloaded_wrong_pixel_hash_never_published(self):
        self.row["quality"]["pixel_sha256"] = "0" * 64
        with patch("requests.get", return_value=Response(self.content)):
            self.assertEqual(restore.restore_one(self.row)["status"], "FAILED")
        self.assertFalse(self.dest.exists())

    def test_manifest_path_escape_rejected(self):
        self.row["file_name"] = "../outside.jpg"
        with self.assertRaises(ValueError):
            restore.restore_one(self.row)


if __name__ == "__main__":
    unittest.main()
