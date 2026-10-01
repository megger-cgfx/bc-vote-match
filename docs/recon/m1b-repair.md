# M1b — suspect sources repaired, duplicate scan complete

_Run 2026-10-01 (agent flower). Machine-readable companion: `data/recon/m1b-scan.json`._

## What this pass covered

Every record in `data/raw/*/sources.json` — 222 records across the five party directories
plus the riding layer — was re-checked against the bytes on disk. Two questions were asked of
each record: is this capture a duplicate of another one, and does the stored file actually
contain the document the record claims?

Companion artifacts:

- `data/recon/m1b-scan.json` — the full scan: duplicate groups (by sha256, by URL, by title),
  every flagged record with its flags and notes, and counters.
- `scripts/verify-data.py` — unchanged provenance gate, re-run after every repair below.

## Prior pass (context)

An earlier source-repair agent (commit `3394b71`) ran the first duplicate scan and marked the
five byte-identical pairs, and marked `centrebc-0064` as an unresolvable 301. It also reported
`cpb-0011` and `centrebc-0009` as suspect but could not reproduce either. This pass re-checked
both claims, found the real defect behind the `centrebc-0009` report (file naming, fixed below),
and carried the scan further: URL-level duplicates across parties, text-content checks, and the
repairs in the next section.

## Duplicate scan

| group type | count | handling |
|---|---|---|
| byte-identical captures (same sha256) | 5 | each non-canonical copy carries `superseded_by` |
| same URL, byte-identical | 3 of the 5 above | Hansard files captured independently by two parties |
| same URL, different bytes | 1 | `green-0022` / `ndp-0036` — one Western Standard article, two recon runs |
| duplicate titles within the corpus | 0 | — |
| duplicate ids | 0 | `verify-data.py` would fail on these |

The five identical-byte pairs: `ndp-0024`/`cpb-0024` (Hansard 2026-02-18 pm), `ndp-0028`/
`green-0096` (2026-05-27 pm), `cpb-0025`/`centrebc-0059` (2026-04-02 am), `cpb-0026`/
`centrebc-0067` (2026-04-13 pm), and `centrebc-0003`/`centrebc-0064`. Keeping both copies is
deliberate: each party directory documents what that party's recon actually pulled, and the
duplicate is recorded rather than silently deleted.

`green-0022` and `ndp-0036` are the same Western Standard URL captured twice with different
bytes. The extracted text is identical in both (1,832 bytes) and consists of the headline plus
site chrome — the article body is not in the capture. Both records now carry
`content_status: partial_capture` so no coder quotes a body that was never fetched.

## Repairs

### 1. CentreBC file names now match record ids (root cause of a false alarm)

47 of the 56 CentreBC records pointed at files numbered differently from their own id
(`centrebc-0058` → `centrebc-0048.html`, and so on), because ids were renumbered to close gaps
while the files on disk kept their original numbering. 94 files were renamed so that every
`local_path` / `text_path` basename equals its record id; the sha256 values, URLs and titles
were not touched, and `verify-data.py` confirms all 56 captures still hash-match.

This is what produced the M3 coder report that "centrebc-0009 is the wrong page". The record
for `centrebc-0009` has always pointed at a correct capture of `/our-policy/` — but
`data/raw/centrebc/centrebc-0009.txt` used to hold a different document's text, so anyone
checking a citation by file name saw the wrong page. The claim is refuted for the record and
was true for the file path; the path is now fixed.

### 2. Text recovered for captures that shipped without it

| record | what it is | what was wrong | repair |
|---|---|---|---|
| `cpb-0005` | "Make BC an Energy Superpower", 2026 campaign policy PDF | no `text_path`; an earlier pass tried `pdftotext` and correctly called its per-glyph output unquotable | text layer re-extracted with PyMuPDF → 9,137 chars of clean prose; `text_source` recorded, PDF capture untouched |
| `ndp-0004` | "An Action Plan for You", 2024 platform highlights PDF | no text layer (Illustrator outlines) | 4 pages OCR'd (`pdftoppm` 300 dpi + `tesseract`) → 12,144 bytes; marked `content_status: ocr_text` |
| `wiki-candidates` | Wikipedia candidate list (riding layer) | `text_path` empty | HTML text extracted from the stored capture → 17,849 bytes |

