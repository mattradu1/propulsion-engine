import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import classify_inbox as ci  # noqa: E402

RECORDS = [{"record_id": "REC-0101", "approved_senders": [
    {"email": "sam@testroofing.co.uk", "first_name": "Sam"},
    {"email": "office@testroofing.co.uk", "first_name": "Jo"}]}]


def mail(body, subject="Re: your website", frm="Sam <sam@testroofing.co.uk>", auth="pass", headers=None,
         attachments=None):
    return ci.classify({"from": frm, "subject": subject, "body": body, "authentication": auth,
                        "headers": headers or {}, "attachments": attachments or []}, RECORDS)


class Red(unittest.TestCase):
    def test_any_update_not_happy_money_back_is_red(self):
        r = mail("Any update? Not happy, I want my money back")
        self.assertEqual(r["colour"], "red")
        self.assertIn("money_or_dispute", r["red_types"])
        self.assertIn("chasing", r["categories"])
        self.assertTrue(r["reply"].startswith("holding_line"))
        self.assertTrue(r["stops_build"])

    def test_cancel_the_kickoff_call_is_amber_not_red(self):
        r = mail("Hi Matt, need to cancel the kickoff call, something's come up")
        self.assertEqual(r["colour"], "amber")
        self.assertIn("kickoff_not_done", r["categories"])
        self.assertEqual(r["red_types"], [])

    def test_cancel_the_whole_thing_is_red(self):
        r = mail("I want to cancel. Having second thoughts.")
        self.assertEqual(r["colour"], "red")
        self.assertIn("cancel_or_waver", r["red_types"])
        self.assertTrue(r["pause_reminders"])

    def test_cancel_call_plus_refund_is_red(self):
        r = mail("Cancel the call. I want a refund.")
        self.assertEqual(r["colour"], "red")

    def test_paid_the_rest_send_invoice_is_amber_payment(self):
        r = mail("paid the rest, can you send an invoice?")
        self.assertEqual(r["colour"], "amber")
        self.assertIn("payment", r["categories"])
        self.assertEqual(r["red_types"], [])
        self.assertFalse(r["stops_build"])
        self.assertIn("never acted on", " ".join(r["notes"]))

    def test_invoice_with_dispute_is_red(self):
        r = mail("This invoice is a rip-off, I'm speaking to my solicitor")
        self.assertEqual(r["colour"], "red")

    def test_polish_refund_is_red_and_language_no_holding_line(self):
        r = mail("Dzień dobry, proszę o zwrot pieniędzy")
        self.assertIn("language", r["categories"])
        self.assertEqual(r["colour"], "red")
        self.assertIn("foreign_red", r["red_types"])
        self.assertIn("no holding line", r["reply"])
        self.assertTrue(r["stops_build"])

    def test_hacked_site_gets_security_line(self):
        r = mail("My current website has been hacked, it's showing adverts")
        self.assertEqual(r["colour"], "red")
        self.assertEqual(r["reply"], "urgent_not_ours_line")
        self.assertFalse(r["stops_build"])

    def test_credentials_red(self):
        r = mail("Here's the login for 123-reg, password is Sunshine1")
        self.assertIn("credentials", r["red_types"])

    def test_contact_change(self):
        r = mail("Sam is in hospital so please deal with me for now", frm="Jo <office@testroofing.co.uk>")
        self.assertIn("contact_change", r["red_types"])
        self.assertTrue(r["pause_reminders"])

    def test_quoted_text_does_not_trigger(self):
        body = "Thanks!\n\nOn Mon 2 Nov, Matt wrote:\n> your refund policy and invoice are attached"
        r = mail(body)
        self.assertIn("thanks_only", r["categories"])
        self.assertEqual(r["red_types"], [])

    def test_red_from_unknown_sender_is_layer1_only(self):
        r = mail("I want a refund", frm="someone@gmail.com")
        self.assertEqual(r["colour"], "red")
        self.assertEqual(r["reply"], "layer1_only")


