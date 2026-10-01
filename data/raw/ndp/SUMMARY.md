# BC NDP (ndp) — source inventory summary

Compiled: 2026-10-01 (campaign day 10 of the BC 2026 snap election, E-day Oct 24, 2026)
Index: `data/raw/ndp/sources.json` · 46 sources · 45 with Wayback archive URLs
Files: `data/raw/ndp/ndp-NNNN.html|.txt` (and `.pdf` for the one PDF), all sha256-verified.

## Counts by type

| type | count |
|---|---|
| platform | 5 |
| policy | 9 |
| release | 10 |
| speech | 3 |
| hansard | 5 |
| media | 12 |
| other | 2 |

By date: 26 from 2026, 15 from 2024, 1 from 2023, 2 from 2017, 2 evergreen pages undated.
Pre-2026 records are year-tagged in their titles (e.g. "(2024) ...") so coders cannot mistake them for 2026 positions.

## The big caveat: there is no full 2026 platform document

As of Oct 1, 2026 the BC NDP has **not published a full platform document or platform page** for this election.
Evidence in the inventory:
- `bcndp.ca/platform` and `bcndp.ca/actionplan` both return the site homepage (soft-404). Captured as ndp-0003 (relabeled "BC NDP home").
- bcballot.ca's platform comparison (ndp-0035, checked Oct 1, 2026) lists "BC NDP platform: No platform or plan page" and derives 50 commitments from news releases.
- The campaign is branded "Build B.C. Strong" (launch release ndp-0002, Sept 22, 2026) and rolls out planks as daily announcements. Vancouver Sun (ndp-0030) confirms "Build B.C. Strong" is the platform frame.

The most recent full platform document is the **2024** "An Action Plan for You": the release (ndp-0001, Oct 3, 2024) and the platform highlights PDF (ndp-0004, Oct 2024, 4.4 MB image PDF, OCR'd during this run). The 2024 unveil coverage (ndp-0029/0033/0034, Oct 2024) describes it as a 65-page document with ~$2.9B in new investments. The $1,000 grocery rebate and middle-class income tax cut referenced on the 2026 campaign trail are 2024 promises, and coders should treat them as such unless re-announced in 2026 material.

## Topic coverage

**cost-of-living-taxes — strong.** 2026: OneBC deficit critique (ndp-0014), Doerkson health-cuts release with tax claims ("typical working family... pays $3,000 less in taxes", ndp-0015), jobs/investment release (ndp-0017), Budget 2026 debate Hansard Feb 18-19 (ndp-0024/0025). 2024: middle-class tax cut plan (ndp-0020), Action For You grocery rebate (ndp-0001), highlights PDF (ndp-0004). Media: Vancouver Sun economy piece (ndp-0030), Coastal Front fiscal analysis (ndp-0034).

**housing — strong.** 2026 plank: tax on unsold/new condos plus higher speculation and vacancy fees (party release ndp-0007, CTV ndp-0031, CityNews ndp-0032). 2024 record: highlights PDF and Action For You (ndp-0001/0004), Campbell River school (ndp-0019), Langley-Abbotsford SkyTrain (ndp-0021). Housing shows up in the Feb 19 budget debate (ndp-0025) and bcballot's commitment list (ndp-0035).

**health — moderate.** 2026 campaign plank: triple U.S. health-worker recruitment (Voice of BC ndp-0045 carries the announcement quotes; CBC analysis ndp-0044 tests the "800 recruited / 1.2M without a family doctor" record). Healthcare-cuts framing of the Conservatives (ndp-0015/0016). Health dominates the Estimates Hansards of Apr 14 and May 27 (ndp-0027/0028). Weakness: the party's own Sept 23 recruitment release was not locatable on bcndp.ca (see gaps).

**climate-environment — moderate.** 2026: critique of the Conservative LNG plan (ndp-0008), critical minerals and Port of Prince Rupert expansion (ndp-0009), the major-projects/"Build B.C. Strong" frame including Tilbury LNG (ndp-0030). Record: climate action page (ndp-0011, 2024), highlights PDF climate pillar (ndp-0004), Environmental Assessment Amendment Act (Bill 15) in Hansard (ndp-0027/0028). Note the campaign's center of gravity is resource development, not climate framing.

**indigenous-reconciliation — thin.** 2026: National Day for Truth and Reconciliation statement (ndp-0018, Sept 30), K'ómoks Treaty Act (Bill 20) in Hansard (ndp-0028), DRIPA reversal coverage (ndp-0037). The party's reconciliation page (ndp-0012) dates to 2017 and the throne-speech reprints are 2023/2024. No dedicated 2026 campaign plank found.

**public-safety — thin.** Government record only: Bail and Sentencing Reform Act royal assent (ndp-0039, June 2026), provincewide Chronic Property Offending Intervention Initiative (ndp-0042, July 2026), Safe Access to Schools Amendment Act (Bill 12) in Hansard (ndp-0026). The 2024 highlights PDF has a "Making our streets safer" pillar and the homepage uses safety framing, but no 2026 campaign release or plank on public safety was found.

## Gaps and caveats

1. **No 2026 platform document** (see above). If the NDP publishes one mid-campaign, it must be fetched and added; keep re-checking bcndp.ca and the media centre. This is the single biggest coverage risk for the codings.
2. **Sept 23 health recruitment party release not found on bcndp.ca.** The releases listing loads older items via JavaScript and page 2 (Sept 22-24) was not retrievable. Covered by ndp-0045 (quotes the announcement) and ndp-0044 (CBC).
3. **2026 throne speech Hansard not located.** leg.bc.ca's Hansard app is JavaScript-only; the members index starts Feb 12, 2026 (n116). The Feb 2026 session opening day Hansard (with the throne speech) is likely n113-115 but file names were not resolvable. The Budget 2026 debate Hansards (ndp-0024/0025) partly compensate.
4. **One source not yet archived:** ndp-0035 (bcballot.ca/platforms/) — Internet Archive save kept returning 520 during the retry pass. All other 45 have archive URLs.
5. **Internet Archive was offline** for part of this run (that is why early fetches show null archive URLs); a retry pass after it recovered archived 10 of 11 stragglers.
6. **Two evergreen pages are undated** on the site (BC NDP home, About David Eby); published is empty per schema.
7. **Inventory is above the 15-30 target (46).** The surplus is mostly 2024 background platform material and opponent-response releases; kept because they hash-match what the site serves and they pin down the party's 2024 commitments, which the 2026 campaign reuses. Titles are year-tagged to prevent miscoding.
8. **Concurrency note:** sibling agents co-wrote `sources.json` during this run (a consolidate pass renumbered records mid-flight). Every record was re-verified after the final write: file exists, sha256 matches, title matches content. If the file changes again after 2026-10-01T08:2xZ, re-run the audit.

## Provenance

- HTML sources were fetched and hashed with `agents/fetch_source.py` (raw bytes saved, text extracted, best-effort Wayback).
- Two news.gov.bc.ca records (ndp-0039, ndp-0042) were captured from Wayback archive copies because the live site refused direct fetches; their `sha256` covers the stored raw bytes and content was read and verified.
- ndp-0004 is a PDF: downloaded with curl, sha256 in the record, text extraction empty (image-only PDF); OCR of pages 1-2 was done manually during reconnaissance and confirmed it is the 2024 platform highlights.
- `sha256` in each record covers the raw fetched bytes (`local_path`); `text_path` is the derived plain text for quote hunting.
- All 46 records were re-audited after the final write: file exists, sha256 matches, URL/title match content, schema fields exact (an extra `fetch_via` field from a helper variant was stripped to conform to docs/SCHEMA.md).
