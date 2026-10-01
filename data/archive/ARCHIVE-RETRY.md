# Wayback Archive Retry Report

Generated: 2026-10-01T21:52:18Z

Scope: every source in `data/raw/{{ndp,cpb,green,onebc,centrebc}}/sources.json` whose
`archive_url` was null after the first pass. Only the `archive_url` field was updated;
ids, titles, hashes, local files and all other fields are untouched.

## Method
- `GET https://web.archive.org/save/<url>` with a descriptive user agent, 150s timeout, following the save redirect to read the capture URL.
- Fallback: `https://archive.org/wayback/available?url=...` (closest existing snapshot), then the CDX API for any existing capture.
- Requests paced 12s apart; round-based retries while the Internet Archive was reachable.

## Before / after archived counts

| party | total | archived before | archived after | newly archived | still unarchived |
|---|---|---|---|---|---|
| ndp | 46 | 46 | 46 | 0 | 0 |
| cpb | 54 | 54 | 54 | 0 | 0 |
| green | 43 | 43 | 43 | 0 | 0 |
| onebc | 19 | 19 | 19 | 0 | 0 |
| centrebc | 56 | 50 | 55 | 5 | 1 |
| **total** | **218** | **212** | **217** | **5** | **1** |

## Succeeded (5)

### centrebc
- `centrebc-0029` -> https://web.archive.org/web/20261001214441/https://www.centrebc.ca/news/budget-2026-managing-decline-is-not-leadership/ (save ok (http 200))
- `centrebc-0031` -> https://web.archive.org/web/20261001214912/https://www.centrebc.ca/news/statement-tragic-shooting-in-tumbler-ridge/ (save ok (http 200))
- `centrebc-0032` -> https://web.archive.org/web/20261001214230/https://www.centrebc.ca/news/opinion-facing-trump-threat-bc-needs-more-than-government-by-clickbait/ (save ok (http 200))
- `centrebc-0039` -> https://web.archive.org/web/20261001215112/https://www.centrebc.ca/news/news-release/news-release-eby-remains-uncommitted-to-workers-rewards-friends/ (save ok (http 200))
- `centrebc-0046` -> https://web.archive.org/web/20261001214617/https://www.centrebc.ca/news/opinion-the-hard-work-of-certainty-resolving-bcs-original-sin/ (save ok (http 200))

## Still unarchived (1)

### centrebc
- `centrebc-0050` https://www.centrebc.ca/news/budget-2026-a-blueprint-for-bankruptcy/ — save http 520; available http 200, cdx http 200

