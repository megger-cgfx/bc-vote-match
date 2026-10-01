# AGENTS.md — read me first if you are an agent working in this repo

BC Vote Match: a neutral, fully-sourced voter alignment tool for the BC 2026 provincial election (E-day Oct 24, 2026).

## Before you do anything
- Read `docs/02-PLAN.md` (the plan and gates) and `docs/SCHEMA.md` (the data contract).
- If your task touches codings, read `docs/CODEBOOK.md` and `docs/CODING-PROMPT.md`.
- Stay inside your assigned file scope. Other agents are working at the same time.
- `marketing/` belongs to the marketing director agent. Do not edit it. `data/` and `src/` are shared, so take a disjoint sub-scope and say so in your report.

## Commit your work
Versioning is part of the job, not an afterthought. See `docs/CONTRIBUTING.md` for the full rule set.

- Commit after each logical change, not one dump at the end.
- Message: `<scope>: <what changed>`, scope in {data/questions, data/codings, data/raw, data/candidates, src, agents, scripts, docs}. Sign the body with `Agent: <your id>`.
- Never commit secrets, `node_modules/`, `.next/`, `out/`, or the bulk files under `data/raw/` — they are gitignored. Do not force-add them.
- Run `python3 scripts/verify-data.py` before committing anything under `data/raw/`.
- No force-push, no history rewriting.

## Do not exceed your brief
If your task is source gathering, do not code party positions. If your task is building the site, do not edit the data. Premature work that is later invalidated costs more than it saves. If you believe extra work is needed, say so in your report instead of doing it.
