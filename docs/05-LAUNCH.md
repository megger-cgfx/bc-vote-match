# BCVM M5 — Public launch (human gate)

**Status: NOT READY. The gate is executable as one command and says NO-GO (5 blockers).**
Gate card `<task-id>` · prepared 2026-10-01 by flower · plan: soft link Oct 5, public Oct 8
Launch command card `<task-id>` · current snapshot in §9

This is the last gate before the site is on the public internet under
`bcvotematch.ca`. It has two halves: a mechanical half that a script decides, and
a judgement half that Martin decides. Neither half is optional.

## Operator checklist (launch day)

One-time setup (never committed — the token lives in the operator secret store
under `<secret-store>/`, exported only for the deploy):

    export CLOUDFLARE_API_TOKEN=...   # Cloudflare API token, scope Account / Cloudflare Pages: Edit
    export CLOUDFLARE_ACCOUNT_ID=...  # the Cloudflare account id

Launch, in order:

1. **Preflight.** `bash scripts/launch.sh` — verify, self-test, typecheck, full
   build, the gate (23 checks), and package `dist/bcvm-<sha>.zip`. It stops short
   of publishing and prints GO or the blockers. `python3
   scripts/launch-preflight.py` runs just the gate (data checks + full build +
   output checks); add `--no-build` to judge an existing `out/`.
2. **Deploy.** `bash scripts/deploy-pages.sh` — refuses unless the gate passes,
   then uploads `out/` to Cloudflare Pages. (The full path with live verification
   is `bash scripts/launch.sh --publish`.)
3. **Post-deploy smoke check.**
   `bash scripts/launch.sh --verify-live https://bcvotematch.ca` — fetches the
   live site and compares every file to `out/` byte for byte. Then by hand:
   `curl -sI https://bcvotematch.ca/` shows 200, `/questions/`, `/results/`,
   `/coding-table/` load, the disclaimer and the share card render.
4. **Tag the launch.** `git tag -a site-v1 -m "public launch" <sha>` and push the
   tag (`git push origin site-v1`) — the tag is the rollback pointer.

**Roll back** (tag + redeploy of the previous build): `git checkout
<previous-tag>` (e.g. `q-v1`, or the previous `site-*` tag), then `npm ci &&
npm run build && bash scripts/deploy-pages.sh` — that redeploys the previous
commit's export over the bad one. Verify with
`bash scripts/launch.sh --verify-live https://bcvotematch.ca`. Nothing else is
needed: the site is a static export, so the previous build fully replaces the
new one. Tag every deploy (`git tag -a site-YYYYMMDD-1 ...`) so "the previous
build" is always one `git checkout` away.

### Cloudflare Pages deploy configuration

| setting | value |
|---|---|
| build command | `npm run build` (Next.js static export) |
| output directory | `out/` |
| deploy command | `bash scripts/deploy-pages.sh` → `npx --yes wrangler@4 pages deploy out --project-name=bc-vote-match --branch=main` |
| project name | `bc-vote-match` (override: `BCVM_PAGES_PROJECT`) |
| authentication | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` from the environment at deploy time — **no token is ever committed to this repo** |

Plain wrangler direct upload; no wrangler.toml is needed (project name and
branch are CLI flags). The API token is created at
dash.cloudflare.com/profile/api-tokens with scope *Account / Cloudflare Pages /
Edit*, stored in the operator secret store, and exported only for the deploy
command. To use any other deploy path instead, set `BCVM_DEPLOY_CMD` (see §0).

## 0. The launch is one command (2026-10-01)

    bash scripts/launch.sh              # verify + build + package; stops short of publishing
    bash scripts/launch.sh --publish    # ... and publish (asks you to type "publish")
    bash scripts/launch.sh --check      # verify the existing out/ only, no build
    bash scripts/launch.sh --verify-live https://bcvotematch.ca   # check what is actually live

`npm run launch` is the same command. The logic is `scripts/launch.py`;
`scripts/launch.sh` is the entry point and does nothing but find a python3.

What it does, in order:

1. environment: repo layout, python3/node/npm, `git rev-parse` for the artifact tag;
2. `scripts/test-launch-preflight.py` — the gate's own self-test (21 cases);
3. `npm run typecheck` (`tsc --noEmit`);
4. `npm run build` — Next static export into `out/`;
5. `scripts/launch-preflight.py --strict --online --json --no-build` — the 23-check gate (the launcher builds in step 4 and the gate judges that `out/`);
6. package `dist/bcvm-<sha>[-dirty].zip` plus `dist/MANIFEST.json` (per-file
   sha256, the gate verdict, dataset counts, and a copy of the manifest inside
   the archive);
7. with `--publish`: deploy, then fetch the published site and compare it to
   `out/` byte for byte.

Exit codes: **0** GO and done · **1** NO-GO (gate failed; nothing was built,
packaged or published) · **2** GO but a human step is left (confirmation, or no
credentials) · **3** could not run · **4** deploy failed · **5** deployed but the
live site does not match the build.

Rails, so a launch cannot happen by accident:

- nothing is packaged or deployed unless the gate says GO;
- `--publish` needs the word `publish` typed at the prompt (the prompt defaults
  to no) or `--yes`;
- publishing needs a credential or a command this repo does not hold, because
  the accounts are Martin's — either `CLOUDFLARE_API_TOKEN` +
  `CLOUDFLARE_ACCOUNT_ID`, or `BCVM_DEPLOY_CMD` set to any command that copies
  `$OUT` somewhere (`$OUT`, `$ROOT` and `$ARTIFACT` are exported to it);
- a deploy is not trusted until the live URL is fetched and its bytes match
  `out/`.

Cloudflare Pages, once a token exists:

    export CLOUDFLARE_API_TOKEN=...       # Pages: Edit
    export CLOUDFLARE_ACCOUNT_ID=...
    export BCVM_PAGES_PROJECT=bc-vote-match
    bash scripts/launch.sh --publish --yes

Wrangler 4.146.0 runs through `npx --yes` (verified 2026-10-01), so no repo
install is needed. Before the custom domain is live, verify the preview instead:
`bash scripts/launch.sh --publish --verify-at https://bc-vote-match.pages.dev`.

