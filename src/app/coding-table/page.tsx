import type { Metadata } from "next";
import Link from "next/link";

import { getDataset } from "@/lib/data";
import { TOPIC_LABELS } from "@/lib/schema";
import { SITE, pageOg } from "@/lib/site";

export const metadata: Metadata = {
  title: "Coding table",
  description:
    "Every party code in BC Vote Match with its verbatim quote, source link, archive link and coder.",
  alternates: { canonical: "/coding-table/" },
  openGraph: pageOg(`Coding table · ${SITE.name}`, "/coding-table/"),
};

function codeText(v: number | null): string {
  if (v === null) return "—";
  return v > 0 ? `+${v}` : String(v);
}

export default function CodingTablePage() {
  const { parties, questions, codings, sources } = getDataset();
  const index = new Map(codings.map((c) => [`${c.party_slug}|${c.question_id}`, c]));

  const ordered = [...questions].sort((a, b) =>
    a.topic === b.topic ? a.id.localeCompare(b.id) : a.topic.localeCompare(b.topic),
  );

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-ink-900 sm:text-3xl">
          Full coding table
        </h1>
        <p className="text-ink-700">
          This is the whole dataset, unsummarised: every statement, every party&rsquo;s code, and the
          quote it was drawn from. Publishing this is what makes the summary score checkable.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-ink-900">Codes</h2>
        <div className="overflow-x-auto rounded-lg border border-ink-200 bg-white">
          <table className="w-full border-collapse text-sm">
            <caption className="sr-only">
              Party codes per statement with source references
            </caption>
            <thead>
              <tr className="border-b border-ink-200 bg-ink-50 text-left">
                <th scope="col" className="p-2 font-medium">
                  Statement
                </th>
                {parties.map((p) => (
                  <th key={p.slug} scope="col" className="p-2 text-center font-medium">
                    <span
                      aria-hidden="true"
                      className="mr-1 inline-block h-2.5 w-2.5 rounded-full align-middle"
                      style={{ backgroundColor: p.color }}
                    />
                    {p.short}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ordered.map((q) => (
                <tr key={q.id} className="border-b border-ink-100 align-top">
                  <th scope="row" className="max-w-sm p-2 text-left font-normal">
                    <span className="font-mono text-xs text-ink-400">{q.id}</span>{" "}
                    <span className="text-ink-800">{q.statement}</span>
                    <span className="mt-0.5 block text-xs text-ink-500">
                      {TOPIC_LABELS[q.topic]} · {q.dimensions.join(" + ")} · {q.status}
                    </span>
                  </th>
                  {parties.map((p) => {
                    const c = index.get(`${p.slug}|${q.id}`);
                    return (
                      <td key={p.slug} className="p-2 text-center font-mono">
                        {c ? (
                          <a
                            href={`#${p.slug}-${q.id}`}
                            className="underline decoration-dotted underline-offset-2"
                            title={c.quote ?? "no published position"}
                          >
                            {codeText(c.code)}
                          </a>
                        ) : (
                          <span className="text-ink-300">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-ink-500">
          <span className="font-mono">−2</span> strongly disagree … <span className="font-mono">+2</span>{" "}
          strongly agree. A dash means we have no code we can stand behind for that party on
          that statement — either the party published nothing we could code, or our two
          independent coders split and the row is waiting on a blind tie-break. Either way it
          is recorded as <span className="font-mono">null</span>, never guessed and never
          scored as neutral; the source list below carries the reasoning.
        </p>
        <p className="text-sm text-ink-700">
          In plain terms: when the two coders disagree, we do not split the difference. The cell
          is published as <span className="font-mono">null</span> — a blank, not a zero — until a
          third, blind pass or a human tie-break settles it. Why so strict? A guessed code would
          put words in a party&rsquo;s mouth, and counting silence as <span className="font-mono">0</span>{" "}
          would quietly invent a neutral position the party never took. A <span className="font-mono">null</span>{" "}
          is left out of that party&rsquo;s averages and out of the alignment math entirely, so a
          split can never nudge a score in anyone&rsquo;s favour. Every split and its resolution
          stays in the public record. This is one of the published rules of the{" "}
          <Link className="text-accent underline underline-offset-2" href="/methodology/#neutrality-protocol">
            neutrality protocol
          </Link>
          .
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-ink-900">Every code, with its source</h2>
        <ul className="space-y-3">
          {codings.map((c) => {
            const q = questions.find((qq) => qq.id === c.question_id);
            const party = parties.find((p) => p.slug === c.party_slug);
            const src = c.source_id ? sources.find((s) => s.id === c.source_id) : undefined;
            return (
              <li
                key={`${c.party_slug}-${c.question_id}`}
                id={`${c.party_slug}-${c.question_id}`}
                className="scroll-mt-20 rounded-lg border border-ink-200 bg-white p-4"
              >
                <p className="text-sm">
                  <span
                    aria-hidden="true"
                    className="mr-2 inline-block h-2.5 w-2.5 rounded-full align-middle"
                    style={{ backgroundColor: party?.color ?? "#4d5461" }}
                  />
                  <strong className="font-semibold text-ink-900">{party?.short ?? c.party_slug}</strong>
                  <span className="text-ink-500"> on </span>
                  <span className="font-mono text-xs text-ink-500">{c.question_id}</span>
                  <span className="text-ink-500"> → </span>
                  <span className="font-mono">{codeText(c.code)}</span>
                  <span className="text-xs text-ink-500"> ({c.confidence} confidence)</span>
                </p>
                <p className="mt-1 text-xs text-ink-500">{q?.statement}</p>
                {c.quote ? (
                  <blockquote className="mt-2 border-l-2 border-ink-200 pl-3 text-sm text-ink-700">
                    “{c.quote}”
                  </blockquote>
                ) : (
                  <p className="mt-2 text-sm text-ink-600">
                    No published position found. Recorded as <span className="font-mono">null</span>{" "}
                    rather than scored as neutral.
                  </p>
                )}
                <p className="mt-2 text-xs text-ink-500">
                  Coder {c.coder} · {c.version} · {c.created_at}
                  {c.source_url ? (
                    <>
                      {" · "}
                      <a
                        className="text-accent underline underline-offset-2"
                        href={c.source_url}
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        source
                      </a>
                    </>
                  ) : null}
                  {c.archive_url ? (
                    <>
                      {" · "}
                      <a
                        className="text-accent underline underline-offset-2"
                        href={c.archive_url}
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        archived
                      </a>
                    </>
                  ) : null}
                  {src?.sha256 && src.sha256 !== "0".repeat(64) ? (
                    <span className="ml-1 font-mono">· sha256 {src.sha256.slice(0, 16)}…</span>
                  ) : null}
                </p>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-ink-900">Source inventory</h2>
        {sources.length === 0 ? (
          <p className="text-sm text-ink-600">No sources archived yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-ink-200 bg-white">
            <table className="w-full border-collapse text-sm">
              <caption className="sr-only">Fetched sources with hashes and archive links</caption>
              <thead>
                <tr className="border-b border-ink-200 bg-ink-50 text-left">
                  <th scope="col" className="p-2 font-medium">id</th>
                  <th scope="col" className="p-2 font-medium">party</th>
                  <th scope="col" className="p-2 font-medium">type</th>
                  <th scope="col" className="p-2 font-medium">title</th>
                  <th scope="col" className="p-2 font-medium">fetched</th>
                  <th scope="col" className="p-2 font-medium">sha256</th>
                  <th scope="col" className="p-2 font-medium">links</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={s.id} className="border-b border-ink-100">
                    <td className="p-2 font-mono text-xs">{s.id}</td>
                    <td className="p-2">{s.party_slug}</td>
                    <td className="p-2">{s.type}</td>
                    <td className="p-2">{s.title}</td>
                    <td className="p-2 text-xs text-ink-500">{s.fetched_at}</td>
                    <td className="p-2 font-mono text-xs text-ink-500">{s.sha256.slice(0, 12)}…</td>
                    <td className="p-2 text-xs">
                      <a
                        className="text-accent underline underline-offset-2"
                        href={s.url}
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        live
                      </a>
                      {s.archive_url ? (
                        <>
                          {" · "}
                          <a
                            className="text-accent underline underline-offset-2"
                            href={s.archive_url}
                            rel="noopener noreferrer"
                            target="_blank"
                          >
                            archive
                          </a>
                        </>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
