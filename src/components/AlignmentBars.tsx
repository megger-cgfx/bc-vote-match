export type Bar = {
  label: string;
  color: string;
  /** 0..1 */
  value: number;
  detail?: string;
};

/**
 * Horizontal alignment bars. Each bar is a labelled progress meter with the numeric
 * value printed as text, so the bar is redundant rather than load-bearing.
 */
export function AlignmentBars({ bars, caption }: { bars: Bar[]; caption?: string }) {
  return (
    <figure className="m-0">
      <ul className="space-y-3">
        {bars.map((b) => {
          const pct = Math.round(b.value * 100);
          return (
            <li key={b.label}>
              <div className="flex items-baseline justify-between gap-3">
                <span className="font-medium text-ink-800">
                  <span
                    aria-hidden="true"
                    className="mr-2 inline-block h-2.5 w-2.5 rounded-full align-middle"
                    style={{ backgroundColor: b.color }}
                  />
                  {b.label}
                </span>
                <span className="font-mono text-sm text-ink-700">{pct}%</span>
              </div>
              <div
                className="mt-1 h-2.5 w-full overflow-hidden rounded-full bg-ink-100"
                role="progressbar"
                aria-valuenow={pct}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${b.label} alignment ${pct} percent`}
              >
                <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: b.color }} />
              </div>
              {b.detail ? <p className="mt-1 text-xs text-ink-500">{b.detail}</p> : null}
            </li>
          );
        })}
      </ul>
      {caption ? <figcaption className="mt-3 text-xs text-ink-500">{caption}</figcaption> : null}
    </figure>
  );
}
