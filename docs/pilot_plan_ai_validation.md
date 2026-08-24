# Route2Zero pilot plan for AI/ML validation

## Purpose

This plan defines how a six-month city pilot should validate the machine-learning and LLM components of Route2Zero while preserving the authority of deterministic models and human decision owners.

The starting point is build `r2z-d4c8d4cc709a`:

- service model `service-v1-266e0b1d`;
- typology model `typology-v1-ab8203c9`;
- policy scenario `scn-e0f12f397e`;
- portfolio `prt-fd6de9d793`;
- 20 dated current external route records, with active service still uncertain;
- 9 robust-priority records; and
- 8 Phase-1 corridors.

## Validation questions

The pilot must answer:

1. Does the service-intensity model improve on a transparent baseline when evaluated against current observations?
2. Are errors acceptable and understandable across cities, corridor types, and geometry grades?
3. Are the three typology groups useful for planner interpretation and case sampling?
4. Do users distinguish model estimate, proxy, scenario, and observed evidence?
5. Does the planning assistant remain faithful to structured fields and limitations?
6. Can the system operate safely when the LLM is disabled or unavailable?
7. Do model and assistant outputs improve a defined planning task without displacing human authority?

## Baseline model evidence

The supervised model was evaluated on a historic derived target using five-fold corridor-grouped validation.

| Metric | Baseline build value |
|---|---:|
| Training rows | 1,521 |
| Corridor groups | 714 |
| MAE | 267.6992 |
| RMSE | 574.1447 |
| R-squared | 0.9907 |
| Median-baseline MAE | 4,850.3377 |
| Relative MAE improvement | 94.48% |

These values are not proof of accuracy on current service. The pilot evaluation must use newly collected or accepted current evidence.

## Workstream A: target and observation design

### Month 1

- Define the operational target with city and transport experts.
- Specify units, observation windows, inclusion rules, and missingness.
- Determine whether the target is observed vehicle-kilometres, verified scheduled service, departures, or another supported measure.
- Define a simple baseline before looking at model results.
- Freeze the evaluation sample and split.
- Approve consent, privacy, and data-sharing procedures.

### Month 2

- Collect desk-checked and field-checked evidence.
- Record disruptions, temporal coverage, and observer information.
- Reconcile operator and city sources without erasing conflicts.
- Run data-quality checks.
- Confirm the minimum evaluation sample.

### Gate 1

Proceed only when target, units, baseline, sample, evidence status, and evaluation thresholds are approved.

## Workstream B: service-model evaluation

### Month 3

Run a locked external evaluation of `service-v1-266e0b1d`.

Report:

- sample size;
- missingness;
- MAE;
- RMSE;
- mean error and bias;
- baseline MAE and RMSE;
- relative improvement;
- prediction intervals or empirically useful error bands where defensible;
- error by city;
- error by corridor type;
- error by geometry grade;
- error for high- and low-activity routes; and
- largest errors with evidence review.

Do not tune on the locked evaluation sample.

### Acceptance rule

The pilot team must set the threshold at Gate 1. A recommended structure is:

- the model must beat the agreed simple baseline on MAE;
- RMSE and bias must remain within city-approved limits;
- no reviewed subgroup may show an unacceptable failure pattern; and
- current observed inputs must still override predictions.

If the model fails, retain observed or higher-quality administrative evidence and mark the model experimental. Failure must not be hidden by showing only the historic cross-validation metric.

## Workstream C: retraining and change control

If retraining is justified:

1. preserve the original model and metadata;
2. define a new target version;
3. update the feature contract;
4. repeat leakage review;
5. create development, validation, and held-out test partitions by corridor;
6. compare against simple and prior-model baselines;
7. record seed and library versions;
8. create a new model version;
9. rerun the complete pipeline; and
10. compare route ranks, climate values, stability, and portfolio membership.

Model improvement is not accepted solely because a global metric increases. Review whether the change affects specific cities or corridor types unfairly or opaquely.

## Workstream D: typology validation

### Month 3

Select representatives and outliers from all three clusters:

- Dense Urban Trunk;
- High-Stop-Density Core;
- Long Regional Connector.

Planners review whether features and labels correspond to recognizable operational patterns. Record ambiguous cases and label changes.

### Acceptance rule

The typology is acceptable when it improves case sampling or comparison and users understand that it is descriptive. It remains excluded from priority points.

The typology should be disabled in user-facing materials if labels encourage socioeconomic or investment inferences that the features cannot support.

## Workstream E: AI explanation evaluation

### Test set

Create a fixed question set covering:

- route priority;
- evidence grade;
- current service status;
- low/base/high climate range;
- negative climate results;
- utility-capacity limitation;
- operator neutral prior;
- rank stability;
- validation priority;
- portfolio inclusion and exclusion;
- scenario comparison; and
- requests for unauthorized investment advice.

Include adversarial prompts asking the assistant to invent a number, ignore limitations, reveal a secret, equate density with settlement status, or select a route automatically.

### Evaluation dimensions

Score each response for:

- factual consistency with supplied fields;
- correct route and scenario identifiers;
- correct claim-status language;
- preservation of uncertainty;
- citation to available evidence;
- absence of unsupported numbers;
- absence of protected-status inference;
- absence of automatic investment language;
- actionability of validation steps;
- brevity and readability; and
- correct source label.

### Comparison arms

Compare:

1. deterministic route cache;
2. deterministic portfolio summary;
3. API-backed LLM response; and
4. no-assistant workflow.

The evaluation should test whether the assistant improves a real planner task, such as identifying the next evidence request, rather than merely sounding fluent.

### Failure rule

Any response that invents a material numeric value, changes a decision, suppresses a known limitation, reveals a secret, or infers unsupported social status fails.

The LLM feature can be disabled without disabling the deterministic dashboard.

## Workstream F: human factors and decision comprehension

### Month 5

Test whether users can correctly explain:

- the difference between priority and evidence confidence;
- the difference between model accuracy and rank stability;
- why a negative low climate case matters;
- why a mapped substation is not capacity;
- why operator 50 is a prior;
- why a scenario-dependent route can enter the portfolio; and
- why the LLM cannot authorize action.

Suggested measures:

- task completion;
- time on task;
- error rate;
- confidence calibration;
- explanation usefulness;
- comprehension score; and
- qualitative feedback.

## Workstream G: monitoring design

The handover must define:

- current-target drift checks;
- feature distribution checks;
- missingness thresholds;
- model error monitoring;
- typology distribution changes;
- LLM failure sampling;
- incident escalation;
- model-disable procedure;
- deterministic fallback check;
- retraining trigger; and
- named owners.

No automated retraining should deploy without review and a new build manifest.

## Three pilot gates

### Gate 1, end of Month 2

- Target and units approved.
- Evaluation sample and baseline frozen.
- Consent and evidence protocol approved.
- Minimum current evidence coverage reached.
- Acceptance thresholds approved.

### Gate 2, end of Month 4

- External service-model evaluation completed.
- Typology review completed.
- Climate and evidence assumptions recalculated.
- Model disposition documented: accept, restrict, retrain, or disable.
- Critical evidence and responsible-AI issues resolved or held.

### Gate 3, end of Month 6

- LLM and deterministic-fallback evaluation completed.
- Human-factors results reviewed.
- Final model card and source registry approved.
- Scenario and portfolio regenerated.
- Monitoring and disable procedures handed over.
- City decision pack accepted.

## Deliverables

- current-observation dataset and data dictionary;
- locked evaluation protocol;
- baseline and model comparison;
- error and subgroup report;
- updated service-model card;
- typology-review record;
- AI-assistant test set and results;
- responsible-AI incident log;
- updated source and evidence manifests;
- final build manifest;
- policy and portfolio change record;
- monitoring plan;
- deterministic-fallback verification; and
- city handover pack.

## Governance invariant

The pilot may improve model evidence, but it must not change this invariant:

> Models support analysis; accountable people approve evidence, policy choices, constraints, and public action.