The launcher has its own self-test: `python3 scripts/test-launch.py`. Eleven
cases, no network and no real host touched: a complete dataset says GO; an
unfrozen set, an unarchived source and a missing route each stop it; packaging
produces an artifact whose manifest matches the zip; publishing with no
credentials stops with the missing variable named; a stub deploy target receives
the export and the live check passes; a tampered deploy is caught as exit 5; the
launcher runs the gate self-test; a non-repo root is refused.

## 1. The mechanical half is now executable

    python3 scripts/launch-preflight.py             # data checks + full build + gate
    python3 scripts/launch-preflight.py --no-build  # judge the existing out/ (no build)
    python3 scripts/launch-preflight.py --online    # + is the domain actually registered?
    python3 scripts/launch-preflight.py --strict    # warnings become failures too
    python3 scripts/launch-preflight.py --json      # machine-readable report

It is read-only over `data/`, `src/` and `out/`; the one side effect is the build
step (`npm run build`), which `--no-build` skips.

Exit codes: **0 GO** (no failures), **1 NO-GO** (at least one FAIL), **2 NO-GO under
`--strict`** (warnings only), **3 could not run**.

The rule the script enforces is the one the whole product rests on: *nothing goes
public that is placeholder, unsourced, or missing its provenance*. A FAIL is not a
style opinion. It means publishing would put a fabricated or uncited party position
in front of voters.

### What it checks

| # | check | why it blocks a launch |
|---|---|---|
| 1 | `scripts/verify-data.py` exits 0 | data integrity: every stored capture exists and hash-matches its `sources.json` record |
| 2 | `agents/validate_codings.py` exits 0 over `data/codings/v1/` + the published `data/codings/codings.json` | coder rows must satisfy the coding contract (code -2..2 or null, quote + source when coded) |
| 3 | the published table has no unresolved splits | a split row means two coders disagreed and no tie-break landed — never publish a guessed code |
| 4 | the published table has no fixture references | placeholder rows must be unable to ship |
| 5 | `npm run build` exits 0 (the build step; `--no-build` skips it) | the export that ships must build clean from this tree |
| 6 | `scripts/validate-dataset.py` exits 0 | per-code provenance: every non-null code carries a verbatim quote that really is in the source it cites |
| 7 | `data/parties.json` covers all 5 parties | a missing slug means a party silently absent from every table |
| 8 | the live question set is `status: "frozen"` | the site must not render an unfrozen statement |
| 9 | a coding file exists for every party | asymmetry starts as a missing file |
| 10 | coding coverage is complete | one row per party per frozen question, no silent gaps |
| 11 | every source has an `archive_url` | scraped platform pages vanish mid-campaign; the plan calls archive+hash non-optional |
| 12 | every source has a real `sha256` | a zeroed hash is a plumbing error, not a hash |
| 13 | the export contains every route | a missing `/coding-table/` page would hide the neutrality evidence |
| 14 | the export is newer than the dataset | publishing a stale build ships positions the coders already corrected |
| 15 | no placeholder content in the build | catches `PLACEHOLDER DATA`, `example.invalid`, `v0-fixture`, fixture coders |
| 16 | no third-party trackers or analytics | non-negotiable #3 (no PII, no trackers) |
| 17 | no external script/style origins | fully self-contained static export |
| 18 | no PII collection paths | no `document.cookie` writes, no `sendBeacon`, no external form posts |
| 19 | disclaimers rendered on every page | independence + how-to-vote + privacy copy must not be strippable |
| 20 | open graph share card present | the first impression on every share is the card, not the page |
| 21 | sitemap lists the published origin | 6 indexable routes at `bcvotematch.ca` |
| 22 | robots.txt references the sitemap | crawl hygiene |
| 23 | the dataset is committed (WARN only) | an uncommitted dataset is unreproducible |
| 24 | `--online`: the domain is registered (FAIL) | publishing under a domain nobody owns |

