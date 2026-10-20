import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import presend_check as pc  # noqa: E402

NOW = "2026-11-02T10:00:00+00:00"
FORM = "https://forms.example-propulsion.test/f/REC-0101-tok8f2k"
UPLOAD = "https://upload.example-propulsion.test/u/REC-0101-w9x"
PREVIEW = "https://preview.example-propulsion.test/p/k3J9xQ2mZr8LwT5vB7nC4d"

RECORD = {
    "record_id": "REC-0101",
    "business": "Test Roofing Ltd",
    "trading_names": ["Test Roofing", "TR Roofs"],
    "build_status": 2,
    "colour": "green",
    "signer_email": "sam@testroofing.co.uk",
    "approved_senders": [
        {"email": "sam@testroofing.co.uk", "first_name": "Sam"},
        {"email": "office@testroofing.co.uk", "first_name": "Jo"},
        {"email": "family.smith@gmail.com", "first_name": "Sam", "shared": True},
    ],
    "form_link": FORM,
    "upload_link": UPLOAD,
    "approved_preview_link": PREVIEW,
    "preview_date": "Monday 9 November",
    "feedback_date": "Thursday 12 November",
    "launch_date": "Wednesday 18 November",
}

OTHER = {
    "record_id": "REC-0102", "business": "Bright Spark Electrical", "phone": "01632 960123",
    "approved_senders": [{"email": "lee@brightspark.co.uk", "first_name": "Lee"}],
    "form_link": "https://forms.example-propulsion.test/f/REC-0102-zz",
}

TEMPLATES = pc.load_templates()
ITEMS = pc.load_items()
# Test copy of the fixed lines with one reminder ask approved, as Matt would.
ITEMS_APPROVED = copy.deepcopy(ITEMS)
ITEMS_APPROVED["items"]["photos"]["approved"] = True

STATE = {"kill_switch": "off", "engine_pauses": [], "breaker_tripped": False, "run_sent_count": 0}


def draft(tid, fields, variant=None, to="sam@testroofing.co.uk", shared=False, **extra):
    rec = copy.deepcopy(extra.pop("record", RECORD))
    body, _ = pc.render(TEMPLATES[tid], fields, variant, shared)
    d = {"draft_id": "d-1", "to": [to], "cc": [], "thread_record_id": rec["record_id"], "record": rec,
         "template_id": tid, "variant_id": variant, "fields": fields, "body": body, "links": [],
         "quote_source_auth": "pass"}
    d.update(extra)
    return d


def r1_fields(**kw):
    f = {"first_name": "Sam", "top_item": "your project photos", "where_to_find": "on your upload link",
         "form_link": FORM, "upload_link": UPLOAD}
    f.update(kw)
    return f


def run(d, sent=None, state=None, items=ITEMS_APPROVED, records=None):
    return pc.check(d, sent or [], records if records is not None else [RECORD, OTHER],
                    STATE if state is None else state, NOW, TEMPLATES, items)


def sent_entry(record_id="REC-0101", to="sam@testroofing.co.uk", at="2026-11-02T09:30:00+00:00",
               tid="template_1", engine=True, status="sent", **kw):
    e = {"draft_id": kw.pop("draft_id", f"s-{at}-{to}"), "record_id": record_id, "to": [to], "template_id": tid,
         "engine_labelled": engine, "status": status, "at": at}
    e.update(kw)
    return e


class PreviewEmail(unittest.TestCase):
    def fields(self, **kw):
        f = {"first_name": "Sam", "preview_link": PREVIEW, "feedback_date": "Thursday 12 November",
             "launch_date": "Wednesday 18 November"}
        f.update(kw)
        return f

    def test_round5_preview_email_with_its_own_fixed_link_allows(self):
        res = run(draft("preview_email", self.fields(), engine_labelled=False))
        self.assertEqual(res["decision"], "ALLOW", res["reasons"])
        self.assertEqual(res["action"], "save_gmail_draft_for_matt")

    def test_preview_link_not_the_approved_version_blocks(self):
        d = draft("preview_email", self.fields(preview_link="https://preview.example-propulsion.test/p/other"))
        self.assertEqual(run(d)["decision"], "BLOCK")

    def test_preview_link_on_a_reminder_blocks(self):
        d = draft("reminder_1", r1_fields())
        d["body"] += " " + PREVIEW
        res = run(d)
        self.assertEqual(res["decision"], "BLOCK")
        self.assertTrue(any("only allowed on the preview email" in r for r in res["reasons"]))

    def test_preview_dates_must_match_row(self):
        d = draft("preview_email", self.fields(launch_date="Friday 20 November"))
        self.assertEqual(run(d)["decision"], "BLOCK")


