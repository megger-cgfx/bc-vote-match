# COPY DECK — BC Vote Match outreach (drafts for human review)

Status: **NOT APPROVED FOR PUBLICATION.** Every piece below is a draft. Publishing is gated on Martin personally. As of 2026-10-01 the site's launch preflight is **NO-GO** (8 failures in `docs/05-LAUNCH.md`) and `bcvotematch.ca` is not registered, so **no piece may be published until preflight reports GO and Martin says publish.** Nothing here assumes the site is live.

Schedule these pieces against `marketing/04-calendar/CALENDAR.md`. Pieces are written to be true whenever they run, but the URLs only work once the domain is registered and the site is up.

Rules this deck holds to, from `docs/content/NEUTRALITY-PROTOCOL.md` Gate 1 and `marketing/06-review/RUBRIC.md`:
- "Here is where you sit", never "party X is wrong". No judgement about any party or its supporters.
- No persuasive copy for or against any party, candidate, or outcome. No get-out-the-vote tilt.
- Descriptive language about a party is drawn from the party's own words; where we summarize, we summarize the quote and nothing more.
- Cite every number. The numbers used here (18 statements, 6 topics, 5-point scale, 2 axes, Oct 24 E-day) come from `docs/content/METHODOLOGY.md`, `docs/content/ABOUT.md`, and `src/lib/site.ts`.
- Keep it short. No engagement bait. No "surprise" framing.

Note on `marketing/01-strategy/m8-voice.md`: its "engaging people reached by extremist narratives" framing is not this campaign's posture and is not used here. Only its Reddit-norms material (read the room, disclose, expect skepticism, don't argue) informed the Reddit pieces. See `NEUTRALITY-AUDIT.md` for that judgement.

Channel note on Reddit: both target communities restrict self-promotion (verified rule text in `CALENDAR.md`). Every Reddit piece below is written for **modmail-cleared posting only**. If the mod team does not authorize it, the piece is not posted.

---

## X (Twitter) — single posts

### X-01 — Launch post
- **Channel:** X, main account. **Format:** single post. **Audience:** general BC public, first-contact.
- **Gate 1 note:** announces the tool and its method only; no party named, no outcome implied.

> BC Vote Match is live for the BC 2026 election. Answer 18 statements, see how your answers line up with each party's published positions, and read the quote behind every code. Free, no account, no tracking. bcvotematch.ca

### X-02 — What it is
- **Channel:** X. **Format:** single post. **Audience:** curious first-timers who saw X-01.
- **Gate 1 note:** describes the comparison mechanic neutrally; parties only referenced as "the parties".

> BC Vote Match compares what you think to what the parties have actually said, in public, in their own words. 18 statements, 6 topics, every result linked to a source you can read. bcvotematch.ca

### X-03 — Receipts
- **Channel:** X. **Format:** single post. **Audience:** skeptics and journalists deciding whether to trust the tool.
- **Gate 1 note:** describes provenance of party codes; makes no claim about any party's content.

> Every code in BC Vote Match carries a verbatim quote, checked against a saved, hashed, archived copy of the source. If a quote can't be verified, the code doesn't ship. bcvotematch.ca

### X-04 — "No position" is a real answer
- **Channel:** X. **Format:** single post. **Audience:** people who assume the tool fills gaps by guessing.
- **Gate 1 note:** the "no position" rule applies identically to every party; the piece names none and implies none.

> If a party hasn't stated a position, we don't guess. That question drops out of the alignment math for that party. "No position" is a first-class answer at BC Vote Match. bcvotematch.ca

### X-05 — What it doesn't do
- **Channel:** X. **Format:** single post. **Audience:** anyone treating a high score as a recommendation.
- **Gate 1 note:** explicitly refuses to endorse or predict; lists what sits outside the method without commenting on it.

> BC Vote Match shows distances, not endorsements. It doesn't tell you how to vote and it doesn't predict your vote. Leaders, local candidates, record, and trust all sit outside the method. bcvotematch.ca

### X-06 — Privacy
- **Channel:** X. **Format:** single post. **Audience:** privacy-conscious users.
- **Gate 1 note:** factual claim about the build (no account, no login, answers stay in the browser), verified in `docs/content/METHODOLOGY.md` and `src/lib/site.ts`; nothing about parties.

> No account, no login, no demographic questions. Your answers never leave your browser. BC Vote Match has no trackers and no analytics. bcvotematch.ca

