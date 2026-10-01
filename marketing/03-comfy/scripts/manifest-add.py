#!/usr/bin/env python3
"""manifest-add.py — append honest rows to marketing/assets/MANIFEST.jsonl.

Append-only: reads the decision file given on argv[1] (a JSON list of row dicts),
computes sha256 and real PNG dimensions for each row's path, fills in the fixed
campaign fields, and appends one JSON line per row. Never rewrites existing lines.

    python3 marketing/03-comfy/scripts/manifest-add.py decisions.json

Row dict fields you provide: path, goal, kind, verdict, rationale, model, prompt,
seed, sampler, steps, cfg (provenance block; optional for non-generated renders).
Fixed fields filled here: produced_by, created (file mtime), width, height, sha256.
"""
import hashlib
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MANIFEST = os.path.join(ROOT, "marketing", "assets", "MANIFEST.jsonl")
PRODUCED_BY = "flower (gpu-pipeline worker)"


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")
    return None, None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(sys.argv[1]) as fh:
        rows = json.load(fh)
    lines = []
    for r in rows:
        p = os.path.join(ROOT, r["path"])
        if not os.path.isfile(p):
            raise SystemExit("missing file for manifest row: " + r["path"])
        w, h = png_size(p)
        row = {
            "path": r["path"],
            "produced_by": PRODUCED_BY,
            "goal": r["goal"],
            "created": r.get("created") or time.strftime(
                "%Y-%m-%dT%H:%M:%S%z", time.localtime(os.path.getmtime(p))),
            "kind": r["kind"],
            "verdict": r["verdict"],
            "rationale": r["rationale"],
            "width": r.get("width", w),
            "height": r.get("height", h),
            "sha256": r.get("sha256") or sha256(p),
        }
        for k in ("model", "prompt", "seed", "sampler", "steps", "cfg", "source_format"):
            if k in r and r[k] is not None:
                row[k] = r[k]
        lines.append(json.dumps(row, ensure_ascii=False))
    with open(MANIFEST, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(json.dumps({"appended": len(lines)}))


if __name__ == "__main__":
    main()
