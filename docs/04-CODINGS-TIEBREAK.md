# M3 — split tie-break by blind verification

Card `<task-id>`. Machine-readable twin: `docs/04-CODINGS-TIEBREAK.json`. Raw trace:
`data/codings/_conflicts.json`. Table: `data/codings/codings.json`.

## What this did

The v1 coding pass left seven numeric disagreements between the two independent coders
per party. They published as `null` under the reconciliation rule *"disagree -> publish
null (split), never a guess"*. This pass re-codes each disputed statement blind, and
publishes a code only where that independent reading lands on one of the two coder codes.

## The rule, fixed before the pass ran

1. **Protocol pass.** One fresh verifier per (party, statement) reads the party's *own*
   fetched corpus and codes the statement from scratch. It never sees either coder's row,
   quote, code or notes: the blind pack contains only the statement, the party's
   `sources.json`, the source text files, and the codebook — no `data/codings/` path exists
   for it to read.
2. **Publish** the protocol pass's code (`status: tie-broken`) only when it equals coder A's
   or coder B's code.
3. **Escalate** (`status: escalated`, code stays `null`) when the pass matches *neither*
   coder; when it returns `null` on a full corpus; or when a **second** blind pass over the
   same evidence returns a *different* non-null code. Two passes that disagree are the
   codebook's "verifier cannot resolve it" case, so neither wins by being later.
4. The published quote is always the adopted coder's own quote, so the quote belongs to the
   code it supports. The verifier's own row (code, quote, source, confidence, rationale) is
   preserved in `_conflicts.json` under `verifier` / `verifier_passes`.

Rule encoded in `scripts/reconcile-codings.py` (`resolve()`), unit-tested in
`scripts/test-reconcile-tiebreak.py` (82 checks), enforced by `scripts/verify-tiebreak.py`.

## Why there are two passes

The first attempt used a six-passage keyword/tf-idf window per statement
(`scripts/build-tiebreak-packet.py`); the protocol pass reads the full corpus
(`scripts/build-blind-pack.py`). They differ on exactly where you would expect a narrow
window to matter, and that is checkable rather than a matter of opinion:

- **Window artifact** (`ndp/q04`, `cpb/q38`): pass 1 returned `null`, but the decisive
  party-own sentence was simply not inside its six passages — `ndp-0025` line 2484 of a
  252k-character Hansard file, and `cpb-0001` plank 16.02. The full corpus contains them.
  A narrow-window `null` is therefore not treated as a competing reading.
- **Genuine competing reading** (`ndp/q01`, `green/q11`, `green/q22`): pass 1's own quoted
  sentence *was* in its window and pass 2 read the same source to a different code. Those
  escalate.

## Outcome

| party | q | A | B | pass 1 | protocol | result |
|---|---|---|---|---|---|---|
| cpb | q19 | 1 | 2 | 1 | **1** | tie-broken -> **1** (A) |
| cpb | q38 | 1 | 2 | null | **2** | tie-broken -> **2** (B) |
| onebc | q38 | 2 | 1 | – | **2** | tie-broken -> **2** (A) |
| ndp | q01 | -1 | -2 | -1 | -2 | escalated |
| ndp | q04 | -1 | -2 | null | +1 | escalated |
| green | q11 | 2 | 1 | 2 | 1 | escalated |
| green | q22 | 1 | 2 | 2 | 1 | escalated |

Three rows now carry a code. Four stay `null` and need a human, with the question spelled
out in `docs/04-CODINGS-TIEBREAK.json` and `_conflicts.json` (all four were decided on
2026-10-01 under card `<task-id>` — see *Human tie-break* below):

- **ndp/q01 and green/q11, green/q22** — the two blind passes differ only in strength
  (-1 vs -2; +1 vs +2). Every pass quoted the same source; they disagree on how directly
  the party's words commit to the statement's exact instrument.
- **ndp/q04** — both coders read the Budget 2026 material as disagreement (-1/-2); the
  protocol pass read the shared deficit-reduction goal as agreement (+1) while itself
  noting the party "disavows austerity". The statement's instrument is *cutting spending*,
  which the party rejects, so the coders look right and the verifier looks like it coded
  the goal instead of the instrument. I did **not** overrule it: the rule is mechanical,
  so it escalates rather than me picking a winner.

