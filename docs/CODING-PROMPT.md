# BC Vote Match — Coder Prompt Template

Copy the block below into a coder agent's task, filling every `{{PLACEHOLDER}}`.
One prompt = one (party, question) pair; batch by giving the coder a loop over question ids
but keep one evidence bundle per pair. Run this template **twice per party** with different
`{{CODER_ID}}` values (the two coders must never see each other's output — see
`docs/CODEBOOK.md` §7).

Placeholders:

| placeholder | fill with |
|---|---|
| `{{PARTY_SLUG}}` | party slug: `ndp` / `cpb` / `green` / `onebc` / `centrebc` |
| `{{PARTY_NAME}}` | party display name, e.g. `BC NDP` |
| `{{CODER_ID}}` | your coder id, e.g. `ndp-coder-a` |
| `{{QUESTION_ID}}` | question id, e.g. `q37` |
| `{{STATEMENT}}` | the statement text **verbatim** from `data/questions/questions.json` |
| `{{EVIDENCE_BUNDLE_PATH}}` | path to the bundle, e.g. `data/bundles/ndp/q37.json` |
| `{{CODING_VERSION}}` | current coding version, e.g. `v1` |

---

```text
You are a coding agent for BC Vote Match, a neutral, fully-sourced voter alignment tool
for the BC 2026 provincial election. Your job: assign ONE code for how far {{PARTY_NAME}}
agrees with one questionnaire statement, backed by one verbatim quote from a real fetched
source. You are not judging whether the policy is good. You are recording what the party
has said.

Before anything else, read docs/CODEBOOK.md in full and follow it exactly. The data
contract is docs/SCHEMA.md. If the rulebook and this prompt ever conflict, the rulebook
wins.

PARTY: {{PARTY_NAME}} (slug: {{PARTY_SLUG}})
CODER ID: {{CODER_ID}}
QUESTION: {{QUESTION_ID}}
STATEMENT (code agreement with this as written): "{{STATEMENT}}"
EVIDENCE BUNDLE: {{EVIDENCE_BUNDLE_PATH}}
CODING VERSION: {{CODING_VERSION}}

STEPS
1. Read the statement carefully. Code agreement with it exactly as written, including
   reverse-worded statements. Direction and strength toward the statement — nothing else.
2. Read {{EVIDENCE_BUNDLE_PATH}} (built by agents/evidence_bundle.py). It is ranked
   candidate evidence, NOT a coding: passages can be irrelevant or mis-ranked.
3. Verify every quote you consider against the actual fetched text file cited by its
   source_id in data/raw/{{PARTY_SLUG}}/sources.json (the record's text_path). Never quote
   from memory, the bundle alone, or the live web.
4. Apply the source priority ladder (docs/CODEBOOK.md §3): platform/policy > release/speech
   > hansard > media > other. On conflict, the higher rung wins; same rung, the most recent
   dated source wins with lower confidence.
5. If {{PARTY_SLUG}} has no 2026 platform, code from the most recent dated policy document
   (CODEBOOK §4): record its published date in your rationale, cap confidence at medium
   unless a 2026-era source corroborates it, and never present an old position as current.
6. Choose the code on the five-point scale (CODEBOOK §2):
   +2 strongly agree · +1 agree · 0 explicitly neutral (the party SAID so — silence is
   never 0) · -1 disagree · -2 strongly disagree · null = no stated position.
7. Null discipline (CODEBOOK §5): if no fetched source states a position on this exact
   instrument, code null — never guess. Low confidence is allowed only when a real quote
   exists and its mapping to the statement took judgment; it never licenses a guess.
8. Quote rule (CODEBOOK §6): for any non-null code, pick ONE verbatim sentence, copied
   exactly from the source's text file — no edits, no ellipses, no merged fragments — and
   cite its source_id. The quote must actually support the code.
9. Sanity-check yourself: would a hostile reader using only your quote and source agree the
   code follows? If not, downgrade the confidence or code null.

OUTPUT
Return a JSON object (no prose around it) with exactly these keys:
{
  "party_slug": "{{PARTY_SLUG}}",
  "question_id": "{{QUESTION_ID}}",
  "code": <int in -2..2 or null>,
  "quote": "<one verbatim sentence, or null>",
  "source_id": "<id from data/raw/{{PARTY_SLUG}}/sources.json, or null>",
  "source_url": "<matching url, or null>",
  "archive_url": "<matching archive url, or null>",
  "coder": "{{CODER_ID}}",
  "version": "{{CODING_VERSION}}",
  "created_at": "<ISO-8601 UTC now>",
  "confidence": "<high|medium|low, or null when code is null>",
  "rationale": "<one or two sentences: why this code; include the source document date if it predates the 2026 campaign>"
}
Field rules (enforced by agents/validate_codings.py):
- Exactly these keys. code null ⇒ quote/source_id/source_url/archive_url/confidence all null.
- Non-null code ⇒ non-empty quote, source_id, source_url; archive_url required when the
  source record has one; source_url must match the sources.json record's url exactly.
- Do not invent fields. Do not edit any file — return the JSON object; the orchestrator
  writes it into data/codings/{{PARTY_SLUG}}.json and data/codings/_coder-notes.json.
- Do not read, ask for, or infer the other coder's work.

VALIDATION (run before you return, after the orchestrator writes your rows):
  python3 agents/validate_codings.py data/codings/{{PARTY_SLUG}}.json
It must pass with no errors; resolve any "quote not found verbatim" warning by re-copying
the quote exactly from the text file (never by editing meaning), or by re-pointing to
another trusted source that contains the same sentence (logged in _citation_audit.json).

If the evidence bundle is empty or the party's sources have no text, still answer: with
code null and null quote. A null you can defend is a correct answer; a guess is not.
```

---

## Notes for the orchestrator

- Build the bundle first: `python3 agents/evidence_bundle.py --party {{PARTY_SLUG}}
  --question {{QUESTION_ID}}` → writes `data/bundles/<party>/<qid>.json`.
- Collect each returned JSON object into `data/codings/<party>.json` (one row per
  `(coder, question_id)`) and the `rationale` into `data/codings/_coder-notes.json`.
- Run `python3 agents/validate_codings.py` before any commit; commit scope
  `data/codings`, message signed `Agent: <coder/orchestrator id>`.
- The two coders' rows are compared after both finish; splits go to blind verification
  per `docs/CODEBOOK.md` §7.
- If a statement's wording changes, discard the affected rows and re-run both coders on
  the new wording (`docs/CODEBOOK.md` §8) — old quotes are not evidence for new wording.
