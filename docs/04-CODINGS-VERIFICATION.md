# M3 v1 codings — verification note

_Point-in-time snapshot: 2026-10-01 12:43 PDT, card `<task-id>` (run 60), repo commit `a14531b`._
_Read-only pass: nothing under `data/` was modified by this run. Other workers were writing
`data/codings/v1/` while it ran (see "Live" below), so re-check before acting on counts._

## What was checked

The reconciled v1 dataset (`data/codings/codings.json`, produced by cards `<task-id>` and
`<task-id>`) was verified against the M2 freeze packet (`docs/03-QUESTION-FREEZE.md`,
`data/questions/freeze-proposal.json`) and the schema/provenance gates in `scripts/` and `agents/`.

Passing:

- **Schema.** `agents/validate_codings.py` over the 11 v1 coder files: 171 rows, 0 errors, 0 warnings.
- **Quote provenance.** All 45 published non-null rows cite a trusted stored source whose text
  contains the quote verbatim (after smart-quote normalisation): 45/45, 0 failures, 0 sources with
  unreadable text.
- **Split rule.** The 6 split rows publish `code: null`, never a guess.

## The decisive problem: the coded set is not the proposed frozen set

Frozen proposal (18): `q01 q03 q04 q10 q11 q18 q19 q22 q26 q28 q29 q31 q37 q38 q39 q46 q47 q48`
Actually coded (18): `… q24 … q43 …` — i.e. **q24 for q26** and **q43 for q37**, in all five parties.

The substitution is not recorded in any contract file: `data/questions/questions.json` is still the
54-item candidate pool (all `status: "candidate"`, no frozen set at all), `freeze-proposal.json`
still carries q26/q37, and `docs/03-QUESTION-FREEZE.md` still reads "PROPOSED — awaiting sign-off".
Every bundle under `data/bundles/` is built on the substituted set.

The swap is also a measurable regression. Codes below are from the two passes (v0.9 = proposed set,
v1 = substituted set):

| statement | NDP | CPB | Green | OneBC | CentreBC | verdict |
|---|---|---|---|---|---|---|
| q37 implement DRIPA (proposed) | +2/+2 | −2/−2 | +2/+2 | −2/−2 | −1/+1 | 5 parties positioned, 1 split |
| q43 Indigenous procurement (coded instead) | null | null/+1 | null | — | null | 4 parties no-position, 1 row total |
| q26 nurse ratios (proposed) | null | null/+1 | +2/+2 | null | null | 1 party positioned |
| q24 public dental care (coded instead) | null | null | null | null | null | 0 rows in 10 coder passes |

q37 is the sharpest five-party spread in the dataset; q43 is dead weight. Dropping it removes the
campaign's defining flashpoint and buys nothing. q26→q24 is thinner either way but q26 at least
separates the Greens while q24 separates nobody.

**Lean: keep the proposed 18 (q26, q37) and re-code those two statements.** That is 20 rows
(2 statements × 5 parties × 2 coders). The q24/q43 codes can be kept in the archive as a discarded
variant. If the swap is instead approved, the contract file must be re-cut to q24/q43 and the M2
rationale in `docs/03-QUESTION-FREEZE.md` rewritten — and the answer set would then contain a
statement no party is on record about.

## Integration gate is red

`scripts/validate-dataset.py` (the provenance/publish gate) is **BLOCKED**:

- `0 frozen questions` — it reads `data/questions/questions.json`, which was never re-cut to the
  frozen 18. This alone blocks publication.
- `duplicate coding for this party+question` for ndp/cpb/green/onebc/centrebc — the stale v0.9 files
  `data/codings/<party>.json` (coded against the pre-freeze set, commit `0f47b54` era) still sit
  beside the new `data/codings/codings.json`, and the gate loads every `*.json` in that directory.
- The metadata files `_verification.json` and `_citation_audit.json` in the same directory are
  parsed as coding files and fail the schema (`must be a JSON array`, unknown fields).
- `34 missing questions per party` — coverage is measured against the 54-item pool.

M5 (`<task-id>`, running) runs this gate as part of launch prep, so it will hit the same wall.

## Live fixes observed during this pass (do not double-work these)

- `<task-id>` (tie-break, run 61) is filling the OneBC second coder: at 12:39 OneBC coder A covered
  `q01–q24` and coder B only `q28–q48` — disjoint halves, i.e. **no independent double-coding**; by
  12:42 `onebc-coderB-part1.json` had landed (commit `a14531b`).
- The 6 split rows are that card's job.

## Smaller items

- `docs/04-CODINGS.md` still says "v0.9-prefreeze · PROVISIONAL · awaiting freeze" and lists q26/q37.
  Re-stamp to v1 only after the set decision and the tie-break.
- `ndp` q38 and q39 cite `ndp-0028`, which M1b marked `superseded_by: green-0096` (duplicate
  capture). Re-point to the surviving record.
- `data/bundles/<party>/<party>/` contains nested duplicate bundle trees (e.g. `data/bundles/ndp/ndp/`),
  and the whole `data/bundles/` tree is uncommitted.

## Hotspot

`data/codings/` is being written by at least two workers at once (this run, run 61, and the
orchestrator's direct commits). Serialise per-party work there before adding more.