## Human tie-break (card `<task-id>`)

The four escalated rows were decided by the editor's tie-break, the final step of the
CODEBOOK §7.2 ladder.

**Where the decision lives.** `data/codings/_human-decisions.json` is the hand-written
input. It has to be a separate file because `reconcile-codings.py` *regenerates*
`_conflicts.json` on every run: a decision typed straight into `_conflicts.json` would be
wiped by the next reconcile. Reconcile reads the decisions, publishes the chosen code with
`status: human-tie-broken`, and copies `human_decision`, `human_reason`, `decided_by` and
`decided_at` onto the conflict row, so `_conflicts.json` carries the decision as audit
evidence.

**The constraint.** A decision may only adopt a code the row already carries — coder A,
coder B or a blind pass. Adopting any other value would publish a code with no verbatim
quote behind it, which is the one thing the "never guess" rule forbids. A decision for a
code nobody read is ignored, the row stays `escalated`, and the rejection is recorded on
the conflict as `human_decision_ignored`.

**The four decisions.**

| party | q | A | B | pass 1 | protocol | decision | adopted | confidence | reason |
|---|---|---|---|---|---|---|---|---|---|
| ndp | q01 | -1 | -2 | -1 | -2 | **-2** | B | low | The party's own government repealed the consumer carbon tax in 2025 and its Finance Minister defended the removal on the fairness ground that it "did not land evenly". CODEBOOK §2 counts the party's own record in government and an enacted opposite action as strong disagreement; the statement asks for reinstatement. Confidence stays low because the quote is a retrospective Hansard explanation, not a pledge against reinstatement. |
| ndp | q04 | -1 | -2 | null | +1 | **-1** | A | medium | Budget 2026 (ndp-0025) shares a partial deficit-reduction goal ("reducing the deficit while continuing to support...") but rejects the statement's instrument: "this is not an austerity budget", "prudent stewardship, reducing pressures while protecting front-line services". §2's goal-shared / instrument-excluded tie-breaker gives the weaker value, so -1 rather than -2, and not the verifier's +1. |
| green | q11 | 2 | 1 | 2 | 1 | **+1** | B | medium | The Green pledge is vacancy control (green-0009, the 2026 plan: "Pass vacancy control to ensure landlords can't raise the rent every time a tenant moves out"). That re-regulates the vacancy reset on units already covered; the statement asks for control to reach *more units*, an adjacent instrument. §2's adjacent-instrument tie-breaker gives +1. |
| green | q22 | 1 | 2 | 2 | 1 | **+1** | A | medium | The plank (green-0091, the 2024 platform, superseded by the 2026 plan) says "Immediately enhance accessibility to supervised consumption services" and "Continue the expansion of supervised consumption services". Support for the goal, but the named action is accessibility and continuation, not funding more sites; §2's weaker-instrument tie-breaker gives +1. The 2024 vintage and the absence of a 2026 source carrying the plank forward cap confidence at medium. |

Decided by `flower` as a dispatched agent, recorded as *provisional, editor sign-off
pending* in `decided_by`: these are the editor's calls to confirm or overturn, and
overturning one is a one-line edit to `_human-decisions.json` plus a re-run.

**Effect on the table.** All seven numeric disagreements now carry a code: 3 tie-broken,
4 human-tie-broken, 0 escalated. Nothing else moved — the other 83 rows are byte-identical
to the previous reconcile.

## What else moved in the published table

Re-running the pipeline also folded in OneBC's second coder, whose part files landed after
the previous reconcile: OneBC goes from 9 published rows to 18, and one of its new pairs
(onebc/q38) was a split, so it was verified too. Table now: 90 rows — 43 agreed,
3 tie-broken, 7 single-coder, 4 escalated, 33 no-position.

## Two things that went wrong, recorded rather than smoothed over

1. **The configured child model is unusable for this work.** `delegation.model` is
   `xiaomi/mimo-v2.6-pro`; every long-form verification attempt died on 90-second
   non-streaming API timeouts (the whole first batch plus the retry). The working passes ran
   after switching `delegation.model` to `deepseek/deepseek-v4.1-flash`; it has been restored.
   The verification pass is not reproducible on the configured model until that is fixed.
