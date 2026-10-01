import Link from "next/link";

import { getDataset } from "@/lib/data";
import { SITE } from "@/lib/site";

export default function HomePage() {
  const { parties, questions, counts } = getDataset();
  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <p className="text-xs font-medium uppercase tracking-wide text-ink-500">
          BC provincial election · {SITE.electionDay}
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-ink-900 sm:text-4xl">
          {SITE.tagline}
        </h1>
        <p className="max-w-2xl text-lg text-ink-700">
          Answer {counts.questions} statements on the issues that decide this election. We show you
          where your answers sit next to each party&rsquo;s published positions — with the quote,
          the source, and an archived copy behind every single one.
        </p>
        <div className="flex flex-wrap gap-3 pt-1">
          <Link
            href="/questions/"
            className="rounded bg-accent px-5 py-3 font-medium text-white hover:bg-ink-800"
          >
            Start the questionnaire
          </Link>
          <Link
            href="/methodology/"
            className="rounded border border-ink-300 px-5 py-3 font-medium text-ink-700 hover:border-ink-500"
          >
            How it works
          </Link>
        </div>
        <p className="text-sm text-ink-500">{SITE.slugLine}</p>
      </section>

      <section aria-labelledby="parties-heading" className="space-y-3">
        <h2 id="parties-heading" className="text-lg font-semibold text-ink-900">
          {counts.parties} parties included
        </h2>
        <ul className="grid gap-2 sm:grid-cols-2">
          {parties.map((p) => (
            <li
              key={p.slug}
              className="flex items-start gap-3 rounded-lg border border-ink-200 bg-white p-3"
            >
              <span
                aria-hidden="true"
                className="mt-1.5 inline-block h-3 w-3 shrink-0 rounded-full"
                style={{ backgroundColor: p.color }}
              />
              <div>
                <p className="font-medium text-ink-900">{p.name}</p>
                <p className="text-xs text-ink-500">
                  Leader: {p.leader} · {p.leader_status}
                </p>
              </div>
            </li>
          ))}
        </ul>
        <p className="text-xs text-ink-500">
          Minor parties are added by rule, not by invitation: a full 93-candidate slate and a
          published platform (see{" "}
          <Link className="text-accent underline underline-offset-2" href="/methodology/">
            method
          </Link>
          ).
        </p>
      </section>

      <section aria-labelledby="how-heading" className="space-y-3">
        <h2 id="how-heading" className="text-lg font-semibold text-ink-900">
          What you get
        </h2>
        <ul className="grid gap-3 sm:grid-cols-2">
          <li className="rounded-lg border border-ink-200 bg-white p-4">
            <h3 className="font-medium text-ink-900">Alignment by party</h3>
            <p className="mt-1 text-sm text-ink-600">
              A percentage per party, computed in your browser from codings that are published in full.
            </p>
          </li>
          <li className="rounded-lg border border-ink-200 bg-white p-4">
            <h3 className="font-medium text-ink-900">A two-dimensional compass</h3>
            <p className="mt-1 text-sm text-ink-600">
              Economic (left ↔ right) and social (progressive ↔ traditional), with the numbers printed
              alongside the chart.
            </p>
          </li>
          <li className="rounded-lg border border-ink-200 bg-white p-4">
            <h3 className="font-medium text-ink-900">Statement-by-statement detail</h3>
            <p className="mt-1 text-sm text-ink-600">
              Your answer and every party&rsquo;s coded answer, each with the quote and link it came
              from.
            </p>
          </li>
          <li className="rounded-lg border border-ink-200 bg-white p-4">
            <h3 className="font-medium text-ink-900">Nothing about you leaves your browser</h3>
            <p className="mt-1 text-sm text-ink-600">
              No accounts, no demographics, no third-party trackers, no analytics that identify you.
            </p>
          </li>
        </ul>
      </section>

      <section className="rounded-lg border border-ink-200 bg-white p-4 text-sm text-ink-700 sm:p-5">
        <p>{SITE.disclaimer}</p>
        <p className="mt-2">{SITE.independenceDisclaimer}</p>
        <p className="mt-2 text-xs text-ink-500">
          Dataset currently loaded: {counts.questions} statements ({counts.frozenQuestions} frozen) ·{" "}
          {counts.codings} codings · {counts.sources} archived sources.{" "}
          <Link className="text-accent underline underline-offset-2" href="/coding-table/">
            Inspect the full coding table
          </Link>
          .
        </p>
      </section>
    </div>
  );
}
