# BC Vote Match — Data Contract
_Every agent writes to these shapes. Do not invent fields._

## Provenance rules (non-negotiable)
- Every code must cite a **verbatim quote** from a **real fetched source** and the URL it came from.
- Every fetched source is saved locally, hashed (`sha256`), and — where possible — submitted to the Wayback Machine (`https://web.archive.org/save/<url>`), with the returned archive URL recorded.
- `fetched_at` is ISO-8601 UTC.
- If a party has no statement on a question, `code` is `null` and `quote` is `null` — **never guess**.

## parties.json
```json
[{ "slug": "ndp", "name": "BC New Democratic Party", "short": "BC NDP",
   "leader": "David Eby", "leader_status": "permanent",
   "color": "#F58220", "url": "https://bcndp.ca" }]
```
slug ∈ {`ndp`, `cpb`, `green`, `onebc`, `centrebc`}

## data/raw/<party>/sources.json
```json
[{ "id": "ndp-0001", "party_slug": "ndp", "type": "platform|policy|release|speech|hansard|media|other",
   "title": "...", "url": "https://...", "published": "2026-09-22",
   "fetched_at": "2026-10-01T07:00:00Z", "sha256": "…",
   "local_path": "data/raw/ndp/ndp-0001.html", "text_path": "data/raw/ndp/ndp-0001.txt",
   "archive_url": "https://web.archive.org/web/…" }]
```
Source priority when coding (highest first): `platform` → `policy` → `release`/`speech` → `hansard` → `media` → `other`.

### Optional integrity annotations on a source record

A record may carry these extra fields. They are additive — `scripts/verify-data.py` ignores
them, and a record without them is assumed clean. Add them only from a source-integrity pass
(M1b), never from ad-hoc editing.

| field | values | meaning |
|---|---|---|
| `superseded_by` | source id | byte-identical capture already held by another record (same sha256); this record keeps its provenance but is not the canonical copy |
| `replaced_by` | source id | this capture is unusable (dead / maintenance / boilerplate page) and another record holds the same document from a working URL |
| `fetch_status` | `unresolved` | the recorded URL no longer resolves to a distinct document (e.g. it 301s onto another page) |
| `content_status` | `maintenance_page`, `boilerplate_only`, `partial_capture`, `ocr_text` | what the stored bytes actually contain when they are not clean page text |
| `text_source` | free text | how `text_path` was produced when it was not the original fetch (e.g. `pdftotext (embedded layer)`, `tesseract OCR`) |
| `note` | free text | human-readable explanation of the annotation |

**Coding rule:** a record with `content_status` of `maintenance_page` or `boilerplate_only`
must not be cited as a quote source — it holds no statement text. `partial_capture` supports
only what its text actually contains (typically the headline). `ocr_text` must be checked
against the stored PDF before a quote is published.

## data/questions/questions.json
```json
[{ "id": "q01",
   "statement": "The province should raise taxes on the highest earners to fund public services.",
   "topic": "cost-of-living-taxes",
   "dimensions": ["economic"],
   "status": "candidate|frozen",
   "notes": "why it differentiates the parties" }]
```
`topic` ∈ {`cost-of-living-taxes`, `housing`, `health`, `climate-environment`, `indigenous-reconciliation`, `public-safety`}
`dimensions` ⊂ {`economic`, `social`}

## data/codings/<party>.json
```json
[{ "party_slug": "ndp", "question_id": "q01", "code": 1,
   "quote": "verbatim text", "source_id": "ndp-0004", "source_url": "https://…",
   "archive_url": "https://web.archive.org/…", "coder": "agent-a", "version": "v1",
   "created_at": "2026-10-04T09:00:00Z", "confidence": "high|medium|low" }]
```
`code` ∈ {−2, −1, 0, 1, 2} for agreement with the statement, or `null` if no position.
Meaning: −2 strongly disagree … +2 strongly agree (see methodology scale).

## Scoring (v1)
- Party position per dimension = mean of its codes on that dimension's questions.
- User position per dimension = mean of their answers mapped to the same −2…+2 scale.
- Alignment with a party = `1 − (Σ|user−party| / (2·n))` over answered questions, as a percentage.
- 2-D plot: (economic, social). Topic sub-scores: mean over each topic's questions.

## Riding layer (M6, v1.1) — additive

Riding-level is a fast-follow on top of the party-level tool. It does **not** introduce a
new kind of code: a candidate has no individually-coded platform, so every alignment shown
against a candidate is that candidate's **party's** party-level code. This is stated in the
UI; it is the honest limit of a party-level method.

