# Curator's rubric — what I accept, what I send back

Working notes for the M8 outreach wave. This is the marketing director's judgement standard, written
down so the decisions are reviewable rather than taste. Martin reviews the curated output, not the
raw pile; everything that reaches him should already have survived this.

## The four gates, in order

A candidate asset or piece of copy is rejected at the first gate it fails. Order matters: a beautiful
card that fails neutrality is worse than a plain one that passes.

### Gate 1 — Neutrality (fatal, no exceptions)

Reject outright if it:

- says or implies any party, candidate or supporter is wrong, lying, extreme, or a bad choice;
- treats any party's alignment result as good or bad news;
- nudges toward voting, or toward not voting, or toward any party;
- uses party logos, party colours as campaign framing, or party visual identity as a motif;
- orders parties by score anywhere that reads as a ranking (fixed order only);
- makes an accuracy, user-count or endorsement claim we cannot source;
- relies on a statistic without a citation with URL and read-date.

A list of the specific phrasings rejected, and why, goes in `05-copy/NEUTRALITY-AUDIT.md`. If I reject
something on judgement rather than a stated rule, I record it as a judgement call so Martin can
overrule me.

### Gate 2 — Truthfulness of the picture

- Every number, party name, date and URL on the card is correct against `data/` or `docs/`.
- No placeholder text, no `example.invalid`, no fixture coder ids, no lorem.
- If it shows a chart, the values are real values, and the axis claim matches the method in
  `docs/content/METHODOLOGY.md`. A share card is not allowed to be prettier than the truth.

### Gate 3 — Does it work at the size it will actually be seen

- Legible at thumbnail: the headline survives the smallest real placement (X in-feed, a Reddit
  thumbnail, a Slack unfurl). If it needs to be tapped to be understood, it fails.
- Correct pixel dimensions for its declared slot, verified by the render tool's assertion, not by
  trusting the design.
- Contrast checked, not eyeballed. Text over a photographic plate needs the darkening pass; if a
  card only works because the plate happened to be dark, that is a failure.
- One idea per asset. A card that says three things says nothing.

### Gate 4 — Is it worth the slot

- It says something the reader could not have guessed from the title alone.
- It is not a duplicate of another asset with a different crop.
- It earns its place in the launched set: if the set is 12 assets, each one has a stated job.

## What I deliberately do not optimise for

- **Polish over clarity.** The site is deliberately plain and the assets should look like the same
  project made them.
- **Volume.** A curated set of 8 strong assets beats 40 variants. Martin asked for the best chance of
  impact, not a big folder.
- **Novelty in the brand mark.** The product already has a mark that ships. Extending it beats
  replacing it.
- **Engagement mechanics.** No bait, no urgency, no countdowns, no "you won't believe".

## The reproducibility requirement

Every generated image carries its model, prompt, seed, sampler, steps, cfg and dimensions in a
manifest next to it. An asset I cannot regenerate is one I cannot correct when a coding changes, and
codings *will* change (recode passes Oct 12 and Oct 20). Assets whose text is baked into a diffusion
image are rejected for this reason alone, independently of how they look.

## Standing structural decisions

- **Code draws the words, the GPU draws the pictures.** Text is composed in SVG and rasterised
  deterministically, so a party name or a number can never be misspelled or hallucinated. ComfyUI
  supplies imagery only: plates, textures, illustrations. This is the single most important
  architectural call in the wave and it is not up for trade against visual richness.
- **Fonts:** self-hosted, OFL, one family. No external origins anywhere in the pipeline.
- **Aspect ratios:** the design system is built at all four ratios (1200x630, 1600x900, 1080x1080,
  1080x1350) because composition is code and extra ratios are nearly free, but only the approved
  channels are rendered in v1: og/share cards, X, Reddit.
