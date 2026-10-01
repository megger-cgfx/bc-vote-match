import type { Point } from "@/lib/scoring";

const SIZE = 420;
const PAD = 52;
const SPAN = SIZE - PAD * 2;

/** Map a −2…+2 value onto the SVG canvas for one axis. */
function project(v: number, invert: boolean): number {
  const t = (Math.max(-2, Math.min(2, v)) + 2) / 4; // 0..1
  return PAD + (invert ? 1 - t : t) * SPAN;
}

export type CompassMarker = Point & {
  label: string;
  color: string;
  sub?: string;
  isYou?: boolean;
};

/**
 * 2-D compass: x = economic (left ↔ right), y = social (progressive at top ↔
 * traditional at bottom). Decorative by itself, so the SVG is role="img" with a
 * summarizing label and the same numbers are printed in a table underneath — the
 * table is the accessible source of truth (WCAG 2.1 AA basics).
 */
export function Compass({ markers }: { markers: CompassMarker[] }) {
  return (
    <figure className="m-0">
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="mx-auto block h-auto w-full max-w-md"
        role="img"
        aria-label={
          "Two-dimensional compass plotting " +
          markers.map((m) => `${m.label} at economic ${m.economic.toFixed(2)}, social ${m.social.toFixed(2)}`).join("; ")
        }
      >
        <rect x={PAD} y={PAD} width={SPAN} height={SPAN} fill="#fff" stroke="var(--color-ink-200)" />
        <line x1={PAD + SPAN / 2} y1={PAD} x2={PAD + SPAN / 2} y2={PAD + SPAN} stroke="var(--color-ink-200)" />
        <line x1={PAD} y1={PAD + SPAN / 2} x2={PAD + SPAN} y2={PAD + SPAN / 2} stroke="var(--color-ink-200)" />

        <text x={PAD} y={PAD - 14} className="fill-ink-500" fontSize="12">
          Progressive
        </text>
        <text x={PAD} y={PAD + SPAN + 24} className="fill-ink-500" fontSize="12">
          Traditional
        </text>
        <text x={PAD - 8} y={PAD + SPAN + 12} textAnchor="start" className="fill-ink-500" fontSize="12">
          Left
        </text>
        <text x={PAD + SPAN + 8} y={PAD + SPAN + 12} textAnchor="end" className="fill-ink-500" fontSize="12">
          Right
        </text>
        <text
          x={PAD + SPAN}
          y={PAD + SPAN + 24}
          textAnchor="end"
          className="fill-ink-400"
          fontSize="11"
        >
          economic
        </text>
        <text x={PAD + SPAN / 2 + 6} y={PAD - 14} className="fill-ink-400" fontSize="11">
          social
        </text>

        {markers.map((m) => {
          const cx = project(m.economic, false);
          const cy = project(m.social, true);
          // Flip the label to the left of the marker near the right edge, or it runs off
          // the canvas (a +2/+2 voter sits exactly on the corner).
          const flip = cx > PAD + SPAN * 0.55;
          return (
            <g key={m.label}>
              <circle
                cx={cx}
                cy={cy}
                r={m.isYou ? 9 : 7}
                fill={m.color}
                stroke={m.isYou ? "var(--color-ink-900)" : "#fff"}
                strokeWidth={m.isYou ? 3 : 2}
              />
              <text
                x={flip ? cx - 13 : cx + 13}
                y={cy + 4}
                textAnchor={flip ? "end" : "start"}
                fontSize="12"
                className="fill-ink-700"
                stroke="#fff"
                strokeWidth="3"
                paintOrder="stroke"
              >
                {m.label}
                {m.isYou ? " (you)" : ""}
              </text>
            </g>
          );
        })}
      </svg>

      <figcaption className="sr-only">
        Party and user positions on the economic and social axes, values shown in the table below.
      </figcaption>

      <table className="mt-4 w-full border-collapse text-sm">
        <caption className="sr-only">Positions used to draw the compass above</caption>
        <thead>
          <tr className="border-b border-ink-200 text-left text-ink-600">
            <th scope="col" className="py-1 pr-3 font-medium">
              Position
            </th>
            <th scope="col" className="py-1 pr-3 font-medium">
              Economic (L↔R)
            </th>
            <th scope="col" className="py-1 font-medium">
              Social (prog↔trad)
            </th>
          </tr>
        </thead>
        <tbody>
          {markers.map((m) => (
            <tr key={`row-${m.label}`} className="border-b border-ink-100">
              <th scope="row" className="py-1 pr-3 text-left font-normal">
                <span
                  aria-hidden="true"
                  className="mr-2 inline-block h-2.5 w-2.5 rounded-full align-middle"
                  style={{ backgroundColor: m.color }}
                />
                {m.label}
                {m.isYou ? " (you)" : ""}
                {m.sub ? <span className="ml-2 text-xs text-ink-500">{m.sub}</span> : null}
              </th>
              <td className="py-1 pr-3 font-mono">
                {m.economic > 0 ? "+" : ""}
                {m.economic.toFixed(2)}
              </td>
              <td className="py-1 font-mono">
                {m.social > 0 ? "+" : ""}
                {m.social.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
