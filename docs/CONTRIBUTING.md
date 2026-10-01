# Contributing and versioning discipline

Repo: https://github.com/megger-cgfx/bc-vote-match (branch `main`)

## Auth
Credentials live outside the repo and are exported into the environment when needed. **Never write a token, key, or credential path into any file inside this repo, and never into a commit message.**

## Rules for every agent that writes files
1. **Commit after each logical change.** One change per commit, not one giant dump at the end of a run.
2. **Message format:** `<scope>: <what changed>`, where scope is one of
   `data/questions`, `data/codings`, `data/raw`, `data/candidates`, `src`, `agents`, `scripts`, `docs`, `marketing`.
   Example: `data/codings: code BC NDP on frozen q-set v1`.
3. **Sign your work.** End the commit body with `Agent: <your name or subagent id>`.
4. **Never commit** secrets, `node_modules/`, `.venv/`, `attic/`, `.next/`, `out/`, bulk
   `data/raw/` captures, or benchmark run artifacts (models, runtimes, eval sets). All are
   gitignored — do not force-add them.
5. **Never commit local-machine or operational context.** No absolute home paths
   (`/home/<user>/...`, `/Users/<user>/...`, or the equivalent Windows form), no paths into
   the agent runtime or its task board, no credential-store locations, no live hostnames,
   SSH endpoints or instance ids, no task/delegation ids. Write paths relative to the repo
   root. `scripts/sanitize-check.py` enforces this and runs as a pre-commit hook and in CI;
   run it yourself before you commit. In a fresh clone, enable the hook once with
   `git config core.hooksPath .githooks`.
6. **Data integrity first.** Before committing anything under `data/raw/`, run `python3 scripts/verify-data.py` and make sure it exits clean.
7. **Do not rewrite history.** No force-push, no rebase of `main`. If `main` has moved, pull and re-apply.

## What belongs in this repo
Code, data, documentation, design records and plans. Not the operations layer: no briefs to
workers, no status or interface notes, no post-compaction recovery docs, no environment
captures. If a document only makes sense to the people running the project, it belongs in
the internal repo, not here.

## Versioning the questionnaire (it is a living document)
The campaign moves. The statement set is frozen per version, not forever.

- The question set carries a version. Freezes are tagged: `q-v1`, `q-v2`, and so on.
- Any change to a statement (wording or inclusion) **bumps the version** and gets an entry in `data/questions/CHANGELOG.md` describing the diff and the reason.
- **A changed statement invalidates its codings.** Recoding is required before results that include it are republished.
- A voter's result is only valid for the version they actually answered; the results page should show that version.
- Same discipline for codings: `data/codings/<party>.json` records carry a `version`, and coding freezes are tagged `codings-v1`, `codings-v2`.

## Tags that mark milestones
`q-v1` (18 frozen) → `codings-v1` (coding verified) → `site-v1` (public launch).
