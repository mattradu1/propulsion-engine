#!/usr/bin/env python3
"""S3 Ready to build: Definition of Ready check (file 2 / OS-09 v2 + rulebook S3).

Given a client record JSON (mirror of the Notion row) and a files manifest
(file list with arrival times, plus the photo_score.py summary), returns
"Ready", "Missing Items", "Hold" (new files or facts in the last 24 hours) or
"Stopped" (red: company not Active), with the Missing Items in plain words
taken only from templates/missing_items.json.

This script reads files and prints JSON. It writes nothing to Notion; the
engine (or Matt) copies the result onto the row, Build Status last.

Usage: python3 scripts/readiness_check.py RECORD.json MANIFEST.json [--now ISO]
Exit code 0 = Ready, 1 = not Ready, 2 = bad input.
"""
import argparse
import json
import re
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine_common import ROOT, load_json, now_utc, parse_time  # noqa: E402

ITEMS_PATH = ROOT / "templates" / "missing_items.json"
COPY_FIELDS = ("team_description", "what_makes_you_different")
MIN_WORDS = 5
MIN_PHOTOS = 8
QUIET_HOURS = 24
LATE_FILES_HOURS = 72
SHORT_LINK_RE = re.compile(r"^https?://(?:share\.google|goo\.gl|maps\.app\.goo\.gl|g\.co)/", re.I)
GBP_OK_RE = re.compile(r"^https://(?:www\.)?(?:google\.[a-z.]+/maps|maps\.google\.[a-z.]+|business\.google\.com|"
                       r"g\.page/|www\.google\.[a-z.]+/search)", re.I)


def filled(v):
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def words(s):
    return len(re.findall(r"[A-Za-z0-9£'’-]+", s or ""))


