# BC Green Party 2026 — Source Inventory Summary

Compiled 2026-10-01 for BC Vote Match (M1 Sources). Party slug: `green`. Leader: Emily Lowan (since 2025-09-24). Slogan: "Believe in Better". Domain: bcgreens.ca. All records in `data/raw/green/sources.json`, each with a local hashed copy per docs/SCHEMA.md.

## Counts

- **42 sources total.** By type: platform 3, policy 4, release 12, speech 2, hansard 4, media 12, other 5.
- **34 of 42 have Wayback archive URLs.** 8 are local-copy-only (archive_url null) because Wayback save calls were rate-limited at fetch time: green-0006, green-0020, green-0021, green-0024, green-0026, green-0028, green-0033, green-0097. Every source still has a sha256-verifiable local copy.
- Every record re-verified against its file hash after collection: no hash mismatches, no missing files, no duplicate ids or URLs.

## Key sources

**2026 platform (highest priority for coding)**
- green-0009 — "Our Plan for British Columbia" (bcgreens.ca/our-plan/). Four commitments: A Life You Can Afford, Care You Can Count On, Economic Fairness for All, Fight for your Future. This is the core 2026 platform page.
- green-0003 — election plans announcement (2026-09-23): the four commitments in Lowan's words, plus candidate announcements for Lowan (Saanich North and the Islands), Valeriote, Botterell.

**Policy documents**
- green-0018 — "Lowan Calls for Bold Tax Reform": Ultra-Wealthy Fairness Tax (one-time 5% wealth tax on centimillionaires and billionaires), inheritance tax, land-value tax.
- green-0015 — drug poisoning crisis policy package.
- green-0091 / green-0092 / green-0093 — 2024 platform PDF and the 2024 Justice and Public Safety and Indigenous Relations and Reconciliation policy PDFs (downloaded, sha256'd, text extracted with pdftotext; records written by hand per SCHEMA since the fetch helper does not handle PDFs).

**Press releases (2026 campaign and context)**
- green-0012 — Leader's Statement: BC Greens Will Not Renew CARGA (2026-02-09). The confidence-and-supply style accord with the NDP was abandoned, citing stalled or undelivered commitments. Corroborated by green-0023 (CHEK), green-0034 (CBC), green-0035 (National Observer).
- green-0004 — renters plan (vacancy control, Community Housing Fund), 2026-09-29.
- green-0005 — lift the $10-a-day childcare freeze, universal free childcare by 2031, 2026-09-28.
- green-0006 and green-0098 — LNG Canada Phase 2 statements (Sept 2026 FID reaction; May 2026 FID push response with Valeriote on flaring and health).
- green-0007 — ten urgent climate actions. green-0008 — wildfires emergency statement.
- green-0014 — statement on the snap election (2026-09-18).
- green-0029 — statement on National Day for Truth and Reconciliation (2026-09-30).
- green-0099 — call on the Auditor General to investigate lost gas royalties.

**Speeches**
- green-0039 — Lowan's UBCM speech (2026-09-16, video page; transcript in description).
- green-0040 — 2026 election presser (2026-09-23, video page; transcript in description).

**Hansard (43rd Parliament, 2nd Session)**
- green-0028 — 2026-04-16, Woodfibre LNG expansion and local taxation (Valeriote).
- green-0033 — 2026-02-26, Bill 5 Trade Recognition Act second reading (Valeriote).
- green-0096 — 2026-05-27 pm, Botterell bill debate.
- green-0097 — 2026-05-26 am, Green MLA exchange re sale of tobacco products.

**Media (12 pieces)**
- Accord collapse: CBC (green-0034), National Observer (green-0035), CHEK (green-0023).
- Platform and policy analysis: Times Colonist on tax reform (green-0036), The Tyee interview on Lowan's next steps (green-0037), Western Standard cost-of-living party comparison (green-0022), Victoria Buzz campaign coverage (green-0020), Daily Hive on vacancy control (green-0021), West Coast Current on childcare (green-0024), Yahoo/CBC campaign weekend wrap (green-0026).
- Indigenous rights: This is VANCOLOUR, Lowan defends DRIPA (green-0038).
- Public safety: Global Green News leadership debate coverage, policing positions (green-0095).

## Topic assessment

| Topic | Strength | Evidence |
|---|---|---|
| cost-of-living-taxes | **Strong** | Dedicated tax policy release with named instruments (green-0018), cost-of-living roundups, childcare and renters announcements, platform pillar "A Life You Can Afford" / "Economic Fairness for All" |
| housing | **Strong** | Renters plan release (green-0004), vacancy control coverage (green-0021, green-0020), platform commitments on housing supply and rent |
| health | **Medium-strong** | Platform "Care You Can Count On" (family doctors, mental health through the public system, community health centres), drug poisoning policy (green-0015), LNG flaring health arguments (green-0098). No standalone 2026 health-care platform release captured |
| climate-environment | **Strong** | Ten urgent climate actions (green-0007), wildfires statement (green-0008), two LNG Phase 2 statements, Woodfibre LNG Hansard, gas royalty releases, UBCM speech, full 2024 climate platform (green-0091) |
| indigenous-reconciliation | **Medium** | NDTR statement (green-0029), right-to-say-no and consultation language in the LNG statements, DRIPA defence interview (green-0038), 2024 Indigenous Relations policy PDF (green-0093). 2026-specific policy detail is thin |
| public-safety | **Thin** | Only the 2024 Justice and Public Safety policy PDF (green-0092) and leadership-debate coverage of policing positions (green-0095). No 2026 platform plank, release, or Hansard segment on policing or justice captured |

## Gaps and cautions

1. **Public safety is the weakest area.** The party's 2026 platform page barely touches policing or justice; coders will have to lean on the 2024 policy PDF (lower priority tier in SCHEMA) or code null. If the party publishes a 2026 public safety plank before Oct 24, it should be added.
2. **Indigenous reconciliation in 2026 is statements, not detailed policy.** DRIPA defence and the right-to-say-no framing are clear, but there is no 2026 document equivalent to the 2024 Indigenous Relations PDF.
3. **No dedicated 2026 health-care release** beyond the platform page and the drug poisoning package.
4. **8 sources have no Wayback snapshot** (listed above). Local hashed copies exist for all 42; retry archiving later if needed.
5. **Speech sources are video pages** (YouTube). Transcripts live in the video descriptions, which the saved text extracts capture; there is no separate transcript file.
6. **Collection notes.** Two collection passes ran concurrently on this shared folder. Records were merged and deduplicated by URL, a byte-identical duplicate fetch (green-0010) was dropped from the index, one ID collision (green-0033) was repaired by refetch, and every record was re-verified against its file hash. Unreferenced duplicate artifacts remain on disk and are not in sources.json: green-0001.{html,txt} (duplicate of our-plan, green-0009), green-0010.{html,txt} (byte-identical to green-0003), green-0027.{html,txt} (duplicate of the UBCM video page, green-0039), green-0028.pdf (byte-identical to the 2024 platform PDF, green-0091). A `fetch_via` field emitted by a modified copy of the fetch helper was stripped so all records match docs/SCHEMA.md exactly. PDF sources (green-0091 to green-0093) were fetched and hashed with agents/fetch_pdf_source.py because agents/fetch_source.py does not extract PDF text; their record shape is identical to the helper's.
