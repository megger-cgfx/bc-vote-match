/**
 * smoke-test.mjs — executable checks on the parts of the site that do not need a browser.
 *
 *   node --experimental-strip-types scripts/smoke-test.mjs
 *
 * Covers: the v1 scoring rules in src/lib/scoring.ts (including the null / "no published
 * position" path) and the exported static output in ./out.
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

const {
  alignAllParties,
  alignmentForParty,
  dimensionPositions,
  userDimensionPositions,
  sanitiseAnswers,
  answeredCount,
  MIN_PAIRS,
} = await import(path.join(ROOT, "src/lib/scoring.ts"));

const questions = JSON.parse(
  fs.readFileSync(path.join(ROOT, "src/fixtures/questions.sample.json"), "utf8"),
);
const codings = JSON.parse(
  fs.readFileSync(path.join(ROOT, "src/fixtures/codings.sample.json"), "utf8"),
);
const parties = JSON.parse(
  fs.readFileSync(path.join(ROOT, "src/fixtures/parties.sample.json"), "utf8"),
);

/**
 * Mirror of src/lib/data.ts: which question set the last build actually rendered.
 * Keep the two in step, or this suite will check the export against the wrong dataset.
 */
function renderedQuestions() {
  const v2 = path.join(ROOT, "data/questions/questions.v2.json");
  const real = fs.existsSync(v2) ? v2 : path.join(ROOT, "data/questions/questions.json");
  if (process.env.BCVM_FORCE_FIXTURES !== "1" && fs.existsSync(real)) {
    const rows = JSON.parse(fs.readFileSync(real, "utf8"));
    if (Array.isArray(rows) && rows.length > 0) return { rows, source: real };
  }
  return { rows: questions, source: "src/fixtures/questions.sample.json" };
}
const buildQuestions = renderedQuestions();

let checks = 0;
const ok = (label, fn) => {
  fn();
  checks += 1;
  console.log(`  ok  ${label}`);
};

console.log("scoring.ts");

ok("fixtures follow the schema's code domain", () => {
  for (const c of codings) {
    assert.ok(
      c.code === null || [-2, -1, 0, 1, 2].includes(c.code),
      `${c.party_slug}/${c.question_id} has code ${c.code}`,
    );
  }
  assert.equal(new Set(codings.map((c) => c.party_slug)).size, parties.length);
});

ok("answering exactly like a party scores 100% for that party", () => {
  const slug = "ndp";
  const party = codings.filter((c) => c.party_slug === slug);
  const answers = Object.fromEntries(party.map((c) => [c.question_id, c.code]));
  assert.equal(answeredCount(answers), party.filter((c) => c.code !== null).length);
  const r = alignmentForParty(answers, party, questions, slug);
  assert.equal(r.percent, 100);
  assert.equal(r.meanDistance, 0);
  assert.equal(r.insufficient, false);
});

ok("opposite answers score 0% (clamped) where a position exists, raw score exposed", () => {
  const slug = "cpb";
  const mined = codings.filter((c) => c.party_slug === slug && c.code === 2);
  assert.ok(mined.length >= MIN_PAIRS, "need at least MIN_PAIRS +2 cpb codes in the fixture");
  const answers = Object.fromEntries(mined.map((c) => [c.question_id, -2]));
  const r = alignmentForParty(answers, codings.filter((c) => c.party_slug === slug), questions, slug);
  assert.equal(r.compared, mined.length);
  assert.equal(r.meanDistance, 4);
  // The schema formula is 1 − Σ|u−p|/(2n); with ±2 answers it goes negative. We display the
  // clamp and keep the raw value — see the open spec issue flagged in scoring.ts.
  assert.equal(r.percent, 0);
  assert.equal(r.rawPercent, -100);
});

ok("displayed alignment is always inside 0–100 regardless of the raw formula", () => {
  for (const slug of parties.map((p) => p.slug)) {
    for (const sign of [-2, -1, 0, 1, 2]) {
      const party = codings.filter((c) => c.party_slug === slug);
      const answers = Object.fromEntries(party.map((c) => [c.question_id, sign]));
      const r = alignmentForParty(answers, party, questions, slug);
      assert.ok(r.percent === null || (r.percent >= 0 && r.percent <= 100), `${slug}: ${r.percent}`);
    }
  }
});

ok("null party codes are excluded, never treated as neutral", () => {
  const answers = Object.fromEntries(questions.map((q) => [q.id, 0]));
  const slug = "ndp";
  const party = codings.filter((c) => c.party_slug === slug);
  const r = alignmentForParty(answers, party, questions, slug);
  const comparable = party.filter((c) => c.code !== null).length;
  assert.equal(r.compared, comparable);
  assert.ok(comparable < party.length, "fixture should contain at least one null code");
});

