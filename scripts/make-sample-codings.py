#!/usr/bin/env python3
"""make-sample-codings.py — regenerate src/fixtures/codings.sample.json + sources.sample.json.

Placeholder data ONLY. Run from the repo root:

    python3 scripts/make-sample-codings.py

Every record it writes is stamped `coder: "fixture"`, `version: "v0-fixture"` and a
quote that literally says it is not a real quote, so placeholder positions can never be
mistaken for sourced findings (docs/SCHEMA.md provenance rule).
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Q = os.path.join(ROOT, "src", "fixtures", "questions.sample.json")
PARTIES = json.load(open(os.path.join(ROOT, "src", "fixtures", "parties.sample.json")))
questions = json.load(open(Q))

FAKE_QUOTE = ("PLACEHOLDER — this is not a real quote. Replace with verbatim text from a "
              "fetched source (data/raw/<party>/<id>.txt) before publication.")

# Deterministic, obviously synthetic pattern. Not a claim about any real party.
# Slugs listed left→right on economics / progressive→traditional on social for the
# *default* sign; individual questions invert or null out to exercise every code path.
LEAN = {"green": -2, "ndp": -1, "centrebc": 0, "onebc": 1, "cpb": 2}

# Questions where the "economic" lean sign is flipped for the purposes of the fixture,
# because agreement with the statement points the other way.
INVERT = {"q02", "q07", "q11", "q14", "q18"}
# Questions where a fixture party has "no published position" (code null).
NULLS = {("centrebc", "q10"), ("centrebc", "q13"), ("onebc", "q03"), ("onebc", "q09"),
         ("green", "q16"), ("ndp", "q17"), ("cpb", "q15")}
# Questions whose statement is anchored on the social axis, so use the social tilt.
SOCIAL = {"q07", "q08", "q11", "q13", "q16", "q17"}


def social_lean(slug):
    # progressive (-) → traditional (+), a different ordering from economics
    return {"green": -2, "ndp": -1, "centrebc": -1, "onebc": 1, "cpb": 2}[slug]


def code_for(slug, q):
    if (slug, q["id"]) in NULLS:
        return None
    base = social_lean(slug) if q["id"] in SOCIAL else LEAN[slug]
    if q["id"] in INVERT:
        base = -base
    # clamp to the −2…+2 scale
    return max(-2, min(2, base))


codings = []
for p in PARTIES:
    slug = p["slug"]
    for q in questions:
        code = code_for(slug, q)
        codings.append({
            "party_slug": slug,
            "question_id": q["id"],
            "code": code,
            "quote": None if code is None else FAKE_QUOTE,
            "source_id": None if code is None else f"{slug}-0001",
            "source_url": None if code is None else f"https://example.invalid/{slug}/placeholder",
            "archive_url": None,
            "coder": "fixture",
            "version": "v0-fixture",
            "created_at": "2026-10-01T00:00:00Z",
            "confidence": "low",
        })

out = os.path.join(ROOT, "src", "fixtures", "codings.sample.json")
json.dump(codings, open(out, "w"), indent=2)
print(f"wrote {out}: {len(codings)} codings "
      f"({sum(1 for c in codings if c['code'] is None)} null)")

sources = []
for p in PARTIES:
    for i, (typ, title) in enumerate([
        ("platform", f"{p['short']} — placeholder platform page"),
        ("release", f"{p['short']} — placeholder news release"),
    ], start=1):
        sources.append({
            "id": f"{p['slug']}-{i:04d}",
            "party_slug": p["slug"],
            "type": typ,
            "title": title,
            "url": f"https://example.invalid/{p['slug']}/{i}",
            "published": "",
            "fetched_at": "2026-10-01T00:00:00Z",
            "sha256": "0" * 64,
            "local_path": "",
            "text_path": "",
            "archive_url": None,
        })
out = os.path.join(ROOT, "src", "fixtures", "sources.sample.json")
json.dump(sources, open(out, "w"), indent=2)
print(f"wrote {out}: {len(sources)} sources")
