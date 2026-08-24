# Route2Zero

## Evidence-led planning for a just e-jeepney transition

Route2Zero is a city decision-support platform for identifying Metro Manila jeepney corridors that merit validation and transition planning first. It combines route data, machine-learning estimates, climate scenarios, equity screening, charging-readiness signals, operator evidence, and uncertainty analysis in one auditable workflow.

[Live platform](https://route2zero.netlify.app/) | [Source repository](https://github.com/qjmre23/Route2Zero)

The platform is built for local governments, transport agencies, operators and cooperatives, utilities, finance partners, and community stakeholders. Its purpose is to turn fragmented evidence into a defensible validation portfolio before capital, procurement, or franchise decisions are made.

## The decision

Metro Manila's e-jeepney transition is not only a vehicle-replacement problem. Corridor selection depends on service intensity, potential climate benefit, community exposure, charging access, operator capacity, financing conditions, and the quality of the evidence behind every claim.

Route2Zero answers one practical question:

> Which corridors should a city validate first, how strongly does the available evidence support that choice, and what new evidence could change the decision?

The result is not a static ranking. It is a traceable planning package containing corridor priorities, confidence grades, scenario ranges, rank-stability results, missing-evidence priorities, and a constrained Phase-1 portfolio.

## Platform value

| Planning challenge | Route2Zero response | Decision value |
|---|---|---|
| Fragmented route and infrastructure records | Consolidated, versioned route evidence | One inspectable planning baseline |
| Competing climate, equity, and readiness priorities | Human-controlled policy scenarios | Transparent trade-offs |
| Incomplete or outdated evidence | Explicit claim status and confidence grades | Uncertainty remains visible |
| Rankings that change with policy assumptions | Fixed-seed Monte Carlo sensitivity analysis | Robust and scenario-dependent routes are separated |
| Limited validation capacity | Value-of-information prioritization | Fieldwork targets evidence most likely to change a decision |
| Portfolio concentration | City, corridor, evidence, and coverage constraints | A more defensible Phase-1 shortlist |
| Complex analytical outputs | Structured evidence explanations | Results remain accessible without changing the underlying analytics |

## Operational snapshot

| Field | Value |
|---|---:|
| Pipeline specification | 2.1.0 |
| Build ID | r2z-d4c8d4cc709a |
| Build timestamp | 2026-08-24T16:13:03Z |
| Analytical source commit | 190ade5203cc5cbb02840a39246be46713bebd03 |
| Default policy scenario | scn-e0f12f397e |
| Phase-1 portfolio scenario | prt-fd6de9d793 |
| Route-direction records screened | 1,522 |
| Complete priority scores | 1,522 |
| Dated external route validations | 20 |
| Usable source geometries | 22 |
| Robust-priority corridors | 9 |
| Phase-1 corridors | 8 |
| Pipeline result | PASS_WITH_WARNINGS |

The warning state is intentional and substantive. The service universe is derived from a historic 2013–2020 GTFS source. Twenty corridors have dated OpenStreetMap route records and member-way geometry, but those records do not establish active service or franchise authority. Utility capacity, charging-site control, consent-based operator readiness, and financing evidence remain unverified.

Route2Zero therefore supports screening, validation design, and stakeholder review. It does not authorize procurement, investment, franchise action, or infrastructure construction.

## Product experience

| Workspace | Function |
|---|---|
| Overview | Presents the decision question, portfolio headline, evidence state, and primary cautions |
| Corridor Map | Displays street-aligned route geometry with city, priority, evidence, and validation filters |
| Route Lens | Opens a corridor-level evidence card with score components, scenarios, uncertainty, and next evidence |
| Scenario Lab | Reweights climate, equity, charging, and operator priorities without changing the source data |
| Phase-1 Portfolio | Shows selected corridors, exclusions, coverage constraints, climate range, and feasibility proxies |
| Evidence & AI | Generates a bounded explanation from structured facts and identifies unresolved evidence |
| Method & Sources | Exposes methodology, model versions, source records, build identifiers, and limitations |
| Report export | Produces decision-ready PDF, presentation, document, and structured reporting outputs |
| TOUR ME | Runs a narrated 15-stage product tour with one consistent ElevenLabs voice, a visible cursor, animated dropdown selections, random mapped-route selection, map zoom, policy and portfolio controls, a live assistant question, methods, and exports |

The responsive interface is deployed on Netlify and uses Mapbox GL JS for interactive cartography. Reviewed OSM relations are drawn from observed member-way geometry. Other routes use road-following Mapbox interpretations based on ordered screening coordinates and remain labelled as planning geometry. TOUR ME operates the real interface rather than replaying a fixed recording. Its cursor opens a visible option menu, highlights the chosen value, clicks it, and dispatches the same input and change events used by the dashboard. The tour restores the user's starting controls when it ends, supports pause and voice controls, and provides a reduced-motion mode.

## Decision methodology

### 1. Route evidence assembly

Historic GTFS records are normalized into route-direction corridors. Stops, schedule structure, city labels, route geometry, external route records, infrastructure proximity, and controlled evidence ledgers are linked through stable route identifiers.

### 2. Service-intensity completion

Historic schedule-derived vehicle-kilometres are available for 1,521 routes. A leakage-aware histogram gradient-boosting model supplies the missing value for one route. The model does not estimate ridership, passenger demand, revenue, or current operations.

| Service model metric | Result |
|---|---:|
| Model version | service-v1-266e0b1d |
| Training rows | 1,521 |
| Normalized corridor groups | 714 |
| Validation design | Five-fold grouped cross-validation |
| MAE | 267.6992 |
| RMSE | 574.1447 |
| R-squared | 0.9907 |
| Median-baseline MAE | 4,850.3377 |
| Relative MAE improvement | 94.48% |

Features that would leak the target or final decision are excluded, including headway, trips per day, climate impact, and final rank.

### 3. Corridor typology

Median imputation, standardization, and K-means clustering identify three structural route types. Typology supports interpretation and sampling; it contributes no hidden policy points.

| Corridor type | Routes |
|---|---:|
| Dense Urban Trunk | 631 |
| High-Stop-Density Core | 869 |
| Long Regional Connector | 22 |

Model version typology-v1-ab8203c9 records a silhouette score of 0.3730. Cluster labels describe route structure only. They do not infer poverty, settlement status, vulnerability, demand, or investment value.

### 4. Climate and energy scenarios

The deterministic climate engine converts daily vehicle-kilometres into electrified distance, diesel displacement, electricity demand, baseline diesel emissions, grid emissions, and net annual CO2e. Low, base, and high cases preserve uncertainty in electrification share, energy efficiency, grid intensity, and operating conditions.

For the selected Phase-1 portfolio:

| Climate case | Net annual result |
|---|---:|
| Low | -8,190.9 tCO2e |
| Base | +2,710.9 tCO2e |
| High | +22,288.0 tCO2e |

The negative low case is retained because it demonstrates that climate benefit is conditional on technology and grid assumptions. These values are planning scenarios, not measured reductions or finance-grade carbon claims.

### 5. Policy score

The default Climate + Equity scenario uses explicit, human-controlled weights:

    Priority score =
      0.40 x climate impact
      + 0.30 x equity
      + 0.15 x charging readiness
      + 0.15 x operator readiness

Climate-and-equity, equity-first, and infrastructure-first presets are available as comparison lenses. Policy weights remain a governance choice and are stored in versioned configuration.

### 6. Evidence confidence

Priority and evidence quality are deliberately separate.

| Measure | Meaning |
|---|---|
| Priority score | Weighted policy result under a named scenario |
| Evidence confidence | Freshness, directness, spatial specificity, completeness, external validation, and reliability |
| Model uncertainty | Error and residual behavior of the fitted service model |
| Rank stability | Rank behavior across tested policy weights |

A high-priority corridor with grade C evidence is a strong validation candidate, not an implementation approval.

### 7. Sensitivity and robustness

The sensitivity engine evaluates 5,000 fixed-seed policy-weight combinations drawn around the default scenario. It records top-5, top-10, and top-20 frequency, median rank, P10–P90 ranges, and a stability score.

| Stability class | Routes |
|---|---:|
| ROBUST PRIORITY | 9 |
| SCENARIO-DEPENDENT | 1,180 |
| LOW-PRIORITY ROBUST | 333 |

Robustness describes policy-weight sensitivity. It does not strengthen weak source evidence.

### 8. Value of information

Missing fields are perturbed through deterministic tests to estimate their potential effect on rank and portfolio membership. The resulting queue directs validation effort toward the information with the greatest decision value.

### 9. Phase-1 portfolio

Portfolio scenario prt-fd6de9d793 selects a maximum of eight corridors subject to evidence, equity, city coverage, corridor duplication, and activity constraints.

| Constraint | Rule |
|---|---|
| Portfolio size | Maximum 8 |
| Evidence floor | Grade C |
| Equity floor | Score 40 |
| Evidence-limited routes | Maximum 2 |
| Primary-city concentration | Maximum 2 per city |
| Corridor duplication | Maximum 1 direction per normalized corridor |
| Inactive services | Excluded |

Selected corridors:

    LTFRB_PUJ1353
    LTFRB_PUJ1241
    LTFRB_PUJ2083
    LTFRB_PUJ1156
    LTFRB_PUJ1638
    LTFRB_PUJ1153
    LTFRB_PUJ1350
    LTFRB_PUJ1405

The portfolio averages 73.9 for equity and 37.8 for evidence confidence. All eight routes carry grade C evidence.

The feasibility screen estimates approximately 1,943 vehicles, 102 charging stations, and ₱4.91 billion in vehicle-and-charger capital. These figures are order-of-magnitude proxies. Depot works, civil works, grid upgrades, battery replacement, operating costs, taxes, insurance, financing, and site acquisition are excluded.

### 10. Structured explanation

The server-side explanation function receives a bounded set of route, scenario, portfolio, and evidence facts. It can summarize those facts and clarify the next validation need. It cannot change scores, ranks, climate values, model outputs, constraints, or portfolio membership.

## Claim-status contract

Every material value is presented under a defined status:

| Status | Meaning |
|---|---|
| VERIFIED | Checked against an accepted external or field source |
| OBSERVED | Directly recorded under the stated protocol |
| DERIVED | Calculated deterministically from identified inputs |
| ML_ESTIMATED | Produced by a versioned fitted model |
| PROXY | Indirect screening evidence with a documented limitation |
| SCENARIO | Conditional result under explicit assumptions |
| NEUTRAL_PRIOR | Deliberate midpoint used where sufficient evidence is absent |
| MISSING | No defensible value is available |

Source currentness is recorded separately as historic, current, scenario, or mixed.

## Current evidence position

| Evidence area | Position |
|---|---|
| Route operations | 20 dated external route records; active status remains uncertain for all 1,522 records |
| Geometry | 20 reviewed OSM member-way geometries, 2 GTFS shapes, 1,500 ordered-stop approximations |
| Equity | WorldPop population-exposure proxy; no validated poverty or informal-settlement layer |
| Charging | Infrastructure-proximity proxy; no verified feeder capacity or site control |
| Operators | Neutral prior for all routes; one named desk reference does not meet the readiness threshold |
| Financing | No validated financing package or affordability evidence |
| Climate | Conditional low, base, and high scenarios |
| Service intensity | Historic schedule-derived proxy with one ML-completed record |

## Flagship corridor

The portfolio rule selects LTFRB_PUJ1353, Francisco Homes–Cubao, as the flagship corridor.

| Field | Value |
|---|---:|
| Default rank | 1 |
| Priority score | 79.07 |
| Evidence grade | C |
| Evidence confidence | 38.34 |
| Top-10 frequency | 100% |
| Low climate case | -1,111.8 tCO2e/year |
| Base climate case | +368.0 tCO2e/year |
| High climate case | +3,025.3 tCO2e/year |

The selection rule gives precedence to Phase-1 membership, robust-priority status, evidence confidence, priority score, and stable route ID. The result is generated from the recorded build rather than manually assigned.

## System architecture

    Versioned source registry and evidence ledgers
                        |
                        v
    Route normalization and spatial feature engineering
                        |
              +---------+---------+
              |                   |
              v                   v
    Service-intensity ML     Corridor typology
              |                   |
              +---------+---------+
                        |
                        v
    Climate, equity, charging, and operator evidence
                        |
                        v
    Policy scoring and evidence-confidence grading
                        |
                        v
    Monte Carlo sensitivity and value-of-information
                        |
                        v
    Constrained Phase-1 portfolio
                        |
              +---------+---------+
              |                   |
              v                   v
    Netlify dashboard       Submission reports

## Technology

| Layer | Technology |
|---|---|
| Data and spatial processing | Python, pandas, GeoPandas, Shapely, PyProj, Rasterio |
| Machine learning | scikit-learn, SciPy, Joblib |
| Analytical visualization | Plotly, Folium |
| Production interface | HTML, CSS, JavaScript |
| Interactive mapping | Mapbox GL JS, Mapbox Directions, OpenStreetMap evidence |
| Serverless explanation endpoint | Netlify Functions, Node.js |
| Deployment | Netlify |
| Quality assurance | pytest, Node test runner, deterministic checksum contracts |
| Reporting | PDF, PowerPoint, Word, CSV, GeoJSON, and JSON outputs |

## Repository

    Route2Zero/
    |-- app/                         Analytical Streamlit interface
    |-- config/                      Policy, evidence, model, source, and scenario contracts
    |-- data/
    |   |-- raw/                     Immutable source snapshots
    |   |-- validated/               Controlled pilot evidence ledgers
    |   -- processed/                Generated analytical outputs and manifests
    |-- docs/                        Methodology, governance, validation, and pilot references
    |-- models/                      Serialized models and metadata
    |-- netlify-site/                Production dashboard and serverless function
    |-- output/                      Submission and reporting artifacts
    |-- scripts/                     Build, capture, export, and verification utilities
    |-- src/                         Ordered analytical pipeline
    |-- tests/                       Pipeline and function contract tests
    |-- README.md                    Product and technical overview
    |-- idea.txt                     Full solution narrative
    -- technical.txt                 Detailed technical specification

## Reproducible build

### Python pipeline

    python -m venv .venv
    .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
    .\\.venv\\Scripts\\python.exe src\\run_pipeline.py
    .\\.venv\\Scripts\\python.exe -m pytest tests -q

### Netlify production build

    Set-Location netlify-site
    npm run check
    npm run build

The pipeline writes a build manifest with source, configuration, and output checksums; model and scenario identities; fixed random seeds; build time; and analytical source commit. Processed outputs are regenerated from source and configuration rather than edited manually.

Principal outputs:

| Output | Purpose |
|---|---|
| build_manifest.json | Build identity, checksums, versions, and random seeds |
| source_manifest.json | Source registry with dates, licenses, scope, and limitations |
| model_metrics.json | Fitted-model evaluation and metadata |
| route2zero_scores.csv | Route-level score, evidence, uncertainty, and portfolio fields |
| route2zero_scores.geojson | Map-ready route properties and geometry |
| climate_impact.csv | Low, base, and high climate scenarios |
| evidence_confidence.csv | Evidence grades and component diagnostics |
| sensitivity.csv | Monte Carlo rank-stability results |
| portfolio_scenarios.json | Portfolio constraints, membership, and summaries |
| validation_priorities.json | Value-of-information queue |
| route_planner_cache.json | Dashboard-ready route and portfolio package |

## Netlify configuration

The repository-level netlify.toml sets netlify-site as the build base, runs npm run build, publishes netlify-site/public, and bundles functions from netlify-site/netlify/functions.

| Variable | Scope | Purpose |
|---|---|---|
| ABSK_KEY | Netlify Functions | Server-side provider API key |
| BASE_URL | Netlify Functions | OpenAI-compatible API base URL or complete /chat/completions endpoint |
| MODEL | Netlify Functions | Provider model identifier |
| AI_EXPLANATIONS_ENABLED | Netlify Functions | Enables the bounded explanation endpoint when set to true |
| MAPBOX_TOKEN | Build, optional | Overrides the approved public Mapbox browser token |
| ELEVENLABS_API_KEY | Netlify Functions | Required for the narrated TOUR ME voice; never exposed to the browser |
| ELEVENLABS_VOICE_ID | Netlify Functions, optional | Overrides the default male Adam voice (`pNInz6obpgDQGcFmaJgB`) |
| ELEVENLABS_MODEL_ID | Netlify Functions, optional | Overrides the low-latency narration model (`eleven_flash_v2_5`) |

The Mapbox style is mapbox://styles/marwin2323/cmswv687u002u01so2xzd7mrs. Public pk. tokens are browser credentials and remain origin-restricted through the Mapbox account. Server-side provider credentials are never written to browser configuration, committed files, screenshots, or static assets. TOUR ME prewarms its opening narration and prefetches the next steps so every spoken stage uses the same configured ElevenLabs voice. It never switches to browser or device speech. If ElevenLabs is unavailable, the visual tour continues silently and displays the provider status instead of substituting another voice.

## Quality controls

The repository enforces:

- complete source, configuration, and output checksum manifests;
- fixed-seed model, sensitivity, and portfolio operations;
- grouped cross-validation to reduce route-direction leakage;
- strict JSON output without NaN or Infinity;
- explicit status vocabulary for material claims;
- separate priority, evidence, model-error, and rank-stability measures;
- stable model, scenario, portfolio, and build identifiers;
- deterministic portfolio constraints and exclusion reasons;
- Python pipeline tests, Node function tests, and Netlify build checks; and
- visual and structural verification of submission artifacts.

## Boundaries

- The route universe cannot establish active service without dated operational confirmation.
- OpenStreetMap geometry does not establish franchise authority or service activity.
- Population exposure is not a measure of poverty, tenure, accessibility, vulnerability, or informal-settlement status.
- Infrastructure proximity does not establish electrical capacity, ownership, interconnection approval, or site availability.
- Operator readiness remains neutral until consent-based evidence meets the stated threshold.
- Climate outputs are conditional scenarios and include a negative conservative case.
- Fleet, charging, and capital figures are feasibility proxies with material cost exclusions.
- The Phase-1 portfolio is a validation shortlist, not a procurement or investment portfolio.
- Structured explanations do not validate evidence or alter analytical results.

These boundaries define the pilot evidence agenda and keep unsupported assumptions out of city decisions.

## Documentation

| Document | Scope |
|---|---|
| [Methodology](docs/methodology.md) | Ordered analytical stages and field contracts |
| [Data provenance](docs/data_provenance.md) | Source lineage, dates, limitations, and licenses |
| [Model card](docs/model_card.md) | Model purpose, evaluation, failure modes, and validation |
| [Responsible AI](docs/responsible_ai.md) | Governance, human authority, and explanation controls |
| [Validation protocol](docs/validation_protocol.md) | Field, operator, utility, community, and model validation |
| [Optimization methodology](docs/optimization_methodology.md) | Portfolio objective, constraints, and exclusions |
| [City adapter guide](docs/city_adapter_guide.md) | Portability contract for another city |
| [Judging evidence matrix](docs/judging_matrix.md) | Submission claims mapped to evidence |
| [Pilot AI validation plan](docs/pilot_plan_ai_validation.md) | Six-month model and explanation evaluation |
| [Demonstration script](docs/demo_script.md) | Sub-90-second product walkthrough |
| [Technical specification](technical.txt) | Detailed architecture, schemas, tests, and deployment |

## Submission package

The final materials are stored in output/submission:

- Route2Zero_Concept.pdf
- Route2Zero_Concept_Deck_20_Slides.pptx
- Route2Zero_Prototype_Demonstration.pdf
- Route2Zero_Prototype_Demonstration.pptx
- Route2Zero_Team_Larpers_Pilot_Plan.pdf
- Route2Zero_Team_Larpers_Pilot_Plan.docx

## Team Larpers

- John Marwin Ebona
- Isaac Marcus
- Andrei Dela Cruz
- Russel Mendez
- TRISTIAN JAMES CABALAR
- JOHN MICHAEL PALAGANAS
- Carl Nueva
- JOSEPH CLARENCE PARAYAOAN

Route2Zero was developed for the AI x City Climate Action Hackathon 2026.

## License and source terms

Project-authored code and documentation are licensed under the MIT License. Upstream data retains its own terms:

- OpenStreetMap data: ODbL 1.0
- WorldPop data: CC BY 4.0
- Historic GTFS: included Department of Transportation and Communications developer agreement
- Publication and reference materials: source-specific terms recorded in the source registry

Full attribution and reuse conditions are documented in [NOTICE.md](NOTICE.md).
