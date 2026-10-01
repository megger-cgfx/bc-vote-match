/**
 * store.ts — answer persistence. CLIENT ONLY.
 *
 * Privacy rule (SCHEMA.md / non-negotiable #3): no PII, no accounts, no network.
 * Answers live in this browser's localStorage and, optionally, in the URL hash so a
 * user can share or bookmark *their own* result. Nothing is ever sent to a server —
 * the whole site is static, so there is no server to send it to.
 */

import type { Answers } from "./scoring";

const KEY = "bcvm.answers.v1";

export function loadAnswers(): Answers {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === "object" ? (parsed as Answers) : {};
  } catch {
    return {};
  }
}

export function saveAnswers(answers: Answers): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(answers));
  } catch {
    /* private mode / quota — answers simply won't persist */
  }
}

export function clearAnswers(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}

/** Compact URL-safe encoding of the answers: `q01:2,q02:-1,q03:x` (x = don't know). */
export function encodeAnswers(answers: Answers): string {
  return Object.keys(answers)
    .sort()
    .map((id) => {
      const v = answers[id];
      return `${id}:${v === null || v === undefined ? "x" : v}`;
    })
    .join(",");
}

export function decodeAnswers(encoded: string): Answers {
  const out: Answers = {};
  if (!encoded) return out;
  for (const part of encoded.split(",")) {
    const [id, v] = part.split(":");
    if (!id || v === undefined || !/^q\d+$/.test(id)) continue;
    if (v === "x") out[id] = null;
    else if (/^-?[0-2]$/.test(v)) out[id] = Number(v);
  }
  return out;
}

/** Build a shareable results URL from the answers. */
export function resultsUrl(answers: Answers): string {
  const qs = encodeAnswers(answers);
  const base =
    typeof window !== "undefined"
      ? `${window.location.origin}/results/`
      : "/results/";
  return qs ? `${base}?a=${encodeURIComponent(qs)}` : base;
}
