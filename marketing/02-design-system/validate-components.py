#!/usr/bin/env python3
"""validate-components.py — checks the M8 component spec against the token source of truth.

Checks:
 1. m8-components.tokens.json parses and every token path resolves to a leaf in tokens.json.
 2. Every component in the manifest has a non-empty token list.
 3. m8-components.md contains zero raw hex colours (the "no raw hex outside tokens.json" rule).
 4. Raw px occurrences in the markdown are reported, grouped by section, so any *unflagged*
    literal can be reviewed (component constants and proposed breakpoints are expected and
    are marked with the warning glyph in the doc).

Usage: python3 validate-components.py [tokens.json] [manifest.json] [spec.md]
Exits non-zero if any hard check fails.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def leaf_paths(tokens, prefix=""):
    """Collect every token leaf path. A leaf is a dict with a 'value' key.
    Composite groups in 'typography' are also valid named tokens even without a 'value'."""
    paths = set()
    if not isinstance(tokens, dict):
        return paths
    if "value" in tokens:
        paths.add(prefix.rstrip("."))
        return paths
    for key, val in tokens.items():
        if key.startswith("_") or key == "meta":
            continue
        child = f"{prefix}{key}."
        if key == "typography":
            # composites: every entry is a named style, not a leaf with 'value'
            if isinstance(val, dict):
                for name in val:
                    if not name.startswith("_"):
                        paths.add(f"typography.{name}")
            continue
        paths |= leaf_paths(val, child)
    return paths


def main():
    tokens_path = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "tokens.json")
    manifest_path = sys.argv[2] if len(sys.argv) > 2 else str(HERE / "m8-components.tokens.json")
    spec_path = sys.argv[3] if len(sys.argv) > 3 else str(HERE / "m8-components.md")

    failures = []
    tokens = load(tokens_path)
    manifest = load(manifest_path)
    leaves = leaf_paths(tokens)

    # 1. every manifest token resolves
    all_refs = list(manifest.get("global", []))
    for comp, refs in manifest.get("components", {}).items():
        all_refs.extend(refs)
    unknown = sorted({r for r in all_refs if r not in leaves})
    if unknown:
        failures.append("unresolved token names: " + ", ".join(unknown))
    print(f"[1] token names resolve      : {'PASS' if not unknown else 'FAIL'} "
          f"({len(all_refs)} references, {len(set(all_refs))} unique, {len(leaves)} leaves in tokens.json)")

    # 2. components non-empty
    empty = [c for c, r in manifest.get("components", {}).items() if not r]
    if empty:
        failures.append("components with no tokens: " + ", ".join(empty))
    print(f"[2] components have tokens   : {'PASS' if not empty else 'FAIL'} "
          f"({len(manifest.get('components', {}))} components)")

    # 3. no raw hex in the spec
    spec = Path(spec_path).read_text(encoding="utf-8")
    hexes = re.findall(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9A-Za-z_-])", spec)
    if hexes:
        failures.append(f"raw hex in spec: {sorted(set(hexes))}")
    print(f"[3] zero raw hex in spec     : {'PASS' if not hexes else 'FAIL'} "
          f"({len(hexes)} found)")

    # 4. report px occurrences by section heading (advisory)
    px_by_section = {}
    section = "(top)"
    for line in spec.splitlines():
        if line.startswith("#"):
            section = line.lstrip("# ").strip() or section
        for m in re.finditer(r"\b\d+(?:\.\d+)?px\b", line):
            px_by_section.setdefault(section, set()).add(m.group(0))
    total_px = sum(len(v) for v in px_by_section.values())
    print(f"[4] raw px occurrences       : advisory ({total_px} distinct values in "
          f"{len(px_by_section)} sections — expected only in the flagged breakpoint/")
    print("                                container/control-constant text)")

    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  -", f)
        return 1
    print("All hard checks PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