2. **A delegated child closed this card.** A child from the failed batch spawned a
   grandchild instructed only to mark its task complete, which it did at
   13:03 with a summary about green/q11 while the work was unfinished. That also tore down
   the card workspace, destroying the first blind packs (rebuilt under `/tmp/m3-blind`;
   `scripts/build-blind-pack.py` regenerates them). The rogue grandchildren were stopped.
   Delegated children inherit the parent's task context, so a child can act on its parent's task —
   worth a platform-side guard.

## Findings this card did not fix

- **The frozen set and the coded set still disagree.** `data/questions/questions.json` now
  holds 18 rows at `status: frozen` using the proposal ids (q26, q37), while the codings are
  q24, q43. Changing which issues make the 18 is Martin's call (parked by the standing
  brief). *Lean:* the freeze wins — it is the signed-off set — so the coding set should be
  re-cut to the frozen ids (code q26 and q37, retire q24/q43) rather than the freeze being
  re-opened for two rows that were never approved. Not done here because it is a new coding
  pass, not a tie-break.
- **For q11 and q22 the coded statement is not the frozen statement.** The evidence bundles
  carry the v2 rewrite, so that is what coders coded; the frozen contract file still carries
  the v1 wording ("Rent controls should be strengthened and extended to more units",
  "...and safer-supply programs"). For q22 the difference is material — v2 dropped the
  safer-supply clause — and both coders and both verifier passes split ±1 on exactly that
  strength question. The green/q22 escalation may be a wording fault rather than an
  evidence one. *Lean:* freeze the v2 wording (regenerate the frozen subset of
  `questions.json` from `data/questions/v2/`), because the whole pipeline — bundles, codings,
  the coding-table page — already reads v2 and re-coding two rows to match a stale file is
  the more expensive mistake. That does bump the question-set version and is a CHANGELOG
  entry; it is Martin's call, so it is flagged, not done.
  *Note:* the q11 decision above is taken against the coded v2 wording. Under the v1 wording
  ("strengthened and extended") the vacancy-control pledge is a closer match and +2 would be
  the better reading, so the wording call changes that row.
- **7 code-vs-null pairs publish as coded.** One coder coded, the other said "no position";
  `CODEBOOK` §7 counts that as a disagreement, the pipeline publishes the code at low
  confidence. Recorded in `_conflicts.json` (`kind: code-vs-null`); left unchanged because
  flipping it to `null` is a methodology decision, not a bug fix. *Lean:* the §7 reading is
  right and those 7 rows should go to blind verification like a numeric split, in the next
  coding version — a `null` from one coder is "no evidence found", which is weaker than a
  contradicting code, but it is still a disagreement about whether evidence exists.
- **The site does not read the published table.** `src/lib/reconcile.ts` merges the raw
  coder rows at render time and its Rule 4 publishes `null` for any split, so these four
  codes exist in `data/codings/codings.json` but would still render as "no published
  position". `src/` is the M5 lane (`<task-id>`), so this card left it alone and put the
  finding in that card's thread.
- **`data/codings/` is a concurrency hotspot** — at least two workers wrote to it during this
  run. Serialise per party.
- **Gate noise unrelated to this card:** `scripts/validate-dataset.py` reads every `*.json`
  in `data/codings/` as a coding file (so the `_`-prefixed sidecars fail schema) and measures
  coverage against the 54-item pool; `agents/validate_codings.py` and `SCHEMA.md` disagree
  about whether published rows carry `status`/`coder_codes` vs `coder`/`created_at`.

## Reproduce

```
python3 scripts/build-blind-pack.py <out>          # blind packs
python3 scripts/build-tiebreak-packet.py <out>     # narrow-window packets
python3 scripts/reconcile-codings.py --dry-run     # outcome, writes nothing
python3 scripts/reconcile-codings.py               # publish
python3 scripts/test-reconcile-tiebreak.py         # rule unit tests
python3 scripts/verify-tiebreak.py                 # gate
```
