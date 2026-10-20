---
name: pre-send-check
description: Run before saving ANY client-facing email as a Gmail draft (reminders, Templates 1-5, holding line, security line, preview email, nudges, approval and signer-only questions). Returns ALLOW or BLOCK with reasons. Blocks by default.
---
# Pre-send check (rulebook S3, S11)

## When
Before every draft the engine or an agent makes for a client. In supervised mode ALLOW means only "may
be saved as a Gmail DRAFT for Matt". Nothing is ever sent from here.

## Build the body with the script, never by hand
```python
import sys; sys.path.insert(0, "scripts")
import presend_check as pc
t = pc.load_templates()["reminder_1"]
body, _ = pc.render(t, fields)            # variant_id="still_needed" for template_1, etc.
```
Client words quoted back (Template 3 bullets, Template 4 fact) go through `pc.strip_client_quote()`
first, and only when the sender's authentication was "pass"; otherwise use "{n} changes logged".

## Run
```
python3 scripts/presend_check.py draft.json --sent-log sent.json --records records.json \
    --state state.json --now 2026-11-02T10:00:00+00:00
```
- `draft.json`: draft_id, to [one address], cc, bcc, thread_record_id, record (the row: record_id,
  business, signer_email, approved_senders [{email, first_name, shared}], form_link, upload_link,
  approved_preview_link, dates, colour, build_status, manual, reminders_paused, on_hold, bounced,
  trading_names), template_id, variant_id, fields, field_dates {date_needed: ISO}, body, links,
  quote_source_auth.
- `sent.json`: Gmail Sent as a list: draft_id, record_id, to, template_id, engine_labelled, status
  (sent / sending / blocked), block_type, at. Only engine-labelled "sent" rows count for the 20-hour
  rule and the breaker; Matt's own sends and the vacation reply never count.
- `state.json`: {"kill_switch": "off", "breaker_tripped": false, "engine_pauses": [], "run_sent_count": n}.
  Missing or unreadable kill switch = ON.
Exit 0 ALLOW, 1 BLOCK, 2 bad input (also a block).

## Reading the result
- `block_types` `content`: the draft is wrong. For a reminder it still counts towards the 3 and the
  row goes red (`counts_as_reminder: true`, `row_colour: red`).
- `kill_switch`, `breaker`, `engine_pause`, `carry_over`, `hold_20h`: not the draft's fault. Doesn't
  count as a reminder; the row keeps its colour; re-plan next run (carry over, oldest first).
- Log every result to the Engine Log line for the run, and write "sending {id}" before / "sent {id}"
  after when Matt sends.

Never edit the wording to make it pass. Never bypass a BLOCK. Tests:
`python3 -m unittest tests/test_presend_check.py`.
