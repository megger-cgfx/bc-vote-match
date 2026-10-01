#!/usr/bin/env python3
"""validate-dataset.py — the M5 integration gate.

Checks that the *real* dataset under data/ is publishable before the site is
allowed to render it: the question set is frozen, every party's non-null code
carries a verbatim quote that is actually present in the cited source, and no
placeholder/fixture record survives anywhere.

Contract: docs/SCHEMA.md. Run from the repo root:

    python3 scripts/validate-dataset.py
    python3 scripts/validate-dataset.py --json
    python3 scripts/validate-dataset.py --data-root /tmp/fixture --draft

Exit codes
    0  pass (no errors)
    1  errors — do not publish
    2  warnings only and --strict-warnings was passed
    3  the validator could not run (bad arguments / unreadable data root)

`--draft` relaxes *coverage* only (missing codings and unfrozen questions become
warnings). Provenance errors are never relaxed: an unsourced code cannot ship in
any mode.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import unicodedata

PARTY_SLUGS = ["ndp", "cpb", "green", "onebc", "centrebc"]
TOPICS = [
    "cost-of-living-taxes",
    "housing",
    "health",
    "climate-environment",
    "indigenous-reconciliation",
    "public-safety",
]
DIMENSIONS = ["economic", "social"]
CONFIDENCES = ["high", "medium", "low"]

CODING_KEYS = {
    "party_slug",
    "question_id",
    "code",
    "quote",
    "source_id",
    "source_url",
    "archive_url",
    "coder",
    "version",
    "created_at",
    "confidence",
}

# Anything that smells like a stand-in rather than a finding.
PLACEHOLDER_RE = re.compile(
    r"(placeholder|PLACEHOLDER|lorem ipsum|TODO|FIXME|TBD|example\.invalid|"
    r"not a real quote|dummy|sample data)",
    re.IGNORECASE,
)
FIXTURE_CODERS = {"fixture", "sample", "demo", "placeholder", "test"}
FIXTURE_VERSION_RE = re.compile(r"(fixture|sample|demo|placeholder)", re.IGNORECASE)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
        self.stats: dict = {}

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.info.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read().strip()
    if not raw:
        raise ValueError(f"{path} is empty")
    return json.loads(raw)


def norm_ws(text: str) -> str:
    """Collapse whitespace + normalise quotes/dashes so a quote that was
    re-wrapped during transcription still matches the source text."""
    text = unicodedata.normalize("NFKC", text)
    for a, b in (
        ("\u2019", "'"),
        ("\u2018", "'"),
        ("\u201c", '"'),
        ("\u201d", '"'),
        ("\u2013", "-"),
        ("\u2014", "-"),
        ("\u00a0", " "),
    ):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip().casefold()


def is_int_code(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and -2 <= v <= 2


def is_iso8601_z(s: str) -> bool:
    if not isinstance(s, str) or not s.endswith("Z"):
        return False
    try:
        _dt.datetime.fromisoformat(s[:-1])
        return True
    except ValueError:
        return False


# --------------------------------------------------------------------------- #
# loaders
# --------------------------------------------------------------------------- #
def load_questions(data_root: str, rep: Report, require_frozen: bool) -> list[dict]:
    path = os.path.join(data_root, "questions", "questions.json")
    if not os.path.exists(path):
        rep.error(f"missing {path} — the live question contract file")
        return []
    try:
        rows = load_json(path)
    except Exception as exc:  # noqa: BLE001
        rep.error(f"{path} is not readable JSON: {exc}")
        return []
    if not isinstance(rows, list) or not rows:
        rep.error(f"{path} must be a non-empty JSON array")
        return []

    seen: set[str] = set()
    for i, q in enumerate(rows):
        where = f"questions.json[{i}]"
        if not isinstance(q, dict):
            rep.error(f"{where} is not an object")
            continue
        qid = q.get("id")
        if not isinstance(qid, str) or not qid:
            rep.error(f"{where} has no string id")
            continue
        if qid in seen:
            rep.error(f"duplicate question id {qid}")
        seen.add(qid)
        if not isinstance(q.get("statement"), str) or not q["statement"].strip():
            rep.error(f"{qid} has no statement")
        if q.get("topic") not in TOPICS:
            rep.error(f"{qid} has unknown topic {q.get('topic')!r}")
        dims = q.get("dimensions")
        if not isinstance(dims, list) or not dims or any(d not in DIMENSIONS for d in dims):
            rep.error(f"{qid} has bad dimensions {dims!r}")
        st = q.get("status")
        if st not in ("candidate", "frozen"):
            rep.error(f"{qid} has bad status {st!r}")

    frozen = [q["id"] for q in rows if isinstance(q, dict) and q.get("status") == "frozen"]
    rep.stats["questions_total"] = len(rows)
    rep.stats["questions_frozen"] = len(frozen)

    if require_frozen:
        if not frozen:
            rep.error(
                "no frozen questions: data/questions/questions.json still holds the candidate "
                "pool. The M2 freeze gate must be approved and applied before integration."
            )
        elif len(frozen) != len(rows):
            stale = sorted({q["id"] for q in rows if isinstance(q, dict)} - set(frozen))
            rep.error(
                f"{len(rows) - len(frozen)} question(s) still status='candidate' in the live "
                f"file ({', '.join(stale[:6])}{'…' if len(stale) > 6 else ''}). "
                "After the freeze, questions.json should contain only the frozen set."
            )
        else:
            rep.note(f"{len(frozen)} frozen questions")
    return [q for q in rows if isinstance(q, dict) and isinstance(q.get("id"), str)]


def load_parties(data_root: str, rep: Report) -> list[dict]:
    path = os.path.join(data_root, "parties.json")
    if not os.path.exists(path):
        rep.error(f"missing {path}")
        return []
    try:
        rows = load_json(path)
    except Exception as exc:  # noqa: BLE001
        rep.error(f"{path} is not readable JSON: {exc}")
        return []
    slugs = [p.get("slug") for p in rows if isinstance(p, dict)]
    unknown = [s for s in slugs if s not in PARTY_SLUGS]
    if unknown:
        rep.error(f"parties.json has slugs outside the contract: {unknown}")
    missing = [s for s in PARTY_SLUGS if s not in slugs]
    if missing:
        rep.error(f"parties.json is missing contract slugs: {missing}")
    rep.stats["parties"] = len([s for s in slugs if s in PARTY_SLUGS])
    return [p for p in rows if isinstance(p, dict)]


def load_sources(data_root: str, rep: Report) -> dict[str, dict[str, dict]]:
    """slug -> {source_id: record}. Also validates the record shape."""
    out: dict[str, dict[str, dict]] = {}
    for slug in PARTY_SLUGS:
        path = os.path.join(data_root, "raw", slug, "sources.json")
        by_id: dict[str, dict] = {}
        out[slug] = by_id
        if not os.path.exists(path):
            rep.warn(f"no source inventory at {path} — codings citing {slug} cannot be verified")
            continue
        try:
            rows = load_json(path)
        except Exception as exc:  # noqa: BLE001
            rep.error(f"{path} is not readable JSON: {exc}")
            continue
        if not isinstance(rows, list):
            rep.error(f"{path} must be a JSON array")
            continue
        for rec in rows:
            if not isinstance(rec, dict):
                rep.error(f"{path} contains a non-object entry")
                continue
            sid = rec.get("id")
            if not isinstance(sid, str) or not sid:
                rep.error(f"{path} has a source with no id")
                continue
            if sid in by_id:
                rep.error(f"duplicate source id {sid} in {path}")
            by_id[sid] = rec
            if rec.get("party_slug") != slug:
                rep.error(f"source {sid} in {slug}/sources.json has party_slug={rec.get('party_slug')!r}")
            sha = rec.get("sha256") or ""
            if not HEX64_RE.match(sha):
                rep.error(f"source {sid} has no valid sha256 ({sha[:12]!r}…)")
            elif sha == "0" * 64:
                rep.error(f"source {sid} has a zeroed sha256 — placeholder record")
            url = rec.get("url") or ""
            if not url.startswith("http"):
                rep.error(f"source {sid} has no http(s) url ({url!r})")
            tp = rec.get("text_path") or ""
            if not tp or not os.path.exists(os.path.join(data_root, "..", tp)) and not os.path.exists(tp):
                rep.warn(f"source {sid} has no readable text_path ({tp!r}) — quote check will be skipped")
            if not rec.get("archive_url"):
                rep.warn(f"source {sid} has no archive_url")
        rep.stats[f"sources_{slug}"] = len(by_id)
    return out


def source_text(data_root: str, rec: dict, cache: dict) -> str | None:
    tp = rec.get("text_path") or ""
    if not tp:
        return None
    for cand in (tp, os.path.join(data_root, "..", tp), os.path.join(data_root, tp)):
        if os.path.exists(cand):
            if cand not in cache:
                with open(cand, "r", encoding="utf-8", errors="replace") as fh:
                    cache[cand] = norm_ws(fh.read())
            return cache[cand]
    return None


# --------------------------------------------------------------------------- #
# the codings checks — the part that actually protects the product
# --------------------------------------------------------------------------- #
def check_codings(
    data_root: str,
    questions: list[dict],
    sources: dict[str, dict[str, dict]],
    rep: Report,
    draft: bool,
) -> tuple[dict, dict[str, set[str]]]:
    codings_dir = os.path.join(data_root, "codings")
    qids = [q["id"] for q in questions]
    qset = set(qids)

    files: list[str] = []
    if os.path.isdir(codings_dir):
        # Published coding rows only. "_"-prefixed audit sidecars (coder notes,
        # conflicts, human decisions, verification) and sub-directories (notes/,
        # v1/, v0/) are metadata or raw coder rounds, not published rows — the
        # site loader (src/lib/data.ts) skips exactly these, so the gate must
        # not treat metadata as a failed coding file either.
        files = sorted(
            f for f in os.listdir(codings_dir)
            if f.endswith(".json")
            and not f.startswith(".")
            and not f.startswith("_")
            and os.path.isfile(os.path.join(codings_dir, f))
        )
    if not files:
        msg = f"no coding files in {codings_dir} — nothing to integrate yet (M3 has not landed)"
        (rep.warn if draft else rep.error)(msg)
        rep.stats["coding_files"] = 0
        rep.stats["codings"] = 0

    text_cache: dict[str, str] = {}
    matrix: dict[str, dict[str, dict]] = {s: {} for s in PARTY_SLUGS}
    seen_pairs: set[tuple[str, str]] = set()
    problems: list[str] = []

    for name in files:
        path = os.path.join(codings_dir, name)
        try:
            rows = load_json(path)
        except Exception as exc:  # noqa: BLE001
            rep.error(f"{name} is not readable JSON: {exc}")
            continue
        if not isinstance(rows, list):
            rep.error(f"{name} must be a JSON array")
            continue
        stem = name[:-5]
        if stem in PARTY_SLUGS:
            # filename is the canonical per-party file; every row must match it
            for rec in rows:
                if isinstance(rec, dict) and rec.get("party_slug") != stem:
                    rep.error(f"{name} contains a row for party_slug={rec.get('party_slug')!r}")

        for i, rec in enumerate(rows):
            where = f"{name}[{i}]"
            if not isinstance(rec, dict):
                rep.error(f"{where} is not an object")
                continue
            slug = rec.get("party_slug")
            qid = rec.get("question_id")
            where = f"{name}[{i}] {slug}/{qid}"

            extra = set(rec) - CODING_KEYS
            if extra:
                # Informational extras (e.g. the published aggregate's
                # `coder_codes`/`status`) do not affect provenance — warn, do not block.
                rep.warn(f"{where}: unknown field(s) {sorted(extra)} — docs/SCHEMA.md is the contract")
            absent = CODING_KEYS - set(rec)
            if absent:
                problems.append(f"{where}: missing field(s) {sorted(absent)}")

            if slug not in PARTY_SLUGS:
                problems.append(f"{where}: party_slug not in the contract")
                continue
            if not isinstance(qid, str) or qid not in qset:
                problems.append(f"{where}: question_id not in the live question set")
                continue
            if not isinstance(slug, str):
                problems.append(f"{where}: party_slug is not a string")
                continue
            pair = (slug, qid)
            if pair in seen_pairs:
                problems.append(f"{where}: duplicate coding for this party+question")
            seen_pairs.add(pair)
            matrix[slug][qid] = rec

            code = rec.get("code")
            quote = rec.get("quote")
            sid = rec.get("source_id")
            surl = rec.get("source_url")

            if code is None:
                for field, val in (("quote", quote), ("source_id", sid), ("source_url", surl)):
                    # "" is the null-equivalent encoding (validate_codings accepts
                    # "quote is null/empty"); any actual citation still fails here.
                    if val is not None and (not isinstance(val, str) or val.strip()):
                        problems.append(f"{where}: code is null but {field} is set — a no-position row cites nothing")
            elif not is_int_code(code):
                problems.append(f"{where}: code {code!r} is not null or an integer in -2..2")
            else:
                # provenance: quote + resolvable source
                if not isinstance(quote, str) or len(quote.strip()) < 40:
                    problems.append(f"{where}: code set but quote is missing or under 40 chars")
                elif PLACEHOLDER_RE.search(quote):
                    problems.append(f"{where}: quote still contains placeholder text")
                if not isinstance(sid, str) or not sid:
                    problems.append(f"{where}: code set but source_id is missing")
                else:
                    rec_src = sources.get(slug, {}).get(sid)
                    if rec_src is None:
                        problems.append(f"{where}: source_id {sid!r} does not resolve in data/raw/{slug}/sources.json")
                    else:
                        if surl and surl != rec_src.get("url"):
                            problems.append(
                                f"{where}: source_url does not match {sid}.url "
                                f"({surl!r} vs {rec_src.get('url')!r})"
                            )
                        if not surl:
                            problems.append(f"{where}: code set but source_url is missing")
                        if isinstance(quote, str) and quote.strip() and not PLACEHOLDER_RE.search(quote):
                            body = source_text(data_root, rec_src, text_cache)
                            if body is None:
                                problems.append(f"{where}: cannot verify quote — source {sid} has no readable text file")
                            elif norm_ws(quote) not in body:
                                problems.append(
                                    f"{where}: quote is NOT present in the cited source {sid} "
                                    "— verbatim provenance fails (SCHEMA.md)"
                                )
                        if not rec_src.get("archive_url"):
                            rep.warn(f"{where}: cited source {sid} has no archive_url")

            conf = rec.get("confidence")
            if code is not None:
                if conf not in CONFIDENCES:
                    problems.append(f"{where}: confidence {conf!r} not in {CONFIDENCES}")
            elif conf not in CONFIDENCES and conf not in (None, "n/a"):
                # null-code rows carry no evidence to rate; null and "n/a" are
                # the same "not applicable" marker (validate_codings agrees).
                problems.append(
                    f"{where}: confidence {conf!r} must be one of {CONFIDENCES}, 'n/a' or null when code is null"
                )
            if not isinstance(rec.get("coder"), str) or not rec["coder"].strip():
                problems.append(f"{where}: coder is missing")
            elif rec["coder"].strip().lower() in FIXTURE_CODERS:
                problems.append(f"{where}: coder {rec['coder']!r} is a fixture coder, not a real coder")
            ver = rec.get("version")
            if not isinstance(ver, str) or not ver.strip():
                problems.append(f"{where}: version is missing")
            elif FIXTURE_VERSION_RE.search(ver):
                problems.append(f"{where}: version {ver!r} marks this as fixture data — must not ship")
            created = rec.get("created_at")
            if not isinstance(created, str) or not created.strip():
                problems.append(f"{where}: created_at is missing")
            elif not is_iso8601_z(created):
                rep.warn(f"{where}: created_at {created!r} is not ISO-8601 UTC (…Z)")

    for p in problems:
        rep.error(p)

    # coverage matrix
    covered = {s: len(matrix[s]) for s in PARTY_SLUGS}
    nulls = {s: sum(1 for c in matrix[s].values() if c.get("code") is None) for s in PARTY_SLUGS}
    rep.stats["coding_files"] = len(files)
    rep.stats["codings"] = len(seen_pairs)
    rep.stats["coverage"] = covered
    rep.stats["null_codes"] = nulls
    rep.stats["expect_rows"] = len(PARTY_SLUGS) * len(qids)

    if qids and len(files):
        for slug in PARTY_SLUGS:
            missing = [q for q in qids if q not in matrix[slug]]
            if missing:
                # a real party file may legitimately omit skipped questions, but a
                # *silent* gap is how asymmetry creeps in — make it loud.
                lvl = rep.warn if draft else rep.error
                lvl(
                    f"{slug}: no coding for {len(missing)} question(s) "
                    f"({', '.join(missing[:6])}{'…' if len(missing) > 6 else ''}) — "
                    "either code it or record an explicit null row"
                )
        rows = sum(len(matrix[s]) for s in PARTY_SLUGS)
        rep.note(
            f"{rows} coding rows across {len(files)} file(s); "
            + ", ".join(f"{s}={covered[s]}({nulls[s]} null)" for s in PARTY_SLUGS)
        )
    return matrix, {s: set(matrix[s]) for s in PARTY_SLUGS}


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", default=None, help="repo data/ directory (default: ./data)")
    ap.add_argument("--draft", action="store_true",
                    help="relax coverage/freeze checks to warnings (provenance is never relaxed)")
    ap.add_argument("--strict-warnings", action="store_true", help="exit 2 when only warnings remain")
    ap.add_argument("--json", action="store_true", help="emit a machine-readable report on stdout")
    ap.add_argument("--no-require-frozen", action="store_true",
                    help="do not require status='frozen' in questions.json")
    args = ap.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_root = args.data_root or os.path.join(root, "data")
    if not os.path.isdir(data_root):
        print(f"validate-dataset: data root not found: {data_root}", file=sys.stderr)
        return 3

    rep = Report()
    rep.stats["data_root"] = data_root

    require_frozen = not args.no_require_frozen and not args.draft
    questions = load_questions(data_root, rep, require_frozen)
    load_parties(data_root, rep)
    sources = load_sources(data_root, rep)
    check_codings(data_root, questions, sources, rep, args.draft)

    if args.json:
        print(json.dumps(
            {
                "ok": rep.ok,
                "errors": rep.errors,
                "warnings": rep.warnings,
                "info": rep.info,
                "stats": rep.stats,
            },
            indent=2,
        ))
    else:
        print(f"validate-dataset  data_root={data_root}  mode={'draft' if args.draft else 'integration'}")
        print("-" * 72)
        for line in rep.info:
            print(f"  ok   {line}")
        for line in rep.warnings:
            print(f"  WARN {line}")
        for line in rep.errors:
            print(f"  FAIL {line}")
        print("-" * 72)
        print(
            f"  {rep.stats.get('questions_frozen', 0)} frozen questions · "
            f"{rep.stats.get('codings', 0)} codings · "
            f"{len(rep.errors)} errors · {len(rep.warnings)} warnings"
        )
        print("  RESULT: " + ("PASS — dataset is publishable" if rep.ok else "BLOCKED — do not publish"))

    if not rep.ok:
        return 1
    if args.strict_warnings and rep.warnings:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
