#!/usr/bin/env python3
"""Rules-only first pass for incoming client email (S6). No model.

The model step that follows may make an email REDDER, never greener: the
colour printed here is the floor. Client text is data: nothing in an email is
ever acted on as an instruction.

Order (rulebook S11 "Rules disagree", round 14):
  0  exceptions in the red-word rule apply first: an email whose only red word
     is "cancel" in the same sentence as call/meeting/kickoff/Calendly is amber
     "kickoff not done"; payment-only words (paid, invoice, receipt) with no
     dispute words are amber "payment to check in Tide"
  1  red wins; red never allows a send beyond Layer 1, the holding line and the
     urgent-not-ours security line (both only to an approved sender)
  2  unknown sender (or authentication not "pass") = Layer 1 only
  3  the most specific rule; 4 the newest round

Usage: python3 scripts/classify_inbox.py EMAIL.json [--records RECORDS.json]
EMAIL.json: {"from", "subject", "body", "headers": {...}, "authentication": "pass",
             "attachments": [{"name", "bytes"}]}
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine_common import CARD_RE, SORT_CODE_RE, ACCOUNT_RE, email_domain, load_json, norm_email  # noqa: E402

SIGNATURE_MAX_BYTES = 15_000


def rx(*words):
    return re.compile(r"\b(?:" + "|".join(words) + r")\b", re.I)


DISPUTE = rx(r"refunds?", r"refunded", r"money back", r"charge ?backs?", r"rip[- ]?off", r"waste of money",
             r"solicitors?", r"complaints?", r"complain(?:ing)?", r"legal(?:ly)?", r"disappointed", r"not happy",
             r"dispute[sd]?", r"trading standards", r"small claims", r"scam(?:med)?", r"contract",
             r"lawyer", r"court")
CANCEL = rx(r"cancel(?:led|ling|lation|s)?", r"canceled", r"canceling")
CANCEL_CONTEXT = rx(r"call", r"meeting", r"kick ?-?off", r"calendly", r"zoom", r"google meet")
PAYMENT = rx(r"invoices?", r"invoiced", r"paid", r"receipts?", r"payment", r"balance")
WAVER = rx(r"second thoughts", r"my mate can do it", r"stop emailing me", r"don'?t want to (?:go ahead|continue)",
           r"pull(?:ing)? out", r"changed my mind", r"not going ahead")
WHOLE_SITE = rx(r"not what i wanted", r"looks like a template", r"hate it", r"start again")
URGENT = rx(r"hacked", r"virus", r"malware", r"site (?:is )?down", r"website (?:is )?down", r"been compromised",
            r"phishing")
CONTACT_CHANGE = rx(r"passed away", r"died", r"in hospital", r"seriously ill", r"is ill", r"funeral",
                    r"no longer (?:with|at) the company")
CREDENTIALS = rx(r"password", r"passcode", r"login details", r"log ?in is", r"my pin", r"username and")
REVIEW = re.compile(r"\b(?:remove|delete|take down|reply to|report)\b[^.?!\n]{0,40}\breviews?\b|\bbad review\b", re.I)
CHASING = rx(r"any update", r"any news", r"are you still there", r"heard nothing", r"haven'?t heard",
             r"what'?s happening", r"chasing", r"where are we")
BUSY = rx(r"next week", r"after christmas", r"when it'?s dry", r"on holiday", r"having an operation",
          r"flat out", r"after the new year", r"in a few weeks")
PHOTO_WORRY = re.compile(r"photos? (?:are|is) (?:rubbish|terrible|bad|crap|not great)|not (?:got )?(?:many|enough) "
                         r"(?:good )?photos|don'?t have (?:many|any|enough) (?:good )?photos|can'?t take (?:any )?more",
                         re.I)
PHOTOS_ELSEWHERE = rx(r"facebook", r"instagram", r"checkatrade", r"my old site", r"my website")
FILE_LINK = re.compile(r"(?:wetransfer\.com|we\.tl|dropbox\.com|db\.tt|photos\.google\.com|photos\.app\.goo\.gl|"
                       r"icloud\.com|drive\.google\.com)", re.I)
CHANGES = rx(r"change", r"can you make", r"instead of", r"swap", r"darker", r"lighter", r"bigger", r"smaller",
             r"move the", r"take out", r"add (?:a|the|our)")
FACT = rx(r"new number", r"our number is", r"phone number", r"we now cover", r"we also cover", r"address is",
          r"email is", r"we'?ve been trading", r"years in the trade", r"accredited", r"registered with")
INSTRUCTION = rx(r"send (?:me |over )?(?:the|an|a|my) (?:final )?invoice", r"change the price", r"bank details", r"transfer", r"pay (?:to|into)")
CALL_ME = rx(r"ring me", r"call me", r"give me a (?:call|ring)", r"recommend(?:ed)? you", r"my mate wants")
PROSPECT = rx(r"how much", r"quote", r"price for a website", r"interested in")

# Small non-English red list (round 8a, Polish replies). Raises red; no holding line.
FOREIGN_RED = rx(r"zwrot", r"zwrotu", r"pieni[eę]dzy", r"reklamacj[ae]", r"prawnik", r"adwokat", r"umow[ay]",
                 r"anuluj(?:[eę])?", r"oszust\w*", r"skarg[ai]", r"niezadowolon\w*",
                 r"rambursare", r"avocat", r"pl[aâ]ngere", r"devoluci[oó]n", r"reembolso")

THANKS_WORDS = {"thanks", "thank", "you", "cheers", "ok", "okay", "great", "ta", "will", "do", "yes", "perfect",
                "lovely", "brilliant", "mate", "much", "many", "appreciated", "noted", "got", "it", "👍", "sound",
                "nice", "one", "x", "matt", "fine", "cool"}
EN_STOP = {"the", "and", "to", "is", "you", "i", "it", "of", "for", "a", "my", "me", "can", "have", "this", "that",
           "with", "be", "on", "not", "are", "we", "will", "what", "please", "thanks", "in", "at", "do", "so",
           "if", "but", "just", "your", "our", "was", "any", "get", "no", "yes", "hi", "from", "all", "when",
           "need", "want", "send", "update", "website", "photos", "call", "back", "there", "here", "know", "about"}
AUTO_SUBJECT = re.compile(r"^(?:automatic reply|auto[- ]?reply|autoreply|out of (?:the )?office|away from|"
                          r"undeliverable|delivery status notification|mail delivery failed|returned mail|"
                          r"delivery has failed|i am away|i'm away|on annual leave)", re.I)
AUTO_BODY = re.compile(r"\b(?:i am|i'm) (?:currently )?(?:out of (?:the )?office|away from the office|on annual leave)"
                       r"|this is an automatic reply|this is an automated (?:message|response)", re.I)
BOUNCE_SUBJECT = re.compile(r"undeliverable|delivery status notification|mail delivery failed|returned mail|"
                            r"delivery has failed", re.I)
NOREPLY_LOCAL = re.compile(r"^(?:no-?reply|do-?not-?reply|donotreply|mailer-daemon|postmaster|bounces?|notifications?)"
                           r"(?:[+.\-].*)?$", re.I)

STOP_BUILD_RED = {"money_or_dispute", "cancel_or_waver", "credentials", "contact_change", "whole_site_reject",
                  "foreign_red"}


def strip_quoted(body):
    """Drop quoted replies and signatures so Matt's own words never trigger."""
    out = []
    for ln in (body or "").splitlines():
        s = ln.strip()
        if s.startswith(">"):
            continue
        if re.match(r"^On .+wrote:$", s) or re.match(r"^-{2,} ?Original Message", s, re.I) or s == "--" \
                or re.match(r"^From: .+", s) or re.match(r"^Sent from my (?:iPhone|iPad|Samsung|Android)", s, re.I):
            break
        out.append(ln)
    return "\n".join(out).strip()


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def tokens(text):
    return re.findall(r"[^\W\d_]+|👍", text.lower())


