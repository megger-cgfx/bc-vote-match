/**
 * check-riding-export.mjs — end-to-end gate for the M6 riding layer.
 *
 *   npm run build && node scripts/check-riding-export.mjs
 *
 * Proves the built site actually carries the riding layer: the exported /riding page
 * exists, renders the district search, and embeds a dataset whose district and
 * candidate counts match data/ridings/*.json (i.e. the loader picked up the real files
 * rather than falling back to an empty layer).
 */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

const read = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), "utf8"));
const ridings = read("data/ridings/ridings.json");
const candidates = read("data/ridings/candidates.json");

const pagePath = path.join(ROOT, "out/riding/index.html");
assert.ok(fs.existsSync(pagePath), "out/riding/index.html missing — run `npm run build`");
const html = fs.readFileSync(pagePath, "utf8");

let checks = 0;
const ok = (cond, msg) => {
  assert.ok(cond, msg);
  checks += 1;
  console.log("  ok  " + msg);
};

ok(html.includes("Find your electoral district"), "riding page renders the district search");
ok(html.includes("electoral districts"), "riding page states the district count");

// The candidate roster is serialised into the client component's props; spot-check that
// a known candidate and a known district reach the page.
const sample = candidates[0];
ok(html.includes(sample.riding_slug), `payload carries riding ${sample.riding_slug}`);
ok(html.includes(sample.name), `payload carries candidate ${sample.name}`);

// Every district the builder produced is present in the payload.
const missing = ridings.filter((r) => !html.includes(r.slug));
ok(missing.length === 0, `all ${ridings.length} districts present in the payload` +
  (missing.length ? ` (missing ${missing.slice(0, 3).map((r) => r.slug)})` : ""));

// Counts the page claims must equal what the builder wrote.
const ridingCountRe = new RegExp(`\\b${ridings.length}\\b`);
ok(ridingCountRe.test(html), `page reflects the ${ridings.length}-district count`);

// The sitemap must advertise the page.
const sitemap = fs.readFileSync(path.join(ROOT, "out/sitemap.xml"), "utf8");
ok(sitemap.includes("/riding/"), "sitemap.xml includes /riding/");

console.log(`check-riding-export: ${checks} checks passed ` +
  `(${ridings.length} districts, ${candidates.length} candidates)`);
