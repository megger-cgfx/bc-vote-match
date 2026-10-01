# BCVM M7 — Recode pass #2 (Oct 20), v2 → v3

_Status: **cannot run today — dispatched before its inputs exist** (card `<task-id>`,
run 2026-10-01). Tooling independently re-verified this run; the pass itself is blocked
`kind=dependency`._
_Prepared by flower._

## Why this card did nothing but a runbook

The board's cards were all created with `parents: []`, so the dispatcher starts every
milestone in parallel. That is the third time it has bitten:

- `<task-id>` (M5 integration) — nothing to integrate; fixed in `docs/04-INTEGRATION.md`.
- `<task-id>` (M7 recode #1, Oct 12) — ran in parallel with the codings it is meant to recode;
  fixed in `docs/05-RECODE.md`.
- `<task-id>` (this card, M7 recode #2, Oct 20) — same defect, plus it was dispatched
  *simultaneously* with recode #1.

Today (Oct 1): `data/codings/` is empty, `data/codings/archive/` does not exist, the
18-question freeze is not signed off (`<task-id>` blocked on Martin), and the site is a
fixture build. There is no v1 to freeze and no v2 to diff, so the Oct 20 pass has nothing
to consume. Writing a v2→v3 report now would mean inventing codings, which is exactly the
thing this project cannot do.

**No file owned by another running worker was touched.** `scripts/recode-diff.py`,
`scripts/test-recode-diff.py` and `docs/05-RECODE.md` belong to recode #1, which was still
running when this card started; this card only read them and ran them.

## What this run actually did

1. **Independently re-verified the recode tooling** rather than trusting recode #1's
   summary (a second pair of eyes on the one artifact this card depends on):

       python3 scripts/test-recode-diff.py      # 15/15 cases behaved as expected, exit 0
       python3 scripts/recode-diff.py           # exit 3: "no baseline to diff against"

   Both match what `docs/05-RECODE.md` claims. The tool refuses to diff data it does not
   trust, which is the behaviour the Oct 20 pass needs.

2. **Fixed this card's graph** so it stops being dispatched into an empty repo: linked as
   a child of

   - `<task-id>` — M7 recode #1 (Oct 12). Hard dependency: the Oct 20 pass diffs against
     the `v2` snapshot that the Oct 12 pass produces.
   - `<task-id>` — M5 public launch (human gate). A recode log for a site that is not
     public yet has nothing to amend.

   Blocked `kind=dependency`; it re-queues by itself when both parents are done.

## The Oct 20 pass, mechanically (once the parents land)

The only difference from Oct 12 is the labels: recode #1 freezes `v1` and publishes
`RECODE-v1-to-v2.md`; this pass freezes `v2` and publishes `RECODE-v2-to-v3.md`.

    # precondition: data/codings/ hold the recoded set and validate-dataset.py exits 0
    python3 scripts/validate-dataset.py                  # must be green first
    python3 scripts/recode-diff.py --snapshot v2         # freeze the Oct-12 result as v2
    # ... run the Oct 20 recode as an M3-shaped pass (2 coders + blind verification)
    #     writing into data/codings/ against the SAME frozen 18 questions ...
    python3 scripts/validate-dataset.py                  # must still be green
    python3 scripts/recode-diff.py                       # newest archive -> live
    # writes data/codings/recode/RECODE-v2-to-v3.{json,md}

Do **not** start editing `data/codings/` before `--snapshot v2` runs. An unfrozen baseline
cannot be reconstructed afterwards; that is the one step in M7 that is not recoverable.

## Human review checklist for the published diff

The tool classifies and counts; it does not judge. Before `RECODE-v2-to-v3.md` goes on the
site, a human reads it for:

- every `position-changed` row: is the new code defensible from the cited quote, and does
  the quote really come from the body of the source (not the nav header `docs/04-INTEGRATION.md`
  warns about)?
- every `provenance-changed` row with the same code: did the evidence *move* (a platform
  page was edited, a candidate changed their line), or did a coder just pick a different
  quote? Both are publishable, but they are not the same claim.
- the position-movement table: any delta a reader would notice needs a sentence of
  explanation in the log, not just a number.
- `null` → code and code → `null` rows: these change a party's mean and, if it is the last
  non-null code on a dimension, drop the position to `—`. Check the `n_from → n_to` column.
- symmetry: the same review effort per party, same as M3.

## Guardrails

- `--snapshot` refuses to overwrite an existing label. Never pass `--force` to a **published**
  baseline; a public diff that can be quietly rewritten is not a diff. If a mistake is made,
  publish a new label, do not rewrite the old one.
- The recode log is pinned to the two snapshot `content_sha256` values, so the published
  page can be re-derived and checked by anyone.
- `data/codings/archive/` does not exist yet; it is created by the first `--snapshot`.

## Findings handed back

- `hotspot: scripts/recode-diff.py, docs/05-RECODE.md` — two M7 cards (Oct 12 and Oct 20) were
  dispatched into the same repo at the same time. They do not conflict in the end (this card
  wrote only `docs/06-RECODE-OCT20.md`), but the next wave should not run two cards that both
  own `data/codings/recode/`.
- The shared-repo write contention already flagged by the M1 recon cards (one worker per
  `data/raw/<party>/`) applies to `data/codings/` too: only one M7 pass should write
  `data/codings/archive/` and `data/codings/recode/` at a time.
