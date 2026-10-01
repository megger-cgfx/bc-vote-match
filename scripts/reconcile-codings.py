#!/usr/bin/env python3
"""reconcile-codings.py -- merge independent coder files into one published dataset.

Rule (docs/CODEBOOK.md s7, "Resolution ladder"):

  both coders coded, agree                      -> publish the code, status "agreed"
  both coders coded, disagree, verifier present -> the blind third pass decides:
        verifier code == coder A or coder B     -> publish that code, status "tie-broken"
        verifier code == anything else          -> publish null, status "escalated"
                                                   (verifier disagrees with both;
                                                    human tie-break, CODEBOOK s7.2)
        a second blind pass present whose code
        is non-null and differs from the first  -> publish null, status "escalated"
                                                   (verifier ambiguity; the two passes
                                                    read the same evidence differently)
  both coders coded, disagree, no verifier      -> publish null, status "split"
  exactly one coder coded                       -> publish the code, status "single-coder"
  neither coder coded                           -> publish null, status "no-position"

An escalated row (or any numeric disagreement) that carries a human decision in
data/codings/_human-decisions.json publishes that code, status "human-tie-broken"
(CODEBOOK s7.2, the editor's tie-break). The decision must equal a code already read on
the row - coder A, coder B or a blind pass - so the published quote always belongs to the
code it supports; a decision for a code nobody read is ignored and the row stays escalated.

The published quote/source of a tie-broken row is the adopted coder's own row, so the
quote always belongs to the code it supports. The verifier's row (code, quote, source,
confidence) is preserved verbatim in _conflicts.json, so the decision is auditable
without looking at the raw coder files.

Reads:
  data/codings/v1/<party>-coder{A,B}[-partN].json   independent coder rows
  data/codings/v1/<party>-verifier.json             blind third pass (optional)
  data/codings/v1/<party>-verifier-notes.json       verifier rationale (optional)
  data/codings/_human-decisions.json                editor tie-breaks (optional, hand-written)

Writes:
  data/codings/codings.json          published table, one row per party x question
  data/codings/_conflicts.json       every disagreement + its disposition and evidence
  data/codings/RECONCILE-REPORT.md   human-readable summary

Usage:
  python3 scripts/reconcile-codings.py [--dry-run]
"""
import argparse
import json
import glob
import os
import re
from datetime import datetime, timezone
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V1 = os.path.join(REPO, "data/codings/v1")
OUT = os.path.join(REPO, "data/codings/codings.json")
CONFLICTS = os.path.join(REPO, "data/codings/_conflicts.json")
REPORT = os.path.join(REPO, "data/codings/RECONCILE-REPORT.md")
HUMAN = os.path.join(REPO, "data/codings/_human-decisions.json")

PARTIES = ["ndp", "cpb", "green", "onebc", "centrebc"]
CONF_RANK = {"high": 0, "medium": 1, "low": 2}
TIE_BREAK_RULE = ("docs/CODEBOOK.md s7 - blind third pass decides; a second pass that "
                  "disagrees, or a pass that matches neither coder, escalates to a human")
HUMAN_TIE_BREAK_RULE = ("docs/CODEBOOK.md s7.2 - the editor breaks the tie; the decision "
                        "is final and must adopt a code already read on the row")


def load_rows(path):
    try:
        rows = json.load(open(path, encoding="utf-8"))
    except Exception:
        return []
    return rows if isinstance(rows, list) else []


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


NOTES = os.path.join(REPO, "data/codings/notes")


def sidecar_rows(party, stem):
    """Verifier metadata sidecars live in data/codings/notes/ (moved there from
    v1/); fall back to v1/ so either layout resolves."""
    for base in (NOTES, V1):
        rows = load_rows(os.path.join(base, f"{party}-{stem}.json"))
        if rows:
            return rows
    return []


def coder_files(party):
    """Return {coder_key: [paths]} for a party, handling split part files."""
    out = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(V1, f"{party}-coder*.json"))):
        if "notes" in os.path.basename(p):
            continue
        m = re.match(rf"{party}-coder([AB])", os.path.basename(p))
        if m:
            out[m.group(1)].append(p)
    return out


