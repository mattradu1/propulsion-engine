---
name: readiness-check
description: Use on "intake {client}", after new files or facts arrive, and in every engine run, to decide if a client is Ready to build (Definition of Ready + S3 rules) and to write Missing Items in plain words from the approved list.
---
# Readiness check (file 2 Definition of Ready, rulebook S3)

## Run
```
python3 scripts/readiness_check.py record.json manifest.json --now 2026-11-03T12:00:00+00:00
```
- `record.json`: the Notion row mirrored as JSON (deposit_paid, agreement_signed, kickoff_done,
  kickoff_form_sent/returned, provisional_build_approved, onboarding_form_complete, i_or_we,
  words_you_use, words_never_use, years_in_trade, guarantee, training, insurance,
  facts_confirmed_in_writing, areas, areas_footer_line, photos_not_to_show, legal_name, company_number,
  registered_office or service_area_only, is_limited, company_status, ico_number, gbp_url,
  enquiry_email/mobile, funnel_url, registrar, dns_call_booked, preview/feedback/launch_date, baseline,
  trading_names, site_trading_name(+_source "signer_written"), team_description,
  what_makes_you_different, reminder_3_sent, pending [{item, waiting_on}], last_fact_update,
  ready_hold_since, logo_file, svg_logo_pending, badges).
- `manifest.json`: {"files": [{name, arrived_at}], "photo_summary": the photo-scorer `summary`}.
Exit 0 = Ready, 1 = not Ready.

## Reading the result
- `Ready` → Build Status 3 (written last on the row).
- `Missing Items` → copy `missing_items` onto the row as written. `top_item` and `still_needed_lines`
  are the only words that may go into a reminder or Template 1.
- `Hold` → files or facts arrived in the last 24 hours; check again next run (after 72 hours of
  arrivals it builds with what's there, "late files").
- `Stopped` → red (company not Active). Build stops; Matt decides.
- `unapproved_lines` → those rows stall amber until Matt approves the line in
  `templates/missing_items.json` (S1 r7). Never invent a line.
- `gate_b_blockers` (ICO, client-waiting PENDING, badges, domain ownership) never block Ready.

Tests: `python3 -m unittest tests/test_readiness_check.py`.
