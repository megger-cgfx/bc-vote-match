"use client";

import { LIKERT_LABELS } from "@/lib/site";

const VALUES = [-2, -1, 0, 1, 2] as const;

/**
 * A five-point Likert control plus an explicit "Don't know / no opinion" option.
 * Implemented as a real radiogroup so keyboard and screen-reader users get standard
 * behaviour; the visual treatment is a row of pills on wide screens.
 */
export function Likert({
  questionId,
  value,
  onChange,
}: {
  questionId: string;
  value: number | null | undefined;
  onChange: (v: number | null) => void;
}) {
  const name = `answer-${questionId}`;
  return (
    <fieldset className="mt-3">
      <legend className="sr-only">Your position on this statement</legend>
      <div role="radiogroup" aria-label="Your position on this statement" className="flex flex-wrap gap-2">
        {VALUES.map((v, i) => {
          const id = `${name}-${i}`;
          const checked = value === v;
          return (
            <label
              key={v}
              htmlFor={id}
              className={`cursor-pointer rounded-full border px-3 py-2 text-sm transition-colors ${
                checked
                  ? "border-accent bg-accent text-white"
                  : "border-ink-300 bg-white text-ink-700 hover:border-accent hover:text-accent"
              }`}
            >
              <input
                id={id}
                className="sr-only"
                type="radio"
                name={name}
                value={v}
                checked={checked}
                onChange={() => onChange(v)}
              />
              <span aria-hidden="true" className="mr-1 font-mono text-xs opacity-70">
                {v > 0 ? `+${v}` : v}
              </span>
              {LIKERT_LABELS[i]}
            </label>
          );
        })}
        <label
          htmlFor={`${name}-dontknow`}
          className={`cursor-pointer rounded-full border px-3 py-2 text-sm transition-colors ${
            value === null
              ? "border-ink-600 bg-ink-600 text-white"
              : "border-dashed border-ink-300 bg-white text-ink-500 hover:border-ink-500 hover:text-ink-700"
          }`}
        >
          <input
            id={`${name}-dontknow`}
            className="sr-only"
            type="radio"
            name={name}
            value="dontknow"
            checked={value === null}
            onChange={() => onChange(null)}
          />
          Don&rsquo;t know
        </label>
      </div>
    </fieldset>
  );
}
