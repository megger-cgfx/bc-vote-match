#!/usr/bin/env python3
"""verify-tiebreak.py -- gate for the M3 blind tie-break.

Proves, from the artifacts on disk, that:
  1. no published row carries a code while its two coders disagree, unless a blind
     verifier row exists and its code is the published code (or the row is escalated);
  2. every tie-broken row agrees with _conflicts.json (published code, matched coder,
     verifier code) and the conflict records the rule it was decided under;
  2b. every human-tie-broken row agrees with _conflicts.json (the editor's code is the
     published code, it adopts a coder or verifier code on the row, and the record
     carries a reason and an attribution);
  3. every published non-null quote -- adopted or verifier -- is verbatim in the text
     file of the source record it cites, and that record's url/archive_url match;
  4. the blind verifier files pass agents/validate_codings.py --strict, and their
     coder ids are distinct from both original coder ids;
  5. every verified question is present in the verifier rationale sidecar.

Reads: data/codings/codings.json, data/codings/_conflicts.json,
       data/codings/v1/<party>-verifier*.json, data/codings/v1/<party>-coder*.json
Exits non-zero on any failure. Read-only.
"""
import glob
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COD = os.path.join(REPO, "data/codings")
V1 = os.path.join(COD, "v1")
PARTIES = ["ndp", "cpb", "green", "onebc", "centrebc"]

problems = []
notes = []


def norm_ws(text):
    text = (text or "").translate(str.maketrans("\u2018\u2019\u201c\u201d", "''\"\""))
    return re.sub(r"\s+", " ", text).strip()


def as_dict(value):
    """json-loaded values are untyped; keep the helpers total."""
    return value if isinstance(value, dict) else {}


