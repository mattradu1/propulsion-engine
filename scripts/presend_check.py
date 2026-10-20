#!/usr/bin/env python3
"""S3 Pre-send check. Blocks by default.

Runs before every email or Gmail draft the engine makes. In supervised mode
(until Matt's Thu 29 Oct go/no-go) ALLOW means only "may be saved as a Gmail
DRAFT for Matt". Nothing here sends, and nothing here touches the network.

Usage:
  python3 scripts/presend_check.py DRAFT.json [--sent-log SENT.json]
      [--records RECORDS.json] [--state STATE.json] [--now ISO]
  Exit code 0 = ALLOW, 1 = BLOCK, 2 = bad input (also a block).

Rules implemented (rulebook section in brackets):
  thread/record match, listed recipient, greeting matches the listed sender,
  "Hi," for shared addresses                                    [S3, S11 r5, S0 r8]
  approved template only, body equals the rendered template     [S3 2]
  links only from the record: form, upload, and on the preview email
  the approved version's fixed link                             [S3 3, S11 r5, round 5]
  no braces, no CC/BCC, no model chatter, no other clients' details [S11 r5]
  filled text 300 characters at most                            [S11 r5, S6 r6]
  client quotes: no URLs, emails, phones, sort-code/account patterns, HTML;
  120 characters; only when sender authentication passed        [S6 r10]
  signer-only lines go only to the signer                       [S11 r7]
  20-hour rule per client and per address; circuit breaker (>10 engine emails
  an hour, >1 to any client or address in 20 h); engine-labelled Sent only;
  Matt's own sends and the vacation reply never count           [S11 r4, r7]
  kill switch missing/unreadable = ON                            [S11 r10]
  8 per run, the rest carry over                                [S11 r5]
  blocked by breaker / kill switch / engine pause / carry-over / 20-hour hold
  does NOT count as a reminder; a content block does, and turns the row red
                                                                [S1 r5, S1 r11]
  red rows: only the holding line (once per trip) and the urgent-not-ours line,
  to an approved sender                                         [precedence 1]
  Manual rows, paused/On Hold rows, bounced addresses: nothing sends [S0 r4, S1]
  "sending" without "sent" for this draft: never resend          [S6 r2]
  reminder 3's date_needed never in the past                    [S1 r13]
"""
import argparse
import json
import re
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine_common import (ACCOUNT_RE, EMAIL_RE, FREE_MAIL_DOMAINS, HTML_RE, LONDON, PHONE_RE,  # noqa: E402
                           ROOT, SORT_CODE_RE, URL_RE, digits, email_domain, extract_urls, load_json,
                           norm_email, norm_ws, now_utc, parse_time)

TEMPLATES_PATH = ROOT / "templates" / "approved.json"
ITEMS_PATH = ROOT / "templates" / "missing_items.json"

LINK_FIELDS = {"form_link", "upload_link", "preview_link"}
CLIENT_QUOTE_MAX = 120
FILLED_MAX = 300
RUN_MAX = 8
BREAKER_PER_HOUR = 10
HOLD_HOURS = 20

SYSTEM_BLOCKS = {"kill_switch", "breaker", "engine_pause", "carry_over", "hold_20h"}

CHATTER = [
    r"\bas an ai\b", r"\blanguage model\b", r"\bhere(?:'s| is) (?:the|a|your) (?:draft|email|message|reply)\b",
    r"\bi hope this helps\b", r"^\s*(?:sure|certainly|of course)\b[,!.]", r"\blet me know if you(?:'d| would) like\b",
    r"\[insert", r"\bplaceholder\b", r"\bclaude\b", r"\banthropic\b", r"```", r"\btodo\b", r"\blorem ipsum\b",
    r"^\s*subject\s*:", r"\bdraft (?:email|reply|below)\b", r"\bfeel free to (?:edit|adjust)\b",
]
CHATTER_RE = [re.compile(p, re.I | re.M) for p in CHATTER]
CHANGES_LOGGED_RE = re.compile(r"^\d{1,3} changes logged(?: in your words)?$")
GREETING_RE = re.compile(r"^(?:(?:Hi|Thanks|Quick one,) )?\{first_name\}[,.:]\s*")
PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")


