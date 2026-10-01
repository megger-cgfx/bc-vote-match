#!/usr/bin/env python3
"""archive_retry.py — best-effort Wayback submission for records with no
archive_url yet. Rewrites sources.json with whatever the archive returns.

Usage: python3 agents/archive_retry.py --party ndp [--timeout 30]
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def wayback(url, timeout):
    try:
        req = urllib.request.Request("https://web.archive.org/save/" + url,
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
            headers={"User-Agent": UA_BROWSER})
        with urllib.request.urlopen(req, timeout=20) as r:
            snap = json.loads(r.read().decode()).get("archived_snapshots", {}).get("closest")
            if snap:
                return snap.get("url")
    except Exception:
        pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--party", required=True)
    ap.add_argument("--timeout", type=int, default=30)
    a = ap.parse_args()
    outdir = os.path.join(ROOT, "data", "raw", a.party)
    spath = os.path.join(outdir, "sources.json")
    recs = json.load(open(spath))
    todo = [r for r in recs if not r.get("archive_url")]
    print(f"{len(todo)} record(s) without an archive_url")
    for r in todo:
        got = wayback(r["url"], a.timeout)
        r["archive_url"] = got
        print(("  OK   " if got else "  none ") + r["id"] + " " + r["url"][:80])
        json.dump(recs, open(spath, "w"), indent=2)
        time.sleep(1)
    still = sum(1 for r in recs if not r.get("archive_url"))
    print(f"done; {still} still unarchived")


if __name__ == "__main__":
    main()
