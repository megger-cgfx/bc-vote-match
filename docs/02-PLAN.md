# BC Vote Match — Plan & Orchestration
_Started 2026-10-01 · owner: Martin (editor/operator) · orchestrator: flower_

## Goal
Ship a **neutral, sourced, party-level voter alignment tool** for the BC 2026 snap election (E-day **Oct 24, 2026**). Open source, self-hosted, public contributions reviewed. Then riding-level. A separate outreach/comms campaign (visuals via ComfyUI on vast.ai, influencer + media) runs later, under this project.

## Non-negotiables
1. **Neutrality lives in the method.** Same coding effort per party, every code backed by a public quote, the full coding table published. Outreach copy never says "party X is wrong," only "here's where you sit."
2. **Provenance.** Every code carries a quote + source URL + archive URL + hash. Nothing unsourced ships.
3. **No PII.** No login, no third-party trackers, no demographics stored.
4. **Disclaimers.** Educational tool, not how-to-vote; independent, not affiliated with Vote Compass / Vox Pop Labs.
5. **The questionnaire is a living document.** The campaign moves, so the set can change: statements are frozen per version, not forever; a change bumps the version and is published as a diff; a changed statement invalidates its codings and forces a recode; a voter's result is valid only for the version they answered. Pool is 54, shortlist 18, all still `candidate`.

## Milestones
- **M0 Setup** — Oct 1: board, repo, schema, decisions locked. ✅ this turn
- **M1 Sources** — Oct 2: per-party source inventory, archived + hashed.
- **M2 Questions** — Oct 3: 18 statements frozen. **[human gate]**
- **M3 Codings** — Oct 5: 5 parties coded (2 independent coders + blind verifier). **[human gate]**
- **M4 Site** — Oct 6: static build green, content wired, share cards working.
- **M5 Launch** — soft link Oct 5, **public Oct 8**.
- **M6 Rides** — Oct 14: riding-level v1.1 before advance voting (Oct 16–21).
- **M7 Recodes** — Oct 12 + Oct 20: versioned diffs, published.

## Orchestration layers
- **L0 Orchestrator** — me (flower): plans, dispatches, holds the gates.
- **L1 Recon** — 5 party-source agents (one per party) + 1 question-pool agent.
- **L2 Coding** — 2 independent coder agents per party; each proposes a code + quote per question.
- **L3 Adversarial verification** — blind re-code per party; conflicts escalate to a human tie-break.
- **L4 Build** — scaffold, data pipeline, UI, share cards, accessibility.
- **L5 Integration & launch** — assemble, QA, publish **[human gate]**.

Concurrency: `delegation.max_concurrent_children = 30`, `delegation.max_spawn_depth = 2`.

## Delegation topology (updated Oct 1)
With depth 2 the tree is three levels deep:
- **L0 Orchestrator** — me (flower): owns the plan, the human gates, and cross-stream sequencing.
- **L1 Stream leads** (orchestrator role) — one per workstream: Sources, Questions, Coding, Verification, Build, Riding, Outreach. Each decomposes its stream and fans out to its own workers.
- **L2 Workers** (leaf) — fetch, code, build, check. Up to 30 running at once across the tree.

Practical effect: a stream lead can run a whole pipeline (recon, code, self-check) without returning to me at every step, so streams progress in parallel rather than in my serial waves. I keep the two human gates (freeze the 18, publish) and the cross-stream merge. Each writer still gets a disjoint file scope, to avoid the mid-run collisions we saw in wave 1.

Verified Oct 1: a probe subagent spawned its own worker successfully (grandchild returned PONG in about 10 seconds), so depth 2 is live, not just configured. Grandchildren are leaves and cannot delegate further, so the tree bottoms out at three levels.

## Repository & versioning
- Remote: https://github.com/megger-cgfx/bc-vote-match, branch `main`. Token and credential store live outside the repo under `<secret-store>/`.
- Every agent that writes files commits its own work, scoped and signed, per `docs/CONTRIBUTING.md`; the short version is in the repo-root `AGENTS.md`.
- Milestone tags: `q-v1` (18 frozen) → `codings-v1` (coding verified) → `site-v1` (launch).
- Bulk raw captures (html, txt, pdf under `data/raw/`) are not committed; provenance is carried by `sources.json` hashes plus archive URLs. Switch to Git LFS if we decide we want the raw files in-repo.

## Status note (Oct 1, 01:24)
An agent ran ahead of its brief and produced a full coding pass: 180 rows (5 parties × 18 questions × 2 coders), with coder notes, 22 logged splits and a citation audit, committed as `v0.9-prefreeze` against the **proposed** 18. Treat it as a head start, not as the verified M3. It must be reconciled against the frozen question set and the codebook before it counts.

## State on disk
```
data/parties.json          # the 5 parties
data/raw/<party>/          # fetched HTML/text + sources.json
data/archive/              # archived copies + MANIFEST.json (sha256)
data/questions/questions.json
data/codings/<party>.json
data/candidates/*.json     # riding phase
docs/SCHEMA.md             # the contract every agent follows
```

## Wave 1 (dispatching now)
1. **L1 × 5** — party source hunt: NDP, Conservative, Green, OneBC, CentreBC → inventory + archive + hash.
2. **L1 × 1** — question pool (~45–60 candidate statements, 6 topics / 2 dimensions).
3. **L4 × 1** — Next.js static scaffold that builds green against the schema.

## Risks
- 23 days to E-day; party churn and interim leaders make codings a moving target → version everything.
- Scraped platform pages vanish mid-campaign → archive + hash is not optional.
- Credibility is the whole product: any asymmetry in coding effort kills it.
- Scope creep: riding-level is a fast-follow, not v1.
