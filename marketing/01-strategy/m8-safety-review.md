# M8 Safety Review — Reddit guardrails assessment

_Reviewer: reddit-safety (<task-id>). Reviewed: m8-channel-plan.md (337 lines, sha256 a1019cf0…)._
_Date: 2026-10-01. Status: complete. Downstream: m8-outreach-strategy.md (<task-id>)._

This review assesses every section of the channel plan against Reddit's published content policy,
anti-spam systems, and the norms documented in the M8 voice guide (m8-voice.md). Verdict per section:
PASS (no changes needed), PASS-WITH-CHANGES (safe with the listed corrections), or BLOCK (must be
fixed before any execution).

---

## 1. Rate limits

### 1.1 Steady-state cadences

| Channel | Proposed | Verdict | Corrected (if needed) | Rationale |
|---------|----------|---------|----------------------|-----------|
| r/britishcolumbia | 3-4 comments/week | PASS-WITH-CHANGES | 3 comments/week max (see below) | 4/week is within platform tolerance for an established account but the plan assumes a new or low-karma account. Reddit does not publish hard rate limits, but new accounts routinely hit "rate exceeded" errors above 3-4 actions/day across all subs. At 3-4 comments/week the per-action interval is fine, but the **combination** with r/vancouver (2-3) and r/QAnonCasualties (1-2) pushes the weekly total to 6-9 comments across 3 subs — a pattern that low-karma accounts cannot sustain without triggering spam filters. |
| r/vancouver | 2-3 comments/week | PASS-WITH-CHANGES | 2 comments/week max | Same reasoning. The plan correctly notes this sub is faster-moving; comments get buried faster, so volume is less effective anyway. |
| r/QAnonCasualties | 1-2 comments/week | PASS | — | Lowest cadence. Support-community norms naturally limit frequency. No correction needed. |
| r/britishcolumbia modmail | One message | PASS | — | Single message, no follow-up. No rate-limit concern. |

**Required change (Section 2.2, lines 99-104):** Cap the combined steady-state total at **5 comments/week across all channels** (not 6-9). The simplest split: r/britishcolumbia 3, r/vancouver 2, r/QAnonCasualties 1 (max 6 but only if QAC has a genuine engagement opportunity; otherwise 5). The plan's table should be updated accordingly.

### 1.2 Ramp schedule

| Phase | Proposed cadence | Verdict | Issue |
|-------|-----------------|---------|-------|
| Lurk (days 1-3) | 0 comments | PASS | Correct. |
| Low-stakes replies (days 4-7) | 1-2 comments/week total | PASS-WITH-CHANGES | 1-2/week is safe, but the plan says "target housing, cost-of-living, and local-news threads" — if all 2 comments land in the same sub on the same day, a new account will hit the per-sub rate limiter. |
| Value-add (days 8-14) | 3-5 comments/week total | PASS-WITH-CHANGES | 5/week across 3 subs is the upper bound of safe for a new account. At day 8 the account is only 8 days old. Many subs enforce a minimum account age of 7-30 days and minimum karma thresholds (often 50-100 comment karma). A day-8 account with fewer than 10 comments will be filtered by AutoModerator in many mid-to-large subs. |
| Original posts (days 15+) | Max 1 post/week per channel | PASS | One original post per week is safe at this stage, provided the account has accumulated comment karma and age. |

**Required change (Section 2.3, lines 113-116):**

1. **Line 114 (low-stakes replies):** Add: "Distribute the 1-2 comments across different days and different subs. Never post 2 comments in the same sub on the same day during this phase."
2. **Lines 115-116 (value-add):** The 3-5 comments/week target is too aggressive for a ~10-day-old account posting in political-adjacent subs. Cap at **3 comments/week** during days 8-14. The plan's 3-5 range should become 2-3. Rationale: a new account posting 5 political-adjacent comments per week across 3 subs, with disclosure language that mentions a tool, will trigger spam heuristics. The tool mention is the risk amplifier — even disclosed, a pattern of comments that all lead back to the same site looks like promotion to Reddit's classifiers.

### 1.3 Election-period blackout

