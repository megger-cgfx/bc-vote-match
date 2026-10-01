# Core design tokens — M8 design system

`tokens.json` is the single source of truth for every colour, type step, space, radius,
border width, shadow, z-index and duration in BC Vote Match. Nothing else in the design
system may contain a raw hex or px value: stylesheets and component specs reference tokens
by name, and `build-tokens.py` turns the token file into CSS custom properties.

Version: 1.0.0 · Status: draft for human review · Owner: eagle (M8)

## Contents

- [Files](#files)
- [Neutrality constraint](#neutrality-constraint)
- [Naming convention](#naming-convention)
- [Token leaf shape](#token-leaf-shape)
- [Groups](#groups)
  - [color](#color)
  - [font](#font)
  - [typography](#typography)
  - [space](#space)
  - [radius](#radius)
  - [border](#border)
  - [shadow](#shadow)
  - [z](#z)
  - [motion](#motion)
- [Contrast policy](#contrast-policy)
- [How to consume this](#how-to-consume-this)
- [Relationship to the existing stylesheet](#relationship-to-the-existing-stylesheet)
- [Versioning](#versioning)
- [Open questions](#open-questions)

## Files

| File | Role |
| --- | --- |
| `tokens.json` | The deliverable. Machine-readable, versioned token set. |
| `README.md` | This taxonomy guide. |
| `build-tokens.py` | Generator: `tokens.json` → `tokens.css`. |
| `validate-tokens.py` | Checks the file parses, every colour documents contrast, every cross-reference resolves, and every quoted contrast ratio recomputes correctly. |
| `tokens.css` | **Generated.** Do not edit by hand; regenerate with `build-tokens.py`. |

Run both scripts before handing the token file to anyone:

    python3 validate-tokens.py     # 6 checks, all must print PASS
    python3 build-tokens.py        # rewrites tokens.css from tokens.json

## Neutrality constraint

The product earns credibility by being method-neutral
(`marketing/BRIEF-FOR-WORKERS.md`, `docs/content/NEUTRALITY-PROTOCOL.md`). The UI palette is
therefore greyscale plus one accent. Party colours are never page-level framing and appear
only as small swatches inside result views, taken from each party's own published branding.
No token in this file may be re-mapped to a party colour, and no new hue may be added to
`color.brand` without a neutrality review.

The palette is deliberately small: one accent (deep institutional blue), one secondary
(muted teal, for comparison baselines), a neutral ramp, and four semantic states. `semantic.info.base`
is intentionally the same value as `brand.primary` so the neutral UI does not grow a fourth hue.

## Naming convention

Dotted lower-kebab paths. Each dot is one level of nesting:

    color.brand.primary        a colour, in the brand group, named primary
    color.neutral.400          step 400 of the neutral ramp
    space.4                    the 4th step of the space scale (4 × the 4px base)
    border.width.focus         geometry: the focus ring width
    color.border.focus         colour: the focus ring colour
    motion.duration.base       a duration
    z.modal                    a stacking layer

Two namespaces that look similar and are not:

- `border.width.*` is **geometry**. `color.border.*` is **colour**.
- `font.size.*` is **font size**. `space.*` is **layout space**. They are independent scales.

Dark mode is not a separate naming scheme. The dark tree mirrors the light tree leaf for
leaf under the `color.dark.` prefix, so `color.surface.canvas` has its dark counterpart at
`color.dark.surface.canvas`. A token with no `color.dark.` counterpart keeps its light value.
That is what makes `build-tokens.py` a straight name remap.

## Token leaf shape

Every leaf is an object:

    {
      "value": <the value>,
      "type": "color" | "dimension" | "number" | "fontFamily" | "fontWeight" | "duration" | "cubicBezier" | "shadow",
      "intent": "where this token is used and why",
      "contrast": [ ... ]          // colour tokens only
    }

Extra fields:

- `contrast` — an array of `{against, ratio, level}`. `against` names the token this one is
  used with. For a foreground token it is the background; for a background token it is the
  text intended to sit on it. Ratios are computed, not estimated, and `validate-tokens.py`
  recomputes every one of them.
- `background` — for text tokens, an array of the surface tokens the text is designed for.
- `aliasOf` — this token intentionally mirrors another. The two must change together;
  `aliasOf` is a note to the consolidation pass, not a duplicate.
- `_note` — prose that applies to a whole group.

Units: dimensions are px strings (`"16px"`), line-height is unitless, letter-spacing is em,
durations are numbers of milliseconds. px (not rem) is canonical because the project's
stylesheet works in px and no root font-size has been declared. Changing that is a breaking
change to the whole scale and is listed under open questions.

## Groups

### color

Nine sub-groups, 70 colour tokens.

| Sub-group | Purpose |
| --- | --- |
| `color.brand` | The accent. Links, primary buttons, focus, selected states. Plus `secondary` for comparison baselines. |
| `color.neutral` | The 50–900 ramp. Values are identical to the existing `--color-ink-*` custom properties, so adopting these names changes nothing visually. |
| `color.text` | Nine text roles, each stating the background it targets. |
| `color.surface` | Page canvas, card, raised, sunken, tinted, and the modal scrim. |
| `color.border` | Boundary colours: subtle, default, strong, focus, danger. |
| `color.semantic` | `success / warning / danger / info`, each as `base` (solid fill, white text intended) and `soft` (tinted background, `color.text.primary` intended). |
| `color.dark` | Dark-mode counterparts of the above. |

Example — a link that passes AA:

    a { color: var(--color-text-link); text-decoration: underline; }
    a:hover { color: var(--color-text-link-hover); }

Example — a success banner:

    .banner--success {
      background: var(--color-semantic-success-soft);
      color: var(--color-text-primary);
      border-left: var(--border-width-thick) solid var(--color-semantic-success-base);
    }

Choosing a text colour: walk `color.text` from `primary` down to `subtle` and stop at the
first one the design allows. `subtle` is the floor — it is the lowest neutral that still
reaches AA. `disabled` is exempt from the ratio rule but must be paired with a non-colour
cue such as `aria-disabled`.

### font

Font families, weights and the seven-step type scale.

- `font.family.sans` / `font.family.mono` — system stacks only. The project bans external
  font origins, so no hosted webfont may be added; `Noto Sans` is the last fallback for
  scripts the system stack may not cover.
- `font.weight.regular / medium / semibold / bold`.
- `font.size.xs … 3xl` — each step carries its own `lineHeight`, `letterSpacing` and default
  `weight`, so a size is never chosen without its leading.

    h1 { font-size: var(--font-size-3xl); line-height: var(--line-height-3xl);
         letter-spacing: var(--letter-spacing-3xl); font-weight: var(--font-weight-bold); }

### typography

Composite text styles (display, heading-1/2, body-lg/body/body-sm, label, caption, code,
link). Each states its `fontFamily`, size, weight, line-height, letter-spacing, `color` and
the `background` it is intended for. Prefer a composite over assembling a size and a colour
by hand:

    .prose p { font: var(--font-size-md)/var(--line-height-md) var(--font-sans);
               color: var(--color-text-primary); background: var(--color-surface-canvas); }

Composites are documentation, not emitted variables; they name the tokens to combine.

### space

The base unit is 4px and the index is the multiplier: `space.<n>` is `n × 4px`, so `space.1`,
`space.4` and `space.6` are the first, fourth and sixth multiples of the base. Steps: 0, 1, 2,
3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32. There is no `space.7` and no `space.9` — if you need
one, the layout is probably wrong. Never write a literal padding, margin or gap.

    .card { padding: var(--space-6); display: flex; gap: var(--space-3); }

### radius

`none, xs (2), sm (4), md (6), lg (8), xl (12), 2xl (16), full (9999)`. Applied consistently:
controls use `sm`, containers use `lg`, pills and badges use `full`.

    .button { border-radius: var(--radius-sm); }
    .badge  { border-radius: var(--radius-full); }

### border

Two sub-groups. `border.width` is geometry: `none, thin (1), default (1, an alias of thin for
prose specs), thick (2), focus (3)`. `border.style` is `solid` (default) and `dashed` (drop
targets and unverified rows only). `border.focus-offset` is the focus ring's outline offset.
Colours are under `color.border`.

    .input { border: var(--border-width-default) solid var(--color-border-default); }
    .input:focus-visible { outline: var(--border-width-focus) solid var(--color-border-focus);
                           outline-offset: var(--border-focus-offset); }

The focus ring offset is itself a token (`border.focus-offset`), so no part of the ring is
hand-written.

### shadow

Five elevation levels. Each level maps to a specific stacking intent, never decoration:
0 = flush, 1 = card at rest, 2 = dropdown/popover/sticky header, 3 = modal/drawer,
4 = toast/command palette. Dark-mode variants are heavier, because a shadow on a dark
surface needs more opacity to read as raised. A `focus-ring` shadow is available for the
cases where an outline alone gets clipped.

    .card    { box-shadow: var(--shadow-elevation-1); }
    .popover { box-shadow: var(--shadow-elevation-2); }
    .modal   { box-shadow: var(--shadow-elevation-3);
               background: var(--color-surface-raised); }

### z

Named stacking layers: `base 0, content 1, sticky 100, dropdown 200, overlay 300, modal 400,
toast 500, tooltip 600, max 9999`. Use the constants only; a literal z-index is always a bug.

    .tooltip { z-index: var(--z-tooltip); }

### motion

- `motion.duration`: `instant 0, fast 100, base 200, slow 300, slower 500` (ms).
- `motion.easing`: `standard` for anything that both enters and leaves, `decelerate` for
  entrances, `accelerate` for exits, `linear` for progress bars and looping spinners only.
- `motion.reduced-motion`: under `prefers-reduced-motion: reduce` every duration collapses to
  `0.01ms` and looping animation stops. The generated stylesheet applies this override; it
  beats every duration token.

    .menu { transition: opacity var(--duration-base) var(--easing-standard),
                        transform var(--duration-base) var(--easing-decelerate); }

## Contrast policy

Baseline is WCAG 2.1 AA, computed with the standard sRGB relative-luminance formula and
verified by `validate-tokens.py`.

| Content | Minimum | Token guidance |
| --- | --- | --- |
| Body text | 4.5:1 | `color.text.primary` through `color.text.subtle`. |
| Large text (≥24px, or ≥18.66px bold) | 3:1 | `color.text.subtle` is safe; do not go below it. |
| Non-text UI boundary (focus ring, sole-affordance control border, icon that carries meaning) | 3:1 | `color.border.focus`, `color.border.strong`, or a `semantic.base`. |
| Decorative separator | no minimum | `color.border.subtle` and `color.border.default` are decorative. They are below 3:1: never let one be the only affordance of a control. |
| Disabled text | exempt | `color.text.disabled`. Still pair it with a non-colour cue. |

Every colour token carries its own `contrast` array with the computed ratio and level, so the
table above is a summary — the token file is authoritative. A ratio that is quoted anywhere
in the design system must match the token file; if the palette changes, rerun
`validate-tokens.py` and update the prose.

Two rules that fall out of the numbers:

- `color.border.subtle` and `color.border.default` do not reach 3:1. Use `color.border.strong`
  when the border is the only thing marking an interactive control.
- In dark mode, `color.dark.border.strong` also falls short of 3:1 against the dark canvas.
  Use `color.dark.border.focus` there.

## How to consume this

1. **Import the tokens.** Either take the generated stylesheet or re-generate it:

       python3 build-tokens.py tokens.json src/app/tokens.css

   `src/app/globals.css` then imports `tokens.css` and uses the `var()` names. Tailwind v4 can
   also consume the same file by mapping the variables into its `@theme` block, but the values
   must still come from `tokens.json` — not be retyped.

2. **Use a token in a component.** Reference the `var()` name, never a literal:

       .button--primary {
         background: var(--color-brand-primary);
         color: var(--color-text-on-accent);
         padding: var(--space-2) var(--space-4);
         border-radius: var(--radius-sm);
         box-shadow: none;
       }
       .button--primary:hover { background: var(--color-brand-primary-hover); }
       .button--primary:focus-visible {
         outline: var(--border-width-focus) solid var(--color-border-focus);
         outline-offset: var(--border-focus-offset);
       }

3. **Pull an asset.** Asset specs (`<task-id>`) and component specs (`<task-id>`) reference
   these token names; they must not restate a value. An icon that should inherit text colour
   uses `currentColor`; a duotone illustration names its two tokens, for example
   `color.brand.primary` and `color.brand.primary-soft`.

4. **Check your work.**

       python3 validate-tokens.py

## Relationship to the existing stylesheet

`src/app/globals.css` already declares an `ink` ramp, one accent, two warning colours and the
font stacks. Those values are carried into `tokens.json` unchanged where they exist:

| Existing custom property | Token |
| --- | --- |
| `--color-ink-50 … --color-ink-900` | `color.neutral.50 … color.neutral.900` |
| `--color-accent` | `color.brand.primary` |
| `--color-accent-soft` | `color.brand.primary-soft` |
| `--color-warn` | `color.semantic.warning.base` |
| `--color-warn-soft` | `color.semantic.warning.soft` |
| `--font-sans`, `--font-mono` | `font.family.sans`, `font.family.mono` |

Adopting the token names is therefore a rename, not a redesign. The stylesheet is the
marketing director's adjacent territory and this task does not edit it; the migration is
listed under open questions.

## Versioning

Semver. Adding a token is a minor bump; changing or removing an existing value is a major
bump and requires re-running `validate-tokens.py` plus a note in the M8 change log (the
consolidation task `<task-id>` owns that log). Bump `meta.version` and `meta.date` when the
file changes. Regenerate `tokens.css` in the same commit so the two never drift.

## Open questions

For the consolidation pass and the next milestone:

1. **px or rem.** The scale is px because no root font-size is declared. If the project adopts
   a rem root, the whole dimension set changes unit. Decide once, before components are built.
2. **Who owns breakpoints.** Not defined here. `<task-id>` (component specs) defines the
   breakpoint set; if it needs tokens, they should land in this file rather than in a component
   doc, to keep one source of truth.
3. **Migrating `globals.css`.** The rename above is mechanical but touches `src/`, which is
   outside this task's scope. Someone with a `src` mandate should schedule it.
4. **Dark mode trigger.** The generated stylesheet supports both `[data-theme="dark"]` and
   `prefers-color-scheme`. Whether the product ships a manual toggle is a product decision.
5. **Density.** Only one spacing rhythm (comfortable) is defined. A compact table density would
   need either a second space scale or a documented multiplier; not defined here.
