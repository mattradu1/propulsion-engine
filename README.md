# Propulsion build engine (supervised mode)

Scripts and Claude Code setup for the website build engine in `docs/build-engine-rulebook.md`.
Read `CLAUDE.md` first. **Nothing here sends email or touches Gmail, Notion, Drive or the network.**
Every script reads JSON/files and prints JSON. Cost to run: $0 (no model calls).

```
python3 -m unittest discover -s tests     # 127 tests, all must pass
```

## How supervised mode runs today
Until Matt's Thu 29 Oct go/no-go there is no scheduled task and no Make scenario. Matt types
**"run engine"** in the project chat. Claude then does this, one client at a time, and reports one line
per client in the chat:

| # | Step | Who / what | Reads | Writes |
|---|---|---|---|---|
| 0 | Health | Claude in the project chat | kill switch, Notion fields, test reads | heartbeat line in the Engine Log (Notion) |
| 1 | Pull | Notion + Gmail connectors | Pipeline rows (not Manual), new client email, Sent | local JSON: `records.json`, `sent.json`, `state.json`, one `email.json` per message |
| 2 | Sort | `scripts/classify_inbox.py email.json --records records.json` | each new email | category, colour floor, reply route |
| 3 | Understand | model step (Haiku), one client per call, **no send/write tools** | the email text as data | fixed fields only (facts, changes, files mentioned). It may make an email redder, never greener |
| 4 | Files | Matt or Claude stages attachments into a local folder; `scripts/photo_score.py <folder> --record-id REC-… --export <clean>` | photos | scores, layout, clean JPEGs (location stripped) |
| 5 | Ready? | `scripts/readiness_check.py record.json manifest.json` | row + manifest | Ready / Missing Items / Hold / Stopped |
| 6 | Draft | `presend_check.render()` builds each body from `templates/approved.json`; `scripts/presend_check.py draft.json --sent-log sent.json --records records.json --state state.json` | each draft | ALLOW → **Gmail draft for Matt** (never sent). BLOCK → flagged with reasons |
| 7 | Build (Ready rows only, oldest deposit first, 3 max) | site-builder agent on the pinned template, then `scripts/gate_a_static.py` + browser `qa-gate-a.js` + PageSpeed | client.json, photos | preview + Gate A report |
| 8 | Record | Notion connector in the chat | results above | row fields first, **Build Status last**; Missing Items in the fixed words; one Engine Log line |
| 9 | Report | chat | — | one line per client: "{client} — {stage} — {RAG} — next — waiting on"; drafts waiting for Matt |

At launch (Matt sets Approved): `scripts/dns_guide.py` for the website-records guide; launch email,
invoice and handover pack as drafts (launch-engineer, project-manager agents).

Rules applied in the scripts (see each script's docstring for the rulebook references): the pre-send
rules (thread/record, listed sender + greeting, record-only links incl. the preview email's own fixed
link, braces, CC, model chatter, other clients, 300-character cap, client-quote stripping, signer-only,
20-hour rule, circuit breaker, kill switch, 8 per run, which blocks count as a reminder), the
Definition of Ready and S3 rules, the photo rules, the red/amber words with the step-0 exceptions, and
Gate A's static checks.

## Repo map
```
CLAUDE.md                     launch check, hard rules, supervised mode, precedence
docs/build-engine-rulebook.md the rulebook (source of every rule and draft)
templates/approved.json       approved drafts, copied by scripts/build_templates.py word for word
templates/missing_items.json  Missing Items lines; approved: false = needs Matt
scripts/presend_check.py      S3 pre-send check (+ render, strip_client_quote, reminders_counted)
scripts/readiness_check.py    Definition of Ready
scripts/photo_score.py        S1 photo scorer
scripts/classify_inbox.py     rules-only inbox first pass
scripts/gate_a_static.py      Gate A static checks on a built preview
scripts/dns_guide.py          website-records DNS guide
.claude/agents/               AG-11, 12, 14, 15, 16, 22
.claude/skills/               pre-send-check, readiness-check, photo-scorer, gate-a, dns-guide
tests/                        unittest suites + synthetic photo fixtures
```

## Needs Matt (before any of this runs unattended)
1. **Paste the real launch-check header** from `claude/claude-code-launch-check.md` into CLAUDE.md
   (this session couldn't read the project doc; the block there is rebuilt from This Week).
2. **Approve the drafted lines** in `templates/missing_items.json` (every `approved: false`: reminder
   asks, where-to-find, per-field questions) by Fri 30 Oct 12:00. Until then reminders BLOCK for content
   and rows stall amber. The rulebook's own lines (ICO, logo, PNG, photo origin, trading name) are in.
3. **Shared-address greeting:** the check drops the first name and opens with "Hi," (e.g. "Hi, these are
   saved to your project…"). Confirm that wording, or say otherwise.
4. **20 hours vs 48 hours:** This Week (19 Oct 15:37) says reminders "never two within 48h, weekdays
   09:00–17:00"; the rulebook says 1 working day apart and one engine email per client per 20 hours.
   The script uses 20 hours. Which wins?
5. **300-character cap:** counted as the total of all filled-in values except links. Confirm.
6. **Photos under 8:** treated as a Missing Item until reminder 3 has gone (or the neutral-line build
   date), then the low-photo layout builds. Confirm that reading of DoR "8+ photos" vs S2 low-photo.
7. Spend decision on Make (paid plan by 23 Oct) and the Thu 29 Oct go/no-go.

## Still to build (not in this repo yet)
- **Make scenarios:** M1 Inbox Saver (needs a paid Make plan, ~2,900 ops/month; free plan is full),
  M2 Heartbeat Watch. Needs Matt (spend) and Claude in Chrome (Matt logged in). Needs testing at 600
  files and with iPhone email.
- **Scheduled tasks:** E1 engine run, E2 watchdog, E3 Saturday pack, E4 draft maker, E5 Monday link
  check. None created: new scheduled tasks need Matt's go, and supervised mode replaces them until
  29 Oct. Needs testing: automatic approval in a scheduled run, a Google connection that lasts past
  day 7, one real send in a dry run started by Thu 22 Oct.
- **Notion fields:** Build Status stages, colour + reason, Missing Items, Reminders Paused, On Hold,
  Manual tag, approved senders (+ shared flag, signer), unique form token, draft ID, approved fixed
  preview link, run lock (run ID + time), kill switch, Engine Log database. New databases need Matt's
  approval; extend Customer Records / Pipeline Control first.
- **Glue:** a small runner that turns Notion/Gmail reads into the JSON files above (inside the chat,
  via the connectors), the model step's fixed-field schema, face/plate detection (no OpenCV cascades
  installed here: needs a model step), SVG-to-PNG offline conversion, PDF export of the DNS guide,
  Lighthouse run in the container.
- **Real tests the paper can't settle:** a messy real-world test inbox through classify → pre-send
  → photo scorer; Polish/other-language heuristics on real mail; screenshot heuristic on real phones.
