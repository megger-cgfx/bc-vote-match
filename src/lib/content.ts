/**
 * content.ts — build-time loader for the public copy in docs/content/.
 *
 * The pages render these markdown files directly, so an edit to the markdown
 * flows into the site on the next build. Nothing here may state a partisan
 * position. See docs/content/NEUTRALITY-PROTOCOL.md before editing.
 */
import fs from "node:fs";
import path from "node:path";

const CONTENT_DIR = path.join(process.cwd(), "docs", "content");

/** Canonical docs/content file names used by the site. */
export const DOC_FILES = {
  about: "ABOUT.md",
  disclaimer: "DISCLAIMER.md",
  methodology: "METHODOLOGY.md",
  neutrality: "NEUTRALITY-PROTOCOL.md",
  privacy: "PRIVACY.md",
} as const;

/**
 * Where relative markdown links (e.g. [Privacy](PRIVACY.md)) land on the site.
 * Everything else is left alone.
 */
const DOC_ROUTES: Record<string, string> = {
  "about.md": "/about/",
  "disclaimer.md": "/about/#disclaimer",
  "editorial-checklist.md": "/about/",
  "methodology.md": "/methodology/",
  "neutrality-protocol.md": "/methodology/#neutrality-protocol",
  "privacy.md": "/privacy/",
};

/** Rewrite a markdown link target to a site route when it points at a doc file. */
export function docLinkHref(href: string): string {
  if (/^[a-z][a-z0-9+.-]*:/i.test(href) || href.startsWith("#") || href.startsWith("/")) {
    return href;
  }
  const file = href.split("/").pop()!.toLowerCase();
  return DOC_ROUTES[file] ?? `/${file.replace(/\.md$/, "")}/`;
}

const cache = new Map<string, string>();

/**
 * Read a markdown file from docs/content/ at build time (pages using this are
 * statically prerendered by `next build`).
 */
export function getDoc(file: string): string {
  const cached = cache.get(file);
  if (cached !== undefined) return cached;
  const text = fs
    .readFileSync(path.join(CONTENT_DIR, file), "utf8")
    .replace(/\r\n/g, "\n");
  cache.set(file, text);
  return text;
}
