#!/usr/bin/env python3
"""test-recode-diff.py — self-test for the M7 recode pass.

A recode log is only worth publishing if it catches every way a code can move and
refuses to run on input it cannot trust. This builds throwaway snapshot pairs in
temp dirs and checks `scripts/recode-diff.py` says exactly the right thing.

    python3 scripts/test-recode-diff.py          # run all cases
    python3 scripts/test-recode-diff.py --keep   # keep temp dirs for inspection

Exit codes
    0  every case behaved as expected
    1  at least one case failed
    3  could not run (script missing)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "recode-diff.py")
PARTY_SLUGS = ["ndp", "cpb", "green", "onebc", "centrebc"]

QUESTIONS = [
    {"id": "q01", "statement": "A", "topic": "housing", "dimensions": ["economic"],
     "status": "frozen", "notes": ""},
    {"id": "q02", "statement": "B", "topic": "health", "dimensions": ["social"],
     "status": "frozen", "notes": ""},
    {"id": "q03", "statement": "C", "topic": "health", "dimensions": ["economic"],
     "status": "frozen", "notes": ""},
]


def row(slug, qid, code, *, quote="Q", sid=None, conf="high", coder="coder-a", version="v1"):
    return {
        "party_slug": slug,
        "question_id": qid,
        "code": code,
        "quote": None if code is None else quote,
        "source_id": None if code is None else (sid or f"{slug}-0001"),
        "source_url": None if code is None else f"https://example.org/{slug}/1",
        "archive_url": None,
        "coder": coder,
        "version": version,
        "created_at": "2026-10-01T00:00:00Z",
        "confidence": conf,
    }


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)


def write_snapshot(dirpath, rows):
    """rows: {(slug, qid): record}; grouped into <party>.json files."""
    for slug in PARTY_SLUGS:
        sel = [r for (s, _), r in sorted(rows.items()) if s == slug]
        if sel:
            write_json(os.path.join(dirpath, f"{slug}.json"), sel)


def make_data_root(rows_by_version):
    root = tempfile.mkdtemp(prefix="bcvm-recode-")
    write_json(os.path.join(root, "data", "questions", "questions.json"), QUESTIONS)
    for name, rows in rows_by_version.items():
        # "codings" is the live dir the tool reads; everything else is a sibling snapshot
        base = os.path.join(root, "data") if name == "codings" else root
        write_snapshot(os.path.join(base, name), rows)
    return root


def run(root, args, expect_rc=None):
    cmd = [sys.executable, SCRIPT, "--data-root", os.path.join(root, "data"), "--json"] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    rep: dict = {}
    try:
        rep = json.loads(proc.stdout)
    except json.JSONDecodeError:
        rep = {"_raw": proc.stdout + proc.stderr}
    if not isinstance(rep, dict):
        rep = {"_raw": proc.stdout + proc.stderr}
    if expect_rc is not None and proc.returncode != expect_rc:
        rep["_rc_mismatch"] = f"exit {proc.returncode}, wanted {expect_rc}"
    return proc.returncode, rep


BASELINE = {
    ("ndp", "q01"): row("ndp", "q01", 1),
    ("ndp", "q03"): row("ndp", "q03", 1),
    ("cpb", "q01"): row("cpb", "q01", -1),
    ("cpb", "q02"): row("cpb", "q02", -2),
    ("green", "q02"): row("green", "q02", -2),
}


def mut(rows, key, **changes):
    out = {k: dict(v) for k, v in rows.items()}
    out[key].update(changes)
    return out


def case(label, fn):
    try:
        ok, detail = fn()
    except Exception as exc:  # noqa: BLE001
        ok, detail = False, f"raised {type(exc).__name__}: {exc}"
    print(f"[{'PASS' if ok else 'FAIL'}] {label}: {detail}")
    return ok


# --------------------------------------------------------------------------- #
# cases
# --------------------------------------------------------------------------- #
def c_identical(keep):
    root = make_data_root({"v1": BASELINE, "v2": BASELINE})
    keep.append(root)
    _, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    n = rep.get("counts", {}).get("unchanged")
    ok = n == len(BASELINE) and rep.get("position_level_changes") == 0
    return ok, f"unchanged={n} position_changes={rep.get('position_level_changes')}"


def c_code_change(keep):
    root = make_data_root({"v1": BASELINE, "v2": mut(BASELINE, ("ndp", "q01"), code=-1)})
    keep.append(root)
    _, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    pc = rep.get("position_changes", [])
    got = pc[0] if pc else {}
    move = {m["dimension"]: m for m in rep.get("position_movement", []) if m["party_slug"] == "ndp"}
    # ndp economic: v1 mean of (1,1)=1.0 -> v2 mean of (-1,1)=0.0, delta -1.0
    ok = (len(pc) == 1
          and got.get("party_slug") == "ndp" and got.get("question_id") == "q01"
          and got.get("fields", {}).get("code") == {"from": 1, "to": -1}
          and move["economic"]["delta"] == -1.0
          and rep.get("position_level_changes") == 1)
    return ok, f"changes={len(pc)} delta={move['economic']['delta']}"


def c_fail_on_change(keep):
    root = make_data_root({"v1": BASELINE, "v2": mut(BASELINE, ("cpb", "q01"), code=2)})
    keep.append(root)
    rc, _ = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2"),
                       "--fail-on-change"])
    rc2, _ = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v1"),
                        "--fail-on-change"])
    return rc == 1 and rc2 == 0, f"changed->{rc} (want 1), identical->{rc2} (want 0)"


def c_added_removed(keep):
    rows2 = dict(BASELINE)
    rows2[("green", "q01")] = row("green", "q01", 0)       # added
    rows2.pop(("cpb", "q02"))                              # removed
    root = make_data_root({"v1": BASELINE, "v2": rows2})
    keep.append(root)
    _, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    ok = ([a["question_id"] for a in rep.get("added", [])] == ["q01"]
          and [r["question_id"] for r in rep.get("removed", [])] == ["q02"]
          and rep.get("position_level_changes") == 2)
    return ok, f"added={len(rep.get('added', []))} removed={len(rep.get('removed', []))} total=" \
               f"{rep.get('position_level_changes')}"


def c_quote_only(keep):
    root = make_data_root({"v1": BASELINE,
                           "v2": mut(BASELINE, ("ndp", "q03"), quote="a different quote")})
    keep.append(root)
    _, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    ok = (rep.get("counts", {}).get("provenance-changed") == 1
          and rep.get("position_level_changes") == 0)
    return ok, f"provenance={rep.get('counts', {}).get('provenance-changed')} " \
               f"position={rep.get('position_level_changes')}"


def c_confidence_only(keep):
    root = make_data_root({"v1": BASELINE,
                           "v2": mut(BASELINE, ("ndp", "q01"), confidence="low")})
    keep.append(root)
    _, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    ok = (rep.get("counts", {}).get("meta-changed") == 1
          and rep.get("position_level_changes") == 0)
    return ok, f"meta={rep.get('counts', {}).get('meta-changed')}"


def c_version_bump_only(keep):
    rows2 = {k: dict(v) for k, v in BASELINE.items()}
    for v in rows2.values():
        v["version"] = "v2"
    root = make_data_root({"v1": BASELINE, "v2": rows2})
    keep.append(root)
    _, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    ok = (rep.get("counts", {}).get("meta-changed") == len(BASELINE)
          and rep.get("position_level_changes") == 0)
    return ok, f"meta={rep.get('counts', {}).get('meta-changed')} position=" \
               f"{rep.get('position_level_changes')}"


def c_null_transitions(keep):
    root = make_data_root({"v1": BASELINE,
                           "v2": mut(mut(BASELINE, ("ndp", "q01"), code=None),
                                     ("cpb", "q01"), code=-2)})
    keep.append(root)
    _, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    f = {(c["party_slug"], c["question_id"]): c["fields"].get("code")
         for c in rep.get("position_changes", [])}
    ok = (f.get(("ndp", "q01")) == {"from": 1, "to": None}
          and f.get(("cpb", "q01")) == {"from": -1, "to": -2})
    return ok, f"ndp={f.get(('ndp','q01'))} cpb={f.get(('cpb','q01'))}"


def c_hash_determinism(keep):
    root = make_data_root({"v1": BASELINE, "v2": dict(reversed(list(BASELINE.items())))})
    keep.append(root)
    _, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    ok = (rep["from"]["sha256"] == rep["to"]["sha256"]
          and rep.get("position_level_changes") == 0
          and rep.get("counts", {}).get("unchanged") == len(BASELINE))
    return ok, f"sha from={rep['from']['sha256'][:12]} to={rep['to']['sha256'][:12]}"


def c_snapshot(keep):
    root = make_data_root({"codings": BASELINE})
    keep.append(root)
    data = os.path.join(root, "data")
    first = subprocess.run([sys.executable, SCRIPT, "--data-root", data, "--snapshot", "v1"],
                           capture_output=True, text=True)
    man = os.path.join(data, "codings", "archive", "v1", "MANIFEST.json")
    manifest = json.load(open(man)) if os.path.exists(man) else {}
    second = subprocess.run([sys.executable, SCRIPT, "--data-root", data, "--snapshot", "v1"],
                            capture_output=True, text=True)
    forced = subprocess.run([sys.executable, SCRIPT, "--data-root", data, "--snapshot", "v1", "--force"],
                            capture_output=True, text=True)
    ok = (first.returncode == 0 and second.returncode == 3 and forced.returncode == 0
          and manifest.get("rows") == len(BASELINE)
          and manifest.get("files", {}).get("ndp.json")
          and len(manifest.get("content_sha256", "")) == 64)
    return ok, f"first={first.returncode} second={second.returncode} forced={forced.returncode} " \
               f"rows={manifest.get('rows')}"


def c_default_from_archive(keep):
    root = make_data_root({"v1": BASELINE,
                           "codings": mut(BASELINE, ("ndp", "q01"), code=2)})
    keep.append(root)
    data = os.path.join(root, "data")
    # archive/v1 holds the v1 baseline; data/codings is the live (recoded) set
    shutil.copytree(os.path.join(root, "v1"), os.path.join(data, "codings", "archive", "v1"))
    rc, rep = run(root, [], 0)
    ok = (rc == 0 and rep["from"]["label"] == "v1" and rep["to"]["label"] == "codings"
          and rep.get("position_level_changes") == 1)
    return ok, f"exit {rc} from={rep.get('from', {}).get('label')} " \
               f"to={rep.get('to', {}).get('label')} " \
               f"changes={rep.get('position_level_changes')}"


def c_no_baseline(keep):
    root = make_data_root({"codings": BASELINE})
    keep.append(root)
    rc, rep = run(root, [], 3)
    return rc == 3 and "no baseline" in json.dumps(rep), f"exit {rc}"


def c_malformed_row(keep):
    bad = dict(BASELINE)
    bad[("ndp", "q01")] = dict(bad[("ndp", "q01")], code=7)
    root = make_data_root({"v1": BASELINE, "v2": bad})
    keep.append(root)
    rc, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 3)
    problems = " ".join(rep.get("problems", []))
    return rc == 3 and "not null or an int" in problems, f"exit {rc}; problems={len(rep.get('problems', []))}"


def c_ignores_nonparty_json(keep):
    root = make_data_root({"v1": BASELINE, "v2": dict(BASELINE)})
    keep.append(root)
    write_json(os.path.join(root, "v2", "MANIFEST.json"), {"label": "x"})
    write_json(os.path.join(root, "v2", "RECODE-v1-to-v2.json"), {"stale": True})
    rc, rep = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    ok = rc == 0 and rep.get("counts", {}).get("unchanged") == len(BASELINE) \
        and rep.get("counts", {}).get("added") is None
    return ok, f"exit {rc} unchanged={rep.get('counts', {}).get('unchanged')}"


def c_writes_reports(keep):
    root = make_data_root({"v1": BASELINE, "v2": mut(BASELINE, ("green", "q02"), code=0)})
    keep.append(root)
    rc, _ = run(root, ["--from", os.path.join(root, "v1"), "--to", os.path.join(root, "v2")], 0)
    md = os.path.join(root, "data", "codings", "recode", "RECODE-v1-to-v2.md")
    js = os.path.join(root, "data", "codings", "recode", "v1-to-v2.json")
    text = open(md).read() if os.path.exists(md) else ""
    ok = (rc == 0 and os.path.exists(js) and "Recode log" in text
          and "Effect on published positions" in text and "position changes" in text)
    return ok, f"md={'yes' if text else 'no'} json={'yes' if os.path.exists(js) else 'no'}"


CASES = [
    ("identical snapshots report no change", c_identical),
    ("a moved code is a position change with a score delta", c_code_change),
    ("--fail-on-change exits 1 only when a code moved", c_fail_on_change),
    ("added and removed rows are counted as position-level", c_added_removed),
    ("quote-only edit is evidence, not position", c_quote_only),
    ("confidence-only edit is meta", c_confidence_only),
    ("version bump alone is meta, not a code change", c_version_bump_only),
    ("null<->code transitions are position changes", c_null_transitions),
    ("content hash is order-independent", c_hash_determinism),
    ("snapshot writes a manifest and refuses to overwrite", c_snapshot),
    ("default baseline is the newest archive", c_default_from_archive),
    ("no baseline exits 3 with guidance", c_no_baseline),
    ("a malformed code blocks the run", c_malformed_row),
    ("non-party json in a snapshot dir is ignored", c_ignores_nonparty_json),
    ("reports are written to data/codings/recode/", c_writes_reports),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Self-test for scripts/recode-diff.py")
    ap.add_argument("--keep", action="store_true", help="keep the temp roots")
    args = ap.parse_args(argv)
    if not os.path.exists(SCRIPT):
        print("cannot run: scripts/recode-diff.py missing", file=sys.stderr)
        return 3
    keep: list[str] = []
    failures = 0
    for label, fn in CASES:
        if not case(label, lambda fn=fn: fn(keep)):
            failures += 1
    if args.keep:
        print("\ntemp roots kept:")
        for d in keep:
            print("  " + d)
    else:
        for d in keep:
            shutil.rmtree(d, ignore_errors=True)
    print(f"\n{len(CASES) - failures}/{len(CASES)} cases behaved as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
