#!/usr/bin/env python3
"""validate_codings.py -- validate coding files against docs/SCHEMA.md.

Usage:
    python3 agents/validate_codings.py                       # all data/codings/<party>.json
    python3 agents/validate_codings.py data/codings/ndp.json data/codings/green.json

Checks per record (errors, any one fails the file and exits non-zero):
  - required fields all present (missing fields are errors; extra informational
    fields — e.g. the published aggregate's `coder_codes`/`status` — are warnings)
  - party_slug matches the file's party and is one of the known slugs
  - code is an integer in {-2,-1,0,1,2} or null
  - when code is not null: quote non-empty, source_id non-empty, source_url non-empty
  - when code is null: quote is null/empty (schema: "never guess")
  - source_id exists in that party's data/raw/<party>/sources.json
  - source_url matches the sources.json record's url
  - archive_url present when the sources.json record has one
  - confidence in {high, medium, low} (or null when code is null)
  - created_at parses as an ISO-8601 timestamp
  - no duplicate (coder, question_id) pairs within the file

Warnings (reported, do not fail the run):
  - question_id not found in data/questions/questions.json
  - code null but source_id/source_url/archive_url populated
  - archive_url differs from the sources.json record's archive_url
  - quote not found verbatim (whitespace-normalized) in the source's text file

Prints a per-file summary. Exits non-zero on any failure.
"""

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_FIELDS = [
    "party_slug", "question_id", "code", "quote", "source_id", "source_url",
    "archive_url", "coder", "version", "created_at", "confidence",
]
PARTY_SLUGS = ["ndp", "cpb", "green", "onebc", "centrebc"]
CODES = {-2, -1, 0, 1, 2}
CONFIDENCE = {"high", "medium", "low"}


