import json, os, hashlib
from collections import defaultdict
p = "data/raw/ndp"
recs = json.load(open(os.path.join(p, "sources.json")))
byurl, bysha = defaultdict(list), defaultdict(list)
for r in recs:
    byurl[r["url"].rstrip("/").lower()].append(r["id"])
    lp = r.get("local_path")
    if lp and os.path.exists(lp):
        bysha[hashlib.sha256(open(lp, "rb").read()).hexdigest()].append(r["id"])
print("== duplicate urls ==")
for u, ids in byurl.items():
    if len(ids) > 1:
        print(ids, u)
print("== duplicate content ==")
for h, ids in bysha.items():
    if len(ids) > 1:
        print(ids, h[:12])
print("== all urls ==")
for r in recs:
    print(r["id"], r["url"])