def verifier_rows(party):
    """Blind third-pass rows for a party, as {question_id: row}."""
    rows = {}
    for row in load_rows(os.path.join(V1, f"{party}-verifier.json")):
        if row.get("question_id"):
            rows[row["question_id"]] = row
    return rows


def verifier_notes(party):
    notes = {}
    for row in sidecar_rows(party, "verifier-notes"):
        if row.get("question_id"):
            notes[row["question_id"]] = row.get("rationale", "")
    return notes


def verifier_pass1_rows(party):
    """The exploratory narrow-window pass, kept for the audit trail only."""
    rows = {}
    for row in sidecar_rows(party, "verifier-pass1-window"):
        if row.get("question_id"):
            rows[row["question_id"]] = row
    return rows


def human_decisions():
    """Editor tie-breaks as {(party_slug, question_id): decision dict}.

    Hand-written input (data/codings/_human-decisions.json), so it survives a re-run of
    this script: the decisions are the durable record, _conflicts.json is regenerated.
    """
    doc = load_json(HUMAN, {})
    if isinstance(doc, dict):
        defaults = {k: doc[k] for k in ("decided_by", "decided_at") if doc.get(k)}
        doc = doc.get("decisions", [])
    else:
        defaults = {}
    out = {}
    for row in doc if isinstance(doc, list) else []:
        party, qid = row.get("party_slug"), row.get("question_id")
        if party and qid and row.get("decision") is not None:
            merged = dict(defaults)
            merged.update(row)
            out[(party, qid)] = merged
    return out


def pass_brief(row):
    if not row:
        return None
    return {
        "coder": row.get("coder"),
        "code": row.get("code"),
        "confidence": row.get("confidence"),
        "quote": row.get("quote"),
        "source_id": row.get("source_id"),
    }


def brief(rows):
    """A short, auditable view of one coder row."""
    return {
        "code": rows.get("code"),
        "confidence": rows.get("confidence"),
        "quote": rows.get("quote"),
        "source_id": rows.get("source_id"),
    }


def rule_resolve(rows, verifier, notes, pass1=None):
    """Apply the resolution ladder to one (party, question).

    pass1 is the exploratory narrow-window pass (optional). A tie-break is only
    published when the two blind passes do not contradict each other; a non-null
    pass-1 code that differs from the protocol pass is 'verifier ambiguity' and
    escalates to a human, exactly like a verifier that agrees with neither coder.

    Returns (published_row_fields, conflict_or_None).
    """
    coded = {c: r for c, r in rows.items() if r.get("code") is not None}
    codes = {r["code"] for r in coded.values()}
    coder_codes = {c: r.get("code") for c, r in sorted(rows.items())}

    if not coded:
        return (None, "no-position", "n/a", {}), None

    if len(codes) == 1 and len(coded) >= 2:
        adopted = coded[sorted(coded)[0]]
        conf = min((r.get("confidence") or "medium" for r in coded.values()),
                   key=lambda c: CONF_RANK.get(c, 1))
        return (adopted["code"], "agreed", conf, adopted), None

    if len(codes) == 1:
        first = sorted(coded)[0]
        adopted = coded[first]
        null_by = [c for c, r in rows.items() if r.get("code") is None]
        conflict = None
        if null_by:
            # CODEBOOK s7 counts a code-vs-null pair as a real disagreement (whether
            # any evidence exists). Recorded here, but the publish rule for v1 keeps
            # the single coder's code at low confidence; flagged in the report.
            conflict = {
                "party_slug": adopted.get("party_slug"),
                "question_id": adopted.get("question_id"),
                "kind": "code-vs-null",
                "coder_a": brief(rows.get("A", {})),
                "coder_b": brief(rows.get("B", {})),
                "spread": None,
                "verifier": None,
                "disposition": "single-coder-published",
                "published_code": adopted["code"],
                "matched_coder": first,
                "tie_break_rule": TIE_BREAK_RULE,
            }
        return (adopted["code"], "single-coder", "low", adopted), conflict

    # A real disagreement between two coded values.
    lo, hi = sorted(codes)
    conflict = {
        "party_slug": rows[sorted(rows)[0]].get("party_slug"),
        "question_id": rows[sorted(rows)[0]].get("question_id"),
        "kind": "numeric",
        "coder_a": brief(rows.get("A", {})),
        "coder_b": brief(rows.get("B", {})),
        "spread": hi - lo,
        "verifier": None,
        "disposition": None,
        "published_code": None,
        "matched_coder": None,
        "tie_break_rule": TIE_BREAK_RULE,
    }

    if verifier is None:
        conflict["disposition"] = "awaiting-verification"
        return (None, "split", "n/a", {}), conflict

    conflict["verifier"] = {
        "code": verifier.get("code"),
        "confidence": verifier.get("confidence"),
        "quote": verifier.get("quote"),
        "source_id": verifier.get("source_id"),
        "coder": verifier.get("coder"),
        "rationale": notes.get(conflict["question_id"]),
    }

    matches = [c for c, r in coded.items() if r["code"] == verifier.get("code")]
    conflict["verifier_passes"] = [pass_brief(pass1), pass_brief(verifier)]
    if not matches:
        conflict["disposition"] = "escalated"
        conflict["escalation_reason"] = "verifier-agrees-with-neither-coder"
        return (None, "escalated", "n/a", {}), conflict

    # Two blind passes that read the same evidence and land on different codes are
    # the "verifier cannot resolve it" case in CODEBOOK s7.2, so they escalate
    # rather than let the later pass win by being later.
    if pass1 is not None and pass1.get("code") is not None and pass1["code"] != verifier.get("code"):
        conflict["disposition"] = "escalated"
        conflict["escalation_reason"] = "verifier-ambiguity-two-passes-disagree"
        return (None, "escalated", "n/a", {}), conflict

    matched = sorted(matches)[0]
    adopted = coded[matched]
    # Conservative: a tie-broken row carries the weaker of the two supporting
    # confidences (the adopted coder's and the verifier's).
    conf = max((adopted.get("confidence") or "medium",
                verifier.get("confidence") or "medium"),
               key=lambda c: CONF_RANK.get(c, 1))
    conflict["disposition"] = "tie-broken"
    conflict["published_code"] = adopted["code"]
    conflict["matched_coder"] = matched
    return (adopted["code"], "tie-broken", conf, adopted), conflict


