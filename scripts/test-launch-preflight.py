#!/usr/bin/env python3
"""test-launch-preflight.py — self-test for the M5 launch gate.

The launch gate is only trustworthy if it can actually say GO on a complete,
sourced dataset *and* say NO-GO on each way the build can go wrong. This builds a
throwaway "green" repo root in a temp dir, checks the gate passes it, then mutates
that root once per guard and checks the gate catches exactly the right thing.

It never touches the real data/ or out/ trees; everything happens under a temp dir.

    python3 scripts/test-launch-preflight.py            # run all cases
    python3 scripts/test-launch-preflight.py --keep     # keep temp dirs for inspection

Exit codes
    0  every case behaved as expected
    1  at least one case failed
    3  could not run (missing scripts)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

PARTY_SLUGS = ["ndp", "cpb", "green", "onebc", "centrebc"]
GOOD_SHA = "a" * 64
BAD_SHA = "0" * 64
QUOTE = (
    "This government will keep the consumer carbon price off fuel while investing "
    "in the transition that actually lowers household bills."
)
HTML_BODY = (
    "<!doctype html><html><head>"
    '<link rel="canonical" href="https://bcvotematch.ca"/>'
    '<meta property="og:image" content="https://bcvotematch.ca/og.png"/>'
    "</head><body>"
    "BC Vote Match does not tell you how to vote and does not predict your vote. "
    "It is not affiliated with Vote Compass or Vox Pop Labs. "
    "No accounts, no tracking, no personal data."
    "</body></html>"
)

def write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def write_json(path: str, obj) -> None:
    write(path, json.dumps(obj, indent=2))


def build_green(root: str) -> None:
    """A minimal but complete dataset: 2 frozen questions x 5 parties.

    Layout mirrors the real repo: hash-verified captures under data/raw/,
    per-coder rows in data/codings/v1/, and the published, reconciled table in
    data/codings/codings.json (one row per party x question — the provenance
    gate counts pairs, so per-party files must NOT duplicate those pairs).
    """
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(root, "agents"), exist_ok=True)
    for name in ("validate-dataset.py", "launch-preflight.py", "verify-data.py"):
        shutil.copy(os.path.join(HERE, name), os.path.join(root, "scripts"))
    shutil.copy(
        os.path.join(HERE, "..", "agents", "validate_codings.py"),
        os.path.join(root, "agents"),
    )

    write_json(
        os.path.join(root, "data", "parties.json"),
        [
            {
                "slug": s,
                "name": f"Party {s}",
                "short": s.upper(),
                "leader": "A Leader",
                "leader_status": "permanent",
                "color": "#334455",
                "url": f"https://example.org/{s}",
            }
            for s in PARTY_SLUGS
        ],
    )
    questions = [
        {
            "id": "q01",
            "statement": "The province should raise the consumer carbon tax.",
            "topic": "cost-of-living-taxes",
            "dimensions": ["economic"],
            "status": "frozen",
            "notes": "",
        },
        {
            "id": "q02",
            "statement": "The province should override municipal zoning rules.",
            "topic": "housing",
            "dimensions": ["economic", "social"],
            "status": "frozen",
            "notes": "",
        },
    ]
    write_json(os.path.join(root, "data", "questions", "questions.json"), questions)

    published_rows: list[dict] = []
    for slug in PARTY_SLUGS:
        sid = f"{slug}-0001"
        html = f"<html><body>{QUOTE}</body></html>"
        write(os.path.join(root, "data", "raw", slug, f"{sid}.html"), html)
        write(os.path.join(root, "data", "raw", slug, f"{sid}.txt"), f"{QUOTE}\n")
        src = {
            "id": sid,
            "party_slug": slug,
            "type": "platform",
            "title": f"{slug} platform",
            "url": f"https://example.org/{slug}/platform",
            "published": "2026-09-01",
            "fetched_at": "2026-10-01T00:00:00Z",
            "sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
            "local_path": f"data/raw/{slug}/{sid}.html",
            "text_path": f"data/raw/{slug}/{sid}.txt",
            "archive_url": f"https://web.archive.org/web/2026/https://example.org/{slug}/platform",
        }
        write_json(os.path.join(root, "data", "raw", slug, "sources.json"), [src])
        for coder in ("coder-a", "coder-b"):
            rows = [
                {
                    "party_slug": slug,
                    "question_id": q["id"],
                    "code": 1 if i == 0 else -1,
                    "quote": QUOTE,
                    "source_id": sid,
                    "source_url": src["url"],
                    "archive_url": src["archive_url"],
                    "coder": coder,
                    "version": "v1",
                    "created_at": "2026-10-01T00:00:00Z",
                    "confidence": "high",
                }
                for i, q in enumerate(questions)
            ]
            write_json(
                os.path.join(root, "data", "codings", "v1", f"{slug}-{coder}.json"), rows
            )
            if coder == "coder-a":
                published_rows.extend(rows)
    # The published table: one reconciled row per party x question, in the
    # coder-record schema (docs/SCHEMA.md).
    write_json(os.path.join(root, "data", "codings", "codings.json"), published_rows)
    # verify-data.py expects the schema-sanctioned riding layer dir to exist.
    write_json(os.path.join(root, "data", "raw", "ridings", "sources.json"), [])

    out = os.path.join(root, "out")
    for route in [
        "index.html",
        "questions/index.html",
        "results/index.html",
        "parties/index.html",
        "methodology/index.html",
        "coding-table/index.html",
        "about/index.html",
        "404.html",
    ]:
        write(os.path.join(out, route), HTML_BODY)
    write(os.path.join(out, "og.png"), "png")
    write(
        os.path.join(out, "sitemap.xml"),
        "<urlset>" + "".join(
            f"<url><loc>https://bcvotematch.ca/{p}</loc></url>"
            for p in ["", "questions/", "parties/", "methodology/", "coding-table/", "about/"]
        ) + "</urlset>",
    )
    write(os.path.join(out, "robots.txt"), "User-agent: *\nAllow: /\nSitemap: https://bcvotematch.ca/sitemap.xml\n")


def run_gate(
    root: str, strict: bool = False, online: bool = False, build: bool = False
) -> tuple[int, dict]:
    cmd = [sys.executable, os.path.join(root, "scripts", "launch-preflight.py"), "--root", root, "--json"]
    if not build:
        cmd.append("--no-build")
    if strict:
        cmd.append("--strict")
    if online:
        cmd.append("--online")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, {"checks": [], "raw": proc.stdout + proc.stderr}


def status_of(report: dict, check_name: str) -> str | None:
    for c in report.get("checks", []):
        if c["name"] == check_name:
            return c["status"]
    return None


# --------------------------------------------------------------------------- #
# mutations: name -> (expected check, mutation fn)
# --------------------------------------------------------------------------- #
def m_placeholder(root: str) -> None:
    write(os.path.join(root, "out", "index.html"), HTML_BODY + "<!-- PLACEHOLDER DATA -->")


def m_tracker(root: str) -> None:
    write(os.path.join(root, "out", "index.html"), HTML_BODY + '<script src="https://www.googletagmanager.com/gtag.js"></script>')


def m_external_script(root: str) -> None:
    write(os.path.join(root, "out", "index.html"), HTML_BODY + '<script src="https://cdn.jsdelivr.net/npm/x.js"></script>')


def m_no_disclaimer(root: str) -> None:
    write(os.path.join(root, "out", "about", "index.html"), "<html><body>nothing here</body></html>")


def m_pii(root: str) -> None:
    write(os.path.join(root, "src", "lib", "track.ts"), "document.cookie = 'id=1';\n")


def m_unfrozen(root: str) -> None:
    path = os.path.join(root, "data", "questions", "questions.json")
    rows = json.load(open(path))
    rows[1]["status"] = "candidate"
    write_json(path, rows)


def m_missing_codings(root: str) -> None:
    # the published table holds the per-party rows in this layout
    path = os.path.join(root, "data", "codings", "codings.json")
    rows = json.load(open(path))
    write_json(path, [r for r in rows if r.get("party_slug") != "green"])


def m_partial_coverage(root: str) -> None:
    path = os.path.join(root, "data", "codings", "codings.json")
    rows = json.load(open(path))
    ndp = [r for r in rows if r.get("party_slug") == "ndp"]
    rest = [r for r in rows if r.get("party_slug") != "ndp"]
    write_json(path, ndp[:1] + rest)


def m_no_archive(root: str) -> None:
    path = os.path.join(root, "data", "raw", "cpb", "sources.json")
    rows = json.load(open(path))
    rows[0]["archive_url"] = None
    write_json(path, rows)


def m_zero_hash(root: str) -> None:
    path = os.path.join(root, "data", "raw", "onebc", "sources.json")
    rows = json.load(open(path))
    rows[0]["sha256"] = BAD_SHA
    write_json(path, rows)


def m_missing_route(root: str) -> None:
    os.remove(os.path.join(root, "out", "questions", "index.html"))


def m_stale_build(root: str) -> None:
    # a data file changed after the export was written
    future = os.path.getmtime(os.path.join(root, "out", "index.html")) + 3600
    os.utime(os.path.join(root, "data", "codings", "codings.json"), (future, future))


def m_missing_capture(root: str) -> None:
    # the stored bytes a source record points at vanish -> data integrity
    os.remove(os.path.join(root, "data", "raw", "green", "green-0001.html"))


def m_bad_coder_row(root: str) -> None:
    path = os.path.join(root, "data", "codings", "v1", "ndp-coder-a.json")
    rows = json.load(open(path))
    rows[0]["code"] = 9  # off the -2..2 contract scale
    write_json(path, rows)


def m_split_row(root: str) -> None:
    path = os.path.join(root, "data", "codings", "codings.json")
    rows = json.load(open(path))
    rows[0]["status"] = "split"
    rows[0]["code"] = None
    rows[0]["quote"] = ""
    rows[0]["source_id"] = ""
    rows[0]["source_url"] = ""
    rows[0]["coder_codes"] = {"A": 1, "B": -1}
    write_json(path, rows)


def m_fixture_ref(root: str) -> None:
    path = os.path.join(root, "data", "codings", "codings.json")
    rows = json.load(open(path))
    rows[0]["quote"] = "v0-fixture sample data — not a real quote"
    write_json(path, rows)


def m_no_og(root: str) -> None:
    write(os.path.join(root, "out", "index.html"), "<html><head><title>x</title></head><body>"
          "It does not tell you how to vote. Not affiliated with anyone. No accounts, no tracking.</body></html>")


def m_broken_sitemap(root: str) -> None:
    write(os.path.join(root, "out", "sitemap.xml"), "<urlset><url><loc>https://elsewhere.invalid/</loc></url></urlset>")


CASES = [
    ("clean green dataset", None, None, 0),
    ("placeholder marker in build", m_placeholder, "no placeholder content in the build", 1),
    ("third-party tracker", m_tracker, "no third-party trackers or analytics", 1),
    ("external script origin", m_external_script, "no external script/style origins", 1),
    ("disclaimer copy missing", m_no_disclaimer, "disclaimers rendered on every page", 1),
    ("cookie write in src", m_pii, "no PII collection paths", 1),
    ("question left unfrozen", m_unfrozen, "live question set is frozen", 1),
    ("a party has no codings", m_missing_codings, "a coding file exists for every party", 1),
    ("coding coverage gap", m_partial_coverage, "coding coverage is complete", 1),
    ("source without archive_url", m_no_archive, "every source has an archive_url", 1),
    ("zeroed sha256", m_zero_hash, "every source has a real sha256", 1),
    ("built route missing", m_missing_route, "static export contains every route", 1),
    ("stale export (data newer than out/)", m_stale_build, "export is newer than the dataset", 1),
    ("og share card missing", m_no_og, "open graph share card present", 1),
    ("sitemap wrong origin", m_broken_sitemap, "sitemap lists the published origin", 1),
    ("missing capture file (hash mismatch)", m_missing_capture, "data integrity (verify-data.py)", 1),
    ("bad coder row in v1", m_bad_coder_row, "coding validation (validate_codings.py)", 1),
    ("unresolved split in published dataset", m_split_row, "published dataset has no unresolved splits", 1),
    ("fixture reference in published dataset", m_fixture_ref, "published dataset has no fixture references", 1),
]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Self-test for scripts/launch-preflight.py")
    ap.add_argument("--keep", action="store_true", help="keep the temp roots")
    ap.add_argument(
        "--network",
        action="store_true",
        help="also exercise the --online domain check (needs DNS + the .ca RDAP service)",
    )
    args = ap.parse_args(argv)

    for script in ("validate-dataset.py", "launch-preflight.py", "verify-data.py"):
        if not os.path.exists(os.path.join(HERE, script)):
            print(f"cannot run: scripts/{script} missing", file=sys.stderr)
            return 3
    if not os.path.exists(os.path.join(REPO, "agents", "validate_codings.py")):
        print("cannot run: agents/validate_codings.py missing", file=sys.stderr)
        return 3

    failures = 0
    keep_dirs: list[str] = []
    for label, mutate, expect_check, expect_rc in CASES:
        root = tempfile.mkdtemp(prefix="bcvm-preflight-")
        keep_dirs.append(root)
        build_green(root)
        if mutate:
            mutate(root)
        rc, report = run_gate(root)
        ok = rc == expect_rc
        detail = f"exit {rc} (want {expect_rc})"
        if expect_check:
            got = status_of(report, expect_check)
            # a broken dataset also trips the provenance gate; that is expected
            ok = ok and got == "FAIL"
            detail += f"; '{expect_check}'={got}"
        print(f"[{'PASS' if ok else 'FAIL'}] {label}: {detail}")
        failures += 0 if ok else 1

    # default run includes the full static build: a root without a buildable
    # project must trip the build step, not silently skip it.
    root = tempfile.mkdtemp(prefix="bcvm-preflight-")
    keep_dirs.append(root)
    build_green(root)
    rc, report = run_gate(root, build=True)
    checked = status_of(report, "next build is green")
    build_ok = rc == 1 and checked == "FAIL"
    print(
        f"[{'PASS' if build_ok else 'FAIL'}] default runs the full build: "
        f"exit {rc} (want 1), 'next build is green'={checked}"
    )
    failures += 0 if build_ok else 1

    # strict mode: a warning-only run must exit 2. Force a warning by making the
    # root a git repo with uncommitted data, which trips the release-hygiene check.
    root = tempfile.mkdtemp(prefix="bcvm-preflight-")
    keep_dirs.append(root)
    build_green(root)
    subprocess.run(["git", "-c", "init.defaultBranch=main", "init"], cwd=root, capture_output=True)
    rc, report = run_gate(root, strict=True)
    checked_warn = status_of(report, "dataset is committed")
    strict_ok = rc == 2 and checked_warn == "WARN"
    print(
        f"[{'PASS' if strict_ok else 'FAIL'}] --strict exits 2 on warnings only: "
        f"exit {rc}, 'dataset is committed'={checked_warn}"
    )
    failures += 0 if strict_ok else 1
    total = len(CASES) + 2

    if args.network:
        root = tempfile.mkdtemp(prefix="bcvm-preflight-")
        keep_dirs.append(root)
        build_green(root)
        rc, report = run_gate(root, online=True)
        got = status_of(report, "domain bcvotematch.ca is registered")
        ok = rc == 1 and got == "FAIL"
        print(f"[{'PASS' if ok else 'FAIL'}] --online flags an unregistered domain: exit {rc} (want 1); got={got}")
        failures += 0 if ok else 1
        total += 1

    if args.keep:
        print("\ntemp roots kept:")
        for d in keep_dirs:
            print("  " + d)
    else:
        for d in keep_dirs:
            shutil.rmtree(d, ignore_errors=True)

    print(f"\n{total - failures}/{total} cases behaved as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
