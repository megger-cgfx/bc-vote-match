import json, re

def srgb_to_lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lum(h):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return 0.2126*srgb_to_lin(r) + 0.7152*srgb_to_lin(g) + 0.0722*srgb_to_lin(b)

def cr(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi+0.05)/(lo+0.05), 2)

doc = json.load(open("tokens.json"))
print("PASS  JSON parses cleanly")

def walk(node, path=""):
    out = []
    if isinstance(node, dict):
        if "value" in node and "type" in node:
            out.append((path, node))
        else:
            for k, v in node.items():
                if k.startswith("_") or k in ("contrast", "intent", "background", "aliasOf", "aliasOf_existing", "fallbacks"):
                    continue
                out += walk(v, f"{path}.{k}" if path else k)
    return out

leaves = walk(doc)
by_path = dict(leaves)
colors = [(p, n) for p, n in leaves if n["type"] == "color"]
print(f"PASS  {len(leaves)} leaf tokens, {len(colors)} colour tokens")

no_contrast = [p for p, n in colors if "contrast" not in n]
print("PASS" if not no_contrast else "FAIL", " every colour token documents contrast intent:", no_contrast or "none missing")

# resolve references used in contrast/background/aliasOf
def resolve(name):
    n = name.strip()
    n = re.sub(r"\s*\(.*$", "", n)
    n = re.sub(r"\s+as\s+.*$", "", n)
    n = n.rstrip(".")
    return n in by_path

bad = []
for p, n in colors:
    for c in n.get("contrast", []):
        a = c["against"]
        if a.startswith("color.") and not resolve(a):
            bad.append((p, a))
    if "aliasOf" in n and n["aliasOf"] not in by_path:
        bad.append((p, n["aliasOf"]))
print("PASS" if not bad else "FAIL", " all colour cross-references resolve:", bad or "all resolve")

bg_missing = []
for p, n in leaves:
    if n.get("type") == "color" and "background" in n:
        bgs = n["background"] if isinstance(n["background"], list) else [n["background"]]
        for b in bgs:
            if not resolve(b):
                bg_missing.append((p, b))
print("PASS" if not bg_missing else "FAIL", " text-token background targets resolve:", bg_missing or "all resolve")

# contrast spot-check of every quoted ratio against its own declared "against" hex, where the
# against-string names a token we can resolve
mismatch = []
for p, n in colors:
    for c in n.get("contrast", []):
        a = re.sub(r"\s*\(.*$", "", c["against"])
        a = re.sub(r"\s+as\s+.*$", "", a).rstrip(".")
        if a in by_path and str(by_path[a]["value"]).startswith("#") and str(n["value"]).startswith("#"):
            actual = cr(n["value"], by_path[a]["value"])
            if isinstance(c["ratio"], (int, float)) and abs(actual - c["ratio"]) > 0.02:
                mismatch.append((p, a, c["ratio"], actual))
print("PASS" if not mismatch else "FAIL", " quoted ratios match recomputation:", mismatch or "all match")

# groups
print("groups:", [k for k in doc if k != "meta"])

# dark tree must mirror the light tree: every color.dark.* path has a same-named light counterpart
light_paths = {p for p, n in by_path.items() if p.startswith("color.") and not p.startswith("color.dark.")}
dark_paths = {p for p in by_path if p.startswith("color.dark.")}
non_mirrored = sorted(p for p in dark_paths if "color." + p[len("color.dark."):] not in light_paths)
print("PASS" if not non_mirrored else "NOTE", " dark tokens with no light counterpart:",
      non_mirrored or "none — dark mirrors light exactly")
print("dark overrides:", len(dark_paths), "of", len(light_paths), "light colour tokens")

print("type scale steps:", list(doc["font"]["size"].keys()))
print("space steps:", [k for k in doc["space"] if not k.startswith("_")])
