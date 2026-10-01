/**
 * postal.ts — postal code → electoral district lookup (M6b), client-side and offline.
 *
 * Reads the shape produced by `scripts/build-postal-lookup.py` and documented in
 * docs/M6b-POSTAL-LOOKUP.md / docs/SCHEMA.md:
 *
 *   postal:  "V0A0A0" -> "columbia-river-revelstoke"  (or a sorted list when the code
 *            straddles a boundary — GeoNames representative points can land on one)
 *   fsa:     "V0A" -> { ridings, primary, counts }    (fallback for partial input)
 *   ridings: the 93-riding master map
 *
 * Honesty rules baked in here:
 *   • A code that is not in the dataset is reported as not found. It is NEVER resolved
 *     to `fsa.primary` silently — `primary` is just the FSA's largest cluster of codes,
 *     not a fact about the visitor's address.
 *   • The FSA fallback only ever *lists* the districts an FSA covers; the visitor picks.
 *     The only automatic resolution is an exact 6-character hit in `postal`.
 *
 * Pure module (type-only imports, no fs, no deps): `node --experimental-strip-types`
 * can import it directly for the smoke suite. The dataset itself is loaded lazily via
 * `loadPostalIndex()` — one ~3.8 MB fetch chunk, only when the visitor uses the lookup.
 */

/** data/candidates/postal-to-riding.json — the master map's riding entry. */
export interface PostalRidingInfo {
  name: string;
  district_id?: number;
  ed_abbreviation?: string;
}

/** An FSA ("V8R"): the districts its postal codes fall in, with per-district counts. */
export interface PostalFsaInfo {
  ridings: string[];
  primary: string;
  counts: Record<string, number>;
}

/** The subset of postal-to-riding.json the site needs. */
export interface PostalIndex {
  ridings: Record<string, PostalRidingInfo>;
  fsa: Record<string, PostalFsaInfo>;
  postal: Record<string, string | string[]>;
}

export type PostalLookup =
  /** Exact 6-character hit: one district. The UI may select it. */
  | { kind: "exact"; code: string; riding: string }
  /** Exact hit that straddles a boundary: the visitor must pick one. */
  | { kind: "straddling"; code: string; ridings: string[] }
  /** Input was a 3-character forward sorting area, not a full code. */
  | { kind: "fsa"; fsa: string; ridings: PostalFsaInfo }
  /** Full code not in the dataset, but its FSA is: show what the FSA covers. */
  | { kind: "fsa-hint"; code: string; fsa: string; ridings: PostalFsaInfo }
  /** Well-formed code (or FSA) with no entry at all. */
  | { kind: "not-found"; input: string }
  /** Not even a plausible Canadian postal code shape. */
  | { kind: "invalid"; input: string };

const FSA_RE = /^[A-Z]\d[A-Z]$/;
const FULL_RE = /^[A-Z]\d[A-Z]\d[A-Z]\d$/;

/** Uppercase and strip spaces, hyphens and anything else: "v8r-3l2 " → "V8R3L2". */
export function normalisePostal(raw: string): string {
  return String(raw ?? "")
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "");
}

/** True for "A1A 1A1" (after normalisation) or its "A1A" FSA prefix. */
export function isPostalShaped(input: string): boolean {
  return FSA_RE.test(input) || FULL_RE.test(input);
}

export function lookupPostal(index: PostalIndex, raw: string): PostalLookup {
  const input = normalisePostal(raw);

  if (FSA_RE.test(input)) {
    const fsa = index.fsa?.[input];
    return fsa && fsa.ridings?.length
      ? { kind: "fsa", fsa: input, ridings: fsa }
      : { kind: "not-found", input };
  }

  if (!FULL_RE.test(input)) return { kind: "invalid", input };

  const hit = index.postal?.[input];
  if (typeof hit === "string" && hit) return { kind: "exact", code: input, riding: hit };
  if (Array.isArray(hit) && hit.length > 0) {
    return hit.length === 1
      ? { kind: "exact", code: input, riding: hit[0] }
      : { kind: "straddling", code: input, ridings: [...hit] };
  }

  // No entry for the full code. The FSA may still be known — offer its districts as
  // an explicit choice, never as an automatic answer.
  const fsa = index.fsa?.[input.slice(0, 3)];
  if (fsa && fsa.ridings?.length) {
    return { kind: "fsa-hint", code: input, fsa: input.slice(0, 3), ridings: fsa };
  }
  return { kind: "not-found", input };
}

/** Cheap runtime guard so a malformed bundle can't crash the lookup UI. */
export function isPostalIndex(x: unknown): x is PostalIndex {
  if (!x || typeof x !== "object") return false;
  const o = x as Record<string, unknown>;
  return (
    typeof o.ridings === "object" &&
    o.ridings !== null &&
    typeof o.fsa === "object" &&
    o.fsa !== null &&
    typeof o.postal === "object" &&
    o.postal !== null
  );
}

/**
 * Lazy-load the real dataset (3.8 MB, one fetch chunk, on first use). The relative
 * import resolves to data/candidates/postal-to-riding.json; the bundler emits it as a
 * separate chunk rather than inlining it into the page.
 */
export async function loadPostalIndex(): Promise<PostalIndex> {
  const mod = await import("../../data/candidates/postal-to-riding.json");
  const data = (mod as { default?: unknown }).default ?? mod;
  if (!isPostalIndex(data)) {
    throw new Error("postal-to-riding.json has an unexpected shape");
  }
  return data;
}