def load(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else []


def sources_for(party):
    return {s["id"]: s for s in load(os.path.join(REPO, "data/raw", party, "sources.json"))}


def text_of(rec, cache):
    tp = (rec or {}).get("text_path") or ""
    fp = os.path.join(REPO, tp) if tp else ""
    if not fp or not os.path.exists(fp):
        return None
    if fp not in cache:
        with open(fp, encoding="utf-8", errors="replace") as f:
            cache[fp] = norm_ws(f.read())
    return cache[fp]


def main():
    published = load(os.path.join(COD, "codings.json"))
    conflicts_doc = load(os.path.join(COD, "_conflicts.json"), {})
    if isinstance(conflicts_doc, list):
        # Pre-freeze shape (a bare array, no disposition/rule fields). Normalise so the
        # check can still see the disagreements; anything it does not name a
        # disposition for is by definition not yet tie-broken.
        conflicts = [dict(c, kind=c.get("kind") or "numeric",
                          disposition=c.get("disposition") or "awaiting-verification",
                          verifier=c.get("verifier"))
                     for c in conflicts_doc]
    else:
        conflicts = conflicts_doc.get("conflicts", [])
    by_key = {(c.get("party_slug"), c.get("question_id")): c for c in conflicts}

    if not published:
        problems.append("codings.json is empty or unreadable")
    if not conflicts:
        problems.append("_conflicts.json has no conflicts array")

    cache = {}
    n_broken = n_escalated = n_human = n_checked_quotes = 0

    # 1 + 2 + 3: published vs conflicts, and quote provenance.
    for row in published:
        party, qid = row.get("party_slug"), row.get("question_id")
        cc = row.get("coder_codes") or {}
        numeric = [c for c in cc.values() if c is not None]
        disagrees = len(set(numeric)) > 1
        status = row.get("status")
        conf = by_key.get((party, qid))

        if disagrees and row.get("code") is not None:
            if status not in ("tie-broken", "human-tie-broken"):
                problems.append(
                    f"{party}/{qid}: coders disagree {cc} but row publishes "
                    f"code={row['code']} with status={status}")
            if not conf or conf.get("disposition") != status:
                problems.append(f"{party}/{qid}: {status} row has no matching "
                                f"conflict record")
            elif status == "tie-broken":
                ver = conf.get("verifier") or {}
                if ver.get("code") != row["code"]:
                    problems.append(f"{party}/{qid}: verifier code {ver.get('code')!r} "
                                    f"!= published {row['code']!r}")
                matched = conf.get("matched_coder")
                if cc.get(matched) != row["code"]:
                    problems.append(f"{party}/{qid}: matched coder {matched} is not the "
                                    f"coder whose code was published")
                if not ver.get("source_id"):
                    problems.append(f"{party}/{qid}: verifier row has no source_id")
                if not (conf.get("tie_break_rule") or "").strip():
                    problems.append(f"{party}/{qid}: conflict records no tie_break_rule")
            else:
                # human-tie-broken: the editor's decision must match the published code
                # and must adopt a code the record already carries, with a reason and an
                # attribution on file (CODEBOOK s7.2).
                if conf.get("human_decision") != row["code"]:
                    problems.append(f"{party}/{qid}: human_decision "
                                    f"{conf.get('human_decision')!r} != published "
                                    f"{row['code']!r}")
                if not (conf.get("human_reason") or "").strip():
                    problems.append(f"{party}/{qid}: human decision has no human_reason")
                if not (conf.get("decided_by") or "").strip():
                    problems.append(f"{party}/{qid}: human decision has no decided_by")
                if not (conf.get("tie_break_rule") or "").strip():
                    problems.append(f"{party}/{qid}: conflict records no tie_break_rule")
                matched = conf.get("matched_coder")
                if matched == "verifier":
                    ver = as_dict(conf.get("verifier"))
                    if ver.get("code") != row["code"]:
                        problems.append(f"{party}/{qid}: human decision adopts the "
                                        f"verifier code but the verifier row disagrees")
                elif matched not in cc or cc.get(matched) != row["code"]:
                    problems.append(f"{party}/{qid}: matched coder {matched!r} is not a "
                                    f"coder whose code was published")
        if disagrees and row.get("code") is None and status not in ("split", "escalated"):
            problems.append(f"{party}/{qid}: coders disagree, code null, but "
                            f"status={status}")
        if status == "escalated":
            n_escalated += 1
        if status == "human-tie-broken":
            n_human += 1

        if row.get("code") is not None:
            src = sources_for(party).get(row.get("source_id"))
            if not src:
                problems.append(f"{party}/{qid}: source_id {row.get('source_id')!r} not in "
                                f"{party} sources.json")
            else:
                if row.get("source_url") != src.get("url"):
                    problems.append(f"{party}/{qid}: source_url does not match sources.json")
                text = text_of(src, cache)
                if text is None:
                    problems.append(f"{party}/{qid}: source text file missing "
                                    f"({src.get('text_path')})")
                elif norm_ws(row.get("quote")) not in text:
                    problems.append(f"{party}/{qid}: published quote not verbatim in "
                                    f"{os.path.basename(src.get('text_path') or '')}")
                else:
                    n_checked_quotes += 1

    n_broken = sum(1 for c in conflicts if c.get("disposition") == "tie-broken")

    # 4 + 5: verifier files.
    verifier_files = []
    for party in PARTIES:
        vpath = os.path.join(V1, f"{party}-verifier.json")
        if not os.path.exists(vpath):
            continue
        verifier_files.append(vpath)
        vrows = load(vpath, [])
        coder_ids = set()
        for p in glob.glob(os.path.join(V1, f"{party}-coder*.json")):
            if "notes" in os.path.basename(p):
                continue
            for r in load(p, []):
                coder_ids.add(r.get("coder"))
        vids = {r.get("coder") for r in vrows}
        if vids & coder_ids:
            problems.append(f"{party}: verifier coder id collides with a coder id "
                            f"({sorted(vids & coder_ids)})")
        for r in vrows:
            cid = (r.get("coder") or "")
            if "verif" not in cid:
                problems.append(f"{party}: verifier row coder {cid!r} is not named "
                                f"as a verifier")
            src = sources_for(party).get(r.get("source_id"))
            text = text_of(src, cache)
            if r.get("code") is not None:
                if text is None or norm_ws(r.get("quote")) not in text:
                    problems.append(f"{party}/{(r.get('question_id') or '?')}: verifier "
                                    f"quote not verbatim in its cited source")
                else:
                    n_checked_quotes += 1
            else:
                notes.append(f"{party}/{(r.get('question_id') or '?')}: verifier coded "
                             f"null (escalates to a human)")
        # rationale sidecar (metadata moved to data/codings/notes/, fall back to v1/)
        npath = None
        for base in (os.path.join(COD, "notes"), V1):
            cand = os.path.join(base, f"{party}-verifier-notes.json")
            if os.path.exists(cand):
                npath = cand
                break
        npath = npath or os.path.join(V1, f"{party}-verifier-notes.json")
        rationales = {r.get("question_id") for r in load(npath, [])}
        for r in vrows:
            if r.get("question_id") not in rationales:
                problems.append(f"{party}/{r.get('question_id')}: no verifier rationale "
                                f"in {os.path.basename(npath)}")

    if verifier_files:
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "agents", "validate_codings.py"),
             "--strict", *verifier_files],
            capture_output=True, text=True)
        if proc.returncode != 0:
            problems.append("agents/validate_codings.py --strict failed on the verifier "
                            f"files:\n{proc.stdout}{proc.stderr}")
        else:
            notes.append("agents/validate_codings.py --strict PASS on "
                         f"{len(verifier_files)} verifier file(s)")
    else:
        notes.append("no verifier files present: no tie-breaks applied yet")

    # 6: the exploratory narrow-window pass is audit evidence in _conflicts.json, and
    # a non-null pass-1 code that differs from the protocol pass must have blocked the
    # tie-break (verifier ambiguity).
    n_pass1 = 0
    for party in PARTIES:
        p1path = os.path.join(V1, f"{party}-verifier-pass1-window.json")
        if not os.path.exists(p1path):
            continue
        for r in load(p1path, []):
            n_pass1 += 1
            if r.get("code") is None:
                continue
            src = sources_for(party).get(r.get("source_id"))
            text = text_of(src, cache)
            if text is None or norm_ws(r.get("quote")) not in text:
                problems.append(f"{party}/{(r.get('question_id') or '?')}: pass-1 window "
                                f"quote not verbatim in its cited source")
            else:
                n_checked_quotes += 1
            conf = by_key.get((party, r.get("question_id")))
            ver = (conf or {}).get("verifier") or {}
            if (conf and conf.get("disposition") == "tie-broken"
                    and r.get("code") != ver.get("code")):
                problems.append(f"{party}/{r.get('question_id')}: tie-broken although a "
                                f"second blind pass returned code {r.get('code')!r} "
                                f"(protocol pass said {ver.get('code')!r})")

    print(f"published rows          : {len(published)}")
    print(f"numeric conflicts       : {sum(1 for c in conflicts if c.get('kind') == 'numeric')}")
    print(f"tie-broken              : {n_broken}")
    print(f"human tie-broken        : {n_human}")
    print(f"escalated to a human    : {n_escalated}")
    print(f"quotes verified verbatim: {n_checked_quotes}")
    for n in notes:
        print(f"note: {n}")
    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nPASS: tie-break gate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
