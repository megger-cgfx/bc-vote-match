import json, os, glob
p = "data/raw/ndp"
recs = json.load(open(os.path.join(p, "sources.json")))
print("records:", len(recs))
for r in recs:
    lp = r.get("local_path") or ""
    print(f"{r['id']}  {r['type']:<9} {os.path.getsize(lp) if os.path.exists(lp) else 'MISSING':>8}  {'A' if r.get('archive_url') else '-'}  {'T' if r.get('text_path') else ' '}  {(r.get('title') or '')[:70]}")
files = sorted(glob.glob(os.path.join(p, "ndp-*")))
print("\nfiles on disk:", len(files))
known = {os.path.basename(r["local_path"]) for r in recs}
known |= {os.path.basename(r["text_path"]) for r in recs if r.get("text_path")}
for f in files:
    b = os.path.basename(f)
    if b not in known:
        print("  ORPHAN", b, os.path.getsize(f))
