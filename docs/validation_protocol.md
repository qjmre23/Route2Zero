# Route2Zero city-pilot validation protocol

## Objective

The protocol converts build `r2z-d4c8d4cc709a` from a historic screening baseline into a locally reviewed decision workflow. It defines the minimum evidence needed to validate route status, service intensity, geometry, climate assumptions, equity indicators, charging feasibility, operator readiness, model behavior, rank stability, and portfolio constraints.

The protocol does not authorize procurement. It produces an evidence-backed Phase-1 shortlist and an explicit list of unresolved questions.

## Baseline state

At pilot start:

| Field | Baseline |
|---|---:|
| Route-direction records | 1,522 |
| Current route validations | 0 |
| Historic-only service status | 1,522 |
| Active status uncertain | 1,522 |
| Observed operator scores | 0 |
| Verified utility-capacity records | 0 |
| Verified charging sites | 0 |
| Dated current OSM route records | 20; active status uncertain |
| Ordered-stop geometries requiring validation | 1,500 |
| Evidence grade C | 1,519 |
| Evidence grade D | 3 |
| Robust priorities | 9 |
| Phase-1 selected corridors | 8 |

This baseline is a starting condition, not a defect to conceal.

## Pilot sample

The pilot should select:

- the eight corridors in portfolio `prt-fd6de9d793`;
- the build-selected flagship `LTFRB_PUJ1353`;
- at least one typology representative from each cluster;
- at least one typology outlier;
- at least one grade-D or otherwise evidence-limited comparison route where practical;
- relevant opposite-direction records; and
- a limited control sample outside the selected portfolio.

Sampling should be agreed with the city and operators. It should not be changed after observing results without a documented reason.

## Evidence levels

### `historic_only`

No accepted current evidence. This is the present default.

### `desk_checked`

At least two current sources have been reviewed, their dates and conflicts are recorded, and a named reviewer has signed the record.

### `operator_confirmed`

An authorized operator or cooperative confirms the relevant service or operational field, with consent and source reference.

### `lgu_confirmed`

An authorized city or transport-agency counterpart confirms the field or accepts the evidence record.

### `field_checked`

A dated observation follows the approved method and is independently reviewed.

### `conflicting_evidence`

Current sources disagree materially. The conflict remains visible until resolved.

These levels communicate evidence process, not general truth. A field can still be incomplete at a higher level.

## Route-validation ledger

Each route record should include:

- route ID and displayed name;
- observed origin and destination;
- validation status;
- active, inactive, suspended, or uncertain status;
- observation date and time window;
- validator and organization;
- source type and reference;
- observed headway;
- observed service window;
- geometry-verification flag;
- verified operator name where consent permits;
- evidence-quality assessment;
- conflict notes; and
- follow-up owner.

Route IDs must remain stable. If the current operator or route designation differs, record the relationship rather than overwriting the historic identifier.

## Service observation

### Minimum method

1. Select representative weekday periods with the city and operator.
2. Record location, date, weather, disruptions, and observer.
3. Count vehicle passages or departures using a fixed rule.
4. Record at least the observation window and number of intervals.
5. Calculate observed headway with exclusions documented.
6. Record the known or observed service-day window.
7. Repeat where temporal variation is expected.
8. Reconcile field observations with operator and administrative evidence.

### Output

The pilot should create an observed service-intensity target appropriate to the available data. It may be observed vehicle-kilometres, verified scheduled service, or a carefully documented proxy. The target must not be silently relabeled as passenger demand.

### Quality checks

- Timestamp and location are present.
- Observation duration is sufficient for the intended claim.
- Missing or disrupted periods are recorded.
- Units are consistent.
- Duplicate observations are reconciled.
- Reviewer approval is present.
- Historic and current values remain separate.

## Geometry validation

For each pilot corridor:

1. compare the historic representative-trip line with current documents;
2. confirm origin, destination, key waypoints, terminals, and directional differences;
3. capture a field trace or accepted official line where permitted;
4. record deviations from the Mapbox planning path;
5. retain both historic and validated geometry with source status; and
6. mark geometry verified only after named review.

A Mapbox Directions result is not sufficient verification. It identifies a drivable connection between screening coordinates, not necessarily the operated or franchised alignment.

## Operator evidence

Operator evidence collection requires consent and purpose limitation.

The ledger may include:

- verified fleet size;
- depot control;
- financing readiness;
- organizational capacity;
- maintenance capability;
- willingness to participate;
- modernization experience;
- charging-site access;
- evidence date;
- source reference; and
- verifier.

At least three supported components are required before Route2Zero replaces the neutral prior. Absent evidence remains a prior; refusal or inability to share is not scored as low readiness.

## Charging and utility evidence

Mapped proximity is the starting point, not the validation result.

For each candidate site or depot, seek:

- site identity and coordinates;
- ownership or control status;
- current electrical service;
- available capacity only when formally supplied;
- relevant feeder or substation evidence;
- proposed charger type and power;
- simultaneity and charging schedule;
- interconnection-study requirement;
- tariff and connection questions;
- resilience and safety considerations;
- utility or qualified reviewer;
- source date and reference; and
- unresolved study requirements.

`utility_capacity_verified` may be true only when the accepted evidence supports that field. Nearby infrastructure alone never sets it true.

## Climate calibration

The pilot must review:

