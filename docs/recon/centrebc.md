# BCVM M1 — Source recon: CentreBC
Slug: `centrebc` · Recon date: 2026-10-01 · Recon worker: flower
Raw sources: `data/raw/centrebc/` (52 records in `sources.json`) · Manifests: `data/manifests/centrebc.json`, `data/manifests/centrebc-hansard.json`

Method: every source below was fetched live from its own URL (browser user-agent; party
site is Cloudflare-fronted and 403s a plain crawler UA), saved to `data/raw/centrebc/`,
sha256-hashed, and submitted to the Wayback Machine where the save endpoint cooperated.
Text companions (`.txt`) are the verbatim extracted page text — **all quotes in this
report were re-checked programmatically against those files** (`tools` note at the end).

## 1. What CentreBC is (facts the coding team must not get wrong)

- **New party, no platform.** CentreBC was formed in 2025 (founder: former MLA Karin
  Kirkpatrick). Its `/our-policy/` page (2026-06-18) states the policy pillars are still
  being written. Source `centrebc-0009`: "Our Policy Committee is currently hard at work
  developing CentreBC's first major policy pillars." / "our goal is to present a complete,
  thoughtful, and fully developed platform". **There is no platform document to code from.**
- **Caucus collapsed to one MLA.** Media (Canadian Press, 2026-09-25, `centrebc-0041`,
  `centrebc-0043`): "CentreBC, which was formed last year, has gone from the political
  margins to a viable contender with eight legislators, then back to having just one."
  The eight ex-BC Conservative MLAs — including Peter Milobar — rejoined the Conservatives;
  Elenore Sturko is the leader and sole incumbent. (Reporter account of that defection:
  `centrebc-0041`.) Any brief that assumes a multi-MLA CentreBC caucus is stale.
- **Leadership churn inside 18 months:** Karin Kirkpatrick (2025 → spring 2026) →
  Mike Bernier, "former cabinet minister", announced as leader (`centrebc-0017`, 2026-07-18) →
  Peter Milobar as "short-lived leader" (`centrebc-0043`) → **Elenore Sturko**
  (leader page `centrebc-0023`; announced 2026-09-22/23). Releases before July 2026 are
  signed by Kirkpatrick (e.g. `centrebc-0029`) — attribute positions to the party, not to Sturko.
- **Riding note:** Sturko was elected for Surrey South (2022 byelection) and Surrey-Cloverdale
  (2024); she is running in **Surrey South** in 2026 (`centrebc-0023`, `centrebc-0044`).
- **Her DRIPA vote is a matter of record and self-reported:** `centrebc-0052` (2026-08-13):
  "When DRIPA was introduced in 2019, I was the only MLA who did not vote in favour of the
  legislation." A coder should treat that as a party-leader statement, not media spin.

## 2. Source inventory (52 sources, all sha256-verified, no duplicate URLs)

| type | n | ids |
|---|---|---|
| platform | 3 | 0001 (/), 0002 (core values), 0003 (vision) |
| policy | 1 | 0009 (policy philosophy & process) |
| release | 31 | 0010-0012, 0015, 0017, 0019-0021, 0024-0025, 0027, 0029, 0031-0033, 0035-0040, 0046-0054, 0063 |
| media | 5 | 0041 Global News, 0042 CTV, 0043 Times Colonist (all CP wire 2026-09-25), 0044 Coast Mountain News, 0045 Don Shafer interview |
| hansard | 7 | 0055 n168 (2026-04-30), 0056 n131 (2026-03-03), 0057 n124 (2026-02-24), 0058 n133 (2026-03-05), 0059 n147 (2026-04-02), 0060 n171 (2026-05-04), 0061 n144 (2026-03-31) |
| other | 5 | 0004 resources/independent-adjudicator, 0005 candidates, 0007 resources, 0023 leader bio, 0062 our-team |

Date range 2025-04-10 → 2026-09-25 (one undated: 0045). Total 9.3 MB HTML / 1.9 MB text.
Origins: 40 centrebc.ca, 7 lims.leg.bc.ca (Hansard), 5 media.
**Wayback snapshots: 29 / 52** — the archive.org `/save` endpoint was rate-limited for the
remainder across three retry passes (verified 2026-10-01 08:2xZ). Every source still has a
hash-pinned local copy plus its `.txt`, so nothing in the coding pipeline depends on the
archive; the missing snapshots can be back-filled later.