def load_templates(path=TEMPLATES_PATH):
    return load_json(path)["templates"]


def load_items(path=ITEMS_PATH):
    return load_json(path)


# ---------------------------------------------------------------- rendering
def _value_text(name, value):
    if name == "bullets" and isinstance(value, list):
        return "; ".join(f'"{v}"' for v in value)
    if name == "missing_items" and isinstance(value, list):
        return " ".join(str(v) for v in value)
    if value is None:
        return ""
    return str(value)


def render(template, fields, variant_id=None, shared=False):
    """Render one approved template. Used by the engine to build bodies and by
    this check to compare them, so both sides use the same words."""
    variants = template["variants"]
    var = next((v for v in variants if v["id"] == variant_id), None) if variant_id else variants[0]
    if var is None:
        raise KeyError(f"unknown variant {variant_id!r}")
    text = var["text"]
    if shared:
        # S0 r8: a shared address is greeted "Hi," (no first name).
        text = GREETING_RE.sub("Hi, ", text, count=1) if GREETING_RE.match(text) else text

    def sub(m):
        name = m.group(1)
        return _value_text(name, fields.get(name, "")) if name in fields or name == "other_files" else m.group(0)

    out = PLACEHOLDER_RE.sub(sub, text)
    out = out.replace("?.", "?").replace("..", ".")
    return out, var


def placeholders(template, variant_id=None, shared=False):
    var = next((v for v in template["variants"] if v["id"] == variant_id), None) if variant_id \
        else template["variants"][0]
    text = var["text"]
    if shared and GREETING_RE.match(text):
        text = GREETING_RE.sub("Hi, ", text, count=1)
    return PLACEHOLDER_RE.findall(text)


# ---------------------------------------------------------------- counting
def _engine_sent(sent_log):
    for e in sent_log:
        if e.get("status") == "sent" and e.get("engine_labelled") is True \
                and e.get("template_id") not in ("vacation_reply", "whatsapp_away"):
            yield e


def breaker_state(sent_log, now):
    """Return (tripped, reason) from engine-labelled Sent entries only."""
    hour_ago = now - timedelta(hours=1)
    sent = list(_engine_sent(sent_log))
    last_hour = [e for e in sent if parse_time(e["at"]) > hour_ago]
    if len(last_hour) > BREAKER_PER_HOUR:
        return True, f"circuit breaker: {len(last_hour)} engine emails in the last hour (limit {BREAKER_PER_HOUR})"
    window = now - timedelta(hours=HOLD_HOURS)
    by_client, by_addr = {}, {}
    for e in sent:
        if parse_time(e["at"]) <= window:
            continue
        by_client[e.get("record_id")] = by_client.get(e.get("record_id"), 0) + 1
        for a in e.get("to", []):
            by_addr[norm_email(a)] = by_addr.get(norm_email(a), 0) + 1
    for k, n in by_client.items():
        if n > 1:
            return True, f"circuit breaker: {n} engine emails to client {k} in 20 hours"
    for k, n in by_addr.items():
        if n > 1:
            return True, f"circuit breaker: {n} engine emails to {k} in 20 hours"
    return False, ""


def would_trip_breaker(sent_log, now):
    hour_ago = now - timedelta(hours=1)
    n = sum(1 for e in _engine_sent(sent_log) if parse_time(e["at"]) > hour_ago)
    return n + 1 > BREAKER_PER_HOUR, n


def reminders_counted(sent_log, record_id):
    """Reminders that count towards the 3: sent, or blocked for content.
    Blocks by breaker, kill switch, engine pause, carry-over or the 20-hour hold
    don't count (S1 r11)."""
    n = 0
    for e in sent_log:
        if e.get("record_id") != record_id or not str(e.get("template_id", "")).startswith("reminder_"):
            continue
        if e.get("status") == "sent":
            n += 1
        elif e.get("status") == "blocked" and e.get("block_type") == "content":
            n += 1
    return n