def iso_ok(value):
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def norm_ws(text):
    text = (text or "").translate(str.maketrans("‘’“”", "''\"\""))
    return re.sub(r"\s+", " ", text).strip()


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_file(path):
    """Return (errors, warnings, n_rows, party)."""
    errors, warnings = [], []
    stem = os.path.splitext(os.path.basename(path))[0]
    party = stem
    try:
        rows = load_json(path)
    except (OSError, ValueError) as e:
        return [f"unreadable or invalid JSON: {e}"], [], 0, party
    if not isinstance(rows, list):
        return ["top-level value must be a JSON array of coding records"], [], 0, party

    # Coder files are named like ndp-coderA.json or onebc-coderB-part2.json, so the
    # filename stem is not always a party slug. When it is not, infer the party from
    # the rows themselves rather than failing on a naming convention.
    if party not in PARTY_SLUGS:
        slugs = {r.get("party_slug") for r in rows if isinstance(r, dict)}
        slugs.discard(None)
        if len(slugs) == 1:
            party = str(slugs.pop())
        else:
            warnings.append(
                f"filename stem {stem!r} is not a party slug and the rows do not agree "
                "on party_slug; party-scoped checks may be skipped"
            )

    # Party sources index.
    src_path = os.path.join(REPO, "data/raw", party, "sources.json")
    sources = {}
    if os.path.exists(src_path):
        sources = {s["id"]: s for s in load_json(src_path)}
    else:
        warnings.append(f"no sources index at {os.path.relpath(src_path, REPO)}; "
                        "source checks skipped")

    # Question index (optional).
    q_path = os.path.join(REPO, "data/questions/questions.json")
    qids = set()
    if os.path.exists(q_path):
        qids = {q["id"] for q in load_json(q_path)}

    # Text cache for verbatim-quote warnings.
    text_cache = {}

    seen_pairs = set()
    for i, row in enumerate(rows):
        tag = f"row {i + 1}"
        if isinstance(row, dict):
            qid = row.get("question_id")
            tag = f"row {i + 1} ({qid})"

        if not isinstance(row, dict):
            errors.append(f"{tag}: record must be a JSON object")
            continue

        # Fields.
        keys = set(row)
        missing = [k for k in REQUIRED_FIELDS if k not in keys]
        extra = sorted(keys - set(REQUIRED_FIELDS))
        if missing:
            errors.append(f"{tag}: missing fields {missing}")
        if extra:
            # Informational extras (e.g. the published aggregate's `coder_codes`
            # and `status`) do not affect provenance; only missing fields fail.
            warnings.append(f"{tag}: extra fields {extra} (informational only — schema: do not invent fields)")
        if missing:
            continue  # remaining checks need the fields

        # Party slug.
        if row["party_slug"] != party:
            errors.append(f"{tag}: party_slug {row['party_slug']!r} does not match "
                          f"file party {party!r}")
        if row["party_slug"] not in PARTY_SLUGS:
            errors.append(f"{tag}: party_slug {row['party_slug']!r} not in {PARTY_SLUGS}")

        # Code.
        code = row["code"]
        if code is not None and (not isinstance(code, int) or isinstance(code, bool)
                                 or code not in CODES):
            errors.append(f"{tag}: code {code!r} must be an int in -2..2 or null")

        # Quote / provenance coherence.
        quote = row["quote"]
        source_id = row["source_id"]
        source_url = row["source_url"]
        archive_url = row["archive_url"]
        if code is not None:
            if not (isinstance(quote, str) and quote.strip()):
                errors.append(f"{tag}: quote must be non-empty when code is {code}")
            if not (isinstance(source_id, str) and source_id.strip()):
                errors.append(f"{tag}: source_id must be non-empty when code is {code}")
            if not (isinstance(source_url, str) and source_url.strip()):
                errors.append(f"{tag}: source_url must be non-empty when code is {code}")
        else:
            if quote not in (None, ""):
                errors.append(f"{tag}: quote must be null when code is null (never guess)")
            for field in ("source_id", "source_url", "archive_url"):
                if row[field] not in (None, ""):
                    warnings.append(f"{tag}: {field} populated while code is null")

        # Source cross-checks.
        if isinstance(source_id, str) and source_id.strip():
            rec = sources.get(source_id)
            if rec is None:
                errors.append(f"{tag}: source_id {source_id!r} not in {party}'s sources.json")
            else:
                if source_url != rec.get("url"):
                    errors.append(f"{tag}: source_url {source_url!r} does not match "
                                  f"sources.json url {rec.get('url')!r}")
                if rec.get("archive_url") and not (isinstance(archive_url, str)
                                                   and archive_url.strip()):
                    errors.append(f"{tag}: archive_url missing but source record has "
                                  f"one ({rec.get('archive_url')!r})")
                if (isinstance(archive_url, str) and archive_url.strip()
                        and rec.get("archive_url") and archive_url != rec["archive_url"]):
                    warnings.append(f"{tag}: archive_url differs from sources.json record")
                # Verbatim quote check (whitespace-normalized containment).
                if isinstance(quote, str) and quote.strip():
                    tp = rec.get("text_path") or ""
                    fp = os.path.join(REPO, tp) if tp else ""
                    if fp and os.path.exists(fp):
                        if fp not in text_cache:
                            with open(fp, encoding="utf-8", errors="replace") as f:
                                text_cache[fp] = norm_ws(f.read())
                        if norm_ws(quote) not in text_cache[fp]:
                            warnings.append(f"{tag}: quote not found verbatim in "
                                            f"{os.path.basename(fp)}")

        # Enum + format fields.
        if code is not None:
            if row["confidence"] not in CONFIDENCE:
                errors.append(f"{tag}: confidence {row['confidence']!r} must be one of "
                              f"{sorted(CONFIDENCE)} when code is not null")
        elif row["confidence"] not in CONFIDENCE | {None, "n/a"}:
            # null-code rows carry no evidence to rate; null and the published
            # aggregate's "n/a" are the same "not applicable" marker.
            errors.append(f"{tag}: confidence {row['confidence']!r} must be one of "
                          f"{sorted(CONFIDENCE)}, 'n/a' or null")
        if not iso_ok(row["created_at"]):
            errors.append(f"{tag}: created_at {row['created_at']!r} is not ISO-8601")
        for field in ("coder", "version"):
            if not (isinstance(row[field], str) and row[field].strip()):
                errors.append(f"{tag}: {field} must be a non-empty string")

        # Duplicates.
        pair = (row.get("coder"), row.get("question_id"))
        if pair in seen_pairs:
            errors.append(f"{tag}: duplicate (coder, question_id) = {pair}")
        seen_pairs.add(pair)

        # Question exists.
        if qids and row.get("question_id") not in qids:
            warnings.append(f"{tag}: question_id not found in questions.json")

    return errors, warnings, len(rows), party


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*",
                    help="coding files to validate (default: data/codings/<party>.json)")
    ap.add_argument("--strict", action="store_true",
                    help="treat warnings as failures")
    args = ap.parse_args()

    files = args.files
    if not files:
        files = [p for p in (os.path.join(REPO, "data/codings", f"{s}.json")
                             for s in PARTY_SLUGS) if os.path.exists(p)]
        if not files:
            sys.exit("error: no coding files found; pass paths explicitly")

    any_fail = False
    total_rows = total_err = total_warn = 0
    for path in files:
        if not os.path.exists(path):
            print(f"FAIL {path}: file not found")
            any_fail = True
            continue
        errors, warnings, n, party = validate_file(path)
        failed = bool(errors) or (args.strict and bool(warnings))
        status = "FAIL" if failed else "PASS"
        any_fail = any_fail or failed
        total_rows += n
        total_err += len(errors)
        total_warn += len(warnings)
        rel = os.path.relpath(path, REPO)
        shown = rel if not rel.startswith("..") else path
        print(f"{status} {shown}  party={party}  rows={n}  "
              f"errors={len(errors)}  warnings={len(warnings)}")
        for e in errors:
            print(f"  ERROR   {e}")
        for w in warnings:
            print(f"  warning {w}")

    print(f"\nfiles={len(files)} rows={total_rows} errors={total_err} "
          f"warnings={total_warn} -> {'FAIL' if any_fail else 'PASS'}")
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
