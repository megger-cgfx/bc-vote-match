# CentreBC — Source Inventory Summary

Compiled 2026-10-01 for BC Vote Match (M1 Sources). All records in `data/raw/centrebc/sources.json`.
Every source was fetched with `agents/fetch_source.py`, saved locally with a sha256 hash, and submitted to the Wayback Machine where possible. All 56 records pass a hash and file-presence check.

## Inventory (56 sources)

| Type | Count | Notes |
|---|---|---|
| platform | 3 | Homepage, Our Core Values, Our Vision for B.C. |
| policy | 2 | Our Policy (philosophy/process), Path Forward for B.C. |
| release | 31 | News releases and op-eds, Apr 2025 to Sep 2026 |
| hansard | 8 | All feature Elenore Sturko (see Hansard note below) |
| media | 7 | Global News, CTV, Times Colonist, Coast Mountain News, Don Shafer interview, Vancouver Sun, CityNews |
| other | 5 | Leader bio, team page, candidates page, resources page, independent adjudicator page |

Wayback archive URL recorded for 31 of 56 sources (rate limits and 403s caused misses on the rest; the local hashed copies are complete). Local files: `centrebc-NNNN.html` plus extracted `.txt` for every record. No PDFs were found or handled.

## Party context (why the record is thin)

- CentreBC was founded in 2025 by Karin Kirkpatrick (first release Apr 2025). Leader churn: Kirkpatrick, then Mike Bernier (Jul 2026), then Peter Milobar for about a day (Sep 18, 2026), then Elenore Sturko (Sep 22, 2026, current leader and Surrey South candidate).
- Seven ex-Conservative MLAs (Milobar, Paton, Wat, Banman, Bird, Wilson, Warbus) joined Sep 18 and returned to the Conservatives at the writ drop. Sturko is the party's only current MLA.
- **No full election platform had been published as of Oct 1, 2026.** CityNews (Sep 27) reports the platform was in "final touches" and would be unveiled soon. The party's positions live in press releases, op-eds, and vision-level pages. Thin policy is a finding, not a failure.

## Topic coverage

**Strong topics**

- **health** (10 party/media docs): dedicated op-ed "Healthcare 'Crisis' Was Never a Surprise" (Jun 2026), HIV care funding criticism (Aug 2026), concrete budget asks (expand home care, cut doctor paperwork), mental health and addictions content, plus four Hansard debates where Sturko pressed health estimates, home care, and hospital staffing.
- **public-safety** (8 docs): "3-Step Plan to Crush Transnational Extortion" (Nov 2025), intimate partner violence op-ed (Feb 2026), Tumbler Ridge shooting statement, "stronger justice and treatment systems" budget asks, Sturko's RCMP background framing, Hansard on violent crime and mental illness (Apr 2026).
- **cost-of-living-taxes** (10 docs): concrete asks in the Budget 2026 releases (scrap PST on food production and farm equipment, real $10-a-day childcare, debt-per-person and $13.3B deficit criticism), "Look West" critique, tariff/economy releases. Note: no stated position on income tax rates or taxes on high earners.

**Moderate**

- **indigenous-reconciliation** (9 docs): dedicated statement "Reconciliation, Certainty, and Prosperity" (Aug 2026, reworks DRIPA while affirming rights and title), "The Hard Work of Certainty: Resolving B.C.'s Original Sin" op-ed (Mar 2026), and Sturko's Bill M241 (Apr 2026, would repeal the Interpretation Act's DRIPA interpretation clause). Distinctive and codable, but the stance is economic-certainty framing rather than rights-expansion.

**Thin topics: housing, climate-environment**

- **housing**: only one party document with substantive mentions (Budget 2026 release: link housing policy to affordability outcomes) plus passing vision-page language. No housing policy document, no supply/density/rent specifics.
- **climate-environment**: 7 docs but the substance is pipeline advocacy ("five hard conditions" Oct 2025, pipeline-conditions op-ed Jul 2026), wildfire accountability (Aug 2026), and vision-page green-tech language. No emissions targets, carbon pricing stance, or conservation specifics.

## Hansard note

8 Hansard records, all drawn from the Second Session, 43rd Parliament (Feb-May 2026), all featuring Sturko. Two caveats for coders:

1. The other seven named MLAs (Milobar, Paton, Wat, Banman, Bird, Wilson, Warbus) were CentreBC members only Sep 18-22, 2026. The legislature never sat in that window (fall session was scheduled Oct 5; the writ dropped Sep 22), so **no Hansard record shows them speaking as CentreBC members**. Their earlier statements were made as Conservatives and were deliberately excluded to avoid mis-coding.
2. Hansard files are full-day debates containing all speakers. Attribute quotes to Sturko's own remarks only. Key item: Bill M241 introduction (centrebc-0067, Apr 13, 2026).

## Gaps (honest list)

- No election platform document (pending as of Oct 1). Re-run M1 for CentreBC if the platform drops before Oct 24.
- No positions found on: income tax rates / taxes on high earners, housing supply specifics, emissions targets or carbon pricing, childcare costing, healthcare workforce numbers.
- Wayback coverage is partial (31/56). Some Wayback saves were rate-limited or blocked; local hashed copies exist for every source.
- Debate participation: media reports note CentreBC was excluded from the main televised leaders debate and lacks official party status, which limits the debate/Hansard record further.
- `sources.json` records include a `fetch_via` field ("live") written by the current helper, beyond the field list in docs/SCHEMA.md. Left in place since the helper is the mandated writer; flag if strict schema validation is required.

## Media pieces (7)

Leadership-horse-race coverage dominated the news cycle, so two policy-rich pieces were added past the 3-6 target: the Vancouver Sun merger piece (policy priorities quoted: healthcare, crime and safety) and CityNews (affordability focus, platform status). Titles and URLs are in sources.json.

## Provenance notes

- All fetches via `agents/fetch_source.py`. Early centrebc.ca fetches 403'd the helper's research User-Agent; `agents/_fetch_shim.py` (thin wrapper, same pipeline) was used until the helper gained multi-UA support.
- Two concurrent runs of this task wrote to the same directory, causing ID collisions mid-run. The directory was reconciled and renumbered; the final state has 56 records, 56 files, no duplicate IDs or URLs, and every record's sha256 verified against its file.