ok("too few comparable answers yields null, not a fake percentage", () => {
  const answers = { [questions[0].id]: 1 };
  const r = alignmentForParty(answers, codings.filter((c) => c.party_slug === "ndp"), questions, "ndp");
  assert.equal(r.compared, 1);
  assert.equal(r.insufficient, true);
  assert.equal(r.percent, null);
  assert.ok(MIN_PAIRS > 1);
});

ok("'don't know' (null) answers are ignored end to end", () => {
  const answers = Object.fromEntries(questions.map((q) => [q.id, null]));
  assert.equal(answeredCount(answers), 0);
  for (const r of alignAllParties(answers, codings, questions, parties.map((p) => p.slug))) {
    assert.equal(r.percent, null);
    assert.equal(r.compared, 0);
  }
});

ok("parties are scored against their own codings, never a neighbour's", () => {
  const answers = Object.fromEntries(questions.map((q) => [q.id, 2]));
  const all = alignAllParties(answers, codings, questions, parties.map((p) => p.slug));
  assert.equal(all.length, parties.length);
  const bySlug = new Map(all.map((a) => [a.partySlug, a]));
  const seen = new Set();
  for (const p of parties) {
    const mine = codings.filter((c) => c.party_slug === p.slug);
    const solo = alignmentForParty(answers, mine, questions, p.slug);
    const viaAll = bySlug.get(p.slug);
    assert.equal(viaAll.percent, solo.percent, `${p.slug}: bulk != solo`);
    assert.equal(viaAll.compared, solo.compared, `${p.slug}: compared differs`);
    seen.add(`${solo.percent}/${solo.compared}/${solo.meanDistance}`);
  }
  // If every party produced an identical triple, the party filter is being ignored.
  assert.ok(seen.size > 1, `all parties scored identically: ${[...seen]}`);
});

ok("alignment percentages are ordered best-first and within 0–100", () => {
  const answers = Object.fromEntries(
    questions.map((q, i) => [q.id, i % 2 === 0 ? 2 : -1]),
  );
  const rows = alignAllParties(answers, codings, questions, parties.map((p) => p.slug));
  assert.equal(rows.length, parties.length);
  for (const r of rows) {
    assert.ok(r.percent === null || (r.percent >= 0 && r.percent <= 100), `${r.percent}`);
  }
  const shown = rows.filter((r) => r.percent !== null).map((r) => r.percent);
  assert.deepEqual(shown, [...shown].sort((a, b) => b - a));
});

ok("dimension positions stay inside the −2…+2 scale", () => {
  const answers = Object.fromEntries(questions.map((q, i) => [q.id, i % 2 ? 2 : -2]));
  const u = userDimensionPositions(answers, questions);
  const p = dimensionPositions(answers, codings, questions, "green");
  for (const v of [u.economic, u.social, p.economic, p.social]) {
    if (v === null) continue;
    assert.ok(v >= -2 && v <= 2, `${v} out of range`);
  }
  assert.ok(Math.abs(u.economic) <= 2 && Math.abs(u.social) <= 2);
  // Cross-check against an independent mean over each dimension's questions.
  for (const dim of ["economic", "social"]) {
    const ids = questions.filter((q) => q.dimensions.includes(dim)).map((q) => q.id);
    const expected =
      ids.reduce((acc, id) => acc + answers[id], 0) / ids.length;
    assert.ok(Math.abs(u[dim] - expected) < 1e-9, `${dim}: ${u[dim]} != ${expected}`);
    assert.ok(ids.length > 0, `no questions load on ${dim}`);
  }
});

ok("malformed localStorage answers are dropped, not trusted", () => {
  const a = sanitiseAnswers(
    { q01: 2, bogus: 2, q02: 9, q03: "x", q04: null, q05: -1.5 },
    questions,
  );
  assert.deepEqual(a, { q01: 2, q04: null });
});

console.log("\nexported site (out/)");

const OUT = path.join(ROOT, "out");
const pages = [
  "index.html",
  "questions/index.html",
  "results/index.html",
  "parties/index.html",
  "methodology/index.html",
  "coding-table/index.html",
  "about/index.html",
  "404.html",
];

