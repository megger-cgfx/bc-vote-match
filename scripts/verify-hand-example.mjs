/**
 * verify-hand-example.mjs — the scoring maths, checked against a hand-worked example.
 *
 *   node --experimental-strip-types scripts/verify-hand-example.mjs
 *
 * One party (BC NDP), six statements, six fixed user answers. The alignment is
 * computed TWICE:
 *   (a) here, straight from the formula in docs/SCHEMA.md § "Scoring (v1)":
 *       alignment = 1 − (Σ|user − party| / (2·n)) over the compared questions,
 *   (b) by the site's own code path — src/lib/reconcile.ts (coder rows → published
 *       codes) and src/lib/scoring.ts (the numbers the results page renders).
 * The script fails unless (a), (b) and the precomputed expected value all agree.
 * The full arithmetic is printed so it can be transcribed into docs/04-INTEGRATION.md.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.dirname(path.dirname(new URL(import.meta.url).pathname));
const { mergeCodings, UNRESOLVED_SPLIT } = await import(
  path.join(ROOT, "src/lib/reconcile.ts")
);
const { alignmentForParty } = await import(path.join(ROOT, "src/lib/scoring.ts"));

// --- the dataset exactly as src/lib/data.ts loads it ---------------------------------
const questions = JSON.parse(
  fs.readFileSync(path.join(ROOT, "data/questions/questions.json"), "utf8"),
);
const codingsDir = path.join(ROOT, "data/codings");
let coderRows = [];
for (const name of fs.readdirSync(codingsDir).sort()) {
  if (!name.endsWith(".json") || name.startsWith("_") || name.startsWith(".")) continue;
  coderRows.push(...JSON.parse(fs.readFileSync(path.join(codingsDir, name), "utf8")));
}
const codings = mergeCodings(coderRows);

// --- the hand example ----------------------------------------------------------------
const PARTY = "ndp";
const EXAMPLE = {
  q01: -2, // agrees with the NDP's opposition to reinstating the carbon tax
  q04: -1,
  q10: 2,
  q11: 0,
  q19: -2,
  q28: 1,
};
const EXPECTED_PERCENT = 75; // 1 − 3/12 = 0.75

// (a) hand computation, formula transcribed literally from SCHEMA.md.
let sum = 0;
let n = 0;
const lines = [];
const partyCodes = new Map(
  codings.filter((c) => c.party_slug === PARTY).map((c) => [c.question_id, c.code]),
);
for (const [qid, u] of Object.entries(EXAMPLE)) {
  const p = partyCodes.get(qid);
  assert.ok(typeof p === "number", `${PARTY} has no published code on ${qid}`);
  const d = Math.abs(u - p);
  sum += d;
  n += 1;
  lines.push({ qid, u, p, d });
}
const hand = 1 - sum / (2 * n);
const handPercent = Math.round(Math.min(1, Math.max(0, hand)) * 1000) / 10;

// (b) the site's code path.
const site = alignmentForParty(EXAMPLE, codings, questions, PARTY);

console.log(`hand-worked alignment — ${PARTY}, n = ${n}`);
for (const l of lines) {
  console.log(
    `  ${l.qid}  user ${String(l.u).padStart(2)}  party ${String(l.p).padStart(2)}` +
      `  |u−p| = ${l.d}`,
  );
}
console.log(`  Σ|u−p| = ${sum}`);
console.log(`  1 − ${sum}/(2·${n}) = 1 − ${sum / (2 * n)} = ${hand} → ${handPercent}%`);

assert.equal(sum, 3, "hand example should total 3 points of distance");
assert.equal(handPercent, EXPECTED_PERCENT, "hand arithmetic drifted from the recorded example");
assert.equal(site.compared, n, "site compared a different number of questions");
assert.equal(site.rawPercent, EXPECTED_PERCENT, `site rawPercent ${site.rawPercent} != ${EXPECTED_PERCENT}`);
assert.equal(site.percent, EXPECTED_PERCENT, `site percent ${site.percent} != ${EXPECTED_PERCENT}`);
assert.equal(site.meanDistance, sum / n, "mean distance drifted");
assert.equal(site.insufficient, false);

// The reconciliation rules are part of the maths: a split pair must publish nothing.
assert.ok(
  coderRows.filter((c) => c.party_slug === "ndp" && c.question_id === "q38").length === 2,
  "expected two independent coder rows for ndp/q38",
);
assert.equal(partyCodes.get("q38"), null, "split pair ndp/q38 must reconcile to null");
assert.ok(
  codings.some((c) => c.party_slug === "ndp" && c.question_id === "q38" && c.coder === UNRESOLVED_SPLIT),
  "split pair must be marked unresolved-split",
);
// …and a null code must never enter the comparison.
const withNull = alignmentForParty({ ...EXAMPLE, q38: 2 }, codings, questions, PARTY);
assert.equal(withNull.compared, n, "null party code leaked into the comparison");

console.log(`\nsite: percent=${site.percent} rawPercent=${site.rawPercent} compared=${site.compared} meanDistance=${site.meanDistance}`);
console.log("verify-hand-example: OK");
