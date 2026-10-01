#!/usr/bin/env python3
"""fetch_source.py — fetch, save, hash and (best-effort) archive one source.

Usage:
  python3 agents/fetch_source.py --party ndp --url https://bcndp.ca/... \
      --type platform --title "BC NDP Platform" [--published 2026-09-22]

Writes  data/raw/<party>/<party>-NNNN.html|.txt  and appends a record to
data/raw/<party>/sources.json per docs/SCHEMA.md. Prints the record as JSON.
"""
import argparse, hashlib, json, os, re, sys, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "BCVoteMatch/0.1 (civic research; contact: editor@bcvotematch.ca)"
# Cloudflare-fronted party sites (centrebc.ca, conservativebc.ca) 403 on a
# non-browser UA, so a browser UA is tried first, civic UA second.
UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/[IP_ADDRESS] Safari/537.36")
UA_LIST = (UA_BROWSER, UA)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self._skip = [], 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1
    def handle_data(self, data):
        if not self._skip and data.strip():
            self.out.append(data.strip())


def _open(url, ua, timeout, accept="*/*"):
    req = urllib.request.Request(url, headers={
        "User-Agent": ua, "Accept": accept, "Accept-Language": "en-CA,en;q=0.9"})
    return urllib.request.urlopen(req, timeout=timeout)


def fetch(url, timeout=45):
    """Fetch URL. Returns (raw_bytes, content_type, fetch_via).

    Tries the live page first (browser UA, then civic UA); if every direct
    attempt fails, falls back to the closest Wayback snapshot and reports
    fetch_via='archive' so the caller can label the provenance honestly.
    """
    last = None
    for ua in UA_LIST:
        try:
            with _open(url, ua, timeout) as r:
                return r.read(), r.headers.get("Content-Type", ""), "live"
        except Exception as e:  # noqa: BLE001 - any failure falls through
            last = e
    try:
        snap = wayback(url, save=False)
    except Exception:
        snap = None
    if snap:
        try:
            with _open(snap, UA_BROWSER, timeout) as r:
                return r.read(), r.headers.get("Content-Type", ""), "archive"
        except Exception as e:  # noqa: BLE001
            last = e
    raise last if last is not None else RuntimeError(f"fetch failed: {url}")


def to_text(raw, ctype=""):
    body = raw.decode("utf-8", "replace")
    if "pdf" in ctype.lower() or raw[:4] == b"%PDF":
        return None  # caller should run pdftotext separately
    p = _Text(); p.feed(body)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(p.out))


def wayback(url, timeout=45, save=True):
    if save:
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
            headers={"User-Agent": UA})
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
    ap.add_argument("--url", required=True)
    ap.add_argument("--type", default="other",
                    choices=["platform", "policy", "release", "speech", "hansard", "media", "other"])
    ap.add_argument("--title", default="")
    ap.add_argument("--published", default="")
    ap.add_argument("--no-archive", action="store_true")
    a = ap.parse_args()

    outdir = os.path.join(ROOT, "data", "raw", a.party)
    os.makedirs(outdir, exist_ok=True)
    # Index from the highest id already used by any file or record in this dir,
    # so manually added records (e.g. PDFs) never collide with generated ids.
    used = []
    for f in os.listdir(outdir):
        m = re.match(rf"^{a.party}-(\d+)\.", f)
        if m:
            used.append(int(m.group(1)))
    spath = os.path.join(outdir, "sources.json")
    existing = []
    if os.path.exists(spath):
        try:
            existing = json.load(open(spath))
        except Exception:
            existing = []
    for r in existing:
        m = re.match(rf"^{a.party}-(\d+)$", str(r.get("id", "")))
        if m:
            used.append(int(m.group(1)))
    idx = (max(used) + 1) if used else 1
    sid = f"{a.party}-{idx:04d}"

    try:
        raw, ctype, via = fetch(a.url)
    except Exception as e:
        print(json.dumps({"id": sid, "error": str(e), "url": a.url}), file=sys.stderr)
        sys.exit(1)

    html_path = os.path.join(outdir, f"{sid}.html")
    with open(html_path, "wb") as f:
        f.write(raw)
    sha = hashlib.sha256(raw).hexdigest()

    text = to_text(raw, ctype)
    text_path = ""
    if text:
        text_path = os.path.join(outdir, f"{sid}.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

    arch = None if a.no_archive else wayback(a.url)

    rec = {
        "id": sid, "party_slug": a.party, "type": a.type, "title": a.title,
        "url": a.url, "published": a.published,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha,
        "local_path": os.path.relpath(html_path, ROOT),
        "text_path": os.path.relpath(text_path, ROOT) if text_path else "",
        "archive_url": arch,
        "fetch_via": via,
    }
    spath = os.path.join(outdir, "sources.json")
    existing = []
    if os.path.exists(spath):
        try:
            existing = json.load(open(spath))
        except Exception:
            existing = []
    existing = [r for r in existing if r.get("url") != a.url] + [rec]
    json.dump(existing, open(spath, "w"), indent=2)
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    import urllib.parse  # noqa
    main()
