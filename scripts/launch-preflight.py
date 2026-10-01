#!/usr/bin/env python3
"""launch-preflight.py — the M5 public-launch gate.

Mechanical go/no-go for publishing the static site. It answers one question:
*is the thing in `out/` allowed to go on the public internet?* It does not
decide whether we *want* to launch — that is Martin's call — it decides whether
launching is even possible without shipping placeholder or unsourced content.

Nothing here rewrites the site. The script is read-only over `data/`, `src/` and
`out/`; the one side effect is the build step (`npm run build`, which
regenerates `out/`), and `--no-build` skips it.

The gate runs in a fixed order: data integrity (`scripts/verify-data.py`) →
coding validation (`agents/validate_codings.py` over `data/codings/v1/` and the
published `data/codings/codings.json`) → published-dataset checks (no unresolved
splits, no fixture references) → a full static build → the output, compliance
and release-hygiene checks.

Contract: docs/SCHEMA.md, docs/05-LAUNCH.md. Run from the repo root:

    python3 scripts/launch-preflight.py             # data checks + full build + gate
    python3 scripts/launch-preflight.py --no-build  # judge the existing out/ (no build)
    python3 scripts/launch-preflight.py --json      # machine-readable report
    python3 scripts/launch-preflight.py --online    # + is bcvotematch.ca registered?
    python3 scripts/launch-preflight.py --root DIR  # another checkout

Exit codes
    0  GO        — no failures and no warnings
    1  NO-GO     — at least one FAIL (never publish)
    2  NO-GO     — warnings only, but --strict was passed
    3  could not run (bad arguments / missing repo root)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass, field

PARTY_SLUGS = ["ndp", "cpb", "green", "onebc", "centrebc"]

# Routes the static export must contain for the product to work.
EXPECTED_ROUTES = [
    "index.html",
    "questions/index.html",
    "results/index.html",
    "parties/index.html",
    "methodology/index.html",
    "coding-table/index.html",
    "about/index.html",
    "404.html",
    "robots.txt",
    "sitemap.xml",
    "og.png",
]

# Strings that must never reach the public build. These are the fixture /
# placeholder markers the schema and the M4 scaffold define.
FORBIDDEN_MARKERS = [
    "PLACEHOLDER DATA",
    "Sample data",
    "example.invalid",
    "v0-fixture",
    "not a real quote",
]

# Third-party hosts that would break the "no trackers, no third parties" rule.
TRACKER_HOSTS = [
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
    "connect.facebook.net",
    "facebook.net",
    "hotjar.com",
    "mixpanel.com",
    "segment.io",
    "segment.com",
    "plausible.io",
    "posthog.com",
    "sentry.io",
    "matomo",
    "clarity.ms",
    "cloudflareinsights.com",
    "amplitude.com",
]

# Copy that must actually appear in the published HTML (non-negotiable #4).
# The first three live in SiteFooter, so they must be present on *every* page —
# a stripped footer is a compliance regression, not a style choice.
REQUIRED_ON_EVERY_PAGE = [
    ("not affiliated with", "independence disclaimer"),
    ("does not tell you how to vote", "how-to-vote disclaimer"),
    ("no personal data", "privacy line"),
]
# Home-page-only slogans.
REQUIRED_ON_HOME = [("no accounts, no tracking", "privacy slug line")]

TEXT_EXT = {
    ".html", ".txt", ".json", ".js", ".jsx", ".mjs", ".cjs",
    ".ts", ".tsx", ".css", ".xml", ".svg", ".webmanifest", ".md",
}


@dataclass
class Check:
    name: str
    status: str  # PASS | WARN | FAIL
    detail: str = ""


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str, warn_only: bool = False) -> None:
        if ok:
            self.checks.append(Check(name, "PASS", detail))
        else:
            self.checks.append(Check(name, "WARN" if warn_only else "FAIL", detail))

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.status == "FAIL"]

    @property
    def warnings(self) -> list[Check]:
        return [c for c in self.checks if c.status == "WARN"]

    def to_dict(self) -> dict:
        return {
            "verdict": "NO-GO" if self.failures else "GO",
            "failures": len(self.failures),
            "warnings": len(self.warnings),
            "checks": [
                {"name": c.name, "status": c.status, "detail": c.detail} for c in self.checks
            ],
        }


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError):
        return "INVALID"


def _walk_text_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules"}]
        for name in filenames:
            if os.path.splitext(name)[1].lower() in TEXT_EXT:
                yield os.path.join(dirpath, name)


def _read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


# --------------------------------------------------------------------------- #
# Check groups
# --------------------------------------------------------------------------- #

def check_data_integrity(root: str, rep: Report) -> None:
    """Step 1: scripts/verify-data.py — every capture exists and hash-matches."""
    name = "data integrity (verify-data.py)"
    script = os.path.join(root, "scripts", "verify-data.py")
    if not os.path.exists(script):
        rep.add(name, False, "scripts/verify-data.py is missing")
        return
    proc = subprocess.run(
        [sys.executable, script], cwd=root, capture_output=True, text=True
    )
    lines = (proc.stdout or "").strip().splitlines()
    problems = [ln.strip().lstrip("!").strip() for ln in lines if ln.strip().startswith("!")]
    if proc.returncode == 0:
        scanned = next(
            (ln.split(":", 1)[1].strip() for ln in lines if ln.startswith("all records scanned")),
            "",
        )
        rep.add(name, True, f"exit 0, {scanned} record(s) hash-verified" if scanned else "exit 0")
    else:
        first = problems[0] if problems else f"exit {proc.returncode}"
        rep.add(
            name,
            False,
            (f"{len(problems)} integrity problem(s); first: {first[:90]}" if problems
             else f"exit {proc.returncode}"),
        )


def check_coding_validation(root: str, rep: Report) -> None:
    """Step 2: agents/validate_codings.py over data/codings/v1 + codings.json.

    The validator takes one party per file, so the published aggregate is split
    into per-party views in a temp dir (the repo tree is not touched) and
    validated with exactly the same rules as the coder files.
    """
    name = "coding validation (validate_codings.py)"
    script = os.path.join(root, "agents", "validate_codings.py")
    if not os.path.exists(script):
        rep.add(name, False, "agents/validate_codings.py is missing")
        return
    v1_dir = os.path.join(root, "data", "codings", "v1")
    targets: list[str] = []
    if os.path.isdir(v1_dir):
        for fname in sorted(os.listdir(v1_dir)):
            if not fname.endswith(".json"):
                continue
            stem = os.path.splitext(fname)[0]
            if stem.startswith("_") or "notes" in stem:
                continue  # coder-notes sidecars are not coding rows
            targets.append(os.path.join(v1_dir, fname))
    n_v1 = len(targets)
    if not n_v1:
        rep.add(name, False, "no coding files under data/codings/v1/ (notes sidecars don't count)")
        return

    published = os.path.join(root, "data", "codings", "codings.json")
    rows = _read_json(published)
    if not isinstance(rows, list) or not rows:
        rep.add(name, False, "published data/codings/codings.json missing, unreadable or empty")
        return

    tmp = tempfile.mkdtemp(prefix="bcvm-codings-")
    try:
        groups: dict[str, list] = {}
        for r in rows:
            if isinstance(r, dict):
                groups.setdefault(str(r.get("party_slug") or "unknown"), []).append(r)
        for slug, grows in sorted(groups.items()):
            view = os.path.join(tmp, f"{slug}.json")
            with open(view, "w", encoding="utf-8") as fh:
                json.dump(grows, fh)
            targets.append(view)

        proc = subprocess.run(
            [sys.executable, script, *targets], cwd=root, capture_output=True, text=True
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    out = (proc.stdout or "").strip().splitlines()
    summary = next((ln for ln in reversed(out) if ln.startswith("files=")), "")
    first_err = next(
        (ln.strip().removeprefix("ERROR").strip() for ln in out if ln.strip().startswith("ERROR")),
        "",
    )
    scope = f"{n_v1} file(s) in data/codings/v1 + codings.json ({len(rows)} rows, {len(groups)} parties)"
    if proc.returncode == 0:
        rep.add(name, True, f"{scope}: {summary or 'exit 0'}")
    else:
        rep.add(
            name,
            False,
            f"{scope}; {summary or f'exit {proc.returncode}'}"
            + (f"; first: {first_err[:80]}" if first_err else ""),
        )


# Anything that smells like a fixture rather than a finding (docs/SCHEMA.md).
FIXTURE_TOKEN_RE = re.compile(
    r"fixture|example\.invalid|v0-fixture|not a real quote|sample data|placeholder data",
    re.IGNORECASE,
)
FIXTURE_CODERS = {"fixture", "sample", "demo", "placeholder", "test"}


def check_published_dataset(root: str, rep: Report) -> None:
    """Step 3: the published table must be resolved and real — no splits, no fixtures."""
    splits_name = "published dataset has no unresolved splits"
    fixture_name = "published dataset has no fixture references"
    rows = _read_json(os.path.join(root, "data", "codings", "codings.json"))
    if not isinstance(rows, list) or not rows:
        rep.add(splits_name, False, "data/codings/codings.json missing, unreadable or empty")
        rep.add(fixture_name, False, "data/codings/codings.json missing, unreadable or empty")
        return

    splits: list[str] = []
    fixtures: list[str] = []
    single = 0
    for r in rows:
        if not isinstance(r, dict):
            continue
        label = f"{r.get('party_slug')}/{r.get('question_id')}"
        codes = r.get("coder_codes")
        values = {v for v in codes.values() if isinstance(v, int)} if isinstance(codes, dict) else set()
        n_coded = len([v for v in codes.values() if isinstance(v, int)]) if isinstance(codes, dict) else 0
        if r.get("status") == "split" or (len(values) > 1 and r.get("code") is None):
            splits.append(f"{label} {sorted(values)}")
        elif n_coded == 1:
            single += 1
        for key, val in r.items():
            texts: list[str] = []
            if isinstance(val, str):
                texts.append(val)
            elif isinstance(val, dict):
                texts.extend(v for v in val.values() if isinstance(v, str))
            for text in texts:
                if FIXTURE_TOKEN_RE.search(text):
                    fixtures.append(f"{label}.{key}")
        if isinstance(r.get("coder"), str) and r["coder"].strip().lower() in FIXTURE_CODERS:
            fixtures.append(f"{label}.coder={r['coder']}")

    rep.add(
        splits_name,
        not splits,
        f"{len(splits)}/{len(rows)} rows unresolved, e.g. {splits[0]}" if splits
        else f"{len(rows)} rows all resolved" + (f" ({single} single-coder)" if single else ""),
    )
    rep.add(
        fixture_name,
        not fixtures,
        f"{len(fixtures)} hit(s), e.g. {fixtures[0]}" if fixtures else "clean",
    )


def check_provenance_gate(root: str, rep: Report) -> None:
    """Delegate the per-code provenance rule to the M5 integration gate."""
    validator = os.path.join(root, "scripts", "validate-dataset.py")
    if not os.path.exists(validator):
        rep.add("provenance gate present", False, "scripts/validate-dataset.py is missing")
        return
    proc = subprocess.run(
        [sys.executable, validator, "--json", "--data-root", os.path.join(root, "data")],
        cwd=root,
        capture_output=True,
        text=True,
    )
    detail = ""
    try:
        payload = json.loads(proc.stdout)
        errs = payload.get("errors") or []
        if errs:
            detail = f"{len(errs)} error(s); first: {errs[0][:90]}"
        else:
            detail = f"ok, {len(payload.get('warnings') or [])} warning(s)"
    except (json.JSONDecodeError, AttributeError):
        tail = (proc.stdout or proc.stderr).strip().splitlines()
        detail = tail[-1] if tail else "no output"
    rep.add(
        "provenance gate (validate-dataset.py)",
        proc.returncode == 0,
        detail if proc.returncode else "exit 0",
    )


def check_dataset(root: str, rep: Report) -> None:
    data = os.path.join(root, "data")

    parties = _read_json(os.path.join(data, "parties.json"))
    if isinstance(parties, list):
        slugs = {p.get("slug") for p in parties if isinstance(p, dict)}
        missing = [s for s in PARTY_SLUGS if s not in slugs]
        rep.add(
            "data/parties.json covers all 5 parties",
            not missing,
            f"{len(slugs)} slugs" + (f", missing {missing}" if missing else ""),
        )
    else:
        rep.add("data/parties.json covers all 5 parties", False, "missing or unreadable")

    questions = _read_json(os.path.join(data, "questions", "questions.json"))
    if isinstance(questions, list) and questions:
        not_frozen = [q.get("id") for q in questions if q.get("status") != "frozen"]
        rep.add(
            "live question set is frozen",
            not not_frozen,
            f"{len(questions)} questions, {len(not_frozen)} not frozen"
            + (f" ({not_frozen[:5]}…)" if not_frozen else ""),
        )
    else:
        rep.add("live question set is frozen", False, "data/questions/questions.json missing or empty")

    codings_dir = os.path.join(data, "codings")
    rows: list[dict] = []
    for slug in PARTY_SLUGS:
        rows_for = _read_json(os.path.join(codings_dir, f"{slug}.json"))
        if isinstance(rows_for, list):
            rows.extend(r for r in rows_for if isinstance(r, dict))
    # The published aggregate may hold the per-party rows instead of
    # data/codings/<slug>.json (the two must never coexist — the provenance gate
    # counts one row per party x question). Count coverage from either shape so
    # the gate follows the dataset, not its file layout.
    published = _read_json(os.path.join(codings_dir, "codings.json"))
    if isinstance(published, list):
        rows.extend(r for r in published if isinstance(r, dict))
    pairs = {(r.get("party_slug"), r.get("question_id")) for r in rows}
    per_party = {s: len({q for p, q in pairs if p == s}) for s in PARTY_SLUGS}
    missing_codings = [s for s in PARTY_SLUGS if not per_party.get(s)]
    rep.add(
        "a coding file exists for every party",
        not missing_codings,
        ", ".join(f"{s}={per_party.get(s, 0)}" for s in PARTY_SLUGS),
    )

    # Coverage: one row per party per frozen question.
    if isinstance(questions, list) and questions and rows:
        expected = len(questions) * len(PARTY_SLUGS)
        got = len(pairs)
        rep.add(
            "coding coverage is complete",
            got >= expected,
            f"{got}/{expected} party-question rows",
        )
    else:
        rep.add("coding coverage is complete", False, f"{len(rows)} coding rows found")

    # Archive coverage — the plan treats archive+hash as non-optional.
    # Walk only the contract party dirs (mirrors validate-dataset.py; stray dirs
    # like data/raw/onebc.messy-bak are not part of the dataset).
    sources: list[dict] = []
    for slug in PARTY_SLUGS:
        rows_src = _read_json(os.path.join(data, "raw", slug, "sources.json"))
        if isinstance(rows_src, list):
            sources.extend(r for r in rows_src if isinstance(r, dict))
    no_archive = [s.get("id") for s in sources if not s.get("archive_url")]
    zero_hash = [s.get("id") for s in sources if not s.get("sha256") or set(s["sha256"]) <= {"0"}]
    rep.add(
        "every source has an archive_url",
        not no_archive,
        f"{len(no_archive)}/{len(sources)} sources unarchived",
    )
    rep.add(
        "every source has a real sha256",
        not zero_hash,
        f"{len(zero_hash)}/{len(sources)} sources without a hash",
    )


def check_build(root: str, rep: Report) -> None:
    out = os.path.join(root, "out")
    if not os.path.isdir(out):
        rep.add("static export exists", False, "out/ is missing — run `npm run build`")
        return
    missing = [r for r in EXPECTED_ROUTES if not os.path.exists(os.path.join(out, r))]
    rep.add(
        "static export contains every route",
        not missing,
        f"{len(EXPECTED_ROUTES) - len(missing)}/{len(EXPECTED_ROUTES)} present"
        + (f", missing {missing}" if missing else ""),
    )

    # A stale build is a launch bug: the export must be at least as new as the
    # newest input. 2s tolerance for filesystem timestamp granularity.
    home = os.path.join(out, "index.html")
    if not os.path.exists(home):
        return
    newest, newest_where = 0.0, ""
    for base in ("data", "src"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, base)):
            dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".next"}]
            for name in filenames:
                p = os.path.join(dirpath, name)
                try:
                    m = os.path.getmtime(p)
                except OSError:
                    continue
                if m > newest:
                    newest, newest_where = m, os.path.relpath(p, root)
    for name in ("package.json", "next.config.mjs", "tsconfig.json"):
        p = os.path.join(root, name)
        if os.path.exists(p) and os.path.getmtime(p) > newest:
            newest, newest_where = os.path.getmtime(p), name
    built = os.path.getmtime(home)
    stale = built + 2 < newest
    rep.add(
        "export is newer than the dataset",
        not stale,
        f"stale by {int(newest - built)}s (newest input: {newest_where})" if stale else "fresh",
    )


def check_no_placeholders(root: str, rep: Report) -> None:
    out = os.path.join(root, "out")
    if not os.path.isdir(out):
        rep.add("no placeholder content in the build", False, "out/ is missing")
        return
    hits: dict[str, list[str]] = {}
    for path in _walk_text_files(out):
        text = _read_text(path)
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                hits.setdefault(marker, []).append(os.path.relpath(path, root))
    summary = "; ".join(f"{m!r} in {len(v)} file(s)" for m, v in hits.items())
    rep.add("no placeholder content in the build", not hits, summary or "clean")


def check_compliance(root: str, rep: Report) -> None:
    out = os.path.join(root, "out")
    src = os.path.join(root, "src")

    # 1. No third-party trackers anywhere in shipped code or built output.
    found: dict[str, list[str]] = {}
    for base in (src, out):
        if not os.path.isdir(base):
            continue
        for path in _walk_text_files(base):
            text = _read_text(path)
            for host in TRACKER_HOSTS:
                if host in text:
                    found.setdefault(host, []).append(os.path.relpath(path, root))
    rep.add(
        "no third-party trackers or analytics",
        not found,
        "; ".join(f"{h} in {len(v)} file(s)" for h, v in found.items()) or "clean",
    )

    # 2. No external script/style origins in the export (self-contained static site).
    external: list[str] = []
    for path in _walk_text_files(out) if os.path.isdir(out) else []:
        if os.path.splitext(path)[1] not in {".html"}:
            continue
        for m in re.finditer(r'<(?:script|link)[^>]+(?:src|href)="(https?://[^"]+)"', _read_text(path)):
            url = m.group(1)
            if not url.startswith("https://bcvotematch.ca"):
                external.append(f"{os.path.relpath(path, root)} -> {url}")
    rep.add(
        "no external script/style origins",
        not external,
        "; ".join(sorted(set(external))[:4]) or "self-contained",
    )

    # 3. No PII collection: no cookie writes, no form posts, no beacon.
    pii: list[str] = []
    for path in _walk_text_files(src) if os.path.isdir(src) else []:
        text = _read_text(path)
        if re.search(r"document\.cookie\s*=", text):
            pii.append(f"{os.path.relpath(path, root)}: document.cookie write")
        if re.search(r"navigator\.sendBeacon", text):
            pii.append(f"{os.path.relpath(path, root)}: sendBeacon")
        if re.search(r"<form[^>]+action=\"https?://", text):
            pii.append(f"{os.path.relpath(path, root)}: external form action")
    rep.add("no PII collection paths", not pii, "; ".join(pii) or "clean")

    # 4. Required disclaimer copy is actually rendered, on every page.
    html_files = [
        p for p in _walk_text_files(out) if p.endswith(".html")
    ] if os.path.isdir(out) else []
    missing_copy: list[str] = []
    for needle, label in REQUIRED_ON_EVERY_PAGE:
        offenders = [os.path.relpath(p, root) for p in html_files if needle.lower() not in _read_text(p).lower()]
        if not html_files:
            missing_copy.append(f"{label}: no HTML in out/")
        elif offenders:
            missing_copy.append(f"{label} missing on {len(offenders)} page(s) e.g. {offenders[0]}")
    home = os.path.join(out, "index.html")
    if os.path.exists(home):
        home_html = _read_text(home)
        for needle, label in REQUIRED_ON_HOME:
            if needle.lower() not in home_html.lower():
                missing_copy.append(f"{label} missing on the home page")
    rep.add(
        "disclaimers rendered on every page",
        not missing_copy,
        "; ".join(missing_copy) if missing_copy else f"present on {len(html_files)} page(s)",
    )

    # 5. Share cards: og:image meta in the home page.
    if os.path.exists(home):
        home_html = _read_text(home)
        has_og = 'property="og:image"' in home_html and "/og.png" in home_html
        rep.add("open graph share card present", has_og, "og:image + /og.png" if has_og else "og:image missing")
        canonical = 'rel="canonical"' in home_html
        rep.add("canonical link present", canonical, "rel=canonical" if canonical else "missing")
    else:
        rep.add("open graph share card present", False, "out/index.html missing")

    # 6. robots + sitemap reference the published origin.
    sitemap = os.path.join(out, "sitemap.xml")
    robots = os.path.join(out, "robots.txt")
    sm = _read_text(sitemap) if os.path.exists(sitemap) else ""
    url_count = sm.count("<url>")
    # 6 indexable routes: /, /questions, /parties, /methodology, /coding-table, /about
    # (/results is deliberately excluded in robots.ts).
    rep.add(
        "sitemap lists the published origin",
        "bcvotematch.ca" in sm and url_count >= 6,
        f"{url_count} url entries",
    )
    rb = _read_text(robots) if os.path.exists(robots) else ""
    rep.add(
        "robots.txt present and references the sitemap",
        "sitemap" in rb.lower(),
        "ok" if "sitemap" in rb.lower() else "robots.txt missing or has no sitemap line",
    )


def check_release_hygiene(root: str, rep: Report) -> None:
    """Warnings only — these matter but do not make the build unpublishable."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        dirty = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        relevant = [ln for ln in dirty if "/data/" in ln or ln.startswith("?? data/") or "data/" in ln]
        rep.add(
            "dataset is committed",
            not relevant,
            f"{len(relevant)} uncommitted data change(s)" if relevant else "clean",
            warn_only=True,
        )
    except (OSError, FileNotFoundError):
        rep.add("dataset is committed", False, "git unavailable", warn_only=True)


