---
name: trade-buyer-brief
description: Use each evening for the next day's call list (AG-3 Briefer). Builds a short pre-call brief for each trade prospect from their own website and their own customer reviews, quoted word for word with links. Drafts only; never contacts anyone.
---
# Trade buyer brief (AG-3 Briefer)

## When
Evening before dial day, for each row on tomorrow's list. Also on request for one prospect. Output is a draft for Matt to read before calling.

## Inputs (only these)
- The Pipeline Control row (audit fields, Contact Rule, TPS status).
- Their own website pages you can actually open.
- Their public customer reviews you can actually open (Google, Facebook, Checkatrade, Trustpilot).
- The OS-01 call card questions.
If you cannot open a source, say so. Do not guess what it says.

## Steps
1. Skip and flag any row marked TPS Registered, Do not contact, existing client, or an agency or directory.
2. From their site, find 1-2 facts you can verify (for example, no clear enquiry route, a form that goes nowhere, a phone number only). Note the page URL.
3. From their reviews, find what their customers say mattered: speed, tidy work, communication, price honesty, turning up. Pick one short quote, word for word, with the review link and the date shown on it. Need at least 3 public reviews to call something a pattern; otherwise give the quote with no pattern claim.
4. Pair each fact with one OS-01 question.
5. Anything you could not check is marked [ASSUMPTION].

## Output format (one block per prospect)
```
Business: {name} | Row: {Pipeline Control id}
Fact: {true thing} ({page URL})
Their customers say: "{exact words}" ({review link}, {date})
Ask: {OS-01 question}
Unknowns: [ASSUMPTION] ...
```
If nothing is verifiable: `No fact — open with question 3 (what happens after an enquiry)`.

## Hard rules
- Drafts only. Never send, post, call, text, email or edit Notion.
- Quote reviews word for word with the source link. Never reword, merge or trim to change the meaning.
- A review is a prompt for a question. It is not proof of anything Propulsion has done and never goes into public copy.
- Never estimate. No industry percentages. No invented results, years trading or names.
- Never "free audit" or "free check" wording. No outcome guarantees.
- Mark every unknown [ASSUMPTION]. Proof slots stay [PLACEHOLDER].
- Report back: how many briefs, how many "No fact", which sources could not be opened.
