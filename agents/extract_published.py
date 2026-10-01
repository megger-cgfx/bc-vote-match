#!/usr/bin/env python3
"""extract_published.py — fill the `published` date on each record from the
page text (first date-looking string) or from the URL (news sites). Only fills
records where published is empty; never overwrites.

Usage: python3 agents/extract_published.py --party ndp
"""
import argparse, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHS = ("January February March April May June July August September October November December").split()
LONG = re.compile(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2}),?\s+(\d{4})\b")
ABBR = re.compile(r"\b(" + "|".join(m[:3] for m in MONTHS) + r")\.?\s+(\d{1,2}),?\s+(\d{4})\b", re.I)
ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
URLDATE = re.compile(r"/(20\d{2})/(\d{2})/(\d{2})/")


def find(txt, url):
    m = URLDATE.search(url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    head = "\n".join(txt.splitlines()[:40])
    for rx in (LONG, ISO):
        mm = rx.search(head)
        if mm:
            if rx is LONG:
                return f"{mm.group(3)}-{MONTHS.index(mm.group(1)) + 1:02d}-{int(mm.group(2)):02d}"
            return f"{mm.group(1)}-{mm.group(2)}-{mm.group(3)}"
    mm = ABBR.search(head)
    if mm:
        name = [x for x in MONTHS if x.lower().startswith(mm.group(1).lower())]
        if name:
            return f"{mm.group(3)}-{MONTHS.index(name[0]) + 1:02d}-{int(mm.group(2)):02d}"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--party", required=True)
    a = ap.parse_args()
    outdir = os.path.join(ROOT, "data", "raw", a.party)
    spath = os.path.join(outdir, "sources.json")
    recs = json.load(open(spath))
    n = 0
    for r in recs:
        if r.get("published"):
            continue
        tp = r.get("text_path") or ""
        txt = open(os.path.join(ROOT, tp), encoding="utf-8", errors="replace").read() if tp and os.path.exists(os.path.join(ROOT, tp)) else ""
        d = find(txt, r["url"])
        if d:
            r["published"] = d
            n += 1
            print(f"  {r['id']} -> {d}  {r['url'][:70]}")
    json.dump(recs, open(spath, "w"), indent=2)
    print(f"filled {n} date(s)")


if __name__ == "__main__":
    main()