### X-07 — Corrections invited
- **Channel:** X. **Format:** single post. **Audience:** party researchers, journalists, and anyone who spots an error.
- **Gate 1 note:** describes the corrections process neutrally; the same procedure applies to every party.

> Think we have a code wrong? Send the question id, the party, and a verbatim quote from a public source with a URL. If the quote supports a different code we recode, version it, and publish what moved. bcvotematch.ca

### X-08 — Recode notice (template for the Oct 12 and Oct 20 recode passes)
- **Channel:** X. **Format:** single post. **Audience:** followers who already have a result.
- **Gate 1 note:** recoding is versioned and diffed for every party alike; the piece states the process, never a judgement about who moved or why.

> Party positions change during a campaign. When they do, BC Vote Match recodes the affected rows, versions the change, and publishes the diff. Same questions, same method, current sources. Check the version date on your result. bcvotematch.ca

Publish timing note: run after each recode pass lands (Oct 12, Oct 20), not before. If Martin wants the specific diff counts in the post, add them from the published coding table at publish time. Do not state numbers that are not in the table yet.

---

## X — thread

### X-THREAD — What BC Vote Match is (5 posts)
- **Channel:** X, main account. **Format:** thread. **Audience:** general public on launch day, second-wave reach.
- **Gate 1 note:** the thread explains method and limits only; it names no party, scores no outcome, and ends on corrections rather than a call to vote.

**1/5**
> BC Vote Match is live for the BC 2026 election. What it is and how it works, in five posts. bcvotematch.ca

**2/5**
> You answer 18 statements on a five-point scale, with "don't know" if you'd rather skip. Three statements each on cost of living and taxes, housing, health, climate and environment, Indigenous reconciliation, and public safety.

**3/5**
> We code each party on the same scale from what the parties have said in public: platforms and policy documents first, then releases and speeches, then Hansard, then media. Every code carries a verbatim quote.

**4/5**
> Your result is the distance between your answers and each party's codes, per topic and on a two-axis map. The map is a reading aid, not a measurement of anyone. Parties stay in a fixed order. We never rank them.

**5/5**
> The method, the full coding table, the quotes, and the code are all public. If we have something wrong, send the quote that proves it and we'll version the change. No account, no tracking. bcvotematch.ca

---

## Reddit

Both pieces below are **modmail-cleared drafts only**. Verified community rules and the approval requirements are in `marketing/04-calendar/CALENDAR.md`. If approval is not granted in writing, do not post.

### REDDIT-BC — r/britishcolumbia text post
- **Channel:** r/britishcolumbia. **Format:** text post, title + body. **Audience:** BC voters discussing the election.
- **Gate 1 note:** disclosure-first, method-focused, invites corrections; no claim about any party's positions or quality.

**Title:**
> We built a free, open-source tool that compares your views to BC parties' published positions, with a sourced quote behind every code. Posted with mod permission.

**Body:**
> Disclosure first: we're the small volunteer team behind this, and we're posting with moderator permission.
>
> BC Vote Match is a free, independent tool for the October 24 provincial election. You answer 18 statements on a five-point scale, "don't know" allowed, and it shows how your answers line up with each party's published positions, per topic and on a two-axis map.
>
> What it doesn't do: it doesn't tell you how to vote and it doesn't predict your vote. Parties are listed in a fixed order and never ranked.
>
> Every code carries a verbatim quote from a source we saved and archived. The full coding table is public, including where our independent coders disagreed and how each disagreement was resolved. If we have something wrong, the fastest fix is the quote that proves it: send it and we recode, version it, and publish what moved.
>
> No account, no login, no tracking; your answers never leave your browser. Open source, volunteer-run, and not affiliated with Elections BC, any party, any candidate, Vote Compass, or Vox Pop Labs. It accepts no money from parties, candidates, or their financial agents.
>
> bcvotematch.ca
>
> Happy to answer anything about the method.

### REDDIT-VAN — r/vancouver text post
- **Channel:** r/vancouver. **Format:** text post, title + body. **Audience:** Metro Vancouver voters (relevance rule: provincial election, local angle).
- **Gate 1 note:** same neutral description as REDDIT-BC with a Metro Vancouver relevance line; no party is discussed.

**Title:**
> For the Oct 24 provincial election: a free open-source tool comparing your answers to each party's published positions (we made it, mod permission)

