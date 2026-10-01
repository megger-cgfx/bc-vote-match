#!/usr/bin/env python3
"""build-postal-lookup.py — BC Vote Match: offline postal-code → electoral-district lookup.

Extends the M6 riding layer (scripts/build-ridings.py) with the geographic join that
lets a visitor type a postal code and land on their riding, with no runtime API call.

Inputs (all open data, fetched and saved under data/raw/ridings/):
  geonames-postal   GeoNames "CA_full.csv.zip" — every Canadian six-character postal
                    code with a representative lat/long. CC BY 4.0.
                    (Statistics Canada's PCCF would be the traditional source, but since
                    2018 its distribution is restricted to DLI members and Canada Post
                    customers, so it is not openly downloadable. GeoNames is the open
                    substitute at six-character granularity.)
  ebc-ed-polygons   "Current Provincial Electoral Districts of British Columbia"
                    (WHSE_ADMIN_BOUNDARIES.EBC_PROV_ELECTORAL_DIST_SVW), served as
                    GeoJSON (EPSG:4326) by the BC Geographic Warehouse WFS at
                    openmaps.gov.bc.ca — Elections BC's 2023-recommendation boundaries,
                    the 93 districts of the 2024–2028 redistribution. Open Government
                    Licence - BC.

Method: point-in-polygon of each postal-code representative point against the 93
district polygons (shapely STRtree; nearest-district fallback for points that land
just outside a boundary, e.g. on water). One postal code can in principle straddle a
boundary; those rare cases are stored as a list of slugs.

Outputs (generated, regenerable — do not hand-edit):
  data/candidates/postal-to-riding.json   the site-importable lookup
  data/candidates/ridings.json            93 districts + Elections BC district ids
  data/candidates/candidates.json         candidate roster enriched with district id
  data/candidates/postal-lookup-report.json  counts + coverage checks

Requires shapely (the repo .venv: `python3 -m venv --system-site-packages .venv &&
.venv/bin/pip install shapely`). `fetch` needs only the standard library.

Usage
-----
  .venv/bin/python scripts/build-postal-lookup.py fetch    # download + hash + archive
  .venv/bin/python scripts/build-postal-lookup.py build    # join -> JSON (offline)
  .venv/bin/python scripts/build-postal-lookup.py check    # coverage + spot checks
  .venv/bin/python scripts/build-postal-lookup.py all      # fetch then build then check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "ridings")
OUTDIR = os.path.join(ROOT, "data", "candidates")
RIDDIR = os.path.join(ROOT, "data", "ridings")
VERSION = "v1.0"

UA_CIVIC = "BCVoteMatch/0.1 (civic research; contact: editor@bcvotematch.ca)"
UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/[IP_ADDRESS] Safari/537.36")

WFS_URL = ("https://openmaps.gov.bc.ca/geo/pub/wfs?service=WFS&version=2.0.0"
           "&request=GetFeature&typeName=pub:WHSE_ADMIN_BOUNDARIES.EBC_PROV_ELECTORAL_DIST_SVW"
           "&outputFormat=application/json&srsName=EPSG:4326"
           "&propertyName=ED_NAME,ED_ABBREVIATION,ELECTORAL_DISTRICT_ID,SHAPE")

SOURCES = {
    "geonames-postal": {
        "type": "other",
        "title": "Canadian postal codes with coordinates (CA_full.csv.zip)",
        "publisher": "GeoNames",
        "url": "https://download.geonames.org/export/zip/CA_full.csv.zip",
        "published": "",
        "local": "geonames-ca-postal-codes.zip",
        "note": "CC BY 4.0 (geonames.org). Open substitute for the restricted PCCF.",
    },
    "ebc-ed-polygons": {
        "type": "other",
        "title": "Current Provincial Electoral Districts of British Columbia "
                 "(EBC_PROV_ELECTORAL_DIST_SVW, GeoJSON EPSG:4326)",
        "publisher": "Elections BC / BC Geographic Warehouse (Data BC)",
        "url": WFS_URL,
        "published": "2023-12-07",
        "local": "ebc-electoral-districts.geojson",
        "note": "Open Government Licence - BC. Gazette date 2023-12-07; the 93 "
                "districts of the 2024-2028 redistribution.",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("‒", "-").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


# ------------------------------------------------------------------ fetch
def _get(url: str, ua: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": ua, "Accept": "*/*", "Accept-Language": "en-CA,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def wayback(url: str, timeout: int = 45) -> str | None:
    try:
        req = urllib.request.Request(
            "https://web.archive.org/save/" + url,
            headers={"User-Agent": UA_BROWSER, "Accept": "text/html"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            final = r.geturl()
            if "web.archive.org/web/" in final:
                return final
    except Exception:
        pass
    try:
        req = urllib.request.Request(
            "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe=""),
            headers={"User-Agent": UA_CIVIC})
        with urllib.request.urlopen(req, timeout=20) as r:
            snap = json.loads(r.read().decode()).get("archived_snapshots", {}).get("closest")
            return snap.get("url") if snap else None
    except Exception:
        return None


def merge_sources(records: list[dict]) -> None:
    """Merge records into data/raw/ridings/sources.json by id (never drop other ids)."""
    path = os.path.join(RAW, "sources.json")
    existing: list[dict] = []
    if os.path.exists(path):
        existing = json.load(open(path))
    by_id = {r.get("id"): r for r in existing if r.get("id")}
    for r in records:
        by_id[r["id"]] = r
    json.dump(list(by_id.values()), open(path, "w"), indent=2)


def stage_fetch(archive: bool = True) -> list[dict]:
    os.makedirs(RAW, exist_ok=True)
    records = []
    for sid, spec in SOURCES.items():
        dest = os.path.join(RAW, spec["local"])
        raw = None
        last = None
        for ua in (UA_BROWSER, UA_CIVIC):
            try:
                raw = _get(spec["url"], ua)
                break
            except Exception as exc:  # noqa: BLE001
                last = exc
        if raw is None:
            raise SystemExit(f"fetch failed for {sid}: {last}")
        with open(dest, "wb") as f:
            f.write(raw)
        text_path = ""
        if dest.endswith(".zip"):
            # unzip the single CSV/TSV next to it for provenance-free re-parsing
            with zipfile.ZipFile(dest) as z:
                names = z.namelist()
                inner = next((n for n in names if n.lower().endswith((".csv", ".txt"))), names[0])
                txt = os.path.join(RAW, os.path.splitext(spec["local"])[0] + ".txt")
                with open(txt, "wb") as f:
                    f.write(z.read(inner))
                text_path = os.path.relpath(txt, ROOT)
        records.append({
            "id": sid,
            "party_slug": None,
            "phase": "riding",
            "type": spec["type"],
            "title": spec["title"],
            "publisher": spec.get("publisher", ""),
            "url": spec["url"],
            "published": spec["published"],
            "fetched_at": now_iso(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "local_path": os.path.relpath(dest, ROOT),
            "text_path": text_path,
            "archive_url": wayback(spec["url"]) if archive else None,
            "fetch_via": "live",
        })
        print(f"  fetched {sid}: {len(raw)} bytes sha256={records[-1]['sha256'][:12]}… "
              f"archive={records[-1]['archive_url']}")
    merge_sources(records)
    return records


# ------------------------------------------------------------------ build
def load_districts() -> list[dict]:
    """ED polygons -> [{slug, name, district_id, ed_abbreviation, shapely_geom}]."""
    from shapely.geometry import shape

    path = os.path.join(RAW, SOURCES["ebc-ed-polygons"]["local"])
    gj = json.load(open(path))
    out = []
    for feat in gj["features"]:
        p = feat["properties"]
        name = p["ED_NAME"]
        out.append({
            "slug": slugify(name),
            "name": name,
            "district_id": p["ELECTORAL_DISTRICT_ID"],
            "ed_abbreviation": p.get("ED_ABBREVIATION") or "",
            "geom": shape(feat["geometry"]),
        })
    return out


def load_postal_points() -> dict[str, list[tuple[float, float, str]]]:
    """GeoNames CA_full -> {postal (A1A1A1): [(lon, lat, place_name), ...]}."""
    txt = os.path.join(RAW, SOURCES["geonames-postal"]["local"].rsplit(".", 1)[0] + ".txt")
    pts: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    with open(txt, encoding="utf-8") as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 11 or cols[4] != "BC":
                continue
            pc = cols[1].replace(" ", "").upper()
            if len(pc) != 6:
                continue
            try:
                lat, lon = float(cols[9]), float(cols[10])
            except ValueError:
                continue
            pts[pc].append((lon, lat, cols[2]))
    return pts


def stage_build() -> dict:
    from shapely.geometry import Point
    from shapely.strtree import STRtree

    districts = load_districts()
    pts = load_postal_points()
    geoms = [d["geom"] for d in districts]
    tree = STRtree(geoms)

    postal: dict[str, object] = {}
    fsa_counts: dict[str, Counter] = defaultdict(Counter)
    approx = 0
    ambiguous = 0
    unmatched = []

    for pc, rows in pts.items():
        slugs = set()
        for lon, lat, _place in rows:
            pt = Point(lon, lat)
            hit = None
            for idx in tree.query(pt):
                if geoms[idx].covers(pt):
                    hit = districts[idx]["slug"]
                    break
            if hit is None:
                idx = tree.nearest(pt)
                if geoms[idx].distance(pt) <= 0.01:  # ~1 km, points on water/edges
                    hit = districts[idx]["slug"]
                    approx += 1
            if hit is not None:
                slugs.add(hit)
        if not slugs:
            unmatched.append(pc)
            continue
        if len(slugs) > 1:
            ambiguous += 1
            postal[pc] = sorted(slugs)
            for s in slugs:
                fsa_counts[pc[:3]][s] += 1
        else:
            s = next(iter(slugs))
            postal[pc] = s
            fsa_counts[pc[:3]][s] += 1

    fsa = {
        f: {
            "ridings": [s for s, _ in c.most_common()],
            "primary": c.most_common(1)[0][0],
            "counts": dict(c),
        }
        for f, c in sorted(fsa_counts.items())
    }

    # riding master list from the M6 dataset, enriched with Elections BC district ids
    ridings = json.load(open(os.path.join(RIDDIR, "ridings.json")))
    by_slug = {d["slug"]: d for d in districts}
    missing_poly, missing_data = [], []
    ridings_out = []
    for r in ridings:
        d = by_slug.get(r["slug"])
        if d is None:
            missing_poly.append(r["slug"])
            continue
        ridings_out.append({
            "slug": r["slug"], "name": r["name"], "region": r["region"],
            "district_id": d["district_id"], "ed_abbreviation": d["ed_abbreviation"],
            "source_id": "ebc-ed-polygons",
        })
    for d in districts:
        if d["slug"] not in {r["slug"] for r in ridings}:
            missing_data.append(d["slug"])

    # candidates mirror, enriched with riding name + district id
    cands = json.load(open(os.path.join(RIDDIR, "candidates.json")))
    rid_by_slug = {r["slug"]: r for r in ridings_out}
    cands_out = []
    for c in cands:
        r = rid_by_slug.get(c["riding_slug"], {})
        c2 = dict(c)
        c2["riding_name"] = r.get("name")
        c2["district_id"] = r.get("district_id")
        cands_out.append(c2)

    covered = Counter()
    for v in postal.values():
        for s in (v if isinstance(v, list) else [v]):
            covered[s] += 1

    lookup = {
        "version": VERSION,
        "built_at": now_iso(),
        "source_ids": ["geonames-postal", "ebc-ed-polygons"],
        "method": ("point-in-polygon of GeoNames postal-code representative points "
                   "against Elections BC provincial electoral district polygons"),
        "key_format": "6-character postal code, no space, uppercase (e.g. V8R3L2)",
        "value_format": "riding slug, or a sorted list of slugs when a postal code "
                        "straddles a boundary",
        "ridings": {
            r["slug"]: {"name": r["name"], "district_id": r["district_id"],
                        "ed_abbreviation": r["ed_abbreviation"]}
            for r in ridings_out
        },
        "fsa": fsa,
        "postal": dict(sorted(postal.items())),
    }

    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "postal-to-riding.json"), "w") as f:
        json.dump(lookup, f, separators=(",", ":"))
    json.dump(ridings_out, open(os.path.join(OUTDIR, "ridings.json"), "w"), indent=2)
    json.dump(cands_out, open(os.path.join(OUTDIR, "candidates.json"), "w"), indent=2)

    report = {
        "version": VERSION,
        "built_at": lookup["built_at"],
        "ridings": len(ridings_out),
        "polygons": len(districts),
        "candidates": len(cands_out),
        "postal_codes_mapped": len(postal),
        "postal_codes_unmatched": len(unmatched),
        "postal_codes_boundary_nearest": approx,
        "postal_codes_straddling": ambiguous,
        "fsa_count": len(fsa),
        "ridings_without_postal_codes": sorted({r["slug"] for r in ridings_out} - set(covered)),
        "slug_mismatch_polygon_missing": missing_poly,
        "slug_mismatch_data_missing": missing_data,
        "unmatched_sample": unmatched[:10],
    }
    json.dump(report, open(os.path.join(OUTDIR, "postal-lookup-report.json"), "w"), indent=2)
    print(json.dumps({k: v for k, v in report.items() if not k.endswith("sample")}, indent=1))
    return report


# ------------------------------------------------------------------ check
def stage_check() -> int:
    path = os.path.join(OUTDIR, "postal-to-riding.json")
    lookup = json.load(open(path))
    postal = lookup["postal"]
    fsa = lookup["fsa"]
    ridings = lookup["ridings"]
    report = json.load(open(os.path.join(OUTDIR, "postal-lookup-report.json")))
    fails = []

    if len(ridings) != 93:
        fails.append(f"ridings map has {len(ridings)} entries, expected 93")
    if report["ridings_without_postal_codes"]:
        fails.append(f"ridings with no postal codes: {report['ridings_without_postal_codes']}")
    if report["slug_mismatch_polygon_missing"] or report["slug_mismatch_data_missing"]:
        fails.append(f"slug mismatches: polygon={report['slug_mismatch_polygon_missing']} "
                     f"data={report['slug_mismatch_data_missing']}")
    if len(postal) < 100000:
        fails.append(f"only {len(postal)} postal codes mapped, expected 100k+")

    for pc, v in list(postal.items()):
        slugs = v if isinstance(v, list) else [v]
        for s in slugs:
            if s not in ridings:
                fails.append(f"postal {pc} -> unknown riding {s}")
                break
        if pc[:3] not in fsa:
            fails.append(f"postal {pc} has no FSA entry")
            break
        if len(fails) > 20:
            break

    # spot checks against well-known geography
    spots = {
        "V8R": "victoria-beacon-hill",   # Victoria residential
        "V6B": "vancouver-west-end",     # downtown Vancouver (check primary below)
        "V2V": "abbotsford-mission",     # Mission
        "V0H": "boundary-similkameen",   # Christina Lake / Boundary country
    }
    for fsa_key, expect in spots.items():
        if fsa_key not in fsa:
            fails.append(f"spot check: FSA {fsa_key} missing")
            continue
        primaries = set(fsa[fsa_key]["ridings"])
        if expect not in primaries:
            fails.append(f"spot check: FSA {fsa_key} ridings {sorted(primaries)} "
                         f"do not include {expect}")

    print(f"[check] {len(postal)} postal codes, {len(fsa)} FSAs, "
          f"{len(ridings)} ridings, {report['postal_codes_straddling']} straddling, "
          f"{report['postal_codes_boundary_nearest']} nearest-fallback")
    if fails:
        for f in fails[:25]:
            print("  FAIL", f)
        return 1
    print("[check] OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["fetch", "build", "check", "all"])
    ap.add_argument("--no-archive", action="store_true")
    args = ap.parse_args()
    if args.stage in ("fetch", "all"):
        stage_fetch(archive=not args.no_archive)
    if args.stage in ("build", "all"):
        stage_build()
    if args.stage in ("check", "all"):
        return stage_check()
    return 0


if __name__ == "__main__":
    sys.exit(main())