**Verified, not assumed.** `python3 scripts/test-launch-preflight.py` builds a
complete synthetic dataset in a temp dir and asserts the gate says GO on it, then
mutates that dataset 18 ways and asserts each specific check flips to FAIL and the
exit code is right, plus a case proving the default run really runs the build
(`--network` adds a 22nd case for the domain). Current result (2026-10-01):
**21/21 cases behaved as expected**. Without that positive case, a gate that fails
on everything would look identical to a gate that works.

Run it after any change to the preflight, the validator, the data contract, or the
compliance copy.

## 2. Where we actually are (2026-10-01 01:12 PDT)

_(historical snapshot — §9 is the current state)_

Live output of `python3 scripts/launch-preflight.py --online`: **19 checks, 11 pass,
8 fail, 1 warning.** Every count below drifts while the M1/M3/M4 workers are still
writing, so treat the numbers as a snapshot and re-run the gate before acting.

    [FAIL] provenance gate (validate-dataset.py)   2 errors: no frozen questions; no coding files
    [FAIL] live question set is frozen             54 questions, 54 not frozen
    [FAIL] a coding file exists for every party    ndp=0, cpb=0, green=0, onebc=0, centrebc=0
    [FAIL] coding coverage is complete             0 coding rows found
    [FAIL] every source has an archive_url         60/212 sources unarchived
    [FAIL] export is newer than the dataset        stale by 83s (newest input: data/raw/onebc/SUMMARY.md)
    [FAIL] no placeholder content in the build     PLACEHOLDER DATA in 16 files; v0-fixture in 4
    [FAIL] domain bcvotematch.ca is registered     not registered (RDAP 404)
    [WARN] dataset is committed                    332 uncommitted data changes

The four that matter, in order:

1. **The question set is not frozen.** M2 (`<task-id>`) is sitting on Martin's
   desk. Until it is approved, `data/questions/questions.json` holds 54 candidates
   and the coders have nothing legal to code. This is the critical path; everything
   else is downstream of one line from Martin.
2. **There are no codings yet.** `data/codings/` is empty. The M3 coding card
   (`<task-id>`) is already running, carrying a hold note that tells it to code
   against the *proposed* frozen ids in `freeze-proposal.json` rather than the
   unfrozen live pool. That is a reasonable workaround, but it means codings may
   land before the freeze is formally applied, and if Martin swaps a question the
   work on it is wasted. The freeze should be applied first if it can be.
3. **60 of 212 sources have no `archive_url`** and `data/archive/` is still empty.
   The plan treats archive + hash as non-optional, and a mid-campaign vanishing
   platform page is exactly the failure mode it exists to prevent. M1 recon cards.
4. **`bcvotematch.ca` is not registered.** Checked against the .ca registry RDAP
   service (`rdap.ca.fury.ca`), which returns `404 Domain not found`; a control
   lookup of `elections.bc.ca` resolves, so this is the domain, not the network.
   `SITE.url` in `src/lib/site.ts` is that domain, so every canonical link, og:url,
   sitemap entry and share card points at somewhere nobody owns.

The other checks pass today: the build exports all 11 routes, disclaimers render on
every page, there are no trackers, no PII paths, and robots/sitemap/og are correct.
So the *site* is fine. The *dataset and the domain* are what is missing.

## 3. The path to GO

Mechanical, in order. Each step names the card that owns it.

