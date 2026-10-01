#!/usr/bin/env python3
"""recode-diff.py — the M7 recode pass.

M7 is "versioned diffs, published": the v1 codings are frozen before launch, and
each later recode (Oct 12, Oct 20) is published as a diff against the previous
version, so the coding table never changes under the reader's feet without a
record of what changed and why.

This tool does not decide any code. It:
  1. snapshots the live codings (`--snapshot LABEL`) so a later recode has a
     baseline to be compared against, with a sha256 manifest;
  2. diffs two snapshots (`--from DIR --to DIR`) per party x question and
     classifies every change (position / provenance / confidence / meta);
  3. reports what the change does to the *published* numbers — each party's
     economic and social position (docs/SCHEMA.md scoring v1) before and after.

Contract: docs/SCHEMA.md. Run from the repo root:

    python3 scripts/recode-diff.py --snapshot v1            # freeze the baseline
    python3 scripts/recode-diff.py                          # newest archive -> live
    python3 scripts/recode-diff.py --from data/codings/archive/v1 --to data/codings

Exit codes
    0  ran; no position-level change
    1  ran; position-level changes found and --fail-on-change was passed
    3  could not run (missing/unreadable snapshot, malformed rows, bad args)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import shutil
import sys

PARTY_SLUGS = ["ndp", "cpb", "green", "onebc", "centrebc"]
DIMENSIONS = ["economic", "social"]

# Fields whose change alters what the reader is told a party stands for.
POSITION_FIELDS = ("code",)
# Fields that alter the evidence behind a code but not the code itself.
PROVENANCE_FIELDS = ("quote", "source_id", "source_url", "archive_url")
# Fields that are bookkeeping.
META_FIELDS = ("confidence", "coder", "version", "created_at")


# --------------------------------------------------------------------------- #
# io / hashing
# --------------------------------------------------------------------------- #
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read().strip()
    if not raw:
        raise ValueError("file is empty")
    return json.loads(raw)


def coding_files(directory: str) -> list[str]:
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"no such codings directory: {directory}")
    return sorted(
        f for f in os.listdir(directory)
        if f.endswith(".json") and not f.startswith(".") and os.path.isfile(os.path.join(directory, f))
    )


def load_snapshot(directory: str) -> tuple[dict[tuple[str, str], dict], list[str]]:
    """-> {(party, question): row}, [problems]. Only <party>.json files are read;
    any other .json in the directory is ignored (the archive dir also holds the
    diff reports this tool writes)."""
    rows: dict[tuple[str, str], dict] = {}
    problems: list[str] = []
    names = [f for f in coding_files(directory) if f[:-5] in PARTY_SLUGS]
    if not names:
        problems.append(
            f"{directory} holds no per-party coding file (expected one of "
            f"{', '.join(s + '.json' for s in PARTY_SLUGS)}) — nothing to diff"
        )
        return rows, problems
    for name in names:
        stem = name[:-5]
        path = os.path.join(directory, name)
        try:
            data = load_json(path)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{name}: not readable JSON ({exc})")
            continue
        if not isinstance(data, list):
            problems.append(f"{name}: must be a JSON array")
            continue
        for i, rec in enumerate(data):
            if not isinstance(rec, dict):
                problems.append(f"{name}[{i}]: not an object")
                continue
            slug = rec.get("party_slug")
            qid = rec.get("question_id")
            if not isinstance(qid, str) or not qid:
                problems.append(f"{name}[{i}]: no question_id")
                continue
            if not isinstance(slug, str) or slug != stem:
                problems.append(f"{name}[{i}]: party_slug={slug!r} does not match the filename")
                continue
            key = (slug, qid)
            if key in rows:
                problems.append(f"{name}[{i}]: duplicate row for {slug}/{qid}")
                continue
            code = rec.get("code")
            if code is not None and not (isinstance(code, int) and not isinstance(code, bool) and -2 <= code <= 2):
                problems.append(f"{name}[{i}] {slug}/{qid}: code {code!r} is not null or an int in -2..2")
            rows[key] = rec
    return rows, problems


def canonical_hash(rows: dict[tuple[str, str], dict]) -> str:
    """Stable content hash of a snapshot. Key order and row order do not matter;
    any field value does. This is what gets published next to a recode so the
    two sides of a diff are pinned."""
    ordered = [rows[k] for k in sorted(rows)]
    blob = json.dumps(ordered, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# scoring (docs/SCHEMA.md, scoring v1)
# --------------------------------------------------------------------------- #
def dimensions_of(data_root: str) -> dict[str, list[str]]:
    """question_id -> dimensions, from the live question file. Missing file is
    not fatal: the diff still runs, positions are just not computed."""
    path = os.path.join(data_root, "questions", "questions.json")
    out: dict[str, list[str]] = {}
    if not os.path.exists(path):
        return out
    try:
        rows = load_json(path)
    except Exception:  # noqa: BLE001
        return out
    for q in rows if isinstance(rows, list) else []:
        if isinstance(q, dict) and isinstance(q.get("id"), str):
            dims = q.get("dimensions")
            out[q["id"]] = [d for d in dims if d in DIMENSIONS] if isinstance(dims, list) else []
    return out


def positions(rows: dict[tuple[str, str], dict], dims: dict[str, list[str]]) -> dict[str, dict]:
    """party -> {dimension: {mean, n, nulls}}. Mean of the party's non-null codes
    on that dimension's questions (SCHEMA scoring v1)."""
    out: dict[str, dict] = {}
    for slug in PARTY_SLUGS:
        per: dict[str, dict] = {}
        for dim in DIMENSIONS:
            codes = [
                rec["code"]
                for (s, qid), rec in rows.items()
                if s == slug and rec.get("code") is not None and dim in dims.get(qid, [])
            ]
            nulls = sum(
                1 for (s, qid), rec in rows.items()
                if s == slug and rec.get("code") is None and dim in dims.get(qid, [])
            )
            per[dim] = {
                "mean": round(sum(codes) / len(codes), 3) if codes else None,
                "n": len(codes),
                "nulls": nulls,
            }
        out[slug] = per
    return out


