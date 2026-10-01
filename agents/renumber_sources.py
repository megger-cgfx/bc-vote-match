#!/usr/bin/env python3
"""renumber_sources.py — make <party>/sources.json ids contiguous (party-0001..NNNN)
in list order and rename the local files to match.

Renames via a temp pass so existing names never collide. Idempotent: safe to
re-run after more sources are appended.

Usage: python3 agents/renumber_sources.py --party ndp
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--party", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    outdir = os.path.join(ROOT, "data", "raw", a.party)
    spath = os.path.join(outdir, "sources.json")
    recs = json.load(open(spath))

    # pass 1: move every file to a unique temp name
    moves = []  # (tmp_path, final_path)
    for i, r in enumerate(recs, 1):
        new_id = f"{a.party}-{i:04d}"
        for key in ("local_path", "text_path"):
            rel = r.get(key) or ""
            if not rel:
                continue
            cur = os.path.join(ROOT, rel)
            if not os.path.exists(cur):
                print(f"WARN missing {rel}", file=sys.stderr)
                continue
            ext = os.path.splitext(cur)[1]
            tmp = cur + f".renum.{i}.tmp"
            if not a.dry_run:
                os.replace(cur, tmp)
            moves.append((tmp, os.path.join(outdir, new_id + ext), key, i))

    # pass 2: temp -> final, and rewrite the record
    for tmp, final, key, i in moves:
        new_id = f"{a.party}-{i:04d}"
        if not a.dry_run:
            os.replace(tmp, final)
        rec = recs[i - 1]
        rec[key] = os.path.relpath(final, ROOT)

    for i, r in enumerate(recs, 1):
        r["id"] = f"{a.party}-{i:04d}"

    if not a.dry_run:
        json.dump(recs, open(spath, "w"), indent=2)
    print(f"renumbered {len(recs)} records for {a.party}"
          f"{' (dry run)' if a.dry_run else ''}")


if __name__ == "__main__":
    main()
