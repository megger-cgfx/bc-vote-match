#!/usr/bin/env python3
"""make-og.py — render public/og.png, the static social share card (1200×630).

Run:  python3 scripts/make-og.py

The site is a static export, so there is no server to render a per-user card. This is
the one card every page points at via Open Graph / Twitter metadata; the *link* carries
the user's answers instead of the image.
"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "og.png")
W, H = 1200, 630

INK = (20, 23, 28)
NAVY = (31, 78, 121)
WHITE = (255, 255, 255)
MUTED = (182, 188, 199)
PARTY_COLORS = ["#F58220", "#1A4C8B", "#3D9B35", "#8A1C1C", "#2E7D8F"]

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def centred(draw, y, text, f, fill):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=f)
    draw.text(((W - (right - left)) / 2 - left, y), text, font=f, fill=fill)
    return bottom - top


def main():
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)

    # Left accent bar in the site accent colour.
    d.rectangle([0, 0, 16, H], fill=NAVY)

    # Title block.
    centred(d, 96, "BC Vote Match", font(BOLD, 84), WHITE)
    centred(d, 214, "See which party matches your views \u2014 BC 2026.", font(REG, 40), MUTED)

    # Mini compass: axes + a few party dots + a "you" dot.
    cx, cy, r = W // 2, 400, 120
    d.line([cx - r, cy, cx + r, cy], fill=(70, 77, 88), width=2)
    d.line([cx, cy - r, cx, cy + r], fill=(70, 77, 88), width=2)
    d.text((cx + r + 8, cy - 8), "economic", font=font(REG, 18), fill=(120, 128, 140))
    d.text((cx + 6, cy - r - 26), "social", font=font(REG, 18), fill=(120, 128, 140))

    dots = [(-0.62, -0.34), (0.55, 0.42), (-0.30, 0.51), (0.28, -0.15), (0.05, 0.30)]
    for (x, y), colour in zip(dots, PARTY_COLORS):
        px, py = cx + x * r, cy + y * r
        d.ellipse([px - 11, py - 11, px + 11, py + 11], fill=colour)
    # The user's dot, outlined so it is visually distinct.
    px, py = cx - 0.12 * r, cy + 0.06 * r
    d.ellipse([px - 13, py - 13, px + 13, py + 13], fill=WHITE, outline=INK, width=3)

    # Footer band.
    d.rectangle([0, H - 74, W, H], fill=NAVY)
    centred(d, H - 56, "party-level \u00b7 every position quoted and archived \u00b7 no accounts, no tracking",
            font(REG, 24), WHITE)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({img.width}x{img.height}, {os.path.getsize(OUT)} bytes)")


if __name__ == "__main__":
    main()