class Reminders(unittest.TestCase):
    def test_clean_reminder_1_allows(self):
        res = run(draft("reminder_1", r1_fields()))
        self.assertEqual(res["decision"], "ALLOW", res["reasons"])

    def test_unapproved_ask_blocks_until_matt_approves(self):
        res = run(draft("reminder_1", r1_fields()), items=ITEMS)
        self.assertEqual(res["decision"], "BLOCK")
        self.assertTrue(res["counts_as_reminder"])

    def test_wrong_form_link_blocks(self):
        res = run(draft("reminder_1", r1_fields(form_link="https://forms.example-propulsion.test/f/OTHER")))
        self.assertEqual(res["decision"], "BLOCK")

    def test_reminder_3_past_date_blocks(self):
        f = {"first_name": "Sam", "preview_date": "Monday 9 November", "top_item": "your project photos",
             "date_needed": "Friday 30 October", "upload_link": UPLOAD, "form_link": FORM}
        d = draft("reminder_3", f, field_dates={"date_needed": "2026-10-30"})
        self.assertEqual(run(d)["decision"], "BLOCK")
        d2 = draft("reminder_3", dict(f, date_needed="Wednesday 4 November"), field_dates={"date_needed": "2026-11-04"})
        self.assertEqual(run(d2)["decision"], "ALLOW", run(d2)["reasons"])

    def test_content_block_counts_and_turns_red(self):
        d = draft("reminder_1", r1_fields())
        d["body"] = d["body"].replace("Thanks, Matt", "Cheers, Matt")
        res = run(d)
        self.assertEqual(res["decision"], "BLOCK")
        self.assertTrue(res["counts_as_reminder"])
        self.assertEqual(res["row_colour"], "red")

    def test_breaker_block_does_not_count_as_reminder(self):
        res = run(draft("reminder_1", r1_fields()), state=dict(STATE, breaker_tripped=True))
        self.assertEqual(res["decision"], "BLOCK")
        self.assertEqual(res["block_types"], ["breaker"])
        self.assertFalse(res["counts_as_reminder"])
        self.assertIsNone(res["row_colour"])

    def test_kill_switch_missing_counts_as_on_and_not_a_reminder(self):
        res = run(draft("reminder_1", r1_fields()), state={})
        self.assertEqual(res["decision"], "BLOCK")
        self.assertIn("kill_switch", res["block_types"])
        self.assertFalse(res["counts_as_reminder"])

    def test_engine_pause_blocks(self):
        res = run(draft("reminder_2", {"first_name": "Sam", "top_item": "your project photos",
                                       "upload_link": UPLOAD, "form_link": FORM}),
                  state=dict(STATE, engine_pauses=["Make down"]))
        self.assertEqual(res["block_types"], ["engine_pause"])

    def test_paused_row_blocks(self):
        rec = dict(RECORD, reminders_paused=True)
        self.assertEqual(run(draft("reminder_1", r1_fields(), record=rec))["decision"], "BLOCK")

    def test_reminders_counted_ignores_system_blocks(self):
        log = [sent_entry(tid="reminder_1", at="2026-10-28T09:40:00+00:00"),
               sent_entry(tid="reminder_2", status="blocked", block_type="breaker", at="2026-10-30T09:40:00+00:00"),
               sent_entry(tid="reminder_2", status="blocked", block_type="content", at="2026-10-31T09:40:00+00:00")]
        self.assertEqual(pc.reminders_counted(log, "REC-0101"), 2)


class Limits(unittest.TestCase):
    def test_20_hour_rule_per_client(self):
        log = [sent_entry(to="office@testroofing.co.uk", at="2026-11-01T18:00:00+00:00")]
        res = run(draft("reminder_1", r1_fields()), sent=log)
        self.assertEqual(res["block_types"], ["hold_20h"])
        self.assertFalse(res["counts_as_reminder"])

    def test_20_hour_rule_after_window_allows(self):
        log = [sent_entry(at="2026-11-01T13:00:00+00:00")]
        self.assertEqual(run(draft("reminder_1", r1_fields()), sent=log)["decision"], "ALLOW")

    def test_matt_own_sends_and_vacation_reply_never_count(self):
        log = [sent_entry(engine=False, tid="preview_email", at="2026-11-02T09:00:00+00:00"),
               sent_entry(engine=True, tid="vacation_reply", at="2026-11-02T09:10:00+00:00")]
        self.assertEqual(run(draft("reminder_1", r1_fields()), sent=log)["decision"], "ALLOW")

    def test_breaker_more_than_10_an_hour(self):
        log = [sent_entry(record_id=f"REC-9{i:02d}", to=f"c{i}@example.co.uk",
                          at=f"2026-11-02T09:{10 + i:02d}:00+00:00") for i in range(10)]
        res = run(draft("reminder_1", r1_fields()), sent=log)
        self.assertEqual(res["decision"], "BLOCK")
        self.assertIn("breaker", res["block_types"])
        self.assertFalse(res["counts_as_reminder"])

    def test_breaker_two_to_one_client_in_20h_trips_everything(self):
        log = [sent_entry(record_id="REC-0200", to="a@x.co.uk", at="2026-11-02T08:00:00+00:00"),
               sent_entry(record_id="REC-0200", to="a@x.co.uk", at="2026-11-02T08:30:00+00:00")]
        self.assertIn("breaker", run(draft("reminder_1", r1_fields()), sent=log)["block_types"])

    def test_carry_over_after_8_in_a_run(self):
        res = run(draft("reminder_1", r1_fields()), state=dict(STATE, run_sent_count=8))
        self.assertEqual(res["block_types"], ["carry_over"])

    def test_sending_without_sent_never_resends(self):
        log = [sent_entry(draft_id="d-1", status="sending", engine=True, at="2026-10-30T09:00:00+00:00")]
        self.assertEqual(run(draft("reminder_1", r1_fields()), sent=log)["decision"], "BLOCK")


