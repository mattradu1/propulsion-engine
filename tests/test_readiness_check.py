import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import readiness_check as rc  # noqa: E402

NOW = "2026-11-03T12:00:00+00:00"

FULL = {
    "record_id": "REC-0101", "business": "Test Roofing Ltd",
    "deposit_paid": True, "agreement_signed": True, "kickoff_done": True, "onboarding_form_complete": True,
    "i_or_we": "we", "words_you_use": "tidy, honest", "words_never_use": "cheap",
    "years_in_trade": "in the trade since 2009", "guarantee": "10-year written guarantee", "training": "NVQ Level 3",
    "insurance": "£5m public liability", "facts_confirmed_in_writing": True,
    "areas": ["St Albans", "Harpenden"], "areas_footer_line": "Covering St Albans and Harpenden.",
    "photos_not_to_show": "none",
    "legal_name": "Test Roofing Ltd", "company_number": "00000000", "registered_office": "1 Example Street, St Albans",
    "company_status": "Active", "ico_number": "ZA000000",
    "gbp_url": "https://www.google.com/maps/place/Test+Roofing/@51.75,-0.33",
    "enquiry_email": "sam@testroofing.co.uk", "funnel_url": "https://example.test/enquire",
    "registrar": "123-reg", "dns_call_booked": True,
    "preview_date": "Monday 9 November", "feedback_date": "Thursday 12 November", "launch_date": "Wednesday 18 November",
    "baseline": "unknown", "trading_names": ["Test Roofing"],
    "team_description": "Sam and two roofers who have worked together ten years",
    "what_makes_you_different": "We photograph every job and leave the site cleaner than we found it",
    "logo_file": True,
}
MANIFEST = {"files": [{"name": "a.jpg", "arrived_at": "2026-11-01T10:00:00+00:00"}],
            "photo_summary": {"usable": 10, "labelled_usable": 10, "no_camera_data": 0}}


def rec(**kw):
    r = copy.deepcopy(FULL)
    r.update(kw)
    return r


