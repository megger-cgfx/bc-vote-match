# Coding reconciliation report

Rule: agree -> publish code; disagree -> blind third pass decides, publishes
that code; verifier matching neither coder -> publish null and escalate to a
human; an escalated row with a written human decision -> publish that code;
no verifier -> publish null; one coder -> publish with low confidence;
neither -> null.

- ndp: 18 questions | agreed 11 | tie-broken 0 | human tie-broken 2 | escalated 0 | split 0 | single-coder 1 | no-position 4
- cpb: 18 questions | agreed 10 | tie-broken 2 | human tie-broken 0 | escalated 0 | split 0 | single-coder 2 | no-position 4
- green: 18 questions | agreed 10 | tie-broken 0 | human tie-broken 2 | escalated 0 | split 0 | single-coder 1 | no-position 5
- onebc: 18 questions | agreed 7 | tie-broken 1 | human tie-broken 0 | escalated 0 | split 0 | single-coder 1 | no-position 9
- centrebc: 18 questions | agreed 5 | tie-broken 0 | human tie-broken 0 | escalated 0 | split 0 | single-coder 2 | no-position 11

Numeric disagreements: 7 (tie-broken 3, human tie-broken 4, escalated 0, awaiting verification 0); code-vs-null disagreements: 7.

Human tie-breaks applied from data/codings/_human-decisions.json:

- green/q11 -> 1 (flower (agent, provisional - editor sign-off pending)): The Green pledge is vacancy control (green-0009 2026 plan: 'Pass vacancy control to ensure landlords can't raise the rent every time a tenant moves out'; green-0004 explains rent is tied to the unit across tenancies).
- green/q22 -> 1 (flower (agent, provisional - editor sign-off pending)): The plank (green-0091, the 2024 platform) says 'Immediately enhance accessibility to supervised consumption services and overdose prevention sites' and 'Continue the expansion of supervised consumption services'.
- ndp/q01 -> -2 (flower (agent, provisional - editor sign-off pending)): The party's own government repealed the consumer carbon tax in 2025 and its Finance Minister defended the removal in Hansard (ndp-0024: 'when the carbon tax was removed, so too did we remove that'), giving the fairness ground that the tax 'did not land evenly' - the same cost tradeoff the statement accepts.
- ndp/q04 -> -1 (flower (agent, provisional - editor sign-off pending)): Budget 2026 (ndp-0025) shares a partial deficit-reduction goal ('reducing the deficit while continuing to support the housing, health care, education and social services British Columbians need') while explicitly rejecting the statement's instrument ('this is not an austerity budget.

