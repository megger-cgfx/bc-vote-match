/**
 * verify-riding-bundle.mjs — internal-consistency gate for the M6b delivery bundle
 * (data/candidates/) the site's riding view renders from.
 *
 *   node scripts/verify-riding-bundle.mjs
 *
 * Checks, against data/candidates/{ridings,candidates,postal-to-riding}.json:
 *   • 93 unique riding slugs; the postal master map covers the same set, both ways.
 *   • every candidate references a riding that exists; unique candidate ids.
 *   • party_slug is one of the five contract slugs (docs/SCHEMA.md) or null;
 *     affiliation stays consistent with party_slug; status ∈ {nominated, declared}.
 *   • every riding has at least one candidate and at least one postal code.
 *   • postal keys are 6-char uppercase; FSA entries only reference existing ridings.
 *   • the bundle mirrors data/ridings/ (M6 canonical) slug-for-slug, id-for-id.
 *
 * Exits 1 and prints every finding when anything is inconsistent — it reports, it does
 * not paper over. It never writes to data/.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const read = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), "utf8"));

const KNOWN_PARTIES = new Set(["ndp", "cpb", "green", "onebc", "centrebc"]);

const ridings = read("data/candidates/ridings.json");
const candidates = read("data/candidates/candidates.json");
const postal = read("data/candidates/postal-to-riding.json");

const findings = [];
const finding = (msg) => findings.push(msg);

// --- ridings -----------------------------------------------------------------
const slugs = ridings.map((r) => r.slug);
const slugSet = new Set(slugs);
if (slugs.length !== 93) finding(`ridings.json has ${slugs.length} rows, expected 93`);
if (slugSet.size !== slugs.length) {
  const dup = [...new Set(slugs.filter((s, i) => slugs.indexOf(s) !== i))];
  finding(`duplicate riding slugs in ridings.json: ${dup.join(", ")}`);
}

// --- candidates --------------------------------------------------------------
const seenIds = new Map();
const byRiding = new Map();
for (const c of candidates) {
  seenIds.set(c.id, (seenIds.get(c.id) ?? 0) + 1);
  if (!slugSet.has(c.riding_slug)) {
    finding(`candidate ${c.id} references missing riding "${c.riding_slug}"`);
  } else {
    byRiding.set(c.riding_slug, (byRiding.get(c.riding_slug) ?? 0) + 1);
  }
  if (c.party_slug !== null && !KNOWN_PARTIES.has(c.party_slug)) {
    finding(`candidate ${c.id} has party_slug "${c.party_slug}" outside the five contract slugs`);
  }
  if ((c.party_slug !== null) !== (c.affiliation === "party")) {
    finding(`candidate ${c.id}: party_slug/affiliation disagree (${c.party_slug} / ${c.affiliation})`);
  }
  if (!["nominated", "declared"].includes(c.status)) {
    finding(`candidate ${c.id} has status "${c.status}"`);
  }
}
for (const [id, n] of seenIds) if (n > 1) finding(`duplicate candidate id ${id} (${n} rows)`);
for (const slug of slugs) {
  if (!byRiding.get(slug)) finding(`riding ${slug} has no candidates`);
}

// --- postal lookup -----------------------------------------------------------
const pSlugs = new Set(Object.keys(postal.ridings ?? {}));
for (const s of slugSet) if (!pSlugs.has(s)) finding(`riding ${s} missing from postal-to-riding.ridings`);
for (const s of pSlugs) if (!slugSet.has(s)) finding(`postal-to-riding.ridings has unknown riding ${s}`);

const pcByRiding = new Map();
let straddling = 0;
for (const [code, val] of Object.entries(postal.postal ?? {})) {
  if (!/^[A-Z0-9]{6}$/.test(code)) finding(`postal key "${code}" is not 6-char uppercase alnum`);
  const targets = Array.isArray(val) ? val : [val];
  if (Array.isArray(val)) straddling += 1;
  for (const t of targets) {
    if (!slugSet.has(t)) finding(`postal code ${code} maps to missing riding "${t}"`);
    pcByRiding.set(t, (pcByRiding.get(t) ?? 0) + 1);
  }
}
for (const slug of slugs) {
  if (!pcByRiding.get(slug)) finding(`riding ${slug} has no postal codes`);
}
for (const [fsa, info] of Object.entries(postal.fsa ?? {})) {
  for (const s of info.ridings ?? []) {
    if (!slugSet.has(s)) finding(`FSA ${fsa} references missing riding ${s}`);
  }
  if (!(info.ridings ?? []).includes(info.primary)) {
    finding(`FSA ${fsa}: primary "${info.primary}" is not in its own ridings list`);
  }
}

// --- mirror of the M6 canonical files ---------------------------------------
const m6Ridings = read("data/ridings/ridings.json");
const m6Candidates = read("data/ridings/candidates.json");
if (m6Ridings.map((r) => r.slug).join(",") !== slugs.join(",")) {
  finding("data/candidates/ridings.json slugs differ from data/ridings/ridings.json");
}
const m6Ids = new Set(m6Candidates.map((c) => c.id));
const bundleIds = new Set(candidates.map((c) => c.id));
for (const id of m6Ids) if (!bundleIds.has(id)) finding(`candidate ${id} in data/ridings but not the bundle`);
for (const id of bundleIds) if (!m6Ids.has(id)) finding(`candidate ${id} in the bundle but not data/ridings`);

// --- report ------------------------------------------------------------------
if (findings.length > 0) {
  console.error(`verify-riding-bundle: ${findings.length} finding(s):`);
  for (const f of findings) console.error("  - " + f);
  process.exit(1);
}
console.log(
  `verify-riding-bundle: OK — ${slugs.length} ridings, ${candidates.length} candidates, ` +
    `${Object.keys(postal.postal ?? {}).length} postal codes (${straddling} straddling), ` +
    `${Object.keys(postal.fsa ?? {}).length} FSAs`,
);