class Readiness(unittest.TestCase):
    def test_full_record_is_ready(self):
        res = rc.check(FULL, MANIFEST, NOW)
        self.assertEqual(res["status"], "Ready", res)
        self.assertEqual(res["build_status"], 3)

    def test_kickoff_not_done_never_ready(self):
        res = rc.check(rec(kickoff_done=False), MANIFEST, NOW)
        self.assertEqual(res["status"], "Missing Items")
        self.assertTrue(any("Kickoff not done" in m for m in res["missing_items"]))

    def test_written_kickoff_counts_when_returned_not_sent(self):
        r = rec(kickoff_done=False, kickoff_form_sent=True, kickoff_form_returned=False)
        res = rc.check(r, MANIFEST, NOW)
        self.assertTrue(any("not returned" in m for m in res["missing_items"]))
        r2 = rec(kickoff_done=False, kickoff_form_sent=True, kickoff_form_returned=True)
        self.assertEqual(rc.check(r2, MANIFEST, NOW)["status"], "Ready")

    def test_provisional_build_counts_as_kickoff(self):
        res = rc.check(rec(kickoff_done=False, provisional_build_approved=True), MANIFEST, NOW)
        self.assertEqual(res["status"], "Ready")

    def test_under_five_word_answer_is_missing(self):
        res = rc.check(rec(team_description="just me"), MANIFEST, NOW)
        self.assertEqual(res["status"], "Missing Items")
        self.assertIn("short_answer", res["unapproved_lines"])

    def test_under_five_words_after_reminder_3_builds_with_neutral_line(self):
        res = rc.check(rec(team_description="just me", reminder_3_sent=True), MANIFEST, NOW)
        self.assertEqual(res["status"], "Ready")
        self.assertTrue(any("neutral line" in n for n in res["notes"]))

    def test_pending_client_waiting_does_not_block_ready_but_blocks_gate_b(self):
        res = rc.check(rec(pending=[{"item": "guarantee length", "waiting_on": "client"}]), MANIFEST, NOW)
        self.assertEqual(res["status"], "Ready")
        self.assertTrue(any("guarantee length" in g for g in res["gate_b_blockers"]))

    def test_two_trading_names_need_signer_writing(self):
        r = rec(trading_names=["Test Roofing", "TR Roofs"])
        self.assertEqual(rc.check(r, MANIFEST, NOW)["status"], "Missing Items")
        r2 = rec(trading_names=["Test Roofing", "TR Roofs"], site_trading_name="Test Roofing",
                 site_trading_name_source="signer_written")
        self.assertEqual(rc.check(r2, MANIFEST, NOW)["status"], "Ready")
        r3 = rec(trading_names=["Test Roofing", "TR Roofs"], site_trading_name="Test Roofing",
                 site_trading_name_source="office_manager_email")
        self.assertEqual(rc.check(r3, MANIFEST, NOW)["status"], "Missing Items")

    def test_24_hour_quiet_rule_holds(self):
        m = copy.deepcopy(MANIFEST)
        m["files"].append({"name": "b.jpg", "arrived_at": "2026-11-03T06:00:00+00:00"})
        res = rc.check(FULL, m, NOW)
        self.assertEqual(res["status"], "Hold")
        self.assertIsNone(res["build_status"])

    def test_fact_update_in_last_24h_holds(self):
        res = rc.check(rec(last_fact_update="2026-11-03T09:00:00+00:00"), MANIFEST, NOW)
        self.assertEqual(res["status"], "Hold")

    def test_after_72_hours_of_arrivals_builds_with_late_files(self):
        m = copy.deepcopy(MANIFEST)
        m["files"].append({"name": "b.jpg", "arrived_at": "2026-11-03T06:00:00+00:00"})
        res = rc.check(rec(ready_hold_since="2026-10-31T10:00:00+00:00"), m, NOW)
        self.assertEqual(res["status"], "Ready")
        self.assertTrue(any("Late files" in n for n in res["notes"]))

    def test_fewer_than_8_photos_missing(self):
        m = {"files": [], "photo_summary": {"usable": 5, "labelled_usable": 5}}
        res = rc.check(FULL, m, NOW)
        self.assertEqual(res["status"], "Missing Items")
        self.assertTrue(any("8 usable" in x for x in res["missing_items"]))

    def test_ico_missing_blocks_gate_b_only_and_uses_approved_line(self):
        res = rc.check(rec(ico_number=""), MANIFEST, NOW)
        self.assertEqual(res["status"], "Ready")
        self.assertTrue(res["gate_b_blockers"])
        self.assertTrue(res["still_needed_lines"][0].startswith("Have you paid the ICO"))

    def test_share_google_short_link_is_missing(self):
        res = rc.check(rec(gbp_url="https://share.google/abc123"), MANIFEST, NOW)
        self.assertEqual(res["status"], "Missing Items")

    def test_dissolved_company_stops(self):
        res = rc.check(rec(company_status="Dissolved"), MANIFEST, NOW)
        self.assertEqual(res["status"], "Stopped")
        self.assertEqual(res["colour"], "red")

    def test_no_logo_uses_approved_line_svg_pending_does_not(self):
        res = rc.check(rec(logo_file=False), MANIFEST, NOW)
        self.assertIn("If you have your logo as a file", res["still_needed_lines"][0])
        res2 = rc.check(rec(logo_file=False, svg_logo_pending=True), MANIFEST, NOW)
        self.assertEqual(res2["still_needed_lines"], [])

    def test_no_camera_data_asks_photo_origin_with_business(self):
        m = copy.deepcopy(MANIFEST)
        m["photo_summary"]["no_camera_data"] = 3
        res = rc.check(FULL, m, NOW)
        self.assertIn("your team at Test Roofing Ltd?", res["still_needed_lines"][0])

    def test_missing_lines_are_from_the_fixed_list(self):
        items = json.loads((rc.ITEMS_PATH).read_text())["items"]
        allowed = {v["plain"] for v in items.values()}
        r = rec(deposit_paid=False, voice=None, i_or_we="", baseline="", registrar="")
        for line in rc.check(r, MANIFEST, NOW)["missing_items"]:
            self.assertTrue(any(line.startswith(a) for a in allowed), line)

    def test_sole_trader_needs_no_company_number(self):
        res = rc.check(rec(is_limited=False, company_number="", legal_name="Sam Smith t/a Test Roofing"),
                       MANIFEST, NOW)
        self.assertEqual(res["status"], "Ready")

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            r, m = Path(tmp) / "r.json", Path(tmp) / "m.json"
            r.write_text(json.dumps(FULL))
            m.write_text(json.dumps(MANIFEST))
            out = subprocess.run([sys.executable, str(Path(rc.__file__)), str(r), str(m), "--now", NOW],
                                 capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            self.assertEqual(json.loads(out.stdout)["status"], "Ready")


if __name__ == "__main__":
    unittest.main()
