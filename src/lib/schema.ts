/**
 * schema.ts — TypeScript mirror of docs/SCHEMA.md.
 *
 * This file is a 1:1 transcription of the data contract every agent writes to.
 * If you change a shape here, change docs/SCHEMA.md in the same commit.
 */

export type PartySlug = "ndp" | "cpb" | "green" | "onebc" | "centrebc";

export const PARTY_SLUGS: PartySlug[] = ["ndp", "cpb", "green", "onebc", "centrebc"];

export type Topic =
  | "cost-of-living-taxes"
  | "housing"
  | "health"
  | "climate-environment"
  | "indigenous-reconciliation"
  | "public-safety";

export const TOPICS: Topic[] = [
  "cost-of-living-taxes",
  "housing",
  "health",
  "climate-environment",
  "indigenous-reconciliation",
  "public-safety",
];

export type Dimension = "economic" | "social";

export const DIMENSIONS: Dimension[] = ["economic", "social"];

export type SourceType =
  | "platform"
  | "policy"
  | "release"
  | "speech"
  | "hansard"
  | "media"
  | "other";

/** Source priority when coding (highest first), per SCHEMA.md. */
export const SOURCE_PRIORITY: SourceType[] = [
  "platform",
  "policy",
  "release",
  "speech",
  "hansard",
  "media",
  "other",
];

export type Confidence = "high" | "medium" | "low";

/** data/ridings/ridings.json — one of BC's 93 electoral districts (M6). */
export interface Riding {
  slug: string;
  name: string;
  /** Grouping heading from the source article, e.g. "Greater Victoria". */
  region: string;
  source_id: string;
}

export type CandidateAffiliation = "party" | "independent" | "other";
export type CandidateStatus = "nominated" | "declared";

/** data/ridings/candidates.json — a candidate standing in a riding (M6). */
export interface Candidate {
  id: string;
  riding_slug: string;
  name: string;
  /** One of the five contract parties, or null for independent/other candidates. */
  party_slug: PartySlug | null;
  /** The ballot label, e.g. "BC NDP", "Independent", "Libertarian". */
  party_label: string;
  /** The source article's column heading, kept verbatim for auditability. */
  party_col: string;
  affiliation: CandidateAffiliation;
  /** True when this candidate is the riding's sitting MLA. */
  incumbent: boolean;
  /** True when the source article marks the candidate as registered with Elections BC. */
  registered: boolean;
  /** "nominated" = confirmed on the Elections BC candidate list, else "declared". */
  status: CandidateStatus;
  source_id: string;
  source_url: string;
  ebc_source_id: string | null;
  version: string;
  fetched_at: string;
}

/** data/parties.json */
export interface Party {
  slug: PartySlug;
  name: string;
  short: string;
  leader: string;
  leader_status: string;
  color: string;
  url: string;
  note?: string;
}

/** data/raw/<party>/sources.json */
export interface SourceRecord {
  id: string;
  party_slug: PartySlug;
  type: SourceType;
  title: string;
  url: string;
  published: string;
  fetched_at: string;
  sha256: string;
  local_path: string;
  text_path: string;
  archive_url: string | null;
}

/** data/questions/questions.json */
export interface Question {
  id: string;
  statement: string;
  topic: Topic;
  dimensions: Dimension[];
  status: "candidate" | "frozen";
  notes: string;
}

/** data/codings/<party>.json */
export interface Coding {
  party_slug: PartySlug;
  question_id: string;
  /** −2 … +2 = agreement with the statement, or null = no published position. */
  code: -2 | -1 | 0 | 1 | 2 | null;
  quote: string | null;
  source_id: string | null;
  source_url: string | null;
  archive_url: string | null;
  coder: string;
  version: string;
  created_at: string;
  confidence: Confidence;
}

/** The whole dataset the site renders, however it was sourced. */
export interface Dataset {
  parties: Party[];
  questions: Question[];
  codings: Coding[];
  sources: SourceRecord[];
  /** The 93 electoral districts (M6 riding layer). Empty until built. */
  ridings: Riding[];
  /** Candidates standing in those ridings (M6 riding layer). Empty until built. */
  candidates: Candidate[];
  counts: {
    parties: number;
    questions: number;
    frozenQuestions: number;
    codings: number;
    sources: number;
    ridings: number;
    candidates: number;
  };
}

export const TOPIC_LABELS: Record<Topic, string> = {
  "cost-of-living-taxes": "Cost of living & taxes",
  housing: "Housing",
  health: "Health care",
  "climate-environment": "Climate & environment",
  "indigenous-reconciliation": "Indigenous reconciliation",
  "public-safety": "Public safety",
};

export const DIMENSION_LABELS: Record<Dimension, string> = {
  economic: "Economic",
  social: "Social",
};

/** Left/right pole captions for the 2-D compass. */
export const DIMENSION_POLES: Record<Dimension, { low: string; high: string }> = {
  economic: { low: "Economic left", high: "Economic right" },
  social: { low: "Socially progressive", high: "Socially traditional" },
};