- diesel vehicle efficiency;
- diesel emissions factor;
- electric vehicle energy use;
- charger efficiency;
- operating days;
- electrification share;
- electricity emissions factor;
- service intensity; and
- whether rebound, deadheading, or depot movements are material.

Retain low, base, and high cases. The low case in the current build is negative for every route. Do not remove it merely because it is unfavorable.

The pilot should report the range and the assumptions that drive sign changes. Real avoided emissions may be claimed only after actual deployment and an accepted monitoring baseline.

## Equity and accessibility validation

WorldPop exposure is the present proxy. The pilot should determine which local evidence can supplement or replace it, such as:

- travel-time accessibility;
- essential-destination access;
- service alternatives;
- affordability;
- disability access;
- gender and safety considerations;
- barangay-level socioeconomic indicators with lawful use;
- community-identified service gaps; and
- validated underserved-area sources.

Do not infer informal-settlement status from density. Do not use resident PII for the core route screen. Community review should be able to challenge both data and interpretation.

## Service-model validation

### External test

Evaluate `service-v1-266e0b1d` against the new observed target without training on the evaluation records.

Report:

- evaluation sample size;
- target definition and units;
- MAE;
- RMSE;
- bias;
- simple-baseline result;
- relative improvement;
- error by city;
- error by corridor type;
- error by geometry grade;
- outliers; and
- missingness.

### Decision rule

The city and model owner must agree a threshold before reviewing final results. If the model does not beat the agreed baseline or shows unacceptable subgroup error, current observations and higher-quality evidence take precedence. The model should be retrained, restricted, or disabled.

The historic grouped-validation R-squared of 0.9911 is not the acceptance threshold for current operations.

## Typology validation

Review representatives and outliers from all three clusters. Ask whether the labels are understandable and operationally useful. Record misclassified or ambiguous cases.

Typology acceptance affects only interpretive use and sampling. It does not alter the priority score.

## Evidence-confidence validation

Review whether the deterministic evidence score responds appropriately when a record moves from historic-only to desk checked, operator confirmed, LGU confirmed, or field checked.

Check that:

- grades do not overstate weak evidence;
- missing fields remain visible;
- operator refusal is not scored as low readiness;
- current verification changes the intended component only;
- conflicts lower or qualify confidence; and
- users can distinguish evidence confidence from rank stability.

## Policy and sensitivity workshops

At least one workshop should:

1. define the decision question;
2. review component definitions;
3. reject unsupported indicators;
4. compare named policy scenarios;
5. agree weights or a scenario set;
6. inspect rank P10-P90 and top-10 frequency;
7. record stakeholder disagreements; and
8. approve the scenario record.

The workshop output must identify the decision owner, date, attendees, weights, rationale, and unresolved issues.

## Portfolio-constraint validation

Review each present constraint:

- maximum eight corridors;
- evidence grade C minimum;
- equity score 40 minimum;
- maximum two evidence-limited corridors;
- maximum two per primary city;
- maximum one direction per normalized corridor; and
- inactive-route exclusion.

Confirm whether the city tag and normalized corridor are correct before relying on those constraints. Add cost or budget only when defensible route-level inputs exist. Record every added constraint, unit, source, and rationale.

## Planning-assistant validation

Use a fixed set of questions covering:

- flagship route status;
- evidence gaps;
- climate range;
- utility limitations;
- operator prior;
- rank stability;
- portfolio inclusion; and
- scenario comparison.

Score responses for field consistency, correct status language, limitation coverage, absence of invented facts, and actionability. Compare API output with deterministic fallback. Any hallucinated numeric value or automatic investment instruction is a failure.

## Six-month gate structure

### Gate 1: end of Month 2

Required:

- pilot charter and decision question approved;
- route sample fixed;
- consent and governance approved;
- minimum current evidence coverage reached;
- model-validation target defined;
- climate assumptions to test documented; and
- unresolved ethical or sharing issues assigned.

### Gate 2: end of Month 4

Required:

- route and geometry evidence reviewed;
- external model evaluation completed;
- climate and energy cases calibrated;
- charging and operator evidence cards produced;
- equity indicators reviewed;
- evidence grades recalculated; and
- critical unresolved routes held or labeled.

### Gate 3: end of Month 6

Required:

- policy scenarios approved;
- portfolio constraints accepted;
- final scenario and portfolio regenerated;
- decision pack accepted;
- model card and source registry updated;
- open issues have named owners;
- city analysts receive the refresh process; and
- handover is documented.

## Success metrics

Minimum reporting should include:

- percentage of pilot routes ground checked;
- percentage with complete evidence cards;
- number and type of validation interactions;
- model MAE/RMSE and baseline comparison on current observations;
- percentage of evidence grades improved;
- stability before and after validation;
- number of decision-sensitive gaps resolved;
- planner task-completion rate;
- planner comprehension of priority, evidence, and stability;
- one accepted decision pack; and
- one completed reproducibility handover.

Optional scenario metrics include calibrated portfolio CO2e and energy ranges. Do not report actual emissions avoided unless electrification occurs and an accepted monitoring method is used.

## Rebuild and approval

Accepted evidence must enter `data/validated/` or versioned configuration. Run the complete pipeline, automated checks, and Netlify build. Compare the new build with `r2z-d4c8d4cc709a` for:

- changed sources and checksums;
- validation statuses;
- model metrics;
- priority scores;
- evidence grades;
- stability labels;
- validation priorities;
- portfolio membership; and
- climate ranges.

The final record must state who approved the change and which decision it supports.