# --------------------------------------------------------------------------- #
# the diff
# --------------------------------------------------------------------------- #
def diff_rows(
    old: dict[tuple[str, str], dict], new: dict[tuple[str, str], dict]
) -> list[dict]:
    changes: list[dict] = []
    for key in sorted(set(old) | set(new)):
        slug, qid = key
        a, b = old.get(key), new.get(key)
        fields: dict = {}
        if a is None:
            status = "added"
        elif b is None:
            status = "removed"
        else:
            for field in POSITION_FIELDS + PROVENANCE_FIELDS + META_FIELDS:
                va, vb = a.get(field), b.get(field)
                if va != vb:
                    fields[field] = {"from": va, "to": vb}
            if not fields:
                status = "unchanged"
            elif set(fields) & set(POSITION_FIELDS):
                status = "position-changed"
            elif set(fields) & set(PROVENANCE_FIELDS):
                status = "provenance-changed"
            else:
                status = "meta-changed"
        changes.append({"party_slug": slug, "question_id": qid, "status": status,
                        "fields": fields if a is not None and b is not None else {},
                        "old_row": a, "new_row": b})
    return changes


def build_report(from_dir: str, to_dir: str, label_from: str, label_to: str, data_root: str) -> dict:
    old, old_problems = load_snapshot(from_dir)
    new, new_problems = load_snapshot(to_dir)
    problems = [f"{label_from}: {p}" for p in old_problems] + [f"{label_to}: {p}" for p in new_problems]

    dims = dimensions_of(data_root)
    changes = diff_rows(old, new)
    by_status: dict[str, int] = {}
    for c in changes:
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1
    by_party: dict[str, dict] = {}
    for slug in PARTY_SLUGS:
        rows = [c for c in changes if c["party_slug"] == slug]
        by_party[slug] = {
            s: sum(1 for c in rows if c["status"] == s)
            for s in ("position-changed", "provenance-changed", "meta-changed", "added", "removed", "unchanged")
        }

    pos_from = positions(old, dims)
    pos_to = positions(new, dims)
    movement = []
    for slug in PARTY_SLUGS:
        for dim in DIMENSIONS:
            a, b = pos_from[slug][dim], pos_to[slug][dim]
            delta = None
            if a["mean"] is not None and b["mean"] is not None:
                delta = round(b["mean"] - a["mean"], 3)
            movement.append({"party_slug": slug, "dimension": dim,
                             "from": a["mean"], "to": b["mean"], "delta": delta,
                             "n_from": a["n"], "n_to": b["n"],
                             "nulls_from": a["nulls"], "nulls_to": b["nulls"]})

    return {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "from": {"label": label_from, "dir": from_dir, "rows": len(old), "sha256": canonical_hash(old)},
        "to": {"label": label_to, "dir": to_dir, "rows": len(new), "sha256": canonical_hash(new)},
        "questions_known": len(dims),
        "counts": by_status,
        "by_party": by_party,
        "position_changes": [c for c in changes if c["status"] == "position-changed"],
        "provenance_changes": [
            {k: c[k] for k in ("party_slug", "question_id", "fields")}
            for c in changes if c["status"] == "provenance-changed"
        ],
        "added": [
            {"party_slug": c["party_slug"], "question_id": c["question_id"],
             "code": (c["new_row"] or {}).get("code")}
            for c in changes if c["status"] == "added"
        ],
        "removed": [
            {"party_slug": c["party_slug"], "question_id": c["question_id"],
             "code": (c["old_row"] or {}).get("code")}
            for c in changes if c["status"] == "removed"
        ],
        "meta_changes": [
            {k: c[k] for k in ("party_slug", "question_id", "fields")}
            for c in changes if c["status"] == "meta-changed"
        ],
        "position_movement": movement,
        "problems": problems,
        "position_level_changes": by_status.get("position-changed", 0)
        + by_status.get("added", 0) + by_status.get("removed", 0),
    }