def check(record, manifest, now=None, items=None):
    items = (items or load_json(ITEMS_PATH))["items"]
    now = parse_time(now) if now else now_utc()
    missing, gate_b, notes, still_needed, unapproved = [], [], [], [], []
    top_items = []
    status = None
    colour = "green"

    def miss(key, extra=None):
        it = items[key]
        line = it["plain"] + (f" ({extra})" if extra else "")
        missing.append(line)
        if it.get("client_facing"):
            if it.get("approved") and it.get("short"):
                top_items.append({"top_item": it["short"], "where_to_find": it.get("where")})
            elif not it.get("approved"):
                unapproved.append(key)

    def need_line(key):
        it = items[key]
        line = it["still_needed"].replace("{business}", record.get("business", ""))
        if it.get("approved"):
            still_needed.append(line)
        else:
            unapproved.append(key)

    # ---- hard stop first
    cs = record.get("company_status")
    if record.get("is_limited", True) and cs and cs.lower() != "active":
        return {"record_id": record.get("record_id"), "status": "Stopped", "colour": "red",
                "missing_items": [f"Companies House status is {cs}: build stops; no Ltd or number on the site; "
                                  "Matt decides who the contract is with."],
                "still_needed_lines": [], "top_item": None, "gate_b_blockers": [], "notes": [],
                "unapproved_lines": [], "build_status": None}

    if record.get("manual"):
        notes.append("Row tagged Manual: the engine reports only; no builds, reminders or confirmations.")

    # ---- Definition of Ready
    if not record.get("deposit_paid"):
        miss("deposit")
    if not record.get("agreement_signed"):
        miss("agreement_signed")
    kickoff = record.get("kickoff_done") or record.get("kickoff_form_returned") \
        or record.get("provisional_build_approved")
    if not kickoff:
        miss("kickoff")
        if record.get("kickoff_form_sent") and not record.get("kickoff_form_returned"):
            miss("kickoff_form_returned")
    if record.get("provisional_build_approved") and not (record.get("kickoff_done")
                                                         or record.get("kickoff_form_returned")):
        notes.append("Provisional build (Matt approved) without a kickoff.")
    if not record.get("onboarding_form_complete"):
        miss("onboarding_form")
    if not (filled(record.get("i_or_we")) and filled(record.get("words_you_use"))
            and filled(record.get("words_never_use"))):
        miss("voice")
    facts = ("years_in_trade", "guarantee", "training", "insurance")
    gaps = [f for f in facts if not filled(record.get(f))]
    if gaps or not record.get("facts_confirmed_in_writing"):
        miss("facts_in_writing", ", ".join(gaps) if gaps else "not confirmed in writing")
    if not (filled(record.get("areas")) and filled(record.get("areas_footer_line"))):
        miss("areas")
    elif len(record.get("areas") or []) > 15:
        notes.append("Areas list over 15 towns: main towns used, full list in the footer.")

    # photos
    summ = manifest.get("photo_summary") or manifest.get("summary") or {}
    usable = int(summ.get("usable", 0))
    labelled = int(summ.get("labelled_usable", usable if summ.get("labelled") else 0))
    neutral_ok = bool(record.get("reminder_3_sent")) or (
        record.get("neutral_build_from") and now >= parse_time(record["neutral_build_from"]))
    if labelled < MIN_PHOTOS:
        if neutral_ok:
            notes.append(f"{labelled} labelled usable photos: building the low-photo layout (reminder 3 gone "
                         "or neutral-line build date reached).")
        else:
            miss("photos", f"{labelled} labelled usable of {MIN_PHOTOS}")
    if not filled(record.get("photos_not_to_show")):
        miss("photo_exclusions")
    if int(summ.get("no_camera_data", 0)) > 0 and not record.get("photo_origin_answer_on_file"):
        need_line("photo_origin")
        notes.append("Photos with no camera data: never the hero; used only after Matt's Saturday tick "
                     "with the client's written origin answer.")

    # legal identity
    is_ltd = record.get("is_limited", True)
    office_ok = filled(record.get("registered_office")) or record.get("service_area_only") is True
    if not filled(record.get("legal_name")) or (is_ltd and not filled(record.get("company_number"))) \
            or not office_ok:
        miss("legal_identity")
    if not is_ltd:
        notes.append("Not a limited company: no 'Ltd' on the site.")

    # ICO: Gate B only
    if not filled(record.get("ico_number")) and not record.get("ico_written_result"):
        gate_b.append("ICO number or the client's written result")
        need_line("ico")

    gbp = record.get("gbp_url") or ""
    if not gbp or SHORT_LINK_RE.match(gbp) or not GBP_OK_RE.match(gbp):
        miss("gbp_url", "short link given" if SHORT_LINK_RE.match(gbp) else None)
    if not ((filled(record.get("enquiry_email")) or filled(record.get("enquiry_mobile")))
            and filled(record.get("funnel_url"))):
        miss("enquiry_routing")
    if not (filled(record.get("registrar")) and record.get("dns_call_booked")):
        miss("registrar")
    if not all(filled(record.get(k)) for k in ("preview_date", "feedback_date", "launch_date")):
        miss("dates_agreed")
    if not filled(record.get("baseline")):
        miss("baseline")

    # trading name (S3 r6)
    tn = record.get("trading_names") or []
    if len(tn) > 1 and not (filled(record.get("site_trading_name"))
                            and record.get("site_trading_name_source") == "signer_written"):
        miss("trading_name", " or ".join(tn))
        notes.append("Trading-name question goes to the signer only.")

    # under-5-word answers (S3 r7, r9)
    for f in COPY_FIELDS:
        v = record.get(f) or ""
        if words(v) < MIN_WORDS:
            if record.get("reminder_3_sent"):
                notes.append(f"'{f}' under {MIN_WORDS} words after reminder 3: approved neutral line used; "
                             "listed on Saturday.")
            else:
                miss("short_answer", f)

    # logo (non-blocking)
    if not record.get("logo_file"):
        if record.get("svg_logo_pending"):
            notes.append("SVG logo waiting for offline conversion: no logo question sent.")
        elif record.get("svg_conversion_failed"):
            need_line("logo_png")
        else:
            need_line("logo")
            notes.append("No logo file: clean text version of the business name.")

    # PENDING markers (S5 r6)
    for p in record.get("pending") or []:
        if p.get("waiting_on") == "client":
            gate_b.append(f"PENDING: {p.get('item')} (waiting on the client; neutral line on the preview)")
        else:
            notes.append(f"PENDING: {p.get('item')} (waiting on Propulsion: fails the Monday check)")

    # Gate B items that never block Ready
    for b in record.get("badges") or []:
        if not b.get("proof_number"):
            gate_b.append(f"Badge {b.get('name')}: current number naming the business or engineer")
    if record.get("domain_in_client_name") is False:
        gate_b.append("Domain not in the client's name: transfer plan")

    # ---- decide
    if missing:
        status = "Missing Items"
        colour = "amber"
    else:
        times = [parse_time(f["arrived_at"]) for f in manifest.get("files", []) if f.get("arrived_at")]
        if record.get("last_fact_update"):
            times.append(parse_time(record["last_fact_update"]))
        latest = max(times) if times else None
        if latest and now - latest < timedelta(hours=QUIET_HOURS):
            hold_since = record.get("ready_hold_since")
            if hold_since and now - parse_time(hold_since) >= timedelta(hours=LATE_FILES_HOURS):
                status = "Ready"
                notes.append("Late files: built with what's there after 72 hours of new arrivals.")
            else:
                status = "Hold"
                colour = "amber"
                notes.append(f"New files or facts in the last {QUIET_HOURS} hours (latest {latest.isoformat()}): "
                             "not Ready yet.")
        else:
            status = "Ready"
    if unapproved:
        notes.append("Lines not yet approved by Matt (row stalls amber until approved): "
                     + ", ".join(sorted(set(unapproved))))
        if status != "Ready":
            colour = "amber"

    return {
        "record_id": record.get("record_id"),
        "status": status,
        "build_status": 3 if status == "Ready" else None,
        "colour": colour,
        "missing_items": missing,
        "still_needed_lines": still_needed,
        "top_item": top_items[0] if top_items else None,
        "gate_b_blockers": gate_b,
        "notes": notes,
        "unapproved_lines": sorted(set(unapproved)),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Definition of Ready check")
    ap.add_argument("record")
    ap.add_argument("manifest")
    ap.add_argument("--now")
    a = ap.parse_args(argv)
    try:
        res = check(load_json(a.record), load_json(a.manifest), a.now)
    except Exception as exc:
        print(json.dumps({"status": "Missing Items", "missing_items": [f"bad input: {exc}"]}))
        return 2
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["status"] == "Ready" else 1


if __name__ == "__main__":
    sys.exit(main())
