# M8 component library — specification

Component layer of the M8 design system for **BC Vote Match** (neutral, fully-sourced voter
alignment tool, BC 2026 provincial election).

- Version: **1.0.0**
- Status: **draft for human review**
- Owner: eagle (M8 design system)
- Task: `<task-id>` (component specs)
- Consumes: `tokens.json` v1.0.0 (`<task-id>`), read token names only — see the prerequisite note below.
- Feeds: `<task-id>` (consolidation pass).

> **Prerequisite / authority.** This document expresses every colour, space, radius, border
> width, shadow, z-index and duration **by token name**. It does not restate a raw hex or a
> raw px value. `tokens.json` is the single source of truth; where the two ever disagree, the
> token file wins and this file is wrong. Every token name used here is machine-checked
> against `tokens.json` — see `validate-components.py` and the token consumption matrix in
> section 12.

## Table of contents

1. [How to read this spec](#1-how-to-read-this-spec)
2. [Breakpoints and the responsive model](#2-breakpoints-and-the-responsive-model)
3. [Accessibility baseline](#3-accessibility-baseline)
4. [Composition rules](#4-composition-rules)
5. [Foundations quick reference](#5-foundations-quick-reference)
6. [Form controls](#6-form-controls)
   - [6.1 Field (label / help / error wrapper)](#61-field-label--help--error-wrapper)
   - [6.2 Input and Textarea](#62-input-and-textarea)
   - [6.3 Select](#63-select)
   - [6.4 Checkbox](#64-checkbox)
   - [6.5 Radio group and Likert](#65-radio-group-and-likert)
7. [Actions](#7-actions)
   - [7.1 Button](#71-button)
   - [7.2 Icon button](#72-icon-button)
8. [Containers and feedback](#8-containers-and-feedback)
   - [8.1 Card](#81-card)
   - [8.2 Modal / Dialog (and Drawer)](#82-modal--dialog-and-drawer)
   - [8.3 Tooltip](#83-tooltip)
   - [8.4 Toast](#84-toast)
   - [8.5 Banner / Alert](#85-banner--alert)
   - [8.6 Badge](#86-badge)
   - [8.7 Spinner / Progress](#87-spinner--progress)
9. [Navigation](#9-navigation)
   - [9.1 Top nav](#91-top-nav)
   - [9.2 Sidebar](#92-sidebar)
   - [9.3 Tabs](#93-tabs)
   - [9.4 Breadcrumb](#94-breadcrumb)
10. [Data display](#10-data-display)
    - [10.1 Table](#101-table)
    - [10.2 List](#102-list)
    - [10.3 Pagination](#103-pagination)
11. [Layout primitives](#11-layout-primitives)
    - [11.1 Container](#111-container)
    - [11.2 Stack](#112-stack)
    - [11.3 Grid](#113-grid)
12. [Token consumption matrix](#12-token-consumption-matrix)
13. [Keyboard interaction summary](#13-keyboard-interaction-summary)
14. [Open questions](#14-open-questions)

---

## 1. How to read this spec

Each component section is structured identically:

- **Anatomy** — the parts, in DOM order.
- **Variants** — named treatments.
- **Sizes** — the size scale and the token that drives each dimension.
- **States** — every state enumerated explicitly (`default`, `hover`, `active`, `focus`,
  `disabled`, `loading`, `error` where applicable). A state that is not listed does not exist.
- **Tokens** — the exact token names consumed. No literal values.
- **Accessibility** — role, ARIA, keyboard, focus, contrast minimum.
- **Content and overflow** — what happens when text or children exceed the box.

Two global rules apply to every component and are not repeated per section:

1. **Dark mode** is a name remap, not a second design. Every `color.*` token below has a
   counterpart at `color.dark.*` **if** it is listed in `tokens.json` under `color.dark`
   (26 of 44 light colour tokens are overridden). A colour with no dark counterpart inherits
   its light value. Implementations must consume the same token name and let the theme layer
   swap the value — never branch on a theme in component code.
2. **Reduced motion.** Under `motion.reduced-motion` every duration collapses. Components set
   transitions using the `motion.duration.*` and `motion.easing.*` tokens; the generated
   stylesheet's `prefers-reduced-motion` block does the rest. No component may hard-code a
   transition time.

Foundations referenced by name in this document but defined upstream: `color.brand.*`,
`color.neutral.*`, `color.text.*`, `color.surface.*`, `color.border.*`, `color.semantic.*`,
`font.*`, `typography.*`, `space.*`, `radius.*`, `border.width.*`, `border.style.*`,
`border.focus-offset`, `shadow.*`, `z.*`, `motion.*`.

---

## 2. Breakpoints and the responsive model

The token file deliberately left breakpoints to this task (open question 2 in the token
README). This section is the **authoritative definition**, but the values are *proposed
tokens*, not yet present in `tokens.json`, so they are marked ⚠. The consolidation pass
should promote them into `tokens.json` under a `breakpoint` group so the token file stays the
single source of truth. Until then they live here only.

Aligned to the Tailwind v4 defaults already in use in the codebase (`src/components/SiteHeader.tsx`
uses the `sm:` prefix, and `globals.css` imports `tailwindcss`), so the CSS layer needs no
custom config.

| Token (⚠ proposed) | Value | Range | Name | Primary use |
| --- | --- | --- | --- | --- |
| `breakpoint.xs` | `0px` | 0–639 | — | Mobile base; single-column everything. |
| `breakpoint.sm` | `640px` | 640–767 | Small | Dense 2-up grids, top nav goes horizontal. |
| `breakpoint.md` | `768px` | 768–1023 | Medium | Sidebar appears; 2-column layouts. |
| `breakpoint.lg` | `1024px` | 1024–1279 | Large | 3-column grids, wide tables. |
| `breakpoint.xl` | `1280px` | 1280–1535 | XL | Max content width reached. |
| `breakpoint.2xl` | `1536px` | ≥1536 | XXL | Whitespace grows; content width fixed. |

**Model.** Mobile-first (`min-width` media queries only). The base style is the `xs` (mobile)
layout; each breakpoint may add columns, reveal chrome, or widen the container. The product is
a responsive PWA (decision from `<task-id>`), so no breakpoint targets a native shell.

**Touch and pointer.** Assume touch at every breakpoint (a tablet at `lg` width is still a
touch device). Interactive hit targets are at least 44 × 44 CSS px regardless of viewport.
`hover` is treated as an enhancement: every hover-revealed affordance (tooltips, row actions)
must have a focus and a tap path.

**Responsive type.** Type steps do not change per breakpoint in this system — the scale is
fixed. Long-form `typography.body` may drop to `font.size.sm` only inside `lg`-and-up
multi-column text; that is the single documented exception.

---

## 3. Accessibility baseline

**Conformance target: WCAG 2.1 Level AA**, computed with the sRGB relative-luminance formula
(the same method `validate-tokens.py` uses), not estimated.

| Requirement | Rule | Tokens that satisfy it |
| --- | --- | --- |
| Body text contrast | ≥ 4.5:1 | `color.text.primary` (16.90 canvas / 17.96 default), `color.text.secondary`, `color.text.muted` (7.17), `color.text.subtle` (4.56 — the floor, never go below). |
| Large text (≥24px, or ≥18.66px bold) contrast | ≥ 3:1 | `color.text.subtle` and up. |
| Non-text UI boundary (focus ring, sole-affordance control border, meaningful icon) | ≥ 3:1 | `color.border.focus` (8.15/8.66), `color.border.strong` (3.09), `color.semantic.*.base`, `color.dark.border.focus`. |
| Decorative separator | no minimum | `color.border.subtle` (1.36) and `color.border.default` (1.91) are decorative. **Never** the sole boundary of an interactive control. |
| Disabled text | exempt | `color.text.disabled`, always paired with a non-colour cue (`aria-disabled`, `disabled`, a struck state). |
| Text on a solid accent/semantic fill | ≥ 4.5:1 | `color.text.on-accent` (AA against every `semantic.*.base` and AAA against `brand.primary`). |

**Focus-visible policy.**

- The focus ring is always drawn with `border.width.focus` (3px) `color.border.focus`, at
  `border.focus-offset` (2px), in `border.style.solid`. In dark mode the same token name
  (`color.border.focus`) remaps to the dark focus colour (ratio 10.48).
- `:focus-visible` only — pointer clicks must not paint the ring; keyboard and assistive
  navigation must. This matches the existing `globals.css` rule.
- The ring must not be clipped by an ancestor's `overflow: hidden`. Where it would be,
  substitute `shadow.focus-ring` (a 3px halo) **in addition to** the outline, never instead of
  it, unless the outline is genuinely invisible (then the halo alone must still reach 3:1).
- Any element made keyboard-focusable gets the ring; nothing focusable is left unstyled. Where
  an element is intentionally removed from tab order it uses `tabindex="-1"` + `aria-hidden`,
  not CSS `outline: none`.

**Reduced motion.** `motion.reduced-motion` (`prefers-reduced-motion: reduce`) collapses every
duration to `0.01ms` and stops looping animation (`spinner`, `progress`). Components reference
`motion.duration.*`, so the override is automatic. A `loading` state must still convey its
message without motion — pair the spinner with text ("Loading…") or `aria-busy`.

**Assistive-tech contract.**

- Every interactive control has an accessible name (visible label, `aria-label`, or
  `aria-labelledby`). Icon-only controls always carry a text alternative.
- Status changes that matter are announced: polite via `role="status"` (toasts, save
  confirmations), assertive via `role="alert"` (validation errors that block progress).
- No information is conveyed by colour alone: errors add an icon + text, links add an
  underline, selected nav adds `aria-current`, required fields add `aria-required` + a visible
  marker, not just a colour.
- Language: the document sets `lang="en-CA"` (BC product); switches to `lang="fr"` for
  French-language citations rendered in the results views.

---

## 4. Composition rules

How components nest, and the invariants that keep nesting legal.

**The lattice.**

```
Container                        page-width wrapper; the only element that centres content
└─ Stack                         vertical rhythm between blocks (gap = space.*)
   ├─ Card                       a surface; owns padding, radius, elevation
   │  ├─ Card.Header / .Body / .Footer
   │  ├─ Stack                   internal vertical rhythm
   │  │  ├─ Field → Input        a labelled control
   │  │  └─ Button               an action
   │  └─ Table                   data display inside a surface
   ├─ Grid                       rame of equal tracks; cells are Cards or Stacks
   └─ Banner                     full-width semantic message
```

**Rules.**

1. **One Container per page region.** `Container` sets max width and horizontal padding. It
   never nests inside itself; a `Grid` inside a `Container` is the normal pattern, a
   `Container` inside a `Container` is a bug.
2. **Space is owned by the parent.** A component does not set its own outer margin. The parent
   `Stack`/`Grid` supplies `gap` (`space.3`–`space.6`); a component sets only its internal
   padding. This is why no component token list below includes an outer margin token.
3. **Cards are surfaces, not layout.** A `Card` never contains another `Card` at the same
   elevation. Nesting a `Card` inside a `Card` is only legal one level deep and the inner
   card must be `color.surface.sunken` with `shadow.elevation-0`.
4. **Buttons nest inside Card.Body/Footer, Table.Toolbar, Modal.Footer, Toast.Actions.** A
   Button is never a direct child of a `Grid` track (it would stretch) — wrap it in a `Stack`
   with `align` set, or an explicit cluster.
5. **One primary Button per surface.** A Card, Modal, or page section has at most one
   `primary` Button; everything else is `secondary` or `ghost`. `danger` is reserved for a
   destructive confirm and never appears twice on one surface.
6. **Focus order follows DOM order.** Visual order must match DOM order at every breakpoint.
   Reordering with CSS `order`/`flex-direction` that breaks tab order is forbidden.
7. **Z-index is declared, not stacked.** Overlays take `z.modal` / `z.toast` / `z.tooltip`
   from the token set. A component never creates a new stacking context to "get on top".
8. **Elevation maps to intent.** `shadow.elevation-1` = card at rest, `-2` = dropdown/sticky,
   `-3` = modal/drawer, `-4` = toast. Two different elevations never express the same intent.

**Worked nesting example (the "compare two candidates" card).**

```
Container (max-width at breakpoint.xl)
└─ Stack (gap = space.6)
   ├─ heading (typography.heading-1)
   └─ Grid (2 columns ≥ breakpoint.md, gap = space.4)
      ├─ Card  [elevation-1, radius.lg, surface.default]
      │  ├─ Card.Body (padding space.6)
      │  │  ├─ Badge (party swatch + name)
      │  │  ├─ heading (typography.heading-2)
      │  │  └─ Stack (gap = space.3) → Body text
      │  └─ Card.Footer (padding space.4, border-top color.border.subtle)
      │     └─ Button[variant=secondary,size=md]
      └─ Card … (the second candidate)
```

---

## 5. Foundations quick reference

Only the subsets the component layer actually consumes. Full definitions in `tokens.json`.

- **Surface ramp:** `color.surface.canvas` (page) → `color.surface.default` (card) →
  `color.surface.raised` (popover/modal) → `color.surface.sunken` (inset). Tints:
  `color.surface.accent-soft`, `color.semantic.*.soft`.
- **Text roles:** `color.text.primary` > `secondary` > `muted` > `subtle` (floor) >
  `disabled` (exempt). Plus `color.text.on-accent`, `color.text.link`, `color.text.link-hover`.
- **Borders:** `color.border.subtle` / `.default` (decorative) / `.strong` (3:1) /
  `.focus` / `.danger`. Geometry in `border.width.*`.
- **Space scale:** `space.0,1,2,3,4,5,6,8,10,12,16,20,24,32` (index = ×4px).
- **Radius:** controls `radius.sm`; small surfaces `radius.md`; cards `radius.lg`; modals
  `radius.xl`; pills/avatars `radius.full`.
- **Elevation:** `shadow.elevation-0..4` + `shadow.focus-ring`.
- **Motion:** `motion.duration.instant/fast/base/slow/slower`,
  `motion.easing.standard/decelerate/accelerate/linear`.
- **Type:** `font.size.xs..3xl` each with `lineHeight`/`letterSpacing`; composites
  `typography.caption/label/body-sm/body/body-lg/heading-2/heading-1/display/code/link`.
- **Weights:** `font.weight.regular/medium/semibold/bold`.

---

## 6. Form controls

Shared expectations for all four controls below.

- **Name from a visible label.** Every control is wrapped by a `Field` (6.1). A placeholder is
  never the label.
- **Focus the control, ring the field.** The focus ring is drawn on the control's own border
  box via `:focus-visible`.
- **Error is a field-level state**, set by the `Field`, communicated through
  `aria-describedby` (help + error ids) and `aria-invalid` on the control.

### 6.1 Field (label / help / error wrapper)

**Anatomy**
1. `label` (always visible) — `typography.label`.
2. optional required marker — a text glyph + `aria-required` on the control, never colour alone.
3. the control (Input / Select / Checkbox / Radio group / Textarea).
4. optional help text — `typography.caption`.
5. optional error message — `typography.caption` in `color.semantic.danger.base`, prefixed by
   an error icon, with `role="alert"`.

**Layout** Control and label stack: `space.1` between every row (label→control, control→help,
control→error). Interactive rows inside the field use `space.2`.

**States** — `default` · `disabled` · `error` · `readonly` (Input/Textarea only).

**Tokens**

| Purpose | Token |
| --- | --- |
| Label type | `typography.label` (`font.size.sm`, `font.weight.medium`, `color.text.secondary`) |
| Help type | `typography.caption` (`font.size.xs`, `color.text.muted`) |
| Error text colour | `color.semantic.danger.base` |
| Gap between rows | `space.1` |
| Gap between controls in a group | `space.2` |

**Accessibility** `<label for>` is bound to the control id. Help id and error id are referenced
by the control's `aria-describedby` (help first, error second). Error container uses
`role="alert"`. `aria-invalid="true"` is set on the control only in the `error` state. Required
uses `aria-required="true"`.

**Content and overflow** Long help/error text wraps (no truncation); the label never truncates
— it wraps. If a label would exceed one line the field grows, it does not clip.

---

### 6.2 Input and Textarea

**Anatomy** Root box → (optional) leading icon → native `input`/`textarea` → (optional)
trailing slot (clear button, unit, character count).

**Variants** `text` · `email` · `password` · `search` · `tel` · `url` · `number` · `date` ·
`textarea` (multi-line). Variants change the input `type` and the trailing slot, not the frame.

**Sizes**

| Size | Padding-block | Padding-inline | Text token | Use |
| --- | --- | --- | --- | --- |
| `sm` | `space.2` | `space.3` | `typography.body-sm` | Dense tables/toolbars |
| `md` (default) | `space.3` | `space.4` | `typography.body` | Forms |
| `lg` | `space.4` | `space.5` | `typography.body` | Single-field hero forms |

Min-height is derived from padding + line-height; the interactive box must still reach 44px on
touch at every size (padding grows at `breakpoint.xs` for `sm`/`md`).

**States (explicit)**

| State | Border | Background | Text | Other |
| --- | --- | --- | --- | --- |
| `default` | `color.border.default` (decorative — never the sole affordance; pair with a visible label/box) | `color.surface.default` | `color.text.primary` | placeholder `color.text.subtle` |
| `hover` | `color.border.strong` | `color.surface.default` | `color.text.primary` | transition `motion.duration.fast` `motion.easing.standard` |
| `focus` (`:focus-visible`) | `color.border.focus` ring at `border.width.focus`, `border.focus-offset` | `color.surface.default` | `color.text.primary` | outline, not box-shadow, so it survives overflow |
| `active` | n/a | n/a | n/a | text inputs have no distinct active state beyond focus |
| `disabled` | `color.border.subtle` | `color.surface.sunken` | `color.text.disabled` | `disabled` + `aria-disabled`; cursor not-allowed |
| `readonly` | `color.border.subtle` | `color.surface.sunken` | `color.text.secondary` | `readonly`; still focusable and copyable |
| `error` | `color.border.danger` (2px would collide with focus, so keep `border.width.default` and rely on `aria-invalid` + message) | `color.surface.default` | `color.text.primary` | error message in Field; icon in trailing slot optional |

**Tokens**

| Purpose | Token |
| --- | --- |
| Rest border | `color.border.default`, `border.width.default`, `border.style.solid` |
| Hover border | `color.border.strong` |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Error border | `color.border.danger` |
| Disabled/readonly bg | `color.surface.sunken` |
| Field bg | `color.surface.default` |
| Text | `color.text.primary`; placeholder `color.text.subtle`; disabled `color.text.disabled` |
| Corner | `radius.sm` |
| Padding | `space.2`/`space.3`/`space.4` (block), `space.3`/`space.4`/`space.5` (inline) |
| Icon gap | `space.1` |
| Type | `typography.body` (md/lg), `typography.body-sm` (sm) |
| Motion | `motion.duration.fast`, `motion.easing.standard` |
| Char count | `typography.caption`, `color.text.muted` |

**Accessibility** Native `<input>`/`<textarea>` (never a div). `disabled` uses the `disabled`
attribute. `aria-invalid` and `aria-describedby` come from the Field. Visible label required;
`placeholder` is a hint only and must not restate the label. Password fields provide a
show/hide toggle (Icon button, `aria-pressed`). Search inputs get `role="searchbox"` via
`type="search"` and an accessible clear control with `aria-label`. Contrast: text ≥ 4.5:1
(`color.text.primary` = 16.90), placeholder ≥ 4.5:1 is *not* guaranteed by `color.text.subtle`
on its own pairings — treat placeholder as non-essential and never put required information in
it.

**Keyboard** Tab moves in/out (single stop). Native editing keys. In a `textarea`, Enter inserts
a newline and does not submit the form (form submit is an explicit Button or Ctrl/Cmd+Enter,
documented on the form).

**Content and overflow** Single-line: text scrolls horizontally within the box; no clipping of
the caret. `textarea`: fixed min-height (2 rows) and grows to a max, then scrolls vertically;
never grows unbounded. Trailing slot (clear/count) does not overlap typed text — it reserves
inline space via `space.6`. Long unbroken strings (URLs) wrap or scroll, never overflow the
field.

---

### 6.3 Select

Native-first. A custom listbox is only used where the native `<select>` cannot meet the design
(a searchable party/riding picker). Both are specified.

**Anatomy (native)** Root box → native `select` → trailing chevron icon (decorative,
`aria-hidden`).

**Anatomy (custom listbox)** trigger button (shows current value) → popover list
(`role="listbox"`) → options (`role="option"`), optional search field.

**Variants** `single` (default) · `multi` (checkbox-per-option; native uses
`<select multiple>`).

**Sizes** identical to Input (6.2): `sm`/`md`/`lg`.

**States (explicit)** — `default` · `hover` · `focus` · `open` (custom) · `disabled` ·
`error` · `placeholder` (no value chosen: text shown in `color.text.subtle`).

**Tokens**

| Purpose | Token |
| --- | --- |
| Frame, states | same set as Input (6.2): `color.border.default`/`.strong`/`.focus`/`.danger`, `border.width.*`, `border.focus-offset` |
| Background | `color.surface.default`; disabled `color.surface.sunken` |
| Text | `color.text.primary`; placeholder `color.text.subtle` |
| Chevron | `color.text.muted` (decorative icon) |
| Popover surface | `color.surface.raised`, `shadow.elevation-2`, `radius.md`, `z.dropdown` |
| Option hover/selected | `color.surface.accent-soft`; selected text `color.text.primary` |
| Option selected marker | `color.brand.primary` check icon (meaningful, ≥3:1) |
| Padding | `space.2`/`space.3` (block), `space.3`/`space.4` (inline); option rows `space.2` |
| Type | `typography.body` / `typography.body-sm` |
| Motion | `motion.duration.slow`, `motion.easing.decelerate` (open), `motion.easing.accelerate` (close) |

**Accessibility** Native `<select>` preferred: browser semantics, mobile pickers, and keyboard
all come free. Custom listbox must implement the WAI-ARIA listbox pattern: trigger
`role="combobox"` `aria-haspopup="listbox"` `aria-expanded`; the popover `role="listbox"`;
options `role="option"` `aria-selected`; the active option tracked with
`aria-activedescendant`. Selected value reflected in the trigger's accessible name. Chevron is
decorative. Contrast of the control boundary: `color.border.default` is decorative — the
visible label (Field) is the affordance, and the `focus`/`open` states use `color.border.focus`
(3:1+).

**Keyboard (native)** per platform.
**Keyboard (custom)** Enter/Space/Alt+Down open; Down/Up move the active option; Home/End jump;
type-ahead matches by prefix; Enter selects and closes; Esc closes without selecting and
returns focus to the trigger; Tab selects and moves on. Multi: Space toggles an option without
closing; the list stays open.

**Content and overflow** Long option labels wrap or truncate with the full value in the
accessible name and a `title`/tooltip fallback. The popover is max-height-capped (roughly 8
rows) and scrolls. When the popover would leave the viewport it flips above the trigger.

---

### 6.4 Checkbox

**Anatomy** Root label → box (`input[type=checkbox]`, visually custom) → check glyph → label
text → optional help.

**Variants** `single` (with label on the right) · `indeterminate` (a "some selected" state for
a parent controlling children — set via `input.indeterminate`, never a third colour).

**Sizes** `sm` (box `space.4`, `radius.xs`) · `md` (default; box `space.5`, `radius.xs`) ·
`lg` (box `space.6`). Tap target padded to 44px at every size.

**States (explicit)** — `default` (unchecked) · `checked` · `indeterminate` · `hover` ·
`focus` · `active` · `disabled` (unchecked) · `disabled checked` · `error` (e.g. a required
consent not ticked).

**Tokens**

| Purpose | Token |
| --- | --- |
| Box rest | `color.border.strong` (3:1 — the box is the sole affordance), `border.width.default`, `radius.xs`, `color.surface.default` |
| Box hover | `color.border.focus` |
| Box checked | `color.brand.primary` fill; glyph `color.text.on-accent` |
| Box indeterminate | `color.brand.primary` fill; dash glyph `color.text.on-accent` |
| Box error | `color.border.danger` |
| Box disabled | `color.surface.sunken` + `color.border.subtle`; glyph `color.text.disabled` |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Label | `typography.body`, `color.text.primary` |
| Help | `typography.caption`, `color.text.muted` |
| Gaps | `space.2` box→label; `space.1` label→help |
| Motion | `motion.duration.fast` (glyph fade/scale), `motion.easing.standard` |

**Accessibility** Native checkbox visually hidden but focusable (`.sr-only` pattern, or
`appearance: none` on the real box), with the real element owning the label via wrapping
`<label>`. `aria-invalid` + Field error for the error state. The check/dash glyph is
`aria-hidden`. Contrast: `color.brand.primary` fill vs `color.text.on-accent` glyph = 8.66:1;
box boundary `color.border.strong` = 3.09:1, meeting 1.4.11 for the unchecked box.

**Keyboard** Space toggles; the label click toggles; Tab moves in/out. In a group, Tab enters
the group's first item and each subsequent Tab leaves — arrow-key navigation is not used for a
plain checkbox group (only for the "checkbox menu" pattern, which we do not use).

**Content and overflow** Label wraps; a long label pushes help text down, never clips. Checkbox
never truncates its label.

---

### 6.5 Radio group and Likert

The product's primary input. The five-point Likert control (agree/disagree scale) plus
"Don't know / no opinion" is built on `role="radiogroup"`, matching the existing
`src/components/Likert.tsx`.

**Anatomy** `fieldset` → `legend` (may be visually hidden in dense layouts but present) →
`role="radiogroup"` → one label+radio per option. Each option is a pill on `width ≥
breakpoint.sm`; on `breakpoint.xs` the group wraps into rows.

**Variants** `radio` (standard dot) · `pill` (Likert: bordered pill, whole pill is the hit
target) · `card` (option rendered as a `Card` with a description; radio inside).

**Sizes** `md` (default), `sm` (dense tables). Pill padding `space.2`/`space.3` (sm) and
`space.3`/`space.4` (md).

**States (explicit)** — `default` (unselected) · `selected` · `hover` · `focus` ·
`active` · `disabled` · `error` (required group, nothing chosen).

**Tokens**

| Purpose | Token |
| --- | --- |
| Group legend | `typography.label` |
| Radio dot rest | `color.border.strong`, `border.width.default`, `color.surface.default` |
| Radio selected | `color.brand.primary` fill/dot |
| Pill rest | `color.surface.default`, `color.border.default`, `color.text.secondary` |
| Pill hover | `color.border.focus`, `color.text.link` |
| Pill selected | `color.brand.primary` fill, `color.text.on-accent` text |
| Pill "Don't know" | dashed `border.style.dashed`, `color.border.strong`, `color.text.muted`; selected → `color.neutral.600` fill, `color.text.on-accent` |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Disabled | `color.surface.sunken`, `color.text.disabled`, `color.border.subtle` |
| Corner (pill) | `radius.full` |
| Corner (card variant) | `radius.lg` |
| Padding | `space.2`/`space.3` (sm), `space.3`/`space.4` (md); group gap `space.2` |
| Motion | `motion.duration.fast`, `motion.easing.standard` |

**Accessibility** `fieldset`/`legend` names the group; `role="radiogroup"` with
`aria-labelledby` (or `aria-label`) reinforces it for AT. Radios share one `name`. The whole
pill is the label (`<label>` wrapping the input), so the tap target equals the visual target.
`aria-invalid` + `role="alert"` error on the group when required and unanswered. Numeric
prefix (`+2 … -2`) is `aria-hidden` decorative; the option's accessible name is the text label
("Strongly agree"). Contrast: unselected pill text `color.text.secondary` (10.43:1); selected
pill `color.text.on-accent` on `color.brand.primary` (8.66:1). Dashed border meets 3:1 via
`color.border.strong`.

**Keyboard** WAI-ARIA radiogroup: **Tab** enters the group at the selected radio (or the first
if none), and leaves the group in one stop. **Arrow keys** move to and select the next/previous
radio (wrapping). **Space** selects the focused radio. This is the standard and must be
preserved — a Likert must never require a separate Space to select after arrow-navigation.

**Content and overflow** Option labels wrap inside the pill up to two lines, then the pill grows
in height. On `breakpoint.xs` the pill row wraps; pills never shrink below their text width.
The Likert scale is never horizontally scrolled — it wraps.

---

## 7. Actions

### 7.1 Button

**Anatomy** Root `button` → optional leading icon → label text → optional trailing icon. Icons
inherit `currentColor`.

**Variants**

| Variant | Background | Text | Border | Use |
| --- | --- | --- | --- | --- |
| `primary` | `color.brand.primary` (hover `-hover`, active `-active`) | `color.text.on-accent` | none | The one main action on a surface |
| `secondary` | `color.surface.default` | `color.text.link` | `color.border.strong`, `border.width.default` | Secondary action |
| `ghost` | transparent | `color.text.link` (hover: `color.surface.accent-soft` bg) | none | Tertiary / in-text / toolbar actions |
| `danger` | `color.semantic.danger.base` (hover/active: **no token yet** — see note) | `color.text.on-accent` | none | Destructive confirm only |

> **Danger hover/active gap.** The token set defines `brand.primary-hover` and
> `brand.primary-active`, but there are **no** hover/active tokens for the semantic solids. So
> the `danger` Button has a documented rest state and no token-backed hover/active state. This
> is an open gap (open question 2), not a design decision: the interim is a declared
> `filter: brightness()` step that must be replaced by real tokens (`color.semantic.danger.hover`,
> `.active`) in a v1.1 minor bump. Flagged, not invented.

**Sizes**

| Size | Padding-block | Padding-inline | Type | Icon | Radius |
| --- | --- | --- | --- | --- | --- |
| `sm` | `space.1` | `space.3` | `typography.body-sm` + `font.weight.medium` | `space.4` box | `radius.sm` |
| `md` (default) | `space.2` | `space.4` | `typography.label` (`font.size.sm`/`medium`) | `space.5` box | `radius.sm` |
| `lg` | `space.3` | `space.5` | `typography.body` + `font.weight.medium` | `space.6` box | `radius.sm` |

Min-width: `sm` ≥ 64px, `md` ≥ 80px, `lg` ≥ 96px. Touch target ≥ 44px regardless of size.
`fullWidth` option stretches to the parent width (used in mobile Modal.Footer).

**States (explicit)** — `default` · `hover` · `active` (pressed) · `focus-visible` ·
`disabled` · `loading`. Error is not a Button state (a failed action is a Toast/Banner).

| State | Visual | Tokens |
| --- | --- | --- |
| `hover` | background steps down one level | `color.brand.primary-hover`; secondary: `color.surface.accent-soft`; ghost: `color.surface.accent-soft`; danger: see note |
| `active` | background steps down again | `color.brand.primary-active` |
| `focus-visible` | 3px ring at 2px offset | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| `disabled` | flat, non-interactive | primary: `color.neutral.200` fill + `color.text.disabled`; secondary/ghost: `color.text.disabled`; `disabled` attr + `aria-disabled` |
| `loading` | label replaced/shrouded by a spinner, width preserved | spinner in `currentColor`; `aria-busy="true"`; control stays `disabled` for pointer but keeps its accessible name |

**Tokens (all variants, consolidated)**

| Purpose | Token |
| --- | --- |
| Primary fill / hover / active | `color.brand.primary` / `.primary-hover` / `.primary-active` |
| Text on primary/danger | `color.text.on-accent` |
| Secondary text/link | `color.text.link` (`color.brand.primary`) |
| Secondary border | `color.border.strong`, `border.width.default`, `border.style.solid` |
| Ghost hover bg | `color.surface.accent-soft` |
| Danger fill | `color.semantic.danger.base` |
| Disabled | `color.neutral.200`, `color.text.disabled` |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset`, `shadow.focus-ring` (fallback only) |
| Corner | `radius.sm` |
| Padding | `space.1`–`space.3` (block), `space.3`–`space.5` (inline) |
| Icon↔label gap | `space.1` (sm) / `space.2` (md, lg) |
| Type | `typography.label` / `typography.body-sm` / `typography.body`, `font.weight.medium` |
| Motion | `motion.duration.fast`, `motion.easing.standard` |
| z (sticky version) | `z.sticky` |

**Accessibility** Native `<button>`. Type attribute explicit (`type="button"` unless it truly
submits). Accessible name = visible text; icon-only buttons are the Icon button (7.2). Loading:
`aria-busy="true"`, and while loading the accessible name is kept (spinner text is
`aria-hidden`); do not swap the name to "Loading" (it hides the action). `aria-disabled`
preferred over removing the element when the control should stay focusable to explain itself;
if truly inert, use `disabled`. Contrast: primary `color.text.on-accent` on
`color.brand.primary` = 8.66:1 (AAA); secondary text `color.text.link` on
`color.surface.default` = 8.66:1; danger `color.text.on-accent` on
`color.semantic.danger.base` = 6.54:1 (AA).

**Keyboard** **Enter** and **Space** activate (native). **Tab** moves in/out; buttons are one
stop. Enter on a focused button activates it (not the surrounding form) when wired to a
handler. In a toolbar, arrow-key navigation between buttons is the toolbar pattern and is owned
by the toolbar container, not the Button.

**Content and overflow** Label is single-line by default; if it wraps, the button grows in
height and its corner radius is unchanged. No truncation of a button label with an ellipsis in
the `md`/`lg` sizes; if space is tight the layout must reflow, not ellipsise the primary action.
Icons never overlap text; on very narrow widths a Button with a leading icon may drop the icon
(at `breakpoint.xs`) rather than shrink the target.

---

### 7.2 Icon button

**Anatomy** Root `button` (square/round) → icon (`currentColor`) → visually-hidden text label.

**Variants** same colour variants as Button; `shape = square` (`radius.sm`) or `circle`
(`radius.full`, used for close buttons and avatars).

**Sizes** `sm` (`space.6` box) · `md` (`space.8` box) · `lg` (`space.10` box), each padded to a
≥ 44px touch target at `breakpoint.xs`.

**States** identical to Button, plus `aria-pressed` for toggles (e.g. the password show/hide,
a grid/list view switch). Toggled-on uses `color.surface.accent-soft` bg + `color.text.link`.

**Tokens** as Button, plus: corner `radius.full` (circle) / `radius.sm` (square); icon colour
`color.text.muted` at rest, `color.text.link` on hover.

**Accessibility** **Every icon button has an accessible name** (`aria-label` or a visually
hidden `<span>`). Decorative-only icons are never buttons. Minimum 44px target. Toggle buttons
expose `aria-pressed`.

**Keyboard** Tab in/out; Enter/Space activate. In a toolbar, roving focus with arrows
(container-owned).

**Content and overflow** n/a (icon only); the icon scales within its box and never clips.

---

## 8. Containers and feedback

### 8.1 Card

**Anatomy** Root surface → optional `Card.Header` (title + actions) → `Card.Body` → optional
`Card.Footer` (actions, separated by `color.border.subtle`). A `Card` may be a link/button
(`interactive`) — then the whole surface is the target and the focus ring is drawn on the root.

**Variants** `default` (`color.surface.default`, `shadow.elevation-1`) · `flat`/`sunken`
(`color.surface.sunken`, `shadow.elevation-0`) · `raised` (`color.surface.raised`,
`shadow.elevation-2` — for a card that overlays) · `interactive` (adds hover elevation) ·
`outlined` (border `color.border.default`, no shadow).

**Sizes** padding `sm` = `space.4`, `md` (default) = `space.5`, `lg` = `space.6`. Footer
padding uses the same step. Media variant: `Card.Media` with `radius` inherited from the root
and inner corners squared.

**States (explicit)** — `default` · `hover` (interactive only: `shadow.elevation-2`,
`color.border.strong`) · `focus-visible` (interactive: ring on the root) · `active` (pressed) ·
`selected` (`color.surface.accent-soft` + `color.border.focus` 2px) · `disabled`
(`color.surface.sunken`, `color.text.disabled`).

**Tokens**

| Purpose | Token |
| --- | --- |
| Background | `color.surface.default` / `.raised` / `.sunken` |
| Border | `color.border.default` (outlined); dividers `color.border.subtle` |
| Selected bg/border | `color.surface.accent-soft`, `color.border.focus`, `border.width.thick` |
| Elevation | `shadow.elevation-1` (rest), `.elevation-2` (hover/raised) |
| Corner | `radius.lg` |
| Padding | `space.4`/`space.5`/`space.6` |
| Internal gaps | `space.3` (title→body), `space.4` (body→footer top border inset) |
| Title type | `typography.heading-2` |
| Body type | `typography.body` / `typography.body-sm` |
| Footer action gap | `space.2` |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Motion | `motion.duration.base`, `motion.easing.standard` |

**Accessibility** Non-interactive Card is a plain container (`<section>`/`<div>` with a
heading). Interactive Card is a real link/button: the root carries the role and the accessible
name (from the title via `aria-labelledby`), and there is exactly **one** focusable element per
interactive card — nested interactive children (a secondary Button in the footer) must be
outside the clickable root or the pattern becomes ambiguous. Selected Card uses
`aria-selected` (in a selectable list/group) or `aria-pressed` (a toggle). Contrast: default
card `color.text.primary` on `color.surface.default` = 17.96:1.

**Keyboard** Non-interactive: n/a. Interactive: Tab focuses the card root, Enter/Space activate.
A card containing its own buttons: those buttons are separate tab stops after the card root, and
the card root does **not** absorb their activation.

**Content and overflow** Body text wraps. Long titles wrap (max two lines then the card grows).
`Card.Media` images use `object-fit: cover` and a fixed aspect ratio per the asset spec
(`<task-id>`); overflow is clipped to `radius.lg`. A footer that runs out of room wraps its
buttons onto a second row rather than shrinking them.

---

### 8.2 Modal / Dialog (and Drawer)

**Anatomy** Portal → backdrop (`color.surface.overlay-scrim`, `z.overlay`) → dialog panel
(`z.modal`, `color.surface.raised`, `shadow.elevation-3`, `radius.xl`) → `Modal.Header`
(title + Icon-button close) → `Modal.Body` (scrollable) → `Modal.Footer` (actions; `primary`
last in DOM).

**Variants** `dialog` (centred, `max-width` capped) · `confirm` (compact, danger primary
allowed) · `drawer` (slides from the inline-end edge, full height, `radius.none` on the docked
edge) · `sheet` (bottom sheet at `breakpoint.xs`, becomes a centred dialog at `breakpoint.sm`).

**Sizes** `sm` (narrow confirm), `md` (default form dialog) · `lg` (content/detail) · `full`
(mobile sheet). Width caps are component constants (not tokens) and scale with the Container
(§11.1).

**States (explicit)** — `closed` · `opening` · `open` · `closing` · `loading` (body pending) ·
`error` (body failed; shows a Banner). Backdrop has `default` and `hover` (no-op) — the scrim is
not interactive except to dismiss where dismissible.

**Tokens**

| Purpose | Token |
| --- | --- |
| Backdrop | `color.surface.overlay-scrim` (light) / `color.dark.surface.overlay-scrim` (dark) |
| Panel bg | `color.surface.raised` |
| Elevation | `shadow.elevation-3` |
| Corner | `radius.xl` (dialog), `radius.none` (docked drawer edge) |
| Scrim layer | `z.overlay` |
| Panel layer | `z.modal` |
| Header/footer divider | `color.border.subtle`, `border.width.thin` |
| Title type | `typography.heading-1` |
| Body type | `typography.body` |
| Padding | `space.6` (header/body/footer), `space.4` (footer at `breakpoint.xs`) |
| Action gap | `space.2` |
| Close icon | `color.text.muted` → `color.text.link` on hover |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Motion (enter) | `motion.duration.slower`, `motion.easing.decelerate` |
| Motion (exit) | `motion.duration.base`, `motion.easing.accelerate` |

**Accessibility** `role="dialog"` (or `role="alertdialog"` for a destructive confirm) with
`aria-modal="true"` and `aria-labelledby` → title id (and `aria-describedby` → body summary
where useful). **Focus is trapped** within the panel while open; on open, focus moves to the
first meaningful element (the title's container or the first control — never the close button
unless that is the only choice); on close, focus returns to the element that opened it. The
backdrop is `aria-hidden`. Background content is inert (`inert` attribute / `aria-hidden` on the
app root). Body scrolling is locked. Contrast: `color.text.primary` on `color.surface.raised`
(light: 17.96:1) and `color.dark.text.primary` on `color.dark.surface.raised` (11.25:1).

**Keyboard** **Esc** closes (unless a destructive action is mid-flight). **Tab/Shift+Tab**
cycle within the panel (trap). **Enter** activates the focused control; a confirm's default
action is the focused button, never an implicit Enter on the whole dialog. Focus is restored on
close.

**Content and overflow** Body scrolls vertically when it exceeds the viewport (header/footer
stay pinned). Long titles wrap; the close button stays aligned to the top. At `breakpoint.xs`
the dialog becomes a full-width sheet; the footer stacks `fullWidth` buttons with `primary`
last. No horizontal scroll inside a dialog.

---

### 8.3 Tooltip

**Anatomy** Trigger (any focusable element) → popper (`role="tooltip"`, `color.surface.raised`
in dark / `color.neutral.900`-style dark bubble in light, `shadow.elevation-2`, `radius.md`,
`z.tooltip`) → short text (or, for the rich variant, a title + body).

**Variants** `plain` (one line of text) · `rich` (title + body + optional source line — used
for citation footnotes). Tooltips are **non-interactive**: no links or buttons inside.

**Sizes** one size; padding `space.2`/`space.3`; type `typography.caption` (plain) /
`typography.body-sm` (rich).

**States (explicit)** — `hidden` · `visible` · `disabled` (a trigger can opt out).

**Tokens**

| Purpose | Token |
| --- | --- |
| Bubble bg (dark-on-light) | `color.neutral.900` |
| Bubble text | `color.text.on-accent` (white on `neutral.900`) |
| Bubble border (dark mode) | `color.border.default` |
| Elevation | `shadow.elevation-2` |
| Corner | `radius.md` |
| Padding | `space.2` (block), `space.3` (inline) |
| Type | `typography.caption`, `typography.body-sm` |
| Layer | `z.tooltip` |
| Motion | `motion.duration.fast`, `motion.easing.decelerate` |

**Accessibility** `role="tooltip"`, referenced by the trigger's `aria-describedby`. Tooltips
supplement, never replace, a visible label — an icon-only button still needs its `aria-label`,
not a tooltip alone. Appears on **hover and focus**, dismissible with **Esc** (WCAG 2.1.1 /
1.4.13). Content contrast: white on `color.neutral.900` = 17.96:1. Content is not clipped and
does not disappear when the pointer moves onto it only to allow re-reading (it is non-interactive
so this is moot, but it must not block the trigger).

**Keyboard** Focus shows the tooltip; Esc hides it; blur hides it. No tooltip content is
focusable.

**Content and overflow** Max ~2 lines / a short paragraph. If it needs more, it is not a
tooltip — use a `Popover` or inline help text. Text wraps within a max-width cap; the popper
flips/clamps to stay in the viewport.

---

### 8.4 Toast

**Anatomy** Toast viewport (fixed, `z.toast`) → toast (`color.surface.raised`,
`shadow.elevation-4`, `radius.lg`) → status icon (`currentColor` of the variant) → message
(title + optional body) → optional actions (e.g. Undo, Retry) → optional close.

**Variants** `info` (icon `color.semantic.info.base`) · `success` (`color.semantic.success.base`)
· `warning` (`color.semantic.warning.base`) · `danger`/`error` (`color.semantic.danger.base`).

**Sizes** `md` default; `sm` for dense toolbars. Padding `space.3`/`space.4`.

**States (explicit)** — `entering` · `visible` · `exiting` · `paused` (hover/focus holds the
timer) · `dismissed`.

**Tokens**

| Purpose | Token |
| --- | --- |
| Surface | `color.surface.raised` |
| Elevation | `shadow.elevation-4` |
| Corner | `radius.lg` |
| Layer | `z.toast` |
| Status icon | `color.semantic.{info,success,warning,danger}.base` |
| Left accent bar (optional) | same `semantic.*.base`, `border.width.thick` |
| Title type | `typography.body` + `font.weight.medium` |
| Body type | `typography.body-sm`, `color.text.secondary` |
| Action link | `color.text.link` |
| Close icon | `color.text.muted` |
| Padding | `space.3` (block), `space.4` (inline) |
| Motion (enter) | `motion.duration.slow`, `motion.easing.decelerate` |
| Motion (exit) | `motion.duration.base`, `motion.easing.accelerate` |

**Accessibility** `role="status"` (polite) for info/success; `role="alert"` (assertive) for
error/danger. The viewport is a live region. Toasts are not the only channel for an important
message — a validation error is also inline in the Field. **Auto-dismiss:** info/success ~5s and
pausable on hover/focus; **error/warning do not auto-dismiss** (they require a close). Provide a
visible close and, where relevant, an "Undo" action. Contrast: text on
`color.surface.raised` uses the text tokens' own documented ratios (≥ 4.5:1).

**Keyboard** When an action is present, the toast must be reachable: focus the toast (or the
action) via a keyboard path — do not trap. Esc dismisses. After dismiss, focus returns to where
the action originated.

**Content and overflow** Message wraps to a max of ~3 lines then the toast grows; long content
truncates with the full text in the accessible name (and a "view details" path). Toasts stack
(viewport caps the count and scrolls or collapses). At `breakpoint.xs` the toast is full-width
and docked to the bottom.

---

### 8.5 Banner / Alert

**Anatomy** Root (`role` per variant) → status icon → content (title + body + optional inline
link/action). Used for the `FixtureBanner`-style informational strip and form-level errors.

**Variants** `info` · `success` · `warning` · `danger`. Each uses `semantic.*.soft` as the
background with a `semantic.*.base` left border and icon, and `color.text.primary` for the body.

**Sizes** one size; padding `space.3`/`space.4`.

**States** — `default` · `dismissible` (shows a close) · `with-action`.

**Tokens**

| Purpose | Token |
| --- | --- |
| Background | `color.semantic.{info,success,warning,danger}.soft` |
| Border/icon | `color.semantic.{…}.base`, `border.width.thick` (left) |
| Body text | `color.text.primary` (15.39–16.29:1 on the soft surfaces) |
| Corner | `radius.sm` |
| Padding | `space.3` (block), `space.4` (inline) |
| Icon↔text gap | `space.2` |
| Link | `color.text.link` + underline |
| Title type | `typography.body` + `font.weight.medium` |

**Accessibility** `role="status"` when it appears dynamically and is non-critical;
`role="alert"` for form-level or blocking errors. Icon `aria-hidden` (the text carries the
meaning). Contrast verified per soft pairing in `tokens.json`. Never colour-only: the icon and
the wording repeat the semantic.

**Keyboard / overflow** Dismissible banner's close is an Icon button (focusable, named). Body
text wraps; the banner grows in height. Inline links are underlined on focus/hover.

---

### 8.6 Badge

**Anatomy** Small pill → optional leading dot/icon → short text.

**Variants** `neutral` (metadata; `color.surface.sunken`, `color.text.secondary`) · `accent`
(`color.surface.accent-soft`, `color.text.link`) · `solid` (`color.brand.primary`,
`color.text.on-accent`) · semantic (`semantic.*.soft` + `semantic.*.base` text) · `party`
(neutral chrome + a `color` swatch taken from a party colour token — see note).

> **Party swatch note.** Per `<task-id>`, party logos are never reproduced; a party is shown
> as a small colour swatch plus its name. The asset spec names those swatches `color.party.*`,
> but **that group does not exist in `tokens.json` v1.0.0** — party colours are third-party
> branding, not UI tokens, and are supplied per party at render time. This is a known
> cross-document gap for the consolidation pass (`<task-id>`): either a `color.party.*` group
> is added to the token file (with a neutrality review) or the asset spec's naming is corrected.
> The Badge chrome itself uses only the tokens above; the swatch value is data, never a
> page-level design token.

**Sizes** `sm` (default), `md`. Padding `space.1`/`space.2`; corner `radius.full`; type
`typography.caption`.

**States** — `default` only (a Badge is not interactive). A **removable** variant (with a
close) is an Icon button inside the pill and follows Icon-button states.

**Tokens** `color.surface.sunken`, `color.surface.accent-soft`, `color.brand.primary`,
`color.text.on-accent`, `color.text.secondary`, `color.text.link`,
`color.semantic.*.soft`/`.base`, `radius.full`, `space.1`, `space.2`, `typography.caption`.

**Accessibility** Text is real text (never an image of text). A status badge that repeats the
same information as adjacent text is `aria-hidden` to avoid double-reading; a standalone
status badge is readable normally. Contrast: `solid` = 8.66:1; `neutral` text
`color.text.secondary` on `color.surface.sunken` ≥ 4.5:1; semantic-soft pairings verified in
`tokens.json`.

**Overflow** Single line; the badge never wraps. Long labels are not truncated silently — the
`max-width` is capped and the full text is in the accessible name / `title`.

---

### 8.7 Spinner / Progress

**Anatomy** `spinner` (rotating ring, `currentColor`) · `progress` (track + fill; determinate)
· `progress` (indeterminate bar).

**Variants** `spinner` · `bar` (determinate) · `bar-indeterminate`.

**Sizes** `sm`/`md`/`lg` mapped to `space.4`/`space.5`/`space.6`.

**States** — `determinate` (value known) · `indeterminate` (value unknown) · `complete`.

**Tokens** track `color.surface.sunken`; fill/ring `color.brand.primary`; success completion
`color.semantic.success.base`; corner `radius.full`; type (with-label) `typography.caption`,
`color.text.muted`; motion `motion.duration.slower` with `motion.easing.linear` (the only
sanctioned use of `linear`).

**Accessibility** `role="progressbar"` with `aria-valuemin/max/now` when determinate, no
`aria-valuenow` when indeterminate. A spinner is decorative when a visible "Loading…" exists;
otherwise it carries `role="status"` and an accessible name. Under
`motion.reduced-motion` looping stops — the state is then conveyed by text alone. Contrast: the
ring/fill `color.brand.primary` against the surface ≥ 3:1.

**Overflow** n/a; fixed size, never clipped.

---

## 9. Navigation

### 9.1 Top nav

**Anatomy** `header` (`color.surface.default`, bottom border `color.border.subtle`) → brand link
→ primary `nav` (`aria-label="Main"`) with a `ul` of links → optional utility slot (search,
theme toggle) → at `breakpoint.xs` a menu toggle (Icon button, `aria-expanded`,
`aria-controls`).

**Variants** `horizontal` (default) · `centred` (brand centred) · `with-secondary` (a second
row for section sub-nav).

**Sizes** height uses `space.10` (compact) or `space.12` (default); padding-inline `space.4`
(`breakpoint.xs`) → `space.6` (`breakpoint.sm`+).

**States** — link `default` · `hover` · `focus-visible` · `current` (`aria-current="page"`,
`color.text.link` + 2px `color.border.focus` underline) · `disabled` (rare).

**Tokens**

| Purpose | Token |
| --- | --- |
| Bar bg | `color.surface.default` |
| Bottom border | `color.border.subtle`, `border.width.thin` |
| Link rest | `color.text.secondary` (or `color.text.link` in the current stylesheet's header) |
| Link hover | `color.text.link`, `color.text.link-hover` |
| Link current | `color.text.link` + `border.width.thick` `color.border.focus` underline |
| Brand text | `typography.body` + `font.weight.semibold`; `color.text.primary` |
| Nav gap | `space.4` (`breakpoint.sm`+), `space.2` (stacked at `breakpoint.xs`) |
| Sticky layer | `z.sticky`, `shadow.elevation-2` when scrolled |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Mobile menu | `color.surface.raised`, `shadow.elevation-2`, `z.dropdown` |

**Accessibility** `<nav aria-label="Main">`; the brand link is first and returns home. Current
page marked with `aria-current="page"` (and the underline, not colour alone). Mobile menu
toggle is an Icon button with `aria-expanded`/`aria-controls`; when the menu opens, focus moves
into it and Esc/Space closes and returns focus. Links are underlined on hover and always on
focus for meaning. Contrast: link text `color.text.link` on `color.surface.default` = 8.66:1.

**Keyboard** Tab through brand → nav links → utility → (mobile) toggle. **Enter** activates.
Inside the mobile menu, arrows move between items; Esc closes. No keyboard traps.

**Content and overflow** Too many items: at `breakpoint.sm`+ a subset is promoted and the rest
move into an overflow "More" menu (a `dropdown`, `z.dropdown`); never shrink below readable
size. On `breakpoint.xs` the whole nav collapses behind the toggle. Long labels wrap in the
mobile menu; the horizontal bar never scrolls sideways without an explicit affordance.

---

### 9.2 Sidebar

**Anatomy** `aside` (`color.surface.default` or `.canvas`) → optional section label →
`nav` with grouped `ul` links → optional collapse toggle. `sticky`/fixed, `z.sticky`.

**Variants** `expanded` (labels + optional icons) · `collapsed` (icons only, labels as
tooltips) · `overlay` (drawn over content at `breakpoint.xs`/`sm`, with the modal scrim).

**Sizes** width in the `space.32`–`space.40` range as component constants; collapsed =
`space.12`. Item height `space.8`; padding-inline `space.3`.

**States** — link `default` · `hover` · `focus-visible` · `current` (`aria-current`,
`color.surface.accent-soft` bg + `color.text.link`, 2px `color.border.focus` inline-start
bar) · `disabled`; sidebar `expanded`/`collapsed`.

**Tokens**

| Purpose | Token |
| --- | --- |
| Surface | `color.surface.default` / `color.surface.canvas` |
| Divider | `color.border.subtle` |
| Item rest text | `color.text.secondary` |
| Item hover bg | `color.surface.sunken` |
| Item current bg/text/bar | `color.surface.accent-soft`, `color.text.link`, `color.border.focus` |
| Item gap | `space.1`; group gap `space.4` |
| Radius | `radius.sm` (items), root none |
| Sticky layer | `z.sticky` (or `z.overlay` when in overlay mode) |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |

**Accessibility** `<nav aria-label="Section">`; `aria-current="page"` on the current item;
collapse toggle is an Icon button with `aria-expanded`. In `collapsed` mode each item keeps its
accessible name (visually-hidden text) — it is not an unlabelled icon. In `overlay` mode the
sidebar follows the dialog focus-trap contract. Contrast: item text `color.text.secondary`
(10.43:1); current text `color.text.link`.

**Keyboard** Tab through items; Enter activates. Collapse toggle via Enter/Space. In overlay
mode, Esc closes and restores focus.

**Content and overflow** The list scrolls independently; the section header may stick. Long
labels wrap or ellipsise with the full name in the accessible name. Nested groups use an
indent of `space.4` and an expandable disclosure (`aria-expanded`).

---

### 9.3 Tabs

**Anatomy** `div[role=tablist]` → `button[role=tab]` (selected one `tabindex="0"`, others
`-1`) → `div[role=tabpanel]` (`aria-labelledby` the tab, `tabindex="0"` when it holds no
focusable content).

**Variants** `underline` (default, in-page content switch) · `pill` (segmented control; used
for result-view switches) · `enclosed` (card-like tabs).

**Sizes** `sm`/`md`. Padding `space.2`/`space.3` (sm) and `space.3`/`space.4` (md); gap
`space.1`.

**States** — tab `default` · `hover` · `focus-visible` · `selected` (`aria-selected="true"`,
`color.text.link` + `border.width.thick` `color.border.focus` underline in the underline
variant; `color.brand.primary` fill in the pill variant) · `disabled` · `with-badge`.

**Tokens**

| Purpose | Token |
| --- | --- |
| Rest text | `color.text.secondary` |
| Hover text/bg | `color.text.link`; pill hover bg `color.surface.sunken` |
| Selected | underline `color.border.focus` + `border.width.thick`; pill fill `color.brand.primary` + `color.text.on-accent` |
| Panel | `color.surface.default`, `space.4` padding |
| Tablist divider | `color.border.subtle` |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Motion (indicator) | `motion.duration.base`, `motion.easing.standard` |

**Accessibility** Full WAI-ARIA tabs pattern: `role="tablist"/"tab"/"tabpanel"`;
`aria-selected`; `aria-controls` → panel id; panel `aria-labelledby` → tab id. **Roving
tabindex**: only the selected tab is in the tab order.

**Keyboard** **Tab** enters the tablist at the selected tab and, after one more Tab, moves into
the panel. **Left/Right arrows** move between tabs (wrapping); **Home/End** jump to first/last;
**Enter/Space** activate (or arrow-activation, chosen consistently across the app). Activating a
tab moves focus into the panel only if the panel is empty of focusable content.

**Content and overflow** Overflowing tab rows scroll horizontally with the selected tab
scrolled into view; on `breakpoint.xs` tabs may become a Select. Panels size to content; no
fixed heights.

---

### 9.4 Breadcrumb

**Anatomy** `nav[aria-label="Breadcrumb"]` → `ol` → `li` (link `separator` link `separator`
current). Separator is a decorative glyph (`aria-hidden`).

**Variants** `full` · `truncated` (middle items collapsed into a "…" menu at `breakpoint.xs`).

**Sizes** one size; type `typography.body-sm` (≈14px — meets AA at 4.5:1 via
`color.text.secondary`); gap `space.2`.

**States** — link `default` · `hover` (`color.text.link-hover`, underline) · `focus-visible` ·
`current` (not a link: text `color.text.muted`, `aria-current="page"`).

**Tokens** `color.text.secondary` (links), `color.text.link`/`color.text.link-hover` (hover),
`color.text.muted` (current), separator `color.text.subtle`, `space.2` gap,
`typography.body-sm`, focus ring tokens.

**Accessibility** `<nav aria-label="Breadcrumb">` + ordered list (order is meaning). Current
item uses `aria-current="page"`. Separators are `aria-hidden`. Contrast: link text
`color.text.secondary` = 10.43:1; current `color.text.muted` = 7.17:1.

**Keyboard** Tab through the links in order; Enter activates. The "…" overflow is a menu
(arrow keys, Esc) that is a single tab stop.

**Content and overflow** Long trails truncate the middle at `breakpoint.xs` (keep first and
last), exposing the hidden items via the "…" menu. Items never wrap to a second line — the bar
is single-line and truncates.

---

## 10. Data display

### 10.1 Table

**Anatomy** Optional toolbar (title + search + density toggle) → scroll wrapper → `table` →
`caption` (visually hidden if a heading already names it) → `thead` (`th scope="col"`) →
`tbody` (`td`) → optional `tfoot` → empty state.

**Variants** `default` (bordered rows) · `zebra` (`color.surface.sunken` alternate rows) ·
`compact` (dense; the density question the token README flagged) · `card` (each row rendered as
a Card on `breakpoint.xs`). Sortable columns, a selectable variant (`checkbox` per row + a
select-all header checkbox), and an expandable-row variant.

**Sizes** `md` default; row padding-block `space.2` (dense) / `space.3` (default); cell
padding-inline `space.3`. Header type `typography.label`; body `typography.body`; numeric cells
`typography.code` (mono, aligned right).

**States** — row `default` · `hover` (`color.surface.sunken`) · `selected`
(`color.surface.accent-soft`) · `focus-visible` · `disabled`; header `sortable` / `sorted-asc`
/ `sorted-desc`; table `loading` (skeleton rows) · `empty`.

**Tokens**

| Purpose | Token |
| --- | --- |
| Surface | `color.surface.default` |
| Header bg | `color.surface.sunken` |
| Row divider | `color.border.subtle`, `border.width.thin` |
| Zebra / row hover | `color.surface.sunken` |
| Selected row | `color.surface.accent-soft` |
| Strong cell boundary (uses `color.border.strong` where a boundary must be sole affordance) | `color.border.strong` |
| Header text | `typography.label`, `color.text.secondary` |
| Body text | `typography.body`, `color.text.primary` |
| Numeric/mono | `typography.code` |
| Sort indicator | `color.text.muted` (decorative) + `aria-sort` on the `th` |
| Empty state | `color.text.muted`, `typography.body`, `space.10` padding |
| Loading skeleton | `color.surface.sunken` shimmer (motion `motion.duration.slower`, `motion.easing.linear`) |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Radius | `radius.none` on cells; `radius.lg` on the container in `card` variant |

**Accessibility** Real `<table>` with `<th scope="col">`/`"row"`, a `<caption>` (visually
hidden when a heading names it). Sortable headers are buttons inside `th` with `aria-sort`
(`ascending`/`descending`/`none`) on the `th`. The row-selection checkbox has an accessible name
including the row's identifier. The scroll wrapper is keyboard-scrollable
(`tabindex="0"` + `role="region"` + `aria-label`) when the table overflows horizontally.
Contrast: header `color.text.secondary` on `color.surface.sunken` ≥ 4.5:1; numerals pass via
`color.text.primary`.

**Keyboard** Tab reaches: toolbar controls → (if scrollable) the scroll region → row checkboxes
→ any in-cell links/buttons. Sort header via Enter/Space. Row actions are real buttons, not a
hover-only affordance. No `onmouseover`-only interactions.

**Content and overflow** Cells truncate with the full value in the accessible name/`title`, or
wrap in long-text columns (configurable per column). Horizontal overflow is contained by the
scroll wrapper and never pushes the page wide. At `breakpoint.xs` the `card` variant is the
default. Empty state replaces `tbody` with a message + optional primary action.

---

### 10.2 List

**Anatomy** `ul`/`ol` → `li` (optional leading icon/avatar, primary text, secondary text,
trailing meta/action) → optional list header (group label) → optional empty state.

**Variants** `plain` · `divided` (`color.border.subtle` separators) · `interactive` (each row a
link/button) · `selectable` (`role="listbox"` + `option`, single/multi) · `compact`.

**Sizes** row padding `space.2`/`space.3`; gap `space.1`; type `typography.body` (primary) +
`typography.body-sm` (secondary).

**States** — row `default` · `hover` (`color.surface.sunken`) · `selected`
(`color.surface.accent-soft`) · `focus-visible` · `disabled`; list `loading`/`empty`.

**Tokens** `color.surface.default`, `color.surface.sunken`, `color.surface.accent-soft`,
`color.border.subtle`, `color.text.primary`, `color.text.secondary`, `space.1`–`space.3`,
`radius.sm`, focus ring tokens, `typography.body`/`typography.body-sm`.

**Accessibility** A plain list is a list (no ARIA roles). An `interactive` list is a set of
links/buttons. A `selectable` list uses `role="listbox"` with `aria-multiselectable` and
`role="option"` + `aria-selected`, roving focus. Contrast per text token.

**Keyboard** Plain: Tab to any interactive children. Selectable: Tab enters/exits the list;
**Up/Down** move; **Home/End** jump; **Space** toggles (multi); **Enter** activates the row's
primary action.

**Content and overflow** Long primary text truncates with the full text in the accessible name;
secondary text wraps to one extra line then truncates. Trailing actions are real buttons, wrap
below at `breakpoint.xs`.

---

### 10.3 Pagination

**Anatomy** `nav[aria-label="Pagination"]` → `ul` of page controls → optional "prev"/"next"
Icon buttons → optional "results X–Y of N" text → optional page-size Select.

**Variants** `pages` (numbered with ellipsis windowing) · `prev-next` (mobile/simple) ·
`load-more` (button) · `infinite` (deferred — see open questions).

**Sizes** one size; control padding `space.2`/`space.3`; type `typography.body-sm`; gap
`space.1`.

**States** — page `default` · `hover` · `focus-visible` · `current`
(`aria-current="page"`, `color.surface.accent-soft` bg + `color.text.link`, 1px
`color.border.focus`) · `disabled` (prev on first page, next on last).

**Tokens**

| Purpose | Token |
| --- | --- |
| Control rest | `color.surface.default`, `color.border.default`, `color.text.secondary` |
| Hover | `color.surface.sunken`; text `color.text.link` |
| Current | `color.surface.accent-soft`, `color.text.link`, `color.border.focus` |
| Disabled | `color.text.disabled`, `color.surface.sunken` |
| Ellipsis | `color.text.subtle` |
| Radius | `radius.sm` |
| Gap | `space.1` |
| Focus ring | `color.border.focus`, `border.width.focus`, `border.focus-offset` |
| Type | `typography.body-sm` |

**Accessibility** `<nav aria-label="Pagination">`. Current page uses `aria-current="page"`.
Prev/Next are Icon buttons with names ("Previous page"/"Next page"); disabled state uses the
`disabled` attribute. The "results X–Y of N" text is a polite live region so a page change is
announced.

**Keyboard** Tab through prev → pages → next; Enter/Space activate. Ellipsis is not focusable.

**Content and overflow** Windowing shows first, last, current ±1 and ellipses for the rest. On
`breakpoint.xs` the numbered buttons collapse to `prev-next` + a page indicator. The list never
wraps mid-control.

---

## 11. Layout primitives

### 11.1 Container

**Anatomy** A single `div` that caps content width and sets horizontal padding. No visual
affordance of its own.

**Variants** `default` (content) · `narrow` (prose; ≈ `breakpoint.md`) · `wide` (tables/dashboards;
≈ `breakpoint.xl`) · `full` (no max-width; padding only).

**Sizes** max-width steps (component constants that track the breakpoints):

| Variant | Max-width | Padding-inline |
| --- | --- | --- |
| `narrow` | `768px` (`breakpoint.md`) | `space.4` (`xs`) → `space.6` (`sm`+) |
| `default` | `896px` (matches the current `max-w-4xl` header) | `space.4` → `space.6` |
| `wide` | `1280px` (`breakpoint.xl`) | `space.4` → `space.8` |
| `full` | none | `space.4` → `space.8` |

**States** stateless.

**Tokens** padding `space.4`, `space.6`, `space.8`; everything else is breakpoint-driven (⚠
`breakpoint.*`, §2). No colour.

**Accessibility** Pure layout; no role. Must not create a horizontal scrollbar at any
breakpoint (content wraps or the inner scroll region handles overflow).

**Overflow** Inner content that overflows is the child's responsibility (Table scroll wrapper,
Card `overflow: hidden`).

---

### 11.2 Stack

**Anatomy** A `div` whose only job is to space its children. 1-D.

**Variants** `vertical` (default) · `horizontal` (row, wraps by default).

**Sizes** gap from the space scale: `space.1` … `space.8` (the recommended set; any space token
is legal). Alignment props: `align` (cross axis) and `justify` (main axis).

**States** stateless.

**Tokens** `space.*` (gap). No colour, no radius.

**Accessibility** Pure layout, no role; must preserve DOM order (no CSS reordering that breaks
tab order — see composition rule 6).

**Overflow** Children wrap in `horizontal`; in `vertical` a tall child scrolls itself.

---

### 11.3 Grid

**Anatomy** A CSS grid with a named column count per breakpoint and a consistent gap.

**Variants** `auto` (responsive `auto-fit`/`minmax`; the default for card grids) · `fixed`
(explicit columns per breakpoint) · `sidebar` (2-col: content + aside, collapses to 1 below
`breakpoint.md`).

**Sizes** recommended column spans: 12-column mental model at `wide`; card grids use
`auto-fit, minmax(space.32, 1fr)`-style tracks. Gap: `space.4` (default), `space.6` (section
grids).

**Breakpoint behaviour**

| Breakpoint | `auto` grid | `sidebar` grid |
| --- | --- | --- |
| `breakpoint.xs` | 1 column | 1 column |
| `breakpoint.sm` | 2 columns | 1 column |
| `breakpoint.md` | 2–3 columns | 2 columns (aside appears) |
| `breakpoint.lg` | 3 columns | 2 columns |
| `breakpoint.xl` | 3–4 columns (capped) | 2 columns |

**States** stateless.

**Tokens** gap `space.4`/`space.6`; no colour. Breakpoint-driven (⚠ `breakpoint.*`).

**Accessibility** Pure layout, no role. Grid track reordering must not change DOM/tab order.

**Overflow** Cells have `min-width: 0` so long content truncates/wraps instead of blowing out
the track. Grids never introduce page-level horizontal scroll.

---

## 12. Token consumption matrix

Machine-readable per-component token lists are in `m8-components.tokens.json`, and
`validate-components.py` proves every name below resolves in `tokens.json`. This table is the
human-readable roll-up of the tokens each component consumes (common tokens are listed once per
component, not deduplicated across the doc).

| Component | Colour tokens | Dimension / other tokens |
| --- | --- | --- |
| Field | `color.text.secondary`, `color.text.muted`, `color.semantic.danger.base` | `typography.label`, `typography.caption`, `space.1`, `space.2` |
| Input / Textarea | `color.border.default`, `color.border.strong`, `color.border.focus`, `color.border.danger`, `color.surface.default`, `color.surface.sunken`, `color.text.primary`, `color.text.subtle`, `color.text.disabled`, `color.text.muted` | `border.width.*`, `border.focus-offset`, `border.style.solid`, `radius.sm`, `space.*`, `typography.body`, `typography.body-sm`, `motion.duration.fast`, `motion.easing.standard` |
| Select | as Input + `color.surface.raised`, `color.surface.accent-soft`, `color.brand.primary` | + `shadow.elevation-2`, `radius.md`, `z.dropdown`, `motion.duration.slow`, `motion.easing.decelerate`, `motion.easing.accelerate` |
| Checkbox | `color.border.strong`, `color.border.focus`, `color.brand.primary`, `color.text.on-accent`, `color.border.danger`, `color.surface.sunken`, `color.border.subtle`, `color.text.disabled`, `color.text.primary`, `color.text.muted` | `border.width.default`, `border.focus-offset`, `radius.xs`, `space.2`, `space.1`, `typography.body`, `typography.caption`, `motion.duration.fast` |
| Radio / Likert | `color.border.strong`, `color.brand.primary`, `color.text.on-accent`, `color.surface.default`, `color.border.default`, `color.text.secondary`, `color.border.focus`, `color.text.link`, `color.text.muted`, `color.neutral.600`, `color.surface.sunken`, `color.text.disabled`, `color.border.subtle` | `border.width.*`, `border.style.dashed`, `radius.full`, `radius.lg`, `space.*`, `typography.label`, `motion.duration.fast` |
| Button | `color.brand.primary`/`.primary-hover`/`.primary-active`, `color.text.on-accent`, `color.text.link`, `color.border.strong`, `color.surface.accent-soft`, `color.semantic.danger.base`, `color.neutral.200`, `color.text.disabled`, `color.border.focus` | `border.width.*`, `border.focus-offset`, `shadow.focus-ring`, `radius.sm`, `space.*`, `typography.*`, `font.weight.medium`, `motion.duration.fast`, `z.sticky` |
| Icon button | as Button + `color.text.muted` | + `radius.full`, `space.6/8/10` |
| Card | `color.surface.default`/`.raised`/`.sunken`, `color.border.default`, `color.border.subtle`, `color.surface.accent-soft`, `color.border.focus`, `color.text.primary`/`.secondary`/`.disabled` | `shadow.elevation-1`/`-2`, `radius.lg`, `space.*`, `typography.heading-2`, `typography.body*`, `motion.duration.base` |
| Modal / Drawer | `color.surface.overlay-scrim`, `color.surface.raised`, `color.border.subtle`, `color.text.muted`, `color.text.link`, `color.border.focus` | `shadow.elevation-3`, `radius.xl`, `z.overlay`, `z.modal`, `border.width.thin`, `border.width.focus`, `border.focus-offset`, `space.6`, `space.4`, `space.2`, `typography.heading-1`, `typography.body`, `motion.duration.slower`, `motion.duration.base`, `motion.easing.*` |
| Tooltip | `color.neutral.900`, `color.text.on-accent`, `color.border.default` | `shadow.elevation-2`, `radius.md`, `z.tooltip`, `space.2`, `space.3`, `typography.caption`, `typography.body-sm`, `motion.duration.fast`, `motion.easing.decelerate` |
| Toast | `color.surface.raised`, `color.semantic.{info,success,warning,danger}.base`, `color.text.secondary`, `color.text.link`, `color.text.muted` | `shadow.elevation-4`, `radius.lg`, `z.toast`, `border.width.thick`, `space.3`, `space.4`, `typography.body`, `typography.body-sm`, `font.weight.medium`, `motion.duration.slow`, `motion.duration.base`, `motion.easing.decelerate`, `motion.easing.accelerate` |
| Banner | `color.semantic.{…}.soft`, `color.semantic.{…}.base`, `color.text.primary`, `color.text.link` | `border.width.thick`, `radius.sm`, `space.3`, `space.4`, `space.2`, `typography.body`, `font.weight.medium` |
| Badge | `color.surface.sunken`, `color.surface.accent-soft`, `color.brand.primary`, `color.text.on-accent`, `color.text.secondary`, `color.text.link`, `color.semantic.{…}.soft`/`.base` | `radius.full`, `space.1`, `space.2`, `typography.caption` |
| Spinner / Progress | `color.surface.sunken`, `color.brand.primary`, `color.semantic.success.base`, `color.text.muted` | `radius.full`, `space.4/5/6`, `typography.caption`, `motion.duration.slower`, `motion.easing.linear` |
| Top nav | `color.surface.default`, `color.border.subtle`, `color.text.secondary`, `color.text.link`, `color.text.link-hover`, `color.border.focus`, `color.text.primary`, `color.surface.raised` | `border.width.thin`, `border.width.thick`, `border.width.focus`, `border.focus-offset`, `z.sticky`, `z.dropdown`, `shadow.elevation-2`, `space.2`, `space.4`, `space.6`, `space.10`, `space.12`, `typography.body`, `font.weight.semibold` |
| Sidebar | `color.surface.default`, `color.surface.canvas`, `color.border.subtle`, `color.text.secondary`, `color.surface.sunken`, `color.surface.accent-soft`, `color.text.link`, `color.border.focus` | `space.1`, `space.3`, `space.4`, `space.8`, `space.12`, `space.32`, `radius.sm`, `z.sticky`, `z.overlay`, focus tokens |
| Tabs | `color.text.secondary`, `color.text.link`, `color.surface.sunken`, `color.border.focus`, `color.brand.primary`, `color.text.on-accent`, `color.surface.default`, `color.border.subtle` | `border.width.thick`, `border.width.focus`, `border.focus-offset`, `radius.sm`/`full`, `space.1`–`space.4`, `typography.label`, `motion.duration.base` |
| Breadcrumb | `color.text.secondary`, `color.text.link`, `color.text.link-hover`, `color.text.muted`, `color.text.subtle`, `color.border.focus` | `space.2`, `typography.body-sm`, `border.width.focus`, `border.focus-offset` |
| Table | `color.surface.default`, `color.surface.sunken`, `color.border.subtle`, `color.border.strong`, `color.surface.accent-soft`, `color.border.focus`, `color.text.secondary`, `color.text.primary`, `color.text.muted` | `border.width.thin`, `border.width.focus`, `border.focus-offset`, `radius.none`, `radius.lg`, `space.2`, `space.3`, `space.10`, `typography.label`, `typography.body`, `typography.code`, `motion.duration.slower`, `motion.easing.linear` |
| List | as Table's surface/text subset + `space.1`–`space.3`, `radius.sm`, `typography.body`, `typography.body-sm` | |
| Pagination | `color.surface.default`, `color.border.default`, `color.text.secondary`, `color.surface.sunken`, `color.text.link`, `color.surface.accent-soft`, `color.border.focus`, `color.text.disabled`, `color.text.subtle` | `radius.sm`, `space.1`–`space.3`, `typography.body-sm`, focus tokens |
| Container | — (colourless) | `space.4`, `space.6`, `space.8`, ⚠ `breakpoint.*` |
| Stack | — | `space.*` |
| Grid | — | `space.4`, `space.6`, ⚠ `breakpoint.*` |

Every `color.*` row above has a `color.dark.*` counterpart where `tokens.json` defines one; the
component consumes the same token name and the theme layer swaps the value.

---

## 13. Keyboard interaction summary

| Component | Tab | Arrows | Enter | Space | Esc | Home/End | Other |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Button / Icon button | 1 stop | — | activate | activate | — | — | — |
| Input / Textarea | 1 stop | caret | (submit?) textarea=newline | space char | — | line start/end | Ctrl/Cmd+Enter = submit |
| Select (native) | 1 stop | change value | open/confirm | open/confirm | close | first/last | type-ahead |
| Select (custom listbox) | 1 stop | move active option | select+close | open/select | close, return focus | first/last | Alt+Down open; type-ahead |
| Checkbox | 1 stop per box | — | — | toggle | — | — | label click toggles |
| Radio group / Likert | 1 stop (selected or first) | move **and select** (wrap) | — | select focused | — | first/last | — |
| Card (interactive) | 1 stop | — | activate | activate | — | — | footer buttons are separate stops |
| Modal / Dialog | trapped inside | focus moves | activate focused | activate focused | close, restore focus | — | backdrop inert |
| Tooltip | none | — | — | — | hide | — | shows on hover + focus |
| Toast | action only | — | activate action | activate action | dismiss | — | pauses timer on hover/focus |
| Top nav | brand→links→toggle | menu: item nav | activate | activate | close menu | — | — |
| Sidebar | items in order | — | activate | toggle collapse | close (overlay) | — | disclosure expands nested |
| Tabs | 1 stop, then panel | move tab (wrap) | activate | activate | — | first/last | roving tabindex |
| Breadcrumb | links in order | menu: nav | activate | — | close "…" menu | — | — |
| Table | controls→scroll→rows | — | sort header / activate cell | sort / activate | — | — | rows are not hover-only |
| List (selectable) | 1 stop | move | activate row | toggle (multi) | — | first/last | roving focus |
| Pagination | controls in order | — | activate | activate | — | — | ellipsis not focusable |

---

## 14. Open questions

For the consolidation pass (`<task-id>`) and the next milestone.

1. **⚠ Breakpoints are not yet tokens.** §2 defines them, but the token README (open question 2)
   says any breakpoint token should live in `tokens.json`. Recommend promoting `breakpoint.*`
   into the token file in v1.1 so the source of truth stays single. This doc is authoritative
   only until that happens.
2. **Semantic-solid hover/active tokens are missing.** `brand.primary` has hover/active tokens;
   `semantic.danger/success/warning.base` do not. `danger` Button hover/active therefore needs
   either new tokens (`color.semantic.danger.hover/active`) or a documented, sanctioned
   darkening function. Not invented here.
3. **Icon size tokens are missing.** The asset spec uses a 24px icon grid; components need
   16/20/24px icon sizes, which are not space tokens. Recommend `icon.size.sm/md/lg` in
   `tokens.json` rather than reusing `space.*` for icon boxes.
4. **Component size tokens.** Button/Input heights, sidebars widths, and modal max-widths are
   currently component constants, not tokens. Decide whether control geometry becomes tokens
   (`control.height.sm/md/lg`, `container.width.*`) or stays in the component layer.
5. **Density.** Only one spacing rhythm is defined (token README open question 5); the Table's
   `compact` variant is therefore provisional.
6. **Reduced-motion spinner.** Looping animation stops under `prefers-reduced-motion`; a
   non-animated loading indicator is specified (text) but should be visually reviewed.
7. **Focus ring on horizon-agnostic surfaces.** `shadow.focus-ring` is a fallback; audit
   components that clip outlines (Card media, Table scroll region) before shipping.
8. **Party swatches / `color.party.*`.** The asset spec (`<task-id>`) references a
   `color.party.*` token group that is absent from `tokens.json` v1.0.0. Consolidation must
   resolve this: add the group (with a neutrality review) or fix the asset spec. A party's
   colour is render-time data, not page-level framing; confirm the swatch size and the
   mandatory adjacent text label against the neutrality protocol before the results UI is built.
9. **Infinite scroll pagination.** Listed as deferred — it has no focus-management story yet
   and is not recommended for an accessible results list.

---

*End of component specification. Token names in this document are machine-checked against
`tokens.json` by `validate-components.py`; run it before handing this file downstream.*