def resolve(rows, verifier, notes, pass1=None, human=None):
    """rule_resolve(), then the editor's tie-break from _human-decisions.json if present.

    A human decision only applies to a numeric disagreement, and only when it adopts a
    code the row already carries (coder A, coder B or a blind pass); adopting any other
    value would publish a code with no quote behind it, so that row stays escalated and
    the rejection is recorded on the conflict.
    """
    fields, conflict = rule_resolve(rows, verifier, notes, pass1)
    if conflict is None or conflict.get("kind") != "numeric" or human is None:
        return fields, conflict

    choice = human.get("decision")
    adopt, matched = None, None
    if rows.get("A", {}).get("code") == choice:
        adopt, matched = rows["A"], "A"
    elif rows.get("B", {}).get("code") == choice:
        adopt, matched = rows["B"], "B"
    elif verifier is not None and verifier.get("code") == choice:
        adopt, matched = verifier, "verifier"
    if adopt is None:
        conflict["human_decision_ignored"] = (
            f"{choice!r} is not a code on this row (coder A, coder B or a blind pass)")
        return fields, conflict

    conflict["disposition"] = "human-tie-broken"
    conflict["human_decision"] = choice
    conflict["human_reason"] = human.get("reason", "")
    conflict["decided_by"] = human.get("decided_by", "")
    conflict["decided_at"] = human.get("decided_at", "")
    conflict["matched_coder"] = matched
    conflict["published_code"] = choice
    conflict["tie_break_rule"] = HUMAN_TIE_BREAK_RULE
    if human.get("statement_coded"):
        conflict["statement_coded"] = human["statement_coded"]
    return (choice, "human-tie-broken", adopt.get("confidence") or "medium", adopt), conflict


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true",
                    help="print the outcome without writing any file")
    args = ap.parse_args()

    published, report, conflicts = [], [], []
    totals = defaultdict(lambda: defaultdict(int))
    hrules = human_decisions()

    for party in PARTIES:
        files = coder_files(party)
        if not files:
            report.append(f"- {party}: no coder files")
            continue

        by_q = defaultdict(dict)
        for coder, paths in files.items():
            for path in paths:
                for row in load_rows(path):
                    qid = row.get("question_id")
                    if qid:
                        by_q[qid][coder] = row

        vrows = verifier_rows(party)
        vnotes = verifier_notes(party)
        vpass1 = verifier_pass1_rows(party)

        agree = split = single = nopos = broken = escalated = human = 0
        for qid in sorted(by_q):
            rows = by_q[qid]
            (code, status, conf, src), conflict = resolve(
                rows, vrows.get(qid), vnotes, vpass1.get(qid), hrules.get((party, qid)))
            if conflict:
                conflicts.append(conflict)
            if status == "agreed":
                agree += 1
            elif status == "split":
                split += 1
            elif status == "single-coder":
                single += 1
            elif status == "no-position":
                nopos += 1
            elif status == "tie-broken":
                broken += 1
            elif status == "human-tie-broken":
                human += 1
            elif status == "escalated":
                escalated += 1

            published.append({
                "party_slug": party,
                "question_id": qid,
                "code": code,
                "status": status,
                "confidence": conf,
                "quote": src.get("quote", ""),
                "source_id": src.get("source_id", ""),
                "source_url": src.get("source_url", ""),
                "archive_url": src.get("archive_url", ""),
                "coder_codes": {c: r.get("code") for c, r in sorted(rows.items())},
                "version": "v1",
                "coder": "reconciled",
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })

        totals[party] = {"agreed": agree, "split": split, "single": single,
                         "no-position": nopos, "tie-broken": broken,
                         "human-tie-broken": human, "escalated": escalated}
        report.append(
            f"- {party}: {len(by_q)} questions | agreed {agree} | tie-broken {broken} | "
            f"human tie-broken {human} | escalated {escalated} | split {split} | "
            f"single-coder {single} | no-position {nopos}"
        )

    numeric = [c for c in conflicts if c["kind"] == "numeric"]
    counts = {
        "numeric_conflicts": len(numeric),
        "tie_broken": sum(1 for c in numeric if c["disposition"] == "tie-broken"),
        "human_tie_broken": sum(1 for c in numeric
                                if c["disposition"] == "human-tie-broken"),
        "escalated": sum(1 for c in numeric if c["disposition"] == "escalated"),
        "awaiting_verification": sum(1 for c in numeric
                                     if c["disposition"] == "awaiting-verification"),
        "code_vs_null": sum(1 for c in conflicts if c["kind"] == "code-vs-null"),
    }

    conflicts_doc = {
        "version": "v1",
        "tie_break_rule": TIE_BREAK_RULE,
        "human_tie_break_rule": HUMAN_TIE_BREAK_RULE,
        "human_decisions_source": os.path.relpath(HUMAN, REPO),
        "generated_by": "scripts/reconcile-codings.py",
        "counts": counts,
        "conflicts": conflicts,
    }

    lines = [
        "# Coding reconciliation report",
        "",
        "Rule: agree -> publish code; disagree -> blind third pass decides, publishes",
        "that code; verifier matching neither coder -> publish null and escalate to a",
        "human; an escalated row with a written human decision -> publish that code;",
        "no verifier -> publish null; one coder -> publish with low confidence;",
        "neither -> null.",
        "",
        *report,
        "",
        f"Numeric disagreements: {counts['numeric_conflicts']} "
        f"(tie-broken {counts['tie_broken']}, human tie-broken {counts['human_tie_broken']}, "
        f"escalated {counts['escalated']}, "
        f"awaiting verification {counts['awaiting_verification']}); "
        f"code-vs-null disagreements: {counts['code_vs_null']}.",
        "",
    ]
    if hrules:
        lines += [f"Human tie-breaks applied from "
                  f"{os.path.relpath(HUMAN, REPO)}:", ""]
        for (party, qid), rule in sorted(hrules.items()):
            lines.append(f"- {party}/{qid} -> {rule['decision']} "
                         f"({rule.get('decided_by', 'unattributed')}): "
                         f"{rule.get('reason', '').split('.')[0]}.")
        lines.append("")

    print("\n".join(report))
    print(f"\npublished rows: {len(published)} -> {os.path.relpath(OUT, REPO)}")
    print(f"disagreements: {json.dumps(counts)}")

    if args.dry_run:
        print("\n[dry-run] no files written")
        return

    json.dump(published, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(conflicts_doc, open(CONFLICTS, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
