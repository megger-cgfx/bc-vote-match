"""Assert that a perf result JSON contains every metric the acceptance criteria name.

    python -m harness.verify_results results/smoke/perf_*.json

Exit 0 = every required metric present, finite and non-null; 1 = something is
missing (the message names the file and the key).

Required by the task: load time, peak VRAM, prefill tok/s, decode tok/s,
time-to-first-token, and throughput at concurrency 1 and 4 - each measured at
least once, with mean + stddev reported per concurrency.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

BATCH_KEYS = [
    "concurrency",
    "wall_s",
    "aggregate_decode_tps",
    "total_completion_tokens",
    "mean_ttft_s",
    "mean_decode_tps",
    "mean_prefill_tps",
    "per_request",
]
SUMMARY_KEYS = ["aggregate_decode_tps", "ttft_s", "decode_tps_per_stream", "prefill_tps"]


def _bad(v) -> bool:
    return v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v)))


def check(path: str) -> list[str]:
    errs: list[str] = []
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if doc.get("kind") != "perf":
        return []

    label = doc.get("label") or os.path.basename(path)
    if doc.get("status") != "ok":
        errs.append(f"{label}: status={doc.get('status')!r} errors={doc.get('errors')}")
    srv = doc.get("server") or {}
    if _bad(srv.get("load_time_s")):
        errs.append(f"{label}: server.load_time_s is {srv.get('load_time_s')!r}")
    for k in ("environment", "gpu"):
        if doc.get(k) is None:
            errs.append(f"{label}: top-level {k} is null/missing")
    if not (doc.get("gpu", {}) or {}).get("supported"):
        errs.append(
            f"{label}: GPU not detected ({(doc.get('gpu') or {}).get('reason')}) - "
            "peak VRAM is not a hardware measurement on this host"
        )
    elif _bad(doc.get("peak_vram_mb")):
        errs.append(f"{label}: peak_vram_mb is {doc.get('peak_vram_mb')!r}")

    batches = doc.get("batches") or []
    measured = [b for b in batches if not b.get("warmup")]
    if not measured:
        errs.append(f"{label}: no measured (non-warmup) batches")
    for b in batches:
        tag = f"{label}: batch c={b.get('concurrency')} warmup={b.get('warmup')}"
        for k in BATCH_KEYS:
            if k not in b:
                errs.append(f"{tag} missing key {k}")
        for k in ("wall_s", "aggregate_decode_tps", "mean_ttft_s", "mean_decode_tps", "mean_prefill_tps"):
            if _bad(b.get(k)):
                errs.append(f"{tag} {k}={b.get(k)!r}")
        for r in b.get("per_request") or []:
            if r.get("error"):
                errs.append(f"{tag} request failed: {r['error']}")

    for conc in (1, 4):
        got = [b for b in measured if b.get("concurrency") == conc]
        if not got:
            errs.append(f"{label}: no measured concurrency={conc} batch")

    summary = doc.get("summary") or []
    if not isinstance(summary, list) or not summary:
        errs.append(f"{label}: summary missing/empty")
    else:
        by_conc = {s.get("concurrency"): s for s in summary}
        for conc in (1, 4):
            s = by_conc.get(conc)
            if s is None:
                errs.append(f"{label}: summary has no entry for concurrency={conc}")
                continue
            if s.get("repeats", 0) < 2:
                errs.append(f"{label}: summary[c={conc}] has {s.get('repeats')} repeat(s) - stddev unavailable")
            for k in SUMMARY_KEYS:
                st = s.get(k)
                if not isinstance(st, dict):
                    errs.append(f"{label}: summary[c={conc}] missing {k}")
                elif st.get("n", 0) < 1 or _bad(st.get("mean")):
                    errs.append(f"{label}: summary[c={conc}][{k}] = {st}")
                elif s.get("repeats", 0) >= 2 and _bad(st.get("stddev")):
                    errs.append(f"{label}: summary[c={conc}][{k}].stddev = {st.get('stddev')!r}")
    return errs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args(argv)
    errs: list[str] = []
    for p in args.paths:
        if os.path.isdir(p):
            for f in sorted(os.listdir(p)):
                if f.endswith(".json"):
                    errs += check(os.path.join(p, f))
        else:
            errs += check(p)
    if errs:
        for e in errs:
            print(f"FAIL {e}")
        return 1
    print(f"OK  all required metrics present ({len(args.paths)} path(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
