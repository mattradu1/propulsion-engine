#!/usr/bin/env python3
"""Gate A, static part (S5 + OS-09 v2 Gate A). Reads a built preview folder
(dist/) and the client's client.json; never edits anything. Report only.

What it checks on every .html page:
  preview banner "Preview – not live" and a robots noindex meta tag
  one H1, a <main> landmark, every <img> has alt, width and height
  no placeholders ({, [TO BE SUPPLIED], TBC, lorem); "PENDING: {item}" = amber
  no script/iframe/event handlers/javascript: links; scripts only from the
  allow list; no Tailwind CDN or Google Fonts
  every tel: link dials the client's phone
  banned comparisons (best, No.1, cheapest, guaranteed results) fail;
  "free", "24/7", "guarantee" are amber unless on the client's approved claims
  claims about other firms ("cowboys", "unlike other") fail
  review quotes (<blockquote>) are word for word from client.json reviews
  another client's phone, email or domain fails (site quarantined); a name-only
  match is amber
What it can't check (still on the browser pane / Matt): PageSpeed, real
phone-width tap test, keyboard pass, test enquiry within 5 minutes, the
X-Robots-Tag header (host config), facts against the record beyond phone.

Usage: python3 scripts/gate_a_static.py DIST_DIR CLIENT_JSON [--records RECORDS.json]
Exit 0 = pass (amber allowed), 1 = fail.
"""
import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine_common import FREE_MAIL_DOMAINS, digits, email_domain, load_json, norm_ws  # noqa: E402

BANNER = re.compile(r"Preview\s*[–-]\s*not live", re.I)
PLACEHOLDER = re.compile(r"\{[^}]*\}|\[[A-Z][A-Z _\-]{2,}\]|TO BE SUPPLIED|\bTBC\b|lorem ipsum", re.I)
PENDING = re.compile(r"PENDING:\s*([^<\n]{1,80})")
COMPARISON = re.compile(r"\b(?:the best|best in|no\.? ?1|number one|cheapest|guaranteed results|lowest prices?)\b",
                        re.I)
SOFT_CLAIMS = re.compile(r"\b(?:free|24/7|guarantee[ds]?)\b", re.I)
OTHER_FIRMS = re.compile(r"\b(?:cowboys?|unlike other|other firms|other companies|the competition)\b", re.I)
SCRIPT_ALLOW = re.compile(r"^/(?!/)")  # same-site scripts only


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1 = 0
        self.main = 0
        self.imgs = []
        self.tels = []
        self.scripts = []
        self.iframes = 0
        self.handlers = []
        self.js_links = 0
        self.robots = []
        self.styles = []
        self.text = []
        self.quotes = []
        self._in_quote = 0
        self._q = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in a:
            if k.lower().startswith("on"):
                self.handlers.append(f"{tag} {k}")
        if tag == "h1":
            self.h1 += 1
        elif tag == "main":
            self.main += 1
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "a":
            href = a.get("href") or ""
            if href.lower().startswith("javascript:"):
                self.js_links += 1
            if href.lower().startswith("tel:"):
                self.tels.append(href)
        elif tag == "script":
            self.scripts.append(a)
            self._in_script = True
        elif tag == "iframe":
            self.iframes += 1
        elif tag == "meta" and (a.get("name") or "").lower() == "robots":
            self.robots.append(a.get("content") or "")
        elif tag == "link" and (a.get("rel") or "").lower() == "stylesheet":
            self.styles.append(a.get("href") or "")
        elif tag == "blockquote":
            self._in_quote += 1
        if tag == "style":
            self._in_script = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._in_script = False
        if tag == "blockquote" and self._in_quote:
            self._in_quote -= 1
            if not self._in_quote:
                self.quotes.append(norm_ws("".join(self._q)))
                self._q = []

    def handle_data(self, data):
        if self._in_script:
            return
        self.text.append(data)
        if self._in_quote:
            self._q.append(data)


def quote_ok(quote, reviews):
    q = quote.strip().strip("\"“”")
    parts = [p.strip(" .\"“”") for p in q.split("…") if p.strip(" .\"“”")]
    for r in reviews:
        t = norm_ws(r.get("text", ""))
        if parts and all(p in t for p in parts):
            return True
    return False


