# OneBC — Recon Inventory (M1)

_Party: OneBC (1BC) · interim leader: Dallas Brodie · registered with Elections BC 2025-06-09_
_Recon note · date 2026-10-01 · contract: docs/SCHEMA.md_
_Inventory file: `data/raw/onebc/sources.json` (19 records, all sha256-verified)._

## Where OneBC publishes

| Site | Role |
|---|---|
| `https://1bc.ca/` | **Official party site** (Framer build). Platform plan at `/priorities`; party constitution at `/constitution` (+ downloadable PDF); leadership/candidates/petitions pages. |
| `https://ivoteonebc.ca/` | **Independent supporter site** — self-labeled *"Not authorized by, affiliated with, or funded by OneBC or Dallas Brodie."* Summarizes the official plan. Type recorded as `media`, **not** `platform`. |
| `leg.bc.ca` / `lims.leg.bc.ca` | Legislature Hansard — Brodie's floor record. |

`parties.json` had OneBC `url: ""` with the note "verify platform URL" — **resolved: `https://1bc.ca`** (also mirrored at `ivoteonebc.ca`, unofficial).

## Inventory (19 sources in `data/raw/onebc/sources.json`)

Official — platform / policy (highest coding priority):
- `onebc-0001` **platform** — `/priorities`: the numbered platform plan (~38 planks / 11 sections: Reconciliation, Economy & Public Finance, Forestry, Generational Debt, Healthcare, Education, Housing, Drugs & Addiction, Firearms Owners, Crime & Justice, Interprovincial Relations).
- `onebc-0002` **platform** — home page (mission + issue one-liners).
- `onebc-0003` **policy** — `/constitution` page.
- `onebc-0004` **policy** — party **constitution PDF** (principles: rule of law, private property, low tax/spend/regulation, family, free speech, BC resource ownership). Text extracted via `pdftotext`.

Official — other pages:
- `onebc-0005` leadership (Brodie bio) · `onebc-0006` 2026 candidates · `onebc-0007` petitions (issue positions, dated 2025–26).

Legislative record (`hansard`):
- `onebc-0008` 2025-10-28 · `onebc-0009` 2025-10-30 · `onebc-0010` 2026-03-12 · `onebc-0011` 2026-04-23 (Brodie on repealing DRIPA).

Media:
- `onebc-0012` Surrey Now-Leader (MLA Chapman leaves BC Conservatives for OneBC) · `onebc-0013` Castanet (candidate in Armstrong's former riding) · `onebc-0014` Times Colonist/Canadian Press (no official party status) · `onebc-0015` CTV News (won't run against eight BC Conservative candidates) · `onebc-0016` Fraser Valley News Network (no candidate in Fraser Valley by-election) · `onebc-0017` Epoch Times.

Other:
- `onebc-0018` Wikipedia (history, Elections BC registration) · `onebc-0019` iVoteOneBC.ca `/policies` (independent summary; claims the official page held 53 planks / 12 categories as of June 2026 — treat as cross-check only, code from `onebc-0001`).

## Grounded positions (verbatim, for M3 coders)

From `onebc-0001` (platform plan):
- "Repeal DRIPA and declare UNDRIP to have no force and effect in BC"
- "25% tax cuts for every single tax bracket — including corporate"
- "2% off the Provincial Sales Tax (PST)"
- "Private Healthcare alongside fully-funded public healthcare"
- "Remove SOGI-123 and politicized content from classrooms"
- "Eliminate safe supply and drug consumption programs"
- "Eliminate the Step Code that is raising housing costs with unnecessary green building requirements"

From `onebc-0004` (constitution PDF, Party Principles §3):
- "low levels of taxation, spending, and regulation"
- "Defending the ownership rights of British Columbia to utilize its natural resources for the benefit of British Columbians for generations to come."

## Gaps / caveats

- **No `release` and no `speech` source.** The June 12 2025 founding press release (referenced by Wikipedia) was not captured; Brodie's speeches live on X/Facebook/video and are not clean-text fetchable here. Wikipedia (`onebc-0018`) carries a summary of the founding policy set.
- **Wayback gaps.** `archive_url` is present for most records; still null for `onebc-0009`, `onebc-0013`, `onebc-0017`, `onebc-0019` (Wayback `/save` returned 520/connection-refused under load). Local raw bytes + sha256 are captured for all 19 — that is the primary evidence; re-run the archive step later to fill the nulls.
- Platform plank count differs between snapshots: `onebc-0001` shows ~38 numbered planks, while the independent site cites 53 — the official page is the authority.

## Coordination note (orchestrator: please read)

**Two independent OneBC recon agents ran at once and raced on `data/raw/onebc/`:** two concurrent recon workers (goal: "source inventory for the OneBC party"). Both used id allocation (`<party>-NNNN`) that is **not collision-safe under concurrency**, so for a period the directory held a duplicate-id `sources.json`, clobbered files, and orphaned copies (repeated id `onebc-0013`). The two were reconciled into the single 19-record file that now exists, verified (unique ids/urls, every `local_path` sha256 matches the record). **Recommendation:** the two recon approaches are duplicate work — run one, not both, and serialize per-party-directory writes.