**Body:**
> Disclosure: we're the volunteer team behind this and we have moderator permission to post it.
>
> The provincial election is October 24. BC Vote Match is a free tool that shows how your answers to 18 policy statements line up with each party's published positions, per topic and on a two-axis map. Housing and cost of living are two of the six topics, which is most of the conversation in this sub right now.
>
> It does not tell you how to vote and it does not rank the parties. Every party code carries a verbatim quote from an archived source, and the full coding table is public. Corrections welcome: send the quote that proves a change and we version it publicly.
>
> No account, no tracking, answers stay in your browser. Not affiliated with Elections BC or any party or candidate. Open source.
>
> bcvotematch.ca

Note on this piece: r/vancouver's topic rule requires Metro Vancouver relevance and puts PSAs at moderator discretion. The local line in the body is deliberately factual (topics covered, election date), not a hook. If the mods ask for it removed, remove it and thank them.

---

## Launch note

### NOTE-01 — Short launch note (site news page and/or repository README section)
- **Channel:** project site (news/updates) and repository. **Format:** short note, ~150 words. **Audience:** reviewers, journalists, and people arriving from a link.
- **Gate 1 note:** the note explains scope, method transparency, and funding independence; it makes no statement about any party.

> **BC Vote Match is live for the 2026 provincial election**
>
> BC Vote Match is now up for the October 24 provincial election. You answer 18 statements and see how your answers line up with each party's published positions, with the quote and source behind every code.
>
> The method is public, the full coding table is public including coder disagreements, and the code and data are open source. "No position" is a real result: where a party has not stated a position, we do not guess one.
>
> Corrections are welcome and are evaluated on evidence alone. Send a verbatim quote from a public source; if it supports a different code we recode, version the change, and publish what moved. If it does not, we publish the challenge and our reason for leaving the code alone.
>
> BC Vote Match is a volunteer project. It is not affiliated with Elections BC, any political party, any candidate, Vote Compass, or Vox Pop Labs, and it accepts no money from parties, candidates, or their financial agents.

---

## FAQ answers

### FAQ-01 — "Does this tell me who to vote for?"
- **Channel:** site FAQ and Reddit/X comment replies. **Format:** FAQ answer, ~110 words. **Audience:** users reading a result and asking what it means.
- **Gate 1 note:** refuses to recommend or predict and says so plainly; "the vote is yours" is informational, not a get-out-the-vote nudge.

> No. BC Vote Match shows distances between your answers and each party's published positions, not recommendations. Parties are listed in a fixed order and never ranked from best to worst. Plenty of people find they are closest to a party they will never vote for, and that is a perfectly good outcome. Leaders, local candidates, record in government, trust, and strategic voting all sit outside this method, and they are often what decide votes. The result is information. The vote is yours.

### FAQ-02 — "How do I know the numbers aren't rigged?"
- **Channel:** site FAQ and Reddit/X comment replies. **Format:** FAQ answer, ~120 words. **Audience:** sceptical readers and journalists.
- **Gate 1 note:** points at inspectable method artefacts rather than asking for trust; makes no claim about any party's honesty.

> Because you can check them. Every code carries a verbatim quote from a source we saved, hashed, and archived, and quotes are verified mechanically before publication. The full coding table is published, including the places where our two independent coders disagreed and how each disagreement was resolved. The question set was frozen before coding began. The code and the data are open source. If you find an error, send the quote that proves it: if it supports a different code we recode, version it, and publish what moved; if it does not, we publish your challenge and our answer.

---

## Index

| id | channel | format | scheduled for (see CALENDAR.md) |
|----|---------|--------|--------------------------------|
| X-01 | X | single | Oct 8 (launch, gated) |
| X-02 | X | single | Oct 9 |
| X-03 | X | single | Oct 9 |
| X-04 | X | single | Oct 10 |
| X-05 | X | single | Oct 13 |
| X-06 | X | single | Oct 15 |
| X-07 | X | single | Oct 16 |
| X-08 | X | single | Oct 12 and Oct 20 (recode passes) |
| X-THREAD | X | thread (5) | Oct 8 (launch, gated) |
| REDDIT-BC | r/britishcolumbia | text post | Oct 8 (modmail-cleared only) |
| REDDIT-VAN | r/vancouver | text post | Oct 8 (modmail-cleared only) |
| NOTE-01 | site + repo | launch note | Oct 8 (gated) |
| FAQ-01 | site FAQ + replies | FAQ answer | Oct 8 |
| FAQ-02 | site FAQ + replies | FAQ answer | Oct 8 |

14 pieces. Machine-readable copy: `copy-deck.json`. Gate 1 verdicts and cut candidates: `NEUTRALITY-AUDIT.md`.