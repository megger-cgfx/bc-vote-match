#!/usr/bin/env python3
"""Build a blind verification pack for the M3 tie-break.

A blind pack contains ONLY what a fresh verifier may see for its party:
  - the split statements (id + statement + topic + dimensions)
  - the party's sources.json, with text_path rewritten to the pack copy
  - one text file per source, named <source_id>.txt
No coder rows, no coder notes, no _conflicts.json, no codings directory.

Usage: python3 scripts/build-blind-pack.py <out_dir> [party ...]
"""
import json, os, shutil, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPLITS = {
    "ndp": ["q01", "q04"],
    "cpb": ["q19", "q38"],
    "green": ["q11", "q22"],
    "onebc": ["q38"],
}


def bundle_statement(party, qid):
    """The statement text the coders were given (data/bundles/<party>/<qid>.json)."""
    p = os.path.join(REPO, "data/bundles", party, f"{qid}.json")
    if os.path.exists(p):
        b = json.load(open(p))
        if isinstance(b, dict) and b.get("statement"):
            return b["statement"], b.get("topic")
    qs = {q["id"]: q for q in json.load(open(os.path.join(REPO, "data/questions/questions.json")))}
    return qs[qid]["statement"], qs[qid]["topic"]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out = sys.argv[1]
    parties = sys.argv[2:] or sorted(SPLITS)
    qs = {q["id"]: q for q in json.load(open(os.path.join(REPO, "data/questions/questions.json")))}

    for party in parties:
        d = os.path.join(out, party)
        os.makedirs(d, exist_ok=True)
        stmts = []
        for qid in SPLITS[party]:
            s, topic = bundle_statement(party, qid)
            stmts.append({"id": qid, "statement": s, "topic": topic,
                          "dimensions": qs[qid].get("dimensions", [])})
        json.dump(stmts, open(os.path.join(d, "STATEMENTS.json"), "w"), indent=2, ensure_ascii=False)

        src_path = os.path.join(REPO, "data/raw", party, "sources.json")
        src = json.load(open(src_path))
        packed, missing = [], []
        for rec in src:
            tp = rec.get("text_path")
            r = dict(rec)
            if tp:
                src_file = os.path.join(REPO, tp)
                if os.path.exists(src_file):
                    dst = os.path.join(d, rec["id"] + ".txt")
                    shutil.copyfile(src_file, dst)
                    r["text_path"] = rec["id"] + ".txt"
                else:
                    missing.append(rec["id"])
                    r["text_path"] = None
            for k in ("local_path",):
                if k in r:
                    del r[k]
            packed.append(r)
        json.dump(packed, open(os.path.join(d, "sources.json"), "w"), indent=2, ensure_ascii=False)

        # a manifest the verifier must not be able to use to find the coders
        json.dump({
            "party_slug": party,
            "questions": SPLITS[party],
            "sources": len(packed),
            "sources_with_text_copied": len([r for r in packed if r.get("text_path")]),
            "sources_missing_text": missing,
            "note": "Blind pack: contains the party's sources.json and source text only. "
                    "It deliberately contains no coding rows from any earlier pass.",
        }, open(os.path.join(d, "PACK-MANIFEST.json"), "w"), indent=2, ensure_ascii=False)
        print(f"{party}: {len(stmts)} statements, {len(packed)} sources, "
              f"{len(packed) - len(missing)} text files copied, missing={missing}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
