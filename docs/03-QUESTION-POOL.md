# BC Vote Match — Question Pool (M1)

_Compiled 2026-10-01 · orchestrator: flower · **status: candidates, not frozen**_

Machine-readable source of truth: `data/questions/questions.json` (54 statements, schema-conformant).
This doc is the human-readable view for the **M2 freeze gate** (Oct 3) where ~18 statements are locked.

## Summary

- **54 candidate statements** (target 45-60), **9 per topic** across all six contract topics.
- Every statement: `id`, `statement`, `topic`, `dimensions`, `status: candidate`, `notes` (why it differentiates).
- Dimensions: **38 economic**, **22 social** (statements may carry both).
- All statements are phrased as directional propositions a voter can agree/disagree with on the −2…+2 scale.
- Grounded in the real 2026 campaign lines: carbon tax rescinded, deficit as a top-Conservative issue, private-clinic fight, LNG, DRIPA repeal-vs-amend, decriminalization ended, street disorder.

## Flagged: low-differentiation (consensus) items

These are broadly supported by all five parties, so they add little scoring signal. **Recommend dropping at the freeze gate** unless kept for balance/education:

- `q41` Indigenous-led child & family services
- `q45` Indigenous language & culture funding
- `q51` More publicly funded treatment beds (goal is consensus; only funding scale differs)
- `q54` Youth crime-prevention programs

That leaves 50 differentiating candidates to select 18 from.

## Pool by topic

### cost-of-living-taxes
| id | statement | dim |
|----|-----------|-----|
| q01 | Reinstate and raise the consumer carbon tax | economic |
| q02 | Cut taxes for middle/higher earners even if services shrink | economic |
| q03 | Wealth tax on the highest earners | economic |
| q04 | Balance the budget even in uncertain times by cutting spending | economic |
| q05 | Cap grocery and fuel prices | economic |
| q06 | Index the minimum wage to inflation | economic |
| q07 | Cut the deficit mainly by shrinking the public service | economic |
| q08 | Target cost-of-living relief to low-income households, not broad cuts | economic |
| q09 | Raise corporate taxes to fund public services | economic |

### housing
| id | statement | dim |
|----|-----------|-----|
| q10 | Province overrides municipal zoning for transit density | economic, social |
| q11 | Strengthen and extend rent controls | economic |
| q12 | Government builds and owns affordable rental housing | economic |
| q13 | Tax vacant and speculator-owned homes more heavily | economic |
| q14 | Protect homeowners from policies that lower property values | social, economic |
| q15 | Municipalities, not the province, control density | social |
| q16 | Tightly restrict short-term rentals (Airbnb) | economic |
| q17 | Subsidise first-time homebuyers | economic |
| q18 | Expand supportive housing even where neighbourhoods object | social |

### health
| id | statement | dim |
|----|-----------|-----|
| q19 | Expand private for-profit clinics | economic |
| q20 | Speed up hiring of foreign/US health workers | economic |
| q21 | Expand public pharmacare | economic |
| q22 | Fund more supervised consumption and safer supply | social |
| q23 | Keep health care fully public and single-payer | economic |
| q24 | Add dental care to the public system | economic |
| q25 | Expand overdose-prevention sites despite local objections | social |
| q26 | Mandate minimum nurse-to-patient ratios | economic |
| q27 | Allow more private diagnostic imaging | economic |

### climate-environment
| id | statement | dim |
|----|-----------|-----|
| q28 | Approve new LNG export projects | economic |
| q29 | Stop old-growth logging | social, economic |
| q30 | Require steep oil & gas emissions cuts | economic |
| q31 | Invest in transit/rail rather than highways | economic |
| q32 | Apply industrial carbon pricing to largest emitters | economic |
| q33 | Protect 30% of land and water by 2030 | social |
| q34 | Require all new car sales electric by 2035 | economic |
| q35 | Fast-track mining/resource approvals for jobs | economic |
| q36 | End fossil fuel subsidies | economic |

### indigenous-reconciliation
| id | statement | dim |
|----|-----------|-----|
| q37 | Fully implement DRIPA | social |
| q38 | Amend DRIPA to rule out a veto over resources | economic, social |
| q39 | Share resource revenue with First Nations | economic |
| q40 | Affirm Aboriginal title and rights in provincial law | social |
| q41 | Fund Indigenous-led child & family services | social |
| q42 | First Nations have a decisive role in land-use decisions | economic, social |
| q43 | Prioritise Indigenous businesses in procurement | economic |
| q44 | Accelerate treaty negotiations | economic |
| q45 | Expand Indigenous language and culture funding | social |

### public-safety
| id | statement | dim |
|----|-----------|-----|
| q46 | Keep public drug use illegal; don't revive decriminalization | social |
| q47 | Tougher bail for repeat violent offenders | social |
| q48 | Expand involuntary care for severe addiction/mental illness | social |
| q49 | Increase police funding for street disorder | economic, social |
| q50 | Scale back safer supply in favour of treatment | social |
| q51 | Create many more public treatment/recovery beds | economic |
| q52 | Let municipalities ban public drug use by bylaw | social |
| q53 | Allow courts to order addiction treatment for repeat offenders | social |
| q54 | Invest in youth crime-prevention programs | social |

## Proposed 18 for the freeze gate (recommendation, not final)

Three per topic, chosen to maximise party differentiation and to split the NDP's own base as well as the left-right line. The human gate can swap any of these for pool alternates.

- **cost-of-living-taxes:** q01, q04, q09
- **housing:** q10, q11, q13
- **health:** q19, q22, q23
- **climate-environment:** q28, q29, q35
- **indigenous-reconciliation:** q37, q38, q42
- **public-safety:** q46, q48, q50

Notes: q01/q28/q37 are the highest-salience values lines; q04 targets the Conservative base; q10/q11/q19/q23 separate NDP from Conservatives on state-vs-market; q38/q48 cut across left-right and stress-test NDP positioning.

## What happens next (M2)

1. Human reviews this doc + `questions.json`.
2. Gate selects ~18, sets their `status` to `frozen` in `questions.json`.
3. Frozen set is the contract for M3 coding (5 parties, 2 coders + adversarial verifier).
