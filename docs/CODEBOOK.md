# BC Vote Match — Coding Rulebook (CODEBOOK)

_The single authority for how party positions are coded. Every coder agent follows this
document. The data shapes it refers to are defined in `docs/SCHEMA.md`; nothing here
permits inventing fields._

Version: v1 · applies to coding version `v1` (and later) against `data/questions/questions.json`.

## 1. What a code is

For each (party, question) pair you assign one integer from the five-point scale below,
measuring **how far the party's stated position agrees with the questionnaire statement as
written** — not how good the policy is, not how likely it is, not how the party's voters feel.
One row per coder per question, in `data/codings/<party>.json`.

## 2. The five-point scale

Worked examples use this statement (real one from the pool):

> **S:** "The province should raise taxes on the highest earners to fund public services."

| code | meaning | worked wording example that earns the code |
|---|---|---|
| `+2` | **Strongly agree.** The party commits to the statement's action in its own words, with emphasis, priority, or a concrete promise to do it. | "We will raise taxes on the wealthiest to fully fund health care and education." |
| `+1` | **Agree.** The party supports the action but partially, conditionally, or without enthusiasm — a weaker instrument, a smaller scope, or a hedge. | "We're asking top earners and owners of $3-million-plus homes to pay a bit more to protect services." |
| `0` | **Explicitly neutral.** The party has actually refused to take a side, deferred the question, or deliberately balanced both directions **and said so**. Silence is never `0`. | "We will not raise income taxes in this term, and we will not cut them; the review will report after the election." |
| `-1` | **Disagree.** The party opposes the action but weakly, partially, or with an explicit openness to parts of it. | "Now is not the time for broad tax increases, though we'd look at closing loopholes." |
| `-2` | **Strongly disagree.** The party rejects the action outright, promises the opposite, or makes opposing it a headline commitment. | "Under my government, there will be no new taxes on anyone — full stop." |
| `null` | **No stated position.** The party has said nothing that bears on the statement (see §5). | (no quote; `quote` is `null`) |

Coding is about **direction and strength toward the statement**. A party that wants the
opposite policy is negative even if its motivation is sympathetic. Reverse-worded statements
(q15 "Municipalities … should have the final say", q50 "Safer-supply … should be scaled back")
are coded literally as written — agreeing with a reverse-worded statement is still `+`.

Tie-breakers within the scale:
- Commitment strength beats rhetoric: a funded, named promise is at least `+1`/`-1` more than a value statement.
- If the party supports the goal but names an instrument the statement excludes (or vice versa), code the weaker value (`+1`/`-1`), not `+2`/`-2`.
- Past action counts when it is the party's own record in government and nothing supersedes it, but see §4 on dates.

## 3. Source priority ladder

Evidence comes only from fetched, hashed sources listed in `data/raw/<party>/sources.json`.
When sources could support different codes, resolve by rung (highest first):

1. **Platform or policy document** (`type: platform|policy`) — the party's own published platform, policy paper, or costed plan.
2. **Official releases and leader statements** (`type: release|speech`) — news releases, campaign announcements, leader speeches and platform-launch remarks.
3. **Minister or critic statements in Hansard** (`type: hansard`) — legislature debate, including the party's front bench speaking for the party.
4. **Media reporting** (`type: media`) — interviews and reported statements; direct quotes of a named party figure only, never the reporter's characterization.
5. **Other** (`type: other`) — anything else; lowest weight.

Rules:
- **A higher rung overrides a lower rung** when they conflict, even if the lower-rung source is newer — unless the newer source explicitly repudiates the older position (then the newer statement stands and the confidence notes the reversal).
- **Same rung conflict:** use the most recent dated source; set confidence to `medium` or `low`.
- **Never stitch.** One quote, one source. You may not assemble a position out of fragments across sources or rungs that the party never stated in one place.
- `agents/evidence_bundle.py` ranks candidate passages with this same ladder on ties; its output is *candidate* evidence. You must read and confirm each quote in the source text yourself.

## 4. Parties with no 2026 platform

Some parties (or parties in flux after a snap election) will not have published a 2026
platform by the coding deadline. Then:

1. Code from the party's **most recent dated policy document** (`type: policy` or `platform`) that speaks to the statement — the highest rung you have, not a downgrade to media by default.
2. **Record the document date.** The source record's `published` field carries it, and the rationale in `data/codings/_coder-notes.json` must restate it ("as of the 2025-04 policy paper …").
3. **Never present an older position as current.** If the document predates the 2026 campaign, confidence is at most `medium` unless a 2026-era source corroborates the same position. Anything surfaced to users from a pre-campaign document must show its date.
4. If a newer 2026-era source contradicts the old document, the newer source wins (§3) and the old one is not cited.
5. If nothing since the party's founding speaks to the statement: `null`.

## 5. Null codes and confidence

**`code` must be `null` — never guessed — when any of these hold:**
- No fetched source states a position on the statement (topical adjacency is not a position).
- The only "evidence" is an opponent's characterization, a headline, or a reporter's paraphrase.
- The statement's instrument is named nowhere; you would be inferring intent from a goal the party shares with the statement (e.g. "help with cost of living" does not code q05 price caps).
- Sources conflict irreconcilably at the same rung and date, and neither supersedes the other.

With `code: null`, `quote`, `source_id`, `source_url`, `archive_url` are all `null` and
`confidence` is `null`. `agents/validate_codings.py` enforces this.

