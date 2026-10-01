/**
 * site.ts — single source of truth for site-level copy and metadata.
 *
 * Nothing here may state a partisan position. See docs/01-RECOMMENDED-ANSWERS.md
 * (Q2 neutrality / Q3 disclaimer) before editing.
 */

export const SITE = {
  name: "BC Vote Match",
  tagline: "See which party matches your views — BC 2026.",
  url: "https://bcvotematch.ca",
  description:
    "A free, independent, party-level voter alignment tool for the BC 2026 provincial election. " +
    "Every party position is quoted from a public source with an archived copy and a hash.",
  locale: "en_CA",
  electionDay: "2026-10-24",
  advanceVoting: "2026-10-16 – 2026-10-21",
  slugLine: "party-level, EN only · open source · no accounts, no tracking, no personal data",
  ogImage: "/og.png",
  ogImageAlt: "BC Vote Match: see which B.C. party matches your views — BC 2026",
  disclaimer:
    "BC Vote Match is an educational tool. It is designed to show you where your views sit next to " +
    "each party's published positions. It does not tell you how to vote and it does not predict your vote.",
  independenceDisclaimer:
    "BC Vote Match is an independent, non-partisan educational project. It is not affiliated with, " +
    "endorsed by, or connected to Vote Compass or Vox Pop Labs, any political party, candidate, or " +
    "Elections BC. It does not tell you how to vote and it does not predict your vote.",
} as const;

export const NAV = [
  { href: "/questions/", label: "Take the survey" },
  { href: "/riding/", label: "Your riding" },
  { href: "/parties/", label: "Parties" },
  { href: "/methodology/", label: "Method" },
  { href: "/coding-table/", label: "Coding table" },
  { href: "/about/", label: "About" },
] as const;

/**
 * Per-page OpenGraph block. Next replaces the whole `openGraph` object when a page defines
 * one, so every page that sets its own title/url must repeat the share image — otherwise the
 * card loses `og:image` and falls back to a bare link. Use this rather than hand-writing it.
 */
export function pageOg(title: string, path: string) {
  return {
    type: "website" as const,
    siteName: SITE.name,
    title,
    description: SITE.description,
    url: path,
    images: [
      { url: SITE.ogImage, width: 1200, height: 630, alt: SITE.ogImageAlt },
    ],
  };
}

/** Likert labels for the −2 … +2 user scale. Index 0 == −2. */
export const LIKERT_LABELS = [
  "Strongly disagree",
  "Disagree",
  "Neutral",
  "Agree",
  "Strongly agree",
] as const;
