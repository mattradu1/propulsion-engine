"""Shared helpers for the Propulsion engine scripts. Standard library only.

Times: every stored time is ISO 8601 with an offset; gaps are worked out in
UTC, calendar days in London time (S11 r2).
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
LONDON = ZoneInfo("Europe/London")

FREE_MAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "hotmail.co.uk", "live.com",
    "live.co.uk", "msn.com", "icloud.com", "me.com", "mac.com", "yahoo.com", "yahoo.co.uk",
    "aol.com", "btinternet.com", "sky.com", "talktalk.net", "virginmedia.com", "protonmail.com",
    "proton.me", "gmx.com", "mail.com",
}

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"'()\[\]]+", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
# UK-ish and international phone numbers: 10+ digits with optional spaces, dashes, brackets, +44.
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().\-]{8,}\d)")
SORT_CODE_RE = re.compile(r"\b\d{2}[-\s]\d{2}[-\s]\d{2}\b")
ACCOUNT_RE = re.compile(r"\b\d{8}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
HTML_RE = re.compile(r"<\s*/?\s*[A-Za-z][^>]*>|&[a-z]+;|&#\d+;", re.I)


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_time(value):
    """ISO string -> aware UTC datetime. Naive times are refused (no guessing)."""
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"time without offset: {value!r}")
    return dt.astimezone(timezone.utc)


def now_utc():
    return datetime.now(timezone.utc)


def norm_email(addr):
    return (addr or "").strip().lower()


def email_domain(addr):
    a = norm_email(addr)
    return a.split("@", 1)[1] if "@" in a else ""


def digits(s):
    d = re.sub(r"\D", "", s or "")
    if d.startswith("44") and len(d) >= 11:
        d = "0" + d[2:]
    return d


def extract_urls(text):
    out = []
    for m in URL_RE.finditer(text or ""):
        u = m.group(0).rstrip(".,;:!?")
        out.append(u)
    return out


def norm_ws(text):
    return re.sub(r"\s+", " ", (text or "")).strip()
