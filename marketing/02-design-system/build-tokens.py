#!/usr/bin/env python3
"""Generate tokens.css from tokens.json.

tokens.json is the single source of truth. This script is the only sanctioned way
to turn it into CSS custom properties, so no hand-written hex or px value ever has
to appear in a stylesheet: stylesheets consume the var() names emitted here.

Usage:  python3 build-tokens.py [tokens.json] [tokens.css]
"""
import json
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "tokens.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "tokens.css"

doc = json.load(open(SRC, encoding="utf-8"))


def dash(path):
    return path.replace(".", "-")


def leaves(node, path=""):
    """Yield (dotted_path, leaf) for every {'value','type'} object in the tree."""
    if isinstance(node, dict):
        if "value" in node and "type" in node:
            yield path, node
            return
        for k, v in node.items():
            if k.startswith("_"):
                continue
            yield from leaves(v, f"{path}.{k}" if path else k)


all_leaves = dict(leaves(doc))

# ---------------------------------------------------------------- light scope
light = []


def add(name, value):
    light.append((name, value))


for path, leaf in all_leaves.items():
    parts = path.split(".")
    if parts[0] == "color" and parts[1] != "dark":
        add(f"--color-{dash('.'.join(parts[1:]))}", leaf["value"])
    elif parts[0] == "font" and parts[1] == "family":
        add(f"--font-{parts[2]}", leaf["value"])
    elif parts[0] == "font" and parts[1] == "weight":
        add(f"--font-weight-{parts[2]}", leaf["value"])
    elif parts[0] == "font" and parts[1] == "size":
        step = parts[2]
        add(f"--font-size-{step}", leaf["value"])
        for extra, css in (("lineHeight", f"--line-height-{step}"),
                           ("letterSpacing", f"--letter-spacing-{step}")):
            if extra in leaf:
                add(css, leaf[extra])
    elif parts[0] == "space":
        add(f"--space-{parts[1]}", leaf["value"])
    elif parts[0] == "radius":
        add(f"--radius-{parts[1]}", leaf["value"])
    elif parts[0] == "border" and parts[1] == "width":
        add(f"--border-width-{parts[2]}", leaf["value"])
    elif parts[0] == "border" and parts[1] == "focus-offset":
        add("--border-focus-offset", leaf["value"])
    elif parts[0] == "shadow":
        add(f"--shadow-{parts[1]}", leaf["value"])
    elif parts[0] == "z":
        add(f"--z-{parts[1]}", leaf["value"])
    elif parts[0] == "motion" and parts[1] == "duration":
        v = leaf["value"]
        add(f"--duration-{parts[2]}", f"{v}ms" if isinstance(v, (int, float)) else v)
    elif parts[0] == "motion" and parts[1] == "easing":
        add(f"--easing-{parts[2]}", leaf["value"])
    # typography.* composites are documented in the README, not emitted as vars.

# ---------------------------------------------------------------- dark scope
dark = []
for path, leaf in all_leaves.items():
    parts = path.split(".")
    if parts[:2] == ["color", "dark"]:
        dark.append((f"--color-{dash('.'.join(parts[2:]))}", leaf["value"]))
    elif parts[0] == "shadow" and leaf.get("dark") and leaf["dark"] != "none":
        dark.append((f"--shadow-{parts[1]}", leaf["dark"]))

# ---------------------------------------------------------------- emit
lines = [
    "/* tokens.css — GENERATED FILE. DO NOT EDIT BY HAND.",
    f" * Source: {SRC} (the single source of truth for every colour, size and duration).",
    " * Regenerate: python3 build-tokens.py",
    " * Consume the var() names below; never re-declare a raw hex or px in a component. */",
    "",
    ":root {",
]
lines += [f"  {n}: {v};" for n, v in light]
lines += ["}", "", '/* Dark theme: explicit opt-in ... */', '[data-theme="dark"] {']
lines += [f"  {n}: {v};" for n, v in dark]
lines += ["}", "", "/* ... and system preference, unless the page has opted out. */",
          "@media (prefers-color-scheme: dark) {",
          '  :root:not([data-theme="light"]) {']
lines += [f"    {n}: {v};" for n, v in dark]
lines += ["  }", "}", "", "/* Reduced motion overrides every duration token. */",
          "@media (prefers-reduced-motion: reduce) {",
          "  :root {",
          "    --duration-instant: 0.01ms;",
          "    --duration-fast: 0.01ms;",
          "    --duration-base: 0.01ms;",
          "    --duration-slow: 0.01ms;",
          "    --duration-slower: 0.01ms;",
          "  }",
          "}", ""]

open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print(f"wrote {OUT}: {len(light)} light vars, {len(dark)} dark overrides")
