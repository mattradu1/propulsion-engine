# Build Engine Rulebook (source text)
Live page: https://claude.ai/artifact/NJA5aGyJeD4Qg69qxwLm8p · Design only, nothing live. Companion to build-engine-v1, build-engine-away-mode, build-engine-500.
295 rules · 14 review rounds · flags: [auto] = sends with no human, [test] = needs testing.

## Review rounds
- Round 1 (16:03): 120 rules drafted from the build engine, away mode and 500-client docs.
- Round 2 (16:07): an independent machine-failure review found 40 issues: double runs, half-saved files, a watchdog that dies with the engine, test enquiries reaching clients, spoofed fact changes. All merged; 20 new rules, 20 fixed.
- Round 3 (16:09): an independent tradesperson review found 45 issues: WhatsApp as the main channel, iCloud users stuck on Google sign-in, signature logos counted as photos, proud owners insulted by the 'your own jobs?' question, 'looks good mate' treated as approval. All merged.
- Round 4: an independent consistency audit of the merged set found 40 issues: 3 rules that broke the 'only approved messages' rule (invoice chases, free-written asks, a preview date promised before anything was built), a circuit breaker that your own Monday sends would trip, a Google connection expiring mid-trip, Darren's SiteDrop row being swept into the engine, 6 duplicates and 12 conflicts. All merged; the 'sends with no human' flag now means exactly that.
- Round 4 also adds: the Make blocker (free plan full), the three photo-edit levels (tidy, restyle with written yes, never generate), and the machine: every automation, a one-client walk-through and every draft.
- Round 5: 10 made-up clients walked through hour by hour. As written, 0 of 10 reached "press send" cleanly: the pre-send check blocked every preview email's own link. It also found a silent client who never went red, Google Photos links that never opened, false ENGINE DOWN alarms every night, a 2am half-count confirmation, and an angry client hearing nothing for 4 days. 30 fixes merged; the example timeline corrected.
- Round 6: 10 harder made-up clients. 1 of 10 clean; the round-5 fixes held, and the 9 failures were all new edge cases: a husband-and-wife clash, one-word replies switching reminders off, "cancel the call" and "send me an invoice" wrongly going red, a defamatory line about a competitor, AI-made 'photos', iCloud addresses, two trading names, an early payment billed twice, and ICO markers pulling drafts on send day. 19 fixes merged.
- Round 7: the 10 round-6 clients re-run plus 5 new mixed-behaviour clients: 4 of 15 clean. Every failure was a gap between rules (which rule wins, who counts as the signer, lines missing from the approved list); none broke a hard limit, nothing went live, silence never counted as approval. 18 fixes merged, including an order of precedence for when rules disagree.
- Round 8a: 12 client types nobody had tried (mum's email, franchisee, 40-minute voice note, enquiry-only, Dublin firm, Polish replies, accountant replying, dissolved company, 'remove my bad review', only in-progress photos, owner falls ill, double deposit). 1 of 12 clean. Main lesson: the signer has to be a person, not an email address. 12 fixes merged.
- Round 8b: a 500-client operations review (month 6, 40 new a month, still solo). As written that's about 55 hours a week of your time on top of dialling; with its 15 fixes about 20 (its estimate, not measured). Added as a new stage, "At 500 clients": each one needs your go, and launch stays yours.
- Round 9: every client that failed in rounds 7 and 8, re-run: 12 of 22 clean, and none of the 10 failures broke a hard limit. Main fix: "red wins" was overriding the exceptions written into the red-word rule (a cancelled call, a payment made), so exceptions now apply first, and red never allows a send. Shared family addresses get a phone-confirmation route. The machine was re-synced with the rules.
- Round 10: a security and abuse review. Biggest: hidden instructions inside a PDF, photo text or form answer reaching a model that could send email; spoofed client emails; quoted client words used for invoice fraud from your own account; the vacation reply telling scammers your inbox is unwatched; script tags in form answers going onto previews; no deletion schedule for customers' photos. 14 fixes merged: client text never reaches a step that can send, and every outgoing word goes through scripts.
- Round 11: round 9's 10 failures re-run plus 5 nasty overlaps: 7 of 15 clean, none broke a hard limit. Found: a spoofed email with no domain records passing as genuine, the English holding line going to an unread Polish email, the circuit breaker burning everyone's reminders, an SVG logo stuck in quarantine, late-Friday signers with 1 minute to kick off. 10 fixes merged; the Inbox Saver re-synced.
- Round 12: a build-feasibility review against your real diary (dial blocks, 22 signings this week). Verdict: the full engine can't be built and proven by Fri 30 Oct; a minimum safe engine can. Day-by-day plan, the minimum set and the Thu 29 Oct go/no-go added at the top.
- Round 13 (in chat, 16:40): 5 test clients run with you: slow form filler, terrible photos, no logo file, Make running out mid-trip, a hacked old site. 2 of 5 clean. Found: reminder 3's deadline already in the past, no approved logo question, the Make alarm dying with Make, no answer for urgent problems that aren't ours. 5 fixes merged.
- Round 14: final re-test of 13 previous failures, including your 5 chat clients: 9 of 13 clean, none broke a hard limit. Last 4 fixed: a real client's own small domain failing authentication, the PNG logo line missing from the approved list, a quiet inbox looking like 'Make down', and the security line for a hacked old site being blocked by 'red wins'. 9 rules added.
- What paper reviews can't settle: three real tests before Fri 30 Oct. (1) A full unattended dry run with one real send, started by Thu 22 Oct so the Google connection is proven on day 8. (2) The file saver on upgraded Make with 600 files and iPhone emails. (3) A messy test inbox through the sorter, pre-send check and photo scorer.

## The machine
### M1 Inbox Saver (Make scenario)
Runs: Every 15 minutes: new email from an approved client sender with attachments, plus new files in the upload route
1. Check the sender is on a client record (exact address) AND Gmail's authentication result is "pass"; otherwise Unsorted
2. For each attachment: photos, PDFs, audio and video → Clients/{record ID}/Inbox, named record ID + hash; SVG, HTML, XML, zips and mismatched files → Quarantine
3. Skip signature images under the minimum size
4. Apply the Gmail label "Saved" last, only once every file is in Drive
5. Write one line to the Engine Log: client, file count, email ID
6. Writes a heartbeat line every run, even with 0 files
Leaves: Files in the right folder, the email labelled, a log line · Guards: Never opens zips or links; never replies; labels last so a half-save is caught · Cost: Needs a paid Make plan: about 2,900 operations a month for this alone; the free plan (1,000, 2 scenarios) is already full. Spend decision for you by 23 Oct · needs testing

### M2 Heartbeat Watch (Make scenario)
Runs: Every 3 hours
1. Read the last "run finished" time in the Engine Log
2. Between 08:00 and 20:00: older than 3 hours and no run in progress → label the inbox "ENGINE DOWN" and email you one line
3. Overnight: measures from the 20:00 run; no alarms
4. Alarms only; restarts are E2's job
Leaves: A visible alarm that doesn't depend on Claude's platform · Guards: Runs on Make, not Claude, so it doesn't die with the engine · Cost: Needs a Make slot (same blocker as M1) · needs testing

### E1 Engine run (Claude scheduled task)
Runs: Hourly 08:00–20:00 UK time, one run at a time (run-in-progress marker)
1. Health: kill switch, Notion fields, connections (test read), pinned model, usage reserve; write heartbeat
2. Client text (emails, forms, files, photo text, transcripts) goes only to a model step with no send, share or write tools; it returns fixed fields; scripts do the rest
3. Inbox: read new client emails; classify (files, photo worry, changes, fact update, chasing, payment, red, thanks, prospect); dispute and anger words force red, payment-only words go amber; one-word replies never skip a reminder
4. Files: compare Gmail attachment counts with Drive; score photos (script); pull images from Word/PDF; convert HEIC; strip location; blur plates; SVG logos from approved brand senders converted offline
5. Readiness: check every Definition of Ready item; write Missing Items in plain words; hold Ready if files arrived in the last 24 hours
6. Messages: at most 8 per run (the rest carry over), one automatic email per client per 20 hours, inbox replies first, confirmations only 60 minutes after a sender's last email; every one through the pre-send check
7. Builds: up to 3 Ready clients, oldest deposit first; lock, copy (one client per call), build, publish preview (banner, noindex), then Gate A
8. Gate A: speed, accessibility, phone width, links, PENDING markers, facts against the record, other clients' details, banned claims, reviews word for word, test enquiry to Propulsion's test inbox
9. Changes: apply client tweaks to the inputs (no preview yet) or to an internal v2 (preview built)
10. Report: one line per client; heartbeat end
Leaves: Updated rows, saved and scored photos, previews with Gate A results, confirmations sent within the rules · Guards: Build Status written last; locks with run ID; stops on any failed health check; self-pauses builds after 3 hard fails in a day; rows tagged Manual (e.g. Darren) are never touched · Cost: Matt's plan; Haiku for checks and inbox, Sonnet for copy only; 25% of usage kept for the inbox · needs testing

### E2 Watchdog (Claude scheduled task)
Runs: Every 3 hours
1. No finished run in 3 hours and no run in progress → start one engine run
2. Rows stuck past their limit → amber with "stuck since"
3. Make or Drive at 80% of allowance → flag
Leaves: A restarted engine and a list of stuck rows · Guards: Never starts a run while one is in progress; gives up after 2 misses · Cost: Haiku · needs testing

### E3 Saturday pack (Claude scheduled task)
Runs: Daily 21:00 from 31 Oct, and again every time you open the review
1. Sort every client red, amber or green with the reason
2. Attach: preview v1 and v2 links, Gate A result, the week's client messages (summary plus their words), changes applied, photo picks, logo versions, restyle shortlist with prompts
3. Group decisions by type so they can be approved in batches
Leaves: The "Saturday Review" view, ready to work through top to bottom · Guards: Read-only on client data; never sends · Cost: Haiku

### E4 Draft maker (Claude scheduled task)
Runs: Hourly, round the clock, from Sat 7 Nov: within 1 hour of each approval
1. For every preview you approved: the preview email draft in Gmail, using the AG-16 wording
2. No dates in the wording yet: E5 writes the feedback and launch dates at 06:00 on send day
3. Save the draft ID and the approved version's fixed link on the row; never a second draft
4. Also draft: +48h nudges, "Reply YES" questions, "which would you like?" to the signer
Leaves: Gmail drafts, one per client, ready for you to press send · Guards: Approval void if the client sent anything after it; pre-send check on every draft · Cost: Haiku · needs testing

### E5 Monday link check (Claude scheduled task)
Runs: Mon 9 Nov 06:00, then daily 06:00
1. Open every preview link in a draft; light Gate A rerun
2. Check the approved link still shows the approved version
3. Any fail → draft pulled, row red
4. Write only the dates into each draft: feedback date from the planned send day, launch date from the row
Leaves: Only drafts that work · Guards: Never edits a draft's wording except the dates · Cost: Haiku

### S1 Photo scorer (Script)
Runs: Called by the engine
1. Sharpness, brightness, resolution, orientation, duplicates
2. Screenshot and WhatsApp-compression detection
3. No camera data: never the hero, used only after your Saturday tick and the client's written origin answer. AI tag: never used
4. Faces, plates, paperwork, other firms' branding flagged
5. Restyle shortlist (level 2 only where the brief has the client's yes) with a prompt per image
6. Before-and-after check on any restyled image: the job area must be unchanged
Leaves: Scores, labels and a shortlist on each photo · Guards: Tidy only; never generates or alters the work · Cost: Free (code) · needs testing

### S2 Site builder (Script)
Runs: Called by the engine
1. Fill the pinned master template version from client.json
2. Pick layout: standard (8+ usable, including a finished job) or low-photo (fewer, or no finished-job photo: text or van/team hero)
3. Pick the variant not used by the same trade in the same area
4. Write PENDING markers for anything unconfirmed
Leaves: A static site and a preview link · Guards: Each client in its own folder; template, prompt and packages pinned · Cost: Free (code) + preview host plan · needs testing

### S3 Pre-send check (Script)
Runs: Before every email or draft
1. Thread and recipient belong to this record; greeting matches the sender
2. Only approved templates; scripts fill the numbers; client words checked word for word
3. No braces, CC or other clients' details; links only from the record: form, upload and (preview email only) the approved version's fixed link
4. Circuit breaker counts from Gmail Sent
Leaves: Send or block, with the reason · Guards: Blocks by default · Cost: Free (code) · needs testing

### S4 DNS guide and launch pack (Script)
Runs: When you mark a client Approved
1. Personalised DNS guide PDF for their registrar, website records only
2. Launch email, final invoice draft, handover pack, "we're live" graphic
Leaves: Everything for launch day as drafts · Guards: Never touches nameservers or email records; you press go-live · Cost: Free (code) · needs testing

## Every draft
**Layer 1: Gmail vacation reply (you set it)**
> Away until Monday 9 November
> 
> Hi, thanks for your email. I'm away until Monday 9 November and your message is safe in my inbox. If your files save automatically you'll get a short confirmation; if not, they're still safe and I'll confirm when I'm back. Previews go out from Monday 9 November, and I'll reply to anything that needs me personally by Wednesday 11 November.
> 
> Matt, Propulsion · This is an automatic reply.

**Away line in every kickoff and welcome email**
> I'm away 31 October to 8 November. Your build carries on while I'm away, previews go out from Monday 9 November, and email is the only channel I'll see.

**Reminder 1 (day 2)**
> Hi {first_name}, automatic reminder: to start your website I still need {top_item}. You'll find it {where_to_find}. Pick up where you left off: {form_link}. Photos: {upload_link}. Or just reply with a voice note or the photos. Thanks, Matt

**Reminder 2 (day 4)**
> Hi {first_name}, automatic reminder: one thing would get your site moving: {top_item}. Reply to this email with it (even a rough version is fine), or use your upload link: {upload_link}. Your form: {form_link}. Thanks, Matt

**Reminder 3 (day 7)**
> Hi {first_name}, last automatic reminder: your preview date is {preview_date}, and to hit it I need {top_item} by {date_needed}. Upload link: {upload_link}. Form: {form_link}. If now's a bad time, just reply with a date that suits and I'll work around it. Thanks, Matt

**Template 1: files saved**
> Thanks {first_name}, these are saved to your project: {n} photos{, other files}. {Still needed: {missing_items}. | That's all the files I need for now.} Matt (automatic confirmation)

**Template 2: photo worries**
> Thanks {first_name}, send them anyway: I'll pick the best and tidy them up, and you'll see exactly which ones I've used before anything goes live. Upload them here: {upload_link}, or reply with a few at a time. Matt (automatic confirmation)

**Template 3: changes logged**
> Thanks {first_name}, I've logged these against your project, in your words: {bullets}. I'll go through them with you when I'm back on Monday 9 November. Matt (automatic confirmation)

**Template 4: fact update**
> Thanks {first_name}, I've noted: {fact, in their words}. I'll confirm it with you before anything goes live. Matt (automatic confirmation)

**Template 5: chasing**
> Preview ready or later: "Thanks {first_name}, your project is in the queue and your preview is due from Monday 9 November." Otherwise: "Thanks {first_name}, your project is safe and I'll update you when I'm back on 9 November." Matt (automatic confirmation)

**Photo origin check (once)**
> Quick check: were these all done by you or your team at {business}? I can only show your own work.

**ICO question (plain words)**
> Have you paid the ICO's yearly data protection fee? If you're not sure, the ICO website has a short online check. Send me the result.

**Preview email (AG-16, you send)**
> {first_name}, your new site is ready to review:
> 
> [View your website preview]({preview_link})
> 
> Send all your changes in one reply by {feedback_date} and we'll have them done within 2 working days. That keeps your launch on {launch_date}.

**+48h nudge (AG-16, you send)**
> Hi {first_name}, any thoughts on the preview? Even "looks good" helps: it keeps {launch_date} on track.

**Approval question (you send)**
> Reply YES and I'll book in putting the site live exactly as it is.

**Contradictory feedback (to the signer only)**
> I've had a couple of different steers on {item}. Which would you like: {option_a} or {option_b}?

**Holding line (red email, once per trip)**
> Thanks {first_name}, I've read this and I'll ring you on Monday 9 November. Matt (automatic confirmation)

**Link won't open**
> Thanks {first_name}, I can't open that link automatically. Could you use your upload link instead? {upload_link} Matt (automatic confirmation)

**WhatsApp Business away message (you set it, clients who use WhatsApp)**
> Thanks for your message. WhatsApp isn't checked until 9 November. Please email photos and details to matt.radu@propulsionmarketing.co.uk or use the upload link in your welcome email.

**Trading name question (signer only)**
> Quick one, {first_name}: which name should go on the website, {a} or {b}?

**Logo file question (Still needed line)**
> If you have your logo as a file, reply with it. If not, I'll set your name in clean type and you can swap it in later.

**Urgent, not ours (approved sender only)**
> Thanks {first_name}. If your current site has a security problem, contact whoever hosts it now. I'll ring you on Monday 9 November. Matt (automatic confirmation)

**Logo as PNG (only if SVG conversion fails)**
> Could you send the logo as a PNG? A photo or screenshot of it is fine too.

## Rules
### S0 Signing (before you leave)
- IF Verbal yes on a call → THEN Payment link moving within the hour · ELSE Call back same day · (Matt, r1)
- IF Deposit paid and agreement signed → THEN You type "deposit landed {client}"; engine replies with the record's business name, email and deposit amount; Build Status 1 only after your "yes" · ELSE Nothing builds until both are true · (Matt, r2)
- IF Same trade, same town as an existing client → THEN Flag before the proposal; different layout variant and copy angle · ELSE Matt decides on exclusivity · (Engine, r1)
- IF Domain isn't in the client's name → THEN Build and preview carry on; only Gate B waits. Ownership asked on the form (not looked up); transfer plan is a field you fill: who holds it, registrar, date the client asked them · ELSE Never discovered at launch · (Engine, r5)
- IF Domain bought through Wix → THEN Flag on day 0; Wix route tested before their launch · ELSE DNS call booked as the backup · (Engine, r1) [test]
- IF Client signs Thu 29 or Fri 30 Oct → THEN Kickoff before Fri 17:00, or provisional build (your decision) · ELSE Build starts on your return · (Matt, r1)
- IF "Contact saved + never-spam filter" not ticked on the record → THEN Listed on your Friday 30 Oct checklist · ELSE Reminders still run; Reminders Paused is the backstop · (Matt, r1)
- IF A client hasn't been told about the away week → THEN Every kickoff and welcome email before Fri 30 Oct says: "I'm away 31 Oct to 8 Nov. Your build carries on, previews go out from Mon 9 Nov, and email is the only channel I'll see." · ELSE Not told by Fri 30 Oct 12:00: one-off email you approve · (Matt, r3)
- IF Owner, partner or office may email from several addresses → THEN Every address recorded as an approved sender at kickoff · ELSE Others go to Unsorted, matched Saturday · (Matt, r3)
- IF Deposit or signature lands after Fri 30 Oct 17:00 → THEN Logged; no build, no reminders; start date Mon 9 Nov · ELSE On the Mon 9 Nov list in deposit order, welcome and kickoff drafts by Tue 10 Nov; never a 9 Nov preview date · (Matt, r4)
- IF Client signed before the engine (e.g. Darren on SiteDrop) or row lacks engine fields → THEN Tagged "Manual" before Fri 30 Oct: no reminders, builds, confirmations or move-backs; files saved; Layer 1 and amber · ELSE Unclear status is treated as Manual · (Matt, r4)
- IF Kickoff notes say the client lives on WhatsApp → THEN Approved WhatsApp Business away message set before Fri 30 Oct; that client's reminders say "WhatsApp isn't checked while I'm away" · (Matt, r5)
- IF A record has more than one sender → THEN The signer is named the decider at kickoff · (Matt, r6)
- IF Client will email from a phone → THEN One test email from it at kickoff; that exact address recorded (Apple and Gmail alternatives included) · (Matt, r6)
- IF No kickoff by Fri 30 Oct 12:00 → THEN You send the written kickoff form by 17:00; the time you send it is day 0 · (Matt, r6)
- IF Client has no existing website → THEN Copy comes from the form, kickoff and reviews (they already outrank an old site); nothing else changes before launch · (Engine, r6)
- IF Client doesn't own a domain → THEN At kickoff they pick the name in their words; they buy it themselves, in their own name, before Gate B, with a short guide · ELSE Not bought by Gate B: launch waits; never bought on a Propulsion-only account · (Matt, r6)
- IF Client wants email on a new domain → THEN Flagged at kickoff as outside scope, so it's sorted before launch, not on the day · (Matt, r6)
- IF Calendly during the trip → THEN No slots from 31 Oct until Tue 10 Nov 12:00; a kickoff can only be rebooked through the written form · (Matt, r7)
- IF Written kickoff form → THEN Counts as done when the signer returns it, not when it's sent · (Engine, r7)
- IF Payment links used from Fri 30 Oct → THEN Confirmation page and receipt carry the away line (set before you leave) · (Matt, r7)
- IF Kickoff records the address as shared (mum's, a family email) → THEN Approved and big facts also need your phone confirmation; greeting is "Hi," · (Matt, r8)
- IF Client is a franchisee → THEN Head office recorded as an approved sender for brand files only; pack tagged "licensed brand"; head office's written OK added to Gate B · (Matt, r8)
- IF Tier is enquiry-only (they keep their existing site) → THEN Row tagged Manual: no reminders, no site build, no DNS rules · (Matt, r8)
- IF Business address is outside the UK → THEN Flagged before the proposal; automatic ICO and Companies House lines off; you name the right register · (Engine, r8)
- IF A second signature or deposit from an address already on a record → THEN No new record; amber "possible double payment" on the existing row; build carries on; you check Tide and refund on Monday · (Engine, r8)
- IF The vacation reply is switched on → THEN Set to "only send to my Contacts" (client senders added at kickoff); the away line adds: "I'll never change bank details by email; payments only through the link in your agreement." · ELSE Everyone else gets no "away" signal · (Matt, r10)
- IF The trip starts → THEN 2-step sign-in on a passkey or security key, printed backup codes kept apart from the phone, recovery details checked, login alerts to a second address · ELSE Proposal: engine runs from a separate Propulsion mailbox with delegated access · (Matt, r10)
- IF Address recorded as shared (family email, brothers) → THEN Signer-only lines become drafts for you; that address plus your logged phone confirmation counts as the signer's for Approved · (Matt, r9)
- IF Signature after Fri 30 Oct 12:00 with no kickoff, or a client with no email address → THEN After-17:00 rule applies: logged, start Mon 9 Nov, tagged Manual · (Matt, r11)
- IF Client's domain has no SPF/DKIM at kickoff → THEN Record a second address that passes authentication · (Matt, r14)

### S1 Intake and reminders
- IF Anything on Missing Items still outstanding on day 2, 4 or 7 (day 0 = kickoff) → THEN One reminder at the first run after 09:30, at least 1 working day apart; marked "automatic reminder"; one small ask in plain words; carries the form link and the upload link; "or just reply with a voice note or the photos" · ELSE Stops at 3 reminders · (Engine, r5) [auto] [test]
- IF Reminder day falls on a weekend or bank holiday → THEN Next working day, first run after 09:30; the whole sequence moves so there's always a working day between · (Engine, r5) [auto]
- IF Client replied since the last reminder (exact address; business domain only if not gmail, outlook, icloud etc.) → THEN Skip the next reminder only if the reply carries a file or a new fact. "ok", "yes", "will do" don't count; nor do out-of-office, noreply, mailer-daemon or loops · (Engine, r6)
- IF Reminders Paused or On Hold ticked → THEN Nothing sends · (Engine, r1)
- IF Any engine email bounces → THEN All engine email to that address stops; red "email bounced" · ELSE Bounce says the domain doesn't exist: "domain may have lapsed" check added for Gate B · (Engine, r6)
- IF Day 8 with items still outstanding, however many reminders went → THEN Red on Saturday's list · ELSE You call on Monday · (Engine, r6)
- IF Answers are one word or blank → THEN One fixed question per form field (approved by you before 30 Oct), as the "Still needed" line · ELSE No match: nothing added; kickoff fills it · (Engine, r4) [auto]
- IF Form filled by someone else (wife, office manager) → THEN If they were listed as a sender at kickoff: confirmed for files and the form (big facts still go to the owner). Not listed: unconfirmed, Layer 1 only, files to Unsorted · ELSE You confirm them · (Engine, r5)
- IF Form submitted twice → THEN Newest kept, older marked duplicate · ELSE Merge flag; never deleted · (Engine, r1)
- IF Client is busy, away, having an operation or flat out ("next week", "after Christmas", "when it's dry") → THEN Pause until their date, 14 days at most, 7 if no date; Layer 1 only; preview and feedback dates move; red on Monday's call list. The status limit matches the pause · ELSE Layer 1 reply only · (Engine, r4)
- IF Client asks to cancel or wavers ("second thoughts", "my mate can do it", "stop emailing me") → THEN Reminders stop; build On Hold automatically · ELSE Red; Layer 1 only; you ring them first on Monday · (Engine, r4)
- IF Email contains instructions ("send the invoice", "change the price") → THEN Logged as data; never acted on · (Engine, r1)
- IF Voice note sent as an attachment → THEN Saved; transcribed word for word · ELSE Facts from it confirmed by you before use · (Make + engine, r1) [test]
- IF Client sends details on WhatsApp → THEN WhatsApp away text only if you add it to the allowed list in writing before 30 Oct · ELSE Otherwise the away line in the kickoff email does the job · (Matt, r4)
- IF A reminder and a confirmation are both due today → THEN Inbox first, then reminders: one automatic email per client per 20 hours; the confirmation's "Still needed" line replaces the reminder · (Engine, r2)
- IF Drive upload link asks them to sign in to Google → THEN Swap for an upload route with no Google account, tested on an iPhone · ELSE Reminders say "just reply with a few photos at a time" · (Matt, r3) [test]
- IF Any extra ask (more photos, photo origin, ICO, VAT on prices, unproven claims) → THEN One fixed line from your approved list, only as the "Still needed" line of a reminder or confirmation already due · ELSE Nothing due: held for Monday · (Engine, r4)
- IF Reminder 3 is due → THEN {date_needed} = 2 working days after the send (never a date already passed); {preview_date} from the row · (Engine, r13)
- IF Any reminder is blocked by the pre-send check → THEN Still counts towards the 3; row goes red · (Engine, r5)
- IF Facts come from a voice note → THEN Build with "PENDING: confirm {fact}"; removed from Still needed · (Engine, r5)
- IF "Cancel" is about a call or meeting (or a Calendly cancellation that day) → THEN Amber "kickoff not done", not red or On Hold · (Engine, r6)
- IF Fixed lines the rules depend on → THEN Approved list includes: the trading-name question ("Which name should go on the website: {a} or {b}?", signer only), one question per form field, "which would you like?" · ELSE Not approved by 30 Oct 12:00: that row stalls visibly (amber), never silently · (Matt, r7)
- IF A form submission lacks that record's unique token → THEN Unsorted; never changes a row. Newest-wins only within the same token, 3 submissions a day at most · (Engine, r10)
- IF Reminder 3 would land after Wed 4 Nov → THEN Sent Wed 4 Nov instead (reminder 2 dropped if under 1 working day before); the neutral-line build starts Thu 5 Nov 18:00 whether reminder 3 went or not · (Engine, r11)
- IF A kickoff is cancelled a second time → THEN Amber "kickoff cancelled twice", top of Monday's call list · (Engine, r11)
- IF A send is blocked by the breaker, kill switch or an engine-wide pause → THEN Doesn't count towards the 3 reminders; the row keeps its colour (only content failures count) · (Engine, r11)
- IF Make is down → THEN File-asking reminders and the neutral-line build wait until Gmail and Drive counts match again · (Engine, r14)
- IF Written kickoff form sent but not returned → THEN Listed in Missing Items so reminders ask for it · (Engine, r14)

### S2 Files and photos
- IF Email from a known client address has attachments → THEN Make saves each file to the client's folder (named by record ID); applies "Saved" last, only once every attachment is in Drive · ELSE Engine compares Gmail's attachment count with Drive before any confirmation · (Make, r2) [test]
- IF Sender address unknown → THEN Files go to "Unsorted"; no confirmation · ELSE Layer 1 only; flag · (Make, r1)
- IF Files missing, or a client email with attachments over 2 hours old and no "Saved" label → THEN Count with the same minimum-size filter as M1 (skipped files logged); no confirmation; flag · ELSE 3 or more in a day: "Make down", all confirmations stop · (Engine, r5)
- IF WeTransfer, Dropbox, Google Photos or iCloud link → THEN Opened only if it lands on wetransfer.com, dropbox.com, photos.google.com or icloud.com (one redirect allowed from photos.app.goo.gl, we.tl or db.tt to the matching domain), from a known client address, no login · ELSE Can't open: that day's email is the fixed line "I can't open that link automatically. Could you use your upload link?" · (Engine, r5) [test]
- IF iPhone HEIC photo → THEN Converted to JPG · (Engine, r4) [test]
- IF Email between 25 and 50 MB, or too big to send → THEN Make saves anything that arrives; every ask carries the upload link · (Gmail, r4) [test]
- IF Screenshot (status bar showing) → THEN A screenshot of a preview or website is feedback: logged to change requests, never a site photo. Other screenshots scored low · ELSE Flag · (Engine, r3)
- IF WhatsApp-compressed (small, no camera data, but has the WhatsApp file pattern) → THEN Small slots only, and only after your Saturday tick (no camera data rule) · (Engine, r7)
- IF Blurry, dark or wonky → THEN Brightness, crop and straighten allowed; never the hero if still weak · (Engine, r1)
- IF Near-identical duplicates → THEN Best one kept · (Engine, r1)
- IF Number plates or house numbers visible → THEN Blurred automatically · (Engine, r4) [test]
- IF Faces visible (customers, children, staff) → THEN Saved, marked "consent check", not used · ELSE You confirm consent · (Engine, r1)
- IF Watermark, stock or supplier-brochure look → THEN Not used. Ask once: "Quick check: were these all done by you or your team at {business}? I can only show your own work." · ELSE Previous-employer jobs left out unless you decide otherwise · (Engine, r3)
- IF Fewer than 3 usable photos → THEN Low-photo layout; ask once for one exact shot. Owner portrait only if they sent one and said yes in writing; otherwise van, tools or team shot they supplied · ELSE Never ask twice · (Engine, r3) [auto]
- IF 3 to 7 usable → THEN Low-photo layout variant; ask for the missing slot · (Engine, r1) [auto]
- IF 8 or more usable → THEN Standard layout · (Engine, r1)
- IF 200+ photos sent → THEN Scripts cull; the model sees the top 30 · (Engine, r1)
- IF Location data in the photo → THEN Stripped before upload · (Engine, r4) [test]
- IF Logo is blurry or a photo of the van → THEN Build both: their tidied logo and a clean text version, side by side on Saturday; you pick · ELSE Preview email says which was used and that theirs is still an option · (Engine, r3)
- IF Any edit beyond tidying asked for (remove a defect, add something) → THEN Never done: tidy the photo, never the job · (Engine, r1)
- IF Email or file arrived under 30 minutes ago → THEN Left for the next run so Make and Drive catch up · (Engine, r2)
- IF Attachment isn't an image, PDF or audio (zip, exe, macro Word file) → THEN Quarantine folder; never opened or counted · ELSE You check on return · (Make, r2)
- IF One email address on more than one record → THEN Files to Unsorted; reminders pause on both records until you match them; Layer 1 only · ELSE You match on Saturday · (Make, r7)
- IF Photos inside a Word file, PDF or the email body → THEN Each image pulled out and treated as a photo · ELSE Can't: no confirmation, flag · (Engine, r3) [test]
- IF "My photos are on Facebook / Instagram / Checkatrade / my old site" → THEN Link logged; Template 2, which carries the upload link and "or reply with a few photos at a time"; nothing pulled, nothing called saved · ELSE You ask for a direct send Monday · (Engine, r5) [auto]
- IF "Something like this", another firm's branding, Pinterest-style → THEN Marked "reference only"; never shown as their work · ELSE Unsure: held, asked Monday · (Engine, r3)
- IF Unsafe working (no edge protection, ladder on a roof, no kit) or a visible defect → THEN Never the hero; "safety look" flag for you · ELSE Not used · (Engine, r3) [test]
- IF Photo shows a phone, website or name that doesn't match the record (old van livery) → THEN Cropped out or not used; fact-conflict flag · (Engine, r3)
- IF Customer paperwork in shot (invoices, job sheets, names) → THEN Not used; marked "personal data" · ELSE You decide on deletion · (Engine, r3)
- IF Video files (.MOV) → THEN Saved, listed as "videos" in the confirmation; not on the site unless the tier includes video · ELSE Too big: upload link · (Engine, r3)
- IF You forward WhatsApp photos from your own address → THEN Record ID in the subject: saved and counted, confirmation draft for you · ELSE No ID: Unsorted · (Make, r4)
- IF A photo would benefit from a night or dusk version, sky swap or clutter removal (level 2) → THEN Only where the brief has the client's written yes; the engine shortlists it and writes the prompt; you run it in ChatGPT · ELSE No written yes: tidy only · (Engine, r4)
- IF A restyled image comes back → THEN Before-and-after check: the job area must be unchanged; you compare side by side · ELSE Work moved: rejected · (Engine, r4) [test]
- IF Anything that would generate a scene, add fittings or hide a defect (level 3) → THEN Never · (Engine, r4)
- IF Files confirmed in Drive → THEN Template 1, batched. Count only images above a minimum size that don't repeat across their emails (signature logos never counted or used). "That's all the files I need for now" only when no file items are left · (Engine, r4) [auto]
- IF A sender's emails are still arriving → THEN Confirm only 60 minutes after their last one · (Engine, r5)
- IF winmail.dat arrives (Outlook) → THEN Flagged; that day's email is the upload-link line · (Engine, r5) [auto]
- IF Files come through the upload route → THEN Saved to Clients/{record ID} with a log line; confirmed once per batch, 60 minutes after the last file, checked against the upload tool's own count · (Make, r7) [test]
- IF Image has no camera data or carries an AI tag → THEN No camera data: never the hero, used only after you tick it on Saturday. AI tag: never used. The photo-origin question goes as the Still needed line · (Engine, r7) [test]
- IF 600+ files in one batch → THEN M1 batch and Make allowance tested at 600 files before 26 Oct · (Make, r6) [test]
- IF No photo shows a finished job → THEN Low-photo layout with a text or van/team hero; one finished-job shot asked as the Still needed line · (Engine, r8)
- IF A file is SVG, HTML or XML, or its real contents don't match its extension → THEN Quarantined. Every image decoded and re-saved as JPG or PNG with metadata removed; PDF and Word extraction runs with no network; logos always re-saved PNG · (Engine, r10) [test]
- IF A file is saved → THEN Named record ID + hash + allowed extension; original name kept only as a log field; business name never in a path · (Make, r10)
- IF A photo has no camera data and you'd tick it → THEN Your tick only allowed once the client's written answer to the photo-origin question is on file · (Matt, r9)
- IF A file arrives as a drive.google.com link (too big to attach) → THEN Opened only if shared from a known client address with no login; otherwise the "can't open" line · (Engine, r9) [test]
- IF No logo file sent → THEN Clean text version of the business name; fixed line as Still needed: "If you have your logo as a file, reply with it. If not, I'll set your name in clean type and you can swap it in later." · ELSE Van photo shown beside it on Saturday · (Engine, r13)
- IF An image has no camera data → THEN The origin question also asks "Are these real photos, not made or changed with an app or AI?"; your tick needs a written yes to both · (Engine, r11)
- IF A quarantined SVG logo from an approved brand sender → THEN Converted to PNG offline (scripts and links stripped) · ELSE Can't: Still needed line "Could you send the logo as a PNG?" · (Engine, r11) [test]
- IF A quarantined SVG logo is pending conversion → THEN Don't also send the no-logo question; the PNG line (approved) only if conversion fails · (Engine, r14)
- IF The Inbox Saver runs → THEN Writes a heartbeat line even with 0 files (so a quiet inbox isn't "Make down") · (Make, r14)
- IF Client answers the photo-origin question on WhatsApp → THEN Doesn't count as written: you forward it to the record or ask by email · (Matt, r14)

### S3 Ready to build
- IF Every Definition of Ready item present and kickoff done → THEN Build Status = 3, Ready to build · (Engine, r1)
- IF Kickoff not done → THEN Never ready (unless provisional build is approved) · (Engine, r1)
- IF Two sources disagree on a fact → THEN Flag; build goes ahead with "PENDING: {fact}" in its place · ELSE You pick on Saturday; never guessed · (Engine, r2)
- IF Any badge, logo or registration (Gas Safe, NICEIC, TrustMark, Checkatrade, FMB, Which?, approved installer) → THEN Needs a current number naming the business or the named engineer; you check the public register before Gate B; badge logos only with that proof · (Engine, r3) [auto]
- IF Years in the trade longer than the company exists → THEN Client's exact words only ("in the trade since…"); flag · (Engine, r1)
- IF Areas list over 15 towns → THEN Main towns used; full list in the footer · ELSE You decide on town pages · (Engine, r1)
- IF No reviews anywhere → THEN No review section; nothing invented · (Engine, r1)
- IF Reviews only on Checkatrade or Facebook → THEN Quoted word for word; reviewer as first name and town only, never their photo; source link kept · (Engine, r4) [test]
- IF Text pasted from a competitor → THEN Not used · ELSE Flag · (Engine, r1)
- IF ICO number missing → THEN Ask in plain words: "Have you paid the ICO's yearly data protection fee? If you're not sure, the ICO website has a short online check. Send me the result." · ELSE Gate B needs the number or their written result; you never decide it for them · (Engine, r3) [auto]
- IF New files or facts in the last 24 hours → THEN Not marked Ready yet (stops building on 12 of 40 photos) · ELSE After 72 hours, build with what's there, note "late files" · (Engine, r2)
- IF Form answers read like ChatGPT or marketing copy, or pasted from their old site → THEN Every claim in them counts as unproven; plain facts kept in their words · ELSE Ask once · (Engine, r3)
- IF Not a limited company, or name differs from Companies House → THEN "Ltd" only if on Companies House; footer shows registered name, number and office exactly · ELSE Left off, flagged · (Engine, r4) [test]
- IF Business address is a home address → THEN Town only unless they ticked "show my address"; never pinned on a map · (Engine, r3)
- IF Client gives prices ("from £3,500") → THEN Shown exactly as given, with their own VAT wording · ELSE VAT unclear: left off, ask once · (Engine, r3)
- IF Reviews as screenshots of texts, or "write a few for me" → THEN Texts only after the client confirms the customer agreed (first name and town). Writing reviews: never; red · (Engine, r3)
- IF Reviews are on Google → THEN Only reviews the client pasted or screenshotted, saved to Drive as the source; first name only; link to their Google profile; Gate A checks against the saved copy · (Engine, r5)
- IF Ready is checked → THEN Against the written Definition of Ready list on the OS-09 page; ICO and badges block Gate B only · (Engine, r5)
- IF Two approved senders on one record disagree → THEN The signer's latest written answer is used; the other is logged; the signer-only "which would you like?" line goes as the Still needed line · (Engine, r6)
- IF Business has more than one trading name → THEN The one name the site uses, in the signer's writing, joins the Definition of Ready; not Ready until it's written · (Engine, r6)
- IF An answer used for copy is under 5 words → THEN Counts as missing for Ready; that section gets a fixed neutral line; the per-field question goes as the Still needed line · (Engine, r7)
- IF Companies House status isn't Active (dissolved, in liquidation) → THEN Red "company status": build stops; no Ltd or number on the site; you decide who the contract is with · (Engine, r8) [test]
- IF Reminder 3 has gone and an answer is still under 5 words → THEN Build with the approved neutral line (exempt from the traceability check); listed on Saturday · (Engine, r9)

### S4 Build
- IF Row is Ready to build → THEN Queue: oldest deposit first, 3 per run · (Engine, r1)
- IF Another run holds a lock under 2 hours old → THEN Skip that client · (Engine, r1)
- IF Lock over 2 hours old → THEN Lock written with this run's ID and read back; continue only if it's ours. v2 builds, fact reruns and Gate A take the same lock · (Engine, r2)
- IF 2 failed build attempts (host outages never count) → THEN QA failed, "needs Matt" · (Engine, r4)
- IF Master template changed → THEN Clients already building stay on their version · (Engine, r1)
- IF Banned phrase in the copy (guarantee, No.1, cheapest, 24/7, free…) not on the client's list → THEN Comparisons (best, No.1, cheapest, guaranteed results) never used, even if asked. "Free quotes", "24/7" and a written workmanship guarantee only in their words, with the terms, flagged for you; claims list approved by you with proof · ELSE Then flag · (Engine, r3)
- IF Copy too similar to another client's site in the same trade → THEN Rewrite from the client's own words · (Engine, r1)
- IF Preview host or code store down → THEN Zip to Drive, "Built, not published"; publish attempts +1 (separate counter) · ELSE After 3: needs Matt. 3 clients in a row: publishing pauses (only publishing) · (Engine, r4)
- IF Usage reaches the reserve (about 75% of the limit) → THEN Builds stop; 25% kept for the inbox and the watchdog; an interrupted build releases its lock and requeues · (Engine, r2) [test]
- IF A model step reads emails, records or photos → THEN One client per call, fresh context, only that client's files · ELSE Output naming another client is thrown away and flagged · (Engine, r2)
- IF Deposit disputed or refunded → THEN Build, reminders and confirmations stop; On Hold; red · ELSE Nothing restarts without your go · (Matt, r2)
- IF Preview built → THEN "Preview – not live" banner, hidden from Google · ELSE Banner missing: Gate A fails · (Engine, r3)
- IF Client text compares with or criticises other firms, named or not ("unlike the cowboys…") → THEN Sentence never used; amber "comparison" (red if a firm or person is named); Gate A bans claims about other firms · (Engine, r7)
- IF A preview is published → THEN Random path (22+ characters, no business name); X-Robots-Tag noindex header; removed on cancel or On Hold and 30 days after launch · (Engine, r10)

### S5 Quality gate (Gate A)
- IF Gate A passes → THEN Build Status = 6, Preview ready · (Engine, r1)
- IF Technical fail (images, links, markup) → THEN One automatic fix, rerun · ELSE Then QA failed · (Engine, r1)
- IF Fact doesn't match the record → THEN If the record changed after the build started, back to the queue once; only a mismatch against an unchanged record is QA failed · (Engine, r2)
- IF Another client's phone, email or images found on the site (images checked by file fingerprint) → THEN Hard fail; site quarantined; red · ELSE A name-only match is amber (common names at 500 clients) · (Engine, r2)
- IF Placeholder or empty section → THEN Fail, except the one fixed marker "PENDING: {item}", which counts as amber with its reason · ELSE The Monday link check and Gate B fail on any marker · (Engine, r2)
- IF Phone link doesn't dial the right number → THEN Fail · (Engine, r1)
- IF Test enquiry not received within 5 minutes → THEN Preview forms send to a Propulsion test inbox under a label the engine skips; Gate A fails if it isn't there within 5 minutes · ELSE Switched to the client's address at Gate B, by you · (Engine, r2) [test]
- IF PageSpeed check → THEN Lighthouse run in the cloud container (Chromium is installed) · ELSE If it can't run: "PageSpeed pending" for you on Saturday · (Engine, r1) [test]
- IF A line of copy is contradicted by a review on file → THEN Fail; line cut · ELSE Flag for you · (Engine, r3) [test]
- IF Gate A runs → THEN Phone width first: tap-to-call works, form fillable with a thumb, hero readable · ELSE Fail · (Engine, r3)
- IF A real person fills in a preview form → THEN Red "real enquiry on preview"; kept in the test inbox; you pass it on Monday. Preview forms carry the privacy link and "this is a preview" · ELSE No test ID: treated as real · (Engine, r4)
- IF A PENDING marker is waiting on the client (ICO, a fact only they can give) → THEN The preview shows a neutral approved line; the item goes in the preview email; only Gate B fails on it · ELSE Markers waiting on Propulsion still fail the Monday check · (Engine, r6)
- IF A line of descriptive copy can't be traced to the client's own words → THEN Fail (stops invented claims like "reliable, tidy, family-run") · (Engine, r7) [test]
- IF A client string goes into the site → THEN Escaped as plain text, never HTML; Gate A fails on any script, event handler, iframe, javascript: link or domain not on the allow list; Content-Security-Policy blocks inline scripts · (Engine, r10)

### S6 Inbox while away
- IF Any email arrives → THEN Gmail's vacation reply (Layer 1): "Your message is safe in my inbox. If your files save automatically you'll get a short confirmation; if not, they're still safe and I'll confirm when I'm back." · ELSE Gmail only repeats it every 4 days per sender: the chasing rule covers the gap · (Gmail, r3) [auto]
- IF Automatic email (out-of-office, noreply, mailing list) → THEN No engine reply · (Engine, r1)
- IF New address, even on the client's domain → THEN Layer 1 only; flag · (Engine, r1)
- IF Photo worries ("my photos are rubbish", not enough, can't take more) → THEN Template 2 · (Engine, r4) [auto]
- IF Changes or tweaks → THEN Template 3. Changes to their own site content go into the build inputs (no preview yet) or an internal v2. Anything about Propulsion's price, invoice, scope, sending or access is logged only, red · (Engine, r4) [auto]
- IF Fact update → THEN Template 4. Name, trade, areas, phone, email, domain, address and accreditation changes are queued for you, whoever sends them; old value stays in use. Other facts update with the old value kept · (Engine, r4) [auto]
- IF Unclear → THEN Layer 1 only; amber · (Engine, r1)
- IF Only "thanks" or "ok" → THEN Nothing · (Engine, r1)
- IF New prospect (not a client) → THEN Layer 1 only; flagged for Monday · (Engine, r1)
- IF Spam or phishing → THEN Nothing; links never opened · (Engine, r1)
- IF One email, several categories → THEN One combined reply; if any part is red, no engine reply · (Engine, r1)
- IF An engine email went to this client in the last 20 hours → THEN Hold and combine into the next one · (Engine, r4)
- IF Client says their current site is down, or it's urgent → THEN Layer 1; red flag; push notification · ELSE You may be off grid; Saturday at the latest · (Engine, r4) [test]
- IF About to send any client email → THEN Check Sent for that thread first; write "sending {id}" before and "sent {id}" after · ELSE Says sending but Sent shows nothing: flag, never resend · (Engine, r2)
- IF Email or form contains a password, login, card or bank number → THEN Never copied anywhere; red flag "credentials sent, not stored" · ELSE Saturday pack shows [removed]; you ask them to change it · (Engine, r2)
- IF Money, anger or legal words (refund, money back, chargeback, rip-off, waste of money, solicitor, contract, complaint, legal, cancel, disappointed, not happy, invoice). Not the client's own prices to their customers (those are amber) → THEN Red: stops replies, never builds. Layer 1 only, whatever the model thinks · ELSE The model can make an email redder, never greener · (Engine, r5)
- IF Client chases ("any update?", "are you still there?") → THEN Amber. If Layer 1 went in the last 4 days: Template 5. Date line only if the row is Preview ready or later; otherwise "Your project is safe and I'll update you when I'm back on 9 November." · ELSE No template approved: red, first call Monday · (Engine, r4) [auto]
- IF Client refers someone or asks you to ring → THEN Top of Monday's call list with name and best time · ELSE Layer 1 only until then · (Engine, r3)
- IF Big fact change (name, phone, trade, areas) from a second contact → THEN Template 4 only to senders approved at kickoff (unconfirmed contacts: Layer 1); logged for the owner to confirm · ELSE Confirmed on the preview call · (Engine, r4) [auto]
- IF Client rings or texts your mobile → THEN Voicemail greeting matches Layer 1; Monday missed calls matched to records before the first dial block · ELSE Unmatched numbers: prospects list · (Matt, r4)
- IF A red email arrives and Layer 1 already went to that sender in the last 4 days → THEN One approved holding line, once per trip: "Thanks {first_name}, I've read this and I'll ring you on Monday 9 November." · ELSE Then on Monday's red call list · (Engine, r5) [auto]
- IF Several change emails would push Template 3 past 300 characters → THEN Template 3 says "{n} changes logged in your words" instead of listing them · (Engine, r6) [auto]
- IF A red-list word is only about paying (paid, invoice, receipt) with no dispute words → THEN Amber "payment to check in Tide": replies held, build carries on · (Engine, r6)
- IF Sender isn't an approved sender → THEN Layer 1 only: overrides every template, including the holding line · (Engine, r7)
- IF Client email isn't in English → THEN Amber "language"; Layer 1 only for that email; copy only from English answers or a translation the client approves in writing · (Engine, r8)
- IF Client asks us to remove, report or reply to a Google review → THEN Amber "review request"; logged only, no template; you explain on Monday that only Google or the client can act · (Engine, r8)
- IF Any sender says the client is ill, away or has died → THEN Reminders pause at once; red "contact change"; you confirm a new signer in writing with the original signer or from the company record · (Engine, r8)
- IF Sender authentication is anything but "pass" (fail, none, missing) → THEN Treated as an unknown sender: Unsorted, Layer 1 only, never a fact, file or approval · ELSE One address trips the breaker: mute that record only · (Engine, r11) [test]
- IF Client words would be quoted back in an email → THEN Strip URLs, email addresses, phone numbers, sort-code and account-number patterns and HTML; 120 characters at most; only when sender authentication passed · ELSE Otherwise "{n} changes logged" · (Engine, r10)
- IF A Monday missed call doesn't match a record → THEN Checked against names in Unsorted and red emails before it goes on the prospects list · (Engine, r9)
- IF A client email isn't in English → THEN Reminders pause for that client until you've read a translation on Saturday · (Engine, r9)
- IF Urgent but not ours ("hacked", "virus", "site down" about their current site) → THEN Fixed line to an approved sender: "If your current site has a security problem, contact whoever hosts it now. I'll ring you on Monday 9 November."; red · (Engine, r13) [auto]
- IF A red email isn't in English → THEN No holding line (nobody has read it); red still raised; Layer 1 only · (Engine, r11)
- IF Mail from a record's own address fails authentication → THEN Pause that record's reminders; Layer 1 only; Saturday list "unauthenticated sender" · (Engine, r14)
- IF A non-English email → THEN Stops the build for that client until you've read a translation · (Engine, r14)

### S7 Saturday review
- IF Row is red → THEN Top of the list (money and complaints, then cross-client, facts, consent, stalls) · (Engine, r1)
- IF Row is green → THEN Spot-check 1 in 5; approve the rest in one go · (Matt, r1)
- IF Amber with a v2 → THEN You pick v1 or v2 · (Matt, r1)
- IF Not finished by Saturday night → THEN Sunday overflow; unreviewed rows get no Monday draft · (Matt, r1)
- IF Flying home on Saturday → THEN Review on Sunday 8 Nov · ELSE Layer 1 covers to Sunday 23:59 · (Matt, r1)
- IF The trip produces 10 or fewer previews → THEN You open every one at phone width before approving · (Matt, r5)
- IF You open the review → THEN E3 rebuilds the pack first · (Engine, r5)
- IF An unknown address carries a bounced client's name → THEN Top of Saturday as "likely new address" · (Engine, r6)
- IF You match Unsorted files to a client → THEN They count from when they arrived, not when matched · (Engine, r6)
- IF You clear a red → THEN Record "cleared {reason}" on the row; the next run picks it up from its stage · ELSE Every red has you as its named owner · (Matt, r6)
- IF A voice note over 10 minutes → THEN Saturday pack lists at most 15 facts from it; you tick each; ticks trigger a rebuild before you approve · (Engine, r8)
- IF You confirm facts on Saturday (voice notes, PENDING markers) → THEN Rebuild runs before the 06:00 Monday check · (Engine, r8)
- IF A voice note has more than 15 facts → THEN The rest stay PENDING (Gate B only) and show as "+n more" for the Monday call · (Engine, r9)

### S8 Monday send
- IF Preview approved → THEN Gmail draft within 1 hour of your approval, whatever the time; 06:00 Monday check is the only cut-off · (Engine, r4)
- IF 06:00 Monday link check fails → THEN Draft pulled; red · (Engine, r1)
- IF 50 previews to send → THEN Feedback dates staggered, 10 a day across 9–13 Nov · (Engine, r1)
- IF Sending → THEN You send about 10 an hour · (Matt, r1)
- IF You're delayed → THEN Drafts wait; nothing sends itself · (Matt, r1)
- IF A real message after your approval (changes, facts, files or a red word; not "thanks", out-of-office or loops) → THEN Approval void; Monday draft pulled; amber · ELSE 06:00 check compares approval time with the last client message · (Engine, r4)
- IF A Monday draft is due → THEN Draft ID saved on the row; never a second one · ELSE Two drafts: newer deleted, flagged · (Engine, r2)
- IF A Monday draft is pulled → THEN Amber "draft pulled: {reason}" at the top of Monday's 12:00–15:00 decisions; rebuilt if needed, re-approved, new draft · (Engine, r4)
- IF Layer 1 promised "I'll confirm when I'm back" and nothing went (Unsorted, Make down, breaker, after Sun 23:59) → THEN By Mon 08:00 a list of those clients with a Template 1 draft each, for you to send before 12:00 · ELSE Not sent by Tue: red on the call list · (Engine, r4)
- IF First 48 hours back (Sat 7 to Mon 9 Nov) → THEN Order: reconnect and health; red calls; Saturday decisions in batches; previews sent 12:00–15:00 and after 18:00, never in dial blocks · ELSE Not sent Monday: Tuesday, feedback dates reset · (Matt, r4)
- IF Monday make-up list → THEN Includes rows that went red with no reply sent, alongside Unsorted, Make down, breaker and late emails · (Engine, r5)
- IF A preview draft is made → THEN No dates in the wording until 06:00 on send day, when E5 writes only the dates; {launch_date} from the row · (Engine, r5)
- IF Monday make-up list → THEN Unlisted family senders (no vacation reply under contacts-only) go first · (Engine, r11)

### S9 Feedback rounds
- IF Feedback received → THEN Tagged R1–R10; next version built for your yes within 2 working days · (Engine, r1)
- IF Scope request (R10) → THEN Change order: you decide · (Matt, r1)
- IF More rounds than the tier includes → THEN Flag as a change order · (Engine, r1)
- IF Contradictory feedback (partner, a mate) → THEN Draft goes only to the person who signed; only their written choice counts · ELSE You send · (Engine, r3)
- IF Silence past the feedback date → THEN Email draft at +48h; at +96h a text or call on your list; silence is never approval · ELSE After the agreement's pause period, you decide · (Engine, r3)
- IF You approve a preview → THEN That exact version gets a fixed link no later build can overwrite · ELSE Approved link changed: draft pulled · (Engine, r2)
- IF Someone else (a mate, "my IT guy") asks for logins, files, code or hosting → THEN Nothing handed over; logged · ELSE You decide with the person who signed · (Matt, r3)
- IF "Looks good", "spot on mate", a thumbs-up or a WhatsApp yes → THEN Not go-live approval (clause 6.4 needs it in writing); draft: "Reply YES and I'll book in putting the site live exactly as it is." · ELSE You send · (Engine, r4)
- IF Feedback rejects the whole site ("not what I wanted", "looks like a template") → THEN Not counted as a round; red; you ring within 1 working day · (Matt, r3)
- IF A preview is sent → THEN Feedback date counted from the real send time in Gmail Sent · ELSE No Sent record: no feedback date, no silence clock · (Engine, r4)
- IF Anything arrives after Preview ready → THEN All into one v2, rebuilt each time; v1 untouched; new photos only with your pick · (Engine, r5)
- IF Approval words come from anyone but the signer → THEN No "Reply YES" draft to them; the question goes to the signer only; Approved needs the signer's own address on the quoted email · (Engine, r7)

### S10 Launch and DNS
- IF Written approval in → THEN Engine only tags "possible approval" with the quote; only you set Approved, and it must name the version or link · (Engine, r2)
- IF Registrar offers delegate access → THEN Client grants it; you change the website records · (Matt, r1) [test]
- IF No delegate access → THEN Personalised guide PDF with their domain and exact values · ELSE Call only if stuck · (Engine, r1)
- IF No screenshot of their current DNS → THEN With delegate access you take the screenshot yourself; self-serve route needs theirs, with a 3-step guide for their registrar · ELSE No screenshot: nothing changes · (Engine, r3)
- IF Email records on the domain → THEN Never touched; website records only, never nameservers · (Engine, r1)
- IF Not pointing after 48 hours → THEN Check and call · (Matt, r1)
- IF Gate B passes → THEN You press go-live; launch pack drafts (email, invoice, handover, graphic) · (Matt, r1)
- IF Gate B fails → THEN No launch · (Engine, r1)
- IF Final invoice unpaid after 7 days → THEN AG-10 writes a chase draft onto your list; you send it · (Engine, r4)
- IF Money arrives before the final invoice → THEN Your Tide check is a required tick on the row before any chase or final-invoice draft; launch pack drafts a receipt if paid · (Matt, r7)
- IF New domain with no old site → THEN Fresh DNS setup from the guide; no old records, no redirects (that Gate B item is marked not needed) · (Engine, r6)

### S11 Engine health
- IF Every run starts → THEN Check connections with a test read, Notion fields, the pinned model name; write heartbeat. Kill switch checked before every send and every build, flippable from your phone in one tap · ELSE Any fail: stop and flag · (Engine, r4) [test]
- IF A Notion field renamed → THEN Run stops: "schema changed: {field}" · (Engine, r1)
- IF No finished run for 3 hours → THEN M2 (Make) only raises the alarm: labels the inbox "ENGINE DOWN" and emails you. Restarts are E2's job, best effort · ELSE Layer 1 is the only promise during the trip · (Watchdog, r5) [test]
- IF Clocks go back (Sun 25 Oct) → THEN Every time stored in UTC with its offset; gaps worked out in UTC, calendar days in London time; Make account set to Europe/London; "once a day" means 20 hours since the last one · ELSE Test on 26 Oct · (Engine, r2) [test]
- IF Notion rate limit → THEN Batches of 10, retry with a wait · (Engine, r1)
- IF Make or Drive at 80% of allowance → THEN Flag · (Watchdog, r1)
- IF Prompt or template changed → THEN Golden test client re-run and compared before use · (Engine, r1)
- IF Engine-labelled emails: more than 10 in an hour, or more than 1 to any client in 20 hours → THEN Circuit breaker: all engine sending stops. Your own sends and the vacation reply never count · ELSE Only you reset it; Layer 1 covers · (Engine, r4) [test]
- IF Any outgoing email → THEN Pre-send check: thread belongs to this record; listed sender greeted by first name (unknown: "Hi,"); links only from the record: form link, upload link, and on the preview email the approved version's fixed link; no braces, CC, model chatter or other clients' details; filled text under 300 characters · ELSE Fail: not sent, flagged · (Engine, r5)
- IF A scheduled run needs an approval to send or write → THEN All engine tasks set to automatic approval; full unattended test before 26 Oct including one real send · ELSE If it can't send alone, Layer 2 is off for the trip; Layer 1 only · (Matt, r2) [test]
- IF A Google connection may expire 7 days after login → THEN Before 26 Oct, move to a Google connection that doesn't expire weekly; prove it with a test read on day 8 of a dry run · ELSE Not proven: plan Layer 1 only from Fri 6 Nov; reconnecting is your first job on Sat 7 Nov · (Matt, r4) [test]
- IF A row is updated in several steps → THEN Every other field first, Build Status last; next run re-checks rows missing required fields · ELSE Move back one stage, flag "half update" · (Engine, r2)
- IF A Notion create is retried after a rate limit → THEN Look for it first by a unique key · ELSE Duplicates merged Saturday; never two builds · (Engine, r2)
- IF A row sits in one status past its limit (intake 10 working days, ready 1 day, building 4 hours, QA failed or On Hold 7 days) → THEN Amber: "stuck in {status} since {date}", top of Saturday · ELSE Every status has a named exit owner · (Engine, r2)
- IF Away window ends (Sun 8 Nov 23:59) → THEN Vacation reply has its end date set when switched on. Mon 08:00 you check: WhatsApp away off, pauses and breaker reviewed, ENGINE DOWN label cleared, kill switch. From 9 Nov, confirmations become drafts for you · ELSE Delayed: push the end date back from your phone before Sun 23:59 · (Engine, r4)
- IF 3 or more quarantines or half updates in one day → THEN Engine pauses builds itself; inbox and Layer 1 carry on · ELSE Red at the top of Saturday · (Engine, r4)
- IF A connection fails its test read → THEN Flag; Layer 1 still answers everyone · ELSE Reconnect everything as the last thing before you leave; expiry times on the Saturday list · (Watchdog, r4)
- IF Any engine-wide pause → THEN Records how it lifts: Make down and usage reserve after 2 clean test runs; publishing after 6 hours once a test publish works; build pause and breaker only by you · ELSE Every active pause listed first on Saturday · (Engine, r4)
- IF Reminder wording, Templates 1–5, fixed asks or questions not approved in writing by Fri 30 Oct 12:00 → THEN That category falls back to Layer 1 only for the whole trip · (Matt, r4)
- IF Make free plan: 2 of 2 scenarios, 999 of 1,000 credits (18 Oct). M1 alone needs about 2,900 a month → THEN Upgrade by 23 Oct (your spend decision); the free plan can't run the file saver for 9 days · ELSE Not upgraded: Layer 2 off for the trip, Layer 1 only · (Matt, r5)
- IF Between 20:00 and 08:00 → THEN Watchdog measures from the 20:00 run; never starts a run or labels the inbox overnight · (Watchdog, r5)
- IF More than 8 engine emails due in one run → THEN Send 8, carry the rest to the next run, oldest first · (Engine, r5)
- IF Any signer-only line → THEN Pre-send check confirms the recipient is the signer · ELSE Not the signer: blocked · (Engine, r7)
- IF A red is raised → THEN Each red type says whether it stops the build. Stop replies and builds: money, anger, legal, cancel, disputed deposit, company status, contact change, credentials, named comparison. Stop that item only: urgent-not-ours, third-party claim in one sentence, bounce, preview enquiry · ELSE Any red type not listed: stops replies and builds until you clear it · (Engine, r14)
- IF Limits (20 hours, circuit breaker) → THEN Counted per email address as well as per client · (Engine, r7)
- IF Rules disagree → THEN Order: 0 exceptions written into the red-word rule (an email whose only red word is "cancel", in the same sentence as call, meeting, kickoff or Calendly, payment-only words) apply first, so those never count as red; 1 red wins, and red never allows a send beyond Layer 1, the holding line and the urgent-not-ours security line, both only to an approved sender; 2 unknown sender = Layer 1 only for replies (pausing always allowed); 3 the most specific rule; 4 the newest round · (Engine, r14)
- IF Any text came from a client (email, form, file, photo text, transcript) → THEN The model step has no send, forward, share, delete or Notion-write tools and returns only a fixed list of fields; scripts do all writing and sending · ELSE Any output containing an address, URL or another record ID is thrown away; red · (Engine, r10) [test]
- IF Connections for E1–E5 are set up → THEN Read, label and draft only; sending only through the pre-send script. Proven before 26 Oct by trying a forward and a Drive share (both must fail) · (Matt, r10) [test]
- IF Any Clients folder or file has link sharing or a non-Propulsion account → THEN Red and revoked automatically (E2 checks daily); upload links per record, write-only, expire at launch or cancellation · (Watchdog, r10) [test]
- IF Kill switch missing or unreadable, or a record's email, phone, Approved or Build Status changed by anyone but the engine or you during the trip → THEN Switch treated as ON / row frozen, Layer 1 only. Notion guests removed and database locked before 30 Oct · (Engine, r10)
- IF A file isn't used on the live site → THEN Retention schedule (your go, then in the privacy notice): deleted 90 days after launch or cancellation; voice notes once facts are confirmed; unmatched Unsorted after 30 days; credential emails once the client is told. Privacy notice names Make, Claude and Drive · ELSE Deletes are your decision; nothing is deleted until you approve the schedule · (Matt, r10)
- IF Make goes quiet (no log line for 3 hours in working hours) → THEN The Claude watchdog flags "Make down" itself (the Make heartbeat dies with Make) · ELSE Files stay safe in Gmail; Monday make-up list · (Watchdog, r13)
- IF Thu 29 Oct go/no-go → THEN Make must show at least 3 times the forecast operations still available for the trip · ELSE Otherwise: Layer 2 off · (Matt, r13)
- IF Agents and skills for Claude Code → THEN Each AG profile is a file in the repo (.claude/agents) with its model set; procedures as skills (.claude/skills); one CLAUDE.md with the launch check and hard rules; the first session on Tue 20 lists what it can see · ELSE Not listed: that part doesn't run unattended · (Matt, r13) [test]
- IF You reset the circuit breaker → THEN Queued sends older than 24 hours are dropped and re-planned, never sent in a burst · (Engine, r14)

### S12 At 500 clients (phase 2: each needs your go)
- IF Green row whose trade and template have 10 clean sends in a row → THEN Proposal: goes straight to a send queue; you spot-check 1 in 10. Amber and red go in a daily 12:00–15:00 batch · ELSE Today's rule stands until you approve: you see every preview · (Engine, r8)
- IF A message category has 10 clean sends in a row, no complaint, no pre-send fail → THEN Sends itself (your 17 Oct principle: standing approval per template after 10 clean sends); any red or pulled draft resets it to drafts · (Matt, r8)
- IF Row is Live and a Care edit arrives → THEN Care stage with its own edit counter; small text, phone or photo swaps built and Gate A'd, published after the track record; edit 3+ in a month or anything new is a change order for you · ELSE Launch itself always stays yours · (Engine, r8)
- IF More than 10 deposits in a week → THEN Written kickoff form by default, 20-minute call only for gaps; starts staggered at 10 a week, stated on the payment page · (Engine, r8)
- IF Registrar offers delegate access → THEN Required at kickoff; not pointing at 48h: automatic re-check and guide resend; call only at 96h · (Engine, r8)
- IF A register has a public search (Companies House, ICO, Gas Safe) → THEN Engine checks it and saves a screenshot; you review mismatches only; Live sites re-checked quarterly, a lapsed badge removed and flagged · (Engine, r8) [test]
- IF A master template fix (security, legal, broken element) → THEN Rolled out in waves (10, 50, the rest), Gate A on each, automatic rollback on any fail; design changes for new builds only · (Engine, r8)
- IF Over 100 clients → THEN Circuit breaker scales to clients ÷ 25 an hour; auto-resets after 2 clean runs unless red; per-client 20-hour rule stays · (Engine, r8)
- IF An email answers something the client asked (edit done, a reply) → THEN Exempt from the 20-hour hold; the hold covers only messages the engine starts · (Engine, r8)
- IF A payment matches its invoice in Tide by amount and reference → THEN Auto-ticked; only unmatched payments and dispute words come to you · ELSE Needs a Tide read route (needs testing) · (Engine, r8) [test]
- IF Care payment fails twice or the client cancels → THEN 30-day notice, handover zip offered, website records removed on day 30 (email records never touched); red only if still live and unpaid at day 30 · (Engine, r8)
- IF Client is Live → THEN Files archived after launch, used images kept; any allowance past 60% sends you a costed upgrade a month ahead · (Engine, r8)
- IF A red type has a fixed fix (bounce, Unsorted with a name match) → THEN Engine prepares the fix; you tick it; calls only for money, anger or legal · (Engine, r8)
- IF Any Live site → THEN Daily uptime, form and SSL check; one automatic retry, then red; monthly one-line report after the track record · ELSE This is what Care sells as monitoring · (Engine, r8)
- IF Same trade within a set distance → THEN Written once (exclusive or not, layout variant forced); engine applies it without asking · (Matt, r8)
