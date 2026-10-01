/**
 * data.ts — build-time loader for the in-repo JSON dataset.
 *
 * SERVER ONLY. This module touches the filesystem and must only be imported from
 * server components (pages/layouts). Client components receive the resulting
 * `Dataset` as plain props.
 *
 * Real project data only (docs/SCHEMA.md). There is no fixture fallback and no
 * banner: if a contract file is missing or malformed the loader THROWS, so
 * `next build` fails loudly instead of shipping placeholder data.
 *
 *   data/parties.json                        the 5 parties
 *   data/questions/questions.v2.json         versioned question set, when it exists
 *   data/questions/questions.json            otherwise
 *   data/codings/<party>.json                coder rows (`_`/`.` sidecars skipped)
 *   data/raw/<party>/sources.json            fetched-source inventory
 *   data/candidates/ridings.json             riding view (falls back to data/ridings/)
 *   data/candidates/candidates.json          riding view (falls back to data/ridings/)
 *
 * The two independent coder rows per (party, question) are reconciled to one
 * published code by `mergeCodings` (src/lib/reconcile.ts) — agreement publishes the
 * best-evidenced code, a split publishes nothing rather than a guessed number.
 */

import fs from "node:fs";
import path from "node:path";

import type {
  Candidate,
  Coding,
  Dataset,
  Party,
  Question,
  Riding,
  SourceRecord,
} from "./schema";
import { PARTY_SLUGS } from "./schema";
import { mergeCodings } from "./reconcile";

const ROOT = process.cwd();
const DATA = path.join(ROOT, "data");

function readJson<T>(file: string): T {
  if (!fs.existsSync(file)) {
    throw new Error(`[bc-vote-match] required dataset file is missing: ${path.relative(ROOT, file)}`);
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (err) {
    throw new Error(`[bc-vote-match] ${path.relative(ROOT, file)} is not valid JSON: ${err}`);
  }
  return parsed as T;
}

function readJsonOr<T>(file: string, fallback: T): T {
  return fs.existsSync(file) ? readJson<T>(file) : fallback;
}

function rows<T>(value: unknown, file: string): T[] {
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error(`[bc-vote-match] ${path.relative(ROOT, file)} must hold a non-empty JSON array`);
  }
  return value as T[];
}

function loadParties(): Party[] {
  const file = path.join(DATA, "parties.json");
  const all = rows<Party>(readJson(file), file);
  const known = new Set(PARTY_SLUGS as string[]);
  return all.filter((p) => known.has(p.slug));
}

function loadQuestions(): Question[] {
  // The questionnaire is a living document (docs/02-PLAN.md): statements are frozen
  // per version. A questions.v2.json supersedes questions.json when the freeze gate
  // publishes one; until then the pool file is the question set.
  const v2 = path.join(DATA, "questions", "questions.v2.json");
  const file = fs.existsSync(v2) ? v2 : path.join(DATA, "questions", "questions.json");
  return rows<Question>(readJson(file), file);
}

function loadCodings(): Coding[] {
  const dir = path.join(DATA, "codings");
  if (!fs.existsSync(dir)) {
    throw new Error(`[bc-vote-match] required dataset directory is missing: ${path.relative(ROOT, dir)}`);
  }
  const out: Coding[] = [];
  for (const name of fs.readdirSync(dir).sort()) {
    // "_"/"."-prefixed files are audit/verification side-cars, not coding rows.
    if (!name.endsWith(".json") || name.startsWith(".") || name.startsWith("_")) continue;
    const file = path.join(dir, name);
    const raw = rows<Coding>(readJson(file), file);
    const good = raw.filter(
      (r) =>
        r &&
        typeof r === "object" &&
        typeof r.party_slug === "string" &&
        typeof r.question_id === "string" &&
        "code" in r,
    );
    if (good.length === 0) {
      throw new Error(`[bc-vote-match] ${path.relative(ROOT, file)} holds no coding rows`);
    }
    out.push(...good);
  }
  if (out.length === 0) {
    throw new Error(`[bc-vote-match] ${path.relative(ROOT, dir)} holds no <party>.json coding files`);
  }
  // Two independent coder rows per (party, question) → one published code.
  return mergeCodings(out);
}

function loadSources(): SourceRecord[] {
  const raw = path.join(DATA, "raw");
  const out: SourceRecord[] = [];
  for (const party of fs.readdirSync(raw).sort()) {
    const file = path.join(raw, party, "sources.json");
    if (!fs.existsSync(file)) continue;
    out.push(...rows<SourceRecord>(readJson(file), file));
  }
  return out;
}

/**
 * Riding view data from the M6b delivery bundle (data/candidates/), falling back to
 * the canonical M6 build output (data/ridings/) if the bundle is not generated yet.
 * The riding layer is additive: absent files mean "no riding view yet", not an error.
 */
function loadRidings(): Riding[] {
  const bundle = path.join(DATA, "candidates", "ridings.json");
  const m6 = path.join(DATA, "ridings", "ridings.json");
  const file = fs.existsSync(bundle) ? bundle : m6;
  return fs.existsSync(file) ? rows<Riding>(readJson(file), file) : [];
}

function loadCandidates(): Candidate[] {
  const bundle = path.join(DATA, "candidates", "candidates.json");
  const m6 = path.join(DATA, "ridings", "candidates.json");
  const file = fs.existsSync(bundle) ? bundle : m6;
  return fs.existsSync(file) ? rows<Candidate>(readJson(file), file) : [];
}

let cached: Dataset | null = null;

export function getDataset(): Dataset {
  if (cached) return cached;

  const parties = loadParties();
  const questions = loadQuestions();
  const codings = loadCodings();
  const sources = loadSources();
  const ridings = loadRidings();
  const candidates = loadCandidates();

  cached = {
    parties,
    questions,
    codings,
    sources,
    ridings,
    candidates,
    counts: {
      parties: parties.length,
      questions: questions.length,
      frozenQuestions: questions.filter((q) => q.status === "frozen").length,
      codings: codings.length,
      sources: sources.length,
      ridings: ridings.length,
      candidates: candidates.length,
    },
  };
  return cached;
}

/** Candidates standing in one riding, incumbents first, then contract parties, then the rest. */
export function candidatesForRiding(candidates: Candidate[], ridingSlug: string): Candidate[] {
  return candidates
    .filter((c) => c.riding_slug === ridingSlug)
    .sort((a, b) =>
      Number(b.incumbent) - Number(a.incumbent) ||
      a.party_label.localeCompare(b.party_label) ||
      a.name.localeCompare(b.name),
    );
}

export function questionsByTopic(questions: Question[]): Map<string, Question[]> {
  const m = new Map<string, Question[]>();
  for (const q of questions) {
    const list = m.get(q.topic) ?? [];
    list.push(q);
    m.set(q.topic, list);
  }
  return m;
}

export function codingsForParty(codings: Coding[], slug: string): Coding[] {
  return codings.filter((c) => c.party_slug === slug);
}

export function sourcesForParty(sources: SourceRecord[], slug: string): SourceRecord[] {
  return sources.filter((s) => s.party_slug === slug);
}
