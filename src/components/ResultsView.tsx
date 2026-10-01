"use client";

import { useEffect, useMemo, useState } from "react";

import { AlignmentBars } from "./AlignmentBars";
import { Compass, type CompassMarker } from "./Compass";
import { ShareCard } from "./ShareCard";
import { loadAnswers, decodeAnswers, resultsUrl } from "@/lib/store";
import {
  answeredCount,
  alignAllParties,
  codingIndex,
  dimensionPositions,
  sanitiseAnswers,
  userDimensionPositions,
  MIN_PAIRS,
  type Answers,
} from "@/lib/scoring";
import type { Coding, Party, Question, SourceRecord } from "@/lib/schema";
import { TOPIC_LABELS } from "@/lib/schema";
import { LIKERT_LABELS, SITE } from "@/lib/site";

function codeLabel(v: number | null): string {
  if (v === null) return "no position";
  return `${v > 0 ? "+" : ""}${v}`;
}

export function ResultsView({
  parties,
  questions,
  codings,
  sources,
}: {
  parties: Party[];
  questions: Question[];
  codings: Coding[];
  sources: SourceRecord[];
}) {
  const [answers, setAnswers] = useState<Answers>({});
  const [hydrated, setHydrated] = useState(false);

  // A `?a=` payload in the URL wins (that is how a shared link carries a result);
  // otherwise fall back to the answers saved on this device. This has to run in the
  // browser — a static export has no server to read query strings at request time.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const fromUrl = decodeAnswers(params.get("a") ?? "");
    setAnswers(Object.keys(fromUrl).length > 0 ? fromUrl : loadAnswers());
    setHydrated(true);
  }, []);

  const clean = useMemo(() => sanitiseAnswers(answers, questions), [answers, questions]);
  const answered = answeredCount(clean);
  const byQuestion = useMemo(() => codingIndex(codings), [codings]);
  const sourceById = useMemo(() => new Map(sources.map((s) => [s.id, s])), [sources]);

  const alignments = useMemo(
    () => alignAllParties(clean, codings, questions, parties.map((p) => p.slug)),
    [clean, codings, questions, parties],
  );

  const markers = useMemo<CompassMarker[]>(() => {
    const user = userDimensionPositions(clean, questions);
    const out: CompassMarker[] = [];
    if (user.economic !== null && user.social !== null) {
      out.push({
        label: "You",
        color: "#14171c",
        economic: user.economic,
        social: user.social,
        isYou: true,
        sub: `${answered} answered`,
      });
    }
    for (const p of parties) {
      const pos = dimensionPositions(clean, codings, questions, p.slug);
      if (pos.economic === null || pos.social === null) continue;
      out.push({ label: p.short, color: p.color, economic: pos.economic, social: pos.social });
    }
    return out;
  }, [clean, codings, questions, parties, answered]);

  const bars = alignments.map((a) => {
    const party = parties.find((p) => p.slug === a.partySlug);
    return {
      label: party?.short ?? a.partySlug,
      color: party?.color ?? "#4d5461",
      value: (a.percent ?? 0) / 100,
      detail:
        a.percent === null
          ? `Only ${a.compared} comparable question${a.compared === 1 ? "" : "s"} — too few to score (minimum ${MIN_PAIRS}).`
          : `${a.compared} comparable questions · mean distance ${a.meanDistance?.toFixed(2)} on a 0–4 scale`,
    };
  });

  const url = hydrated ? resultsUrl(clean) : "/results/";
  const top = alignments.find((a) => a.percent !== null);
  const topParty = top ? parties.find((p) => p.slug === top.partySlug) : undefined;
  const summary =
    topParty && top
      ? `My closest match is ${topParty.name} at ${top.percent?.toFixed(1)}% on BC Vote Match.`
      : "See which BC party matches your views — BC Vote Match.";

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight text-ink-900 sm:text-3xl">Your results</h1>
        {answered === 0 ? (
          <>
            <p className="text-ink-700">
              No answers yet on this device. Answer the statements and your match will appear here.
            </p>
            <a
              href="/questions/"
              className="inline-block rounded bg-accent px-4 py-2.5 font-medium text-white hover:bg-ink-800"
            >
              Start the questionnaire
            </a>
          </>
        ) : (
          <p className="text-ink-700">
            Based on <strong className="font-semibold">{answered}</strong> of {questions.length}{" "}
            statements. Alignment is calculated in your browser from the published party codings — see{" "}
            <a className="text-accent underline underline-offset-2" href="/methodology/">
              how this is scored
            </a>{" "}
            and the{" "}
            <a className="text-accent underline underline-offset-2" href="/coding-table/">
              full coding table
            </a>
            .
          </p>
        )}
      </header>

      {answered > 0 ? (
        <>
          <section aria-labelledby="align-heading" className="space-y-3">
            <h2 id="align-heading" className="text-lg font-semibold text-ink-900">
              Alignment by party
            </h2>
            <AlignmentBars
              bars={bars}
              caption={`Alignment = 1 − (Σ|you − party| / (2·n)) over questions where both you and the party have a position (docs/SCHEMA.md).`}
            />
            <p className="text-xs text-ink-500">
              A high score means your answers sit near that party&rsquo;s published positions. It is
              not an endorsement, and it does not predict your vote.
            </p>
          </section>

          <section aria-labelledby="compass-heading" className="space-y-3">
            <h2 id="compass-heading" className="text-lg font-semibold text-ink-900">
              Two-dimensional compass
            </h2>
            {markers.length > 1 ? (
              <Compass markers={markers} />
            ) : (
              <p className="text-sm text-ink-600">
                Not enough answered statements to place positions on both axes yet.
              </p>
            )}
          </section>

          <section aria-labelledby="compare-heading" className="space-y-3">
            <h2 id="compare-heading" className="text-lg font-semibold text-ink-900">
              You vs each party, statement by statement
            </h2>
            <p className="text-sm text-ink-600">
              Every party code links to the quote it came from and the source it was fetched from.
            </p>
            <ul className="space-y-4">
              {questions.map((q) => {
                const mine = clean[q.id];
                return (
                  <li key={q.id} className="rounded-lg border border-ink-200 bg-white p-4">
                    <p className="text-sm font-medium text-ink-900">{q.statement}</p>
                    <p className="mt-1 text-xs text-ink-500">{TOPIC_LABELS[q.topic] ?? q.topic}</p>
                    <p className="mt-2 text-sm">
                      <span className="text-ink-500">You:</span>{" "}
                      <strong className="font-semibold text-ink-800">
                        {mine === undefined
                          ? "not answered"
                          : mine === null
                            ? "don’t know"
                            : LIKERT_LABELS[mine + 2]}
                      </strong>
                      {typeof mine === "number" ? (
                        <span className="ml-1 font-mono text-xs text-ink-500">({codeLabel(mine)})</span>
                      ) : null}
                    </p>
                    <ul className="mt-2 grid gap-1 sm:grid-cols-2">
                      {parties.map((p) => {
                        const c = byQuestion.get(`${p.slug}|${q.id}`);
                        const code = c?.code ?? null;
                        const src = c?.source_id ? sourceById.get(c.source_id) : undefined;
                        return (
                          <li key={p.slug} className="text-sm">
                            <span
                              aria-hidden="true"
                              className="mr-2 inline-block h-2.5 w-2.5 rounded-full align-middle"
                              style={{ backgroundColor: p.color }}
                            />
                            <span className="text-ink-700">{p.short}:</span>{" "}
                            <span className="font-mono text-xs text-ink-800">
                              {codeLabel(code)}
                            </span>
                            {c?.quote ? (
                              <>
                                {" — "}
                                <details className="mt-1 inline-block align-top">
                                  <summary className="cursor-pointer text-xs text-accent underline underline-offset-2">
                                    source
                                  </summary>
                                  <blockquote className="mt-1 border-l-2 border-ink-200 pl-2 text-xs text-ink-600">
                                    “{c.quote}”
                                  </blockquote>
                                  <p className="mt-1 text-xs text-ink-500">
                                    {c.source_url ? (
                                      <a
                                        className="text-accent underline underline-offset-2"
                                        href={c.source_url}
                                        rel="noopener noreferrer"
                                        target="_blank"
                                      >
                                        {c.source_id}
                                      </a>
                                    ) : (
                                      <span>{c.source_id}</span>
                                    )}
                                    {c.archive_url ? (
                                      <>
                                        {" · "}
                                        <a
                                          className="text-accent underline underline-offset-2"
                                          href={c.archive_url}
                                          rel="noopener noreferrer"
                                          target="_blank"
                                        >
                                          archived copy
                                        </a>
                                      </>
                                    ) : null}
                                    {src?.sha256 && src.sha256 !== "0".repeat(64) ? (
                                      <>
                                        {" · sha256 "}
                                        <span className="font-mono">{src.sha256.slice(0, 12)}…</span>
                                      </>
                                    ) : null}
                                    {" · coder "}
                                    {c.coder} ({c.version})
                                  </p>
                                </details>
                              </>
                            ) : (
                              <span className="text-xs text-ink-400"> — no published position</span>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </li>
                );
              })}
            </ul>
          </section>

          <ShareCard url={url} summary={summary} />

          <p className="rounded border border-ink-200 bg-white px-4 py-3 text-xs text-ink-600">
            {SITE.disclaimer} {SITE.independenceDisclaimer}
          </p>
        </>
      ) : null}
    </div>
  );
}
