# BC 2026 VAA — Questions Catalogue (short)

_Compiled 2026-10-01 · supersedes the 51-item version. `(rec:)` = my recommended answer; say "use recs" to accept all._

**Locked context:** public-value tool to inform voters & build confidence in the system; must be credible/neutral; **launch in days** (agents run non-stop); clean-room product with a pointer to Vote Compass; **party-level first, then riding-level**; open-source, self-hosted public site; public contributions reviewed; influencer + media outreach campaign.

**Flag:** neutrality must live in the **method** (symmetric, sourced coding) — the lean can only live in **outreach framing and feature choices**. A slanted coder destroys the credibility the goal depends on. (Q2)

## A. Framing
1. Working name + domain?
2. Confirm: tool is **method-neutral + fully sourced**; the "lean" lives only in outreach framing/promotion. *(rec: yes)*
3. One-sentence disclaimer ("educational tool, not how-to-vote") — adopt VC's wording? *(rec: yes)*

## B. MVP scope (launch in days)
4. Confirm **v1 = party-level only**, riding-level fast-follow. **Target launch date?**
5. Question count for v1 *(rec: 15–20)*.
6. v1 feature set + constraints: questionnaire + 2-D compass + alignment bars + per-question citations; English only; mobile-first; basic WCAG AA; **no** demographics/research weighting. *(rec: exactly this)*

## C. Method (your Q4)
7. Scoring: code each party **−2…+2** per statement; pre-assign each statement to a dimension; alignment = normalised similarity; IRT as a later upgrade. *(rec: yes)*
8. Dimensions: **economy/taxes × social**, like VC *(rec)* — or BC-specific axes (economy × environment/resources)?
9. Issue-importance weighting in v1? *(rec: no)*
10. Human coding gate: **2 independent coders + adversarial check agent**, human tie-break, human signs off before publish. *(rec: yes)*
11. Send parties a self-coding request — **without blocking launch** on replies. *(rec: yes)*

## D. Data & scraping
12. Party list: **NDP, Conservative, Green, OneBC, CentreBC**; minors only if full slate + comprehensive platform. *(rec: yes)*
13. Adopt VC's source-priority ladder (platform → policy doc → releases/statements → minister/critic → other MLAs → constitution). *(rec: yes)*
14. Provenance: every coding carries a **quoting snippet + archived URL + hash**. *(rec: yes)*
15. Riding phase: Elections BC candidate list + boundaries + postal→riding (StatCan). Recode **weekly + on platform release**, versioned. *(rec: yes)*

## E. Build / hosting / open source
16. Stack: static site (Astro / Next export), data as in-repo JSON, scoring in-browser, **no DB, no PII**. *(rec: yes)*
17. Public GitHub, permissive license (MIT?), contributions via PR reviewed by agents then a human; host on Cloudflare/Vercel/Netlify or self-hosted VPS? **Preference?**
18. Privacy/legal: PIPEDA/FIPPA-safe, no PII, disclaimer page. *(rec: yes)*

## F. Orchestration, outreach, launch
19. Orchestration layers: **recon → coding → adversarial QA → build → integration**; human gates on final codings + publish. *(rec: yes)*
20. Outreach: which Vote Compass media partners (CBC / The Star / …) and which influencers/communities to approach? Who writes the pitch?
21. Success metric for "a tiny difference": completions, shares, press/influencer pickups — pick targets.
