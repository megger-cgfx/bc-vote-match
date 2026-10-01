#!/usr/bin/env python3
"""fetch_manifest.py — bulk-fetch a manifest of sources into a party raw dir.

Usage:
  python3 agents/fetch_manifest.py data/manifests/centrebc.json [--force]
  python3 agents/fetch_manifest.py data/manifests/centrebc.json --archive-only

Manifest shape:
  {"party_slug": "centrebc",
   "sources": [{"url": "...", "type": "release", "title": "...", "published": "2026-09-22"}]}

Writes data/raw/<party>/<party>-NNNN.html|.txt and sources.json records exactly
per docs/SCHEMA.md (plus a non-schema `fetch_via` field recording whether the
body came from the live page or a Wayback snapshot). Resumable: URLs already in
sources.json are skipped unless --force.
"""
import argparse, hashlib, json, os, sys, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_source as fs  # noqa: E402

ROOT = fs.ROOT


def load_sources(spath):
    if os.path.exists(spath):
        try:
            return json.load(open(spath))
        except Exception:
            return []
    return []


def save_sources(spath, recs):
    recs = sorted(recs, key=lambda r: r["id"])
    json.dump(recs, open(spath, "w"), indent=2)


def do_fetch(job, outdir, lock):
    i, src = job
    sid = src["_id"]
    rec = {
        "id": sid, "party_slug": src["party_slug"], "type": src["type"],
        "title": src["title"], "url": src["url"], "published": src.get("published", ""),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": "", "local_path": "", "text_path": "", "archive_url": None,
        "fetch_via": "",
    }
    try:
        raw, ctype, via = fs.fetch(src["url"])
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {sid} {src['url']} :: {type(e).__name__}: {e}", flush=True)
        return None
    hp = os.path.join(outdir, f"{sid}.html")
    with open(hp, "wb") as f:
        f.write(raw)
    rec["sha256"] = hashlib.sha256(raw).hexdigest()
    rec["local_path"] = os.path.relpath(hp, ROOT)
    text = fs.to_text(raw, ctype)
    if text:
        tp = os.path.join(outdir, f"{sid}.txt")
        with open(tp, "w", encoding="utf-8") as f:
            f.write(text)
        rec["text_path"] = os.path.relpath(tp, ROOT)
    rec["fetch_via"] = via
    print(f"OK   {sid} {len(raw):>8}B via={via} {src['url']}", flush=True)
    return rec


def do_archive(rec):
    try:
        url = fs.wayback(rec["url"])
        rec["archive_url"] = url
        print(f"ARCH {rec['id']} -> {url}", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"ARCH-FAIL {rec['id']} {e}", flush=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--archive-only", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()

    man = json.load(open(a.manifest))
    party = man["party_slug"]
    outdir = os.path.join(ROOT, "data", "raw", party)
    os.makedirs(outdir, exist_ok=True)
    spath = os.path.join(outdir, "sources.json")
    existing = load_sources(spath)
    have = {r["url"]: r for r in existing if r.get("sha256")}

    if a.archive_only:
        need = [r for r in existing if not r.get("archive_url")]
        print(f"archiving {len(need)} records")
        with ThreadPoolExecutor(max_workers=3) as ex:
            list(ex.map(do_archive, need))
        save_sources(spath, existing)
        return

    todo = [s for s in man["sources"]
            if a.force or s["url"] not in have or not have[s["url"]].get("sha256")]
    # continue the numeric id sequence past anything already stored
    start = 1
    for r in existing:
        try:
            start = max(start, int(r["id"].split("-")[-1]) + 1)
        except Exception:
            pass
    for n, s in enumerate(todo):
        s["_id"] = f"{party}-{start + n:04d}"
        s["party_slug"] = party
    print(f"{len(todo)} to fetch, {len(existing)} already stored")

    got = []
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for rec in ex.map(lambda j: do_fetch(j, outdir, None), list(enumerate(todo))):
            if rec:
                got.append(rec)
    merged = {r["url"]: r for r in existing}
    for r in got:
        merged[r["url"]] = r
    save_sources(spath, list(merged.values()))
    print(f"stored {len(got)} new / {len(merged)} total in {spath}")


if __name__ == "__main__":
    main()
