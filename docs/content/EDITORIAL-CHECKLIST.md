# Editorial Checklist

The pre-publish checklist for BC Vote Match content and data releases. A human (the editor of record) works through every item and signs off before anything goes public. No item may be waved through because time is short. This checklist exists so that "we checked" means something specific.

## 1. Content and neutrality

- [ ] No sentence in any public copy says or implies that a party, candidate, or voter is wrong, dishonest, or misguided.
- [ ] No endorsement language anywhere: no "best", "worst", "should win", "get out and vote for", or ranking of parties in prose or in layout.
- [ ] Party ordering is fixed and neutral wherever parties appear. No party first, largest, or highlighted by default.
- [ ] Descriptions of party positions trace to the party's own words or to the coded quote. No invented framing.
- [ ] Outreach copy states where the reader sits, never what the reader should do.
- [ ] Names and trademarks (Vote Compass, Vox Pop Labs, Elections BC) appear only in the disclaimer context and are accurate.

## 2. Coding and sources

- [ ] Every non-null code has a verbatim quote from a fetched source.
- [ ] Every quote passes the mechanical substring check against the stored source file. Zero unverified quotes in the release.
- [ ] Every cited source has a working URL, a stored copy, a matching SHA-256 hash, and an archive URL where one exists.
- [ ] The source-hierarchy rule was applied uniformly across all five parties. Spot-check at least two rows per party.
- [ ] Every "no position" code is a genuine absence of a statement, not a coding shortcut. Spot-check at least one per party against the party's full source inventory.
- [ ] All coder splits were resolved by blind verification or human tie-break, and each resolution is logged.
- [ ] The full coding table (codes, quotes, sources, versions, dispute log) is published alongside the release.

## 3. Questions and scoring

- [ ] The question set matches the frozen, versioned set. Any post-freeze change is recorded with reason and date.
- [ ] The scale legend (-2 strongly disagree through +2 strongly agree, plus "no position") is visible wherever codes or scores appear.
- [ ] The alignment formula in the release matches the formula in the methodology page. Recompute one sample by hand and compare.
- [ ] "Don't know" answers and "no position" codes are excluded from scoring, not counted as zero, in code and in the copy describing it.
- [ ] The 2-D map is described as a summary of the same answers, with the caveat visible near the map itself.

## 4. Privacy and legal

- [ ] No new network calls to third parties have been introduced. Check the built site's requests, not just the source.
- [ ] No login, account, or demographic input exists anywhere in the build.
- [ ] Server logs and analytics match what the privacy page describes, including retention.
- [ ] Disclaimer is present and reachable from every results view.
- [ ] No funding or in-kind support has been accepted from parties, candidates, or their financial agents since the last sign-off. If anything changed, the disclosure is on the front page before this release ships.

## 5. Accessibility and technical

- [ ] The site builds clean and the release is reproducible from the tagged commit.
- [ ] Results and coding tables are readable without JavaScript where the stack allows, and usable with a screen reader.
- [ ] Color is never the only carrier of party identity; labels accompany colors.
- [ ] Share cards contain scores only, never identifying information.

## 6. Versioning and record

- [ ] Coding table version and date are current and shown publicly.
- [ ] Any recode since the last release has a published diff with reason.
- [ ] Quarantined rows, if any, are listed with reasons in the audit record.
- [ ] Outstanding corrections are either resolved or acknowledged publicly.
- [ ] This checklist run is dated and signed in the release log.

## Sign-off

```
Release version: ____________
Checklist completed by: ____________
Date (UTC): ____________
Result: [ ] approved to publish   [ ] held, reason: ____________
```

A held release goes back through the failed section in full before sign-off is offered again. There is no partial publish.