def check_domain(rep: Report, host: str) -> None:
    """--online only: is the canonical domain actually registered?

    Everything else in this gate is offline and deterministic; this one is not,
    which is why it is opt-in. Publishing under a domain nobody owns is a launch
    bug the offline checks cannot see: bcvotematch.ca currently returns 404
    'Domain not found' from the .ca registry RDAP service.
    """
    url = f"https://rdap.ca.fury.ca/rdap/domain/{host}"
    name = f"domain {host} is registered"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "bcvm-launch-preflight"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8", "replace"))
        events = {e.get("eventAction"): e.get("eventDate") for e in payload.get("events", [])}
        rep.add(name, True, f"registered since {events.get('registration', 'unknown')}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            rep.add(name, False, "not registered (RDAP 404)")
        else:
            rep.add(name, False, f"RDAP HTTP {exc.code} - check manually", warn_only=True)
    except Exception as exc:  # noqa: BLE001 - a network failure must not crash the gate
        rep.add(name, False, f"could not check ({type(exc).__name__})", warn_only=True)


# --------------------------------------------------------------------------- #

def run_checks(root: str, do_build: bool, online: bool = False) -> Report:
    rep = Report()
    # Fixed order (docs/05-LAUNCH.md): data integrity, coding validation, the
    # published dataset, then a full static build, then the output checks.
    check_data_integrity(root, rep)
    check_coding_validation(root, rep)
    check_published_dataset(root, rep)
    if do_build:
        try:
            proc = subprocess.run(
                ["npm", "run", "build"], cwd=root, capture_output=True, text=True
            )
            built = proc.returncode == 0
            detail = "exit 0" if built else f"exit {proc.returncode}"
        except OSError as exc:
            built, detail = False, f"could not run npm: {exc}"
        rep.add("next build is green", built, detail)
    check_provenance_gate(root, rep)
    check_dataset(root, rep)
    check_build(root, rep)
    check_no_placeholders(root, rep)
    check_compliance(root, rep)
    check_release_hygiene(root, rep)
    if online:
        check_domain(rep, "bcvotematch.ca")
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="BC Vote Match public-launch preflight gate.")
    ap.add_argument("--root", default=None, help="repo root (default: parent of scripts/)")
    ap.add_argument(
        "--build",
        action="store_true",
        help="run the full static build (the default; kept for compatibility)",
    )
    ap.add_argument(
        "--no-build",
        action="store_true",
        help="skip `npm run build` and judge the existing out/ (used after a separate build)",
    )
    ap.add_argument("--json", action="store_true", help="emit a machine-readable report")
    ap.add_argument("--strict", action="store_true", help="treat warnings as failures")
    ap.add_argument(
        "--online",
        action="store_true",
        help="also check the canonical domain is registered (network; off by default)",
    )
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root) if args.root else os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    )
    if not os.path.isdir(os.path.join(root, "data")):
        print(f"launch-preflight: {root} does not look like the repo root (no data/)", file=sys.stderr)
        return 3

    rep = run_checks(root, not args.no_build, args.online)

    if args.json:
        print(json.dumps(rep.to_dict(), indent=2))
    else:
        width = max(len(c.name) for c in rep.checks) if rep.checks else 0
        for c in rep.checks:
            print(f"[{c.status:4}] {c.name.ljust(width)}  {c.detail}")
        print()
        verdict = "NO-GO" if rep.failures else "GO"
        print(f"{verdict}: {len(rep.failures)} failure(s), {len(rep.warnings)} warning(s)")
        if rep.failures:
            print("Blocking:")
            for c in rep.failures:
                print(f"  - {c.name}: {c.detail}")

    if rep.failures:
        return 1
    if args.strict and rep.warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