**Open question 6 (line 304):** The plan caps engagement at steady-state levels for Oct 22-24 (final 3 days before E-day). The safety review recommends **PASS-WITH-CHANGES**: maintain steady-state cadence but add a hard rule: **no new threads, no original posts, no first-time tool mentions during Oct 22-24**. Comments in existing conversations are fine; initiating new engagement is not. The election window is the highest-scrutiny period and any new activity that reads as electioneering — even neutral — will attract reports.

---

## 2. Content risk

### 2.1 Harassment and brigading risk

**Verdict: PASS** — The channel plan and voice guide together establish strong anti-harassment and anti-brigading guardrails:

- Section 1.1, principle 4 (line 31-32): "One account per person, real disclosure. No multi-accounting, no vote coordination, no astroturfing." This directly addresses Reddit's rule against coordinated inauthentic behavior.
- Voice guide Section 5 (lines 186-209): Explicitly cites Reddit's rules against harassment, impersonation, vote manipulation, and spam. Lists each rule and the practical consequence for M8.
- Channel plan Section 3.3 (lines 196-202): "What never happens" — no day-1 posting, no tool mentions in first comment, no DMs, no engagement in final 3 days. All correct.

No changes required to the anti-harassment/anti-brigading posture.

### 2.2 Vote manipulation risk

**Verdict: PASS** — The plan explicitly prohibits vote coordination (Section 1.1, principle 4; voice guide Section 0, rule 2; voice guide Section 5). Reddit's vote-manipulation detection in 2026 flags any pattern where votes are shaped by coordinated action rather than organic discovery. The plan's one-account-per-person rule and prohibition on asking for upvotes are sufficient.

One caution: the plan's "engagement ladder" (Section 3.1) defines success partly by reply count and conversation depth. This is fine as a measurement framework, but the plan should explicitly state that **posters must never ask for replies, upvotes, or engagement**. The current text does not say this; it implies organic measurement but does not close the loophole.

**Required change (Section 4.1, line 211):** Add to the success-signal table header or as a note: "All engagement signals are passively observed. Posters must never solicit replies, upvotes, shares, or any form of engagement."

### 2.3 Coordinated inauthentic behavior risk

**Verdict: PASS-WITH-CHANGES** — The biggest risk in this category is the **disclosure pattern itself**. Reddit's "Be authentic" rule (voice guide Section 5) prohibits intentionally misleading others. The plan's disclosure model (P6 from voice guide, line 103-104) is:

> "Disclosure: I help build a BC voter-information tool (not affiliated with any party). This is just conversation; ignore the tool if it's not your thing."

This disclosure sentence is flagged as needing human approval (voice guide Section 8, line 251; channel plan open question 3, line 293). The safety review confirms: **the draft disclosure is compliant but should be tightened.** The phrase "This is just conversation" could be read as downplaying the organizational nature of the activity. A better version:

> "Disclosure: I help build BC Vote Match, a non-partisan voter-information tool. I'm here to understand how people are thinking about the election — the tool is just context, not a pitch."

**Required change (voice guide P6, line 103-104):** Replace the disclosure draft with the tightened version above. This is a drafting change, not a structural one — the voice guide already flags it for human sign-off.

### 2.4 r/QAnonCasualties — elevated content risk

**Verdict: PASS-WITH-CHANGES** — This is the highest-risk channel in the plan. Posting in a peer-support community with any organizational affiliation carries a real risk of being perceived as predatory, opportunistic, or exploitative. The plan recognizes this (open question 4, lines 297-300) and includes several mitigations:

- Intervention-poster role (separate from general poster)
- Never post original content in this sub
- Never mention the tool unless directly asked
- Kill signal: leave immediately if mods or community object

These are all correct, but the safety review adds two specific guardrails:

**Required changes (Section 3.2, r/QAnonCasualties block, lines 171-180):**