def check(dist, client, records=None):
    fails, ambers = [], []
    dist = Path(dist)
    pages = sorted(dist.rglob("*.html"))
    if not pages:
        return {"result": "FAIL", "fails": ["no HTML pages in the build"], "ambers": []}
    phone = digits(client.get("phoneE164") or client.get("phone") or "")
    approved_claims = [c.lower() for c in client.get("claimsApproved", [])]
    reviews = client.get("reviews", [])
    mine = {client.get("recordId"), client.get("businessName")}
    for p in pages:
        rel = p.relative_to(dist).as_posix()
        html = p.read_text(encoding="utf-8", errors="replace")
        pg = Page()
        pg.feed(html)
        text = norm_ws(" ".join(pg.text))
        is_404 = p.name == "404.html"
        if not BANNER.search(text):
            fails.append(f"{rel}: 'Preview – not live' banner missing")
        if not any("noindex" in r.lower() for r in pg.robots):
            fails.append(f"{rel}: no robots noindex meta tag")
        if pg.h1 != 1 and not is_404:
            fails.append(f"{rel}: {pg.h1} H1s (needs exactly one)")
        if not pg.main:
            fails.append(f"{rel}: no <main> landmark")
        for im in pg.imgs:
            src = im.get("src", "?")
            if "alt" not in im:
                fails.append(f"{rel}: image without alt ({src})")
            if not im.get("width") or not im.get("height"):
                fails.append(f"{rel}: image without width/height ({src})")
        for m in PLACEHOLDER.finditer(text):
            fails.append(f"{rel}: placeholder {m.group(0)!r}")
        for m in PENDING.finditer(text):
            ambers.append(f"{rel}: PENDING marker ({m.group(1).strip()}): fails the Monday check and Gate B")
        for s in pg.scripts:
            t = (s.get("type") or "").lower()
            src = s.get("src")
            if t == "application/ld+json":
                continue
            if not src:
                fails.append(f"{rel}: inline script")
            elif not SCRIPT_ALLOW.match(src):
                fails.append(f"{rel}: script from another domain ({src})")
            if src and "tailwind" in src.lower():
                fails.append(f"{rel}: Tailwind CDN")
        for st in pg.styles:
            if st.startswith("http") or st.startswith("//"):
                fails.append(f"{rel}: stylesheet from another host ({st})")
        if "fonts.googleapis.com" in html or "fonts.gstatic.com" in html:
            fails.append(f"{rel}: Google Fonts request")
        if pg.iframes:
            fails.append(f"{rel}: iframe")
        for h in pg.handlers:
            fails.append(f"{rel}: event handler ({h})")
        if pg.js_links:
            fails.append(f"{rel}: javascript: link")
        for t in pg.tels:
            if digits(t[4:]) != phone:
                fails.append(f"{rel}: tel link {t} doesn't dial the client's number")
        for m in COMPARISON.finditer(text):
            fails.append(f"{rel}: banned comparison {m.group(0)!r}")
        for m in SOFT_CLAIMS.finditer(text):
            w = m.group(0).lower()
            if not any(w in c for c in approved_claims):
                ambers.append(f"{rel}: claim word {m.group(0)!r} not on the approved claims list: flag for Matt")
        for m in OTHER_FIRMS.finditer(text):
            fails.append(f"{rel}: claim about other firms {m.group(0)!r}")
        for q in pg.quotes:
            if q and not quote_ok(q, reviews):
                fails.append(f"{rel}: review quote not word for word: {q[:60]!r}")
        low = html.lower()
        hdig = digits(re.sub(r"<[^>]+>", " ", html))
        for r in records or []:
            if r.get("record_id") in mine or r.get("business") in mine:
                continue
            rid = r.get("record_id")
            for ph in filter(None, [r.get("phone")] + list(r.get("phones") or [])):
                if len(digits(ph)) >= 10 and digits(ph) in hdig:
                    fails.append(f"{rel}: another client's phone ({rid}): hard fail, quarantine, red")
            for e in [s.get("email") for s in r.get("approved_senders", [])] + [r.get("email")]:
                if e and e.lower() in low:
                    fails.append(f"{rel}: another client's email ({rid}): hard fail, quarantine, red")
                d = email_domain(e or "")
                if d and d not in FREE_MAIL_DOMAINS and d in low:
                    fails.append(f"{rel}: another client's domain ({rid}): hard fail, quarantine, red")
            if r.get("business") and r["business"].lower() in low:
                ambers.append(f"{rel}: another client's name appears ({rid}): name-only match, amber")
    return {"result": "FAIL" if fails else "PASS", "pages": len(pages), "fails": fails, "ambers": ambers,
            "not_checked_here": ["PageSpeed (pagespeed.web.dev or local Lighthouse)", "phone-width tap test",
                                 "keyboard pass", "test enquiry within 5 minutes", "X-Robots-Tag header",
                                 "every line traceable to the client's own words (model + Matt)"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Gate A static checks")
    ap.add_argument("dist")
    ap.add_argument("client_json")
    ap.add_argument("--records")
    a = ap.parse_args(argv)
    res = check(a.dist, load_json(a.client_json), load_json(a.records) if a.records else [])
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
