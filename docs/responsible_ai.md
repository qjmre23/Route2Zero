# Route2Zero responsible-AI and decision-governance framework

## Purpose

Route2Zero supports public-sector planning under incomplete evidence. Its governance objective is not to remove uncertainty. It is to keep uncertainty, policy choices, source limitations, and human decision rights visible throughout the workflow.

This framework applies to build `r2z-d4c8d4cc709a`, policy scenario `scn-e0f12f397e`, and portfolio scenario `prt-fd6de9d793`.

## Governing statement

Machine learning estimates a limited service-activity field when historic data are incomplete. Deterministic models calculate climate scenarios, evidence confidence, rank stability, validation priorities, and portfolio membership. An optional LLM explains structured outputs. Authorized city and stakeholder teams control policy weights, constraints, interpretation, validation, and implementation decisions.

## Decision rights

Route2Zero may:

- screen historic route records;
- calculate versioned scenario results;
- expose weak or missing evidence;
- compare human-selected policy lenses;
- identify routes whose rank is stable or sensitive;
- identify tested fields that can reverse a decision;
- construct a constrained validation shortlist; and
- generate a structured decision record.

Route2Zero may not:

- authorize procurement or investment;
- cancel, suspend, or award a franchise;
- determine fares or service obligations;
- approve loans or operator eligibility;
- infer individual poverty, tenure, or informal status;
- represent historic service as current;
- represent mapped infrastructure as utility capacity;
- present scenario CO2e as measured reduction;
- allow an LLM to change analytical values; or
- suppress conflicting stakeholder evidence.

## AI component inventory

### Supervised machine learning

The service-intensity model estimates a historic schedule-derived vehicle-kilometre proxy. It is used for one route in the current build. It does not estimate passengers or present service.

### Unsupervised machine learning

The corridor typology groups structural route features. It is interpretive and excluded from the policy score.

### Large language model

The optional LLM receives a bounded question and structured ranked facts. It may write a short explanation but cannot read secrets from the browser, call the score pipeline, change weights, edit source data, or update rank.

### Non-AI analytics

Climate, evidence confidence, policy score, three-mode sensitivity summaries, portfolio selection, and value of information are deterministic or fixed-seed calculations. Calling every analytical stage “AI” would obscure accountability.

## Human control points

Human decision owners must approve:

1. the decision question;
2. data-sharing and consent terms;
3. source acceptance and evidence precedence;
4. current-route validation status;
5. climate and vehicle assumptions;
6. equity and accessibility indicators;
7. policy weights;
8. portfolio constraints;
9. interpretation of conflicts and uncertainty;
10. which corridors proceed to further study; and
11. any external publication or implementation decision.

The interface may make these controls easier to use; it does not transfer authority to the model.

## Source and claim labeling

Every material value should be classifiable as `VERIFIED`, `OBSERVED`, `DERIVED`, `ML_ESTIMATED`, `PROXY`, `SCENARIO`, `NEUTRAL_PRIOR`, or `MISSING`.

The display must also distinguish:

- historic evidence;
- current evidence;
- mixed-currentness map data;
- project scenarios; and
- model versions.

Language must follow the status. A proxy must not be called a measurement. A scenario must not be called an outcome. A prior must not be called readiness.

## Current responsible-use warnings

The present build has:

- 20 dated current external route records with active service still uncertain;
- 1,502 historic-only route records;
- zero observed operator scores;
- zero verified utility-capacity records;
- zero verified charging sites;
- 20 observed OSM member-way geometries, two GTFS shapes, and 1,500 planning approximations;
- population exposure as the only equity dimension; and
- grade C or D evidence for every route.

These conditions prohibit using the current rank as a direct investment list.

## Equity and non-discrimination

WorldPop population exposure is not a protected-class, poverty, vulnerability, tenure, accessibility, or settlement-status dataset. Route2Zero does not infer any of those labels.

The system must not assign individual-level risk or eligibility. Core analytics require no resident personally identifiable information.

During a pilot:

- use aggregate, purpose-limited indicators;
- document the population affected by each indicator choice;
- include rider and community review;
- allow stakeholders to challenge labels and evidence;
- test whether model error or evidence gaps differ by city or corridor type; and
- avoid treating low data availability as low public need.

If a defensible marginalized- or underserved-settlement source is unavailable, that field remains missing. It is not reconstructed from density.

WorldPop is an optional population-exposure layer. If it is unavailable, exposure and dependent equity fields remain null with status `MISSING`; the system must not replace them with zero or interpret absence as low need. The same rule applies to optional OSM charging proximity. Downstream constraints may therefore produce an explicit infeasible portfolio, which is safer than fabricating complete evidence.

## Operator evidence and consent

Operator evidence can concern verified fleet size, depot control, financing, organizational capacity, maintenance capability, willingness to participate, modernization experience, and charging-site access. It can be sensitive even when it is not personal data.

The pilot must:

- obtain informed organizational consent;
- identify the intended decision use;
- limit access to authorized users;
- store source references and verifier identities;
- separate factual records from workshop judgments;
- permit correction and withdrawal where applicable;
- avoid publication of confidential financing or personal information; and
- document how evidence affects scores or status.

All eight configured components must be considered when supplied. Missing components are omitted rather than scored as zero, and a header-only ledger is not evidence. The current neutral prior must remain explicit until sufficient evidence is accepted.

## Model governance

The service model must retain:

- a target definition;
- feature and leakage lists;
- corridor-grouped validation;
- baseline comparison;
- version, seed, and library versions;
- serialized artifact;
- performance metrics;
- anomaly flags; and
- limitations.

