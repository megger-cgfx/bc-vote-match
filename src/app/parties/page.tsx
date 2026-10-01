import type { Metadata } from "next";

import { getDataset } from "@/lib/data";
import { TOPIC_LABELS } from "@/lib/schema";
import { SITE, pageOg } from "@/lib/site";

export const metadata: Metadata = {
  title: "The parties",
  description:
    "The parties included in BC Vote Match, their leaders, and how many statements each has a sourced position on.",
  alternates: { canonical: "/parties/" },
  openGraph: pageOg(`Parties · ${SITE.name}`, "/parties/"),
};

export default function PartiesPage() {
  const { parties, questions, codings, sources } = getDataset();

  const perTopic = questions.reduce<Record<string, number>>((acc, q) => {
    acc[q.topic] = (acc[q.topic] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-ink-900 sm:text-3xl">Parties</h1>
        <p className="text-ink-700">
          {parties.length} parties are coded for this release. Every party gets the same question set,
          the same source ladder, and the same coding effort — that symmetry is the whole point.
        </p>
      </header>

      <ul className="space-y-4">
        {parties.map((p) => {
          const own = codings.filter((c) => c.party_slug === p.slug);
          const positioned = own.filter((c) => c.code !== null).length;
          const srcs = sources.filter((s) => s.party_slug === p.slug);
          const byTopic = Object.entries(perTopic).map(([topic, total]) => {
            const coded = own.filter(
              (c) => c.code !== null && questions.find((q) => q.id === c.question_id)?.topic === topic,
            ).length;
            return `${TOPIC_LABELS[topic as keyof typeof TOPIC_LABELS] ?? topic} ${coded}/${total}`;
          });
          return (
            <li key={p.slug} className="rounded-lg border border-ink-200 bg-white p-4 sm:p-5">
              <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <span
                  aria-hidden="true"
                  className="inline-block h-3 w-3 rounded-full"
                  style={{ backgroundColor: p.color }}
                />
                <h2 className="text-lg font-semibold text-ink-900">{p.name}</h2>
                <span className="text-sm text-ink-500">{p.short}</span>
              </div>
              <dl className="mt-3 grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
                <div className="flex gap-2">
                  <dt className="text-ink-500">Leader</dt>
                  <dd className="text-ink-800">
                    {p.leader} <span className="text-ink-500">({p.leader_status})</span>
                  </dd>
                </div>
                <div className="flex gap-2">
                  <dt className="text-ink-500">Positions coded</dt>
                  <dd className="text-ink-800">
                    {positioned} of {questions.length} statements
                  </dd>
                </div>
                <div className="flex gap-2">
                  <dt className="text-ink-500">Sources archived</dt>
                  <dd className="text-ink-800">{srcs.length}</dd>
                </div>
                <div className="flex gap-2">
                  <dt className="text-ink-500">Website</dt>
                  <dd className="text-ink-800">
                    {p.url ? (
                      <a
                        className="text-accent underline underline-offset-2"
                        href={p.url}
                        rel="noopener noreferrer"
                        target="_blank"
                      >
                        {p.url.replace(/^https?:\/\//, "")}
                      </a>
                    ) : (
                      <span className="text-ink-500">not recorded yet</span>
                    )}
                  </dd>
                </div>
              </dl>
              <p className="mt-3 text-xs text-ink-500">{byTopic.join(" · ")}</p>
              {p.note ? <p className="mt-2 text-xs text-ink-500">Note: {p.note}</p> : null}
            </li>
          );
        })}
      </ul>

      <section className="rounded-lg border border-ink-200 bg-white p-4 text-sm text-ink-600 sm:p-5">
        <h2 className="text-base font-semibold text-ink-900">Parties not included</h2>
        <p className="mt-2">
          A minor party is added only when it nominates a full 93-candidate slate and publishes a
          platform we can code against. Until both are true we cannot give it the same treatment as
          the others, and unequal treatment is worse than omission.
        </p>
      </section>
    </div>
  );
}