def is_non_english(text):
    toks = tokens(text)
    if not toks:
        return False
    en = sum(1 for t in toks if t in EN_STOP)
    non_ascii = any(ord(ch) > 127 and ch.isalpha() for ch in text)
    ratio = en / len(toks)
    if non_ascii and ratio < 0.3:
        return True
    return len(toks) >= 4 and ratio < 0.1


def header(headers, name):
    for k, v in (headers or {}).items():
        if k.lower() == name.lower():
            return str(v)
    return None


def automatic(email):
    h = email.get("headers") or {}
    why = []
    a = header(h, "Auto-Submitted")
    if a and a.strip().lower() != "no":
        why.append(f"Auto-Submitted: {a}")
    for k in ("X-Autoreply", "X-Autorespond", "X-Auto-Response-Suppress", "List-Id", "List-Unsubscribe"):
        if header(h, k):
            why.append(f"{k} header")
    p = header(h, "Precedence")
    if p and p.strip().lower() in ("bulk", "junk", "list", "auto_reply"):
        why.append(f"Precedence: {p}")
    rp = header(h, "Return-Path")
    if rp is not None and rp.strip() in ("<>", ""):
        why.append("empty Return-Path")
    local = norm_email(sender_address(email.get("from"))).split("@")[0]
    if NOREPLY_LOCAL.match(local):
        why.append(f"sender {local}@")
    if AUTO_SUBJECT.search(email.get("subject") or ""):
        why.append("auto-reply subject")
    if AUTO_BODY.search(email.get("body") or ""):
        why.append("auto-reply wording")
    bounce = bool(BOUNCE_SUBJECT.search(email.get("subject") or "")) or local in ("mailer-daemon", "postmaster")
    return why, bounce