### data/raw/ridings/sources.json
Same record shape as `data/raw/<party>/sources.json`, with `party_slug: null` and
`phase: "riding"`:
```json
[{ "id": "ebc-list", "party_slug": null, "phase": "riding", "type": "other",
   "title": "…", "publisher": "Elections BC", "url": "https://…", "published": "",
   "fetched_at": "2026-10-01T08:12:04Z", "sha256": "…",
   "local_path": "data/raw/ridings/ebc-candidates.pdf",
   "text_path": "data/raw/ridings/ebc-candidates.txt",
   "archive_url": "http://web.archive.org/web/…", "fetch_via": "live" }]
```

### data/ridings/ridings.json
```json
[{ "slug": "abbotsford-mission", "name": "Abbotsford-Mission",
   "region": "Fraser Valley-Langley-Maple Ridge", "source_id": "wiki-candidates" }]
```
Exactly 93 rows — BC's 93 electoral districts for the 2024–2028 redistribution.

### data/ridings/candidates.json
```json
[{ "id": "rdg-abbotsford-mission-pam-alexis", "riding_slug": "abbotsford-mission",
   "name": "Pam Alexis", "party_slug": "ndp", "party_label": "BC NDP",
   "party_col": "NDP", "affiliation": "party", "incumbent": false,
   "registered": true, "status": "nominated",
   "source_id": "wiki-candidates", "source_url": "https://…",
   "ebc_source_id": "ebc-list", "version": "v1.1", "fetched_at": "…" }]
```
- `party_slug` ∈ {`ndp`, `cpb`, `green`, `onebc`, `centrebc`} or `null`.
- `affiliation` ∈ {`party`, `independent`, `other`}; `status` ∈ {`nominated`, `declared`}.
- `nominated` means the candidate appears on the Elections BC candidate list (the PDF above);
  `declared` means a public candidacy that has not yet been accepted at nomination close.
- `incumbent` is true only when the candidate is the riding's sitting MLA.
- **No PII.** The Elections BC PDF also carries financial- and official-agent names,
  street addresses and phone numbers; the builder reads only the district, candidate name
  and affiliation columns and never writes agent data to disk.

Built by `scripts/build-ridings.py` (`fetch` → `build`), gated by
`scripts/validate-ridings.py`. See docs/M6-RIDING-V1.1.md.

### data/candidates/ — riding-phase delivery bundle + postal lookup (M6b)

`scripts/build-postal-lookup.py` (`fetch` → `build` → `check`) generates, from the M6
files plus two open geographic sources (GeoNames postal-code points, Elections BC
electoral-district polygons via the Data BC WFS):

```jsonc
// data/candidates/postal-to-riding.json — site-importable, offline
{ "version": "v1.0", "built_at": "…", "source_ids": ["geonames-postal", "ebc-ed-polygons"],
  "ridings": { "abbotsford-mission": { "name": "Abbotsford-Mission", "district_id": 258,
                                      "ed_abbreviation": "ABM" } },
  "fsa":    { "V8R": { "ridings": ["oak-bay-gordon-head", "…"], "primary": "oak-bay-gordon-head",
                       "counts": { "oak-bay-gordon-head": 3012, "…": 0 } } },
  "postal": { "V8R3L2": "oak-bay-gordon-head" } }
```
- `postal` keys are 6-character postal codes without a space, uppercase. Values are a
  riding slug, or a sorted **list** of slugs for the rare code whose representative
  points straddle a boundary (the site should ask the visitor to pick).
- `fsa` (first 3 characters) is the fallback for partial input; `primary` is the riding
  containing the most postal codes of that FSA, `ridings` are all of them.
- `data/candidates/candidates.json` and `data/candidates/ridings.json` mirror the M6
  files with `riding_name` / `district_id` (Elections BC `ELECTORAL_DISTRICT_ID`) and
  `ed_abbreviation` added. `data/candidates/postal-lookup-report.json` is the audit trail.
  The M6 files under `data/ridings/` remain canonical; regenerate the bundle instead of
  hand-editing it.

Post-office level point data is GeoNames (CC BY 4.0), not the PCCF — Statistics Canada
restricted PCCF distribution to DLI members and Canada Post in 2018. Method and limits
are in `scripts/build-postal-lookup.py`'s docstring and docs/M6b-POSTAL-LOOKUP.md.
