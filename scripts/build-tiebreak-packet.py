#!/usr/bin/env python3
"""Build a no-tools evidence packet for one (party, question) split.

The packet carries the statement plus the TOP passages for that statement from the
party's own evidence bundle -- the same deterministic keyword+tf-idf ranking the
original coders were given (data/bundles/<party>/<qid>.json, built by the recon
pipeline, not by any coder). Nothing coder-specific is included: no codes, no quotes
chosen by a coder, no rationale.

Usage: python3 scripts/build-tiebreak-packet.py <outdir>
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLITS = [("ndp", "q01"), ("ndp", "q04"), ("cpb", "q19"),
          ("cpb", "q38"), ("green", "q11"), ("green", "q22")]
TOP_N = 6


def main():
    outdir = sys.argv[1]
    for party, qid in SPLITS:
        bundle = json.load(open(os.path.join(REPO, "data/bundles", party, f"{qid}.json"),
                                encoding="utf-8"))
        passages = []
        for p in (bundle.get("passages") or [])[:TOP_N]:
            passages.append({
                "rank": p.get("rank"),
                "score": p.get("score"),
                "source_id": p.get("source_id"),
                "source_type": p.get("source_type"),
                "title": p.get("title"),
                "url": p.get("url"),
                "archive_url": p.get("archive_url"),
                "published": p.get("published"),
                "text": p.get("text") or p.get("quote") or p.get("snippet") or "",
            })
        packet = {
            "party_slug": party,
            "question_id": qid,
            "statement": bundle.get("statement"),
            "topic": bundle.get("topic"),
            "evidence_note": ("Passages are the top tf-idf matches for the statement over "
                              "the party's own fetched corpus (deterministic, built by the "
                              "recon pipeline). They are not a complete corpus."),
            "passages": passages,
        }
        path = os.path.join(outdir, party, f"PACKET-{qid}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(packet, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        got = sum(1 for p in passages if (p["text"] or "").strip())
        print(f"{party}/{qid}: {len(passages)} passages ({got} with text) -> {path}")


if __name__ == "__main__":
    main()
