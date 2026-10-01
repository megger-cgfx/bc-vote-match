#!/usr/bin/env python3
"""Write resolved archive_url values into sources.json, in place.

Text-level edit: replaces only the `"archive_url": null` token belonging to each
record whose id resolves, preserving every other byte of the file. Then writes
data/archive/ARCHIVE-RETRY.md.
"""
import json
import re
import subprocess
import time

BASE = "."
PARTIES = ["ndp", "cpb", "green", "onebc", "centrebc"]
RESULTS_PATH = f"{BASE}/data/archive/retry-results.json"

results = json.load(open(RESULTS_PATH))

before, after, fixed, failed = {}, {}, {}, {}
for p in PARTIES:
    path = f"{BASE}/data/raw/{p}/sources.json"
    text = open(path).read()
    data = json.loads(text)

    # the k-th `"archive_url": null` in the file is the k-th null record in order
    null_slots = [(m.start(), m.end()) for m in re.finditer(r'"archive_url"\s*:\s*null', text)]
    null_records = [s for s in data if not s.get("archive_url")]
    assert len(null_slots) == len(null_records), f"{p}: {len(null_slots)} slots vs {len(null_records)} records"

    before[p] = {"total": len(data), "archived": len(data) - len(null_records)}

    # splice from the end so earlier offsets stay valid
    edits = []
    for (slot, end), rec in zip(null_slots, null_records):
        r = results.get(rec["id"], {})
        au = r.get("archive_url")
        if au:
            edits.append((slot, end, au))
            fixed.setdefault(p, []).append((rec["id"], au, r.get("note", "")))
        else:
            failed.setdefault(p, []).append((rec["id"], rec["url"], r.get("note", "no attempt logged")))
    for slot, end, au in sorted(edits, reverse=True):
        text = text[:slot] + '"archive_url": ' + json.dumps(au) + text[end:]

    new_data = json.loads(text)
    assert len(new_data) == len(data)
    for old, new in zip(data, new_data):
        for k in old:
            if k != "archive_url":
                assert old[k] == new[k], f"{p}/{old['id']}: field {k} changed!"
    open(path, "w").write(text)
    after[p] = {"total": len(new_data), "archived": sum(1 for s in new_data if s.get("archive_url"))}

still = sum(len(v) for v in failed.values())
lines = []
lines.append("# Wayback Archive Retry Report")
lines.append("")
lines.append(f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
lines.append("")
lines.append("Scope: every source in `data/raw/{{ndp,cpb,green,onebc,centrebc}}/sources.json` whose")
lines.append("`archive_url` was null after the first pass. Only the `archive_url` field was updated;")
lines.append("ids, titles, hashes, local files and all other fields are untouched.")
lines.append("")
lines.append("## Method")
lines.append("- `GET https://web.archive.org/save/<url>` with a descriptive user agent, 150s timeout, following the save redirect to read the capture URL.")
lines.append("- Fallback: `https://archive.org/wayback/available?url=...` (closest existing snapshot), then the CDX API for any existing capture.")
lines.append("- Requests paced 12s apart; round-based retries while the Internet Archive was reachable.")
lines.append("")
lines.append("## Before / after archived counts")
lines.append("")
lines.append("| party | total | archived before | archived after | newly archived | still unarchived |")
lines.append("|---|---|---|---|---|---|")
for p in PARTIES:
    na = len(fixed.get(p, []))
    su = len(failed.get(p, []))
    lines.append(f"| {p} | {before[p]['total']} | {before[p]['archived']} | {after[p]['archived']} | {na} | {su} |")
tot_before = sum(before[p]["archived"] for p in PARTIES)
tot_after = sum(after[p]["archived"] for p in PARTIES)
tot_n = sum(before[p]["total"] for p in PARTIES)
lines.append(f"| **total** | **{tot_n}** | **{tot_before}** | **{tot_after}** | **{tot_after - tot_before}** | **{still}** |")
lines.append("")
lines.append(f"## Succeeded ({tot_after - tot_before})")
lines.append("")
for p in PARTIES:
    if p in fixed:
        lines.append(f"### {p}")
        for sid, au, note in fixed[p]:
            lines.append(f"- `{sid}` -> {au} ({note})")
        lines.append("")
if tot_after - tot_before == 0:
    lines.append("None. The Internet Archive refused every save request during the retry window.")
    lines.append("")
lines.append(f"## Still unarchived ({still})")
lines.append("")
for p in PARTIES:
    if p in failed:
        lines.append(f"### {p}")
        for sid, url, note in failed[p]:
            lines.append(f"- `{sid}` {url} — {note}")
        lines.append("")

subprocess.run(["mkdir", "-p", f"{BASE}/data/archive"])
open(f"{BASE}/data/archive/ARCHIVE-RETRY.md", "w").write("\n".join(lines) + "\n")
print(json.dumps({"before": before, "after": after, "still_unarchived": still}))
