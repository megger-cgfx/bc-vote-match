/**
 * Markdown.tsx — a deliberately small markdown → JSX renderer for the public
 * copy in docs/content/. Supports just what those documents use: headings,
 * paragraphs, ordered/unordered lists, tables, fenced code, blockquotes, and
 * inline bold/em/code/links. No runtime dependency, no dangerouslySetInnerHTML.
 */
import type { ReactNode } from "react";
import Link from "next/link";

import { docLinkHref } from "@/lib/content";

const HEADING_CLASSES: Record<number, string> = {
  1: "text-2xl font-semibold tracking-tight text-ink-900 sm:text-3xl",
  2: "mt-2 text-lg font-semibold text-ink-900",
  3: "mt-2 text-base font-semibold text-ink-800",
  4: "mt-2 text-sm font-semibold text-ink-800",
  5: "mt-2 text-sm font-semibold text-ink-800",
  6: "mt-2 text-sm font-semibold text-ink-800",
};

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** Inline markdown pattern. A fresh RegExp is created per call on purpose: a shared
 *  /g regex would have its `lastIndex` clobbered by recursive calls (bold/em/link
 *  labels containing markup), spinning the scan loop forever. */
const INLINE_PATTERN = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\[[^\]]+\]\([^)]+\))|(\*[^*\n]+\*)/;

function renderInline(text: string, keyBase: string): ReactNode[] {
  const re = new RegExp(INLINE_PATTERN.source, "g");
  const nodes: ReactNode[] = [];
  let last = 0;
  let n = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    if (m.index > last) nodes.push(text.slice(last, m.index));
    const key = `${keyBase}-${n++}`;
    const tok = m[0];
    if (tok.startsWith("`")) {
      nodes.push(
        <code key={key} className="rounded bg-ink-100 px-1 py-0.5 font-mono text-[0.85em] text-ink-800">
          {tok.slice(1, -1)}
        </code>,
      );
    } else if (tok.startsWith("**")) {
      nodes.push(
        <strong key={key} className="font-semibold text-ink-900">
          {renderInline(tok.slice(2, -2), key)}
        </strong>,
      );
    } else if (tok.startsWith("[")) {
      const parts = /\[([^\]]+)\]\(([^)]+)\)/.exec(tok);
      const label = renderInline(parts?.[1] ?? tok, key);
      const href = docLinkHref(parts?.[2] ?? "#");
      nodes.push(
        href.startsWith("/") ? (
          <Link key={key} href={href} className="text-accent underline underline-offset-2">
            {label}
          </Link>
        ) : (
          <a
            key={key}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent underline underline-offset-2"
          >
            {label}
          </a>
        ),
      );
    } else {
      nodes.push(<em key={key}>{renderInline(tok.slice(1, -1), key)}</em>);
    }
    last = m.index + tok.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function Heading({ level, id, children }: { level: number; id: string; children: ReactNode }) {
  const className = HEADING_CLASSES[level] ?? HEADING_CLASSES[6];
  if (level === 1) return <h1 id={id} className={className}>{children}</h1>;
  if (level === 2) return <h2 id={id} className={className}>{children}</h2>;
  if (level === 3) return <h3 id={id} className={className}>{children}</h3>;
  if (level === 4) return <h4 id={id} className={className}>{children}</h4>;
  if (level === 5) return <h5 id={id} className={className}>{children}</h5>;
  return <h6 id={id} className={className}>{children}</h6>;
}

function splitRow(line: string): string[] {
  return line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
}

export function Markdown({
  source,
  demote = 0,
}: {
  source: string;
  /** Shift every heading level down by n (e.g. a second H1 on a page becomes H2). */
  demote?: number;
}) {
  const lines = source.split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i++;
      continue;
    }

    // Fenced code block.
    if (/^```/.test(line)) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !/^```/.test(lines[i])) buf.push(lines[i++]);
      i++;
      blocks.push(
        <pre
          key={`code-${i}`}
          className="overflow-x-auto rounded-lg border border-ink-200 bg-ink-50 p-3 font-mono text-xs text-ink-800"
        >
          <code>{buf.join("\n")}</code>
        </pre>,
      );
      continue;
    }

    // Heading.
    const h = /^(#{1,6})\s+(.*)$/.exec(line);
    if (h) {
      const level = Math.min(6, h[1].length + demote);
      const text = h[2].trim();
      blocks.push(
        <Heading key={`h-${i}`} level={level} id={slugify(text)}>
          {renderInline(text, `h${i}`)}
        </Heading>,
      );
      i++;
      continue;
    }

    // Table: a pipe row followed by a separator row.
    if (
      line.trim().startsWith("|") &&
      i + 1 < lines.length &&
      /^\|[\s:|-]+\|$/.test(lines[i + 1].trim())
    ) {
      const header = splitRow(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        rows.push(splitRow(lines[i]));
        i++;
      }
      blocks.push(
        <div key={`table-${i}`} className="overflow-x-auto rounded-lg border border-ink-200 bg-white">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-ink-200 bg-ink-50 text-left">
                {header.map((cell, ci) => (
                  <th key={ci} scope="col" className="p-2 font-medium text-ink-900">
                    {renderInline(cell, `th${i}-${ci}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, ri) => (
                <tr key={ri} className="border-b border-ink-100">
                  {row.map((cell, ci) => (
                    <td key={ci} className="p-2 align-top text-ink-700">
                      {renderInline(cell, `td${i}-${ri}-${ci}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    // Blockquote.
    if (/^>\s?/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) buf.push(lines[i++].replace(/^>\s?/, ""));
      blocks.push(
        <blockquote
          key={`q-${i}`}
          className="border-l-2 border-ink-200 pl-3 text-sm text-ink-700"
        >
          {renderInline(buf.join(" "), `q${i}`)}
        </blockquote>,
      );
      continue;
    }

    // Unordered list (supports "- [ ]" task boxes as plain text).
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ""));
        i++;
      }
      blocks.push(
        <ul key={`ul-${i}`} className="list-disc space-y-2 pl-5 text-sm text-ink-700">
          {items.map((item, ii) => (
            <li key={ii}>{renderInline(item, `li${i}-${ii}`)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    // Ordered list.
    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ""));
        i++;
      }
      blocks.push(
        <ol key={`ol-${i}`} className="list-decimal space-y-2 pl-5 text-sm text-ink-700">
          {items.map((item, ii) => (
            <li key={ii}>{renderInline(item, `oi${i}-${ii}`)}</li>
          ))}
        </ol>,
      );
      continue;
    }

    // Paragraph: run until a blank line or the start of another block.
    const buf: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !/^(#{1,6}\s|```|>\s?|[-*]\s+|\d+\.\s+|\|)/.test(lines[i])
    ) {
      buf.push(lines[i].trim());
      i++;
    }
    blocks.push(
      <p key={`p-${i}`} className="text-sm leading-relaxed text-ink-700">
        {renderInline(buf.join(" "), `p${i}`)}
      </p>,
    );
  }

  return <div className="space-y-4">{blocks}</div>;
}
