# BCVM M7 — Recode pass, versioned and published

_Status: **tooling built and tested; the recode itself is blocked on the codings existing** (card `<task-id>`, run 2026-10-01)._
_Prepared by flower._

## What M7 is, and what it is not

M7 is the two scheduled recode passes in `docs/02-PLAN.md` (Oct 12 and Oct 20). Its
whole job is the sentence in the plan: **versioned diffs, published**.

It is not a re-run of M3 (the first full coding pass) and it is not a new dataset. It is
the record that says: the v1 codings are frozen, here is v2, here is exactly which
party/question codes moved and where the evidence changed, and here is what that does to
the numbers on the site. A voter advice tool that silently edits its own coding table
mid-campaign has no credibility; the diff *is* the neutrality evidence for the change.

## The tool: `scripts/recode-diff.py`

    python3 scripts/recode-diff.py --snapshot v1        # freeze the current codings as the baseline
    python3 scripts/recode-diff.py                      # diff newest archive -> data/codings
    python3 scripts/recode-diff.py --from DIR --to DIR   # explicit snapshots
    python3 scripts/recode-diff.py --fail-on-change      # exit 1 if a code actually moved

`--snapshot LABEL` copies the per-party coding files from `data/codings/` into
`data/codings/archive/LABEL/`, writes a `MANIFEST.json` with a sha256 per file plus a
`content_sha256` over the whole snapshot, and **refuses to overwrite an existing label**
(that is the point of a published baseline; `--force` is the explicit override).

The diff loads two snapshot directories and, for every party x question, classifies the
change:

| status | meaning | counts as a position change? |
|---|---|---|
| `position-changed` | the `code` differs (including `null` <-> integer) | yes |
| `added` / `removed` | the question row appears or disappears | yes |
| `provenance-changed` | same code, different `quote` / `source_id` / `source_url` / `archive_url` | no |
| `meta-changed` | only `confidence` / `coder` / `version` / `created_at` | no |
| `unchanged` | identical | no |

A `version` bump on its own is therefore *not* a position change, which is what makes the
log readable: it lists what a reader would actually see move, and keeps the bookkeeping
noise in its own bucket.

It also reports the effect on the **published numbers**: each party's economic and social
position (mean of its non-null codes on that dimension's questions, `docs/SCHEMA.md`
scoring v1) before and after, with the delta and the code count behind each mean. A recode
that moves a code but not a position, or moves a position by an unexpected amount, shows
up there immediately.

Output is always both machine-readable and human-readable:

- `data/codings/recode/<from>-to-<to>.json` — the full diff, pinned to the two
  `content_sha256` values
- `data/codings/recode/RECODE-<from>-to-<to>.md` — the publishable page

A snapshot directory that contains non-party json (a `MANIFEST.json`, a previously written
`RECODE-*.json`) is diffed on its party files only, so the archive can hold the reports
next to the data without corrupting the comparison.

**Exit codes:** `0` ran; `1` a position-level change exists and `--fail-on-change` was
passed (so CI can gate a merge); `3` could not run — no baseline, unreadable snapshot, or
a malformed row. The tool never silently diffs data it does not trust.

## Verified, not assumed

`python3 scripts/test-recode-diff.py` — 15/15 cases pass. The suite builds throwaway
snapshot pairs in temp dirs and checks the tool says exactly the right thing: a code that
moves is a position change with the correct score delta (−1.0 for the worked example);
`null`→code and code→`null` are position changes; a quote edit is evidence-only; a
confidence edit and a bare version bump are meta; added and removed rows are counted as
position-level; the content hash is order-independent; `--snapshot` writes a manifest and
refuses to overwrite; the default baseline is the newest archive; a missing baseline and a
malformed code both exit 3 with the right message; and both report files are written.

Against the **real repo today** the tool exits 3 with the correct answer:
`no baseline to diff against. Freeze the current codings first:` — because
`data/codings/` is still empty and there is no M3 output to freeze.

_Not yet possible to verify:_ a real v1→v2 diff, because no codings exist. The synthetic
suite is the whole of the evidence for the code paths until M3 lands.

## Dependency graph

This card was created with `parents: []`, so the dispatcher ran it in parallel with the
codings it is supposed to recode. Same defect M5 hit (`docs/04-INTEGRATION.md`). Fixed by
linking two parents:

- `<task-id>` — M3 adversarial verification of codings (produces the v1 codings to freeze)
- `<task-id>` — M5 integrate codings into the site (the surface the diff is published on)

`<task-id>` is already a child of the M2 freeze gate `<task-id>`, so M7 transitively
waits on Martin's sign-off without a second human edge. The card is blocked
`kind=dependency` and re-queues by itself when both parents are done.

Publishing the Oct 12 diff also presumes the Oct 8 public launch (`<task-id>`, human
gate) has happened; a recode log for a site that is not public yet has nothing to amend.

## Remaining M7 checklist (mechanical once the parents land)

1. `python3 scripts/recode-diff.py --snapshot v1` immediately after the v1 codings pass
   `scripts/validate-dataset.py`, and before anyone starts editing them. This is the one
   step that cannot be recovered later — an unfrozen baseline cannot be reconstructed.
2. Run the recode as a normal M3-shaped pass (two coders, blind verification) against the
   same frozen questions, writing into `data/codings/`.
3. `python3 scripts/validate-dataset.py` must pass on the recoded set.
4. `python3 scripts/recode-diff.py` to produce the v1→v2 report; read the position-movement
   table and check every delta is one the coders can defend from the source.
5. Publish `data/codings/recode/RECODE-v1-to-v2.md` on the site next to the coding table,
   and link it from the methodology page.
6. Repeat for the Oct 20 pass with `--snapshot v2` and a v2→v3 diff.

## Findings this run handed back to other cards

- The recode log is only as good as the provenance it diffs. `docs/04-INTEGRATION.md`
  already recorded that the scraped `.txt` files open with site navigation, so a quote can
  be verbatim and still be worthless. The diff cannot see that; it reports that the quote
  *changed*, not that either quote is real evidence. `scripts/validate-dataset.py` stays
  the gate for "the quote is in the cited source", and neither tool substitutes for a
  human reading the change.
- `positions()` returns `null` for a dimension when a party has no non-null codes on it. A
  recode that drops a party's last code on a dimension will therefore show a mean going to
  `—`, which is correct but easy to misread as "no change". The `n_from → n_to` column is
  there so it cannot be read that way by accident.
