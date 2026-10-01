# BCVM M6b — Postal code → riding lookup

_Prepared by flower, 2026-10-01. Additive to M6 (docs/M6-RIDING-V1.1.md)._

## What this adds

An offline postal-code → electoral-district lookup so the site can take a postal code
and land on the right riding with no runtime API call, plus a `data/candidates/`
delivery bundle for the riding phase.

| file | contents |
|---|---|
| `data/candidates/postal-to-riding.json` | 122,334 BC postal codes → riding slug, plus an FSA fallback index and the 93-riding master map (3.8 MB, one lazy fetch) |
| `data/candidates/ridings.json` | 93 districts with Elections BC `district_id` + `ED_ABBREVIATION` |
| `data/candidates/candidates.json` | 208 candidates (v1.1 snapshot) with riding name + district id |
| `data/candidates/postal-lookup-report.json` | counts + coverage checks |

## Sources (open data, saved and hashed under data/raw/ridings/)

1. **GeoNames `CA_full.csv.zip`** — every Canadian six-character postal code with a
   representative lat/long. CC BY 4.0.
   sha256 `eff642df…`, archived `http://web.archive.org/web/20251112181537/…`.
   *Why not the PCCF:* since 2018 Statistics Canada distributes the Postal Code
   Conversion File only to DLI members and through Canada Post; it is not openly
   downloadable, so it can't back a reproducible open pipeline.
2. **Current Provincial Electoral Districts of British Columbia**
   (`WHSE_ADMIN_BOUNDARIES.EBC_PROV_ELECTORAL_DIST_SVW`, GeoJSON EPSG:4326) from the
   BC Geographic Warehouse WFS — Elections BC's gazetted 2023-12-07 boundaries, the 93
   districts of the 2024–2028 redistribution. Open Government Licence - BC.
   sha256 `5e34e59f…`, archived `https://web.archive.org/web/20261001083830/…`.

Method: point-in-polygon (shapely STRtree) of each postal code's representative point
against the district polygons; nearest-district fallback within ~1 km for points that
land just outside a boundary (1 code). Every record in `data/raw/ridings/sources.json`
carries url, sha256, archive_url and fetched_at per docs/SCHEMA.md.

## Verified

- 93/93 district polygons match the M6 riding slugs both ways (no mismatches).
- 122,334 postal codes mapped, **0 unmatched**, 1 nearest-fallback, 1 straddling a
  boundary (`V0K2S1` → cariboo-chilcotin + fraser-nicola, stored as a list).
- 193 FSAs; every riding has postal codes.
- `scripts/build-postal-lookup.py check` → OK (shape, coverage, spot checks:
  `V2V0G4`→abbotsford-mission and `V0H1E1`→boundary-similkameen match the addresses
  printed on the Elections BC candidate list; `V8R` includes victoria-beacon-hill).
- `scripts/validate-ridings.py` → exit 0 (93 districts, 208 candidates, provenance
  intact); `--selftest` all cases behave.

## Known limits

- GeoNames coordinates are representative points, not address-level Canada Post data;
  a few codes on riding boundaries can resolve one riding over (recorded in
  `postal_codes_boundary_nearest`). For v1 this is the honest open-data trade.
- The lookup is geography only. It never implies anything about a candidate.

## Refresh (the one TODO)

Nominations close **3 Oct 2026, 13:00 PT**. After close, from the repo root:

```
python3 scripts/build-ridings.py fetch            # re-pull the Elections BC candidate list
python3 scripts/build-ridings.py build --version v1.2
.venv/bin/python scripts/build-postal-lookup.py all   # re-join, regenerate data/candidates/
python3 scripts/validate-ridings.py               # must exit 0
```

Expect `status` to move from `declared` to `nominated` across the roster and the
candidate count to change; the lookup itself only needs a rebuild to re-copy the
candidate mirror. If Elections BC republishes the district polygons, `fetch` picks
that up too.
