#!/usr/bin/env python3
"""fetch_pdf_source.py — PDF variant of agents/fetch_source.py.

The helper does not extract PDF text; per docs/SCHEMA.md the record shape is
identical. Usage:
  python3 agents/fetch_pdf_source.py --id green-0091 --url <pdf-url> \
      --type platform --title "..." [--published YYYY-MM-DD]
Writes data/raw/green/<id>.pdf + <id>.txt (via pdftotext), appends record to
data/raw/green/sources.json, best-effort Wayback submit. Prints the record.
"""
import argparse, hashlib, json, os, subprocess, sys, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "BCVoteMatch/0.1 (civic research; contact: editor@bcvotematch.ca)"


def wayback(url, timeout=45):
    try:
        req = urllib.request.Request(
            "https://web.archive.org/save/" + url,
            headers={"User-Agent": UA, "Accept": "*/*"})
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
    ap.add_argument("--id", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--type", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--published", default="")
    a = ap.parse_args()

    outdir = os.path.join(ROOT, "data", "raw", "green")
    os.makedirs(outdir, exist_ok=True)
    pdf_path = os.path.join(outdir, f"{a.id}.pdf")
    req = urllib.request.Request(a.url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    if raw[:4] != b"%PDF":
        print(json.dumps({"id": a.id, "error": "not a PDF", "url": a.url}), file=sys.stderr)
        sys.exit(1)
    with open(pdf_path, "wb") as f:
        f.write(raw)
    sha = hashlib.sha256(raw).hexdigest()

    text_path = ""
    txt_file = os.path.join(outdir, f"{a.id}.txt")
    try:
        subprocess.run(["pdftotext", pdf_path, txt_file], check=True, timeout=120)
        text_path = os.path.relpath(txt_file, ROOT)
    except Exception as e:
        print(json.dumps({"id": a.id, "warn": f"pdftotext failed: {e}"}), file=sys.stderr)

    rec = {
        "id": a.id, "party_slug": "green", "type": a.type, "title": a.title,
        "url": a.url, "published": a.published,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha,
        "local_path": os.path.relpath(pdf_path, ROOT),
        "text_path": text_path,
        "archive_url": wayback(a.url),
    }
    spath = os.path.join(outdir, "sources.json")
    existing = []
    if os.path.exists(spath):
        try:
            existing = json.load(open(spath))
        except Exception:
            existing = []
    existing = [r for r in existing if r.get("url") != a.url and r.get("id") != a.id] + [rec]
    json.dump(existing, open(spath, "w"), indent=2)
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    import urllib.parse  # noqa
    main()
