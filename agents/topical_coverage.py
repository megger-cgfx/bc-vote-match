#!/usr/bin/env python3
"""topical_coverage.py — for each of the six question topics, count keyword
hits per source so the coding wave can see which sources actually carry
evidence for each topic.

Usage: python3 agents/topical_coverage.py --party ndp
Writes data/raw/<party>/COVERAGE.md and prints it.
"""
import argparse, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOPICS = {
    "cost-of-living-taxes": r"tax|affordab|cost of living|groceries|benefit|rebate|inflation|wage|speculat|vacanc|rent",
    "housing": r"hous|home|rent|condo|speculat|vacanc|homeless|zoning|rental",
    "health": r"health|doctor|nurse|hospital|surg|emergency|mental health|addiction|pharmacare|dental",
    "climate-environment": r"climate|emission|carbon|clean energy|renewab|LNG|forest|old growth|environment|conservation|protected area",
    "indigenous-reconciliation": r"Indigenous|First Nation|reconciliation|DRIPA|Declaration|UNDRIP|title|Métis|Inuit|residential school|Truth and Reconciliation",
    "public-safety": r"public safety|police|crime|bail|offender|gang|extortion|drug|toxic|victim|justice",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--party", required=True)
    a = ap.parse_args()
    outdir = os.path.join(ROOT, "data", "raw", a.party)
    recs = json.load(open(os.path.join(outdir, "sources.json")))
    rows = []
    for r in recs:
        tp = r.get("text_path") or ""
        body = ""
        if tp and os.path.exists(os.path.join(ROOT, tp)):
            body = open(os.path.join(ROOT, tp), encoding="utf-8", errors="replace").read()
        counts = {t: len(re.findall(rx, body, re.I)) for t, rx in TOPICS.items()}
        total = sum(counts.values())
        rows.append((r, counts, total, len(body)))

    lines = [f"# {a.party.upper()} source coverage by topic", "",
             "Keyword hits in the archived local text (case-insensitive, rough). >0 means the",
             "source is at least worth a look for that topic; it is NOT a code.", "",
             "| id | type | published | " + " | ".join(t[:6] for t in TOPICS) + " | chars | title |",
             "|---|---|---|" + "---|" * len(TOPICS) + "---|---|"]
    for r, counts, total, nchars in rows:
        lines.append(f"| {r['id']} | {r['type']} | {r.get('published') or '?'} | "
                     + " | ".join(str(counts[t]) for t in TOPICS)
                     + f" | {nchars} | {(r.get('title') or '')[:60]} |")

    lines += ["", "## Best sources per topic (top 4 by hits)", ""]
    for t in TOPICS:
        ranked = sorted(rows, key=lambda x: -x[1][t])[:4]
        lines.append(f"- **{t}**: " + ", ".join(f"{r['id']} ({c[t]})" for r, c, _, _ in ranked if c[t] > 0))

    out = "\n".join(lines) + "\n"
    open(os.path.join(outdir, "COVERAGE.md"), "w", encoding="utf-8").write(out)
    print(out)


if __name__ == "__main__":
    main()
