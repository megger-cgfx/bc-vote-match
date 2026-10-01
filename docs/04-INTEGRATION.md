# BCVM M5 — Integrating the codings into the site

_Status: **BLOCKED on dependencies** (card `<task-id>`, run 2026-10-01). Nothing in
`data/codings/` exists yet and the site is still being built by another worker._
_Prepared by flower._

## What M5 is, and what it is not

M5 is the step that swaps the site off placeholder data and onto the real, sourced
dataset: frozen questions + coded party positions + the quotes and source URLs that
back every code. It is *not* the scaffolding step (that is M4, card `<task-id>`) and
it is *not* the public launch (card `<task-id>`, behind a human gate).

The M5 card was created with `parents: []`, so the dispatcher ran it in parallel with
M4 and M3 instead of after them. This run found that and fixed the graph (see
"Dependency graph" below) rather than editing files that another worker is still
writing.

## What this run actually produced

One artifact, plus its tests. Both are additive: no file that M4 or M3 owns was
touched.

### `scripts/validate-dataset.py` — the M5 integration gate

The single rule that keeps the product credible is the one in `docs/SCHEMA.md`:
every non-null party code must carry a verbatim quote that really is in the source it
cites. That rule is now executable instead of aspirational.

    python3 scripts/validate-dataset.py                 # integration gate, strict
    python3 scripts/validate-dataset.py --draft         # coverage relaxed to warnings
    python3 scripts/validate-dataset.py --json          # machine-readable report
    python3 scripts/validate-dataset.py --data-root DIR # validate another dataset

It checks, and fails the run on:

| check | why it matters |
|---|---|
| `questions.json` holds only `status: "frozen"` rows | the site must not render an unfrozen statement |
| every coding row matches the SCHEMA key set exactly | extra fields mean a coder invented a shape |
| `code` is `null` or an integer in `-2..2` | out-of-range codes silently skew every score |
| a `null` code carries no quote/source | "no position" must not smuggle in a citation |
| a non-null code has a quote of 40+ chars, no placeholder text | stops filler reaching the published tables |
| `source_id` resolves in `data/raw/<party>/sources.json` | a code must point at a real fetched source |
| `source_url` equals that source record's `url` | stops a code citing one page and linking another |
| the quote is present in the cited source text | the actual provenance test |
| `coder`, `version`, `created_at`, `confidence` are present and sane | versioning is how recodes stay auditable |
| no fixture coder / fixture version | placeholder positions must be unable to ship |
| no zeroed `sha256`, no duplicate source ids, no unknown slugs | catches plumbing errors in the recon data |
| every party has a row for every frozen question | silence is how coding asymmetry creeps in |

Quote matching is whitespace- and typography-normalised (NFKC, curly quotes, en/em
dashes, line wrapping), so a quote that was re-wrapped during transcription still
matches, while a quote that was written by hand does not.

**Verified, not assumed.** `python3 scripts/validate-dataset.py` against the real
repo exits 1 and prints 9 errors, which is the correct answer today (no frozen
questions, no codings). Sixteen mutation cases each fail with the right message
(bad code range, fabricated quote, placeholder quote, dangling `source_id`,
`source_url` mismatch, null code with a quote, fixture coder, fixture version, bad
confidence, unknown field, duplicate party+question, unknown question id, zeroed
sha256, unfrozen set, partial coverage in strict mode; baseline passes). Against the
real scraped text of `data/raw/ndp/ndp-0001.txt`, a verbatim quote and a
deliberately re-wrapped variant both pass and a fabricated sentence is rejected.

_Not yet possible to verify:_ the full 5 parties x 18 questions run, because those
codings do not exist.

## Dependency graph

M5 was linked as a child of both:

- `<task-id>` — M4 Next.js static scaffold (the thing being integrated *into*)
- `<task-id>` — M3 adversarial verification of codings (the thing being integrated)

`<task-id>` is itself a child of the M2 freeze gate `<task-id>`, so M5 transitively
waits on Martin's sign-off without a second edge. The card is blocked
`kind=dependency`; it re-queues by itself when both parents are done.

## Remaining M5 checklist (mechanical once the parents land)

1. Run `python3 scripts/validate-dataset.py`. It must exit 0 before anything else.
2. Apply the freeze to the live contract file (`questions.json` gets the 18 frozen
   rows; today it still holds all 54 candidates).
3. Point the site's loader at the real dataset. `src/lib/data.ts`
   already prefers `data/` over `src/fixtures/*.sample.json`, but it falls back
   *silently*: an empty `data/codings/` produces a fixture build with a banner. That is
   the right behaviour for `npm run dev` and the wrong behaviour for a publish build.
   Add a build-time assertion that fails `next build` when `isFixture` is true.
4. Render the published coding table: one row per party per question with the code,
   the quote, and the source + archive link. This is the neutrality evidence and it is
   currently not on the site.