ok("every route exported to a real HTML file", () => {
  for (const p of pages) {
    const f = path.join(OUT, p);
    assert.ok(fs.existsSync(f), `missing ${p}`);
    assert.ok(fs.statSync(f).size > 2000, `${p} looks empty`);
  }
  assert.ok(fs.existsSync(path.join(OUT, "og.png")), "missing og.png");
  assert.ok(fs.existsSync(path.join(OUT, "robots.txt")), "missing robots.txt");
  assert.ok(fs.existsSync(path.join(OUT, "sitemap.xml")), "missing sitemap.xml");
});

ok("share-card metadata is present on every page", () => {
  for (const p of pages) {
    const html = fs.readFileSync(path.join(OUT, p), "utf8");
    assert.match(html, /property="og:title"/, `${p}: no og:title`);
    assert.match(html, /property="og:image"/, `${p}: no og:image`);
    assert.match(html, /og\.png/, `${p}: og:image is not the static card`);
    assert.match(html, /name="twitter:card"/, `${p}: no twitter:card`);
  }
});

ok("the disclaimer and independence line ship on the site", () => {
  const html = fs.readFileSync(path.join(OUT, "index.html"), "utf8");
  assert.match(html, /does not tell you how to vote/i, "home page is missing the disclaimer");
  assert.match(html, /not affiliated with/i, "home page is missing the independence line");
  const about = fs.readFileSync(path.join(OUT, "about/index.html"), "utf8");
  assert.match(about, /Vote Compass/, "about page should name Vote Compass in the independence line");
});

