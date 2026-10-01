#!/usr/bin/env python3
"""build-ridings.py — BC Vote Match M6: riding-level dataset builder.

Two public, non-partisan sources become the riding-level contract files:

  data/raw/ridings/sources.json   provenance for the two sources (hash + archive)
  data/ridings/ridings.json       the 93 electoral districts
  data/ridings/candidates.json    the v1.1 candidate roster
  data/ridings/build-report.json  counts + cross-checks (audit trail)

Sources
-------
  ebc-list          Elections BC official candidate list (the authority for who has
                    filed a complete nomination). Fetched as PDF; parsed with
                    `pdftotext -layout`. Only the electoral-district, candidate-name
                    and affiliation columns are read — every agent column (names,
                    street addresses, phone numbers) is dropped, per the project's
                    no-PII rule.
  wiki-candidates   Wikipedia "Candidates of the 2026 British Columbia general
                    election", used for the complete 93-riding roster (Elections BC
                    lists only nominations accepted so far; nominations close
                    2026-10-03). Names marked * there are registered with Elections BC.

Usage
-----
  python3 scripts/build-ridings.py fetch     # download + hash + archive the sources
  python3 scripts/build-ridings.py build     # parse the local copies -> JSON
  python3 scripts/build-ridings.py all       # fetch then build
  python3 scripts/build-ridings.py report    # print the cross-check report

`build` is offline: it only reads data/raw/ridings/*. Re-running it after the
nomination deadline (or later in the campaign) is how the dataset is refreshed —
bump --version and it is a new snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "ridings")
OUTDIR = os.path.join(ROOT, "data", "ridings")
VERSION = "v1.1"
UA_CIVIC = "BCVoteMatch/0.1 (civic research; contact: editor@bcvotematch.ca)"
UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

SOURCES = {
    "ebc-list": {
        "type": "other",
        "title": "Candidates — 2026 Provincial General Election (official candidate list)",
        "publisher": "Elections BC",
        "url": "https://www.elections.bc.ca/docs/fin/GE-2026-10-24-Candidate-Website-Report.PDF",
        "published": "2026-09-30",
        "local": "ebc-candidates.pdf",
    },
    "wiki-candidates": {
        "type": "media",
        "title": "Candidates of the 2026 British Columbia general election",
        "publisher": "Wikipedia",
        "url": "https://en.wikipedia.org/wiki/Candidates_of_the_2026_British_Columbia_general_election",
        "published": "2026-09-30",
        "local": "wiki-candidates.html",
    },
}

# Column label in the Wikipedia candidates tables -> contract party.
CONTRACT = {
    "ndp": "BC New Democratic Party",
    "cpb": "Conservative Party of British Columbia",
    "green": "BC Green Party",
    "onebc": "OneBC",
    "centrebc": "CentreBC",
}
PARTY_NORM = {
    "NDP": ("party", "ndp"),
    "Conservative": ("party", "cpb"),
    "Green": ("party", "green"),
    "OneBC": ("party", "onebc"),
    "CentreBC": ("party", "centrebc"),
    "Independent": ("independent", None),
}
BALLOT_LABEL = {
    "ndp": "BC NDP",
    "cpb": "Conservative Party",
    "green": "BC Green Party",
    "onebc": "OneBC",
    "centrebc": "CentreBC",
}

SUFFIX_RE = re.compile(r"\[\s*[^\]]*\]\s*$")          # footnote markers: " [ 3 ]"
DAGGER_RE = re.compile(r"[\u2020\u2021]")               # † / ‡
PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")              # "(Comm.)"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("‒", "-").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def norm_name(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace(".", " ").replace("'", "").replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def norm_riding(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def clean_cell(text: str) -> str:
    """Cell text -> bare value: drop footnote markers and daggers."""
    text = " ".join(text.split())
    text = SUFFIX_RE.sub("", text).strip()
    text = DAGGER_RE.sub("", text).strip()
    return text


# ------------------------------------------------------------------ fetch
def _get(url: str, ua: str, timeout: int = 60) -> bytes:
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
        if dest.endswith(".pdf"):
            txt = os.path.join(RAW, "ebc-candidates.txt")
            subprocess.run(["pdftotext", "-layout", dest, txt], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            text_path = os.path.relpath(txt, ROOT)
        records.append({
            "id": sid, "party_slug": None, "phase": "riding", "type": spec["type"],
            "title": spec["title"], "publisher": spec.get("publisher", ""),
            "url": spec["url"], "published": spec["published"],
            "fetched_at": now_iso(), "sha256": hashlib.sha256(raw).hexdigest(),
            "local_path": os.path.relpath(dest, ROOT), "text_path": text_path,
            "archive_url": wayback(spec["url"]) if archive else None,
            "fetch_via": "live",
        })
    # merge by id so records written by other builders (e.g. build-postal-lookup.py)
    # survive a refresh of these two sources
    path = os.path.join(RAW, "sources.json")
    by_id = {}
    if os.path.exists(path):
        for r in json.load(open(path)):
            if r.get("id"):
                by_id[r["id"]] = r
    for r in records:
        by_id[r["id"]] = r
    json.dump(list(by_id.values()), open(path, "w"), indent=2)
    for r in records:
        print(f"  fetched {r['id']}: {len(open(os.path.join(ROOT, r['local_path']),'rb').read())} bytes "
              f"sha256={r['sha256'][:12]}… archive={r['archive_url']}")
    return records


# ------------------------------------------------------------ wiki tables
def _table_grid(table) -> tuple[list[str], list[list[str]]]:
    """Expand a candidates table into (party_columns, grid rows).

    Rowspan/colspan are materialised into a rectangular grid so a riding that
    continues onto a second row (e.g. Peace River North, Vancouver-Hastings) is read
    correctly instead of dropping the extra candidates.
    """
    rows = table.find_all("tr")
    party_cols = [" ".join(th.get_text(" ", strip=True).split())
                  for th in rows[1].find_all("th")]
    occ: dict[tuple[int, int], str] = {}
    maxcol = 0
    for r, tr in enumerate(rows[2:]):
        c = 0
        for td in tr.find_all(["td", "th"]):
            while (r, c) in occ:
                c += 1
            val = clean_cell(td.get_text(" ", strip=True))
            cs = int(td.get("colspan") or 1)
            rs = int(td.get("rowspan") or 1)
            for dr in range(rs):
                for dc in range(cs):
                    occ[(r + dr, c + dc)] = val
            c += cs
            maxcol = max(maxcol, c)
    if not occ:
        return party_cols, []
    nrow = max(r for r, _ in occ) + 1
    grid = [[occ.get((r, c), "") for c in range(maxcol)] for r in range(nrow)]
    return party_cols, grid


def parse_wiki_tables(html_path: str) -> tuple[list[dict], list[dict]]:
    """Parse the rendered candidate tables -> (ridings, candidates)."""
    soup = BeautifulSoup(open(html_path, encoding="utf-8").read(), "lxml")

    region_of: dict[int, str] = {}
    current = "British Columbia"
    for el in soup.find_all(["h2", "h3", "h4", "table"]):
        if el.name in ("h2", "h3", "h4"):
            txt = re.sub(r"\[edit\]$", "", " ".join(el.get_text(" ", strip=True).split())).strip()
            if txt:
                current = txt
        elif "wikitable" in (el.get("class") or []):
            region_of[id(el)] = current

    ridings: list[dict] = []
    candidates: list[dict] = []
    seen_riding: set[str] = set()
    seen_cand: dict[tuple[str, str], dict] = {}

    for table in soup.find_all("table", class_=lambda c: c and "wikitable" in c):
        rows = table.find_all("tr")
        if len(rows) < 2 or "Candidates" not in " ".join(rows[0].get_text(" ", strip=True).split()):
            continue
        party_cols, grid = _table_grid(table)
        if not party_cols:
            continue
        region = region_of.get(id(table), "British Columbia")
        for row in grid:
            ride_name = row[0] if row else ""
            if not ride_name:
                continue
            ride_slug = slugify(ride_name)
            if ride_slug not in seen_riding:
                seen_riding.add(ride_slug)
                ridings.append({"slug": ride_slug, "name": ride_name,
                                "region": region, "source_id": "wiki-candidates"})
            for i, col in enumerate(party_cols[:6]):
                idx = 2 + 2 * i
                cell = row[idx] if idx < len(row) else ""
                if not cell:
                    continue
                registered = cell.endswith("*")
                name = cell.rstrip("*").strip()
                name = PAREN_RE.sub("", name).strip() or name
                if not name:
                    continue
                key = (ride_slug, name)
                if key in seen_cand:
                    # a rowspan cell repeats on the riding's continuation row
                    seen_cand[key]["registered_wiki"] |= registered
                    continue
                rec = {"riding_slug": ride_slug, "name": name, "party_col": col,
                       "registered_wiki": registered}
                seen_cand[key] = rec
                candidates.append(rec)
    ridings.sort(key=lambda r: r["name"])
    return ridings, candidates


def apply_incumbents(html_path: str, ridings: list[dict], candidates: list[dict]) -> int:
    soup = BeautifulSoup(open(html_path, encoding="utf-8").read(), "lxml")
    known = {r["slug"] for r in ridings}
    inc: dict[str, set[str]] = {}
    for table in soup.find_all("table", class_=lambda c: c and "wikitable" in c):
        rows = table.find_all("tr")
        if len(rows) < 2 or "Candidates" not in " ".join(rows[0].get_text(" ", strip=True).split()):
            continue
        _, grid = _table_grid(table)
        for row in grid:
            ride = slugify(row[0]) if row and row[0] else ""
            if ride not in known:
                continue
            nm = row[-1] if row else ""
            if len(nm) > 2:
                inc.setdefault(ride, set()).add(norm_name(nm))
    n = 0
    for c in candidates:
        if norm_name(c["name"]) in inc.get(c["riding_slug"], set()):
            c["incumbent"] = True
            n += 1
    return n


# --------------------------------------------------------------- EBC PDF
def parse_ebc_layout(text: str, known_riding_names: set[str]) -> dict:
    """{(riding_norm, name_norm): affiliation_label} from the EBC layout text.

    The PDF renders as fixed-width columns:
      Electoral District | Candidate Name | Affiliation | Financial Agent | ...
    We read only the first three; the agent columns (names, addresses, phones) are
    discarded and never stored. Candidate names that overflow the column wrap onto
    the next line and are re-joined.
    """
    lines = text.split("\n")
    hdr = next((l for l in lines if "Electoral District" in l and "Candidate Name" in l), None)
    if not hdr:
        return {}
    off = {
        "ride": hdr.index("Electoral District"),
        "cand": hdr.index("Candidate Name"),
        "aff": hdr.index("Affiliation"),
        "fin": hdr.index("Financial Agent"),
    }
    rid_norm = {norm_riding(r): r for r in known_riding_names}
    aff_re = re.compile(r"^[A-Za-z][A-Za-z0-9 &.\-']*$")
    name_re = re.compile(r"^[A-Z][A-Za-z'\u00c0-\u017f.\-]*(?: [A-Z][A-Za-z'\u00c0-\u017f.\-]*)*$")

    def is_aff(a: str) -> bool:
        return bool(a) and len(a) <= 30 and bool(aff_re.match(a)) and not a.lower().startswith("the ")

    out: dict[tuple[str, str], str] = {}
    cur_ride = None
    pending = None

    def finalize():
        nonlocal pending
        if pending and pending["name"] and pending["aff"]:
            out[(norm_riding(pending["ride"]), norm_name(pending["name"]))] = pending["aff"]
        pending = None

    for ln in lines:
        if len(ln) <= off["cand"]:
            continue
        col0 = ln[off["ride"]:off["cand"]].strip()
        cand = ln[off["cand"]:off["aff"]].strip()
        aff = ln[off["aff"]:off["fin"]].strip()
        if col0 and norm_riding(col0) in rid_norm:
            finalize()
            cur_ride = rid_norm[norm_riding(col0)]
            # fall through: the riding line also carries that riding's first candidate
        if cur_ride is None or not cand:
            continue
        if pending and pending["aff"] and len(cand.split()) == 1 and (aff in ("", "Party") or not is_aff(aff)):
            # a single-token remainder is a wrapped candidate name ("Stephanie" /
            # "Higginson"), not a second candidate.
            pending["name"] += " " + cand
            if aff == "Party" and not pending["aff"].endswith("Party"):
                pending["aff"] += " Party"
        elif name_re.match(cand) and is_aff(aff):
            finalize()
            pending = {"ride": cur_ride, "name": cand, "aff": aff}
        elif aff == "" and name_re.match(cand):
            finalize()
            pending = {"ride": cur_ride, "name": cand, "aff": ""}
        elif pending and not cand and is_aff(aff) and not pending["aff"]:
            pending["aff"] = aff
    finalize()
    return out


# ----------------------------------------------------------------- build
def stage_build(version: str = VERSION) -> dict:
    sources = json.load(open(os.path.join(RAW, "sources.json")))
    by_id = {s["id"]: s for s in sources}
    html_path = os.path.join(ROOT, by_id["wiki-candidates"]["local_path"])
    ebc_txt = os.path.join(ROOT, by_id["ebc-list"]["text_path"])

    ridings, wiki_cands = parse_wiki_tables(html_path)
    n_inc = apply_incumbents(html_path, ridings, wiki_cands)
    known_names = {r["name"] for r in ridings}
    ebc = parse_ebc_layout(open(ebc_txt, encoding="utf-8").read(), known_names) if \
        os.path.exists(ebc_txt) else {}
    ebc_by_ride: dict[str, dict[str, str]] = {}
    for (rn, nn), aff in ebc.items():
        ebc_by_ride.setdefault(rn, {})[nn] = aff

    candidates = []
    for c in wiki_cands:
        kind, slug = PARTY_NORM.get(c["party_col"], ("other", None))
        if slug and slug not in CONTRACT:
            slug = None
        rn = norm_riding(c["riding_slug"].replace("-", " "))
        ebc_aff = ebc_by_ride.get(rn, {}).get(norm_name(c["name"]))
        nominated = ebc_aff is not None
        label = BALLOT_LABEL.get(slug) if slug else c["party_col"]
        candidates.append({
            "id": f"rdg-{c['riding_slug']}-{slugify(c['name'])}",
            "riding_slug": c["riding_slug"],
            "name": c["name"],
            "party_slug": slug,
            "party_label": label,
            "party_col": c["party_col"],
            "affiliation": kind,
            "incumbent": c.get("incumbent", False),
            "registered": bool(c["registered_wiki"]),
            "status": "nominated" if nominated else "declared",
            "source_id": "wiki-candidates",
            "source_url": by_id["wiki-candidates"]["url"],
            "ebc_source_id": "ebc-list" if nominated else None,
            "version": version,
            "fetched_at": by_id["wiki-candidates"]["fetched_at"],
        })
    candidates.sort(key=lambda c: (c["riding_slug"], c["name"]))

    os.makedirs(OUTDIR, exist_ok=True)
    json.dump(ridings, open(os.path.join(OUTDIR, "ridings.json"), "w"), indent=2)
    json.dump(candidates, open(os.path.join(OUTDIR, "candidates.json"), "w"), indent=2)

    report = {
        "version": version,
        "built_at": now_iso(),
        "sources": [{"id": s["id"], "url": s["url"], "sha256": s["sha256"],
                     "archive_url": s["archive_url"], "fetched_at": s["fetched_at"]}
                    for s in sources],
        "ridings": len(ridings),
        "candidates": len(candidates),
        "incumbents": n_inc,
        "nominated": sum(1 for c in candidates if c["status"] == "nominated"),
        "declared": sum(1 for c in candidates if c["status"] == "declared"),
        "registered_wiki": sum(1 for c in candidates if c["registered"]),
        "ebc_rows_parsed": len(ebc),
        "by_party": {},
        "by_affiliation": {},
        "ridings_without_candidates": [r["slug"] for r in ridings
                                       if not any(c["riding_slug"] == r["slug"] for c in candidates)],
        "registered_not_confirmed": [f"{c['riding_slug']}/{c['name']}"
                                     for c in candidates
                                     if c["registered"] and c["status"] != "nominated"],
        "confirmed_not_registered": [f"{c['riding_slug']}/{c['name']}"
                                     for c in candidates
                                     if not c["registered"] and c["status"] == "nominated"],
    }
    for c in candidates:
        report["by_party"][c["party_label"]] = report["by_party"].get(c["party_label"], 0) + 1
        report["by_affiliation"][c["affiliation"]] = report["by_affiliation"].get(c["affiliation"], 0) + 1
    json.dump(report, open(os.path.join(OUTDIR, "build-report.json"), "w"), indent=2)
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["fetch", "build", "all", "report"])
    ap.add_argument("--version", default=VERSION)
    ap.add_argument("--no-archive", action="store_true")
    a = ap.parse_args()

    if a.stage in ("fetch", "all"):
        print("fetch:")
        stage_fetch(archive=not a.no_archive)
    if a.stage in ("build", "all"):
        print("build:")
        print(json.dumps(stage_build(a.version), indent=2))
    if a.stage == "report":
        path = os.path.join(OUTDIR, "build-report.json")
        if os.path.exists(path):
            print(json.dumps(json.load(open(path)), indent=2))
        else:
            print("no build-report.json yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
