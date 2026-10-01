# M3 v1 codings — adversarial verification (card `<task-id>`)

_2026-10-01 12:45 PDT · repo commit `18838df` · read-only pass; nothing under `data/` was touched._

Independent re-test of the v1 coding dataset's claims. I did not trust the sibling pass
(`docs/04-CODINGS-VERIFICATION.md`, card `<task-id>`); I re-derived each claim from the files and
spot-checked the provenance claim by hand. Where I agree with the sibling I say so; where the
evidence is thinner or the prior write-up overstated, I say that too.

## Verdict

**The v1 codings are not publishable and must not be integrated.** The provenance — the thing this
project lives on — holds up. Everything around it does not: there is no frozen question set in the
repo, the coders coded a different set than the one proposed, and the dataset is mid-flight.

## What I re-verified and agree with (survives an adversarial pass)

- **Quote provenance is real.** The sibling claims 45/45 non-null quotes are verbatim in their cited
  source. I hand-checked 4, spread across three parties and two source types, and all 4 are present
  verbatim in the resolved `text_path` of the cited `source_id`:
  - `ndp q10` -> "We also removed barriers to deliver more homes near transit hubs and other services…"
    -> `data/raw/ndp/ndp-0013.txt:137` (policy page).
  - `ndp q01` -> "the carbon tax did not land evenly on everyone…" -> `ndp-0024.txt:741` (Hansard, re-wrapped).
  - `cpb q43` -> "Jon Coleman is a direct result of how exclusionary procurement has left out First
    Nations on contracts." -> `cpb-0026.txt:802-804` (split across a line-break; normalisation needed,
    the quote is genuine).
  - `centrebc q04` -> "With no path to balancing the budget and a record-breaking $13.3 billion
    deficit…" -> resolved via `centrebc-0050` to `centrebc-0039.txt:121`. This one is worth noting: the
    id/file numbering is offset (source `centrebc-0050` maps to file `centrebc-0039.txt`), so a naive
    "quote not in <id>.txt" check gives a false miss. The gate resolves through `text_path`, which is
    correct.
  CLI: `agents/validate_codings.py` over the 5 top-level party files reports 180 rows and **0 quote
  errors** — its only 18 errors are missing `archive_url` fields where the source record has one.
- **The split rule holds.** Every split row publishes `code: null` with the two coder codes kept in
  `coder_codes`; no split is published as a guess.

## What does not hold

### 1. There is no frozen 18 in the repo (blocker)

- `data/questions/questions.json` is still the **54-item candidate pool** (`status: "candidate"`,
  no frozen item). `scripts/validate-dataset.py` reports `0 frozen questions` and blocks publication.
- `docs/03-QUESTION-FREEZE.md` line 3 still reads **"PROPOSED — awaiting Martin's sign-off. Not live."**
- `docs/COMMANDER-BRIEF.md` line 21 claims the freeze is **"DONE Oct 1, tagged `q-v1`, pushed."**
  That is wrong: tag `q-v1` points at commit `1b64be3`, whose tree contains **no question artifact**
  (it only added `data/archive/ARCHIVE-RETRY.md`, edited `retry-results.json`, and edited the brief
  itself). The tag does not pin a frozen set.
- A parallel **v2 statement rewrite** exists (`data/questions/questions.v2.json` + six files under
  `data/questions/v2/`), built ~03:00, with different wording from both the pool and the proposal.

So there are three competing, non-canonical question sets — pool / `freeze-proposal.json` (v1 wording,
`q26`/`q37`) / v2 (revised wording). A verification cannot assert "the codings match the frozen set"
when no canonical frozen set exists.

### 2. The coded set is not the proposed set (blocker)

The reconciled `data/codings/codings.json` codes these 18 ids for ndp, cpb, green, centrebc:
`q01 q03 q04 q10 q11 q18 q19 q22 q24 q28 q29 q31 q38 q39 q43 q46 q47 q48`.