**Hansard note.** bc's `www.leg.bc.ca` debate pages are JS-rendered shells, and the
`leg.bc.ca` search/`lims.leg.bc.ca` PDF URLs cited elsewhere do not enumerate (CDX is
unreachable from this box). The working route is the Leg Assembly's own mirror:
`api.lims.leg.bc.ca/hdms/file/Index/43rd2nd/2026-Members-Indexs.htm` → per-member index of
every intervention, whose links resolve to
`lims.leg.bc.ca/hdms/file/Debates/43rd2nd/<date><am|pm>-Hansard-n<N>.html`. The 7 transcripts
here are exactly the 43rd/2nd-session days where Sturko spoke on the six topics (n124 budget,
n131 AG estimates, n133 home care, n144 Cloverdale hydro petition, n147 hospital staffing,
n168 violent crime/mental illness, n171 health estimates). Caveat for coders: these are her
**pre-CentreBC** (Conservative/Independent MLA) interventions — leader record, not party policy.

## 3. Topic-by-topic

### cost-of-living-taxes — STRONG (reactive, but concrete asks)
Primary: `centrebc-0029` (2026-02-16 "Budget 2026: Managing Decline is Not Leadership"),
`centrebc-0050` (2026-02-19 "A Blueprint for Bankruptcy"), `centrebc-0035` (2025-11-19 Look
West), `centrebc-0003` (vision/fiscal). Hansard: `centrebc-0057` (budget debate).
- 0029: "Lower Grocery Bills: We will scrap the PST on food production and farm equipment to lower the cost of B.C.-grown food."
- 0029: "True $10-a-Day Childcare: We will treat childcare as essential economic infrastructure to finally make the $10-a-day goal a reality for every family."
- 0050: "The government's refusal to course-correct will bury the next generation under a mountain of debt while failing to fix the affordability and safety crises."
- 0003: "CentreBC believes in responsible financial management—balancing the budget over the long term through smarter investments and spending."
Direction is clear for a tax/affordability question (cut consumption taxes, balance the budget
over time, no new revenue tools proposed). **No position found** on raising taxes on high
earners, corporate tax rates, or carbon pricing as a revenue source.

### housing — THIN (weakest topic)
Primary: `centrebc-0029`, `centrebc-0049` (2026-07-31), `centrebc-0002`, `centrebc-0052`.
- 0029: "Housing You Can Afford: We must link housing policy to actual affordability outcomes rather than just counting units."
- 0049: "It means tackling the cost of living and housing affordability with real supply, not slogans."
- 0052: "Develop practical sector agreements in areas such as forestry, mining, energy, infrastructure, and housing that support both reconciliation and economic development."
No release is dedicated to housing; no stated position on zoning/density, rent control,
purpose-built rental, or public/social housing targets. A housing question will need `code:
null` or a low-confidence code from these two lines only.

### health — MEDIUM (critique is strong, commitments are thin)
Primary: `centrebc-0047` (2026-06-08), `centrebc-0029`, `centrebc-0051` (2026-08-05 HIV care
funding), `centrebc-0003`. Hansard: `centrebc-0058` (home care, hospital capital, 2026-03-05),
`centrebc-0059` (hospital staffing & ER access, 2026-04-02), `centrebc-0060` (health estimates, 2026-05-04).
- 0029: "Healthcare for Families: We will expand home care so seniors can age with dignity and reduce the paperwork for doctors so they can focus on seeing patients."
- 0047: "The waitlist for a long-term care bed has tripled since 2016, from about 2,400 people to over 7,200."
- 0003: "Accessible, well-funded healthcare and mental health supports."
Emphasis: seniors/long-term care/home care, capacity planning, "re-paced" hospital projects.
**No position found** on private clinics / two-tier delivery, or on pharmacare-style expansion.