# ---------------------------------------------------------------- client words
def client_quote_problems(text):
    """Problems with a client quote that would be quoted back (S6 r10)."""
    probs = []
    s = str(text)
    if URL_RE.search(s):
        probs.append("contains a URL")
    if EMAIL_RE.search(s):
        probs.append("contains an email address")
    if any(len(digits(m.group(0))) >= 10 for m in PHONE_RE.finditer(s)):
        probs.append("contains a phone number")
    if SORT_CODE_RE.search(s):
        probs.append("contains a sort-code pattern")
    if ACCOUNT_RE.search(s):
        probs.append("contains an account-number pattern")
    if HTML_RE.search(s):
        probs.append("contains HTML")
    if len(s) > CLIENT_QUOTE_MAX:
        probs.append(f"over {CLIENT_QUOTE_MAX} characters ({len(s)})")
    if "{" in s or "}" in s:
        probs.append("contains braces")
    return probs


def strip_client_quote(text):
    """What the engine does before quoting client words back. The pre-send
    check still verifies the result."""
    s = HTML_RE.sub("", str(text))
    s = URL_RE.sub("", s)
    s = EMAIL_RE.sub("", s)
    s = SORT_CODE_RE.sub("", s)
    s = ACCOUNT_RE.sub("", s)
    s = PHONE_RE.sub(lambda m: "" if len(digits(m.group(0))) >= 10 else m.group(0), s)
    s = s.replace("{", "").replace("}", "")
    s = norm_ws(s)
    if len(s) > CLIENT_QUOTE_MAX:
        s = s[:CLIENT_QUOTE_MAX - 1].rstrip() + "…"
    return s


# ---------------------------------------------------------------- identifiers
def other_client_hits(text, record, records):
    hits = []
    low = (text or "").lower()
    text_digits = digits(text or "")
    mine = record.get("record_id")
    for r in records or []:
        if r.get("record_id") == mine:
            continue
        rid = r.get("record_id")
        names = [r.get("business")] + list(r.get("trading_names") or [])
        for n in names:
            if n and len(n) >= 4 and n.lower() in low:
                hits.append(f"names another client's business ({rid})")
        if rid and rid.lower() in low:
            hits.append(f"contains another record ID ({rid})")
        emails = [s.get("email") for s in r.get("approved_senders", [])] + [r.get("email"), r.get("signer_email")]
        for e in filter(None, emails):
            if norm_email(e) in low:
                hits.append(f"contains another client's email ({rid})")
            d = email_domain(e)
            if d and d not in FREE_MAIL_DOMAINS and d in low:
                hits.append(f"contains another client's domain ({rid})")
        for p in filter(None, [r.get("phone")] + list(r.get("phones") or [])):
            pd = digits(p)
            if len(pd) >= 10 and pd in text_digits:
                hits.append(f"contains another client's phone ({rid})")
        for k in ("form_link", "upload_link", "approved_preview_link", "domain"):
            v = r.get(k)
            if v and v.lower() in low:
                hits.append(f"contains another client's {k} ({rid})")
    return sorted(set(hits))