Against the proposal (`docs/03-QUESTION-FREEZE.md` / `freeze-proposal.json`):
- **coded but not proposed: `q24`, `q43`**
- **proposed but not coded: `q26`, `q37`**

This is a regression, not a neutral swap:
- `q37` (implement DRIPA) is described in the freeze doc itself as *"the defining flashpoint of the
  2026 campaign"* with a five-party spread. `q43` (Indigenous procurement), coded instead, carries a
  single real code in the entire dataset (`cpb`, single-coder, low confidence).
- `q24` (public dental care) carries **zero** codes in any party — every row is `null`.

Net effect: the published answer set loses its sharpest differentiator and gains a statement on which
no party is on record.

### 3. OneBC is not double-coded in the published file (blocker)

`codings.json` holds only **9** OneBC rows (`q01–q24`), and every one has `coder_codes` with an `A`
key only. The OneBC second-coder files (`onebc-coderB-part1.json` 12:42, `onebc-coderB-part2.json`
12:38) landed **after** the reconciler wrote `codings.json` at 12:37, so they are not in the
reconciled file. Locked decision: "two independent coders per party" — OneBC is at one. This is live,
not final: card `<task-id>` (run 61) is still writing `data/codings/v1/`.

### 4. The integration gate is red (`scripts/validate-dataset.py`)

`RESULT: BLOCKED — do not publish · 0 frozen questions · 99 codings · 2020 errors · 9 warnings`.
Most of the 2020 are one gate bug plus one stale-data problem, but the frozen-question failure is real:

- `0 frozen questions` — reads the 54-item pool (real blocker).
- **Gate bug:** the gate parses every `*.json` in `data/codings/`, so the process sidecars
  `_coder-notes.json`, `_citation_audit.json`, `_verification.json`, `_conflicts.json` are read as
  coding files and fail the schema (`unknown field`, `must be a JSON array`). These are notes/audits,
  not codings. The gate should skip `_`-prefixed files. (Worth fixing regardless.)
- **Stale data:** the v0.9 per-party files `data/codings/<party>.json` (pre-freeze, commit `0f47b54`
  era) still sit beside `codings.json`; the gate loads both and emits mass `duplicate coding for this
  party+question`. Archive/remove the v0.9 files.
- Schema: `codings.json` rows lack `docs/SCHEMA.md`'s required `coder` and `created_at`, and add
  non-contract fields (`status`, `coder_codes`). Either the file or `SCHEMA.md` must move.

### 5. Citation hygiene

`ndp q38` (single-coder) and `ndp q39` cite `ndp-0028`, which `data/raw/ndp/sources.json` marks
`superseded_by: green-0096` (duplicate capture). Re-point to the surviving record so the published
citation does not point at a withdrawn source.

## The one decision this needs (Martin's, not mine)

Which issues make the 18 is explicitly a park-and-wait item, so I am not deciding it.

**Lean:** freeze on the **v1-wording proposal already in `freeze-proposal.json`** — keep `q26`/`q37`,
re-cut `data/questions/questions.json` to those 18 at `status: "frozen"`, and archive the `q24`/`q43`
variant. Then re-code `q26` and `q37` (2 statements x 5 parties x 2 coders = 20 rows). Reasons: the
coders already worked the v1 wording, the proposal is the only 18 that exists as a tracked artifact,
and it restores the five-party DRIPA split. Treat the v2 statement rewrite as a **separate, later**
pass — adopting revised wording now invalidates every coding and belongs to the Oct 12 / Oct 20 recode
cards (`<task-id>`, `<task-id>`) that already exist.

If the freeze is instead cut to the v2 wording, that is a full re-code, not a two-statement patch, and
should be scheduled as such.

## Artifacts

- `docs/04-CODINGS-ADVERSARIAL.md` (this file)
- `docs/04-CODINGS-ADVERSARIAL.json` (machine-readable verdict)
