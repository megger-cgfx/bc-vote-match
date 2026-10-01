#!/usr/bin/env bash
# build-cards.sh — regenerate and rasterise the marketing director's share cards.
#
#   bash marketing/tools/build-cards.sh
#
# Two things to know:
#   1. make-director-cards.py emits SVG source. render-card.js rasterises it at density 72,
#      which is what makes the PNG land on the exact requested pixel dimensions.
#   2. sharp renders SVG text through pango and resolves font-family by NAME via fontconfig,
#      not by file path. If Inter is not installed for the current user, every card silently
#      falls back to a system sans and the layout shifts. So install it first.
set -euo pipefail

cd "$(dirname "$0")/../.."
ROOT="$PWD"

FONT_DIR="$HOME/.local/share/fonts/bcvm"
mkdir -p "$FONT_DIR"
cp -f marketing/assets/fonts/Inter.ttf "$FONT_DIR/Inter.ttf"
fc-cache -f >/dev/null 2>&1

python3 marketing/tools/make-director-cards.py >/dev/null
echo "svg: rebuilt"

render() {
  local name="$1" w="$2" h="$3"
  node marketing/tools/render-card.js \
    "marketing/assets/og/director-${name}.svg" \
    "marketing/assets/og/director-${name}.png" \
    --w "$w" --h "$h" >/dev/null
  echo "png: director-${name}.png ${w}x${h}"
}

render og 1200 630
render x 1600 900
render square 1080 1080
render portrait 1080 1350

echo "fitted sizes:"
for f in marketing/assets/og/director-*.svg; do
  printf '  %-28s %s\n' "$(basename "$f")" "$(grep -o 'font-size="[0-9]*"' "$f" | tr '\n' ' ')"
done
