# How BC Vote Match works

BC Vote Match is a tool that shows where you stand relative to the parties running in the 2026 British Columbia provincial election. You answer 18 statements. We show you how closely your answers line up with each party's stated positions. That is the whole product.

This page explains exactly how we get from party platforms to the numbers on your screen. Nothing here is hidden on purpose. If something is unclear, that is our failure, and we want to hear about it.

## Where the party positions come from

We only use what the parties themselves have said in public. Platforms, policy backgrounder documents, news releases, speeches, and occasionally legislative record (Hansard). Every position we assign to a party is backed by a verbatim quote from a document we saved, hashed, and archived, with a link so you can read the quote in its original context.

The sources are ranked in a fixed order when we code a position:

1. The party's election platform
2. Formal policy documents
3. News releases and speeches
4. The legislative record (Hansard)
5. Media coverage
6. Everything else

If a higher-ranked source speaks to a statement, it wins. We do not cherry-pick the source that makes a party look good or bad.

Every source we use is saved locally with a SHA-256 hash and, where possible, submitted to the Wayback Machine. Campaign pages change and disappear. The archive and the hash are how we prove what the page said on the day we read it.

## How statements were chosen

We started with a pool of roughly 50 candidate statements covering six topics: cost of living and taxes, housing, health, climate and environment, Indigenous reconciliation, and public safety. From that pool we chose 18, three per topic.

The rule for choosing was simple: does this statement separate the parties on evidence, not on vibes? A statement where all five parties agree tells you nothing about alignment. We kept the statements where their published positions actually differ, plus a few anchor statements where agreement is itself informative.

Each statement is a single proposition you can agree or disagree with on a five-point scale, with a "don't know" option. Some statements load onto a second dimension we call "social" alongside the main "economic" one. That is what produces the two-dimensional map, explained below.

## How parties are coded

For each of the 18 statements, we assign each party a code from the same scale you answer on:

| Code | Meaning |
|------|---------|
| +2   | Strongly agree with the statement |
| +1   | Agree |
| 0    | Explicitly neutral or balanced |
| -1   | Disagree |
| -2   | Strongly disagree |
| none | The party has stated no position |

A few things about that table matter:

- **"No position" is a real answer.** If a party has not said anything about a statement, we do not guess, infer, or fill the gap with what we think they probably believe. The code is blank, and that question is left out of the alignment math for that party.
- **Every non-blank code carries a quote.** The quote is checked mechanically against the archived source text before it ships. A quote we cannot verify does not go public.
- **Coding is done twice, independently.** Two coders work on each party separately and never see each other's work. Where they disagree, a third blind pass reviews the row. If it is still unresolved, a human makes the final call and the disagreement is recorded, not hidden.
- **The full coding table is published.** Every code, every quote, every source link, and every place where the coders disagreed. You can audit our work line by line.

## How your alignment is calculated

You answer each statement on the same -2 to +2 scale. For each party, we compare your answers to that party's codes on the statements you both have an answer for, and take the average distance between them. Your alignment score is:

```
alignment = 1 - (total distance / maximum possible distance)
```

expressed as a percentage. Two identical sets of answers give 100. Opposite answers on every question give 0. Statements where you answered "don't know", or where the party has no position, are skipped for that party rather than counted against anyone.

We also show sub-scores per topic, so you can see that you line up with a party on housing but not on health.

## The two-dimensional map

Each statement is tagged as economic, social, or both. Averaging the codes on each set of statements gives every party a position on an economic axis and a social axis, and gives you one too. The map plots those two numbers. It is a summary of the same 18 answers, not a separate model.

Treat the map as a reading aid, not a measurement of anyone's soul. Two dots close together on the map can still differ sharply on a specific topic. The topic breakdowns and the raw coding table are the more precise instruments.

## What this tool does not do

- **It does not tell you how to vote.** It shows distances, not endorsements. Parties are listed in a fixed, neutral order and we never rank them from best to worst.
- **It does not predict your vote.** Plenty of people find they are closest to a party they will never vote for. Leaders, local candidates, record in government, trust, and strategic voting all sit outside this method, and they are often what decide votes.
- **It does not measure everything.** Eighteen statements cannot cover a party's full platform, still less a government's record. The questions are a sample chosen to differentiate, not a survey of everything that matters.
- **It does not take your data.** There is no account, no login, and no demographic questions. Your answers never leave your browser. See [Privacy](PRIVACY.md).
- **It does not speak for the parties.** The codes are our reading of published statements. A party may disagree with how we read them, and we publish corrections when the evidence warrants one.

## Corrections and versions

Party positions change during a campaign. When they do, we recode the affected rows, version the change, and publish what moved and why. If you think we have a party wrong, the fastest fix is to send us the quote that proves it. See [About](ABOUT.md) for how to submit a correction.

The underlying data and the code for this site are open source. You do not have to take our word for the math.