def sender_address(frm):
    m = re.search(r"<([^>]+)>", frm or "")
    return (m.group(1) if m else (frm or "")).strip()


def find_sender(addr, records):
    a = norm_email(addr)
    hits = []
    for r in records or []:
        for s in r.get("approved_senders", []):
            if norm_email(s.get("email")) == a:
                hits.append((r, s))
    return hits


def classify(email, records=None, own_addresses=("matt.radu@propulsionmarketing.co.uk",)):
    reasons, cats, red_types, notes = [], [], [], []
    colour = "green"
    addr = norm_email(sender_address(email.get("from")))
    auth = (email.get("authentication") or "missing").lower()
    body_raw = email.get("body") or ""
    body = strip_quoted(body_raw)
    text = f"{email.get('subject') or ''}\n{body}"
    atts = email.get("attachments") or []
    real_files = [a for a in atts if int(a.get("bytes", 0)) >= SIGNATURE_MAX_BYTES]
    hits = find_sender(addr, records)

    res = {"from": addr, "record_id": hits[0][0].get("record_id") if len(hits) == 1 else None}

    def out(reply, **kw):
        order = {"none": 0, "green": 1, "amber": 2, "red": 3}
        res.update(categories=cats or ["unclear"], colour=colour, reasons=reasons, red_types=sorted(set(red_types)),
                   reply=reply, notes=notes, authentication=auth,
                   stops_build=bool(set(red_types) & STOP_BUILD_RED) or "language" in cats,
                   pause_reminders=any(c in cats for c in ("language", "contact_change", "cancel_or_waver",
                                                            "record_auth_fail", "busy_pause", "shared_address_clash")),
                   skips_reminder=bool(real_files) and colour != "red",
                   model_may_only_make_redder=True, colour_rank=order[colour])
        res.update(kw)
        return res

    # own address / loops
    if addr in own_addresses:
        cats.append("own_address")
        reasons.append("from Matt's own address: forwarded files need the record ID in the subject")
        colour = "none"
        return out("none")

    # automatic mail and bounces: no engine reply ever
    why, bounce = automatic(email)
    if why:
        cats.append("bounce" if bounce else "automatic")
        reasons += why
        if bounce:
            colour = "red"
            red_types.append("bounce")
            reasons.append("email bounced: all engine email to that address stops")
        else:
            colour = "none"
        return out("none")

    # authentication
    if auth != "pass":
        cats.append("unknown_sender")
        reasons.append(f"authentication is {auth!r}, not 'pass': Unsorted, never a fact, file or approval")
        if hits:
            cats.append("record_auth_fail")
            reasons.append("mail from a record's own address failed authentication: pause that record's "
                           "reminders; Saturday list 'unauthenticated sender'")
        colour = "amber"
    elif not hits:
        cats.append("unknown_sender")
        dom = email_domain(addr)
        rec_domains = {email_domain(s.get("email")) for r in records or [] for s in r.get("approved_senders", [])}
        if dom in rec_domains:
            reasons.append("new address on a client's domain: Layer 1 only; flag")
        elif PROSPECT.search(text):
            cats.append("prospect")
            reasons.append("not a client: Layer 1 only, flagged for Monday")
        else:
            reasons.append("sender isn't an approved sender: Layer 1 only; files to Unsorted")
        colour = "amber"
    elif len(hits) > 1:
        cats.append("shared_address_clash")
        reasons.append("one address on more than one record: files to Unsorted, reminders pause on both")
        colour = "amber"
    known = auth == "pass" and len(hits) == 1

    # thanks only (on the stripped body)
    toks = tokens(body)
    if toks and len(toks) <= 6 and all(t in THANKS_WORDS for t in toks) and not real_files:
        cats.append("thanks_only")
        reasons.append("only thanks/ok: nothing sent; never skips a reminder")
        if known:
            colour = "none"
        return out("none" if known else "layer1_only", skips_reminder=False)

    # language
    non_en = is_non_english(body or email.get("subject") or "")
    if non_en:
        cats.append("language")
        reasons.append("not in English: Layer 1 only; reminders pause and the build stops until Matt reads "
                       "a translation")
        colour = "amber"

    # ---- red words with the step-0 exceptions applied first
    dispute = [m.group(0) for m in DISPUTE.finditer(text)]
    cancels = []
    for s in sentences(text):
        for m in CANCEL.finditer(s):
            cancels.append((m.group(0), bool(CANCEL_CONTEXT.search(s))))
    payment = [m.group(0) for m in PAYMENT.finditer(text)]
    waver = [m.group(0) for m in WAVER.finditer(text)]
    real_cancel = [c for c, ctx in cancels if not ctx]
    call_cancel = [c for c, ctx in cancels if ctx]

    if dispute:
        red_types.append("money_or_dispute")
        reasons.append("money, anger or legal words: " + ", ".join(sorted(set(w.lower() for w in dispute))))
    if real_cancel or waver:
        red_types.append("cancel_or_waver")
        cats.append("cancel_or_waver")
        reasons.append("cancel or wavering: reminders stop, build On Hold, Matt rings first on Monday")
    if call_cancel and not dispute and not real_cancel:
        cats.append("kickoff_not_done")
        reasons.append("'cancel' is about a call or meeting: amber 'kickoff not done', not red")
        colour = max_colour(colour, "amber")
    if payment and not dispute:
        cats.append("payment")
        reasons.append("payment-only words (" + ", ".join(sorted(set(w.lower() for w in payment)))
                       + "): amber 'payment to check in Tide'; replies held, build carries on")
        colour = max_colour(colour, "amber")
    if WHOLE_SITE.search(text):
        red_types.append("whole_site_reject")
        reasons.append("rejects the whole site: not a round; Matt rings within 1 working day")
    if URGENT.search(text):
        red_types.append("urgent_not_ours")
        cats.append("urgent_not_ours")
        reasons.append("urgent, not ours (their current site): security line to an approved sender; red")
    if CONTACT_CHANGE.search(text):
        red_types.append("contact_change")
        cats.append("contact_change")
        reasons.append("illness, absence or death mentioned: reminders pause; Matt confirms a new signer")
    if CREDENTIALS.search(body) or CARD_RE.search(body) or (SORT_CODE_RE.search(body) and ACCOUNT_RE.search(body)):
        red_types.append("credentials")
        reasons.append("credentials or card/bank numbers: never copied anywhere; 'credentials sent, not stored'")
        notes.append("Saturday pack shows [removed]; Matt asks them to change it")
    if non_en and FOREIGN_RED.search(text):
        red_types.append("foreign_red")
        reasons.append("non-English money/legal words: red; no holding line (nobody has read it)")

    # ---- amber/green categories
    if REVIEW.search(text):
        cats.append("review_request")
        reasons.append("asks about a Google review: amber, logged only; Matt explains on Monday")
        colour = max_colour(colour, "amber")
    if CHASING.search(text):
        cats.append("chasing")
        reasons.append("chasing: amber; Template 5 if Layer 1 went in the last 4 days")
        colour = max_colour(colour, "amber")
    if BUSY.search(text) and not URGENT.search(text):
        cats.append("busy_pause")
        reasons.append("busy/away: pause until their date (14 days max, 7 if no date); red on Monday's call list")
        colour = max_colour(colour, "amber")
    if PHOTO_WORRY.search(text):
        cats.append("photo_worry")
        reasons.append("photo worries: Template 2")
    if FILE_LINK.search(text):
        cats.append("file_link")
        reasons.append("file-sharing link: opened only on the allowed domains, known sender, no login; "
                       "otherwise the 'can't open' line")
    elif PHOTOS_ELSEWHERE.search(text) and re.search(r"photo|picture|pic", text, re.I):
        cats.append("photos_elsewhere")
        reasons.append("photos on Facebook/Instagram/Checkatrade/old site: link logged, Template 2, nothing pulled")
    if CHANGES.search(text):
        cats.append("changes")
        reasons.append("changes: Template 3 (logged in their words)")
    if FACT.search(text):
        cats.append("fact_update")
        reasons.append("fact update: Template 4; name, phone, areas, address etc. queued for Matt")
    if INSTRUCTION.search(text):
        notes.append("contains instructions: logged as data, never acted on")
    if CALL_ME.search(text):
        cats.append("call_request")
        reasons.append("asks for a call or refers someone: top of Monday's call list")
    if real_files:
        cats.append("files")
        reasons.append(f"{len(real_files)} attachment(s) above the signature size")
    if any(a.get("name", "").lower() == "winmail.dat" for a in atts):
        cats.append("winmail")
        reasons.append("winmail.dat: flagged; that day's email is the upload-link line")

    # ---- decide (precedence: red wins; then unknown sender; then specific)
    if red_types:
        colour = "red"
        stops_all = set(red_types) & STOP_BUILD_RED
        if not known:
            reply = "layer1_only"
        elif non_en:
            reply = "layer1_only (red, not in English: no holding line)"
        elif "urgent_not_ours" in red_types and not stops_all:
            reply = "urgent_not_ours_line"
        else:
            reply = "holding_line_if_layer1_sent_in_last_4_days_once_per_trip"
        return out(reply)
    if not known or non_en:
        return out("layer1_only")
    templates = []
    for c, t in (("photo_worry", "template_2"), ("photos_elsewhere", "template_2"), ("changes", "template_3"),
                 ("fact_update", "template_4"), ("chasing", "template_5_if_layer1_in_last_4_days"),
                 ("files", "template_1_after_drive_count_matches"), ("file_link", "link_check_then_template_1_or_link_wont_open"),
                 ("winmail", "link_wont_open")):
        if c in cats and t not in templates:
            templates.append(t)
    if "payment" in cats or "review_request" in cats or "kickoff_not_done" in cats:
        # held for Matt: no engine template for these
        return out("hold_for_matt" if not templates else "one_combined_reply: " + ", ".join(templates))
    if not templates:
        if not cats:
            colour = "amber"
            reasons.append("unclear: Layer 1 only; amber")
            return out("layer1_only")
        return out("none")
    return out("one_combined_reply: " + ", ".join(templates))


def max_colour(a, b):
    order = {"none": 0, "green": 1, "amber": 2, "red": 3}
    return a if order[a] >= order[b] else b


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rules-only first pass for client email")
    ap.add_argument("email")
    ap.add_argument("--records")
    a = ap.parse_args(argv)
    records = load_json(a.records) if a.records else []
    print(json.dumps(classify(load_json(a.email), records), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
