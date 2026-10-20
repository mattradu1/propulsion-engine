---
name: dns-guide
description: Use when Matt marks a client Approved and the registrar has no delegate access, to produce the client's personalised DNS guide (website records only) for Matt to check and send. Never nameservers, never email records.
---
# DNS guide (rulebook S4 machine, S10)

## When
Matt has set Approved (naming the version), the host's record values are known from the host's own
dashboard, and the client's registrar doesn't offer delegate access. With delegate access the client
grants it and Matt changes the records himself; no guide needed.

## Run
```
python3 scripts/dns_guide.py guide.json --html guide.html
```
`guide.json`: {"business", "first_name", "domain", "registrar", "records": [{"type": "A"|"AAAA"|"CNAME",
"host": "@"|"www", "value": "<from the host dashboard>"}], "delegate_access": false,
"has_dns_screenshot": false}

The script REFUSES (exit 1) MX, TXT, NS or any other record type, hosts other than @ and www, and
placeholder values. It never invents values.

## Then
- Matt checks the guide against the registrar's own help page (registrar click paths: needs testing)
  and sends it himself with the launch email draft.
- No screenshot of their current DNS: nothing changes until they send one.
- Not pointing after 48 hours: Matt checks and calls.
- PDF: print the HTML to PDF from Chromium (needs testing). Lookups of live DNS/SPF/DKIM/DMARC are
  blocked from both shells: needs testing elsewhere.
Tests: `python3 -m unittest tests/test_dns_guide.py`.
