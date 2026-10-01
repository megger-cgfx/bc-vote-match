# The WIP contact-sheet process (campaign standing procedure)

Martin's rule: he reviews the curated selection, but he also wants to see **what was not chosen**,
so a rejection is a visible decision rather than a silent one. This is the mechanism that makes
that automatic rather than a favour someone has to remember.

## The two halves

**1. Every image-producing worker registers what it made.** Append one JSON object per line to
`marketing/assets/MANIFEST.jsonl`:

```json
{"path":"marketing/assets/og/director-og.png","produced_by":"<who>","goal":"<task>",
 "created":"<ISO 8601>","kind":"render|generate|download","verdict":"selected",
 "rationale":"<why this verdict>","width":1200,"height":630,"sha256":"<hex>",
 "model":null,"prompt":null,"seed":null,"sampler":null,"steps":null,"cfg":null}
```

Append only. Never rewrite the file, never reformat someone else's line.

`verdict` is one of:

- `selected` — the producer believes this is the best of what it made
- `unselected` — a real candidate that was not picked
- `raw` — unedited generator output
- `superseded` — an earlier attempt replaced by a later one
- `rejected` — failed a rule, and `rationale` names which rule

**Unselected and rejected images stay on disk.** Deleting a candidate destroys the evidence Martin
asked for. If a candidate is bad, leave it and say why.

**2. The sheet is compiled from that manifest.** Run:

```bash
python3 marketing/tools/build-contact-sheet.py
```

It writes `marketing/06-review/contact-sheets/sheet-NN.png` plus `sheet-index.json`.

## Why the compiler scans rather than trusts

The compiler walks the whole image tree (`marketing/assets/`, `public/previews/`, `public/og.png`,
`src/app/`) and then *looks up* verdicts in the manifest. It does not iterate the manifest.

That ordering matters: an image with no manifest entry still appears on the sheet, labelled
`unregistered`. A manifest-driven compiler would silently hide exactly the images nobody bothered
to register, which is the one thing this process exists to prevent. `unregistered` is therefore a
finding, not a cosmetic state — when the count is non-zero, someone did not follow this page.

## SVG sources

Vector sources are rasterised on the fly through `marketing/tools/render-card.js` (no `--w/--h`, so
each source declares its own size), so design work that only exists as SVG is still visible.

## Handoff to Martin

The sheet is an image, so it is passed up as an image: the marketing director attaches the
`sheet-NN.png` files directly. He should not have to open a JSON to see what was made.

## Status of the rule

The rule was introduced on 2026-10-01, mid-wave. Assets produced before it are labelled
`unregistered` on the first sheet. That is expected, not a fault. Anything produced after this page
exists should be registered.