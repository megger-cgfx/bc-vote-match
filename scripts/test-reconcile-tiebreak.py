#!/usr/bin/env python3
"""test-reconcile-tiebreak.py -- unit tests for the tie-break rule in
scripts/reconcile-codings.py (docs/CODEBOOK.md s7 resolution ladder).

Run:  python3 scripts/test-reconcile-tiebreak.py
Exits non-zero if any case fails.
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = importlib.util.spec_from_file_location(
    "reconcile_codings", os.path.join(REPO, "scripts", "reconcile-codings.py"))
RC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RC)

FAILURES = []


def check(name, got, want):
    if got != want:
        FAILURES.append(f"{name}: got {got!r}, want {want!r}")
        print(f"FAIL {name}: got {got!r}, want {want!r}")
    else:
        print(f"ok   {name}")


def row(party, qid, code, coder, confidence="medium", quote="q", sid="s1"):
    return {
        "party_slug": party, "question_id": qid, "code": code, "quote": quote,
        "source_id": sid, "source_url": "https://example.invalid/a",
        "archive_url": "https://web.archive.invalid/a", "coder": coder,
        "version": "v1", "created_at": "2026-10-01T12:00:00Z", "confidence": confidence,
    }


def case(name, coder_rows, verifier=None, notes=None, pass1=None, human=None):
    """Run resolve() on {coder_key: row} and return (fields, conflict)."""
    return RC.resolve(coder_rows, verifier, notes or {}, pass1, human)


def unit_tests():
    print("-- resolution ladder")
    a = row("ndp", "q01", 1, "ndp-coder-a")
    b = row("ndp", "q01", 1, "ndp-coder-b")
    (code, status, conf, _), conflict = case("agree", {"A": a, "B": b})
    check("agree status", status, "agreed")
    check("agree code", code, 1)
    check("agree no conflict", conflict, None)

    a = row("ndp", "q01", -1, "ndp-coder-a")
    b = row("ndp", "q01", -2, "ndp-coder-b")
    (code, status, conf, _), conflict = case("split/no verifier", {"A": a, "B": b})
    check("split status", status, "split")
    check("split publishes null", code, None)
    check("split conflict kind", conflict["kind"], "numeric")
    check("split disposition", conflict["disposition"], "awaiting-verification")
    check("split keeps both codes", [conflict["coder_a"]["code"],
                                     conflict["coder_b"]["code"]], [-1, -2])

    v = row("ndp", "q01", -1, "ndp-verifier", confidence="low")
    (code, status, conf, src), conflict = case("verifier matches A", {"A": a, "B": b}, v)
    check("tie-break A: status", status, "tie-broken")
    check("tie-break A: code", code, -1)
    check("tie-break A: matched", conflict["matched_coder"], "A")
    check("tie-break A: verifier recorded", conflict["verifier"]["code"], -1)
    check("tie-break A: quote is adopted coder's", src["coder"], "ndp-coder-a")
    check("tie-break A: confidence is the weaker of the two", conf, "low")

    v = row("ndp", "q01", -2, "ndp-verifier", confidence="high")
    (code, status, conf, src), conflict = case("verifier matches B", {"A": a, "B": b}, v)
    check("tie-break B: code", code, -2)
    check("tie-break B: matched", conflict["matched_coder"], "B")
    check("tie-break B: quote is adopted coder's", src["coder"], "ndp-coder-b")
    check("tie-break B: confidence", conf, "medium")
    check("tie-break B: both passes recorded",
          [p["code"] for p in conflict["verifier_passes"] if p], [-2])

    # A second blind pass that reads the same evidence and lands elsewhere is the
    # "verifier cannot resolve it" case: escalate rather than let the later pass win.
    v = row("ndp", "q01", -2, "ndp-verifier", confidence="high")
    p1 = row("ndp", "q01", -1, "ndp-verifier-pass1-window")
    (code, status, conf, _), conflict = case("two passes disagree",
                                             {"A": a, "B": b}, v, None, p1)
    check("ambiguity status", status, "escalated")
    check("ambiguity publishes null", code, None)
    check("ambiguity reason", conflict["escalation_reason"],
          "verifier-ambiguity-two-passes-disagree")
    check("ambiguity keeps both pass codes",
          [p["code"] for p in conflict["verifier_passes"]], [-1, -2])

    # A pass-1 null is a window limitation, not a competing reading: it does not
    # block the protocol pass.
    v = row("ndp", "q01", -2, "ndp-verifier", confidence="high")
    p1 = row("ndp", "q01", None, "ndp-verifier-pass1-window",
             confidence=None, quote=None, sid=None)
    (code, status, _, _), conflict = case("pass1 null does not block",
                                          {"A": a, "B": b}, v, None, p1)
    check("pass1-null status", status, "tie-broken")
    check("pass1-null code", code, -2)

    # Two passes that agree keep the tie-break.
    v = row("ndp", "q01", -2, "ndp-verifier", confidence="high")
    p1 = row("ndp", "q01", -2, "ndp-verifier-pass1-window")
    (code, status, _, _), conflict = case("two passes agree", {"A": a, "B": b}, v, None, p1)
    check("agreement keeps status", status, "tie-broken")
    check("agreement keeps code", code, -2)

    v = row("ndp", "q01", 2, "ndp-verifier")
    (code, status, conf, _), conflict = case("verifier matches neither",
                                             {"A": a, "B": b}, v)
    check("escalated status", status, "escalated")
    check("escalated publishes null", code, None)
    check("escalated disposition", conflict["disposition"], "escalated")
    check("escalated reason", conflict["escalation_reason"],
          "verifier-agrees-with-neither-coder")
    check("escalated still records verifier", conflict["verifier"]["code"], 2)

    v = row("ndp", "q01", None, "ndp-verifier", confidence=None, quote=None, sid=None)
    (code, status, _, _), conflict = case("verifier says null", {"A": a, "B": b}, v)
    check("verifier-null escalates", status, "escalated")

    v = row("ndp", "q01", -2, "ndp-verifier")
    notes = {"q01": "Hansard tie-breaker"}
    (_, _, _, _), conflict = case("verifier rationale", {"A": a, "B": b}, v, notes)
    check("verifier rationale recorded", conflict["verifier"]["rationale"],
          "Hansard tie-breaker")

    a = row("green", "q22", 1, "green-coder-a")
    b = row("green", "q22", None, "green-coder-b", confidence=None, quote=None, sid=None)
    (code, status, conf, _), conflict = case("one coded, one null", {"A": a, "B": b})
    check("code-vs-null status", status, "single-coder")
    check("code-vs-null publishes the code", code, 1)
    check("code-vs-null low confidence", conf, "low")
    check("code-vs-null conflict recorded", conflict["kind"], "code-vs-null")

    a = row("green", "q22", None, "green-coder-a", confidence=None, quote=None, sid=None)
    b = row("green", "q22", None, "green-coder-b", confidence=None, quote=None, sid=None)
    (code, status, _, _), conflict = case("neither coded", {"A": a, "B": b})
    check("no-position status", status, "no-position")
    check("no-position null", code, None)
    check("no-position no conflict", conflict, None)


def human_tests():
    print("-- human tie-break (CODEBOOK s7.2)")
    a = row("ndp", "q01", -1, "ndp-coder-a")
    b = row("ndp", "q01", -2, "ndp-coder-b", confidence="low")
    v = row("ndp", "q01", 1, "ndp-verifier", confidence="medium")

    human = {"decision": -2, "reason": "own record in government",
             "decided_by": "editor", "decided_at": "2026-10-01T20:28:15Z"}
    (code, status, conf, src), conflict = case("human adopts coder B",
                                               {"A": a, "B": b}, v, human=human)
    check("human status", status, "human-tie-broken")
    check("human code", code, -2)
    check("human confidence from adopted row", conf, "low")
    check("human quote is coder B's", src["coder"], "ndp-coder-b")
    check("human disposition", conflict["disposition"], "human-tie-broken")
    check("human field", conflict["human_decision"], -2)
    check("human reason", conflict["human_reason"], "own record in government")
    check("human attribution", conflict["decided_by"], "editor")
    check("human matched coder", conflict["matched_coder"], "B")
    check("human rule documented", conflict["tie_break_rule"], RC.HUMAN_TIE_BREAK_RULE)

    human_v = {"decision": 1, "reason": "verifier reading", "decided_by": "editor"}
    (code, status, _, src), conflict = case("human adopts the verifier code",
                                            {"A": a, "B": b}, v, human=human_v)
    check("human-verifier code", code, 1)
    check("human-verifier matched", conflict["matched_coder"], "verifier")
    check("human-verifier quote", src["coder"], "ndp-verifier")

    human_bad = {"decision": 0, "reason": "gut", "decided_by": "editor"}
    (code, status, _, _), conflict = case("human adopts an unread code",
                                          {"A": a, "B": b}, v, human=human_bad)
    check("unread code stays escalated", status, "escalated")
    check("unread code publishes null", code, None)
    check("unread code recorded", "human_decision_ignored" in conflict, True)
    check("unread code disposition", conflict["disposition"], "escalated")

    # a written decision only applies where the coders actually disagree.
    a2 = row("ndp", "q01", 1, "ndp-coder-a")
    b2 = row("ndp", "q01", 1, "ndp-coder-b")
    (code, status, _, _), conflict = case("human ignored on agreement",
                                          {"A": a2, "B": b2}, human=human_bad)
    check("agreement untouched", status, "agreed")
    check("agreement no conflict", conflict, None)

    # a split with no verifier can be broken by adopting either coder's code.
    (code, status, _, src), conflict = case("human breaks a split",
                                            {"A": a, "B": b}, human=human)
    check("split broken by human", status, "human-tie-broken")
    check("split broken to coder B", src["coder"], "ndp-coder-b")


def end_to_end():
    print("-- end to end (temp workspace)")
    tmp = tempfile.mkdtemp(prefix="tiebreak-test-")
    try:
        os.makedirs(os.path.join(tmp, "data/codings/v1"))
        saved = {k: getattr(RC, k) for k in
                 ("REPO", "V1", "OUT", "CONFLICTS", "REPORT", "HUMAN")}
        RC.REPO = tmp
        RC.V1 = os.path.join(tmp, "data/codings/v1")
        RC.OUT = os.path.join(tmp, "data/codings/codings.json")
        RC.CONFLICTS = os.path.join(tmp, "data/codings/_conflicts.json")
        RC.REPORT = os.path.join(tmp, "data/codings/RECONCILE-REPORT.md")
        RC.HUMAN = os.path.join(tmp, "data/codings/_human-decisions.json")  # type: ignore[attr-defined]

        a = row("cpb", "q19", 1, "cpb-coder-a")
        b = row("cpb", "q19", 2, "cpb-coder-b")
        v = row("cpb", "q19", 2, "cpb-verifier", confidence="high")
        json.dump([a], open(os.path.join(RC.V1, "cpb-coderA.json"), "w"))
        json.dump([b], open(os.path.join(RC.V1, "cpb-coderB.json"), "w"))
        json.dump([v], open(os.path.join(RC.V1, "cpb-verifier.json"), "w"))
        json.dump([{"party_slug": "cpb", "question_id": "q19",
                    "coder": "cpb-verifier", "rationale": "platform wording"}],
                  open(os.path.join(RC.V1, "cpb-verifier-notes.json"), "w"))

        sys.argv = ["reconcile-codings.py"]
        RC.main()

        published = json.load(open(RC.OUT))
        check("e2e rows", len(published), 1)
        check("e2e status", published[0]["status"], "tie-broken")
        check("e2e code", published[0]["code"], 2)
        # coder B is medium, the verifier high -> the weaker (medium) is published
        check("e2e confidence", published[0]["confidence"], "medium")
        conflicts = json.load(open(RC.CONFLICTS))
        check("e2e conflicts count", conflicts["counts"]["tie_broken"], 1)
        check("e2e conflict disposition",
              conflicts["conflicts"][0]["disposition"], "tie-broken")
        check("e2e rule is documented",
              conflicts["tie_break_rule"], RC.TIE_BREAK_RULE)
        report = open(RC.REPORT).read()
        check("e2e report mentions tie-broken", "tie-broken 1" in report, True)

        # second run: an escalated row plus a written human decision.
        a2 = row("cpb", "q22", 1, "cpb-coder-a")
        b2 = row("cpb", "q22", 2, "cpb-coder-b", confidence="low")
        v2 = row("cpb", "q22", -2, "cpb-verifier", confidence="high")
        json.dump([a, a2], open(os.path.join(RC.V1, "cpb-coderA.json"), "w"))
        json.dump([b, b2], open(os.path.join(RC.V1, "cpb-coderB.json"), "w"))
        json.dump([v, v2], open(os.path.join(RC.V1, "cpb-verifier.json"), "w"))
        json.dump([{"party_slug": "cpb", "question_id": "q19", "coder": "cpb-verifier",
                    "rationale": "platform wording"},
                   {"party_slug": "cpb", "question_id": "q22", "coder": "cpb-verifier",
                    "rationale": "platform wording"}],
                  open(os.path.join(RC.V1, "cpb-verifier-notes.json"), "w"))
        json.dump({"version": "v1", "decided_by": "editor",
                   "decided_at": "2026-10-01T20:28:15Z", "decisions": [
            {"party_slug": "cpb", "question_id": "q22", "decision": 2,
             "reason": "the party's own plan names the instrument"}]},
            open(RC.HUMAN, "w"))
        RC.main()

        published = {r["question_id"]: r for r in json.load(open(RC.OUT))}
        check("e2e human status", published["q22"]["status"], "human-tie-broken")
        check("e2e human code", published["q22"]["code"], 2)
        check("e2e human confidence", published["q22"]["confidence"], "low")
        check("e2e human quote adopted from coder B",
              published["q22"]["source_id"], b2["source_id"])
        conflicts = json.load(open(RC.CONFLICTS))
        check("e2e human count", conflicts["counts"]["human_tie_broken"], 1)
        check("e2e escalated count now zero", conflicts["counts"]["escalated"], 0)
        check("e2e human rule source recorded",
              conflicts["human_decisions_source"], "data/codings/_human-decisions.json")
        q22c = [c for c in conflicts["conflicts"] if c["question_id"] == "q22"][0]
        check("e2e human conflict field", q22c["human_decision"], 2)
        check("e2e human conflict reason",
              q22c["human_reason"], "the party's own plan names the instrument")
        check("e2e human attribution from the file header",
              q22c["decided_by"], "editor")
        check("e2e human conflict rule",
              q22c["tie_break_rule"], RC.HUMAN_TIE_BREAK_RULE)
        report = open(RC.REPORT).read()
        check("e2e report logs human decision",
              "Human tie-breaks applied" in report, True)

        for k, val in saved.items():
            setattr(RC, k, val)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unit_tests()
    human_tests()
    end_to_end()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s)")
        sys.exit(1)
    print("PASS: all tie-break cases")
