---
name: reply-triage
description: Use when a prospect or client reply arrives (or Matt pastes one). Sorts each reply into Reply-Matt, Book, Not now, Not a fit, Opt-out or No reply needed, and drafts a response for Matt. Drafts only; never sends.
---
# Reply triage (AG-9 Chaser engine, reply side)

## When
A reply lands to a proposal, chaser, booking or cold email, or Matt pastes a thread. Stops the chaser sequence for that row.

## Inputs (only these)
- The whole thread, in order. If it is incomplete, say exactly what is missing.
- The Pipeline Control row (status, tier, Contact Rule).
- Approved terms: Essentials £1,800 / Launch £2,500 / Signature £3,500, deposit splits, care plan £49 a month. No VAT. Prices are in a locked test until 13 Nov 2026. If a term is not on file, ask Matt.

## Buckets
| Bucket | Meaning | Action |
|---|---|---|
| Reply-Matt | A question, objection or doubt only Matt can answer | Draft a reply; one question at most |
| Book | They want a call | Draft times for Matt to confirm; do not book |
| Not now (date) | Later, with a date or season | Set follow-up date suggestion; no chasing before it |
| Not a fit | Clear no, wrong business, or price they won't move on | Close politely; if price, flag for the Friday board review |
| Opt-out | "Stop", "remove me", "no more emails" or similar | STOP. Log it. Mark Do not contact. No reply draft except a one-line confirmation if Matt wants one |
| No reply needed | Out-of-office, thanks, auto-reply | Note it; no draft |

## Steps
1. Read the whole thread. Do not read a short positive reply as a yes: interest is not agreement.
2. Pick one bucket. If two fit, choose the safer one (Opt-out beats everything).
3. Draft per bucket in Matt's plain, short voice. Answer what they asked. Ask at most one question. If they show doubt, use a calibrated question: "What would need to be true for this to be an easy yes?" or "What's the part you're least sure about?"
4. Money: negotiate scope, not price (offer Essentials or "start with Essentials, add pages in month 2"). No discounts. One deal to refuse: no deposit and no start date means no build.
5. Never suggest texting or WhatsApp to a cold or unsolicited contact (PECR). Calls only to TPS-clear numbers.

## Output format
Table first:
```
| Row | Who | Bucket | Why (their words, quoted) | Next step | Owner | Date |
```
Then, per row, "Draft for Matt" (subject if email, body), and a "Check before sending" line listing any [ASSUMPTION] or missing term. Finish with a "Log" line for Notion that Matt pastes himself.

## Hard rules
- Drafts only. Never send, book, publish, change Notion or any record. Matt sends everything.
- Opt-out: stop all sequences for that contact, log date and wording, draft nothing further. Applies to email, calls and anything else.
- Quote their words exactly, with the thread date or review link. Never paraphrase inside quote marks.
- Never "free audit". No outcome guarantees. No invented results, proof or case studies; proof slots stay [PLACEHOLDER].
- Mark unknowns [ASSUMPTION]. If a price, date or term is not approved, say "Matt to decide" instead of filling it.
