"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Likert } from "./Likert";
import { clearAnswers, loadAnswers, saveAnswers, encodeAnswers } from "@/lib/store";
import { answeredCount, type Answers } from "@/lib/scoring";
import type { Question } from "@/lib/schema";
import { TOPIC_LABELS } from "@/lib/schema";

/**
 * The questionnaire. Runs entirely in the browser: answers are written to
 * localStorage (and mirrored into the URL hash) and nothing is transmitted.
 */
export function QuestionFlow({ questions }: { questions: Question[] }) {
  const [answers, setAnswers] = useState<Answers>({});
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setAnswers(loadAnswers());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    saveAnswers(answers);
  }, [answers, hydrated]);

  const set = useCallback((id: string, v: number | null) => {
    setAnswers((prev) => ({ ...prev, [id]: v }));
  }, []);

  const answered = useMemo(() => answeredCount(answers), [answers]);
  const unanswered = questions.length - answered;
  const progress = questions.length ? Math.round((answered / questions.length) * 100) : 0;
  const encoded = useMemo(() => encodeAnswers(answers), [answers]);

  return (
    <div className="space-y-8">
      <div className="sticky top-0 z-10 -mx-4 border-b border-ink-200 bg-ink-50/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6">
        <div className="flex items-baseline justify-between gap-3 text-sm">
          <span className="text-ink-700">
            <strong className="font-semibold">{answered}</strong> of {questions.length} answered
            {unanswered > 0 ? <span className="text-ink-500"> · {unanswered} left</span> : null}
          </span>
          <a
            href={answered > 0 ? `/results/?a=${encodeURIComponent(encoded)}` : "/results/"}
            className={`rounded px-3 py-2 text-sm font-medium ${
              answered === 0
                ? "pointer-events-none bg-ink-200 text-ink-500"
                : "bg-accent text-white hover:bg-ink-800"
            }`}
            aria-disabled={answered === 0}
          >
            See my results
          </a>
        </div>
        <div
          className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-ink-200"
          role="progressbar"
          aria-valuenow={progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Questionnaire progress"
        >
          <div className="h-full rounded-full bg-accent transition-[width]" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <ol className="space-y-6">
        {questions.map((q, i) => (
          <li key={q.id} id={q.id} className="rounded-lg border border-ink-200 bg-white p-4 sm:p-5">
            <div className="flex items-start justify-between gap-4">
              <p className="text-base font-medium text-ink-900">
                <span className="mr-2 font-mono text-xs text-ink-400">{i + 1}/{questions.length}</span>
                {q.statement}
              </p>
              <span className="hidden shrink-0 rounded-full bg-ink-100 px-2 py-0.5 text-xs text-ink-600 sm:block">
                {TOPIC_LABELS[q.topic] ?? q.topic}
              </span>
            </div>
            <Likert questionId={q.id} value={answers[q.id]} onChange={(v) => set(q.id, v)} />
          </li>
        ))}
      </ol>

      <div className="flex flex-wrap items-center gap-3 border-t border-ink-200 pt-6">
        <a
          href={answered > 0 ? `/results/?a=${encodeURIComponent(encoded)}` : "/results/"}
          className="rounded bg-accent px-4 py-2.5 font-medium text-white hover:bg-ink-800"
        >
          See my results
        </a>
        <button
          type="button"
          className="rounded border border-ink-300 px-4 py-2.5 text-sm text-ink-700 hover:border-ink-500"
          onClick={() => {
            clearAnswers();
            setAnswers({});
          }}
        >
          Clear my answers
        </button>
        <p className="text-xs text-ink-500">
          Answers stay on this device. You can share your result with the link on the results page.
        </p>
      </div>
    </div>
  );
}
