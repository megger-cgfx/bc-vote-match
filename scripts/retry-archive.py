#!/usr/bin/env python3
"""Retry Wayback Machine archiving for sources with a null archive_url.

Round-based: probes IA health first, then walks unresolved URLs. Follows the
save-endpoint redirect to get the capture URL, falls back to the availability
API and CDX for existing captures. Only archive_url is ever written back.
Resumable via data/archive/retry-results.json.
"""
import json
import os
import re
import subprocess
import time
import urllib.parse

BASE = "."
PARTIES = ["ndp", "cpb", "green", "onebc", "centrebc"]
RESULTS_PATH = f"{BASE}/data/archive/retry-results.json"
LOG = "/tmp/retry-archive.log"
UA = "BCVoteMatch-Archiver/1.0 (academic election research; one polite request per source)"
DEADLINE_MIN = 52
PACE = 12          # seconds between sources within a round
OFFLINE_SLEEP = 90 # seconds between health probes while IA is down
MAX_ROUNDS = 6


def log(msg):
    print(msg, flush=True)
    with open(LOG, "a") as f:
        f.write(msg + "\n")


def curl(url, timeout=60, follow=True):
    cmd = ["curl", "-sS", "--max-time", str(timeout), "-A", UA]
    if follow:
        cmd += ["-L", "--max-redirs", "5"]
    cmd += ["-w", "\n__META__%{http_code} %{url_effective}", url]
    p = subprocess.run(cmd, capture_output=True)
    out = p.stdout.decode("utf-8", errors="replace")
    if "__META__" in out:
        body, meta = out.rsplit("__META__", 1)
        parts = meta.strip().split(" ", 1)
        code = int(parts[0]) if parts[0].isdigit() else 0
        eff = parts[1] if len(parts) > 1 else ""
    else:
        body, code, eff = out, 0, ""
    return code, body, eff


WEB_TS = re.compile(r"https?://web\.archive\.org/web/\d{6,14}[a-z_]*/")


def try_save(url):
    code, body, eff = curl(f"https://web.archive.org/save/{url}", timeout=150)
    m = WEB_TS.search(eff)
    if m:
        return eff, f"save ok (http {code})"
    m = WEB_TS.search(body)
    if m:
        return m.group(0) + url, "save ok (body)"
    return None, f"save http {code}"


def try_available(url):
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    code, body, _ = curl(api, timeout=45, follow=False)
    note = f"available http {code}"
    if code == 200:
        try:
            d = json.loads(body)
            c = d.get("archived_snapshots", {}).get("closest") or {}
            if c.get("url"):
                return c["url"], "availability-api closest snapshot"
        except Exception:
            note = "available 200 unparseable"
    cdx = ("https://web.archive.org/cdx/search/cdx?url="
           + urllib.parse.quote(url, safe="") + "&output=json&limit=1&filter=statuscode:200")
    code2, body2, _ = curl(cdx, timeout=45, follow=False)
    if code2 == 200:
        try:
            rows = json.loads(body2)
            if len(rows) > 1 and rows[1]:
                return f"https://web.archive.org/web/{rows[1][1]}/{url}", "cdx existing capture"
        except Exception:
            pass
    return None, f"{note}, cdx http {code2}"


def ia_healthy():
    code, body, _ = curl("https://archive.org/wayback/available?url=example.com", timeout=30, follow=False)
    if code == 200 and "Temporarily Offline" not in body:
        return True
    code2, body2, _ = curl("https://web.archive.org/cdx/search/cdx?url=example.com&output=json&limit=1", timeout=30, follow=False)
    return code2 == 200 and "Temporarily Offline" not in body2


def main():
    start = time.time()
    deadline = start + DEADLINE_MIN * 60

    targets = []
    for p in PARTIES:
        data = json.load(open(f"{BASE}/data/raw/{p}/sources.json"))
        for s in data:
            if not s.get("archive_url"):
                targets.append((p, s["id"], s["url"]))

    results = {}
    if os.path.exists(RESULTS_PATH):
        results = json.load(open(RESULTS_PATH))

    log(f"=== retry-archive start: {len(targets)} targets, "
        f"{sum(1 for v in results.values() if v.get('archive_url'))} already resolved ===")

    for rnd in range(1, MAX_ROUNDS + 1):
        pending = [(p, i, u) for p, i, u in targets if not (results.get(i, {}) or {}).get("archive_url")]
        if not pending:
            break
        # wait for IA to be up
        waits = 0
        while not ia_healthy() and time.time() < deadline:
            waits += 1
            if waits % 5 == 1:
                log(f"[round {rnd}] IA not healthy, waiting...")
            time.sleep(OFFLINE_SLEEP)
        if time.time() >= deadline:
            break

        log(f"[round {rnd}] {len(pending)} unresolved")
        for n, (party, sid, url) in enumerate(pending, 1):
            if time.time() >= deadline:
                log("deadline reached mid-round")
                break
            entry = results.get(sid, {"party": party, "url": url})
            entry.setdefault("attempts", 0)
            entry["attempts"] += 1

            archive, note = try_save(url)
            if not archive:
                a2, n2 = try_available(url)
                note = f"{note}; {n2}"
                archive = a2

            if archive:
                entry["archive_url"] = archive
                entry["note"] = note
                log(f"[round {rnd} {n}/{len(pending)}] {sid} OK {archive} ({note})")
            else:
                entry["archive_url"] = None
                entry["note"] = note
                log(f"[round {rnd} {n}/{len(pending)}] {sid} FAIL ({note})")
            results[sid] = entry
            with open(RESULTS_PATH, "w") as f:
                json.dump(results, f, indent=2)
            time.sleep(PACE)

    ok = sum(1 for v in results.values() if v.get("archive_url"))
    log(f"=== DONE rounds: {ok} archived, {len(results) - ok} unresolved ===")


if __name__ == "__main__":
    main()
