# NEUTRALITY AUDIT — copy deck (marketing/05-copy)

Audited against Gate 1 of `marketing/06-review/RUBRIC.md` and Rule 4 of `docs/content/NEUTRALITY-PROTOCOL.md`, on 2026-10-01. Every piece in `COPY-DECK.md` is listed with a verdict. The rejected phrasings section is the real working record: candidates that were written during drafting and then cut, so the rejections are visible rather than implied.

## Gate 1 standard applied

Public copy says "here is where you sit", never "party X is wrong", "party Y is lying", or any judgement about a party or its supporters. No persuasive copy for or against any party, candidate, or outcome. No get-out-the-vote tilt in any direction. Descriptive language about a party's position comes from the party's own words; where we summarize, we summarize the quote and nothing more. Neutrality lives in the method, not in tone, so a piece passes only if both the wording and the underlying claim are neutral.

## Verdict table

| id | piece | Gate 1 verdict | basis |
|----|-------|----------------|-------|
| X-01 | Launch post | PASS | Names no party; "each party's published positions" is the tool's mechanic, not a claim about any party. No outcome implied. |
| X-02 | What it is | PASS | "What the parties have actually said, in public, in their own words" describes sourcing, not truth-value of any party. |
| X-03 | Receipts | PASS | Provenance claim about our own pipeline (quote, hash, archive). Says nothing about what any party said. |
| X-04 | "No position" is real | PASS | The guessing ban applies identically to all five parties; no party is named or implied to lack positions. |
| X-05 | What it doesn't do | PASS | Refusal to endorse/predict. Listing what sits outside the method (leaders, record, trust) is scope definition, not commentary. |
| X-06 | Privacy | PASS | Verifiable factual claims about the build (no account, no login, no trackers; METHODOLOGY.md, src/lib/site.ts). No party content. |
| X-07 | Corrections invited | PASS | "Think we have a code wrong" invites challenge to our codes symmetrically; the procedure is identical for every party. |
| X-08 | Recode notice | PASS | Describes versioned recoding that applies to every party alike. "Check the version date on your result" is factual, not a verdict on any movement. |
| X-THREAD | 5-post thread | PASS | Method explanation end to end. Post 4/5 disclaims the map ("reading aid, not a measurement of anyone") and states fixed party ordering. Ends on corrections, not on voting. |
| REDDIT-BC | r/britishcolumbia post | PASS | Disclosure-first; "what it doesn't do" paragraph carries the neutrality claim explicitly; invites corrections; no party discussed. |
| REDDIT-VAN | r/vancouver post | PASS | Same content spine as REDDIT-BC. The local line ("housing and cost of living are two of the six topics") is a statement about our question set, verifiable in METHODOLOGY.md, not about party performance. |
| NOTE-01 | Launch note | PASS | Scope, transparency, funding independence. "Where a party has not stated a position, we do not guess one" is method, applied uniformly. |
| FAQ-01 | "Who to vote for?" | PASS | Explicit non-recommendation. "Plenty of people find they are closest to a party they will never vote for, and that is a perfectly good outcome" was checked for GOTV tilt: it legitimises ignoring the result, which is the opposite of persuasion. |
| FAQ-02 | "Numbers rigged?" | PASS | Answers with inspectable artefacts (quotes, table, freeze, open source). Makes no claim about any party's honesty or dishonesty. |

14 pieces, 14 PASS, 0 REVISE, 0 REJECT in the final deck. The REJECT column below is not empty though: it lives in the cut list.

## Note on m8-voice.md

