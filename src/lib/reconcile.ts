/**
 * reconcile.ts — merge the two independent coder rows into one published code.
 *
 * The M3 coding pass writes TWO rows per (party, question): coder-a and coder-b
 * (docs/04-CODINGS.md). docs/SCHEMA.md's contract has exactly ONE code per pair, and
 * scoring needs one number per pair. This module performs that reconciliation with a
 * conservative, deterministic rule — it never invents a number neither coder wrote:
 *
 *   1. Rows with `code: null` carry no position (the party published nothing we could
 *      code). If every row is null, the merged code is null.
 *   2. If the non-null codes all agree, that code is published — the row kept for
 *      provenance is the highest-confidence one among those carrying the code
 *      (ties: first in file order).
 *   3. If a single coder wrote a code and the other wrote null, the sourced code wins.
 *      A null is absence of evidence, not a contradicting position, and every non-null
 *      code carries an audited verbatim quote.
 *   4. If the two non-null codes DISAGREE, the pair is unsettled: the merged code is
 *      `null` (site shows "no published position") and the row is marked
 *      `coder: "unresolved-split"` until the human tie-break in docs/02-PLAN.md (L3/L4)
 *      adjudicates it. Publishing one coder's guess as the party's position is exactly
 *      what the "never guess" rule forbids.
 *
 * Pure module: type-only imports, no fs, no runtime deps — so `node
 * --experimental-strip-types` can import it directly for verification runs.
 */

import type { Coding, Confidence } from "./schema";

const CONFIDENCE_RANK: Record<Confidence, number> = { high: 3, medium: 2, low: 1 };

/** Coder label used on merged rows where the two coders split and a tie-break is pending. */
export const UNRESOLVED_SPLIT = "unresolved-split";

/**
 * Merge raw coder rows to one row per (party, question), per the rules in the module
 * header. Input order is preserved for the first appearance of each pair.
 */
export function mergeCodings(rows: Coding[]): Coding[] {
  const byPair = new Map<string, Coding[]>();
  for (const row of rows) {
    const key = `${row.party_slug}|${row.question_id}`;
    const list = byPair.get(key) ?? [];
    list.push(row);
    byPair.set(key, list);
  }

  const out: Coding[] = [];
  for (const group of byPair.values()) {
    out.push(mergeGroup(group));
  }
  return out;
}

function mergeGroup(group: Coding[]): Coding {
  const first = group[0];
  const coded = group.filter((r) => typeof r.code === "number");

  // Rule 1: nobody coded a position.
  if (coded.length === 0) return first;

  const codes = new Set(coded.map((r) => r.code));

  // Rules 2 + 3: the non-null codes agree (or only one coder found evidence) —
  // publish the best-evidenced row.
  if (codes.size === 1) {
    return coded.reduce((best, r) =>
      CONFIDENCE_RANK[r.confidence] > CONFIDENCE_RANK[best.confidence] ? r : best,
    );
  }

  // Rule 4: the coders split. No published position until the human tie-break.
  return {
    ...first,
    code: null,
    quote: null,
    source_id: null,
    source_url: null,
    archive_url: null,
    coder: UNRESOLVED_SPLIT,
    confidence: "low" as Confidence,
  };
}