The PDF captures themselves were not re-fetched, so their sha256 values are unchanged.

While repairing `cpb-0005` every PDF capture in the corpus was re-audited (12 records): all
others already carry text that matches what PyMuPDF extracts from the same file. Only
`cpb-0005` was degraded, and only `ndp-0004` has no text layer at all.

### 3. Unusable captures marked, one replaced

| record | problem | outcome |
|---|---|---|
| `green-0099` | caucus page serves the site-wide "under maintenance" page (live and in Wayback) | `content_status: maintenance_page`, `replaced_by: green-0100` |
| `green-0100` (new) | — | same release (Auditor General letter on the ~$1.5B gas-royalty forecast error, Rob Botterell) captured live from the party site, `bcgreens.ca`, published 2026-08-31 |
| `green-0098` | same maintenance page | `content_status: maintenance_page`; no live equivalent found on `bcgreens.ca` (its LNG items are different documents) |
| `green-0039`, `green-0040` | YouTube watch pages; extraction returns 213–216 bytes of page chrome | `content_status: boilerplate_only` — pointer records, not quotable |
| `green-0022`, `ndp-0036` | headline + chrome only | `content_status: partial_capture` |

### 4. Claims checked and refuted

`cpb-0011` was reported as a text/title mismatch: record title, URL, stored file and sha256 all
agree, and the extracted text opens with the release headline. Refuted, no change.

## Verification

```
$ python3 scripts/verify-data.py
party sources total : 218
all records scanned : 222
local files present : 222
sha256 verified     : 222
hash mismatches     : 0
missing files       : 0
archive coverage    : 216/222
RESULT: PASS — 0 integrity problems
```

### Where this landed in git

The M1b changes are committed as `d681b1c` (`docs: M1b repair report …` — the message is wrong,
see below; `git show --stat d681b1c` lists the ten files, including every `data/raw/*/sources.json`).

The message is wrong because of a shared-repo race. The M1b edits were staged for a `data/raw:`
commit when a concurrent coding worker committed the whole index, so the M1b files rode along
under its codings message (`a6cd058`). That worker then reset `main` back one commit
(`git reflog`: `reset: moving to HEAD~1`) and re-committed only its own file (`1c7f660`), which
put the M1b edits back in the working tree. They were then committed on their own as `d681b1c`.
Nothing was lost; `verify-data.py` passes at HEAD.

Two process notes for the orchestrator, both true of this repo as of this run:

1. Concurrent `git add`/`git commit` in one shared clone is a race — the first commit takes
   whatever both workers have staged. Serialise commits, or commit with explicit pathspecs.
2. A worker reset `main` back a commit, which the repo rules forbid ("no history rewriting").
   It was recovered here, but the resets make the shared branch unreliable for everyone else.

## Open items

- **The BC Green caucus site is still in maintenance** (`bcgreencaucus.ca`, site-wide). Any
  further capture from that host will store the maintenance page; the two affected records are
  marked so nothing downstream quotes them.
- **YouTube records have no transcript.** `green-0039` and `green-0040` are chrome-only. A
  transcript capture (yt-dlp or an API) would turn them into usable speech sources.
- **OCR text is approximate.** `ndp-0004`'s recovered text comes from a graphic-heavy PDF;
  quotes must be checked against the page images before publication.
- **Wayback coverage is 216/222.** `green-0100` was archived during this pass
  (`web.archive.org/web/20261001195432/…`); the six remaining are mostly Hansard and PDF
  captures that predate this pass. `web.archive.org/save` rate-limits by IP, so backfilling is
  a retry job, not a failure.
- **Not checked in this pass:** whether each record's party attribution matches its content
  (a release filed under the wrong party), and near-duplicate text that is not byte-identical.
  The first would need a per-record content read; the second would need shingling over the
  text files. Neither is currently known to be a problem.
