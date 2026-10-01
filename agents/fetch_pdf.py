#!/usr/bin/env python3
"""fetch_pdf.py — fetch one PDF source: save .pdf + .txt (pdftotext), hash, archive.

Usage:
  python3 agents/fetch_pdf.py --party cpb --url https://.../doc.pdf \
      --type policy --title "..." [--published 2026-09-28] [--no-archive]

Writes data/raw/<party>/<party>-NNNN.pdf and .txt and appends a record to
data/raw/<party>/sources.json per docs/SCHEMA.md. Ids continue the party
sequence in sources.json. Prints the record as JSON.
"""
import argparse, hashlib, json, os, subprocess, sys, tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_source as fs  # noqa: E402

ROOT = fs.ROOT


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--party", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--type", default="policy",
                    choices=["platform", "policy", "release", "speech", "hansard", "media", "other"])
    ap.add_argument("--title", default="")
    ap.add_argument("--published", default="")
    ap.add_argument("--no-archive", action="store_true")
    a = ap.parse_args()

    outdir = os.path.join(ROOT, "data", "raw", a.party)
    os.makedirs(outdir, exist_ok=True)
    spath = os.path.join(outdir, "sources.json")
    existing = []
    if os.path.exists(spath):
        try:
            existing = json.load(open(spath))
        except Exception:
            existing = []

    start = 1
    for r in existing:
        try:
            start = max(start, int(r["id"].split("-")[-1]) + 1)
        except Exception:
            pass
    sid = f"{a.party}-{start:04d}"

    raw, ctype, via = fs.fetch(a.url)
    if raw[:4] != b"%PDF":
        # not actually a PDF (redirect page / block) -> refuse
        print(json.dumps({"id": sid, "error": "not a PDF", "ctype": ctype,
                          "head": raw[:60].decode('latin-1')}), file=sys.stderr)
        sys.exit(1)

    pdf_path = os.path.join(outdir, f"{sid}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(raw)
    sha = hashlib.sha256(raw).hexdigest()

    txt_path = os.path.join(outdir, f"{sid}.txt")
    txt_ok = True
    try:
        subprocess.run(["pdftotext", "-layout", pdf_path, txt_path], check=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        txt_ok = False
        print(f"pdftotext failed: {e}", file=sys.stderr)

    arch = None if a.no_archive else fs.wayback(a.url)

    rec = {
        "id": sid, "party_slug": a.party, "type": a.type, "title": a.title,
        "url": a.url, "published": a.published,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sha256": sha,
        "local_path": os.path.relpath(pdf_path, ROOT),
        "text_path": os.path.relpath(txt_path, ROOT) if txt_ok else "",
        "archive_url": arch,
        "fetch_via": via,
    }
    existing = [r for r in existing if r.get("url") != a.url] + [rec]
    existing = sorted(existing, key=lambda r: r["id"])
    json.dump(existing, open(spath, "w"), indent=2)
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
