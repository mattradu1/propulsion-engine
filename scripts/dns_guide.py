#!/usr/bin/env python3
"""S4 / S10 DNS guide: a personalised, plain-English guide for the client's
registrar, website records only. Never nameservers, never email records
(MX, SPF/DKIM/DMARC TXT). Output is Markdown (and optional HTML) for Matt to
check and send; PDF export is still to do (needs testing: print the HTML from
Chromium).

The hosting values (where the records point) must come from the chosen host's
own dashboard; this script refuses to invent them.

Usage: python3 scripts/dns_guide.py GUIDE.json [--html OUT.html]
GUIDE.json: {"business", "first_name", "domain", "registrar",
             "records": [{"type": "A"|"AAAA"|"CNAME", "host": "@"|"www", "value": "..."}],
             "delegate_access": false, "has_dns_screenshot": false}
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine_common import load_json  # noqa: E402

ALLOWED_TYPES = {"A", "AAAA", "CNAME"}
ALLOWED_HOSTS = {"@", "www"}
# Where each registrar keeps DNS. These are pointers, not tested click paths: check against the
# registrar's own help page before sending (needs testing).
REGISTRAR_HINT = {
    "123-reg": "In your 123-reg control panel, open the domain, then its DNS settings ('Manage DNS').",
    "godaddy": "In your GoDaddy account, open My Products, then the domain's DNS ('Manage DNS').",
    "ionos": "In your IONOS account, open Domains & SSL, then the domain's DNS settings.",
    "namecheap": "In your Namecheap account, open Domain List, then 'Manage' and 'Advanced DNS'.",
    "cloudflare": "In your Cloudflare dashboard, open the domain, then DNS, then Records.",
    "squarespace": "In your Squarespace Domains dashboard, open the domain, then DNS settings.",
    "wix": "Wix domain: Wix's route must be tested before launch (rule S0). Book the DNS call as the backup.",
}


class GuideError(ValueError):
    pass


def validate(g):
    for k in ("business", "domain", "registrar", "records"):
        if not g.get(k):
            raise GuideError(f"missing {k}")
    if not re.fullmatch(r"(?:[a-z0-9-]+\.)+[a-z]{2,}", g["domain"].lower()):
        raise GuideError(f"domain {g['domain']!r} doesn't look like a domain")
    for r in g["records"]:
        t = str(r.get("type", "")).upper()
        if t not in ALLOWED_TYPES:
            raise GuideError(f"{t} records are never touched: website records (A, AAAA, CNAME) only")
        if r.get("host") not in ALLOWED_HOSTS:
            raise GuideError(f"host {r.get('host')!r}: only @ and www")
        v = str(r.get("value", ""))
        if not v or re.search(r"[{}\[\]<>]|example|tbc|todo", v, re.I):
            raise GuideError(f"record value {v!r} isn't a real value from the host's dashboard")


def build(g):
    validate(g)
    reg = g["registrar"]
    hint = REGISTRAR_HINT.get(reg.lower().replace(" ", ""), f"In your {reg} account, find the domain's DNS "
                                                             "settings (sometimes called 'DNS zone' or 'Manage DNS').")
    lines = [f"# Putting {g['domain']} live: website records only", "",
             f"For {g['business']}. Prepared by Propulsion. This changes where your website points. "
             "It does not touch your email.", ""]
    if g.get("delegate_access"):
        lines += ["Your registrar lets you give Propulsion delegate access. If you've done that, Matt makes "
                  "these changes and screenshots your current settings first: you don't need to do anything "
                  "below.", ""]
    lines += ["## Before you start", "",
              "1. Take a screenshot of your current DNS settings page and email it to Matt. "
              "Nothing changes until he has it." if not g.get("has_dns_screenshot") else
              "1. Matt already has a screenshot of your current settings.",
              "2. Don't change nameservers.",
              "3. Don't change or delete any MX or TXT records: they run your email.", "",
              "## Where to go", "", hint, "", "## The records to set", "",
              "| Type | Host / Name | Value |", "|---|---|---|"]
    for r in g["records"]:
        lines.append(f"| {r['type'].upper()} | {r['host']} | {r['value']} |")
    lines += ["", "If a record with the same type and host already exists, edit it to the value above. "
              "Leave everything else exactly as it is.", "",
              "## After", "", "Changes can take up to 48 hours. If it isn't pointing after 48 hours, Matt "
              "checks and calls you.", ""]
    return "\n".join(lines)


def to_html(md):
    out = ["<!doctype html><meta charset='utf-8'><title>DNS guide</title><body style='font-family:sans-serif;"
           "max-width:720px;margin:2rem auto;line-height:1.5'>"]
    for ln in md.split("\n"):
        e = html.escape(ln)
        if ln.startswith("# "):
            out.append(f"<h1>{e[2:]}</h1>")
        elif ln.startswith("## "):
            out.append(f"<h2>{e[3:]}</h2>")
        elif ln.startswith("|") and not ln.startswith("|---"):
            cells = [html.escape(c.strip()) for c in ln.strip("|").split("|")]
            out.append("<div>" + " · ".join(f"<code>{c}</code>" for c in cells) + "</div>")
        elif ln.strip() and not ln.startswith("|---"):
            out.append(f"<p>{e}</p>")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Personalised DNS guide (website records only)")
    ap.add_argument("guide")
    ap.add_argument("--html")
    a = ap.parse_args(argv)
    try:
        md = build(load_json(a.guide))
    except GuideError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    print(md)
    if a.html:
        Path(a.html).write_text(to_html(md), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
