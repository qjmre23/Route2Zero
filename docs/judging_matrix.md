# Route2Zero judging evidence matrix

## Use of this matrix

This matrix maps the Route2Zero implementation to the published judging areas of Relevance, Innovation, Impact, Presentation, Feasibility, and Viability. No numerical weights are assumed because none are encoded in the repository evidence used for this submission.

The evidence anchor is build `r2z-a7181752a17d`, scenario `scn-e0f12f397e`, and portfolio `prt-fd6de9d793`.

## Build facts

| Fact | Evidence |
|---|---|
| Route universe | 1,522 PUJ route-direction records |
| Complete scores | 1,522 |
| Dated external map records | 20; active service remains uncertain |
| Usable source geometries | 22: 20 OSM relations + 2 GTFS shapes |
| Robust priorities | 9 |
| Phase-1 corridors | 8 |
| Service model | Histogram gradient boosting, version `service-v1-266e0b1d` |
| Model validation | Grouped five-fold, MAE 267.6992, baseline MAE 4,850.3377 |
| Typology | Three overlapping descriptive groups, silhouette 0.3730; excluded from policy score |
| Sensitivity | 5,000 fixed-seed policy-weight scenarios |
| Portfolio climate range | -8,190.9 to 22,288.0 tCO2e/year |
| Evidence distribution | 1,519 grade C; 3 grade D |

## 1. Relevance

### Claim

Route2Zero addresses the urban-transportation focus area by helping city and transport partners decide where limited e-jeepney transition validation should begin.

### Implemented evidence

- The screening universe covers 1,522 historic Metro Manila and nearby PUJ route-direction records.
- The decision unit is a transport corridor record, not a generic city score.
- The workflow integrates service, climate, equity exposure, charging, operator, evidence, and city-coverage considerations.
- The Phase-1 output is an eight-corridor validation portfolio.
- The system identifies current evidence gaps instead of treating the historic feed as current.
- A city adapter and six-month validation protocol are documented.

### Responsible limitation

The current build has 20 reviewed, dated OSM route records and observed member-way geometries, but no record is field-confirmed active. Relevance to an actual city decision must still be confirmed through city pairing, operator engagement, utility evidence, and field validation.

Route2Zero does not claim the Informal or Marginalized Settlements focus area from WorldPop density. A defensible settlement or underserved-area source would be required.

### Judge verification path

1. Open the build summary.
2. Confirm 1,522 historic records and 20 dated external map records with active status uncertain.
3. Open the flagship evidence card.
4. Inspect its source statuses and validation queue.
5. Review the pilot protocol.

## 2. Innovation

### Claim

Route2Zero's innovation is a hybrid planning workflow: machine learning for limited data completion and typology; deterministic climate and evidence models; fixed-seed uncertainty analysis; decision-sensitive evidence prioritization; constrained portfolio construction; and an explanation layer that cannot change the decision.

### Implemented evidence

- A supervised service model uses grouped validation and explicit leakage exclusions.
- The model is used only for one missing historic service input in the current build.
- An unsupervised typology identifies three structural corridor types; typology remains descriptive and outside the policy score.
- Low, base, and high climate-and-energy scenarios preserve negative results.
- Evidence confidence is separate from priority and rank stability.
- Monte Carlo analysis records top-k frequency and P10-P90 rank ranges.
- Value-of-information output tests six evidence fields for rank swing and portfolio flips.
- Deterministic selection differs from simple top-N by four routes.
- Structured planning explanations cite route fields and retain deterministic fallback.

### Responsible limitation

The service model predicts a historic derived target, not current demand. The portfolio selector is a deterministic greedy scan, not a mathematical or financial optimizer. The LLM is an explanation interface, not the source of innovation or authority.

### Judge verification path

1. Inspect `model_metrics.json`.
2. Confirm leakage exclusions and corridor-grouped validation.
3. Compare default rank with sensitivity fields.
4. Compare simple top eight with the selected portfolio.
5. Confirm `llm_ranking_influence = false`.

## 3. Impact

### Claim

Route2Zero helps a city focus expensive validation and planning work on corridors with stronger combined climate, equity-exposure, infrastructure, and operator signals while exposing conditions that could reverse the result.

### Implemented evidence

- Climate results include energy demand and net CO2e under three explicit cases.
- The Phase-1 portfolio has low/base/high results of -8,190.9, 2,710.9, and 22,288.0 tCO2e/year.
- The negative low case demonstrates that electrification is not automatically beneficial under every grid and vehicle assumption.
- The selected portfolio's average population-exposure equity score is 73.9.
- Value-of-information output turns uncertainty into a route-field validation queue.
- City and corridor limits broaden the validation portfolio beyond a simple top-eight list.

### Responsible limitation

Climate figures are scenarios, not measured avoided emissions. Equity is population exposure only. No vehicle transition, charger installation, service improvement, or real emissions reduction has occurred through this prototype.

### Judge verification path

