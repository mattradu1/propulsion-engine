---
name: gate-a
description: Use before any preview can be marked Preview ready (Build Status 6), on the Monday 06:00 light rerun, and on the live domain at launch. Runs the static Gate A script, then the browser QA script and PageSpeed. Report only.
---
# Gate A (OS-09 v2, rulebook S5)

## 1. Static checks (this repo)
```
python3 scripts/gate_a_static.py <preview dist folder> clients/<slug>/client.json --records records.json
```
`records.json` = every other client's record (for the cross-client check). Exit 0 = pass (ambers
allowed), 1 = fail. Fails: banner or noindex missing, not one H1, no `<main>`, image without
alt/width/height, placeholders, inline/foreign scripts, iframes, event handlers, javascript: links,
Tailwind CDN or Google Fonts, wrong tel number, banned comparisons, claims about other firms, review
quotes not word for word, another client's phone/email/domain (hard fail: quarantine, red). Ambers:
PENDING markers, "free"/"24/7"/"guarantee" not on the approved claims list, another client's name only.

## 2. Browser script (project doc `qa-gate-a.js`)
In the browser pane on every page of the preview, after setting
`window.QA_CFG = {phone, gbpPhone, routes, reviewTexts}` (verbatim reviews from client.json).

## 3. By hand / needs testing
- PageSpeed at pagespeed.web.dev (API blocked from both shells) or local Lighthouse: performance ≥ 85,
  LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms, accessibility ≥ 95. Can't run: "PageSpeed pending" on Saturday.
- Phone width first: tap-to-call, thumb-fillable form, readable hero; keyboard pass.
- Test enquiry to Propulsion's test inbox within 5 minutes, source recorded.
- X-Robots-Tag noindex header on the host.

## Outcome
All pass: Build Status 6 (last). Technical fail: one automatic fix, rerun, then QA failed. Report
says what was checked and what wasn't. Never edit the site from this skill.
Tests: `python3 -m unittest tests/test_gate_a_static.py`.