# ---------------------------------------------------------------- main check
def check(draft, sent_log=None, records=None, state=None, now=None, templates=None, items=None, mode="supervised"):
    sent_log = sent_log or []
    state = state if state is not None else {}
    templates = templates or load_templates()
    items = items or load_items()
    now = parse_time(now) if now else now_utc()
    reasons, system = [], []
    record = draft.get("record") or {}
    tid = draft.get("template_id")
    tpl = templates.get(tid)
    engine_auto = bool(tpl and tpl["kind"] == "engine_auto")
    engine_labelled = draft.get("engine_labelled", engine_auto)

    def result(decision):
        block_types = []
        if system:
            block_types = sorted(set(t for t, _ in system))
        elif reasons:
            block_types = ["content"]
        is_reminder = bool(tpl and tpl.get("reminder"))
        counts = None
        colour = None
        if decision == "BLOCK" and is_reminder:
            counts = not system and bool(reasons)
            colour = "red" if counts else None  # S1 r5; system blocks keep the row's colour (S1 r11)
        return {
            "decision": decision,
            "reasons": [r for _, r in system] + reasons,
            "block_types": block_types,
            "counts_as_reminder": counts,
            "row_colour": colour,
            "action": ("save_gmail_draft_for_matt" if decision == "ALLOW" else "do_not_draft_flag_for_matt"),
            "mode": mode,
            "template_id": tid,
            "draft_id": draft.get("draft_id"),
            "record_id": record.get("record_id"),
        }

    if mode != "supervised":
        reasons.append("only supervised mode exists until Matt's Thu 29 Oct go/no-go: drafts only")
        return result("BLOCK")

    # ---- system checks first: these never count as a reminder (S1 r11)
    ks = state.get("kill_switch")
    if ks != "off":
        system.append(("kill_switch", f"kill switch is {ks!r}: missing or unreadable counts as ON"))
    if engine_labelled:
        if state.get("engine_pauses"):
            system.append(("engine_pause", "engine-wide pause active: " + ", ".join(state["engine_pauses"])))
        if state.get("breaker_tripped"):
            system.append(("breaker", "circuit breaker is tripped (only Matt resets it)"))
        tripped, why = breaker_state(sent_log, now)
        if tripped:
            system.append(("breaker", why))
        else:
            over, n = would_trip_breaker(sent_log, now)
            if over:
                system.append(("breaker", f"this would be engine email {n + 1} this hour (limit {BREAKER_PER_HOUR})"))
        if int(state.get("run_sent_count", 0)) >= RUN_MAX:
            system.append(("carry_over", f"{RUN_MAX} engine emails already this run: carry to next run"))
        window = now - timedelta(hours=HOLD_HOURS)
        to_set = {norm_email(a) for a in draft.get("to", [])}
        for e in _engine_sent(sent_log):
            if parse_time(e["at"]) <= window:
                continue
            if e.get("record_id") == record.get("record_id"):
                system.append(("hold_20h", "engine email to this client in the last 20 hours: hold and combine"))
                break
            if to_set & {norm_email(a) for a in e.get("to", [])}:
                system.append(("hold_20h", "engine email to this address in the last 20 hours: hold and combine"))
                break
    if system:
        return result("BLOCK")

    # ---- template exists and can be an email on its own
    if not tpl:
        reasons.append(f"template {tid!r} is not on the approved list")
        return result("BLOCK")
    if tpl["kind"] not in ("engine_auto", "matt_sends"):
        reasons.append(f"template {tid!r} is a {tpl['kind']} and can't be an email on its own")
        return result("BLOCK")

    # ---- never resend
    did = draft.get("draft_id")
    if did:
        st = [e.get("status") for e in sent_log if e.get("draft_id") == did]
        if "sent" in st:
            reasons.append(f"draft {did} is already in Sent")
        elif "sending" in st:
            reasons.append(f"draft {did} says 'sending' but Sent shows nothing: flag, never resend")

    # ---- record and thread
    if not record.get("record_id"):
        reasons.append("no record on the draft")
        return result("BLOCK")
    if draft.get("thread_record_id") != record.get("record_id"):
        reasons.append(f"thread belongs to {draft.get('thread_record_id')!r}, not this record "
                       f"{record.get('record_id')!r}")
    if record.get("manual"):
        reasons.append("row tagged Manual: the engine never emails it")
    if engine_auto and (record.get("reminders_paused") or record.get("on_hold")):
        if tpl.get("reminder") or tid not in ("holding_line", "urgent_not_ours"):
            reasons.append("Reminders Paused or On Hold: nothing sends")
    if record.get("bounced"):
        reasons.append("engine email to this record bounced: all engine email to it stops")
    if record.get("colour") == "red" and not tpl.get("red_allowed"):
        reasons.append("row is red: only the holding line or the urgent-not-ours line may go")
    if tpl.get("once_per_trip"):
        if any(e.get("record_id") == record.get("record_id") and e.get("template_id") == tid
               and e.get("status") == "sent" for e in sent_log):
            reasons.append(f"{tid} already went to this client once this trip")

    # ---- recipients
    to = [norm_email(a) for a in draft.get("to", [])]
    if draft.get("cc") or draft.get("bcc"):
        reasons.append("CC or BCC present: never allowed")
    senders = {norm_email(s.get("email")): s for s in record.get("approved_senders", [])}
    recipient = None
    if len(to) != 1:
        reasons.append(f"exactly one recipient required (got {len(to)})")
    else:
        recipient = senders.get(to[0])
        if not recipient:
            reasons.append(f"{to[0]} is not a listed sender on this record")
    if recipient and tpl.get("signer_only"):
        if to[0] != norm_email(record.get("signer_email")):
            reasons.append("signer-only line: recipient is not the signer")
    shared = bool(recipient and recipient.get("shared"))

    # ---- fields and rendering
    fields = dict(draft.get("fields") or {})
    variant_id = draft.get("variant_id")
    try:
        names = placeholders(tpl, variant_id, shared)
    except Exception:
        reasons.append(f"unknown variant {variant_id!r} for {tid}")
        return result("BLOCK")
    var = next((v for v in tpl["variants"] if v["id"] == variant_id), tpl["variants"][0]) if variant_id \
        else tpl["variants"][0]
    if var.get("requires_build_status_min") and int(record.get("build_status") or 0) < var["requires_build_status_min"]:
        reasons.append("Template 5 date line only when the row is Preview ready or later")

    for n in names:
        if n == "other_files":
            continue
        if n not in fields or fields[n] in (None, "", []):
            reasons.append(f"field {{{n}}} not filled")

    # first name / greeting
    if "first_name" in names and recipient:
        if fields.get("first_name") != recipient.get("first_name"):
            reasons.append(f"greeting {fields.get('first_name')!r} doesn't match the listed sender "
                           f"{recipient.get('first_name')!r}")
    if shared and "{first_name}" in var["text"] and not draft.get("body", "").startswith("Hi,"):
        reasons.append('shared address: greeting must be "Hi,"')

    # links in fields must be the record's
    link_map = {"form_link": record.get("form_link"), "upload_link": record.get("upload_link"),
                "preview_link": record.get("approved_preview_link")}
    for n in names:
        if n in LINK_FIELDS:
            if not link_map.get(n):
                reasons.append(f"record has no {n.replace('preview_link', 'approved fixed preview link')}")
            elif fields.get(n) != link_map[n]:
                reasons.append(f"{{{n}}} isn't the record's {n}")

    # numbers and fixed facts filled by scripts
    if "n" in names and not re.fullmatch(r"\d{1,4}", str(fields.get("n", ""))):
        reasons.append("{n} must be a number filled by the script")
    if "other_files" in names:
        of = str(fields.get("other_files", "") or "")
        if of and not re.fullmatch(r", [0-9]{1,4} [a-zA-Z ,0-9]{1,60}", of):
            reasons.append("{other_files} must be empty or a count like ', 2 PDFs'")
    if "business" in names and fields.get("business") != record.get("business"):
        reasons.append("{business} isn't the record's business name")
    for dn in ("preview_date", "feedback_date", "launch_date"):
        if dn in names and record.get(dn) and fields.get(dn) != record.get(dn):
            reasons.append(f"{{{dn}}} doesn't match the row")
    if "date_needed" in names:
        iso = (draft.get("field_dates") or {}).get("date_needed")
        if not iso:
            reasons.append("{date_needed} has no machine date to check")
        else:
            from datetime import date
            try:
                if date.fromisoformat(iso) <= now.astimezone(LONDON).date():
                    reasons.append("{date_needed} is today or already passed (S1 r13)")
            except ValueError:
                reasons.append("{date_needed} machine date unreadable")
    if "a" in names or "b" in names:
        tn = record.get("trading_names") or []
        for k in ("a", "b"):
            if fields.get(k) not in tn:
                reasons.append(f"{{{k}}} isn't one of the record's trading names")

    # approved fixed lines only
    item_lines = items["items"]
    approved_shorts = {v.get("short") for v in item_lines.values() if v.get("approved") and v.get("short")}
    approved_wheres = {v.get("where") for v in item_lines.values() if v.get("approved") and v.get("where")}
    approved_still = {}
    for k, v in item_lines.items():
        if v.get("approved") and v.get("still_needed"):
            approved_still[v["still_needed"].replace("{business}", str(record.get("business", "")))] = k
    if "top_item" in names and fields.get("top_item") and fields["top_item"] not in approved_shorts:
        reasons.append(f"{{top_item}} {fields['top_item']!r} isn't an approved line")
    if "where_to_find" in names and fields.get("where_to_find") and fields["where_to_find"] not in approved_wheres:
        reasons.append(f"{{where_to_find}} {fields['where_to_find']!r} isn't an approved line")
    if "missing_items" in names and fields.get("missing_items"):
        mi = fields["missing_items"]
        mi = mi if isinstance(mi, list) else [mi]
        for line in mi:
            if line not in approved_still:
                reasons.append(f"Still needed line isn't approved: {str(line)[:60]!r}")

    # client words
    for n in tpl.get("client_words", []):
        if n not in names or n not in fields:
            continue
        val = fields[n]
        vals = val if isinstance(val, list) else [val]
        if n == "bullets" and len(vals) == 1 and CHANGES_LOGGED_RE.match(str(vals[0])):
            continue
        if draft.get("quote_source_auth") != "pass":
            reasons.append(f"{{{n}}} quotes client words but sender authentication isn't 'pass': "
                           "use '{n} changes logged'")
        for v in vals:
            for p in client_quote_problems(v):
                reasons.append(f"client quote in {{{n}}} {p}")

    # filled-text cap
    filled = sum(len(_value_text(n, fields.get(n))) for n in set(names) if n not in LINK_FIELDS)
    if filled > FILLED_MAX:
        reasons.append(f"filled text is {filled} characters (max {FILLED_MAX}): use '{{n}} changes logged'")

    # body must equal the rendered template
    body = draft.get("body", "")
    try:
        expected, _ = render(tpl, fields, variant_id, shared)
    except Exception as exc:  # pragma: no cover
        reasons.append(f"can't render template: {exc}")
        expected = None
    if expected is not None and norm_ws(body) != norm_ws(expected):
        reasons.append("body isn't the approved template word for word")

    # braces anywhere
    if "{" in body or "}" in body:
        reasons.append("braces left in the body")
    for k, v in fields.items():
        if "{" in _value_text(k, v) or "}" in _value_text(k, v):
            reasons.append(f"braces in field {k}")

    # model chatter
    for rx in CHATTER_RE:
        if rx.search(body):
            reasons.append(f"model chatter in body ({rx.pattern})")
            break

    # links: every URL in the body or link list must be a record link allowed for this template
    allowed = {link_map[k] for k in tpl.get("links", []) if link_map.get(k)}
    if tid == "preview_email" and record.get("approved_preview_link"):
        allowed.add(record["approved_preview_link"])  # round-5 fix: its own fixed link is allowed
    seen = set(extract_urls(body)) | set(draft.get("links") or [])
    for u in sorted(seen):
        if u not in allowed:
            if record.get("approved_preview_link") and u == record["approved_preview_link"]:
                reasons.append("preview link only allowed on the preview email")
            else:
                reasons.append(f"link not from this record for this template: {u}")

    # other clients
    for h in other_client_hits(body + " " + json.dumps(fields, ensure_ascii=False), record, records):
        reasons.append(h)

    return result("BLOCK" if reasons else "ALLOW")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("draft")
    ap.add_argument("--sent-log")
    ap.add_argument("--records")
    ap.add_argument("--state")
    ap.add_argument("--now")
    args = ap.parse_args(argv)
    try:
        draft = load_json(args.draft)
        sent = load_json(args.sent_log) if args.sent_log else []
        records = load_json(args.records) if args.records else []
        state = load_json(args.state) if args.state else {}
        res = check(draft, sent, records, state, args.now)
    except Exception as exc:
        print(json.dumps({"decision": "BLOCK", "reasons": [f"bad input: {exc}"], "block_types": ["input"]}))
        return 2
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["decision"] == "ALLOW" else 1


if __name__ == "__main__":
    sys.exit(main())