1. **Add a minimum karma requirement for the intervention-poster account.** The account posting in r/QAnonCasualties must have at least **200 comment karma and 30 days account age** before its first comment in this sub. This is a higher bar than the general ramp because the community's trust sensitivity is higher. Line 173 ("Stage 1 begins Oct 9") should be gated: "Stage 1 begins Oct 9 ONLY IF the poster account has ≥200 comment karma. If not, extend the lurk phase until the threshold is met."
2. **Add: "Never mention the tool even when asked, unless the question is specific and direct."** The current rule (line 179) says "Never mention the tool unless someone is asking for exactly the kind of resource it is." Tighten this to: "Never mention the tool unless a user asks a question that the tool directly answers (e.g., 'is there a site that shows where BC candidates stand on housing?') AND the question is asked in a resource-seeking thread, not a grief or venting thread. When in doubt, do not mention the tool."

### 2.5 Modmail content risk

**Verdict: PASS** — The modmail approach (Section 3.2, lines 182-192) is correctly scoped: transparent, single message, no follow-up, respect silence as tacit tolerance, comply with any restrictions. This is within Reddit norms and does not constitute spam or harassment. The plan correctly notes that modmail is not a posting channel (line 41: "Not a posting channel. A single, transparent modmail introduction").

**Open question 5 (line 302):** The safety review confirms that a single unsolicited modmail is within Reddit norms. Many subs prefer advance notice; none penalize it. The plan's "no follow-up if no response" rule is the key safety mechanism — repeated modmails would be harassment.

### 2.6 Partisan content risk (neutrality)

**Verdict: PASS** — The Neutrality Protocol (docs/content/NEUTRALITY-PROTOCOL.md, Rule 4) and the voice guide (Section 0, rule 1) both establish that M8 copy says "here is where you sit," never "party X is wrong." The channel plan inherits this. No M8 content may argue a party is wrong. The plan's audience targeting (Politically Homeless, Friends & Family) is issue-based (cost-of-living, housing, healthcare), not party-based. No change required.

---

## 3. Account risk

### 3.1 Shadowban and ban exposure per channel

| Channel | Shadowban risk | Ban risk | Mitigations in plan | Gaps |
|---------|---------------|----------|---------------------|------|
| r/britishcolumbia | MODERATE | LOW | Lurk-first, disclose, no original posts without mod okay | No account warm-up phase (see 3.2) |
| r/vancouver | MODERATE | LOW | Same as above | Same gap |
| r/QAnonCasualties | HIGH | MODERATE | Intervention-poster role, no tool mentions unless asked, kill-if-unwelcome rule | No minimum account age/karma threshold for this sub (see 2.4) |
| r/britishcolumbia modmail | NONE | NONE | Single message, no follow-up | None |

**Assessment:** The plan's strongest account-protection measure is its deliberate conservatism — low volume, lurk-first, no day-1 posting, real disclosure. The weakest point is the absence of a pre-Reddit warm-up phase.

### 3.2 Account warm-up (open question 2, line 290)

**Verdict: PASS-WITH-CHANGES** — The plan's ramp schedule starts engagement in political-adjacent subs on day 4. This is too early for a new or low-karma account. Reddit's anti-spam systems and subreddit-level AutoModerator rules commonly filter accounts that are:

- Less than 7-30 days old
- Have fewer than 50-100 comment karma
- Post in political subs as their first activity
- Have no prior participation in the subreddit

A new account that goes from 0 to posting in r/britishcolumbia (482K subs, political content) within 4 days will be filtered by AutoModerator — comments will be silently removed, invisible to everyone except the poster. This is worse than a ban because the poster won't know it's happening.

**Required change (Section 2.3, add a pre-stage before "Lurk"):**

Insert a **Stage -1: Account warm-up** before the Lurk phase:

```
| Warm-up | Days -7 to -1 (Sep 29 - Oct 5) | Using the M8 poster account, post 5-10 genuine,
non-political comments in mid-size, low-moderation subs that are NOT in the channel plan.
Examples: r/CasualConversation, r/books, r/coffee, r/hiking, r/vancouverphotos.
No disclosure, no tool mentions, no BC politics. Goal: establish comment karma (target 50-100)
and a visible, non-spam comment history. | 1-2 comments/day |
```

This pre-stage adds one week before the Oct 6 lurk start. If the safety review completes Oct 1-2, warm-up runs Oct 2-5, lurk begins Oct 6 as planned. If the review slips, the whole schedule shifts — the lurk phase cannot start until the account has at least 50 comment karma and 7 days of visible non-political activity.

