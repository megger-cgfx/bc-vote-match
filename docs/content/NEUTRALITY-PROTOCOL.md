# Neutrality Protocol

This document is the internal rulebook for how BC Vote Match stays method-neutral. It is published because a neutrality claim you cannot inspect is not a neutrality claim. If you are a journalist, a party researcher, or a sceptical reader, this is the standard you can hold us to.

## The core rule

Neutrality lives in the method, not in the tone of the writing. We do not achieve balance by making sure we criticize everyone equally. We achieve it by giving every party the identical process and showing our work.

## Rule 1: identical coding effort per party

- Every party gets the same number of coders on the same questions: two independent coders per party, plus a blind verification pass on disputed rows.
- Coder assignments are not matched to a coder's sympathies. A coder works from sources, not from a preferred outcome.
- The same source hierarchy applies to every party: platform, then policy documents, then releases and speeches, then Hansard, then media, then other. No party gets a more favorable tier.
- If one party publishes less, the result is more "no position" codes for that party. It never results in us inferring positions to make the table look even. Uneven evidence produces uneven coverage, and we show the coverage honestly rather than smoothing it.

## Rule 2: every code is sourced

- No code ships without a verbatim quote from a real, fetched source.
- Quotes are verified mechanically as exact substrings of the stored source file before publication. A quote that does not verify is re-pointed to a trusted source containing the same text, with the fix logged, or the row is quarantined and excluded from the public table.
- Every source is archived and hashed. The hash is in the data. If a party edits or deletes a page mid-campaign, we can still show what it said.
- "No position" is a first-class result. Guessing a party's position is a protocol violation regardless of which party it helps or hurts.

## Rule 3: the full coding table is published

- Every row of the coding table goes public: the code, the quote, the source link, the archive link, the coder identifier, and the version.
- Disagreements between coders are published too, along with how each dispute was resolved. A clean-looking table with the arguments hidden would defeat the purpose.
- Recodes are versioned and diffed. When a party changes position and we change a code, the change history is public.

## Rule 4: outreach copy never argues a party is wrong

- Public copy says "here is where you sit," never "party X is wrong," "party Y is lying," or any other judgment about a party or its supporters.
- We do not write persuasive copy for or against any party, candidate, or outcome. There is no "get out the vote" tilt in any direction, and no framing that treats one result as a good or bad result.
- Descriptive language about a party's position is drawn from the party's own words wherever possible. Where we summarize, we summarize what the quote says and nothing more.
- Design choices are held to the same standard: neutral ordering (fixed, not sorted by score), neutral colors from the parties' own published branding, no visual emphasis on any party's result.

## What we will not do

- We will not accept funding, data, or in-kind support from registered parties, candidates, or their financial agents. If that ever changes, it will be disclosed on the front page, not buried here.
- We will not weight questions to produce a preferred outcome. The question set is frozen before coding and any change after freeze is versioned and disclosed.
- We will not quietly delete a coding row. Quarantined rows stay visible in the audit record with the reason.
- We will not trade corrections for access. A correction is accepted or rejected on the evidence of the quote, nothing else.

## Disputes and corrections

Anyone, including the parties themselves, can challenge a code. The challenge is evaluated the same way in every case: does a verbatim quote from a trusted source support a different code on the published scale? If yes, we recode, version it, and publish the change. If no, we publish the challenge and our reason for leaving the code alone. Both outcomes are logged.

## Why this is public

Credibility is the entire product. A tool like this fails the moment a reasonable person suspects the questions, the codings, or the math were rigged, and no amount of "trust us" survives that suspicion. The only durable answer is to make the method inspectable and then actually follow it. This protocol is the commitment; the published coding table and the open-source repository are the evidence.
