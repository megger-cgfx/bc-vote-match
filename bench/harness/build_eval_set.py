"""Build the frozen M8 quality eval set (`M8-Coding-Eval v1`) + its manifest.

Spec: m8_candidates.md (<task-id>) §4.2 (item construction) and §4.5 (freeze).

  90 Part-A items = 5 parties x 18 frozen questions (one item per pair)
  58 Part-B items = every coding row whose reference `code` is null
                 (cpb 17, centrebc 25, onebc 11, ndp 3, green 2)

Where the spec is silent/contradictory, the choice is explicit and recorded in
MANIFEST.json rather than buried in code:

  * Part-A reference row. Codings carry two independent coders per (party,
    question). The reference row is: coder A's row when it codes a position,
    else coder B's non-null row, else coder A's row (both-null pair). Items are
    tagged `coder_agreement` = `unanimous` | `split` | `both_null` and carry
    `reference_codes_all` so K1 can be reported on the unanimous subset too.

  * Part-B source text. §4.2.1 derives the input text from the row's
    `source_id` -- but every Part-B row has `source_id: null`, so the rule is
    unimplementable as written. `--null-source-policy` selects the fallback:
      corpus (default) - the party's own source files in source_id order,
                         concatenated to the same 12 000-char cap
      paired           - the non-null row's source for the same (party, question)
      skip             - emit the item with `status: skipped` and a reason
    The chosen policy, and the resulting per-party counts, go into the manifest.

Prompt text (§4.3) is embedded verbatim; the item carries the rendered
`messages` array so the runner only has to send it unchanged.

Usage:
    python -m harness.build_eval_set --repo <repo root> --out-dir eval
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import subprocess
import sys

# --- §4.3 frozen prompt (verbatim) ---------------------------------------- #

SYSTEM_PROMPT = (
    "You are a neutral policy coder. You will be given one question statement and text from ONE\n"
    "political party's own materials. Decide where THAT PARTY stands on the statement, using ONLY\n"
    "the supplied text. Output a single JSON object and nothing else."
)

USER_TEMPLATE = """QUESTION
id: {question_id}
statement: "{statement}"

SOURCES
source_id: {source_id}
{source_text}

CODE SCALE - agreement of the party with the statement, per the party's own stated position:
 +2  party strongly agrees
 +1  party agrees, with qualifications
  0  party is explicitly neutral / deliberately balanced on this exact question
 -1  party disagrees, with qualifications
 -2  party strongly disagrees
null  the party has NO clear stated position in the supplied sources

RULES
- If the supplied text does not clearly state the party's position on this exact question,
  output code null with quote null and source_id null. "null" is a real answer; do not guess.
- If code is not null, "quote" MUST be copied character-for-character from the supplied SOURCES
  text - contiguous, under 300 characters - and "source_id" MUST be {source_id}.
- "rationale" is one sentence, under 200 characters, saying why the quote means that code.