### 3.3 Account rotation

**Verdict: PASS (not needed)** — The plan assumes one account per person (Section 7, assumption 2). For the proposed cadence of 5-6 comments/week total, one account is sufficient. Account rotation becomes necessary only if:

- An account is shadowbanned or suspended
- The plan expands to 10+ comments/week
- A poster is operating in a sub where they have been banned

The plan should add a contingency: if the primary account is shadowbanned, all M8 activity pauses until the safety reviewer assesses the cause and approves a replacement account.

**Required change (add to Section 5 or Section 7):** "If the poster account is shadowbanned or suspended, all M8 Reddit activity pauses immediately. The safety reviewer assesses the cause, and no replacement account begins posting until the review is complete and a new warm-up period is observed."

### 3.4 Link risk

**Verdict: PASS-WITH-CHANGES** — The plan correctly delays tool mentions until Stage 2+ and never mentions the tool in a first comment. However, Reddit's spam classifiers also flag domains. If every M8 comment that mentions the tool links to `bcvotematch.ca`, the domain will accumulate a spam score. Mitigations:

**Required change (Section 2.1, add to rate-limit philosophy, line ~96):** "Vary the link format when mentioning the tool. Use plain-text mentions ('BC Vote Match') as often as direct links. When linking, use different pages on the site (homepage, methodology page, specific candidate comparison pages) rather than the same URL every time. Never use URL shorteners."

---

## 4. Escalation

### 4.1 Thread turns hostile

**Verdict: PASS** — The voice guide (P8, lines 112-115) handles this well: "When a thread heats up, gets hostile, or starts repeating, stop replying. Disengagement is a voice choice, not a failure." The channel plan's kill signals (Section 4.1) also cover hostile-domination scenarios: if hostile replies outnumber neutral/positive ones, the channel is dropped.

**One addition needed:** The plan needs an explicit step-by-step escalation protocol for the poster, not just the principle.

**Required change (add to Section 4 or as a new subsection 4.4):**

```
### 4.4 Escalation protocol — what to do when a thread turns hostile

1. STOP REPLYING. Do not post one more comment "to clarify." Hostile threads do not get
   calmer with more engagement.
2. DO NOT DELETE your existing comments unless a mod or the safety reviewer instructs you to.
   Deletion reads as covering tracks and fuels the fire.
3. LOG the incident: thread URL, time, a brief description of what happened, and a screenshot
   of the hostile exchange (stored locally, not posted).
4. REPORT to the safety reviewer within 24 hours. The reviewer decides whether:
   a. The incident is isolated → continue the channel at reduced cadence.
   b. The incident is part of a pattern → adjust or kill the channel (Section 4.1).
   c. The incident involves doxxing, threats, or targeted harassment → report to Reddit
      admins and pause all M8 activity in that sub until resolved.
5. NEVER engage with the hostile user in DMs, in other threads, or on other platforms.
```

### 4.2 User in crisis

**Verdict: PASS-WITH-CHANGES** — The voice guide (Section 4, DM subsection, line 173-174) says: "if someone describes self-harm or immediate danger, do not counsel them. Send one short message pointing to a real local crisis line or the appropriate subreddit resource, then stop." This is correct but incomplete — it only covers DMs, and it doesn't name specific resources.

**Required change (replace the crisis paragraph in voice guide Section 4, line 173-174, and cross-reference in the channel plan):**

```
### Crisis protocol — what to do when a user describes self-harm, violence, or immediate danger

This applies in comments, replies, AND DMs.

1. DO NOT COUNSEL. You are not a crisis worker. Do not ask questions, do not explore feelings,
   do not offer advice.
2. POST ONE REPLY with the appropriate resource and nothing else:
   - BC-specific: BC Crisis Line 1-800-SUICIDE (1-800-784-2433) — 24/7, free.
   - Canada-wide: Talk Suicide Canada 1-833-456-4566 or text 45645 (4 PM - midnight ET).
   - r/QAnonCasualties specific: link to the sub's crisis resources wiki page.
   - If the user is in immediate danger (specific threat, named location, named person):
     call 911 (or local emergency) and report to Reddit admins via reddit.com/report.
3. STOP. Do not reply again. Do not check in later. Do not follow up.
4. LOG the incident (thread URL, time, resource provided) and report to the safety reviewer
   within 24 hours. The reviewer ensures the response was appropriate and files the record.
5. The crisis response does NOT include the disclosure sentence. This is not a branding moment.
```

