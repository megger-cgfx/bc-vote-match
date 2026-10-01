# OneBC — Source Inventory (M1)

Compiled 2026-10-01 for BC Vote Match. Party slug `onebc`, interim leader Dallas Brodie (MLA, Vancouver-Quilchena). All sources fetched live, saved locally, sha256-hashed, and submitted to the Wayback Machine where the save succeeded.

## Inventory: 19 sources

| type | count | ids |
|---|---|---|
| platform | 2 | onebc-0001, onebc-0002 |
| policy | 2 | onebc-0003, onebc-0004 |
| hansard | 4 | onebc-0008 … onebc-0011 |
| media | 6 | onebc-0012 … onebc-0017 |
| other | 5 | onebc-0005 … onebc-0007, onebc-0018, onebc-0019 |

Contents, in source-priority order (see docs/SCHEMA.md):

- **onebc-0001** (platform) `https://1bc.ca/priorities` — the party's platform: numbered planks in 11 sections. This is the primary coding source.
- **onebc-0002** (platform) `https://1bc.ca/` — home page, short issue summaries (Economy, Reconciliation, Crime & Justice, Education, Housing, Forestry, Healthcare).
- **onebc-0003** (policy) `https://1bc.ca/constitution` — party constitution page.
- **onebc-0004** (policy) party constitution PDF (on the party's CDN). Text extracted to `onebc-0004.txt`.
- **onebc-0005** (other) `https://1bc.ca/leadership` — Dallas Brodie bio and mission statement.
- **onebc-0006** (other) `https://1bc.ca/candidates` — 2026 candidate slate.
- **onebc-0007** (other) `https://1bc.ca/petitions` — active petitions, which state issue positions (UBC/UVic "defund" petitions, others).
- **onebc-0008** (hansard) 2025-10-28 — Armstrong on education and land acknowledgements ("humiliation rituals"), cultural-humility curriculum.
- **onebc-0009** (hansard) 2025-10-30 — Armstrong introduces the New Resident Health Cost Recovery Act ($7,500/yr health fee for non-citizen new residents) plus forestry remarks.
- **onebc-0010** (hansard) 2026-03-12 — Brodie statements and questions.
- **onebc-0011** (hansard) 2026-04-23 — Brodie arguing to let voters repeal DRIPA.
- **onebc-0012** (media) Surrey Now-Leader, 2026-09-22 — Chapman floor-crossing; quotes OneBC policy values (50% income-tax cut under $100k, end UNDRIP/DRIPA, Quebec-style immigration control, SOGI removal, gender-care positions).
- **onebc-0013** (media) Castanet — OneBC names candidate for the riding held by former member Tara Armstrong.
- **onebc-0014** (media) Times Colonist / Canadian Press — 300+ would-be candidates, no official party status before election call.
- **onebc-0015** (media) CTV News — OneBC won't run against eight "principled" B.C. Conservative candidates.
- **onebc-0016** (media) Fraser Valley News Network, 2026-08-29 — leader says party won't run in Fraser Valley by-election.
- **onebc-0017** (media) Epoch Times — OneBC promises not to challenge candidates it calls true conservatives.
- **onebc-0018** (other) Wikipedia — party history and policy summary; discovery aid only, do not code from it.
- **onebc-0019** (other) iVoteOneBC.ca/policies, 2026-06-17 — independent supporter-site tracker of the platform; discovery aid only.

16 of 19 have a Wayback snapshot recorded in `sources.json`. Missing snapshots: onebc-0009, onebc-0013, onebc-0017 (save requests failed; hashed local copies exist).

## What the policy record actually looks like

OneBC is codable, not thin overall. Its whole platform is one page: **38 numbered planks in 11 sections** (as fetched 2026-10-01): Reconciliation (6), Economy & Public Finance (6), Generational Debt (4), Healthcare (2), Education (3), Housing (2), Drugs & Addiction (4), Firearms Owners (3), Crime and Justice (4), Forestry (3), Interprovincial Relations (1).

Two things coders must watch:

1. **The platform moved during the campaign.** The iVoteOneBC tracker (June 17, 2026) records 53 planks in 12 categories, including Environment and Democracy sections that are absent from the page as fetched on Oct 1. Code against the current page, cite `onebc-0001`, and note the date.
2. **A tax-plank discrepancy.** The priorities and home pages say "25% tax cuts for every single tax bracket". Surrey Now-Leader (Sept 22, 2026) quotes the party promising an "immediate 50% tax cut on income under $100,000". Whichever a coder quotes, the quote and its source decide the code.

There is no standalone platform PDF, and no working press-release archive (the site's "Latest News" footer link 404s). Leader statements circulate via X and YouTube; only Hansard and media captures of them are in this inventory.

## Topic coverage

| topic | coverage | basis |
|---|---|---|
| cost-of-living-taxes | **strong** | 25% cut all brackets + corporate, 2% PST cut, regulation audit (176,000+), balanced budgets in 4 years, surpluses to debt, pipeline to Prince Rupert/Kitimat. Plus the 50%/$100k claim in onebc-0012. |
| housing | **thin** | Only 2 planks, both deregulatory: eliminate the Step Code, block municipal rent control. Nothing on supply, affordability, or homelessness. |
| health | **moderate** | 2 planks (private care alongside fully-funded public care; shift admin spending to frontline) + Drugs & Addiction section (end safe supply, involuntary rehab) + onebc-0009 Hansard bill on new-resident health fees. |
| climate-environment | **thin** | No climate or emissions policy anywhere in the inventory. Closest: Forestry section (raise allowable cut, cut stumpage, faster permits) and the anti-green-building-code housing plank. The June platform apparently had an Environment section; it is gone from the current page. |
| indigenous-reconciliation | **strong, one-sided** | 6 detailed planks: repeal DRIPA, UNDRIP to have "no force and effect", halt transfers to band governments, band-spending oversight, repeal the Indian Act / reserves to townships, English place names, end mandatory land acknowledgements. Reinforced in onebc-0008 and onebc-0011 Hansard. |
| public-safety | **strong** | Crime and Justice (repeat/violent offenders, prosecutorial direction, port smuggling, no masks at protests) + Drugs & Addiction (4 planks) + Firearms Owners (3 planks). |

## Gaps and caveats

- **No dated platform document.** The priorities page is undated and demonstrably changed mid-campaign. Every quote should carry its source id and fetch date.
- **No press releases.** Party announcements are only visible via social media, YouTube, and media coverage.
- **No Hansard for Brent Chapman as OneBC.** He joined 2026-09-22, the day the legislature was dissolved. His floor-crossing statement is captured in onebc-0012.
- **Housing and climate-environment are thin.** For several 18-topic questions the honest code will be `null` with `quote: null` rather than an inference.
- **Wayback gaps** on onebc-0009, onebc-0013, onebc-0017.
- **Media mix:** mainstream (Times Colonist/CP, CTV, Surrey Now-Leader, Castanet) plus two right-leaning outlets (Epoch Times, Fraser Valley News Network). Wikipedia and iVoteOneBC are secondary and must not be used as coding sources.

## Verdict

OneBC can be coded on all six topics from `onebc-0001` (priorities) plus Hansard, with real positions and quotable language on cost-of-living-taxes, indigenous-reconciliation, and public-safety, moderate material on health, and thin material on housing and climate-environment. Expect `null` codes there rather than guesses.

Files: `data/raw/onebc/onebc-0001.html|.txt` … `onebc-0019` (onebc-0004 is the constitution PDF with extracted text), plus `sources.json` with id, type, url, published, fetched_at, sha256, local_path, text_path, archive_url per source.
