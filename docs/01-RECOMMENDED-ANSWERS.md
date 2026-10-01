# BC 2026 VAA — Recommended Answers (lean)
_2026-10-01 · object on any line and I'll revise._

**Competitive note:** **VoteMate** (votemate.org) already covers BC candidate info + side-by-side platform comparison for 2024 and 2026 — but has **no alignment questionnaire**. Our differentiator is the scoring/compass. Consider them an **ally/partner**, not a rival. Names taken: "Vote BC", "BC Ballot". So avoid those two.

**A. Framing**
1. **Name:** working name **"BC Vote Match"**, domain **bcvotematch.ca** (fallback `bcvotematch.org`). Tagline: _"See which party matches your views — BC 2026."_ (Verify domain + no trademark collision before print.) Honestly, the "lean toward exposing Conservatives" goal can't appear anywhere in the product — it lives only in outreach framing.
2. **Neutrality:** Yes, method-neutral. Add a written **neutrality protocol**: equal coding budget per party; every code sourced; full coding table published; outreach copy only ever says "your views vs the parties," never "party X is wrong."
3. **Disclaimer:** Yes, VC-style + independence line: _"BC Vote Match is an educational tool… It does not tell you how to vote or predict your vote. Independent project; not affiliated with Vote Compass / Vox Pop Labs."_

**B. MVP scope**
4. **Launch:** soft link **Oct 5**, **public launch Oct 8**, content freeze Oct 6; **riding-level v1.1 by Oct 14** (before advance voting Oct 16–21); recoding passes Oct 12 and Oct 20.
5. **Questions:** **18**.
6. **v1 features:** 18 statements (5-pt Likert + "don't know"), 2-D compass, alignment bars, per-question "you vs party" with sources, **OG share cards**; EN only; mobile-first; WCAG 2.1 AA basics; no demographics, no research weighting. Yes.

**C. Method**
7. **Scoring:** Yes — parties coded **−2…+2** per statement; each statement tagged to dimension(s); 2-D position = mean of dimension loadings; alignment = `1 − normalised distance`. No IRT in v1.
8. **Dimensions:** 2 axes = **economic (left↔right) × social (progressive↔conservative)** (VC-comparable) **plus** BC topic sub-scores: cost of living/taxes, housing, health, climate & environment, Indigenous reconciliation, public safety.
9. **Importance weighting:** No in v1 (defer to v1.2).
10. **Human coding gate:** Yes — 2 independent coder agents per party + 1 adversarial verifier + **you sign off** before publish.
11. **Party self-coding:** Yes — email the 5 parties Oct 5, **don't block launch**; reconcile into v1.1.

**D. Data & scraping**
12. **Party list:** 5 majors (NDP, Conservative, Green, OneBC, CentreBC); add a minor only if it runs a **full 93-slate + publishes a platform** (check after nominations close Oct 3).
13. **Source ladder:** Yes — adopt VC's.
14. **Provenance schema:** `{statement_id, party_id, code(−2..2), quote, source_url, archive_url, fetched_at, sha256}`.
15. **Riding phase:** Yes — Elections BC candidate list + shapefiles + StatCan postal→riding; recode weekly + on platform release; versioned diffs published.

**E. Build / hosting / open source**
16. **Stack:** **Next.js (static export) + TypeScript + Tailwind**; data as in-repo JSON; scoring in-browser; no DB; no PII. (Astro fine too.)
17. **Repo/license/hosting:** public **GitHub**, **MIT** license (use AGPL if you want derivatives to stay open), contributions via PR (agents triage → human merges) + a public "corrections" issue form; host on **Cloudflare Pages** with custom domain.
18. **Privacy/legal:** Yes — no PII, no login, no third-party trackers; privacy-first analytics (Cloudflare Web Analytics / Plausible); PIPEDA/FIPPA-safe; disclaimer + independence page; **named operator/editor** (needed for credibility and outreach).

**F. Orchestration, outreach, launch**
19. **Orchestration:** Yes — 5 layers (recon → coding → adversarial QA → build → integration); shared state in workspace JSON; human gates = freeze codings after QA, and before publish.
20. **Outreach:** target media — CBC BC, Global BC, CTV Vancouver, The Tyee, Vancouver Sun/Postmedia, Castanet, Daily Hive, The Narwhal; **partner pitch to VoteMate**; UBC/SFU poli-sci. Influencers — BC politics YouTubers/podcasters, TikTok/IG civic creators, Reddit r/britishcolumbia & r/vancouver (mind self-promo rules). **I draft all copy; you approve.**
21. **Success metrics:** min **5k** completions by E-day · target **25k** · stretch **100k**; share rate ≥20%; ≥3 earned-media pickups; ≥1 influencer >50k reach; 100+ public corrections; 99.9% uptime.

**Biggest risk to your stated goal:** the "faint hope" about the Conservatives. Keep it strictly out of the product and lightly out of the outreach, or the neutrality that makes it credible evaporates. The neutrality protocol (Q2) is the artifact that protects it.