Add a cross-reference in the channel plan, Section 3.2, r/QAnonCasualties block: "If a user describes self-harm, violence, or immediate danger, follow the crisis protocol in m8-safety-review.md Section 4.2. Do not counsel. Point to a resource and stop."

---

## 5. Open questions from the channel plan — resolved

| # | Question (line ref) | Answer |
|---|-------------------|--------|
| 1 | Rate limits (line 286) | See Section 1 above. Cadences are safe IF the warm-up pre-stage is added and the combined weekly cap is reduced to 5 comments. |
| 2 | Account age and karma (line 290) | Yes, the plan needs a pre-stage warm-up period. See Section 3.2. |
| 3 | Disclosure wording (line 293) | The draft is compliant but should be tightened. See Section 2.3 for the approved rewrite. Needs human sign-off before execution per voice guide Section 8. |
| 4 | r/QAnonCasualties risk (line 297) | Additional guardrails required: minimum 200 comment karma / 30 days account age, and tighter "never mention the tool" rule. See Section 2.4. |
| 5 | Modmail approach (line 302) | Single unsolicited modmail is within norms. The "no follow-up" rule is sufficient. No change needed. |
| 6 | Election-period escalation (line 304) | Steady-state cadence is acceptable but add: no new threads, no original posts, no first-time tool mentions during Oct 22-24. See Section 1.3. |

---

## 6. Pre-flight checklist (run before every posting session)

The poster must complete this checklist before writing or posting any comment. Check every item.

```
PRE-FLIGHT CHECKLIST — M8 REDDIT ENGAGEMENT
Run before every session. If any item fails, do not post until it is resolved.

□ 1. ACCOUNT CHECK
   □ Account age is ≥ 7 days (≥ 30 days for r/QAnonCasualties).
   □ Comment karma is ≥ 50 (≥ 200 for r/QAnonCasualties).
   □ Account is NOT shadowbanned (check r/ShadowBan or reddit.com/appeal).
   □ No prior comments in this sub have been removed by mods in the last 48 hours.

□ 2. CHANNEL CHECK
   □ Target subreddit is in the active channel list (Section 1.2 of channel plan).
   □ Secondary channel? → Activation trigger is met (Section 1.3).
   □ Today is NOT in the Oct 22-24 blackout window for new threads/tool mentions.

□ 3. CADENCE CHECK
   □ This week's comment count is below the per-channel cap.
   □ This comment is NOT the second comment in the same sub on the same day (Stage 1).
   □ No comment posted in the last 10 minutes (new-account rate limit).

□ 4. CONTENT CHECK (voice guide Section 7)
   □ Did I ask something before I asserted something? (P1, P2)
   □ Is any line aimed at the person rather than the claim? If yes, cut it. (P3, P4)
   □ Does this leave the other person somewhere to go, or does it end with a verdict? (P5)
   □ Have I disclosed my connection to the tool where it could matter? (P6)
   □ Would this survive being screenshotted, and does it follow the subreddit's rules? (P7, Section 5)
   □ No party names, no party judgments, no "party X is wrong" language (Neutrality Protocol Rule 4).
   □ If this is a FIRST comment in a new community: no tool mention, no link, disclosure only.

□ 5. CRISIS CHECK
   □ Does the user's comment describe self-harm, violence, or immediate danger?
     → If YES: follow crisis protocol (Section 4.2). Do NOT use the normal voice guide.
     → If NO: proceed.

□ 6. POSTING CHECK
   □ Comment is written specifically for this thread (not copy-pasted).
   □ No URL shorteners; link is to the tool's own domain (bcvotematch.ca) or omitted.
   □ Disclosure is included if this is the first comment in this thread where affiliation matters.

□ 7. LOGGING
   □ After posting: log the comment (channel, thread URL, type, disclosure, timestamp).
```

