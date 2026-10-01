#!/usr/bin/env python3
"""repair_sources.py — re-fetch any source record whose local file is missing
or empty, writing back to the exact recorded path and refreshing sha/text.

Usage: python3 agents/repair_sources.py --party ndp
"""
import argparse, hashlib, json, os, re, sys, urllib.request, urllib.parse
from datetime import datetime, timezone
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out, self._skip = [], 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"): self._skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip: self._skip -= 1
    def handle_data(self, data):
        if not self._skip and data.strip(): self.out.append(data.strip())


def to_text(raw):
    if raw[:4] == b"%PDF":
        return None
    p = _Text(); p.feed(raw.decode("utf-8", "replace"))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(p.out))


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA_BROWSER,
                                              "Accept": "*/*",
                                              "Accept-Language": "en-CA,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--party", required=True)
    ap.add_argument("--ids", default="", help="comma-separated ids to force re-fetch")
    a = ap.parse_args()
    force = {i.strip() for i in a.ids.split(",") if i.strip()}
    outdir = os.path.join(ROOT, "data", "raw", a.party)
    spath = os.path.join(outdir, "sources.json")
    recs = json.load(open(spath))
    fixed = 0
    for r in recs:
        lp = os.path.join(ROOT, r.get("local_path") or "")
        ok = (r.get("local_path") and os.path.exists(lp) and os.path.getsize(lp) > 0)
        if ok and r["id"] not in force:
            continue
        try:
            raw = get(r["url"])
        except Exception as e:  # noqa: BLE001
            print(f"STILL FAILING {r['id']} {r['url']}: {e}", file=sys.stderr)
            continue
        ext = ".pdf" if raw[:4] == b"%PDF" else ".html"
        lp = os.path.join(outdir, r["id"] + ext)
        open(lp, "wb").write(raw)
        r["local_path"] = os.path.relpath(lp, ROOT)
        r["sha256"] = hashlib.sha256(raw).hexdigest()
        r["fetched_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        r["fetch_via"] = "live"
        txt = to_text(raw)
        if txt:
            tp = os.path.join(outdir, r["id"] + ".txt")
            open(tp, "w", encoding="utf-8").write(txt)
            r["text_path"] = os.path.relpath(tp, ROOT)
        else:
            r["text_path"] = ""
        fixed += 1
        print(f"repaired {r['id']} -> {r['local_path']} ({len(raw)} bytes)")
    json.dump(recs, open(spath, "w"), indent=2)
    print(f"repaired {fixed} record(s)")


if __name__ == "__main__":
    main()