`marketing/01-strategy/m8-voice.md` frames outreach as engaging people "reached by extremist narratives". That framing is not this campaign's posture and was not adopted. A tool that intervenes to correct someone's beliefs argues with its users, and a tool that argues with its users cannot credibly claim neutrality of method. Gate 1 would in any case reject the register ("tell them the truth", "don't let the lies stand") because it necessarily characterises some party or campaign as deceptive. Only the practical Reddit-norms material from m8-voice was used (read the room, disclose affiliation, expect skepticism, answer method questions, don't argue in comments). If the director wants the m8 posture, that is a strategy decision to make explicitly, not something this deck should smuggle in.

## Phrasings deliberately rejected

Each entry is a candidate that was written during drafting and then cut. Verdict: REJECT unless marked otherwise.

| # | candidate phrasing | where it was tried | why it was cut |
|---|--------------------|--------------------|----------------|
| R-01 | "See which party actually stands with you." | X-01 opening line | "Stands with you" implies alliance and endorsement; "actually" implies other sources of information are false. Gate 1: judgement plus implication of a preferred outcome. |
| R-02 | "Don't let the campaign spin decide your vote." | X-02 | Calls campaign communication "spin", which is a judgement about parties' honesty. Also a voting directive. Gate 1 twice over. |
| R-03 | "Cut through the noise and find your real match." | X-THREAD 1/5 | "Noise" devalues every party's communication; "real match" implies the tool reveals a truth the parties hide. |
| R-04 | "Most voters never read a platform. You can do better." | NOTE-01 first line (lifted from ABOUT.md) | Fine inside ABOUT.md as project motivation, but in outreach it reads as a scold and a self-congratulation. Also smuggles a GOTV-adjacent "you should read platforms" nudge. Cut to neutral scope language. |
| R-05 | "Find out who's really on your side." | X-01 variant | Endorsement framing ("on your side"), plus "really" conspiratorial edge. |
| R-06 | "The election is days away. Don't miss your chance to compare." | X-08 variant | Urgency framing is a get-out-the-vote tilt even without naming a party. Gate 1: "no framing that treats one result as good or bad", and urgency pushes action toward voting. Cut; the recode notice stays purely informational. |
| R-07 | "See how close the parties really are to ordinary British Columbians." | X-THREAD 4/5 | "Ordinary British Columbians" sets up a people-vs-parties frame; "really are" again implies hidden truth. |
| R-08 | "Spoiler: the result might surprise you." | X-02 variant | Engagement bait (rubric) and it pre-signals that some party's position is surprising, i.e. a commentary on positions. |
| R-09 | "Whose side are you on? Find out in 3 minutes." | X-01 variant | "Whose side" is a partisan frame by construction. REJECT without further analysis. |
| R-10 | "Every party's promises, fact-checked." | X-03 variant | "Fact-checked" claims we adjudicate truth of promises. We verify quotes, not promises. Would breach the neutrality claim and the truthfulness gate. |
| R-11 | "No spin, no bias, unlike the rest of the coverage." | X-03 variant | Claims other coverage is biased, which is a judgement about third parties and an unverifiable comparative claim. |
| R-12 | "Five parties, one honest comparison." | NOTE-01 variant | "Honest" implies the comparison needed rescuing from dishonesty elsewhere. Comparative superiority claim without evidence. |
| R-13 | "Join thousands of British Columbians who've already found their match." | X-01 variant | Unsourced social-proof number (would breach the citation gate) plus "found their match" implies the tool decides something. |
| R-14 | "Time is running out to figure out where you stand." | X-THREAD 1/5 | Deadline pressure is a GOTV-adjacent nudge. |
| R-15 | "Even if you think you know, check the receipts." | X-03 variant | "Even if you think you know" is faintly corrective, the m8 register. Cut on the posture decision above as well as tone. |
| R-16 | "Better than a poll. Better than a pundit." | X-02 variant | Comparative claims about third parties, unverifiable. |
| R-17 | "The tool the parties don't want you to see." | (joke draft, X-01) | Implies parties are hiding something and that we are in conflict with them. Neutrality failure and factual failure. Never in serious contention; recorded so it is visible that it was considered and dismissed. |
| R-18 | "Make sure you actually vote this time." | (reply template draft) | Pure get-out-the-vote. Rule 4 forbids GOTV tilt in any direction. |
| R-19 | "Whichever way you lean, this is worth 5 minutes." | X-02 variant | Survived two rounds then cut: "whichever way you lean" is neutral enough, but "worth 5 minutes" is persuasion for engagement's sake and the piece reads shorter and truer without it. Close call, logged as REVISE-by-deletion: the rest of the line ("compares your answers to the parties' published positions") is already in X-02. |
| R-20 | "Parties change their minds constantly. We keep up." | X-08 variant | "Constantly" is a characterisation of parties' behaviour (unreliable, slippery). The neutral version says positions change during a campaign, which is factual and applies to the process, not to anyone's character. |
| R-21 | "We hold the parties to their own words." | NOTE-01 variant | "Hold to" implies adversarial accountability, the m8 register again. Recast as provenance ("we code from their published words"). |
| R-22 | "Compare yourself to the parties before it's too late." | X-05 variant | "Before it's too late" = election urgency = GOTV tilt. |
| R-23 | "A reality check for your assumptions." | FAQ-02 title variant | Implies the user's assumptions are wrong before they answer anything. Corrective framing, fails neutrality of posture. |
| R-24 | "Trust, but verify. We show every source." | X-03 variant | Cut for origin and edge: the phrase is associated with political rhetoric, and "trust, but verify" still begins from distrust. Plain version ("Every code carries a verbatim quote") does the same work without the attitude. |

## Calibrated non-rejections (accepted on purpose)

These are borderline phrases that were kept, with the reasoning, so the audit does not claim a stricter standard than it applied.

| phrase | piece | why kept |
|--------|-------|----------|
| "what the parties have actually said" | X-02 | "Actually" here modifies the source class (published statements vs second-hand summaries), which is a factual claim about our sourcing. It does not imply a party is lying. Kept but it is the phrase most likely to draw a rubric comment; if the reviewer flags it, the fix is dropping "actually". |
| "The vote is yours." | FAQ-01 | Informational statement of scope after an explicit refusal to recommend. Not a nudge: it ends the interaction rather than pushing action. |
| "which is most of the conversation in this sub right now" | REDDIT-VAN | Community-relevance courtesy line, factual about the subreddit's own front page at posting time. If it drifts from being true, drop it rather than update it. |
| "Happy to answer anything about the method." | REDDIT-BC | Neutrality-safe invitation; it promises answers about method, not arguments about parties. |

## Method notes

- Every piece was checked against the wording rules in Rule 4 and then against the rubric's honesty gates: nothing claims what we cannot verify, numbers (18 statements, 6 topics, 5-point scale, two axes) trace to METHODOLOGY.md, and no piece states a user count, accuracy rate, or prediction.
- The deck contains no "register" from m8-voice: no correcting, no countering, no framing of anyone's beliefs as extremist. Disagreement about that strategy is recorded above rather than resolved silently.
- Zero-party-naming discipline: not one piece names a party, leader, or candidate. The only election facts used are the date (Oct 24) and the existence of "the parties", both uncontroversial and documented in the repo.