**The low-confidence rule.** `confidence` is `high` / `medium` / `low` and describes how
directly the quote maps to the statement:
- **high** — a platform/policy/release statement of the action itself (same instrument, same scope).
- **medium** — the right position on a related instrument, an older document per §4, or a same-rung conflict resolved by recency.
- **low** — the quote implies the position but the mapping required judgment (adjacent instrument, hedged language, Hansard inference).

A `low` code is legal only when a verbatim quote still exists and its mapping is a matter of
judgment, not invention. **Low confidence never licenses a guess**: if you cannot point at a
real quote, the code is `null`, whatever your priors about the party. Low-confidence rows are
prioritized in the adversarial verification pass and must carry a rationale in
`data/codings/_coder-notes.json`.

## 6. The quote rule

For every non-null code, `quote` is **one verbatim sentence**, and:

- **Copied exactly** from the fetched local source file named by the source's `text_path`
  (e.g. `data/raw/ndp/ndp-0024.txt`) — not from the live web, not from memory, not cleaned up.
  Whitespace-only differences are tolerated by the validator; any wording change is not.
- **One sentence.** No merged fragments, no ellipses, no brackets or `[sic]`, no trimming to
  change meaning. If the position spans sentences, quote the single most probative one.
- **Paired with its `source_id`** from that party's `sources.json`, and the row's
  `source_url` / `archive_url` must match that record exactly.
- It must **actually support the code**. Relevance is not support: a passage about health
  funding does not support a code on private clinics.

Mechanics: `agents/validate_codings.py` checks that each quote occurs verbatim
(whitespace-normalized) in the cited source's text file. A quote that fails verification is
never edited to make it fit — the citation may be **re-pointed** to another trusted source of
the same party containing the same verbatim sentence (logged in
`data/codings/_citation_audit.json`); failing that, the row is quarantined in
`data/codings/_quarantined.json` and excluded from published tables.

## 7. Two-coder independence and disagreement

Every party is coded twice, in parallel, by two coder agents (`<party>-coder-a`,
`<party>-coder-b`).

**Independence.** Coders never see each other's rows, rationales (`_coder-notes.json`), or
conflicts. Each coder works only from the question set and their own evidence bundle, and
writes rows only under their own `coder` id. The schema forbids duplicate
`(coder, question_id)` pairs precisely so the two passes stay separable. A coder who has seen
the other's work is disqualified for that party.

**Detecting disagreement.** After both passes, disagreement is computed mechanically over
matching `(party_slug, question_id)` pairs in `data/codings/_conflicts.json`:
- **code split** — both coded and the codes differ (any spread ≥ 1);
- **null split** — one coder coded and the other returned `null` (a real disagreement about
  whether evidence exists; it counts);
- **agree** — identical codes, including both `null`.

**Resolution ladder.**
1. The conflicting pair goes to a **blind third pass** (adversarial verification): a fresh
   coder who sees neither original rationale, re-codes from the evidence and picks one of the
   two codes or `null`.
2. If the verifier cannot resolve it — or the verifier disagrees with both original coders —
   the row escalates to a **human tie-break** by the editor, whose decision is final. The
   decision is written to `data/codings/_human-decisions.json`, not to `_conflicts.json`
   directly, because the reconcile step regenerates `_conflicts.json` on every run. A
   decision may only adopt a code the row already carries (coder A, coder B or a blind
   pass): any other value would publish a code with no verbatim quote behind it. A decision
   that breaks that rule is ignored and the row stays escalated.
3. Every resolution is **recorded**: both original codes, quotes and source ids stay in
   `data/codings/_conflicts.json` with the verifier's code and, where applicable, the human
   decision (`human_decision`, `human_reason`, `decided_by`, `decided_at`) and the
   `status` the row was published under (`tie-broken` or `human-tie-broken`). The adopted
   row is written to `data/codings/codings.json` with `version` set to the current coding
   version and the rationale in `_coder-notes.json`.

Agreement statistics (`agree` / `disagree` / `both_null` per party) live in
`data/codings/_verification.json` and are published — the reader can see how much of the
table was contested.

## 8. Changed statements invalidate their codes

The questionnaire is a living document (`docs/CONTRIBUTING.md`). When a statement changes —

- the question set's version bumps and the diff is entered in `data/questions/CHANGELOG.md`;
- **every code for that `question_id` is invalidated**: both coders' rows for the changed
  statement are deleted or superseded, not edited in place, and a fresh two-coder pass plus
  verification is run for it before it re-enters any published table;
- quotes and rationales from the old wording are never re-used as evidence for the new
  wording, even if the wording change looks cosmetic — the mapping must be redone;
- unchanged statements keep their codes and version;
- a voter's result is valid only for the question-set version they answered, and the results
  page shows that version.

Removing a statement is the same kind of change: its codes leave the published table (they
may be archived), and the version bumps.

## 9. Record checklist (per row)

Before submitting a coding file, every row must satisfy:

- Exactly the fields in `docs/SCHEMA.md` — no extras, no omissions.
- `code` ∈ {−2, −1, 0, 1, 2, null}; `confidence` ∈ {high, medium, low} (or null with a null code).
- Non-null code ⇒ verbatim one-sentence `quote` + valid `source_id`/`source_url` (+ `archive_url` when the source has one).
- Null code ⇒ `quote: null` and null provenance fields.
- `coder` is your assigned id; `version` is the current coding version; `created_at` is ISO-8601 UTC.
- `python3 agents/validate_codings.py data/codings/<party>.json` passes before commit.

Rationale per row (why this code, and the document date for §4 cases) goes in
`data/codings/_coder-notes.json` — that file is commentary and is not a substitute for the
quote.