# --------------------------------------------------------------------------- #
# renderers
# --------------------------------------------------------------------------- #
def code_str(v) -> str:
    return "no position" if v is None else f"{v:+d}"


def render_md(rep: dict) -> str:
    L = []
    L.append(f"# Recode log — {rep['from']['label']} → {rep['to']['label']}")
    L.append("")
    L.append(f"_Generated {rep['generated_at']} by `scripts/recode-diff.py`. "
             "Published under the neutrality rule in `docs/SCHEMA.md`: a change to a "
             "party's code is a change to what this tool tells voters, so every one is "
             "listed here with its source._")
    L.append("")
    L.append("| | version | rows | content sha256 |")
    L.append("|---|---|---|---|")
    L.append(f"| before | `{rep['from']['label']}` | {rep['from']['rows']} | `{rep['from']['sha256']}` |")
    L.append(f"| after | `{rep['to']['label']}` | {rep['to']['rows']} | `{rep['to']['sha256']}` |")
    L.append("")
    c = rep["counts"]
    L.append("## Summary")
    L.append("")
    L.append(f"- position changes (a code moved, was added, or was dropped): "
             f"**{rep['position_level_changes']}**")
    L.append(f"- quote/source changes (same code, different evidence): "
             f"**{c.get('provenance-changed', 0)}**")
    L.append(f"- confidence/coder/version only: **{c.get('meta-changed', 0)}**")
    L.append(f"- unchanged: {c.get('unchanged', 0)}")
    L.append("")

    L.append("## Position changes")
    L.append("")
    if not rep["position_changes"]:
        L.append("None. Every party's code is identical in both versions.")
    else:
        L.append("| party | question | before | after | coder | source |")
        L.append("|---|---|---|---|---|---|")
        for ch in rep["position_changes"]:
            a, b = ch["old_row"] or {}, ch["new_row"] or {}
            L.append(
                f"| {ch['party_slug']} | {ch['question_id']} | {code_str(a.get('code'))} "
                f"| {code_str(b.get('code'))} | {b.get('coder', a.get('coder', ''))} "
                f"| {b.get('source_id') or a.get('source_id') or '—'} |"
            )
    L.append("")

    L.append("## Added / removed")
    L.append("")
    if rep["added"]:
        L.append("Added: " + ", ".join(f"{a['party_slug']}/{a['question_id']} ({code_str(a['code'])})"
                                       for a in rep["added"]))
    if rep["removed"]:
        L.append("Removed: " + ", ".join(f"{r['party_slug']}/{r['question_id']} ({code_str(r['code'])})"
                                         for r in rep["removed"]))
    if not rep["added"] and not rep["removed"]:
        L.append("None.")
    L.append("")

    L.append("## Effect on published positions")
    L.append("")
    L.append("Party position per dimension = mean of its non-null codes on that "
             "dimension's questions (SCHEMA scoring v1), on the −2…+2 scale.")
    L.append("")
    L.append("| party | dimension | before | after | change | codes |")
    L.append("|---|---|---|---|---|---|")
    for m in rep["position_movement"]:
        before = "—" if m["from"] is None else f"{m['from']:+.3f}"
        after = "—" if m["to"] is None else f"{m['to']:+.3f}"
        delta = "—" if m["delta"] is None else ("no change" if m["delta"] == 0 else f"{m['delta']:+.3f}")
        L.append(f"| {m['party_slug']} | {m['dimension']} | {before} | {after} | {delta} "
                 f"| {m['n_from']} → {m['n_to']} |")
    L.append("")

    if rep["provenance_changes"]:
        L.append("## Evidence changes (code unchanged)")
        L.append("")
        L.append("| party | question | fields |")
        L.append("|---|---|---|")
        for p in rep["provenance_changes"]:
            L.append(f"| {p['party_slug']} | {p['question_id']} | {', '.join(sorted(p['fields']))} |")
        L.append("")

    if rep["problems"]:
        L.append("## Problems")
        L.append("")
        for p in rep["problems"]:
            L.append(f"- {p}")
        L.append("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# snapshot mode
# --------------------------------------------------------------------------- #
def do_snapshot(live: str, archive_root: str, label: str, force: bool) -> int:
    dest = os.path.join(archive_root, label)
    if os.path.exists(dest) and not force:
        print(f"recode-diff: snapshot {dest} already exists — refusing to overwrite a "
              f"published baseline (pass --force to replace it)", file=sys.stderr)
        return 3
    try:
        names = [f for f in coding_files(live) if f[:-5] in PARTY_SLUGS]
    except FileNotFoundError as exc:
        print(f"recode-diff: {exc}", file=sys.stderr)
        return 3
    if not names:
        print(f"recode-diff: {live} holds no per-party coding file — nothing to snapshot",
              file=sys.stderr)
        return 3
    os.makedirs(dest, exist_ok=True)
    manifest = {"label": label, "created_at": _dt.datetime.now(_dt.timezone.utc)
                .strftime("%Y-%m-%dT%H:%M:%SZ"), "source": live, "files": {}}
    for name in names:
        src = os.path.join(live, name)
        dst = os.path.join(dest, name)
        shutil.copy2(src, dst)
        with open(src, "rb") as fh:
            manifest["files"][name] = hashlib.sha256(fh.read()).hexdigest()
    rows, problems = load_snapshot(dest)
    manifest["rows"] = len(rows)
    manifest["content_sha256"] = canonical_hash(rows)
    if problems:
        manifest["problems"] = problems
    with open(os.path.join(dest, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"snapshot {label}: {len(names)} file(s), {len(rows)} rows -> {dest}")
    print(f"  content sha256 {manifest['content_sha256']}")
    if problems:
        for p in problems:
            print(f"  WARN {p}")
    return 0


def newest_archive(archive_root: str, exclude: str) -> str | None:
    if not os.path.isdir(archive_root):
        return None
    cands = [
        os.path.join(archive_root, d) for d in os.listdir(archive_root)
        if os.path.isdir(os.path.join(archive_root, d))
        and os.path.abspath(os.path.join(archive_root, d)) != os.path.abspath(exclude)
        and any(f[:-5] in PARTY_SLUGS for f in os.listdir(os.path.join(archive_root, d)))
    ]
    return max(cands, key=os.path.getmtime) if cands else None


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", default=None, help="repo data/ directory (default: ./data)")
    ap.add_argument("--snapshot", metavar="LABEL",
                    help="freeze the live codings into data/codings/archive/LABEL and exit")
    ap.add_argument("--force", action="store_true", help="with --snapshot: replace an existing label")
    ap.add_argument("--from", dest="from_dir", default=None,
                    help="baseline snapshot dir (default: newest under data/codings/archive/)")
    ap.add_argument("--to", dest="to_dir", default=None, help="new snapshot dir (default: data/codings)")
    ap.add_argument("--label-from", default=None)
    ap.add_argument("--label-to", default=None)
    ap.add_argument("--out-json", default=None, help="default: data/codings/recode/<from>-to-<to>.json")
    ap.add_argument("--out-md", default=None, help="default: data/codings/recode/RECODE-<from>-to-<to>.md")
    ap.add_argument("--json", action="store_true", help="also print the report to stdout")
    ap.add_argument("--fail-on-change", action="store_true",
                    help="exit 1 when a position-level change is present")
    args = ap.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_root = args.data_root or os.path.join(root, "data")
    live = os.path.join(data_root, "codings")
    archive_root = os.path.join(live, "archive")

    if args.snapshot:
        return do_snapshot(live, archive_root, args.snapshot, args.force)

    to_dir = args.to_dir or live
    from_dir = args.from_dir or newest_archive(archive_root, exclude=to_dir)
    if from_dir is None:
        print("recode-diff: no baseline to diff against. Freeze the current codings first:\n"
              "    python3 scripts/recode-diff.py --snapshot v1", file=sys.stderr)
        return 3
    if not os.path.isdir(from_dir):
        print(f"recode-diff: baseline dir not found: {from_dir}", file=sys.stderr)
        return 3
    if not os.path.isdir(to_dir):
        print(f"recode-diff: target dir not found: {to_dir}", file=sys.stderr)
        return 3

    label_from = args.label_from or os.path.basename(os.path.normpath(from_dir))
    label_to = args.label_to or os.path.basename(os.path.normpath(to_dir))

    rep = build_report(from_dir, to_dir, label_from, label_to, data_root)
    md = render_md(rep)

    out_dir = os.path.join(live, "recode")
    out_json = args.out_json or os.path.join(out_dir, f"{label_from}-to-{label_to}.json")
    out_md = args.out_md or os.path.join(out_dir, f"RECODE-{label_from}-to-{label_to}.md")
    for p in (out_json, out_md):
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2, sort_keys=True)
        fh.write("\n")
    with open(out_md, "w", encoding="utf-8") as fh:
        fh.write(md)

    if args.json:
        print(json.dumps(rep, indent=2, sort_keys=True))
    else:
        c = rep["counts"]
        print(f"recode-diff  {label_from} ({rep['from']['sha256'][:12]}) -> "
              f"{label_to} ({rep['to']['sha256'][:12]})")
        print("-" * 72)
        print(f"  {rep['position_level_changes']} position change(s), "
              f"{c.get('provenance-changed', 0)} evidence-only, "
              f"{c.get('meta-changed', 0)} meta-only, {c.get('unchanged', 0)} unchanged")
        for m in rep["position_movement"]:
            if m["delta"]:
                print(f"  MOVED {m['party_slug']}/{m['dimension']}: "
                      f"{m['from']:+.3f} -> {m['to']:+.3f} ({m['delta']:+.3f})")
        for p in rep["problems"]:
            print(f"  FAIL {p}")
        print("-" * 72)
        print(f"  wrote {out_md}")
        print(f"  wrote {out_json}")

    if rep["problems"]:
        return 3
    if args.fail_on_change and rep["position_level_changes"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
