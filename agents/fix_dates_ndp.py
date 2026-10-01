import json, os
p = "data/raw/ndp/sources.json"
recs = json.load(open(p))
fix = {"ndp-0035": "", "ndp-0039": "2026-06-16", "ndp-0033": "2024-10-03"}
for r in recs:
    if r["id"] in fix:
        r["published"] = fix[r["id"]]
json.dump(recs, open(p, "w"), indent=2)
for r in recs:
    print(r["id"], repr(r.get("published")), r["type"], (r.get("title") or "")[:55])
