#!/usr/bin/env python3
"""verify-data.py — data-integrity audit for BC Vote Match.

Walks every data/raw/<dir>/sources.json, checks each record against the
contract in docs/SCHEMA.md, verifies that every referenced local file
exists and that its sha256 matches the recorded hash, and reports
Wayback archive coverage.

Exits non-zero if any integrity problem is found:
  - unknown/stray directory under data/raw/
  - missing or invalid required field
  - duplicate source id
  - missing local file (local_path or text_path)
  - sha256 mismatch between record and local file

Usage:
  python3 scripts/verify-data.py                     # audit only
  python3 scripts/verify-data.py --write-manifest     # audit + (re)write
      data/manifests/MANIFEST.json from the party sources

The audit is read-only and deterministic: the same tree always produces
the same report. The manifest is a sorted array of
{id, party, url, sha256, local_path, archive_url, fetched_at} for every
source in the five party directories.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST_PATH = REPO_ROOT / "data" / "manifests" / "MANIFEST.json"

# docs/SCHEMA.md: slug in {ndp, cpb, green, onebc, centrebc}
PARTY_SLUGS = ("ndp", "cpb", "green", "onebc", "centrebc")
# data/raw/ridings/ is the schema-sanctioned riding layer (party_slug: null).
ALLOWED_DIRS = set(PARTY_SLUGS) | {"ridings"}

# Fields every sources.json record must carry (docs/SCHEMA.md).
REQUIRED_FIELDS = (
    "id", "party_slug", "type", "title", "url", "published",
    "fetched_at", "sha256", "local_path", "text_path", "archive_url",
)
# Fields that must hold a non-empty value.
NONEMPTY_FIELDS = ("id", "type", "title", "url", "fetched_at", "sha256", "local_path")
# published/text_path/archive_url may legitimately be empty or null
# (e.g. a PDF with no text extract, a page Wayback has not returned yet).

TYPE_ENUM = {"platform", "policy", "release", "speech", "hansard", "media", "other"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_iso_utc(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


def main() -> int:
    write_manifest = "--write-manifest" in sys.argv[1:]
    problems: list[str] = []
    lines: list[str] = []

    lines.append("BC Vote Match — data integrity audit")
    lines.append(f"root: {REPO_ROOT}")
    lines.append("")

    # 1. Directory hygiene: data/raw/ must contain only schema-known dirs.
    raw_dirs = sorted(p.name for p in RAW_DIR.iterdir() if p.is_dir())
    stray = [d for d in raw_dirs if d not in ALLOWED_DIRS]
    for d in stray:
        problems.append(f"stray directory under data/raw/: {d}")
    for d in sorted(ALLOWED_DIRS - set(raw_dirs)):
        problems.append(f"expected directory missing under data/raw/: {d}")
    lines.append(f"data/raw directories: {', '.join(raw_dirs)}")
    if stray:
        lines.append(f"  STRAY DIRECTORIES: {', '.join(stray)}")
    lines.append("")

    total_sources = 0
    total_hash_ok = 0
    total_files_ok = 0
    total_missing = 0
    total_mismatch = 0
    total_archived = 0
    manifest_rows: list[dict] = []

    for slug in sorted(raw_dirs, key=lambda d: (d == "ridings", d)):
        src_file = RAW_DIR / slug / "sources.json"
        if not src_file.exists():
            problems.append(f"{slug}: sources.json missing")
            continue
        try:
            records = json.loads(src_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"{slug}: sources.json is not valid JSON ({exc})")
            continue
        if not isinstance(records, list):
            problems.append(f"{slug}: sources.json must be a JSON array")
            continue

        is_riding = slug == "ridings"
        seen_ids: set[str] = set()
        n_hash_ok = 0
        n_files_ok = 0
        n_missing = 0
        n_mismatch = 0
        n_archived = 0

        for rec in records:
            rid = rec.get("id", "<no id>")
            label = f"{slug}/{rid}"

            # Required fields.
            for field in REQUIRED_FIELDS:
                if field not in rec:
                    problems.append(f"{label}: missing required field '{field}'")
            for field in NONEMPTY_FIELDS:
                if not rec.get(field):
                    problems.append(f"{label}: empty required field '{field}'")

            # Field validity.
            if rec.get("type") not in TYPE_ENUM:
                problems.append(f"{label}: invalid type {rec.get('type')!r}")
            if not SHA256_RE.match(str(rec.get("sha256", ""))):
                problems.append(f"{label}: sha256 is not 64 lowercase hex chars")
            if not is_iso_utc(rec.get("fetched_at")):
                problems.append(f"{label}: fetched_at is not ISO-8601: {rec.get('fetched_at')!r}")
            if is_riding:
                if rec.get("party_slug") is not None or rec.get("phase") != "riding":
                    problems.append(f"{label}: ridings records need party_slug null and phase 'riding'")
            elif rec.get("party_slug") != slug:
                problems.append(f"{label}: party_slug {rec.get('party_slug')!r} does not match directory '{slug}'")

            # Duplicate ids.
            if rid in seen_ids:
                problems.append(f"{label}: duplicate source id")
            seen_ids.add(rid)

            # Local file existence + hash.
            local_path = rec.get("local_path") or ""
            if local_path:
                local = REPO_ROOT / local_path
                if not local.exists():
                    problems.append(f"{label}: local file missing: {local_path}")
                    n_missing += 1
                else:
                    n_files_ok += 1
                    digest = sha256_of(local)
                    if digest == rec.get("sha256"):
                        n_hash_ok += 1
                    else:
                        n_mismatch += 1
                        problems.append(
                            f"{label}: sha256 mismatch for {local_path} "
                            f"(record {str(rec.get('sha256'))[:12]}…, file {digest[:12]}…)"
                        )
            text_path = rec.get("text_path") or ""
            if text_path and not (REPO_ROOT / text_path).exists():
                problems.append(f"{label}: text file missing: {text_path}")
                n_missing += 1

            if rec.get("archive_url"):
                n_archived += 1

            if not is_riding:
                manifest_rows.append({
                    "id": rid,
                    "party": slug,
                    "url": rec.get("url", ""),
                    "sha256": rec.get("sha256", ""),
                    "local_path": local_path,
                    "archive_url": rec.get("archive_url") or "",
                    "fetched_at": rec.get("fetched_at", ""),
                })

        n = len(records)
        total_sources += n
        total_hash_ok += n_hash_ok
        total_files_ok += n_files_ok
        total_missing += n_missing
        total_mismatch += n_mismatch
        total_archived += n_archived
        coverage = (100.0 * n_archived / n) if n else 0.0
        kind = "riding layer" if is_riding else "party sources"
        lines.append(
            f"{slug:9s} {kind:12s} records={n:3d}  files_ok={n_files_ok:3d}  "
            f"sha256_ok={n_hash_ok:3d}  missing={n_missing}  mismatch={n_mismatch}  "
            f"archived={n_archived}/{n} ({coverage:.0f}%)"
        )

    party_total = sum(
        len(json.loads((RAW_DIR / s / "sources.json").read_text(encoding="utf-8")))
        for s in PARTY_SLUGS
        if (RAW_DIR / s / "sources.json").exists()
    )
    lines.append("")
    lines.append(f"party sources total : {party_total}")
    lines.append(f"all records scanned : {total_sources}")
    lines.append(f"local files present : {total_files_ok}")
    lines.append(f"sha256 verified     : {total_hash_ok}")
    lines.append(f"hash mismatches     : {total_mismatch}")
    lines.append(f"missing files       : {total_missing}")
    lines.append(f"archive coverage    : {total_archived}/{total_sources}")
    lines.append("")
    if problems:
        lines.append(f"RESULT: FAIL — {len(problems)} integrity problem(s)")
        for p in problems:
            lines.append(f"  ! {p}")
    else:
        lines.append("RESULT: PASS — 0 integrity problems")

    report = "\n".join(lines)
    print(report)

    if write_manifest:
        manifest_rows.sort(key=lambda r: (r["party"], r["id"]))
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(
            json.dumps(manifest_rows, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\nmanifest written: {MANIFEST_PATH} ({len(manifest_rows)} records)")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
