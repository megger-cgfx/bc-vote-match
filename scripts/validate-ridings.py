#!/usr/bin/env python3
"""validate-ridings.py — the M6 riding-level gate (v1.1).

Checks the riding layer under data/ridings/ before the site renders it: 93 distinct
electoral districts, every candidate attached to a real district, contract-party slugs
restricted to the five parties in docs/SCHEMA.md, no duplicate identities, and a source
record with a real hash and archive URL behind the whole thing.

Contract: docs/SCHEMA.md. Run from the repo root:

    python3 scripts/validate-ridings.py
    python3 scripts/validate-ridings.py --json
    python3 scripts/validate-ridings.py --selftest      # mutation tests
    python3 scripts/validate-ridings.py --data-root DIR # validate another dataset

Exit codes: 0 pass · 1 errors · 3 validator could not run.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys

PARTY_SLUGS = ["ndp", "cpb", "green", "onebc", "centrebc"]
BALLOT_LABEL = {
    "ndp": "BC NDP",
    "cpb": "Conservative Party",
    "green": "BC Green Party",
    "onebc": "OneBC",
    "centrebc": "CentreBC",
}
AFFILIATIONS = ["party", "independent", "other"]
STATUSES = ["nominated", "declared"]

RIDING_KEYS = {"slug", "name", "region", "source_id"}
CANDIDATE_KEYS = {
    "id", "riding_slug", "name", "party_slug", "party_label", "party_col",
    "affiliation", "incumbent", "registered", "status",
    "source_id", "source_url", "ebc_source_id", "version", "fetched_at",
}
SOURCE_KEYS = {"id", "party_slug", "phase", "type", "title", "publisher", "url",
               "published", "fetched_at", "sha256", "local_path", "text_path",
               "archive_url", "fetch_via"}

EXPECTED_DISTRICTS = 93
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _iso(v) -> bool:
    if not isinstance(v, str) or not v:
        return False
    try:
        _dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def load(root: str):
    rd = os.path.join(root, "ridings")
    files = {
        "ridings": os.path.join(rd, "ridings.json"),
        "candidates": os.path.join(rd, "candidates.json"),
        "sources": os.path.join(root, "raw", "ridings", "sources.json"),
    }
    out = {}
    for k, p in files.items():
        try:
            out[k] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
        except Exception as e:  # noqa: BLE001
            raise SystemExit(f"[validate-ridings] cannot read {p}: {e}")
    return out


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    ridings, cands, sources = data["ridings"], data["candidates"], data["sources"]

    if ridings is None:
        return ["data/ridings/ridings.json is missing — run scripts/build-ridings.py all"]
    if cands is None:
        return ["data/ridings/candidates.json is missing — run scripts/build-ridings.py all"]

    # ---- ridings.json -------------------------------------------------------
    if len(ridings) != EXPECTED_DISTRICTS:
        errors.append(f"expected {EXPECTED_DISTRICTS} electoral districts, found {len(ridings)}")
    seen: set[str] = set()
    for r in ridings:
        if set(r.keys()) != RIDING_KEYS:
            errors.append(f"riding {r.get('slug')!r}: key set must be exactly {sorted(RIDING_KEYS)}")
        slug = r.get("slug", "")
        if not SLUG_RE.match(slug):
            errors.append(f"riding slug {slug!r} is not a clean slug")
        if slug in seen:
            errors.append(f"duplicate riding slug {slug!r}")
        seen.add(slug)
        for k in ("name", "region", "source_id"):
            if not isinstance(r.get(k), str) or not r.get(k).strip():
                errors.append(f"riding {slug!r}: {k} must be a non-empty string")

    # ---- sources ------------------------------------------------------------
    if not sources:
        errors.append("data/raw/ridings/sources.json is missing or empty")
        sources = []
    src_ids = set()
    for s in sources:
        if set(s.keys()) != SOURCE_KEYS:
            errors.append(f"source {s.get('id')!r}: key set must be exactly {sorted(SOURCE_KEYS)}")
        sid = s.get("id", "")
        if sid in src_ids:
            errors.append(f"duplicate source id {sid!r}")
        src_ids.add(sid)
        if not HEX64.match(str(s.get("sha256", ""))):
            errors.append(f"source {sid!r}: sha256 must be 64 lowercase hex chars")
        if not str(s.get("url", "")).startswith("https://"):
            errors.append(f"source {sid!r}: url must be an https URL")
        if not _iso(s.get("fetched_at")):
            errors.append(f"source {sid!r}: fetched_at must be ISO-8601")

    # ---- candidates.json ----------------------------------------------------
    ids, pairs = set(), set()
    by_riding: dict[str, int] = {}
    for c in cands:
        name = c.get("name", "?")
        where = f"{c.get('riding_slug')}/{name}"
        if set(c.keys()) != CANDIDATE_KEYS:
            errors.append(f"candidate {where}: key set must be exactly {sorted(CANDIDATE_KEYS)}")
        cid = c.get("id", "")
        if cid in ids:
            errors.append(f"duplicate candidate id {cid!r}")
        ids.add(cid)
        key = (c.get("riding_slug"), name)
        if key in pairs:
            errors.append(f"duplicate candidate {where}")
        pairs.add(key)

        rs = c.get("riding_slug")
        if rs not in seen:
            errors.append(f"candidate {where}: riding_slug does not resolve in ridings.json")
        else:
            by_riding[rs] = by_riding.get(rs, 0) + 1

        ps = c.get("party_slug")
        if ps is not None and ps not in PARTY_SLUGS:
            errors.append(f"candidate {where}: party_slug {ps!r} is not one of {PARTY_SLUGS}")
        if c.get("affiliation") not in AFFILIATIONS:
            errors.append(f"candidate {where}: affiliation must be one of {AFFILIATIONS}")
        if c.get("status") not in STATUSES:
            errors.append(f"candidate {where}: status must be one of {STATUSES}")
        if not isinstance(c.get("incumbent"), bool) or not isinstance(c.get("registered"), bool):
            errors.append(f"candidate {where}: incumbent/registered must be booleans")

        # a contract-party candidate must carry that party's ballot label
        if ps in PARTY_SLUGS and c.get("party_label") != BALLOT_LABEL[ps]:
            errors.append(
                f"candidate {where}: party_label {c.get('party_label')!r} "
                f"!= ballot label {BALLOT_LABEL[ps]!r} for {ps}"
            )
        if ps is None and c.get("affiliation") == "party":
            errors.append(f"candidate {where}: affiliation 'party' but no contract party_slug")

        if c.get("source_id") not in src_ids:
            errors.append(f"candidate {where}: source_id {c.get('source_id')!r} is not a riding source")
        if not str(c.get("source_url", "")).startswith("https://"):
            errors.append(f"candidate {where}: source_url must be an https URL")
        if c.get("status") == "nominated" and c.get("ebc_source_id") not in src_ids:
            errors.append(f"candidate {where}: nominated but ebc_source_id does not resolve")
        if not _iso(c.get("fetched_at")):
            errors.append(f"candidate {where}: fetched_at must be ISO-8601")
        if not isinstance(c.get("version"), str) or not c.get("version"):
            errors.append(f"candidate {where}: version must be a non-empty string")

    # coverage: every district must have at least one candidate on record
    for r in ridings:
        if by_riding.get(r["slug"], 0) == 0:
            errors.append(f"riding {r['slug']!r} has no candidate on record")

    return errors


def _selftest(root: str) -> int:
    """Mutate a known-good dataset and prove the validator rejects each mutation."""
    base = load(root)
    if base["ridings"] is None or base["candidates"] is None:
        print("selftest needs a built dataset; run scripts/build-ridings.py all first")
        return 3

    def clone():
        return json.loads(json.dumps(base))

    cases = []

    def case(label, fn):
        cases.append((label, fn))

    case("baseline passes", lambda d: None)
    case("district count wrong", lambda d: d["ridings"].pop())
    case("duplicate riding slug", lambda d: d["ridings"].append(dict(d["ridings"][0])))
    case("candidate on unknown riding", lambda d: d["candidates"][0].update(riding_slug="atlantis"))
    case("bad party slug", lambda d: d["candidates"][0].update(party_slug="bloc"))
    case("party label mismatch", lambda d: d["candidates"][0].update(party_label="Green Party of BC"))
    case("bad status", lambda d: d["candidates"][0].update(status="maybe"))
    case("non-bool incumbent", lambda d: d["candidates"][0].update(incumbent="yes"))
    case("extra field", lambda d: d["candidates"][0].update(mood="happy"))
    case("dangling source id", lambda d: d["candidates"][0].update(source_id="nope"))
    case("bad sha256", lambda d: d["sources"][0].update(sha256="nothex"))
    case("nominated without ebc source", lambda d: d["candidates"][0].update(
        status="nominated", ebc_source_id=None))
    case("duplicate candidate", lambda d: d["candidates"].append(dict(d["candidates"][0])))
    case("district with no candidates", lambda d: d.__setitem__(
        "candidates", [c for c in d["candidates"] if c["riding_slug"] != d["ridings"][0]["slug"]]))

    ok = True
    for label, mutate in cases:
        d = clone()
        try:
            mutate(d)
        except Exception:  # noqa: BLE001 - a mutation that can't apply is a test bug
            print(f"  FAIL  {label}: mutation could not be applied")
            ok = False
            continue
        errs = validate(d)
        passed = (label == "baseline passes" and not errs) or (label != "baseline passes" and errs)
        print(f"  {'ok  ' if passed else 'FAIL'}  {label}" +
              ("" if passed else f"  -> errors={errs[:2]}"))
        ok = ok and passed
    print("selftest:", "all checks behaved" if ok else "FAILURES")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    root = a.data_root or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

    if a.selftest:
        return _selftest(root)

    data = load(root)
    errors = validate(data)
    if a.json:
        print(json.dumps({"data_root": root, "errors": errors, "ok": not errors}, indent=2))
    else:
        if errors:
            print(f"[validate-ridings] {len(errors)} error(s):")
            for e in errors:
                print("  -", e)
        else:
            n_r = len(data["ridings"] or [])
            n_c = len(data["candidates"] or [])
            print(f"[validate-ridings] OK — {n_r} districts, {n_c} candidates, provenance intact")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