| # | step | owner |
|---|---|---|
| 1 | Martin replies "approve freeze" (or names swaps) | human, `<task-id>` |
| 2 | Apply the freeze to `data/questions/questions.json`, hash it, commit | M2 |
| 3 | Archive every source, fix the two empty `text_path` fields | M1 × 5 |
| 4 | Code 5 parties, 2 coders each | `<task-id>` |
| 5 | Adversarial blind re-code, escalate conflicts | `<task-id>` |
| 6 | Wire real data into the site + fail `next build` when `isFixture` | `<task-id>` |
| 7 | Register the domain (or change `SITE.url` to one we own) | human |
| 8 | `npm run build` then `python3 scripts/launch-preflight.py --online` → GO | `<task-id>` |
| 9 | Martin's one-line sign-off | human, this card |
| 10 | Publish | this card |

The M2 gate is the root of the graph: `<task-id>` and `<task-id>` are its
children, and the M5 integration card is a child of both the M4 scaffold and
`<task-id>`, so steps 4 through 6 release in order without anyone chasing them.

Two gaps in the graph are worth naming. The M1 recon cards (step 3) have **no
dependency edges at all**, which is why all five ran in parallel and why their
archives can be missing without anything else being held up. And this launch card
was created with `parents: []` too, so it was dispatched in parallel with the work
it depends on; this run linked it to `<task-id>` so it cannot fire before
integration is done.

Step 7 is independent and can happen any time, and it is the only blocker that
costs money rather than effort.

## 4. Publish mechanics (once the gate is GO)

- **Artifact.** `out/` is a fully static directory (`output: "export"`). No server
  runtime, no database, no API. Everything in it is the deliverable.
- **Host.** Any static host. The published `out/` is the only state; there is no
  server-side configuration to drift.
- **Domain.** `SITE.url` is `https://bcvotematch.ca`. Register it, point an A/AAAA
  or CNAME at the host, and confirm HTTPS is issued before announcing. All internal
  URLs are absolute against this value, so changing it means a rebuild.
- **Caching.** Hashed `_next/static/*` assets can be cached immutably. The HTML
  must stay short-TTL, or a recode will not reach readers who already have the page.
- **Recodes (M7, Oct 12 and Oct 20).** Publish as a new build plus a versioned diff
  in `data/manifests/`. Keep the previous build tagged by commit sha so rollback is
  a redeploy, not an investigation.
- **Soft link vs public.** Soft link (Oct 5): give the URL to a small set of
  trusted reviewers and ask them to attack the codings. No promotion, no outreach.
  Public (Oct 8): announce. Outreach and visuals are a separate campaign under this
  project.

## 5. Evidence published with the launch

The neutrality claim is only as good as what a reader can check. These ship with
the site, not after it:

- the coding table page: one row per party per question, with the code, the quote,
  the source and archive link, the coder, the version and the timestamp;
- the full source manifest with sha256 per source under `data/`;
- `docs/SCHEMA.md` (the contract), `docs/03-QUESTION-FREEZE.md` (what was chosen
  and why), `docs/04-INTEGRATION.md` (how provenance is enforced), this file;
- the repo itself, MIT licensed, with corrections and pull requests invited.

## 6. Rollback

Because the whole site is a static directory, rollback is redeploying the previous
build. `out/` is gitignored, so the thing to keep is the commit sha that produced
the last known-good export: rebuilding that commit reproduces it. If a coding turns
out to be wrong, the fix is a recode plus a versioned diff, never a silent edit;
the published diff is part of the product.

## 7. Open items and risks

_(written 2026-10-01 01:12; several of these are fixed — §9 says which. Kept for the trail.)_

- **The domain is not registered.** Verified, not assumed (RDAP 404). Cheapest fix
  is to register it; the alternative is changing `SITE.url` and rebuilding.
- **60 of 212 sources are unarchived** and `data/archive/` is empty. The plan calls
  archive + hash non-optional, so this is a real gap, not a nice-to-have.
- **Two stray directories sit inside `data/raw/`:** `onebc.messy-bak/` and
  `ridings/`, alongside the five contract party dirs. The preflight and the
  validator both iterate a fixed slug list, so they ignore them, but anything that
  globs `data/raw/*` will pick them up: the earlier M5 run read `onebc.messy-bak`
  as 7 real sources, and the `ridings/` tree is riding-level work that must not be
  counted as party sources. M1 and M6 cards.
- **`ndp-0004` and `cpb-0005` have an empty `text_path`**, so a code citing either
  cannot have its quote checked against the source. M1's cards. (Note: the
  duplicate source ids the earlier M5 run reported in `green/sources.json` and
  `onebc/sources.json` have since been fixed by the M1 workers; re-checked
  2026-10-01 01:12, no duplicates remain.)
- **`.gitignore` references `docs/04-SITE-SCAFFOLD.md`, which does not exist.** The
  M4 scaffold wrote its notes under a different name. Cosmetic, M4's card.