### climate-environment — MEDIUM (conditional resource development, not a climate plan)
Primary: `centrebc-0048` (2026-07-07 pipeline conditions), `centrebc-0038` (2025-10-23 five
conditions), `centrebc-0015` (2026-08-03 wildfire state of emergency), `centrebc-0003`.
Hansard: `centrebc-0061` (Cloverdale hydro substation petition, 2026-03-31).
- 0048 (restating CentreBC's own conditions): "an Indigenous participation framework, a dedicated B.C. Energy Future Fund, real safety and climate guardrails, guaranteed local jobs and procurement, and a clear legal pathway with full transparency."
- 0003: "We are committed to responsible economic growth, supporting small business, fostering innovation, and investing in green technology—while also championing our resource industries, including mining, forestry, and energy."
- 0015: "Why has a Provincial State of Emergency not been declared?"
The party supports pipelines **conditionally** and resource industries unconditionally; it has
no emissions-reduction target, carbon-pricing position, or conservation commitment on the record.

### indigenous-reconciliation — STRONG (most explicit commitments found)
Primary: `centrebc-0052` (2026-08-13 statement), `centrebc-0046` (2026-03-06 "Original Sin"),
`centrebc-0024` (2026-05-27), `centrebc-0002`, `centrebc-0048`.
- 0052: "Create a single provincial framework for treaties and reconciliation agreements"
- 0052: "Modern treaties have already demonstrated that negotiated agreements can create stability, strengthen Indigenous communities, and provide greater certainty for everyone."
- 0052: "Simply repealing DRIPA today would not undo those changes"
- 0046: "This failure to address the "Land Question" is our province's original sin"
Posture: pro-negotiation, pro-modern-treaty, pro-certainty; opposed to DRIPA repeal *and*
opposed to the 2019 DRIPA as written; explicitly pairs Indigenous title with private-property
protection. This is the topic where a coder has the most material to work with.

### public-safety — STRONG (developed, costed-ish plan)
Primary: `centrebc-0036` (2025-11-06 three-step extortion plan), `centrebc-0054` (2026-02-11
IPV), `centrebc-0029`, `centrebc-0031` (2026-02-10 Tumbler Ridge), `centrebc-0033`.
Hansard: `centrebc-0055` (violent crime, mental illness, 2026-04-30), `centrebc-0056` (AG
estimates, 2026-03-03).
- 0036: "Establish an integrated FINTRAC–RCMP–CBSA cell in Surrey to map money flows, fast-track production orders and freeze assets within hours, not weeks."
- 0036: "set a 48-hour protection standard with real-time analytics to pre-empt sprees"
- 0029: "Stronger Justice: Our public safety plan is backed by strong justice and treatment systems to ensure those who break the law face consequences while those with addictions get help."
- 0054: "it needs serious action with clear timelines, measurable milestones, meaningful tracking and transparent public accountability"
Posture: enforcement-forward (asset freezes, dedicated prosecution track, victim protection)
paired with treatment. **No position found** on bail-reform specifics, sentencing minimums, or
safe-supply policy as distinct from "treatment".

## 4. Coding readiness summary

| topic | strength | best single source | codable from site alone? |
|---|---|---|---|
| public-safety | strong | centrebc-0036 (2025-11-06) | yes |
| indigenous-reconciliation | strong | centrebc-0052 (2026-08-13) | yes |
| cost-of-living-taxes | strong | centrebc-0029 (2026-02-16) | yes |
| climate-environment | medium | centrebc-0048 (2026-07-07) | conditional-only |
| health | medium | centrebc-0047 (2026-06-08) | critique > commitment |
| housing | thin | centrebc-0029 | likely `code: null` |

## 5. Gotchas for coders
1. There is no platform — do not invent one by reading the values pages as if they were policy.
2. Older releases are signed by a different leader; do not attribute them to Sturko.
3. `centrebc-0041/0042/0043` are the same Canadian Press wire story on three outlets — treat as one.
4. `centrebc-0045` is an audio interview page: it contributes topic *framing*, not quotes.
5. Hansard transcripts are the leader's record as a Conservative/Independent MLA, not CentreBC policy.
6. Some 2026 releases are titled "Opinion:" but are published as party communications on the
   party site with a media contact — usable, but lower weight than a news release.

## 6. Reproducing this
```
python3 agents/fetch_manifest.py data/manifests/centrebc.json --jobs 5      # 45 site/media sources
python3 agents/fetch_manifest.py data/manifests/centrebc-hansard.json       # 7 Hansard transcripts
python3 agents/fetch_manifest.py data/manifests/centrebc.json --archive-only
```
`agents/fetch_source.py` was fixed during this recon: browser UA first (centrebc.ca 403s a
crawler UA), `fetch_via` field records live vs archive provenance, and it now falls back to
the closest Wayback snapshot when a live fetch fails. `agents/fetch_manifest.py` is new
(bulk, resumable, parallel) and reusable by the other party-recon tasks.
