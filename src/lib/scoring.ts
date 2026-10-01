/**
 * scoring.ts — the v1 scoring rules, transcribed from docs/SCHEMA.md § "Scoring (v1)".
 *
 *   • Party position per dimension  = mean of its codes on that dimension's questions.
 *   • User position per dimension   = mean of their answers mapped to the same −2…+2 scale.
 *   • Alignment with a party        = 1 − (Σ|user−party| / (2·n)) over answered questions, as %.
 *   • Topic sub-scores              = mean over each topic's questions.
 *
 * Rules applied here that the schema implies but does not spell out:
 *   • A party code of `null` ("no published position") is never treated as 0 (neutral).
 *     It is excluded from that party's mean, and the question is dropped from that party's
 *     alignment denominator rather than counted as agreement or disagreement.
 *   • "Don't know" by the user is `null` and is excluded the same way.
 *   • An alignment is `null` when fewer than MIN_PAIRS questions survive for that party —
 *     a percentage built on two questions is noise, and we say so instead of showing it.
 *
 * ⚠ OPEN SPEC ISSUE — the divisor in the alignment formula.
 * The schema says `1 − (Σ|user−party| / (2·n))`. Both sides live on −2…+2, so a single
 * question can contribute a distance of 4, and `2·n` therefore lets the raw score fall to
 * −100% for a voter who is maximally opposed. A similarity score should run 0–100, which
 * needs `4·n` (the full span of the distance). This is a methodology change and the plan
 * puts methodology behind a human gate, so this build implements the formula AS WRITTEN and
 * clamps the displayed value to 0–100 (`percent`); the unclamped value is kept in
 * `rawPercent` so the discrepancy is visible rather than silently smoothed over.
 * Flagged for the operator — see docs/04-SITE-SCAFFOLD.md.
 */

import type { Coding, Dimension, Question, Topic } from "./schema";

export const MIN_PAIRS = 5;

/** code ∈ {−2…+2, null}; answers keyed by question id, same scale. */
export type Answers = Record<string, number | null>;

/** A position on the two axes, each on the −2…+2 scale. */
export interface Point {
  economic: number;
  social: number;
}

export interface Alignment {
  partySlug: string;
  /** 0–100 (clamped), or null when too few questions could be compared. */
  percent: number | null;
  /** The unclamped result of the schema formula; can be negative. Diagnostic only. */
  rawPercent: number | null;
  /** Number of questions where both the user and the party have a position. */
  compared: number;
  /** Mean absolute distance on the −2…+2 scale, or null. */
  meanDistance: number | null;
  /** True when `compared` < MIN_PAIRS and no percentage is shown. */
  insufficient: boolean;
}