ok("the question set is wired into the questionnaire page", () => {
  const raw = fs.readFileSync(path.join(OUT, "questions/index.html"), "utf8");
  const text = raw
    .replace(/<[^>]*>/g, " ")
    .replace(/&#x27;|&#39;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
  for (const q of buildQuestions.rows) {
    assert.ok(raw.includes(`id="${q.id}"`), `${q.id} is not rendered as an answer group`);
    assert.ok(text.includes(q.statement), `${q.id} statement text missing from the page`);
  }
  assert.match(raw, /role="radiogroup"/, "no accessible answer control");
  assert.match(text, /Don’t know|Don't know/, "no 'don't know' option");
  console.log(`      (checked ${buildQuestions.rows.length} statements from ${buildQuestions.source})`);
});

ok("no third-party trackers or remote scripts are referenced", () => {
  for (const p of pages) {
    const html = fs.readFileSync(path.join(OUT, p), "utf8");
    for (const bad of ["google-analytics", "googletagmanager", "facebook.net", "hotjar", "doubleclick"]) {
      assert.ok(!html.includes(bad), `${p} references ${bad}`);
    }
    const externals = [...html.matchAll(/<script[^>]+src="(https?:)?\/\//g)];
    assert.equal(externals.length, 0, `${p} loads a remote script`);
  }
});

ok("robots.txt and sitemap.xml reflect the site URL", () => {
  const robots = fs.readFileSync(path.join(OUT, "robots.txt"), "utf8");
  assert.match(robots, /Sitemap: https:\/\/bcvotematch\.ca\/sitemap\.xml/);
  const sitemap = fs.readFileSync(path.join(OUT, "sitemap.xml"), "utf8");
  for (const seg of ["/questions/", "/methodology/", "/coding-table/", "/parties/", "/about/"]) {
    assert.ok(sitemap.includes(seg), `sitemap missing ${seg}`);
  }
  // /results/ is per-user and noindex — it must stay out of the sitemap and the crawl.
  assert.ok(!sitemap.includes("/results/"), "sitemap should not list /results/");
  assert.match(robots, /Disallow: \/results\//, "robots.txt should disallow /results/");
  // /quiz/ is a legacy alias; /questions/ is the one canonical questionnaire route.
  assert.ok(!sitemap.includes("/quiz/"), "sitemap should not list /quiz/");
});

ok("the export carries no fixture/sample-data banner", () => {
  for (const p of pages) {
    const html = fs.readFileSync(path.join(OUT, p), "utf8");
    for (const bad of ["Sample data", "PLACEHOLDER DATA", "illustrative filler"]) {
      assert.ok(!html.includes(bad), `${p} still warns about sample data: "${bad}"`);
    }
  }
});

ok("/quiz/ is a redirect stub to the canonical /questions/ route", () => {
  const html = fs.readFileSync(path.join(OUT, "quiz/index.html"), "utf8");
  assert.match(html, /http-equiv="refresh"/, "no meta-refresh fallback");
  assert.match(html, /url=\/questions\//, "does not point at /questions/");
  assert.match(html, /name="robots"[^>]*noindex/, "redirect stub should be noindex");
});

// ---------------------------------------------------------------------------
// postal.ts — postal code → riding lookup (M6b): normalisation, honest not-found,
// FSA fallback that never guesses, against both a synthetic index and the real
// data/candidates/postal-to-riding.json the site ships.
const { normalisePostal, lookupPostal, isPostalIndex } = await import(
  path.join(ROOT, "src/lib/postal.ts")
);

console.log("postal.ts");

const fakeIndex = {
  ridings: {
    "riding-a": { name: "Riding A" },
    "riding-b": { name: "Riding B" },
  },
  fsa: {
    V0A: { ridings: ["riding-a"], primary: "riding-a", counts: { "riding-a": 2 } },
    V0B: {
      ridings: ["riding-a", "riding-b"],
      primary: "riding-a",
      counts: { "riding-a": 2, "riding-b": 1 },
    },
  },
  postal: {
    V0A0A0: "riding-a",
    V0A0A1: ["riding-a", "riding-b"],
  },
};

ok("postal input is normalised: spaces, case, stray punctuation", () => {
  assert.equal(normalisePostal("v8r 3l2"), "V8R3L2");
  assert.equal(normalisePostal(" V8R-3l2 "), "V8R3L2");
  assert.equal(normalisePostal("v0a0a0"), "V0A0A0");
});

ok("exact postal codes resolve to one riding (with or without space)", () => {
  assert.equal(lookupPostal(fakeIndex, "V0A 0A0").kind, "exact");
  assert.equal(lookupPostal(fakeIndex, "v0a0a0").riding, "riding-a");
});

ok("a boundary-straddling code returns the list, never a picked riding", () => {
  const r = lookupPostal(fakeIndex, "V0A 0A1");
  assert.equal(r.kind, "straddling");
  assert.deepEqual(r.ridings, ["riding-a", "riding-b"]);
});

ok("a full code that is not in the dataset falls back to its FSA as a choice, not an answer", () => {
  const r = lookupPostal(fakeIndex, "V0B 9Z9");
  assert.equal(r.kind, "fsa-hint");
  assert.equal(r.fsa, "V0B");
  assert.deepEqual(r.ridings.ridings, ["riding-a", "riding-b"]);
  assert.ok(!("riding" in r), "fsa-hint must not carry a resolved riding");
});

ok("3-character FSA input is flagged as partial, not resolved", () => {
  assert.equal(lookupPostal(fakeIndex, "v0b").kind, "fsa");
  const r = lookupPostal(fakeIndex, "V0A");
  assert.equal(r.kind, "fsa");
});

ok("malformed and unknown input is reported, never guessed", () => {
  assert.equal(lookupPostal(fakeIndex, "hello").kind, "invalid");
  assert.equal(lookupPostal(fakeIndex, "12345").kind, "invalid");
  assert.equal(lookupPostal(fakeIndex, "K1A 0A1").kind, "not-found");
  assert.equal(lookupPostal(fakeIndex, "V9V").kind, "not-found");
});

ok("the real postal dataset loads and answers the documented spot checks", () => {
  const real = JSON.parse(
    fs.readFileSync(path.join(ROOT, "data/candidates/postal-to-riding.json"), "utf8"),
  );
  assert.ok(isPostalIndex(real), "postal-to-riding.json should pass the shape guard");
  // Spot checks recorded in docs/M6b-POSTAL-LOOKUP.md against Elections BC addresses.
  assert.equal(lookupPostal(real, "V2V 0G4").riding, "abbotsford-mission");
  assert.equal(lookupPostal(real, "V0H1E1").riding, "boundary-similkameen");
  // The one documented straddling code stays a list.
  const s = lookupPostal(real, "V0K2S1");
  assert.equal(s.kind, "straddling");
  assert.deepEqual([...s.ridings].sort(), ["cariboo-chilcotin", "fraser-nicola"]);
  // V8R's forward sorting area includes Victoria-Beacon Hill (documented check).
  const fsa = lookupPostal(real, "V8R");
  assert.equal(fsa.kind, "fsa");
  assert.ok(fsa.ridings.ridings.includes("victoria-beacon-hill"));
  // A well-formed code absent from the dataset, whose FSA is known → fsa-hint.
  const absent = ["V8R0Z9", "V8R1Z9", "V8R2Z9"].find((c) => !(c in real.postal));
  assert.ok(absent, "expected at least one unused V8R code for the fsa-hint case");
  assert.equal(lookupPostal(real, absent).kind, "fsa-hint");
  // An FSA outside BC's dataset → plain not-found.
  assert.equal(lookupPostal(real, "K1A 0A1").kind, "not-found");
});

console.log(`\n${checks} checks passed`);