class Recipients(unittest.TestCase):
    def test_thread_from_another_record_blocks(self):
        d = draft("reminder_1", r1_fields())
        d["thread_record_id"] = "REC-0102"
        self.assertEqual(run(d)["decision"], "BLOCK")

    def test_unlisted_recipient_blocks(self):
        self.assertEqual(run(draft("reminder_1", r1_fields(), to="sam@gmail.com"))["decision"], "BLOCK")

    def test_cc_blocks(self):
        d = draft("reminder_1", r1_fields())
        d["cc"] = ["office@testroofing.co.uk"]
        self.assertEqual(run(d)["decision"], "BLOCK")

    def test_greeting_must_match_listed_sender(self):
        d = draft("reminder_1", r1_fields(first_name="Sam"), to="office@testroofing.co.uk")
        res = run(d)
        self.assertEqual(res["decision"], "BLOCK")
        self.assertTrue(any("greeting" in r for r in res["reasons"]))
        d2 = draft("reminder_1", r1_fields(first_name="Jo"), to="office@testroofing.co.uk")
        self.assertEqual(run(d2)["decision"], "ALLOW", run(d2)["reasons"])

    def test_shared_address_greeted_hi(self):
        f = {"top_item": "your project photos", "where_to_find": "on your upload link",
             "form_link": FORM, "upload_link": UPLOAD}
        d = draft("reminder_1", f, to="family.smith@gmail.com", shared=True)
        self.assertTrue(d["body"].startswith("Hi, automatic reminder"))
        self.assertEqual(run(d)["decision"], "ALLOW", run(d)["reasons"])

    def test_signer_only_line_to_non_signer_blocks(self):
        f = {"first_name": "Jo", "a": "Test Roofing", "b": "TR Roofs"}
        d = draft("trading_name_question", f, to="office@testroofing.co.uk", engine_labelled=False)
        self.assertEqual(run(d)["decision"], "BLOCK")
        d2 = draft("trading_name_question", dict(f, first_name="Sam"), engine_labelled=False)
        self.assertEqual(run(d2)["decision"], "ALLOW", run(d2)["reasons"])

    def test_red_row_allows_only_holding_line_once(self):
        rec = dict(RECORD, colour="red")
        self.assertEqual(run(draft("template_2", {"first_name": "Sam", "upload_link": UPLOAD},
                                   record=rec))["decision"], "BLOCK")
        hl = draft("holding_line", {"first_name": "Sam"}, record=rec)
        self.assertEqual(run(hl)["decision"], "ALLOW", run(hl)["reasons"])
        log = [sent_entry(tid="holding_line", at="2026-10-31T10:00:00+00:00")]
        self.assertEqual(run(hl, sent=log)["decision"], "BLOCK")

    def test_manual_row_blocks(self):
        rec = dict(RECORD, manual=True)
        self.assertEqual(run(draft("template_2", {"first_name": "Sam", "upload_link": UPLOAD},
                                   record=rec))["decision"], "BLOCK")


