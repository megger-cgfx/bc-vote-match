"""Turn result JSON into a human-readable table.

    python -m harness.summarize results/*.json
    python -m harness.summarize --results-dir results --format md

Safe to run on a mix of files: records that are not perf runs are skipped.
"""

from __future__ import annotations

import argparse
import glob
import json
import os


def fmt(value, digits: int = 2, dash: str = "-") -> str:
    if value is None:
        return dash
    if isinstance(value, float):
        if digits == 0:
            return f"{value:,.0f}"
        return f"{value:,.{digits}f}"
    return str(value)


def fmt_pm(stat: dict | None, digits: int = 2) -> str:
    """mean ± stddev."""
    if not stat or stat.get("mean") is None:
        return "-"
    n = stat.get("n", 0)
    if n <= 1 or not stat.get("stddev"):
        return f"{stat['mean']:,.{digits}f}"
    return f"{stat['mean']:,.{digits}f} ± {stat['stddev']:,.{digits}f}"


def row_for(rec: dict) -> dict | None:
    if rec.get("kind") != "perf":
        return None
    cfg = rec.get("config", {})
    summary = {s["concurrency"]: s for s in rec.get("summary", [])}
    c1 = summary.get(1, {})
    c4 = summary.get(4, {})
    device = (rec.get("vram", {}) or {}).get("device") or {}
    return {
        "label": rec.get("label"),
        "backend": cfg.get("backend"),
        "quant": cfg.get("quantization") or "-",
        "status": rec.get("status"),
        "load_s": rec.get("server", {}).get("load_time_s") if rec.get("server") else None,
        "peak_vram_mb": rec.get("peak_vram_mb"),
        "peak_delta_mb": rec.get("peak_vram_delta_mb"),
        "gpu": device.get("name") or "-",
        "ttft1": (c1.get("ttft_s") or {}).get("mean"),
        "prefill1": (c1.get("prefill_tps") or {}).get("mean"),
        "decode1": (c1.get("decode_tps_per_stream") or {}).get("mean"),
        "agg1": (c1.get("aggregate_decode_tps") or {}).get("mean"),
        "ttft4": (c4.get("ttft_s") or {}).get("mean"),
        "decode4": (c4.get("decode_tps_per_stream") or {}).get("mean"),
        "agg4": (c4.get("aggregate_decode_tps") or {}).get("mean"),
        "repeats": cfg.get("repeats"),
        "errors": len(rec.get("errors", [])),
        "file": rec.get("_file"),
    }


COLS = [
    ("label", "model", 34),
    ("backend", "runtime", 9),
    ("quant", "quant", 8),
    ("status", "status", 8),
    ("load_s", "load s", 7),
    ("peak_vram_mb", "peak VRAM MB", 12),
    ("prefill1", "prefill tok/s", 13),
    ("ttft1", "TTFT s", 8),
    ("decode1", "decode tok/s", 12),
    ("agg1", "agg tok/s c1", 12),
    ("agg4", "agg tok/s c4", 12),
    ("decode4", "per-stream c4", 13),
]


def table(rows: list[dict], fmt_name: str = "md") -> str:
    if not rows:
        return "(no perf results found)"
    lines = []
    if fmt_name == "md":
        lines.append("| " + " | ".join(h for _, h, _ in COLS) + " |")
        lines.append("|" + "|".join("---" for _ in COLS) + "|")
        for r in rows:
            cells = []
            for key, _, _ in COLS:
                v = r.get(key)
                digits = 0 if key in ("peak_vram_mb", "peak_delta_mb") else 2
                cells.append(fmt(v, digits))
            lines.append("| " + " | ".join(cells) + " |")
    else:
        widths = [max(len(h), w) for _, h, w in COLS]
        header = "  ".join(h.ljust(w) for (_, h, _), w in zip(COLS, widths))
        lines.append(header)
        lines.append("-" * len(header))
        for r in rows:
            cells = []
            for (key, _, _), w in zip(COLS, widths):
                digits = 0 if key in ("peak_vram_mb", "peak_delta_mb") else 2
                cells.append(fmt(r.get(key), digits).ljust(w))
            lines.append("  ".join(cells))
    return "\n".join(lines)


def load(paths: list[str]) -> list[dict]:
    rows = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                rec = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        rec["_file"] = path
        row = row_for(rec)
        if row is not None:
            rows.append(row)
    rows.sort(key=lambda r: (r["agg1"] is None, -(r["agg1"] or 0)))
    return rows


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harness.summarize")
    p.add_argument("files", nargs="*", help="result JSON files (globs allowed)")
    p.add_argument("--results-dir", default=None, help="directory of *.json results")
    p.add_argument("--format", choices=["md", "text"], default="md")
    p.add_argument("--out", default=None, help="write the table to this file too")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    paths: list[str] = []
    for pattern in args.files:
        paths.extend(sorted(glob.glob(pattern)) or [pattern])
    if args.results_dir:
        paths.extend(sorted(glob.glob(os.path.join(args.results_dir, "*.json"))))
    paths = [p for p in dict.fromkeys(paths) if os.path.isfile(p)]
    out = table(load(paths), args.format)
    print(out)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
