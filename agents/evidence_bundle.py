#!/usr/bin/env python3
"""evidence_bundle.py -- build a ranked evidence bundle for one party + one question.

Usage:
    python3 agents/evidence_bundle.py --party ndp --question q01 \
        [--questions data/questions/questions.json] [--limit 12] [--out-dir data/bundles]

Reads that party's data/raw/<party>/sources.json, searches every local .txt
source for passages relevant to the question statement (keyword + TF-IDF
scoring, stdlib only, no network), and writes:

    data/bundles/<party>/<qid>.json

containing the statement, the party, and a ranked, deduplicated list of
passages (source id, url, archive url, quote text, score). Ties prefer
higher-priority source types (platform > policy > release/speech > hansard
> media > other).

Retrieval is candidate evidence for a coder to read and verify; it is NOT
a coding. The coder must confirm the quote actually supports a position.
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Source-type priority when scoring ties (higher first), per docs/SCHEMA.md.
TYPE_PRIORITY = {
    "platform": 6, "policy": 5, "release": 4, "speech": 4,
    "hansard": 3, "media": 2, "other": 1,
}

STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "are", "was", "were",
    "been", "being", "have", "has", "had", "will", "would", "could", "should",
    "can", "may", "might", "shall", "not", "but", "its", "it's", "their", "they",
    "them", "his", "her", "our", "your", "who", "whom", "which", "what", "when",
    "where", "how", "why", "all", "any", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "than", "then", "too", "very", "just",
    "about", "into", "over", "under", "again", "further", "once", "here", "there",
    "also", "because", "while", "during", "before", "after", "above", "below",
    "between", "through", "out", "off", "own", "same", "only", "even", "much",
    "many", "like", "make", "makes", "made", "get", "gets", "got", "one", "two",
    "per", "vs", "etc", "onto", "upon", "within", "without", "against", "among",
    "does", "did", "doing", "done", "don't", "doesn't", "didn't", "won't",
    "want", "wants", "need", "needs", "way", "ways", "say", "says", "said",
    "people", "province", "government", "british", "columbia", "columbians",
    "party", "plan", "years", "year", "new", "b.c.", "bc",
}

MAX_PASSAGE_CHARS = 700
MIN_PASSAGE_CHARS = 60
PER_SOURCE_CAP = 3
NEAR_DUP_JACCARD = 0.85


def tokenize(text):
    """Lowercase word tokens, keeping short ones only if digits (e.g. tax)."""
    return [t for t in re.findall(r"[a-z0-9][a-z0-9'\-]*", text.lower())]


def content_terms(tokens):
    """Distinct query terms: content words, stopword-filtered."""
    seen, out = set(), []
    for t in tokenize(tokens) if isinstance(tokens, str) else tokens:
        t = t.strip("'-")
        if len(t) < 3 or t in STOPWORDS or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def term_match(passage_token, term):
    """Exact match, or crude prefix match for simple plurals (tax/taxes)."""
    if passage_token == term:
        return True
    if len(term) >= 4 and len(passage_token) >= 4:
        return passage_token.startswith(term) or term.startswith(passage_token)
    return False


def split_passages(text):
    """Split a source text into passages.

    Paragraph blocks (blank-line separated) are the unit; overlong blocks are
    cut on sentence boundaries into chunks of at most MAX_PASSAGE_CHARS.
    """
    passages = []
    blocks = re.split(r"\n\s*\n", text)
    if len(blocks) <= 1:
        # Some extracts are one long line; fall back to sentence windowing.
        blocks = re.split(r"(?<=[.!?])\s+", text.replace("\n", " "))
        blocks = [" ".join(blocks[i:i + 4]) for i in range(0, len(blocks), 4)]
    for block in blocks:
        block = re.sub(r"[ \t]+", " ", block).strip()
        while len(block) > MAX_PASSAGE_CHARS:
            cut = block.rfind(". ", 0, MAX_PASSAGE_CHARS)
            if cut < MIN_PASSAGE_CHARS:
                cut = block.rfind(" ", 0, MAX_PASSAGE_CHARS)
            if cut < MIN_PASSAGE_CHARS:
                cut = MAX_PASSAGE_CHARS
            piece = block[:cut + 1].strip()
            if len(piece) >= MIN_PASSAGE_CHARS:
                passages.append(piece)
            block = block[cut + 1:].strip()
        if len(block) >= MIN_PASSAGE_CHARS:
            passages.append(block)
    return passages


def build_idf(passage_tokens):
    """Document frequency over all passages of the party corpus."""
    df = {}
    for toks in passage_tokens:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    n = max(len(passage_tokens), 1)
    return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}, n


def score_passage(passage_toks, query_terms, idf, bigrams):
    """TF-IDF mass for query terms, coverage gate, phrase bonus."""
    if not passage_toks:
        return 0.0
    score = 0.0
    matched = 0
    for term in query_terms:
        tf = sum(1 for t in passage_toks if term_match(t, term))
        if tf:
            matched += 1
            score += (1.0 + math.log(tf)) * idf.get(term, 2.0)
    if matched == 0:
        return 0.0
    # Phrase bonus: exact statement bigrams are strong evidence.
    text = " ".join(passage_toks)
    hits = sum(1 for b in bigrams if b in text)
    # Coverage gate: a passage must hit an exact statement phrase or at
    # least two distinct query terms, else it is keyword noise.
    if hits == 0 and matched < 2:
        return 0.0
    # Reward coverage of distinct query terms (quadratic, so scattered
    # one-word matches cannot outrank on-topic passages).
    score *= (matched / len(query_terms)) ** 2
    score += 3.0 * hits
    # Mild length normalization so long passages don't dominate.
    score /= math.sqrt(len(passage_toks) / 40.0 + 1.0)
    return round(score, 4)


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a | b))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--party", required=True, help="party slug, e.g. ndp")
    ap.add_argument("--question", required=True, help="question id, e.g. q01")
    ap.add_argument("--questions", default=os.path.join(REPO, "data/questions/questions.json"))
    ap.add_argument("--limit", type=int, default=12, help="max passages (default 12)")
    ap.add_argument("--out-dir", default=os.path.join(REPO, "data/bundles"))
    args = ap.parse_args()

    party = args.party
    qid = args.question

    # Load question.
    with open(args.questions, encoding="utf-8") as f:
        questions = {q["id"]: q for q in json.load(f)}
    if qid not in questions:
        sys.exit(f"error: question '{qid}' not found in {args.questions}")
    question = questions[qid]

    # Load party sources.
    src_path = os.path.join(REPO, "data/raw", party, "sources.json")
    if not os.path.exists(src_path):
        sys.exit(f"error: no sources index at {src_path}")
    with open(src_path, encoding="utf-8") as f:
        sources = json.load(f)
    by_id = {s["id"]: s for s in sources}

    # Query terms from the statement (+ topic words as weak extra terms).
    statement = question["statement"]
    query_terms = content_terms(statement)
    stmt_toks = tokenize(statement)
    bigrams = set()
    content_idx = [i for i, t in enumerate(stmt_toks)
                   if t not in STOPWORDS and len(t) >= 3]
    for a, b in zip(content_idx, content_idx[1:]):
        if b == a + 1:
            bigrams.add(f"{stmt_toks[a]} {stmt_toks[b]}")

    # Gather passages from all local .txt sources.
    all_passages = []   # (source, passage_text, tokens)
    missing_text = []
    for s in sorted(sources, key=lambda x: x["id"]):
        tp = s.get("text_path") or ""
        fp = os.path.join(REPO, tp) if tp else ""
        if not fp or not os.path.exists(fp):
            missing_text.append(s["id"])
            continue
        with open(fp, encoding="utf-8", errors="replace") as f:
            body = f.read()
        for piece in split_passages(body):
            all_passages.append((s, piece, tokenize(piece)))

    if not all_passages:
        sys.exit(f"error: no readable .txt passages for party '{party}'")

    idf, _ = build_idf([t for _, _, t in all_passages])

    scored = []
    for s, piece, toks in all_passages:
        sc = score_passage(toks, query_terms, idf, bigrams)
        if sc > 0:
            scored.append((sc, TYPE_PRIORITY.get(s.get("type", "other"), 1), s, piece, toks))

    # Rank: score first, higher-priority source type on ties.
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]["id"]))

    # Dedupe exact normalized repeats and near-duplicates (keep better rank).
    picked = []
    picked_words = []  # word sets of already-picked passages (near-dup guard)
    per_source = {}
    seen_norm = set()
    for sc, prio, s, piece, toks in scored:
        if per_source.get(s["id"], 0) >= PER_SOURCE_CAP:
            continue
        norm = normalize(piece)
        if norm in seen_norm:
            continue
        words = set(toks)
        if any(jaccard(words, pw) >= NEAR_DUP_JACCARD for pw in picked_words):
            continue
        picked.append((sc, prio, s, piece, toks))
        picked_words.append(words)
        seen_norm.add(norm)
        per_source[s["id"]] = per_source.get(s["id"], 0) + 1
        if len(picked) >= args.limit:
            break

    passages_out = []
    for rank, (sc, prio, s, piece, toks) in enumerate(picked, 1):
        passages_out.append({
            "rank": rank,
            "score": sc,
            "source_id": s["id"],
            "source_type": s.get("type", "other"),
            "title": s.get("title", ""),
            "url": s.get("url", ""),
            "archive_url": s.get("archive_url"),
            "published": s.get("published", ""),
            "quote": piece,
        })

    out_dir = os.path.join(args.out_dir, party)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{qid}.json")
    bundle = {
        "question_id": qid,
        "statement": statement,
        "topic": question.get("topic", ""),
        "party_slug": party,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "keyword + tf-idf over data/raw/%s/*.txt (stdlib, offline)" % party,
        "query_terms": query_terms,
        "sources_searched": len(sources) - len(missing_text),
        "sources_missing_text": missing_text,
        "passages": passages_out,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"party={party} question={qid}")
    print(f"statement: {statement}")
    print(f"sources searched: {bundle['sources_searched']}"
          + (f" (missing text: {', '.join(missing_text)})" if missing_text else ""))
    print(f"passages written: {len(passages_out)} -> {os.path.relpath(out_path, REPO)}")
    for p in passages_out:
        print(f"  #{p['rank']:>2} score={p['score']:>6.2f} type={p['source_type']:<8} "
              f"{p['source_id']} {p['title'][:60]!r}")
        print(f"      {p['quote'][:140].replace(chr(10), ' ')!r}")


if __name__ == "__main__":
    main()
