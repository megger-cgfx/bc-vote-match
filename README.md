# BC Vote Match

A neutral, fully-sourced voter alignment tool for the BC 2026 provincial election
(E-day Oct 24, 2026). You answer the same statements the parties have published positions
on; you see where you line up with each party's published positions, with the quote and
source behind every position.

It is an educational comparison tool, not a how-to-vote guide, and it is not affiliated
with Vote Compass or Vox Pop Labs.

## Principles

- **Neutrality lives in the method.** The same coding effort per party, every code backed by
  a public quote, and the full coding table published.
- **Provenance.** Every code carries a quote, a source URL, an archive URL and a hash.
  Nothing unsourced ships.
- **No PII.** No login, no third-party trackers, no stored demographics.
- **The questionnaire is a living document.** Statements are frozen per version, not
  forever. A change bumps the version, is published as a diff, and invalidates the codings
  for that statement until it is recoded. A voter's result is valid only for the version
  they answered.

## Layout

- `src/` — the Next.js site (static export).
- `data/questions/` — the statement set and its versions.
- `data/codings/` — per-party codings, each with quote and source.
- `data/candidates/`, `data/ridings/` — riding-level data.
- `docs/` — the plan, schema, codebook, coding prompt, methodology and content copy.
- `agents/`, `scripts/` — fetch, validate and build tooling.
- `bench/` — the harness used to compare models on the coding task.
- `marketing/` — campaign strategy, design system, copy and assets.

Bulk raw captures are not versioned. Provenance lives in each source record's `sha256` and
archive URL; `scripts/verify-data.py` re-checks the captures you hold locally.

## Working on it

```sh
npm install
npm run dev          # local dev server
npm run build        # static export
npm run typecheck
```

Read `docs/02-PLAN.md` (the plan and gates), `docs/SCHEMA.md` (the data contract) and
`docs/CONTRIBUTING.md` (commit rules, including the sanitization gate) before you change
anything.

Enable the sanitization hook once after cloning:

```sh
git config core.hooksPath .githooks
```

## Licence

MIT.