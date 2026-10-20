import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))
import make_photo_fixtures as fx  # noqa: E402
import photo_score as ps  # noqa: E402


class PhotoScorer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.src = fx.build(Path(cls.tmp.name) / "in")
        cls.out = Path(cls.tmp.name) / "out"
        cls.res = ps.score_folder(cls.src, {}, cls.out, "REC-0101")
        cls.by = {p["file"]: p for p in cls.res["photos"]}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def label(self, name):
        return self.by[name]["label"]

    def test_sharp_camera_photos_usable(self):
        for i in range(2, 10):
            self.assertEqual(self.label(f"job_{i:02d}.jpg"), "usable")

    def test_blurred_rejected_or_low(self):
        self.assertIn(self.label("blurred.jpg"), ("reject", "low"))
        self.assertTrue(any("blurry" in r for r in self.by["blurred.jpg"]["reasons"]))

    def test_dark_flagged(self):
        self.assertNotEqual(self.label("dark.jpg"), "usable")
        self.assertTrue(any("dark" in r for r in self.by["dark.jpg"]["reasons"]))

    def test_near_duplicate_keeps_best(self):
        self.assertEqual(self.label("job_01.jpg"), "usable")
        self.assertEqual(self.label("job_01_copy.jpg"), "reject")
        self.assertTrue(any("near-duplicate of job_01.jpg" in r for r in self.by["job_01_copy.jpg"]["reasons"]))

    def test_screenshot_exact_phone_size(self):
        self.assertIn("screenshot", self.by["screenshot.png"]["flags"])
        self.assertEqual(self.label("screenshot.png"), "low")

    def test_screenshot_status_bar_heuristic(self):
        self.assertIn("screenshot", self.by["screenshot_odd_size.png"]["flags"])

    def test_whatsapp_pattern(self):
        self.assertIn("whatsapp", self.by["IMG-20261020-WA0001.jpg"]["flags"])
        self.assertEqual(self.label("IMG-20261020-WA0001.jpg"), "low")

    def test_no_camera_data_never_usable_or_hero(self):
        p = self.by["no_exif_photo.jpg"]
        self.assertEqual(p["label"], "low")
        self.assertIn("no_camera_data", p["flags"])
        self.assertFalse(p["hero_ok"])

    def test_signature_skipped_not_counted(self):
        self.assertEqual(self.label("signature.png"), "skipped")

    def test_svg_and_mismatched_type_quarantined(self):
        self.assertEqual(self.label("logo.svg"), "quarantine")
        self.assertEqual(self.label("fake_is_png.jpg"), "quarantine")

    def test_ai_tag_rejected(self):
        self.assertEqual(self.label("ai_render.png"), "reject")

    def test_tiny_rejected(self):
        self.assertEqual(self.label("tiny.jpg"), "reject")

    def test_location_stripped_on_export(self):
        self.assertTrue(self.by["job_01.jpg"]["location_data"])
        exported = Path(self.by["job_01.jpg"]["exported"])
        self.assertTrue(exported.name.startswith("REC-0101-"))
        self.assertEqual(len(Image.open(exported).getexif()), 0)
        self.assertTrue(self.by["job_01.jpg"]["export_location_stripped"])

    def test_heic(self):
        if not ps.HEIC_SUPPORT:
            self.skipTest("pillow-heif not installed")
        p = self.by["iphone.heic"]
        self.assertEqual(p["label"], "usable")
        self.assertTrue(p["location_data"])
        self.assertTrue(p["exported"].endswith(".jpg"))
        self.assertTrue(p["export_location_stripped"])

    def test_layout_needs_finished_job_label(self):
        self.assertEqual(self.res["summary"]["layout"], "lowPhoto")
        labels = {f"job_{i:02d}.jpg": ["finished_job"] for i in range(1, 10)}
        res = ps.score_folder(self.src, labels)
        self.assertEqual(res["summary"]["layout"], "standard")
        self.assertGreaterEqual(res["summary"]["labelled_usable"], 8)

    def test_few_photos_low_photo_layout(self):
        res = ps.layout([{"label": "usable", "file": "a"}] * 2, {})
        self.assertEqual(res["layout"], "lowPhoto")
        self.assertIn("fewer than 3", res["reason"])

    def test_output_is_json(self):
        json.dumps(self.res)


if __name__ == "__main__":
    unittest.main()