- **Two workers can still collide on `package.json`.** Adding a `npm run preflight`
  alias is the natural place to wire this script in, but `package.json` is M4-owned
  and a hotspot while the scaffold is live. Left alone deliberately; whoever closes
  `<task-id>` should add it.
- **`docs/` is a collision hotspot.** Five cards have written into it in the last
  hour (`03-QUESTION-FREEZE.md`, `03-QUESTION-POOL.md`, `04-INTEGRATION.md`,
  `05-RECODE.md`, this file) plus a new `docs/recon/` directory. It has not bitten
  yet because each card picks a distinct filename, but the next wave should agree
  filenames before writing. `hotspot: docs/` — growing file count, several owners.
- **Nothing but the question pool is committed.** The repo is on `master` with one
  commit (`1e2c427`, the M1 question pool) and 38 tracked files; the site, the data
  and every script written since are untracked. Nothing is reproducible from git
  today, which is why the preflight warns rather than fails on it. Someone has to
  commit the waves before launch, and `data/archive/` has to exist for the hashes
  to mean anything.
- **Soft link is 4 days out and the critical path starts at a human reply.** The
  freeze is the whole schedule. If it slips past Oct 3, Oct 8 is at risk.

## 8. What I need from you

The launch gate is one command now (§0), and it comes *after* everything else is
GO:

- **one command** — `bash scripts/launch.sh --publish` (add `--yes` for a
  non-interactive run); or
- **"hold"** plus what has to change first.

Right now that command is not the blocker. The freeze is — the 18 are chosen and
coded but not applied to the live file (§9 item 1) — and the domain purchase
(`<task-id>`) is the only blocker that costs money rather than effort.

## 9. Snapshot after the one-command run (2026-10-01 13:05 PDT)

`bash scripts/launch.sh` on `main`, tree dirty, 5 parties / 218 source records.
Counts drift run to run while M1b and the M3 cards are still writing — re-run the
command for the current list; the shape of the answer has not changed.

    [PASS] typecheck (tsc --noEmit)      exit 0
    [PASS] next build                    exit 0
    [FAIL] launch gate                   5 failure(s) under --strict --online

    Gate detail, untruncated:
      [FAIL] provenance gate (validate-dataset.py): 2020 error(s); first: no frozen
             questions: data/questions/questions.json still holds the candidate pool
      [FAIL] live question set is frozen: 54 questions, 54 not frozen
      [FAIL] coding coverage is complete: 90/270 party-question rows
      [FAIL] every source has an archive_url: 6/217 sources unarchived
      [WARN] dataset is committed: 60 uncommitted data change(s)
      [FAIL] domain bcvotematch.ca is registered: not registered (RDAP 404)

Changed since §2: the export is real and fresh (11 routes, disclaimers on every
page), the codings exist, and the placeholder/fixture failures are gone. What
still stands between this and GO:

1. **The freeze is not applied to the live file.** The 18 are in
   `data/questions/freeze-proposal.json`, board card `<task-id>` is closed, the
   coders coded those 18 (q01, q03, q04, q10 …) — but `data/questions/questions.json`
   still holds all 54 candidates and nothing carries `status: "frozen"`. Three of
   the five failures (provenance, frozen set, coverage) are that one missing step.
   I did not do it: which issues make the 18 is Martin's call, and a second
   question sits on top of it — `questions.v2.json` (54 rewritten statements) is
   what `src/lib/data.ts` prefers when it exists, so the site currently renders 54
   questions, not 18. Whoever applies the freeze has to settle both.
2. **6 of 217 sources have no `archive_url`** (`data/archive/` exists, 211
   archived). M1b's card.
3. **`bcvotematch.ca` is not registered** (RDAP 404, re-checked today). Card
   `<task-id>`, blocked on a purchase.
4. **The dataset is uncommitted** (60 changed paths). A WARN today; under the
   launcher's `--strict` it is a failure. Commit the data before the final run.

The command itself is ready and its deploy path is tested end to end against a
stub host: packaging was run against the real export (69 files, 3.79 MB → a 754 KB
zip, integrity ok, manifest inside), and the artifact was then deleted on purpose
because the gate said NO-GO. `dist/` is gitignored.

One reproducibility limit that matters at launch time: `data/raw/**/*.txt` is
gitignored, so a fresh clone can rebuild the site from the committed codings and
questions but **cannot re-run the provenance gate** — `validate-dataset.py` checks
each quote against the source text, and the text is not in git. The hashes and
archive URLs in `sources.json` are. If the gate has to be re-run somewhere other
than this machine, the raw captures have to travel with the repo (or the check
must move to the archived copies).
