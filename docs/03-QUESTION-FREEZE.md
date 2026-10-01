# BC Vote Match — M2 Question Freeze (gate)

**Status: APPLIED 2026-10-01 by card `<task-id>` — the 18 below are the live set.**
Prepared 2026-10-01 · gate card `<task-id>` · source pool `<task-id>` · applied by `<task-id>`

`data/questions/questions.json` now holds exactly these 18 rows with `status: "frozen"`,
carrying the statement text listed below. That is the text this packet was signed off on
and the text the live codings in `data/codings/<party>.json` were coded against;
`docs/CODING-PROMPT.md` requires the published statement to be the one the coder read.
The 54-item pool is retired to `data/questions/pool/` — `questions.v1.all54.json` (this
wording) and `questions.v2.all54.json` (the later 54-statement rewrite). `src/lib/data.ts`
no longer finds a `questions.v2.json` to prefer, so the site renders the 18.

Frozen set hash: `sha256(data/questions/questions.json)` =
`41bfdc5f7cffe609ed001eb0b41a7882dcaf36680eb4b4a00342512324b7d84e` (2026-10-01).
Regenerate with `python3 scripts/apply-question-freeze.py` (idempotent).

**Open question left for Martin (not a blocker for the gate).** The v2 rewrite supersedes
the wording below in `data/questions/v2/` + `questions.v2.all54.json`. It was *not* applied,
because the coders coded the wording below and the rewrite is a re-code under
`docs/CODING-PROMPT.md` §"If a statement's wording changes …". Adopting v2 wording is a
recoding pass (`<task-id>` / `<task-id>`), not a file swap.

## What I needed from you (resolved)

Martin approved this selection (`<task-id>`, "approve freeze") and it was applied to
`data/questions/questions.json` on 2026-10-01 by card `<task-id>`. The original ask was:

One line back, either:
- **"approve freeze"** — I copy the proposal to `data/questions/questions.json` (status `frozen`), hash it, and release the M3 coding cards; or
- **swaps**, e.g. `q26→q27, drop q38` — I re-cut and re-propose. Every statement's alternates are listed below.

## The proposed 18 (3 per topic, 6 topics)

Every item is phrased as a single proposition, answerable on the 5-point Likert
(strongly disagree … strongly agree) plus "don't know", and coded −2…+2 per party.

### Cost of living & taxes
| id | statement | dim |
|---|---|---|
| q01 | The province should reinstate and raise the consumer carbon tax to cut emissions, even if it increases the cost of fuel. | economic |
| q03 | The province should introduce a wealth tax on the highest earners to fund public services. | economic |
| q04 | BC should balance its budget even in uncertain economic times, cutting spending to get there. | economic |

*Why:* q01 is the single sharpest 2026 cleavage (NDP scrapped the consumer tax, Greens want a rising
price, Conservatives/OneBC oppose outright) — it separates the NDP from its own 2024 base. q04 is the
deficit fight, a top-3 issue for Conservative voters and near-zero for NDP voters. q03 is the clean
redistribution test. Alternates: q02 (tax cuts vs services), q07 (shrink the public service), q08 (targeted rebates).

### Housing
| id | statement | dim |
|---|---|---|
| q10 | The province should override municipal zoning rules to force more density near transit stations. | economic, social |
| q11 | Rent controls should be strengthened and extended to more units. | economic |
| q18 | Supportive and social housing should be expanded even in neighbourhoods that object. | social |

*Why:* q10 is the NDP's signature intervention and tests provincial power over local planning; q11 is the
renter/supply split; q18 is the NIMBY test and carries the housing file's social load. Alternates: q15
(municipal final say), q12 (government builds and owns), q13 (vacant/speculator tax).

### Health
| id | statement | dim |
|---|---|---|
| q19 | BC should expand private, for-profit clinics to reduce health-care wait times. | economic |
| q22 | The province should fund more supervised consumption sites and safer-supply programs. | social |
| q26 | The province should impose minimum nurse-to-patient ratios in hospitals. | economic |

