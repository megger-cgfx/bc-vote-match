# BCVM M6 — Riding-level v1.1

_Status: **built and verified** · card `<task-id>` · prepared by flower, 2026-10-01._
_Snapshot `v1.1`, built 2026-10-01T08:19:40Z._

## What M6 is, and what it is not

M6 adds the riding layer: a visitor enters their electoral district and sees who is on the
ballot there. It is a **fast-follow** on the party-level tool, per `docs/02-PLAN.md`
("riding-level is a fast-follow, not v1"), and it lands before advance voting (16–21 Oct).

It does **not** introduce a new code. No candidate platform has been coded, so every
alignment shown next to a candidate is that candidate's **party's** party-level code. The
page says this in plain words rather than implying a candidate-level score exists. Inventing
per-candidate positions would break the neutrality rule in `docs/SCHEMA.md`, and there is no
sourced basis for it.

## What this run produced

All additive — no party-source, coding, question or site file owned by another card was
edited except the small shared contracts noted under "Files".

### Data

| file | contents |
|---|---|
| `data/ridings/ridings.json` | 93 electoral districts (slug, name, region) |
| `data/ridings/candidates.json` | 208 candidates with district, party, incumbent and nomination status |
| `data/ridings/build-report.json` | counts + cross-checks (audit trail) |
| `data/raw/ridings/sources.json` | provenance for the two sources (url, sha256, archive_url, fetched_at) |
| `data/raw/ridings/ebc-candidates.{pdf,txt}` | Elections BC official candidate list, saved and parsed |

Counts (`build-report.json`): **93 districts, 208 candidates, 94 confirmed nominations,
75 sitting-MLA candidates.**

By party label: Conservative Party 79 · BC NDP 65 · BC Green Party 21 · OneBC 18 ·
CentreBC 14 · Independent 4 · Libertarian 3 · Other 2 · Christian Heritage 1 · CanWest 1.

### Sources and provenance

1. **Elections BC — official candidate list** (the authority for who has filed a complete
   nomination):
   `https://www.elections.bc.ca/docs/fin/GE-2026-10-24-Candidate-Website-Report.PDF`
   sha256 `ed48c18bddfc762fac47cde2be004790e2fcc72efb15509c222fa5c7a5fe22b5`,
   archived at `http://web.archive.org/web/20261001081157/…`.
2. **Wikipedia — "Candidates of the 2026 British Columbia general election"** (the complete
   93-riding roster; the Elections BC list only shows accepted nominations so far):
   `https://en.wikipedia.org/wiki/Candidates_of_the_2026_British_Columbia_general_election`
   sha256 `28854347f1bf8451dc55eaf120c617a5e4551901c81fa24252eae45c507ea02b`,
   archived at `http://web.archive.org/web/20261001081207/…`.

`status` is `nominated` when the candidate appears on the Elections BC list and `declared`
otherwise (a public candidacy not yet accepted at nomination close). `registered` records
the source article's own "* = registered with Elections BC" marker.

**No PII.** The Elections BC PDF also prints every financial- and official-agent name,
street address and phone number. The builder reads only the district, candidate-name and
affiliation columns and never writes agent data to disk.

### Scripts

- `scripts/build-ridings.py` — `fetch` (download, hash, archive) → `build` (parse the local
  copies into the JSON above). `build` is offline and re-runnable; bump `--version` for a
  new snapshot.
- `scripts/validate-ridings.py` — the M6 gate, plus `--selftest`.
- `scripts/check-riding-export.mjs` — end-to-end check on the exported site.

### Site

- `src/app/riding/page.tsx` + `src/components/RidingLookup.tsx` — district search and the
  per-district candidate list, with each candidate's party alignment when the visitor has
  taken the survey (answers stay in `localStorage`).
- `src/lib/schema.ts` (`Riding`, `Candidate`, `Dataset`), `src/lib/data.ts`
  (`loadRidings`, `loadCandidates`, `candidatesForRiding`), `src/lib/site.ts` (nav), and
  `src/app/sitemap.ts` (sitemap entry).
- `docs/SCHEMA.md` — the riding-layer contract.

## Verified, not assumed

- `python3 scripts/validate-ridings.py` → **exit 0**: "93 districts, 208 candidates,
  provenance intact".
- `python3 scripts/validate-ridings.py --selftest` → **14/14 mutation cases behave**: baseline
  passes, and a wrong district count, duplicate slug, candidate on an unknown district, bad
  party slug, party-label/ballot-label mismatch, bad status, non-boolean incumbent, extra
  field, dangling source id, bad sha256, `nominated` without an EBC source, duplicate
  candidate, and a district with no candidates each fail with the expected message.
- `npx tsc --noEmit` → clean.
- `npm run build` → green; `/riding` is prerendered as static content (route table in the
  build log).
- `node scripts/check-riding-export.mjs` → **7/7**: the exported `/riding/index.html` renders
  the district search, all 93 district slugs and the candidate roster are in the payload, the
  page states the 93-district count, and `sitemap.xml` advertises `/riding/`.
- Serving `out/` and fetching `/riding/` returns HTTP 200.

_Not verifiable in this environment:_ the interactive search/select flow needs a browser and
no browser driver is installed here. The pure logic it depends on is covered by the scoring
suite (`scripts/smoke-test.mjs`) and the export check above; the DOM wiring itself was
reviewed but not clicked.

## Known limits (stated, not hidden)

- **Stale by design.** Nominations close **3 October 2026, 1 p.m. Pacific**, so this list
  changes. Re-run `python3 scripts/build-ridings.py all --version v1.2` after close and
  rebuild. `v1.1` is a snapshot, and the page shows its version and build time.
- **One unresolvable name.** `nechako-lakes/Clint Lambert` is marked registered in the source
  article but the Elections BC layout text omits his affiliation cell, so the builder could
  not confirm him and records him as `declared`. It is the single
  `registered_not_confirmed` entry in the build report and it is expected, not a parse bug.
- **Party label drift.** One candidate is counted under `Other` rather than `Libertarian`
  because the source article's column heading differs from Elections BC's affiliation
  string for that row. It does not affect any of the five contract parties.
- **Incumbency** is taken from the source article's incumbent column and only set when that
  name is also a candidate in the district. Vacant seats ("Vacant") and retiring incumbents
  (†) correctly produce no incumbent.

## Refresh / handoff

```
npm run ridings:build      # fetch + rebuild the dataset (bump --version for a new snapshot)
npm run ridings:validate   # must exit 0
npm run build              # must be green
npm run ridings:check      # must pass
```

Findings for other cards:

- The riding layer is independent of M2/M3/M5; it renders with `data/ridings/` alone and
  needs no codings. Its per-candidate alignment is empty until codings exist, and the page
  says so.
- **Hotspot:** `src/lib/schema.ts`, `src/lib/data.ts`, `src/lib/site.ts`, `docs/SCHEMA.md`
  and `package.json` were each edited by this card as well as others (M4/M5). Changes here
  are additive, but concurrent edits to these files are the likely collision point for
  whatever lands next.