class Content(unittest.TestCase):
    def test_braces_left_block(self):
        d = draft("reminder_1", r1_fields())
        d["body"] = d["body"].replace("Sam", "{first_name}")
        self.assertEqual(run(d)["decision"], "BLOCK")

    def test_model_chatter_blocks(self):
        d = draft("reminder_1", r1_fields())
        d["body"] = "Here is the draft email:\n" + d["body"]
        res = run(d)
        self.assertTrue(any("chatter" in r for r in res["reasons"]))

    def test_unapproved_template_blocks(self):
        d = draft("reminder_1", r1_fields())
        d["template_id"] = "free_written"
        self.assertEqual(run(d)["decision"], "BLOCK")

    def test_matt_sets_template_cannot_be_an_email(self):
        d = draft("reminder_1", r1_fields())
        d["template_id"] = "vacation_reply"
        self.assertEqual(run(d)["decision"], "BLOCK")

    def test_other_clients_identifier_blocks(self):
        f = {"first_name": "Sam", "fact": "our new number is like Bright Spark Electrical"}
        res = run(draft("template_4", f))
        self.assertEqual(res["decision"], "BLOCK")
        self.assertTrue(any("another client" in r for r in res["reasons"]))

    def test_template_3_clean_quotes_allow(self):
        f = {"first_name": "Sam", "bullets": ["make the blue darker", "add Harpenden to the areas"]}
        res = run(draft("template_3", f))
        self.assertEqual(res["decision"], "ALLOW", res["reasons"])

    def test_client_quote_with_url_phone_email_sortcode_html_blocks(self):
        for bad in ["see www.oldsite.co.uk", "call 07700 900123", "email me at a@b.co.uk",
                    "pay 20-00-00 12345678", "<script>x</script>"]:
            res = run(draft("template_4", {"first_name": "Sam", "fact": bad}))
            self.assertEqual(res["decision"], "BLOCK", bad)

    def test_client_quote_over_120_blocks(self):
        res = run(draft("template_4", {"first_name": "Sam", "fact": "word " * 30}))
        self.assertEqual(res["decision"], "BLOCK")

    def test_client_quote_needs_auth_pass(self):
        d = draft("template_3", {"first_name": "Sam", "bullets": ["make the blue darker"]},
                  quote_source_auth="fail")
        self.assertEqual(run(d)["decision"], "BLOCK")
        d2 = draft("template_3", {"first_name": "Sam", "bullets": ["4 changes logged"]}, quote_source_auth="fail")
        self.assertEqual(run(d2)["decision"], "ALLOW", run(d2)["reasons"])

    def test_filled_text_over_300_blocks(self):
        bullets = [("change number %d to something a bit longer here" % i) for i in range(8)]
        res = run(draft("template_3", {"first_name": "Sam", "bullets": bullets}))
        self.assertTrue(any("300" in r for r in res["reasons"]))

    def test_strip_client_quote_produces_clean_text(self):
        s = pc.strip_client_quote("Ring 07700 900123 or see <b>www.x.co.uk</b>, sort 20-00-00 acct 12345678 " + "x" * 200)
        self.assertEqual(pc.client_quote_problems(s), [])

    def test_template_1_still_needed_needs_approved_line(self):
        ico = ITEMS["items"]["ico"]["still_needed"]
        f = {"first_name": "Sam", "n": "6", "other_files": ", 1 PDF", "missing_items": [ico]}
        res = run(draft("template_1", f, variant="still_needed"))
        self.assertEqual(res["decision"], "ALLOW", res["reasons"])
        f2 = dict(f, missing_items=["Send me your bank details"])
        self.assertEqual(run(draft("template_1", f2, variant="still_needed"))["decision"], "BLOCK")

    def test_template_5_date_line_needs_preview_ready(self):
        d = draft("template_5", {"first_name": "Sam"}, variant="preview_ready_or_later")
        self.assertEqual(run(d)["decision"], "BLOCK")
        rec = dict(RECORD, build_status=6)
        d2 = draft("template_5", {"first_name": "Sam"}, variant="preview_ready_or_later", record=rec)
        self.assertEqual(run(d2)["decision"], "ALLOW", run(d2)["reasons"])

    def test_only_supervised_mode(self):
        res = pc.check(draft("reminder_1", r1_fields()), [], [RECORD], STATE, NOW, TEMPLATES, ITEMS_APPROVED,
                       mode="unsupervised")
        self.assertEqual(res["decision"], "BLOCK")


class TemplatesVerbatim(unittest.TestCase):
    def test_every_template_text_is_in_the_rulebook(self):
        rb = (Path(__file__).resolve().parent.parent / "docs" / "build-engine-rulebook.md").read_text()
        quoted = "\n".join(ln[2:] if ln.startswith("> ") else ln[1:] if ln.startswith(">") else ln
                           for ln in rb.split("\n"))
        for tid, t in TEMPLATES.items():
            self.assertIn(t["text"], quoted, tid)

    def test_cli_exit_codes(self):
        import subprocess
        import tempfile
        d = draft("preview_email", {"first_name": "Sam", "preview_link": PREVIEW,
                                    "feedback_date": "Thursday 12 November", "launch_date": "Wednesday 18 November"},
                  engine_labelled=False)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "d.json"
            s = Path(tmp) / "s.json"
            p.write_text(json.dumps(d))
            s.write_text(json.dumps(STATE))
            script = Path(pc.__file__)
            ok = subprocess.run([sys.executable, str(script), str(p), "--state", str(s), "--now", NOW],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            bad = subprocess.run([sys.executable, str(script), str(p), "--now", NOW], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)


if __name__ == "__main__":
    unittest.main()