*Why:* q23 (pure single-payer) is the "should we even argue about this" version of q19; q19 is the
concrete policy and the sharpest divide. q22 carries harm reduction (a values line, not a cost line),
q26 adds a staffing/cost question that splits the centre from both flanks. Alternates: q27 (private
diagnostics), q23 (single-payer anchor), q25 (overdose sites over local objection).

### Climate & environment
| id | statement | dim |
|---|---|---|
| q28 | BC should approve new liquefied natural gas (LNG) projects to grow the export economy. | economic |
| q29 | The province should stop logging old-growth forests. | social, economic |
| q31 | The province should invest in public transit and rail rather than expanding highways. | economic |

*Why:* q28 is the best NDP-vs-Greens wedge on the board (and tests the NDP's resource record). q29 is
the forest file, q31 is the clearest spending-direction split. Deliberately no second carbon-pricing
item: q01 already carries that axis, and q32 would double-count it. Alternates: q30 (oil-and-gas
emission cuts), q35 (fast-track mining approvals), q34 (EV mandate).

### Indigenous reconciliation
| id | statement | dim |
|---|---|---|
| q37 | BC should fully implement the Declaration on the Rights of Indigenous Peoples Act (DRIPA). | social |
| q38 | DRIPA should be amended to make clear that Indigenous nations do not have veto power over resource projects. | economic, social |
| q39 | The province should share resource revenue with First Nations whose territories host the projects. | economic |

*Why:* DRIPA is the defining flashpoint of this campaign — q37 is the values anchor, q38 is the live
amendment fight (Eby has floated changes to his own law; it splits the NDP base), q39 puts money and
territory on the table. Alternates: q42 (decisive role in land-use decisions), q40 (title affirmed in
provincial law), q44 (accelerate treaty negotiations).

### Public safety
| id | statement | dim |
|---|---|---|
| q46 | Public drug use should be illegal and the decriminalization pilot should not be revived. | social |
| q47 | Bail should be made tougher for repeat violent offenders. | social |
| q48 | The province should expand involuntary care for people with severe addiction and mental illness. | social |

*Why:* these are the three live 2026 fights (Eby already ended the decriminalization pilot and moved on
bail and involuntary care, so all three cut across left–right rather than along it). Alternates: q50
(scale back safer supply), q49 (police funding), q53 (court-ordered treatment).

## Balance check (computed, not eyeballed)

- 18 questions, exactly 3 per topic.
- Dimension loadings: **12 economic, 9 social** (5 items count on both axes). That supports a 2-D
  compass whose x-axis rests on 12 statements and y-axis on 9 — thin but workable; if you want a fatter
  social axis, the swap that helps most is q26→q25 (health) and q04→q05 (cost of living).
- Party-differentiation: every selected item is flagged by the pool as a split between at least two
  parties. The three pool items explicitly marked *consensus / low differentiation* were dropped:
  q41 (Indigenous child and family services), q45 (Indigenous languages), q54 (youth crime prevention).
- No mirrored pairs: pairs that state the same axis in reverse were cut to one side (q19 over q23,
  q10 over q15, q38 over q42).

## Board note (needs the orchestrator's attention)

- The M2 card was created with `parents: []`, so it has **no dependency edge** to the question-pool card
  `<task-id>` — M2 and the pool were dispatched in parallel. At run start the pool had not written yet;
  it landed mid-run, so this proposal was cut from the completed 54-item pool.
- Likewise, the M3 coding cards (`<task-id>`, `<task-id>`) were created with no parent. I have linked
  both as children of this gate so coders cannot start on an unfrozen set; they auto-promote when this
  gate is approved and completed.
- The M5 integration card (`<task-id>`) should depend on the M3 verification card (`<task-id>`), and
  the M3 pair should also depend on the M1 recon cards. Not done here — orchestrator call.

## After approval (what I do, no further input needed)

1. Copy `freeze-proposal.json` → `data/questions/questions.json`, status `frozen`, hash the file, commit.
2. Record the frozen ids in the M3 cards' handoff metadata.
3. Release `<task-id>` (code 5 parties, 2 coders each) and let `<task-id>` (adversarial verification) follow.
