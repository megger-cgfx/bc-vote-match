import json, os
p = "data/raw/ndp"
recs = json.load(open(os.path.join(p, "sources.json")))
for r in recs:
    tp = r.get("text_path") or ""
    head = ""
    if tp and os.path.exists(tp):
        lines = [l.strip() for l in open(tp, encoding="utf-8", errors="replace") if l.strip()]
        head = " | ".join(lines[:2])[:100]
    lp = r.get("local_path") or ""
    size = os.path.getsize(lp) if lp and os.path.exists(lp) else -1
    print(f"{r['id']} {r['type']:<8} {size:>8} {'A' if r.get('archive_url') else '-'} :: {head}")
