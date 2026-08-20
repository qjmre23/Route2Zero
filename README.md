# Route2Zero

Route2Zero is an AI/ML-assisted electrification planning system for Metro Manila jeepney corridors. It combines service intelligence, climate scenarios, equity exposure, charging and operator evidence, uncertainty analysis, and constrained portfolio selection in one auditable decision workflow.

[Live application](https://route2zero.netlify.app/) | [GitHub repository](https://github.com/qjmre23/Route2Zero)

Route2Zero is designed for transport agencies, local governments, operators, utilities, finance partners, and community stakeholders deciding where limited validation and planning capacity should be used first. It is not a rider trip planner, a franchise decision engine, or an investment authorization system.

## Release snapshot

The repository-facing documentation is anchored to the following reproducible output set.

| Release field | Recorded value |
|---|---|
| Pipeline version | `2.0.0` |
| Build ID | `r2z-45c4ba076af9` |
| Build timestamp | `2026-08-20T06:25:29Z` |
| Default policy scenario | `scn-e0f12f397e` |
| Phase-1 portfolio scenario | `prt-fd6de9d793` |
| Route-direction records | 1,522 |
| Complete priority scores | 1,522 |
| Current route validations | 0 |
| Robust-priority records | 9 |
| Phase-1 selected corridors | 8 |
| Pipeline status | `PASS_WITH_WARNINGS` |

The warnings are substantive. The service network is based on a historic 2013-2020 GTFS feed; no current route-validation record has yet been supplied; no consent-based operator evidence has been supplied; and no utility capacity or charging site has been verified. The current outputs are therefore a screening and evidence-acquisition baseline, not proof of present operations or implementation readiness.

## Decision question

Route2Zero asks:

> Which corridors should a city validate and prioritize first, how robust is that recommendation to changing policy weights, and what missing evidence could reverse the decision?

The system returns more than a ranked list. Each route carries:

- a human-controlled priority score;
- a separate evidence-confidence grade;
- a low, base, and high climate-and-energy scenario;
- a Monte Carlo rank-stability result;
- a corridor typology and anomaly flags;
- a value-of-information queue for missing evidence;
- Phase-1 portfolio membership and exclusion reasons; and
- a structured planning explanation grounded in generated fields.

## What Route2Zero 2.0 adds

Route2Zero 2.0 replaces the original four-proxy MVP story with a broader evidence-aware planning pipeline.

1. A leakage-aware service-intensity model estimates the historic schedule-derived vehicle-kilometre proxy only when that historic input is missing.
2. An unsupervised typology groups structurally similar corridors for interpretation; typology never adds hidden policy points.
3. A deterministic climate engine reports low, base, and high energy and CO2e scenarios.
4. Equity remains explicitly limited to WorldPop population exposure because no validated socioeconomic or marginalized-settlement layer is present.
5. Charging readiness combines mapped-infrastructure proximity with energy-demand screening, while keeping utility capacity and site control unverified.
6. Operator readiness uses consent-based evidence when sufficient fields exist and otherwise retains a visible neutral prior.
7. Evidence confidence is calculated separately from priority, prediction error, and rank stability.
8. Fixed-seed Monte Carlo analysis tests whether a recommendation survives plausible policy-weight changes.
9. Deterministic value-of-information analysis estimates which missing field can move rank or portfolio membership.
10. An evidence-constrained Phase-1 selector creates a diverse eight-corridor validation portfolio without inventing a budget.
11. The planning assistant explains structured outputs but cannot change scores, constraints, climate values, or ranks.

## How to read a Route2Zero result

Four concepts must remain separate.

| Concept | Meaning |
|---|---|
| Priority score | Weighted policy result under a named scenario |
| Evidence confidence | Strength, specificity, completeness, and external validation of the underlying evidence |
| ML prediction uncertainty | Error and residual behavior of the service-intensity model |
| Rank stability | Frequency and range of rank outcomes across tested policy weights |

A high priority with grade C evidence is a reason to validate, not a reason to procure. A stable rank does not make historic data current. A good cross-validation metric does not establish 2026 service. A mapped substation does not establish feeder capacity.

### Claim-status vocabulary

Every important field is intended to be understood through one of these statuses:

| Status | Interpretation |
|---|---|
| `VERIFIED` | Checked against an accepted external or field source |
| `OBSERVED` | Directly recorded for the pilot, subject to the stated protocol |
| `DERIVED` | Calculated deterministically from identified inputs |
| `ML_ESTIMATED` | Produced by a versioned machine-learning model |
| `PROXY` | Indirect screening evidence with a known conceptual limitation |
| `SCENARIO` | Conditional result under explicit assumptions |
| `NEUTRAL_PRIOR` | Deliberate midpoint used because sufficient evidence is absent |
| `MISSING` | No defensible value is available |

`historic`, `current`, `scenario`, and `mixed` describe source currentness. They do not replace the claim-status vocabulary.

## Current policy model

The default scenario is titled `Climate + Equity` and uses the following human-controlled weights:

```text
Priority =
  0.40 x climate_impact_score
  + 0.30 x equity_score
  + 0.15 x charging_readiness_score
  + 0.15 x operator_effective_score
```

The generated scenario ID is `scn-e0f12f397e`. The score is deterministic once the component values and weights are fixed. Machine learning can supply one service-activity input when the historic schedule proxy is missing; the LLM never supplies a numeric input.

Named policy presets in `config/policy_model.json` include climate-and-equity, equity-first, and infrastructure-first lenses. These are comparison lenses, not endorsed policy decisions. A city should approve and document its own weights during the pilot.

## Machine-learning models

### Service-intensity model

The selected model is a histogram gradient-boosting regressor, version `service-v1-266e0b1d`.

| Metric | Recorded grouped cross-validation result |
|---|---:|
| Training rows | 1,521 |
| Normalized corridor groups | 714 |
| Validation design | Five-fold `GroupKFold` by corridor |
| MAE | 266.4485 |
| RMSE | 562.7990 |
| R-squared | 0.9911 |
| Median-baseline MAE | 4,850.0728 |
| Relative MAE improvement | 94.51% |

The target is `historic_daily_vehicle_km_proxy`, derived from the historic schedule. It is not passenger demand, ridership, revenue, or a current service measurement. Leakage fields such as headway, trips per day, climate impact, and final rank are excluded from the model features.

The historic service proxy is available for 1,521 routes. The model is used for one route, `LTFRB_PUJ2451`, because that historic proxy is missing. Validated present-day observations must override both historic and model-estimated service inputs during a pilot.

### Corridor typology

The typology model is version `typology-v1-f9da2ebe`. It applies median imputation, standardization, and K-means clustering. Four clusters were selected because they met the minimum-cluster-size rule and produced a silhouette score of 0.2700.

| Corridor type | Route count |
|---|---:|
| Dense Urban Trunk | 265 |
| High-Stop-Density Core | 620 |
| Local Feeder | 134 |
| Long Regional Connector | 503 |

Typology describes structural similarity. It does not infer socioeconomic status, vulnerability, settlement type, demand, or investment value, and it is not included in the policy score.

## Climate and energy scenarios

The climate engine converts the selected daily vehicle-kilometre input into low, base, and high electrification cases. It calculates electrified vehicle-kilometres, diesel litres displaced, electricity demand, baseline diesel CO2e, grid CO2e, and net scenario CO2e.

The assumptions are stored in `config/climate_scenarios.json` and must be calibrated before investment use. The low case is deliberately conservative and produces negative net CO2e for all 1,522 records under its current efficiency, grid, and electrification assumptions. The base and high cases are positive across the current route universe. This is evidence that the result depends on technology and grid assumptions; it is not a prediction of guaranteed savings.

The selected eight-corridor Phase-1 portfolio has the following scenario range:

| Case | Portfolio result |
|---|---:|
| Low | -8,190.9 tCO2e/year |
| Base | 2,710.9 tCO2e/year |
| High | 22,288.0 tCO2e/year |

These are planning scenarios, not measured reductions, credited emissions, or a project baseline suitable for finance.

## Evidence confidence and validation state

All 1,522 records currently have `validation_status = historic_only` and `active_status = uncertain`.

- 1,519 routes have evidence grade C.
- 3 routes have evidence grade D.
- Evidence confidence ranges from 33.01 to 43.02 in the current build.
- All operator scores are neutral priors of 50 because the operator ledger is empty.
- All charging scores are proxies; utility capacity and site control are unverified.
- All equity scores are population-exposure proxies.
- Two geometries use GTFS shapes; 1,520 use ordered-stop approximations and require validation.

The evidence grade is not a probability that the recommendation is correct. It is a deterministic audit score over freshness, directness, spatial specificity, completeness, external validation, and model reliability.

## Rank stability

The sensitivity stage draws 5,000 fixed-seed policy-weight vectors around the default lens using a Dirichlet distribution. It records top-5, top-10, and top-20 frequency; median rank; P10-P90 rank and score ranges; and a derived stability score.

The current build contains:

- 9 `ROBUST PRIORITY` records;
- 1,183 `SCENARIO-DEPENDENT` records; and
- 330 `LOW-PRIORITY ROBUST` records.

The label describes behavior across tested policy weights. It does not correct weak evidence or make a route operationally ready.

## Phase-1 portfolio

Portfolio scenario `prt-fd6de9d793` is an evidence-validation shortlist, not a procurement portfolio. It uses deterministic selection with these constraints:

- maximum eight corridors;
- minimum evidence grade C;
- minimum equity score 40;
- maximum two evidence-limited corridors;
- maximum two corridors per primary city;
- maximum one route direction per normalized corridor; and
- exclusion of routes explicitly marked inactive.

No budget is used because no defensible cost or fleet dataset has been supplied. The selector differs from a simple top-eight ranking: four records are removed and four are added to satisfy corridor and city-coverage constraints.

The selected route IDs are:

```text
LTFRB_PUJ1353
LTFRB_PUJ1241
LTFRB_PUJ2083
LTFRB_PUJ1156
LTFRB_PUJ1638
LTFRB_PUJ1153
LTFRB_PUJ1350
LTFRB_PUJ1405
```

The selected portfolio has an average equity score of 73.9 and average evidence confidence of 37.8. All eight selected routes have grade C evidence. These values support a validation plan; they do not establish feasibility.

## Flagship corridor

The build-selected flagship is `LTFRB_PUJ1353`, Francisco Homes - Cubao.

| Field | Build value |
|---|---:|
| Default rank | 1 |
| Priority score | 79.07 |
| Evidence grade | C |
| Evidence confidence | 38.34 |
| Top-10 frequency | 100% |
| Low climate scenario | -1,111.8 tCO2e/year |
| High climate scenario | 3,025.3 tCO2e/year |

It is selected by a recorded rule: among Phase-1 corridors, prefer robust-priority records, then higher evidence confidence, priority score, and stable route ID. Its leading position is not manually forced and should be recomputed whenever evidence or configuration changes.

## Repository structure

```text
Route2Zero/
|-- app/                         Legacy Streamlit analytical view
|-- config/                      Versioned model, policy, evidence, and scenario contracts
|-- data/
|   |-- raw/                     Immutable source snapshots
|   |-- validated/               Pilot evidence ledgers; currently header-only
|   `-- processed/               Generated route, model, scenario, and manifest outputs
|-- docs/                        Method, governance, validation, and city-adaptation references
|-- models/                      Serialized fitted models and metadata
|-- netlify-site/                Static production dashboard and Netlify Function
|-- output/                      Submission and generated reporting artifacts
|-- src/                         Ordered pipeline stages
|-- tests/                       Automated checks
|-- README.md                    Project overview
`-- technical.txt                Deep technical reference
```

## Reproducibility

Install the Python dependencies, run the ordered pipeline, run the automated checks, and build the static site.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\run_pipeline.py
.\.venv\Scripts\python.exe -m pytest -q
Set-Location netlify-site
npm run build
```

The final pipeline stage writes `data/processed/build_manifest.json`, including config, source, and output checksums; model and scenario versions; random seeds; the build timestamp; and the recorded Git commit. The current build ID is derived from configuration, source checksums, model versions, and scenario identities. Re-run the pipeline after a release commit when a one-to-one Git attestation is required.

The principal generated outputs are:

- `data/processed/build_manifest.json`
- `data/processed/source_manifest.json`
- `data/processed/model_metrics.json`
- `data/processed/route2zero_scores.csv`
- `data/processed/route2zero_scores.geojson`
- `data/processed/climate_impact.csv`
- `data/processed/evidence_confidence.csv`
- `data/processed/sensitivity.csv`
- `data/processed/portfolio_scenarios.json`
- `data/processed/validation_priorities.json`
- `data/processed/route_planner_cache.json`

## Netlify deployment

The production interface is a static HTML, CSS, and JavaScript application under `netlify-site/public/`. Netlify builds from `netlify-site/`, runs `npm run build`, publishes `public/`, and bundles the optional explanation endpoint from `netlify/functions/`.

The site uses Mapbox GL JS and the project style `mapbox://styles/marwin2323/cmswv687u002u01so2xzd7mrs`. A selected route can request a street-following Mapbox Directions path from ordered screening coordinates. That path improves map readability; it does not verify the franchise alignment or current operation.

The approved `pk.` Mapbox token is a browser token and is available as the build fallback. `MAPBOX_TOKEN` is optional and can override it at build time. Restrict the public token to approved production and development origins in the Mapbox account.

The optional server-side explanation function uses these Netlify variables:

```text
ABSK_KEY=your_api_key
BASE_URL=your_openai_compatible_base_url
MODEL=your_model_name
AI_EXPLANATIONS_ENABLED=true
```

`ABSK_KEY` is the API-key variable. It belongs in Netlify Functions scope and must never be written to `public/config.js`, browser JavaScript, screenshots, or committed environment files. If the variables are absent or the request fails, the endpoint returns deterministic fallback text and the decision pipeline remains available.

## Documentation set

- [Methodology](docs/methodology.md)
- [Data provenance](docs/data_provenance.md)
- [Model card](docs/model_card.md)
- [Responsible AI](docs/responsible_ai.md)
- [Validation protocol](docs/validation_protocol.md)
- [Optimization methodology](docs/optimization_methodology.md)
- [City adapter guide](docs/city_adapter_guide.md)
- [Judging evidence matrix](docs/judging_matrix.md)
- [Pilot AI validation plan](docs/pilot_plan_ai_validation.md)
- [Live demonstration script](docs/demo_script.md)
- [Deep technical reference](technical.txt)

## Known limitations

- The route and schedule universe is historic and cannot establish active 2026 service.
- Text-derived city tags have low confidence and require boundary and local review.
- Only two routes have usable GTFS shapes; other geometries are planning approximations.
- Mapbox road paths are visualization aids, not official or field-verified route traces.
- The service model is evaluated against a historic derived target, not current field observations.
- Population exposure is not poverty, accessibility, tenure, vulnerability, or informal-settlement evidence.
- OSM infrastructure proximity does not establish utility capacity, ownership, interconnection approval, or site availability.
- Operator readiness remains a neutral prior for every route in the current build.
- Climate outputs are conditional scenarios and include a negative conservative case.
- The Phase-1 selection has no budget, cost, fleet, or financing constraint because those inputs are unavailable.
- An LLM explanation can summarize structured fields but cannot validate them.

These limitations define the pilot evidence agenda. They are not permissions to fill gaps with unsupported assumptions.

## Sources and licensing

The primary external sources are the historic Sakay community GTFS feed, WorldPop 2020 Philippines population raster, Philippine Department of Energy 2024 Luzon generation context, and a 20 August 2026 OpenStreetMap infrastructure snapshot. Exact URLs, retrieval dates, reference periods, licenses, and checksums are recorded in `config/source_registry.json` and `data/processed/source_manifest.json`.

Upstream source licenses and attribution requirements remain in force. The project repository should carry an explicit project-code license before wider reuse.

## Team

Route2Zero is developed by Team Larpers for the AI x City Climate Action Hackathon 2026.
