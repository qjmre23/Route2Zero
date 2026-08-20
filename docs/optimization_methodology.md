# Route2Zero Phase-1 portfolio methodology

## Method classification

Route2Zero uses deterministic evidence-constrained selection. It is not a financial optimizer, mixed-integer program, cost-benefit model, or procurement recommendation.

The current result is portfolio scenario `prt-b73fa05705`, derived from policy scenario `scn-c46e1d86c1` in build `r2z-16690ccbe328`.

## Purpose

A simple top-eight ranking can select opposite directions of the same corridor or concentrate selections in one city. The Phase-1 selector creates a more useful validation portfolio by combining priority, stability, evidence confidence, and explicit coverage constraints.

The output answers:

> Which eight corridor records form a defensible first validation portfolio under the current evidence and constraints?

It does not answer:

- what to procure;
- how many vehicles to buy;
- how much the transition costs;
- which operator should receive finance;
- whether charging is feasible; or
- whether the selected routes are active.

## Input table

The selector reads `data/processed/route2zero_scores.csv` after the default score, city tags, and rank-stability fields have been attached.

Required fields include:

- route ID;
- normalized corridor ID;
- primary city;
- priority score;
- equity score;
- evidence grade and confidence;
- active status;
- top-10 probability;
- robustness label; and
- low, base, and high climate values.

The present primary-city field is a low-confidence text fallback. It must be validated before operational use.

## Objective

Each eligible route receives:

```text
portfolio_objective =
  0.60 x priority_score
  + 0.25 x (top_10_probability x 100)
  + 0.15 x overall_evidence_confidence
```

The objective rewards the chosen policy lens, rank robustness, and evidence quality. Its weights are project configuration choices, not universally optimal values.

## Eligibility filters

The current scenario requires:

- evidence grade C or higher; and
- equity score at least 40.

Routes explicitly marked inactive are excluded. All current active statuses are uncertain, so none are excluded by that condition in this build.

The selector does not require `ROBUST PRIORITY`; scenario-dependent routes can be selected when they improve corridor or city coverage.

## Constraints

| Constraint | Current value | Rationale |
|---|---:|---|
| Maximum corridors | 8 | Manageable Phase-1 validation scope |
| Minimum evidence grade | C | Exclude the weakest current evidence |
| Minimum equity score | 40 | Preserve population-exposure relevance |
| Maximum evidence-limited records | 2 | Limit weak-evidence concentration |
| Maximum records per primary city | 2 | Broaden geographic validation coverage |
| Maximum directions per normalized corridor | 1 | Avoid duplicate directions in the shortlist |
| Exclude inactive routes | Yes | Do not select a route explicitly validated inactive |
| Budget | None | No defensible route-level cost input is available |

The evidence-limited rule currently has no effect because the sensitivity output contains no `EVIDENCE-LIMITED` label. The grade filter nevertheless excludes the three grade-D records.

## Selection algorithm

1. Calculate the objective for all routes.
2. Apply evidence-grade and equity eligibility filters.
3. Remove routes explicitly marked inactive.
4. Sort by objective descending, then priority descending, then route ID ascending.
5. Scan the ordered list.
6. Skip a route when its city limit is reached.
7. Skip a route when its normalized-corridor direction limit is reached.
8. Skip an evidence-limited route when that limit is reached.
9. Accept a route otherwise.
10. Stop after eight acceptances.
11. Fail the scenario if eight routes cannot be selected.

This greedy scan is deterministic for fixed inputs. It does not guarantee a mathematical global optimum under a general objective. The term “optimizer” in code refers to the portfolio-selection stage, not a solver claim.

## Current selected portfolio

| Route ID | Route | Primary city tag | Default rank | Robustness |
|---|---|---|---:|---|
| `LTFRB_PUJ1353` | Francisco Homes - Cubao | San Jose del Monte | 1 | Robust priority |
| `LTFRB_PUJ1241` | Dasmarinas Resettlement Area - Baclaran via Coastal Rd. | Pasay | 2 | Robust priority |
| `LTFRB_PUJ2083` | Baclaran - Dasmarinas B Bayan | Dasmarinas | 3 | Robust priority |
| `LTFRB_PUJ1156` | Binangonan - Pasig (TP) | Binan | 6 | Robust priority |
| `LTFRB_PUJ1638` | EDSA/Shaw Central - Morong via Antipolo, Theresa | Mandaluyong | 9 | Robust priority |
| `LTFRB_PUJ1350` | Francisco Homes - Philcoa | San Jose del Monte | 10 | Scenario-dependent |
| `LTFRB_PUJ1153` | Binangonan - JRC via Angono | Mandaluyong | 11 | Scenario-dependent |
| `LTFRB_PUJ1405` | Bagong Silang - Philcoa via Commonwealth Ave., Maligaya Park | Caloocan | 17 | Scenario-dependent |