export function mean(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function meanOrNull(values: Array<number | null | undefined>): number | null {
  const xs = values.filter((v): v is number => typeof v === "number");
  return mean(xs);
}

/** Index codings by `${party}|${question}` for O(1) lookup. */
export function codingIndex(codings: Coding[]): Map<string, Coding> {
  const m = new Map<string, Coding>();
  for (const c of codings) m.set(`${c.party_slug}|${c.question_id}`, c);
  return m;
}

/** Party position on one dimension: mean of its codes on that dimension's questions. */
export function partyDimensionPosition(
  codings: Coding[],
  questionIds: string[],
): number | null {
  const ids = new Set(questionIds);
  return meanOrNull(codings.filter((c) => ids.has(c.question_id)).map((c) => c.code));
}

/** User position on one dimension: mean of their answers to that dimension's questions. */
export function userDimensionPosition(answers: Answers, questionIds: string[]): number | null {
  return meanOrNull(questionIds.map((id) => answers[id] ?? null));
}

/** Per-topic mean for a party, for the topic sub-score bars. */
export function partyTopicScores(
  codings: Coding[],
  questions: Question[],
): Record<string, number | null> {
  const out: Record<string, number | null> = {};
  for (const topic of new Set(questions.map((q) => q.topic))) {
    const ids = questions.filter((q) => q.topic === topic).map((q) => q.id);
    out[topic] = partyDimensionPosition(codings, ids);
  }
  return out;
}

/**
 * Alignment of one party with the user's answers: 1 − (Σ|user−party| / (2·n)).
 * `n` counts only questions where *both* sides have a real position.
 *
 * `codings` may be the whole dataset — this function selects the party's own rows, so
 * passing every party's codings cannot silently compare the user against the wrong party.
 */
export function alignmentForParty(
  answers: Answers,
  codings: Coding[],
  questions: Question[],
  partySlug: string,
): Alignment {
  const byQuestion = new Map(
    codings.filter((c) => c.party_slug === partySlug).map((c) => [c.question_id, c]),
  );
  let sum = 0;
  let compared = 0;

  for (const q of questions) {
    const u = answers[q.id];
    const c = byQuestion.get(q.id);
    if (typeof u !== "number" || !c || typeof c.code !== "number") continue;
    sum += Math.abs(u - c.code);
    compared += 1;
  }

  if (compared === 0) {
    return {
      partySlug,
      percent: null,
      rawPercent: null,
      compared: 0,
      meanDistance: null,
      insufficient: true,
    };
  }

  const meanDistance = sum / compared;
  // Schema formula as written — see the open spec issue in the file header.
  const normalised = 1 - sum / (2 * compared);
  const insufficient = compared < MIN_PAIRS;
  const round1 = (v: number) => Math.round(v * 1000) / 10;
  return {
    partySlug,
    percent: insufficient ? null : round1(Math.min(1, Math.max(0, normalised))),
    rawPercent: insufficient ? null : round1(normalised),
    compared,
    meanDistance: Math.round(meanDistance * 100) / 100,
    insufficient,
  };
}

export function alignAllParties(
  answers: Answers,
  codings: Coding[],
  questions: Question[],
  partySlugs: string[],
): Alignment[] {
  return partySlugs
    .map((slug) => alignmentForParty(answers, codings, questions, slug))
    .sort((a, b) => (b.percent ?? -1) - (a.percent ?? -1));
}

export function answeredCount(answers: Answers): number {
  return Object.values(answers).filter((v) => typeof v === "number").length;
}

export function dimensionPositions(
  answers: Answers,
  codings: Coding[],
  questions: Question[],
  partySlug: string,
): { economic: number | null; social: number | null } {
  const party = codings.filter((c) => c.party_slug === partySlug);
  const out: { economic: number | null; social: number | null } = {
    economic: null,
    social: null,
  };
  for (const dim of ["economic", "social"] as Dimension[]) {
    const ids = questions.filter((q) => q.dimensions.includes(dim)).map((q) => q.id);
    out[dim] = partyDimensionPosition(party, ids);
  }
  return out;
}

export function userDimensionPositions(
  answers: Answers,
  questions: Question[],
): { economic: number | null; social: number | null } {
  const out: { economic: number | null; social: number | null } = {
    economic: null,
    social: null,
  };
  for (const dim of ["economic", "social"] as Dimension[]) {
    const ids = questions.filter((q) => q.dimensions.includes(dim)).map((q) => q.id);
    out[dim] = userDimensionPosition(answers, ids);
  }
  return out;
}

/** Cheap guard so a malformed answers blob from localStorage can't crash the results page. */
export function sanitiseAnswers(raw: unknown, questions: Question[]): Answers {
  const valid = new Set(questions.map((q) => q.id));
  const out: Answers = {};
  if (!raw || typeof raw !== "object") return out;
  for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
    if (!valid.has(k)) continue;
    if (v === null) out[k] = null;
    else if (typeof v === "number" && Number.isInteger(v) && v >= -2 && v <= 2) out[k] = v;
  }
  return out;
}

export type { Topic };