1. Inspect the flagship low/base/high climate values.
2. Inspect the portfolio range and assumption set.
3. Confirm the equity limitation.
4. Open the validation actions.
5. Review success metrics that distinguish scenario outcomes from actual deployment impact.

## 4. Presentation

### Claim

The dashboard presents one decision story across network, route, evidence, uncertainty, portfolio, and export views, with a responsive Mapbox map and a concise demonstration path.

### Implemented evidence

- Production hosting is configured for Netlify.
- The live application is linked from the repository.
- The selected route can request a street-following Mapbox Directions path.
- Data and decision sections are responsive.
- Exports preserve scenario context and caveats.
- Supporting method content is available without dominating the primary workflow.
- The live demo script is designed for less than 90 seconds.

### Responsible limitation

A street-following line improves readability but does not verify the official or operated route. Submission screenshots and reports are tied to the identified build and its evidence state.

### Judge verification path

1. Open the live application.
2. select a Phase-1 route;
3. confirm map, evidence, and robustness fields;
4. switch to the portfolio; and
5. export the decision record.

## 5. Feasibility

### Claim

Route2Zero is feasible as a six-month city validation workflow because its principal data gaps, owners, gates, and fallbacks are explicit.

### Implemented evidence

- A four-ledger pilot evidence structure is present.
- A six-month protocol defines route, model, climate, equity, charging, operator, and governance work.
- Three acceptance gates prevent unsupported progress.
- Current route evidence overrides historic and model-estimated inputs.
- The deterministic dashboard remains functional when the LLM API is unavailable.
- The portfolio selector fails rather than silently relaxing infeasible constraints.
- The city adapter documents what must be recalibrated.
- Netlify hosts the static dashboard without a persistent Python server.

### Responsible limitation

No city partnership, operator evidence, utility confirmation, or current field sample is recorded in the current build. Feasibility is therefore a documented pilot plan, not demonstrated deployment readiness.

### Judge verification path

1. Review the baseline warnings.
2. Review Months 1-6 and three gates.
3. Inspect fallback behavior.
4. Inspect validated ledger schemas.
5. Confirm no secret key enters browser configuration.

## 6. Viability

### Claim

Route2Zero can be maintained and transferred because sources, configurations, models, scenarios, outputs, and releases are versioned and checksummed.

### Implemented evidence

- `source_manifest.json` records six sources and checksums.
- `build_manifest.json` records config, source, and output checksums.
- Model versions and random seeds are recorded.
- Scenario and portfolio IDs are deterministic.
- The pipeline is ordered and rerunnable.
- Raw data are preserved separately from validated and processed data.
- The static dashboard has a reproducible Netlify build.
- The adapter guide defines local calibration rather than claiming universal transfer.
- The handover package includes a refresh and retraining runbook requirement.

### Responsible limitation

The current manifest records analytical source commit `851fab135b3ac0e66548475b124d4b923a191077`, together with source, configuration, model, scenario, and output checksums.

An order-of-magnitude fleet and capital screen is present, but every value is `PROXY`, financing is `MISSING`, and major depot, grid, operating, and finance costs are excluded. Financial viability still requires verified fleet, charging, depot, tariff, and financing inputs during the pilot.

### Judge verification path

1. Open the build manifest.
2. inspect source and config checksums;
3. confirm model and scenario versions;
4. run the pipeline and Netlify build; and
5. compare generated IDs and warnings.

## Cross-criterion responsible-claims audit

| Prohibited claim | Current safeguard |
|---|---|
| Historic GTFS equals active 2026 service | All records marked historic-only and uncertain |
| Population density equals informal settlement | Equity explicitly labeled population-exposure proxy |
| Substation proximity equals capacity | Capacity flag remains false |
| Operator 50 equals observed readiness | `NEUTRAL_PRIOR` status |
| ML service intensity equals passenger demand | Historic vehicle-kilometre target disclosure |
| Scenario CO2e equals measured reduction | `SCENARIO` status and full range |
| Stable rank equals strong evidence | Evidence and stability displayed separately |
| LLM decides priority | No numeric write path; `llm_ranking_influence = false` |
| Portfolio is financially optimized | No budget; deterministic-selection label |
| Mapbox path equals franchise geometry | Planning-visualization warning |

## Submission consistency checklist

Before submission, confirm that the website, Concept, Demonstration, Pilot Plan, README, and technical reference all use:

- build `r2z-a7181752a17d` or a clearly identified later rebuild;
- scenario `scn-e0f12f397e` or a clearly identified replacement;
- portfolio `prt-fd6de9d793` or a clearly identified replacement;
- 1,522 records;
- 20 dated external map records, with active service still uncertain;
- 9 robust priorities;
- 8 Phase-1 corridors;
- the 40/30/15/15 policy lens;
- the full negative-to-positive climate range;
- the current evidence and operator limitations; and
- a consistent boundary between ML, deterministic analytics, LLM explanation, and human authority.

Published descriptions use the scores, weights, evidence state, and language of the identified build.