Current field observations must be used for external validation before the model is treated as operational. If it fails the agreed threshold, observed evidence takes precedence and the model should be constrained or disabled.

The typology must remain excluded from the policy score. Its labels must be reviewed with planners before they are used in reporting or case sampling.

## LLM governance

### Allowed input

The LLM may receive:

- the user's bounded question;
- route IDs and names;
- already-generated scores and ranks;
- evidence grade and confidence;
- rank-stability fields;
- climate scenario fields;
- portfolio membership;
- validation-priority reasons; and
- standard uncertainty notices.

### Prohibited input

The LLM should not receive:

- secret keys;
- resident personally identifiable information;
- confidential operator data without an approved purpose;
- unreviewed free-text allegations;
- procurement deliberations beyond the authorized scope; or
- unsupported claims presented as facts.

### Prohibited output behavior

The LLM must not:

- invent route facts or citations;
- calculate or revise official scores;
- override evidence status;
- state that a route is active without current evidence;
- turn a climate range into a guaranteed reduction;
- call proximity capacity;
- recommend automatic funding; or
- conceal that deterministic fallback was used.

### Technical controls

- API keys remain server-side in Netlify Functions scope.
- The browser sends a bounded question and bounded fact string.
- Requests have a timeout.
- Non-success responses fall back to deterministic text.
- The response source is labeled.
- The pipeline writes deterministic structured caches independently of the API.
- `llm_ranking_influence` remains false.

### Evaluation

Pilot evaluation should use a fixed question set and score:

- factual consistency with cited fields;
- preservation of claim-status language;
- completeness of key limitations;
- absence of unsupported numeric claims;
- actionability of validation recommendations;
- readability for city users; and
- consistency between API and deterministic fallback.

Any material hallucination or authority overreach is a release blocker for the LLM feature, not for the deterministic dashboard.

## Transparency requirements

Every decision pack should identify:

- build ID and timestamp;
- scenario and portfolio IDs;
- policy weights and constraints;
- model versions;
- source and evidence status;
- current-validation count;
- climate assumption set;
- rank-stability method and seed;
- sensitivity mode (`around_default`, `broad_simplex`, or `custom`) and draw count;
- portfolio method;
- portfolio feasibility status and constraint diagnostics;
- known limitations;
- human decision owner; and
- next validation actions.

The interface should not use dark patterns that hide weak evidence. Method and limitations may be collapsible for usability, but the evidence grade, key warnings, and decision-support disclaimer must remain accessible.

## Challenge and correction process

A stakeholder challenge should record:

1. route or portfolio affected;
2. disputed field;
3. current source and claim status;
4. submitted evidence and permission to use it;
5. reviewer and date;
6. conflict-resolution result;
7. field or configuration change;
8. before-and-after scenario result; and
9. approval or unresolved status.

Corrections must flow through validated ledgers or versioned configuration, followed by a complete rebuild. Processed outputs should not be edited manually.

## Risk register

| Risk | Control |
|---|---|
| Historic service treated as current | Historic-only label, current-validation ledger, publication warning |
| High model metric overstated | Historic target disclosure, current holdout requirement |
| Density treated as vulnerability | Proxy label, null socioeconomic fields, prohibited-claim rule |
| Missing WorldPop treated as zero need | Optional-source state, null values, `MISSING` claim status |
| OSM proximity treated as capacity | Capacity flag remains false until formal evidence |
| Missing OSM replaced with fabricated proximity | Optional-source state and null charging-proximity/readiness fields |
| Operator prior treated as observation | `NEUTRAL_PRIOR` status and low confidence |
| Incomplete operator ledger treated as zero capability | Eight-component completeness, present-weight normalization, explicit prior |
| Negative climate case hidden | Preserve full low/base/high range |
| Stable rank mistaken for readiness | Display evidence grade separately |
| LLM hallucination | Bounded facts, deterministic fallback, source label, no numeric write path |
| Policy preferences hidden in score | Named scenarios, visible weights, human approval |
| Portfolio appears financially optimized | State deterministic selection, no budget constraint, and separate `PROXY`/`MISSING` feasibility fields |
| Portfolio constraints silently relaxed | Explicit infeasible result, empty selection, and constraint diagnostics |
| Rank crossing mistaken for portfolio change | Re-run the shared selector for geometry, service, climate, operator, charging, and equity perturbations |
| Text city tag misassigns corridor | Low-confidence label and boundary-validation task |
| Stakeholder conflict erased | Conflict status, change log, challenge process |

## Release gates

The deterministic system may be released for screening when:

- source and build manifests are complete;
- scores, statuses, and IDs are internally consistent;
- no secret is exposed to the browser;
- limitations are visible;
- optional-source absence is preserved as `MISSING`/null;
- infeasible portfolio scenarios return diagnostics without a fabricated shortlist;
- exports preserve scenario context; and
- tests and the Netlify build complete successfully.

The LLM feature may be enabled only when:

- server-side variables are configured;
- the deterministic fallback is functional;
- the fixed evaluation set passes;
- source labels are visible; and
- no score or source-data write path exists.

Investment use requires additional pilot evidence and institutional approval. A prototype release does not satisfy that gate.

## Accountability

The human decision owner remains accountable for the policy lens and action. Data owners remain accountable for accepted evidence. Model owners remain accountable for target, validation, monitoring, and limitations. Product and governance owners remain accountable for access, explanation, challenge, and change control.

Route2Zero's responsible-AI standard is met when the system helps a city ask better questions without pretending that incomplete evidence has become certainty.
