#!/usr/bin/env python3
"""build-contact-sheet.py — compile every image in the campaign into labelled contact sheets.

    python3 marketing/tools/build-contact-sheet.py [--cols 4] [--tile 400] [--out DIR]

Why this exists: Martin reviews the *curated* selection, but he also wants to see what was NOT
chosen, so that a rejection is a visible decision rather than a silent one. So this builds a
labelled sheet over the whole image tree, not over the winners.

Rules it follows:
  * Nothing is hidden. Every raster image under the scanned roots appears. An image with no
    manifest entry is labelled `unregistered` rather than skipped.
  * Verdicts come from marketing/assets/MANIFEST.jsonl (the campaign manifest every worker
    appends to). Missing entries are a finding, not a crash.
  * SVG sources are rasterised on the fly through marketing/tools/render-card.js so vector work
    is visible on the sheet too.
  * Deterministic: same inputs, same sheet, no timestamps in the pixels.

Output: <out>/sheet-NN.png plus <out>/sheet-index.json (machine-readable tile list).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "marketing", "assets", "MANIFEST.jsonl")
RENDER = os.path.join(ROOT, "marketing", "tools", "render-card.js")
FONT = os.path.join(ROOT, "marketing", "assets", "fonts", "Inter.ttf")
RASTER = (".png", ".jpg", ".jpeg", ".webp", ".gif")

# The whole campaign image surface, so nothing is out of frame by accident.
ROOTS = [
    "marketing/assets",
    "public/previews",
    "public/og.png",
    "src/app",
]

BG = (20, 23, 28)
TILE_BG = (28, 32, 38)
BORDER = (58, 64, 72)
INK = (247, 248, 250)
MUTED = (150, 158, 170)
GOOD = (108, 190, 140)
WARN = (214, 168, 90)
COLD = (140, 148, 160)

VERDICT_COLOR = {
    "selected": GOOD,
    "unselected": MUTED,
    "raw": COLD,
    "superseded": COLD,
    "rejected": WARN,
    "unregistered": WARN,
}


def load_manifest():
    rows = {}
    if not os.path.exists(MANIFEST):
        return rows
    with open(MANIFEST, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            p = obj.get("path")
            if p:
                rows[os.path.normpath(p)] = obj
    return rows


def collect():
    """Every candidate image, repo-relative, sorted. Includes SVG sources."""
    found = []
    for rel in ROOTS:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            found.append(rel)
            continue
        for dirpath, _dirs, files in os.walk(p):
            for fn in sorted(files):
                ext = os.path.splitext(fn)[1].lower()
                if ext in RASTER or ext == ".svg":
                    found.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    # Skip the generated contact sheets themselves, and node_modules noise if a root slips.
    full = [f for f in found if "/contact-sheets/" not in f and "node_modules" not in f]
    return sorted(dict.fromkeys(full))


def rasterise(svg_rel, cache):
    """Rasterise an SVG source to a PNG using the campaign's own renderer."""
    key = hashlib.sha256(svg_rel.encode()).hexdigest()[:16]
    out = os.path.join(cache, f"{key}.png")
    if os.path.exists(out):
        return out
    # No --w/--h here on purpose: render-card.js asserts the rendered size matches the request, and
    # a generic sheet does not know each source's dimensions. Let the SVG declare its own size and
    # thumbnail it afterwards.
    cmd = ["node", RENDER, os.path.join(ROOT, svg_rel), out]
    try:
        subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, timeout=60)
    except Exception as exc:  # a broken source must not kill the sheet
        sys.stderr.write(f"rasterise failed for {svg_rel}: {exc}\n")
        return None
    return out if os.path.exists(out) else None


