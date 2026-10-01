#!/usr/bin/env python3
"""add_pdf_source.py — register an already-downloaded PDF as a source record.

Copies the PDF into data/raw/<party>/<id>.pdf, extracts text with pdftotext
(<id>.txt), sha256-hashes it, best-effort archives the URL, and appends a
record to sources.json per docs/SCHEMA.md.

Usage:
  python3 agents/add_pdf_source.py --party ndp --id ndp-0032 --src /tmp/x.pdf \
      --url https://... --type platform --title "..." [--published 2026-09-01]
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def wayback(url, timeout=45):
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
    ap.add_argument("--id", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--type", default="other")
    ap.add_argument("--title", default="")
    ap.add_argument("--published", default="")
    ap.add_argument("--no-archive", action="store_true")
    a = ap.parse_args()

    outdir = os.path.join(ROOT, "data", "raw", a.party)
    os.makedirs(outdir, exist_ok=True)
    pdf_path = os.path.join(outdir, f"{a.id}.pdf")
    shutil.copyfile(a.src, pdf_path)
    raw = open(pdf_path, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()

    txt_path = os.path.join(outdir, f"{a.id}.txt")
    text = ""
    try:
        text = subprocess.run(["pdftotext", pdf_path, "-"], capture_output=True, timeout=180).stdout.decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001
        print(f"pdftotext failed: {e}", file=sys.stderr)
    if text.strip():
        open(txt_path, "w", encoding="utf-8").write(text)
        text_rel = os.path.relpath(txt_path, ROOT)
    else:
        text_rel = ""

    rec = {
        "id": a.id, "party_slug": a.party, "type": a.type, "title": a.title,
        "url": a.url, "published": a.published,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha,
        "local_path": os.path.relpath(pdf_path, ROOT),
        "text_path": text_rel,
        "archive_url": None if a.no_archive else wayback(a.url),
        "fetch_via": "live",
    }
    spath = os.path.join(outdir, "sources.json")
    existing = json.load(open(spath)) if os.path.exists(spath) else []
    existing = [r for r in existing if r.get("url") != a.url and r.get("id") != a.id] + [rec]
    json.dump(existing, open(spath, "w"), indent=2)
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