The city tags above are produced by text matching and require local review. They are reported exactly as the build uses them.

## Difference from simple top eight

The simple top-eight route IDs are:

```text
LTFRB_PUJ1353
LTFRB_PUJ1241
LTFRB_PUJ2083
LTFRB_PUJ1352
LTFRB_PUJ1240
LTFRB_PUJ1156
LTFRB_PUJ2084
LTFRB_PUJ1157
```

The constrained selector removes:

```text
LTFRB_PUJ1157
LTFRB_PUJ1240
LTFRB_PUJ1352
LTFRB_PUJ2084
```

It adds:

```text
LTFRB_PUJ1153
LTFRB_PUJ1350
LTFRB_PUJ1405
LTFRB_PUJ1638
```

The change is driven by the city and normalized-corridor limits, not by manual route substitution.

## Portfolio summaries

| Summary | Current value |
|---|---:|
| Selected corridors | 8 |
| Average equity score | 73.9 |
| Average evidence confidence | 37.8 |
| Evidence-grade distribution | 8 grade C |
| Low climate scenario | -8,190.9 tCO2e/year |
| Base climate scenario | 2,710.9 tCO2e/year |
| High climate scenario | 22,288.0 tCO2e/year |

The low negative result is retained. All climate values are scenarios, not measured results.

## City distribution

The current text-derived primary-city distribution is:

- San Jose del Monte: 2;
- Mandaluyong: 2;
- Pasay: 1;
- Dasmarinas: 1;
- Binan: 1; and
- Caloocan: 1.

This distribution should be recalculated after a boundary-based city adapter or local validation is supplied.

## No budget claim

`hypothetical_budget_php` is null and `hypothetical_budget_used` is false. Route2Zero has no verified vehicle, charging, depot, civil-works, financing, operating-cost, or lifecycle-cost input by corridor.

Adding an arbitrary budget would create false precision. A future budget constraint requires:

- unit definition;
- cost base year and currency;
- fleet quantity method;
- vehicle specification;
- charging and grid-scope definition;
- depot and site costs;
- financing assumptions;
- uncertainty range;
- source and verifier; and
- treatment of shared infrastructure.

## Scenario governance

Every scenario change should record:

- title and decision question;
- constraint value;
- unit;
- source or policy rationale;
- owner;
- approval date;
- affected routes;
- feasibility result;
- comparison with the prior portfolio; and
- unresolved limitations.

The scenario ID changes when its source policy scenario, constraints, or selected route IDs change.

## Feasibility failure

If the algorithm cannot select the required number of routes, it raises an error rather than silently relaxing constraints. The decision owner must then identify the conflicting constraints and approve a revised scenario.

An infeasible result is useful evidence. The system must not manufacture a portfolio to preserve a presentation claim.

## Sensitivity and value of information

Rank stability enters the portfolio objective through top-10 probability. Evidence confidence enters directly at 15%. Value-of-information results do not enter the selection objective; they guide what to validate after selection.

During a pilot, compare portfolio membership before and after current evidence is added. Record routes that enter or leave and which evidence or constraint caused the change.

## Limitations

- The algorithm is greedy, not globally optimized.
- The objective weights are policy choices.
- Current evidence is grade C or D only.
- City tags are low-confidence text fallbacks.
- Normalized corridor IDs are name-based.
- Equity is population exposure only.
- No route is currently confirmed active.
- No operator evidence is observed.
- No charging capacity is verified.
- Climate inputs are scenarios.
- No budget or cost constraint exists.

These limitations make the result appropriate for validation planning, not implementation authorization.

## Pilot acceptance test

The portfolio method is accepted for city use only when:

1. city and corridor tags are validated;
2. selected routes have current status evidence;
3. evidence and climate fields are recalculated;
4. decision owners approve objective and constraints;
5. scenario changes are reproducible;
6. infeasibility is handled transparently;
7. users can explain why constrained selection differs from top-N; and
8. the output is explicitly labeled as a validation or planning portfolio.
