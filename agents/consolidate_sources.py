#!/usr/bin/env python3
"""consolidate_sources.py — dedupe + renumber a party's sources.json.

Other agents are writing into the same shared repo concurrently, which left
duplicate urls and duplicate ids in data/raw/<party>/sources.json. This
dedupes by normalised url (keeping the best record: archived > has text >
larger file), sorts by source priority, renumbers ids contiguously in that
order, and renames the local files to match. Orphan ndp-*.* files that no
record points at are deleted.

Usage: python3 agents/consolidate_sources.py --party ndp
"""
import argparse, glob, hashlib, json, os, shutil, sys
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIORITY = {"platform": 0, "policy": 1, "release": 2, "speech": 3,
            "hansard": 4, "media": 5, "other": 6}


def norm(url):
    s = urlsplit(url)
    return (s.netloc.lower().replace("www.", "") + s.path.rstrip("/")).lower()


def score(r):
    lp = r.get("local_path") or ""
    size = os.path.getsize(os.path.join(ROOT, lp)) if lp and os.path.exists(os.path.join(ROOT, lp)) else 0
    return (1 if r.get("archive_url") else 0, 1 if r.get("text_path") else 0, size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--party", required=True)
    a = ap.parse_args()

    outdir = os.path.join(ROOT, "data", "raw", a.party)
    spath = os.path.join(outdir, "sources.json")
    shutil.copyfile(spath, spath + ".preconsolidate.bak")
    recs = json.load(open(spath))

    # dedupe by normalised url, then by file content hash (a redirect can make
    # two different urls serve the identical page)
    best = {}
    for r in recs:
        k = norm(r["url"])
        if k not in best or score(r) > score(best[k]):
            best[k] = r
    bysha = {}
    for r in list(best.values()):
        lp = os.path.join(ROOT, r.get("local_path") or "")
        if not (r.get("local_path") and os.path.exists(lp)):
            bysha.setdefault("missing:" + r["url"], []).append(r); continue
        h = hashlib.sha256(open(lp, "rb").read()).hexdigest()
        bysha.setdefault(h, []).append(r)
    best = {}
    for h, group in bysha.items():
        winner = sorted(group, key=lambda r: (PRIORITY.get(r.get("type"), 9),
                                              -score(r)[0], -score(r)[2]))[0]
        best[winner["url"]] = winner
    kept = sorted(best.values(), key=lambda r: (PRIORITY.get(r.get("type"), 9),
                                                r.get("published") or "9999-99-99",
                                                r.get("title") or ""))
    dropped = len(recs) - len(kept)

    # pass 1: move every referenced file out of the way
    pend = []
    for i, r in enumerate(kept, 1):
        nid = f"{a.party}-{i:04d}"
        for key in ("local_path", "text_path"):
            rel = r.get(key) or ""
            if not rel:
                continue
            cur = os.path.join(ROOT, rel)
            if not os.path.exists(cur):
                print(f"WARN missing {rel}", file=sys.stderr)
                r[key] = ""
                continue
            tmp = cur + f".cons.{i}.tmp"
            os.replace(cur, tmp)
            pend.append((tmp, os.path.join(outdir, nid + os.path.splitext(cur)[1]), key, i))

    # pass 2: temp -> final
    for tmp, final, key, i in pend:
        os.replace(tmp, final)
        kept[i - 1][key] = os.path.relpath(final, ROOT)

    for i, r in enumerate(kept, 1):
        r["id"] = f"{a.party}-{i:04d}"

    json.dump(kept, open(spath, "w"), indent=2)

    # remove orphans
    referenced = set()
    for r in kept:
        for key in ("local_path", "text_path"):
            if r.get(key):
                referenced.add(os.path.basename(r[key]))
    removed = []
    for f in sorted(glob.glob(os.path.join(outdir, f"{a.party}-*"))):
        b = os.path.basename(f)
        if b.endswith(".tmp") or b.startswith("sources.json"):
            continue
        if b not in referenced:
            os.remove(f)
            removed.append(b)

    print(f"kept {len(kept)} (dropped {dropped} duplicate/no-url records); "
          f"removed {len(removed)} orphan files")
    for b in removed:
        print("  orphan removed:", b)


if __name__ == "__main__":
    main()