Return exactly one JSON object:
{{"code": <int or null>, "quote": <string or null>, "source_id": <string or null>, "rationale": "<string>"}}"""

SOURCE_CHAR_CAP = 12000
PARTIES = ["cpb", "centrebc", "onebc", "ndp", "green"]
SET_NAME = "M8-Coding-Eval v1"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_source(repo: str, party: str, source_id: str | None) -> tuple[str | None, str | None]:
    """Returns (text_or_None, reason_if_missing)."""
    if not source_id:
        return None, "row carries no source_id"
    path = os.path.join(repo, "data", "raw", party, f"{source_id}.txt")
    if not os.path.exists(path):
        return None, f"source file missing: data/raw/{party}/{source_id}.txt"
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()[:SOURCE_CHAR_CAP], None


def load(repo: str):
    with open(os.path.join(repo, "data", "questions", "freeze-proposal.json"), encoding="utf-8") as fh:
        questions = {q["id"]: q for q in json.load(fh) if q.get("status") == "frozen"}
    codings = {}
    for p in PARTIES:
        with open(os.path.join(repo, "data", "codings", f"{p}.json"), encoding="utf-8") as fh:
            codings[p] = json.load(fh)
    return questions, codings


def render_messages(question: dict, source_id: str | None, source_text: str) -> list[dict]:
    user = USER_TEMPLATE.format(
        question_id=question["id"],
        statement=question["statement"],
        source_id=source_id,
        source_text=source_text,
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def build(args) -> tuple[list[dict], dict]:
    repo = os.path.abspath(args.repo)
    questions, codings = load(repo)
    by_pair: dict[tuple[str, str], dict[str, dict]] = {}
    for p in PARTIES:
        for r in codings[p]:
            by_pair.setdefault((p, r["question_id"]), {})[r["coder"].split("-")[-1]] = r

    items: list[dict] = []
    notes: collections.Counter = collections.Counter()
    per_party_b: collections.Counter = collections.Counter()

    # ---- Part A: one item per (party, frozen question) ----
    for p in PARTIES:
        for qid in sorted(questions):
            q = questions[qid]
            coders = by_pair.get((p, qid), {})
            a, b = coders.get("a"), coders.get("b")
            codes = {c: (r["code"] if r else None) for c, r in coders.items()}
            if a and a["code"] is not None:
                ref, agreement = a, ("unanimous" if b and b["code"] == a["code"] else "split")
            elif b and b["code"] is not None:
                ref, agreement = b, "split"
            elif a:
                ref, agreement = a, "both_null"
            else:
                notes["part_a_missing_row"] += 1
                continue
            text, why = read_source(repo, p, ref.get("source_id"))
            item = {
                "item_id": f"A-{p}-{qid}",
                "part": "A",
                "party": p,
                "question_id": qid,
                "statement": q["statement"],
                "source_id": ref.get("source_id"),
                "reference_code": ref["code"],
                "reference_confidence": ref.get("confidence"),
                "reference_codes_all": codes,
                "coder_agreement": agreement,
                "stop": ["}"],
            }
            if text is None:
                item.update(status="skipped", skip_reason=why, source_text=None, messages=None)
                notes["part_a_skipped"] += 1
            else:
                item.update(
                    status="ok",
                    source_text=text,
                    messages=render_messages(q, ref.get("source_id"), text),
                )
            items.append(item)

    # ---- Part B: every row whose reference code is null ----
    for p in PARTIES:
        corpus_cache: str | None = None
        for r in codings[p]:
            if r["code"] is not None:
                continue
            per_party_b[p] += 1
            q = questions.get(r["question_id"])
            if q is None:
                notes["part_b_unknown_question"] += 1
                continue
            sid = r.get("source_id")
            text: str | None = None
            if args.null_source_policy == "skip":
                why = "policy=skip"
            else:
                if args.null_source_policy == "paired":
                    twins = by_pair.get((p, r["question_id"]), {})
                    for other in ("a", "b"):
                        t = twins.get(other)
                        if t is not None and t["code"] is not None and t.get("source_id"):
                            sid = t["source_id"]
                            text, why = read_source(repo, p, sid)
                            break
                    else:
                        text, why = None, "no non-null row for this (party, question)"
                else:  # corpus
                    if corpus_cache is None:
                        corpus_cache = _party_corpus(repo, p)
                    sid = f"{p}-corpus"
                    text, why = corpus_cache, None
            item = {
                "item_id": f"B-{p}-{r['question_id']}-{r['coder']}",
                "part": "B",
                "party": p,
                "question_id": r["question_id"],
                "statement": q["statement"],
                "coder": r["coder"],
                "source_id": sid,
                "reference_code": None,
                "reference_confidence": r.get("confidence"),
                "reference_codes_all": {
                    c: rr["code"] for c, rr in by_pair.get((p, r["question_id"]), {}).items()
                },
                "source_policy": args.null_source_policy,
                "stop": ["}"],
            }
            if text is None:
                item.update(status="skipped", skip_reason=why, source_text=None, messages=None)
                notes["part_b_skipped"] += 1
            else:
                item.update(status="ok", source_text=text, messages=render_messages(q, sid, text))
            items.append(item)

    manifest = {
        "set_name": SET_NAME,
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        "generator": "bench/harness/build_eval_set.py",
        "counts": {
            "total": len(items),
            "part_a": sum(1 for i in items if i["part"] == "A"),
            "part_b": sum(1 for i in items if i["part"] == "B"),
            "ok": sum(1 for i in items if i["status"] == "ok"),
            "skipped": sum(1 for i in items if i["status"] == "skipped"),
            "part_b_by_party": dict(per_party_b),
        },
        "policies": {
            "part_a_reference_row": "coder A if non-null else coder B non-null else coder A (both-null pair)",
            "null_source_policy": args.null_source_policy,
            "source_char_cap": SOURCE_CHAR_CAP,
        },
        "notes": dict(notes),
        "decoding": {
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 0,
            "max_tokens": 512,
            "repetition_penalty": None,
            "chat_template": "model default",
            "stop": ["}"],
        },
        "source_hashes": {},
        "git_rev": _git_rev(repo),
    }

    # source hashes for everything actually used + the frozen inputs
    manifest["source_hashes"]["data/questions/freeze-proposal.json"] = sha256_file(
        os.path.join(repo, "data", "questions", "freeze-proposal.json")
    )
    for p in PARTIES:
        manifest["source_hashes"][f"data/codings/{p}.json"] = sha256_file(
            os.path.join(repo, "data", "codings", f"{p}.json")
        )
    for item in items:
        if item["status"] != "ok":
            continue
        sid = item["source_id"]
        if sid and sid.endswith("-corpus"):
            continue
        rel = f"data/raw/{item['party']}/{sid}.txt"
        path = os.path.join(repo, rel)
        if os.path.exists(path) and rel not in manifest["source_hashes"]:
            manifest["source_hashes"][rel] = sha256_file(path)
    return items, manifest


def _party_corpus(repo: str, party: str) -> str:
    """Deterministic proxy corpus: party source files in source_id order, capped."""
    d = os.path.join(repo, "data", "raw", party)
    files = sorted(f for f in os.listdir(d) if f.endswith(".txt"))
    out, total = [], 0
    for f in files:
        with open(os.path.join(d, f), "r", encoding="utf-8", errors="replace") as fh:
            chunk = fh.read()
        header = f"\n\n[{f[:-4]}]\n"
        if total + len(header) >= SOURCE_CHAR_CAP:
            break
        room = SOURCE_CHAR_CAP - total - len(header)
        out.append(header + chunk[:room])
        total += len(header) + min(len(chunk), room)
        if total >= SOURCE_CHAR_CAP:
            break
    return "".join(out)


def _git_rev(repo: str) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", repo, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=20, check=False,
        ).stdout.strip() or None
    except Exception:
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    ap.add_argument("--out-dir", default="eval")
    ap.add_argument("--name", default="m8_eval_v1")
    ap.add_argument("--smoke-out", default=None,
                    help="also write a small balanced subset for the smoke test (e.g. eval/smoke_eval.jsonl)")
    ap.add_argument("--smoke-n", type=int, default=8, help="items in the smoke subset (balanced A/B)")
    ap.add_argument(
        "--null-source-policy",
        choices=["corpus", "paired", "skip"],
        default="corpus",
        help="how Part-B items get their input text (all Part-B rows have source_id: null)",
    )
    args = ap.parse_args(argv)

    items, manifest = build(args)
    os.makedirs(args.out_dir, exist_ok=True)
    jsonl_path = os.path.join(args.out_dir, f"{args.name}.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")

    manifest["artifacts"] = {f"{args.name}.jsonl": sha256_file(jsonl_path)}

    if args.smoke_out:
        ok = [it for it in items if it["status"] == "ok"]
        a = [it for it in ok if it["part"] == "A"]
        b = [it for it in ok if it["part"] == "B"]
        half = max(1, args.smoke_n // 2)
        subset = a[: args.smoke_n - half] + b[:half]
        os.makedirs(os.path.dirname(os.path.abspath(args.smoke_out)) or ".", exist_ok=True)
        with open(args.smoke_out, "w", encoding="utf-8") as fh:
            for it in subset:
                fh.write(json.dumps(it, ensure_ascii=False) + "\n")
        manifest["artifacts"][os.path.basename(args.smoke_out)] = sha256_file(args.smoke_out)
        manifest["counts"]["smoke_subset"] = len(subset)

    man_path = os.path.join(args.out_dir, "MANIFEST.json")
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(json.dumps(manifest["counts"], indent=2))
    print(f"notes: {manifest['notes']}")
    print(f"wrote {jsonl_path}")
    print(f"wrote {man_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
