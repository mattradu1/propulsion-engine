import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gate_a_static as ga  # noqa: E402

CLIENT = {"businessName": "Test Roofing Ltd (DEMO)", "phone": "01632 960001", "phoneE164": "+441632960001",
          "reviews": [{"text": "Sam and the team were tidy and quick. Would use again for any roof work.",
                       "author": "Jane, St Albans"}],
          "claimsApproved": ["10-year written guarantee"]}
OTHER = [{"record_id": "REC-0102", "business": "Bright Spark Electrical", "phone": "01632 960123",
          "approved_senders": [{"email": "lee@brightspark.co.uk"}]}]

GOOD = """<!doctype html><html><head><meta name="robots" content="noindex, nofollow">
<style>.a{color:red}</style>
<script type="application/ld+json">{"@type":"RoofingContractor"}</script>
<script src="/assets/app.js" defer></script></head><body>
<div class="banner">Preview – not live</div><main><h1>Roofing in St Albans</h1>
<img src="/img/a.webp" alt="New slate roof" width="750" height="938">
<a href="tel:+441632960001">01632 960001</a>
<blockquote>Sam and the team were tidy and quick. …</blockquote>
<p>10-year written guarantee.</p></main></body></html>"""


def run(html, records=OTHER, client=CLIENT):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "index.html").write_text(html)
        return ga.check(tmp, client, records)


class GateA(unittest.TestCase):
    def test_good_page_passes(self):
        r = run(GOOD)
        self.assertEqual(r["result"], "PASS", r["fails"])
        self.assertEqual(r["ambers"], [])

    def test_missing_banner_and_noindex_fail(self):
        r = run(GOOD.replace("Preview – not live", "Welcome").replace("noindex, nofollow", "index"))
        self.assertEqual(r["result"], "FAIL")
        self.assertEqual(len(r["fails"]), 2)

    def test_pending_marker_is_amber(self):
        r = run(GOOD.replace("</main>", "<p>PENDING: confirm years in the trade</p></main>"))
        self.assertEqual(r["result"], "PASS")
        self.assertTrue(any("PENDING" in a for a in r["ambers"]))

    def test_placeholder_fails(self):
        self.assertEqual(run(GOOD.replace("Roofing in", "{business} in"))["result"], "FAIL")

    def test_inline_script_and_handlers_fail(self):
        r = run(GOOD.replace("</main>", "<script>alert(1)</script><img src=x alt='' width=1 height=1 onerror=x></main>"))
        self.assertTrue(any("inline script" in f for f in r["fails"]))
        self.assertTrue(any("event handler" in f for f in r["fails"]))

    def test_wrong_tel_fails(self):
        self.assertEqual(run(GOOD.replace('tel:+441632960001', 'tel:01632960999'))["result"], "FAIL")

    def test_review_not_word_for_word_fails(self):
        r = run(GOOD.replace("tidy and quick", "tidy, quick and cheap"))
        self.assertTrue(any("word for word" in f for f in r["fails"]))

    def test_banned_comparison_and_other_firms_fail(self):
        r = run(GOOD.replace("</main>", "<p>The best roofer around, unlike other cowboys.</p></main>"))
        self.assertTrue(any("comparison" in f for f in r["fails"]))
        self.assertTrue(any("other firms" in f for f in r["fails"]))

    def test_free_quotes_is_amber(self):
        r = run(GOOD.replace("</main>", "<p>Free quotes.</p></main>"))
        self.assertEqual(r["result"], "PASS")
        self.assertTrue(r["ambers"])

    def test_other_client_phone_hard_fails_name_only_amber(self):
        r = run(GOOD.replace("</main>", "<p>01632 960123</p></main>"))
        self.assertTrue(any("another client's phone" in f for f in r["fails"]))
        r2 = run(GOOD.replace("</main>", "<p>Bright Spark Electrical</p></main>"))
        self.assertEqual(r2["result"], "PASS")
        self.assertTrue(any("name-only" in a for a in r2["ambers"]))

    def test_image_without_alt_or_size_fails(self):
        r = run(GOOD.replace('alt="New slate roof" width="750" height="938"', ''))
        self.assertEqual(len([f for f in r["fails"] if "image" in f]), 2)


if __name__ == "__main__":
    unittest.main()