5. Confirm `npm run build` is green and `out/` contains no `PLACEHOLDER` string.
6. Hand to `<task-id>` (public launch, human gate).

## Findings this run handed back to other cards

- `data/raw/green/sources.json` has duplicate ids `green-0028` and `green-0033`;
  `data/raw/onebc/sources.json` has `onebc-0013` five times. Duplicate source ids mean
  a coding's citation is ambiguous. Belongs to the M1 recon cards (still running).
- `green-0028` has an empty `text_path`, so any code citing it cannot be quote-checked.
- 44 sources have no `archive_url`, and the `data/archive/` tree is empty. The plan
  treats archive + hash as non-optional, so this is an M1 gap.
- The scraped `.txt` files begin with site navigation. Code checks can't tell nav text
  from policy text, so coders must be told to quote from the body, and a nav sentence
  will pass the provenance check while being worthless as evidence.

---

## M5 run 2026-10-01 — the site builds from real data (Agent: site-integration)

The runbook items 3–5 above are done. `next build` now renders the real dataset or
fails; there is no fixture path left in the site.

### Loader (`src/lib/data.ts`) — real files only

| part | file(s) |
|---|---|
| parties | `data/parties.json` |
| questions | `data/questions/questions.v2.json` when it exists, else `data/questions/questions.json` |
| codings | `data/codings/<party>.json` (`_`/`.` sidecars skipped) |
| sources | `data/raw/<party>/sources.json` |
| riding view | `data/candidates/{ridings,candidates}.json`, falling back to `data/ridings/` |

A missing or malformed contract file **throws at build time** with the path named —
that is the build-time assertion the runbook asked for, expressed as fail-loud rather
than fail-banner. `src/fixtures/*.sample.json` is no longer imported by the site; it
remains only as unit-test data for `scripts/smoke-test.mjs`. The fixture banner
(`src/components/FixtureBanner.tsx`) and the `isFixture`/`fixtureNote` dataset fields
are gone.

### Two coders, one published code (`src/lib/reconcile.ts`)

M3 wrote two independent coder rows per (party, question); the contract and the
scoring need one. `mergeCodings()` reconciles at load time with a conservative rule —
it never invents a number neither coder wrote:

1. all rows null → `null`;
2. non-null codes agree → that code (best-evidenced row kept for provenance);
3. one non-null code, the other coder null → the sourced code wins (a null is absence
   of evidence, not a contradicting position);
4. non-null codes disagree → `null`, row marked `coder: "unresolved-split"`.

Applied to the 90 (party, question) pairs: 46 both-agree, 14 single-code, 22
both-null, **8 splits → published as null** until the L3/L4 human tie-break. Every
party clears `MIN_PAIRS = 5` (ndp 15, green 15, cpb 13, onebc 11, centrebc 6).

### Routes

`/questions/` is the one canonical questionnaire route (sitemap, home CTA, share
links). `/quiz/` — a route from a dead scaffold attempt — is now a redirect stub
(meta-refresh + client `location.replace`, noindex) so old `/quiz/` links survive the
static export, which has no server to issue a real 301.

### Scoring verified against a hand-worked example

Party **BC NDP**, six statements, six fixed answers, formula as written in SCHEMA.md:
`alignment = 1 − (Σ|user−party| / (2·n))`.

| q | user | ndp | \|u−p\| |
|---|-----|-----|--------|
| q01 | −2 | −2 | 0 |
| q04 | −1 | −2 | 1 |
| q10 | +2 | +2 | 0 |
| q11 | 0 | +1 | 1 |
| q19 | −2 | −2 | 0 |
| q28 | +1 | +2 | 1 |

Σ\|u−p\| = 3, n = 6 → `1 − 3/12 = 0.75` → **75.0 %**. The site's own code path
(`mergeCodings` + `alignmentForParty`) returns `percent=75, rawPercent=75,
compared=6, meanDistance=0.5` — identical. Reproduce with
`node --experimental-strip-types scripts/verify-hand-example.mjs` (asserts the
arithmetic and the split/null handling). `scripts/smoke-test.mjs`: 19 checks passed.

### Open items for the operator

- **8 coder splits** publish as `null` pending the human tie-break (see the rule above).
- The alignment divisor `2·n` (can yield −100 % raw) is still the schema's open spec
  issue — unchanged, methodology is behind a human gate.
- `questions.json` still holds 54 `candidate` rows; only the 18 freeze-proposal
  statements have codings, so the other 36 render with clean "no published position"
  empty states. When the freeze gate ships `questions.v2.json` the loader picks it up
  automatically. Note the 2-D compass compares the user's mean over *answered*
  questions with each party's mean over its *coded* questions; with the full 54-row
  pool those sets differ. If that matters for launch, restrict the questionnaire to
  the frozen 18 (editorial gate, not a code change).
- The M1 findings above (duplicate source ids, missing archive URLs) are unchanged.