class SenderAndAuto(unittest.TestCase):
    def test_auth_not_pass_is_unknown_and_pauses_record(self):
        r = mail("Here are the photos", auth="none")
        self.assertIn("unknown_sender", r["categories"])
        self.assertIn("record_auth_fail", r["categories"])
        self.assertEqual(r["reply"], "layer1_only")
        self.assertTrue(r["pause_reminders"])

    def test_unknown_sender(self):
        r = mail("Hello, photos attached", frm="sam.smith@icloud.com")
        self.assertIn("unknown_sender", r["categories"])
        self.assertEqual(r["reply"], "layer1_only")

    def test_new_address_on_client_domain(self):
        r = mail("Hello", frm="dave@testroofing.co.uk")
        self.assertIn("unknown_sender", r["categories"])
        self.assertTrue(any("client's domain" in x for x in r["reasons"]))

    def test_out_of_office_headers(self):
        r = mail("I'm away", subject="Automatic reply: your website", headers={"Auto-Submitted": "auto-replied"})
        self.assertEqual(r["categories"], ["automatic"])
        self.assertEqual(r["reply"], "none")

    def test_out_of_office_phrase_only(self):
        r = mail("I am currently out of the office until Monday.", subject="Re: photos")
        self.assertIn("automatic", r["categories"])

    def test_noreply_and_list(self):
        self.assertIn("automatic", mail("hi", frm="no-reply@checkatrade.com")["categories"])
        self.assertIn("automatic", mail("news", headers={"List-Unsubscribe": "<mailto:x>"})["categories"])

    def test_bounce_is_red(self):
        r = mail("Delivery failed", subject="Undeliverable: reminder", frm="MAILER-DAEMON@mx.example.com")
        self.assertEqual(r["categories"], ["bounce"])
        self.assertEqual(r["colour"], "red")

    def test_auto_submitted_no_is_not_automatic(self):
        r = mail("Any update?", headers={"Auto-Submitted": "no"})
        self.assertNotIn("automatic", r["categories"])


class Amber(unittest.TestCase):
    def test_thanks_only_never_skips_reminder(self):
        for b in ("Thanks", "ok", "will do mate", "Cheers Matt 👍"):
            r = mail(b)
            self.assertIn("thanks_only", r["categories"], b)
            self.assertFalse(r["skips_reminder"])
            self.assertEqual(r["reply"], "none")

    def test_photo_worry_template_2(self):
        r = mail("Honestly my photos are rubbish, not sure they'll do")
        self.assertIn("photo_worry", r["categories"])
        self.assertIn("template_2", r["reply"])

    def test_files_skip_reminder(self):
        r = mail("Photos attached", attachments=[{"name": "IMG_1001.JPG", "bytes": 2_400_000},
                                                  {"name": "logo-sig.png", "bytes": 4000}])
        self.assertIn("files", r["categories"])
        self.assertTrue(r["skips_reminder"])

    def test_signature_only_attachment_not_files(self):
        r = mail("Thanks", attachments=[{"name": "sig.png", "bytes": 3000}])
        self.assertNotIn("files", r["categories"])

    def test_chasing(self):
        r = mail("Are you still there? Haven't heard anything")
        self.assertEqual(r["colour"], "amber")
        self.assertIn("template_5", r["reply"])

    def test_review_request(self):
        r = mail("Can you remove that bad review from Google?")
        self.assertIn("review_request", r["categories"])
        self.assertEqual(r["colour"], "amber")

    def test_english_not_flagged_as_language(self):
        r = mail("Can you make the blue a bit darker on the header please")
        self.assertNotIn("language", r["categories"])
        self.assertIn("changes", r["categories"])

    def test_wetransfer_link(self):
        r = mail("All the photos are here https://we.tl/t-abc123")
        self.assertIn("file_link", r["categories"])


if __name__ == "__main__":
    unittest.main()