---

## 7. Verdict summary

| Section | Verdict | Items requiring change |
|---------|---------|----------------------|
| 1. Rate limits (cadences) | PASS-WITH-CHANGES | Cap combined weekly total at 5 comments. Cap Stage 2 ramp at 3 comments/week. Add distribution rule (no 2 comments same sub same day). |
| 1. Rate limits (ramp) | PASS-WITH-CHANGES | As above plus warm-up pre-stage. |
| 1. Rate limits (election blackout) | PASS-WITH-CHANGES | No new threads/tool mentions Oct 22-24. |
| 2. Content risk (harassment/brigading) | PASS | — |
| 2. Content risk (vote manipulation) | PASS-WITH-CHANGES | Add explicit prohibition on soliciting engagement. |
| 2. Content risk (coordinated inauthentic) | PASS-WITH-CHANGES | Tighten disclosure wording. |
| 2. Content risk (r/QAnonCasualties) | PASS-WITH-CHANGES | Add karma/age gate. Tighten tool-mention rule. |
| 2. Content risk (modmail) | PASS | — |
| 2. Content risk (neutrality) | PASS | — |
| 3. Account risk (shadowban/ban) | PASS-WITH-CHANGES | Add warm-up pre-stage. Add contingency for shadowban. Add link-diversity rule. |
| 3. Account risk (rotation) | PASS | — |
| 4. Escalation (hostile threads) | PASS-WITH-CHANGES | Add step-by-step escalation protocol. |
| 4. Escalation (user in crisis) | PASS-WITH-CHANGES | Replace crisis paragraph with full protocol; name specific BC/Canada resources. |
| 5. Open questions | RESOLVED | All 6 answered. |
| 6. Pre-flight checklist | NEW | Added. |

**Overall verdict: PASS-WITH-CHANGES.** The M8 channel plan is fundamentally sound — its conservatism, disclosure model, and respect for community norms put it on the right side of Reddit's rules. The changes required are specific, bounded, and actionable. No section is blocked. After the listed changes are applied, the plan is cleared for execution.

---

## 8. Required changes — consolidated action list

Ordered by priority. Every change names the exact file, section, and line range it applies to.

### m8-channel-plan.md

1. **Section 2.2 (lines 99-104):** Update steady-state cadence table. Cap r/britishcolumbia at 3, r/vancouver at 2. Add combined total note: "Weekly total across all channels: max 5 comments."
2. **Section 2.3 (lines 113-116):** Cap Stage 2 (value-add) at 3 comments/week (was 3-5). Add distribution rule: no 2 comments in same sub same day during Stage 1.
3. **New pre-stage before Section 2.3 (before line 111):** Insert "Stage -1: Account warm-up" — 7 days of non-political comments in low-moderation subs to build 50-100 comment karma.
4. **Section 2.1 (line ~96):** Add link-diversity rule: vary URLs, prefer plain-text mentions, no shorteners.
5. **Section 3.2, r/QAnonCasualties (lines 173, 179):** Add minimum 200 comment karma / 30 day account age gate for intervention-poster. Tighten tool-mention rule: only when a specific, direct question is asked in a resource-seeking thread.
6. **Section 3.3 (line ~202) or Section 7 (line ~326):** Add shadowban contingency: if account is shadowbanned, pause all activity until safety reviewer clears a replacement.
7. **Section 4 (after line 243 or as new subsection):** Add escalation protocol (Section 4.1 of this review) and crisis protocol (Section 4.2 of this review). Cross-reference crisis protocol in r/QAnonCasualties block.
8. **Section 4.1 header (line 211):** Add: "All engagement signals are passively observed. Posters must never solicit replies, upvotes, shares, or any form of engagement."

### m8-voice.md

9. **P6 (lines 103-104):** Replace disclosure draft with: "Disclosure: I help build BC Vote Match, a non-partisan voter-information tool. I'm here to understand how people are thinking about the election — the tool is just context, not a pitch."
10. **Section 4, DM crisis paragraph (lines 173-174):** Replace with full crisis protocol (Section 4.2 of this review), covering comments, replies, and DMs, with named BC/Canada crisis resources.