def font(size, weight=400):
    try:
        f = ImageFont.truetype(FONT, size)
        if weight >= 600:
            try:
                f.set_variation_by_name("SemiBold")
            except Exception:
                pass
        return f
    except OSError:
        return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--tile", type=int, default=420)
    ap.add_argument("--out", default="marketing/06-review/contact-sheets")
    ap.add_argument("--per-sheet", type=int, default=12)
    args = ap.parse_args()

    outdir = os.path.join(ROOT, args.out)
    os.makedirs(outdir, exist_ok=True)
    cache = os.path.join(outdir, ".raster-cache")
    os.makedirs(cache, exist_ok=True)

    man = load_manifest()
    items = collect()

    f_name = font(15, 600)
    f_meta = font(13)
    f_head = font(34, 600)
    f_sub = font(16)

    pads = 18
    tile = args.tile
    img_h = int(tile * 0.62)
    tile_h = img_h + 74
    cols = args.cols
    per = args.per_sheet
    sheets = []
    index = []

    for page, start in enumerate(range(0, len(items), per), start=1):
        chunk = items[start:start + per]
        rows = (len(chunk) + cols - 1) // cols
        head = 86
        W = pads + cols * (tile + pads)
        H = head + rows * (tile_h + pads) + pads
        sheet = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(sheet)

        d.text((pads, 24), "BC Vote Match — M8 campaign image contact sheet", font=f_head, fill=INK)
        d.text(
            (pads, 62),
            "Every image in the campaign, including the ones not chosen. "
            "Verdicts come from marketing/assets/MANIFEST.jsonl.",
            font=f_sub,
            fill=MUTED,
        )

        for i, rel in enumerate(chunk):
            cx = pads + (i % cols) * (tile + pads)
            cy = head + (i // cols) * (tile_h + pads)
            d.rectangle([cx, cy, cx + tile, cy + tile_h], fill=TILE_BG, outline=BORDER)

            src = os.path.join(ROOT, rel)
            show = src
            if rel.lower().endswith(".svg"):
                show = rasterise(rel, cache) or src

            w = h = None
            try:
                with Image.open(show) as im:
                    w, h = im.size
                    thumb = im.convert("RGB")
                    thumb.thumbnail((tile - 20, img_h - 10), getattr(Image, "Resampling", Image).LANCZOS)
                    sheet.paste(
                        thumb,
                        (cx + (tile - thumb.width) // 2, cy + 8 + (img_h - thumb.height) // 2),
                    )
            except Exception as exc:
                d.text((cx + 10, cy + 30), f"unreadable: {exc}", font=f_meta, fill=WARN)

            entry = man.get(os.path.normpath(rel), {})
            verdict = entry.get("verdict", "unregistered")
            col = VERDICT_COLOR.get(verdict, WARN)

            ty = cy + img_h + 8
            name = os.path.basename(rel)
            if len(name) > 42:
                name = name[:39] + "..."
            d.text((cx + 10, ty), name, font=f_name, fill=INK)
            d.text((cx + 10, ty + 20), f"{w}x{h}" if w else "vector", font=f_meta, fill=MUTED)
            d.text((cx + 10, ty + 38), verdict.upper(), font=f_name, fill=col)
            if verdict == "unregistered":
                d.text((cx + 10, ty + 56), "no manifest entry", font=f_meta, fill=WARN)

            index.append({
                "path": rel,
                "sheet": f"sheet-{page:02d}.png",
                "verdict": verdict,
                "width": w,
                "height": h,
                "produced_by": entry.get("produced_by"),
                "rationale": entry.get("rationale"),
                "registered": os.path.normpath(rel) in man,
            })

        outp = os.path.join(outdir, f"sheet-{page:02d}.png")
        sheet.save(outp)
        sheets.append(os.path.relpath(outp, ROOT))

    counts = {}
    for it in index:
        counts[it["verdict"]] = counts.get(it["verdict"], 0) + 1

    summary = {
        "sheets": sheets,
        "images": len(index),
        "verdict_counts": counts,
        "unregistered": [i["path"] for i in index if not i["registered"]],
        "index": os.path.relpath(os.path.join(outdir, "sheet-index.json"), ROOT),
    }
    with open(os.path.join(outdir, "sheet-index.json"), "w", encoding="utf-8") as fh:
        json.dump({"summary": summary, "items": index}, fh, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
