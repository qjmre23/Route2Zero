# Route2Zero

**An equity-aware decision-support platform for prioritizing e-jeepney electrification in Metro Manila.**

Route2Zero helps transport agencies, local governments, operators, and financing stakeholders identify jeepney corridors that merit deeper electrification feasibility assessment.

The platform evaluates **1,522 PUJ route-direction records** using four dimensions:

* Emissions-reduction potential
* Equity
* Grid feasibility
* Operator readiness

These dimensions are combined into a transparent and adjustable **Just Transition Score**, allowing different policy priorities to be explored without hiding the assumptions behind the ranking.

Route2Zero is designed as a **screening and evidence-gap identification tool**. It does not determine funding eligibility, procurement decisions, franchise status, fare policy, route cancellation, or lending approval.

The project was developed for the **AI x City Climate Action Hackathon 2026**, with Metro Manila as the pilot area.

---

## Platform Overview

Route2Zero combines a reproducible data pipeline with an interactive web dashboard for route-level electrification screening.

The platform provides:

* Interactive ranking of Metro Manila jeepney routes
* Adjustable policy weights
* City-level filtering and summaries
* Four-factor route score breakdowns
* Mapbox-powered route visualization
* Impact-versus-equity comparison
* Route confidence and evidence indicators
* Ranked action queues
* PDF, Word, and CSV decision-pack exports
* Generated policy briefs
* Optional AI-generated explanations
* Reproducible scoring and data-processing scripts

Historic records, proxy variables, placeholders, incomplete fields, and confidence limitations remain visible throughout the interface and exported reports.

---

## Just Transition Score

The default scoring model gives equal priority to emissions reduction and equity while retaining grid and operator considerations.

| Dimension                     | Default Weight |
| ----------------------------- | -------------: |
| Emissions-reduction potential |            35% |
| Equity                        |            35% |
| Grid feasibility              |            15% |
| Operator readiness            |            15% |

The default composite score is:

```text
0.35 × Emissions
+ 0.35 × Equity
+ 0.15 × Grid
+ 0.15 × Operator Readiness
```

Dashboard weights can be adjusted interactively.

When users change the policy weights, the values are normalized in the browser before the rankings are recomputed.

The scoring process remains deterministic. AI-generated content has no authority over score fields, policy weights, or route rankings.

---

## Scoring Dimensions

### Emissions-Reduction Potential

The emissions dimension represents relative service activity.

It is derived from:

```text
Route Length × Estimated Weekday Trips
```

The resulting values are normalized across the PUJ route universe.

This score represents **activity-based emissions potential**, rather than directly measured fuel consumption or greenhouse-gas reduction.

It does not claim route-level knowledge of:

* Vehicle age
* Engine technology
* Actual fuel consumption
* Passenger volume
* Fleet composition
* Measured CO₂ emissions
* Tonnes of CO₂ avoided

---

### Equity

The equity dimension uses a **300-metre route catchment** combined with WorldPop population-density data.

It estimates how strongly a route overlaps areas with relatively high population concentration.

This is intentionally treated as a **density proxy**.

Population density is not used as evidence of:

* Household income
* Poverty
* Informal-settlement status
* Land tenure
* Social vulnerability
* Accessibility need

These factors require additional verified datasets or community-level validation.

---

### Grid Feasibility

The current grid dimension uses the official **2024 Luzon renewable-generation share** as regional context.

```text
14,550 GWh / 90,269 GWh = 16.118%
```

This value is intentionally coarse and remains constant across the current route universe.

The grid score is not a substitute for assessment of:

* Distribution feeders
* Substations
* Depot electrical capacity
* Charging infrastructure
* Interconnection requirements
* Electricity tariffs
* Charging schedules

Route-level electrification decisions require utility and site-specific evidence beyond the current screening model.

---

### Operator Readiness

Operator readiness currently begins at a neutral baseline of:

```text
50 / 100
```

The value acts as an explicit placeholder where verified cooperative, financing, fleet, governance, or consolidation information is unavailable.

Verified operator information can replace the default value without changing the upstream scoring methodology.

---

## Current Route Universe

The canonical transport network is based on the Sakay community GTFS dataset.

The analyzed snapshot contains:

| Record                                         |  Count |
| ---------------------------------------------- | -----: |
| Total routes                                   |  1,717 |
| LTFRB routes                                   |  1,711 |
| PUJ route-direction records                    |  1,522 |
| PUB route-direction records                    |    189 |
| Trips                                          |  1,864 |
| Stops                                          |  4,858 |
| Stop-time records                              | 79,414 |
| Frequency records                              |  1,864 |
| Shape IDs                                      |     10 |
| PUJ records with usable GTFS shapes            |      2 |
| PUJ records using stop-sequence approximations |  1,520 |

The underlying GTFS service calendar spans **2013–2020**.

It is therefore used as a historic network baseline for the MVP and is not presented as proof of active 2026 operations.

---

## Web Architecture

The primary Route2Zero interface is a responsive static web application deployed through Netlify.

```text
netlify-site/
├── public/
├── scripts/
├── netlify/
└── package.json
```

The application uses:

* HTML
* CSS
* Browser JavaScript
* Mapbox GL JS
* Mapbox Directions
* Netlify static hosting
* Netlify Functions for optional AI explanations

The deployed dashboard does not require a persistent backend server.

Processed datasets are copied into the application's public data directory during the build process.

Netlify configuration also defines security headers, asset caching, function bundling, and controlled handling of browser-safe configuration.

---

## Map and Route Visualization

Route2Zero uses **Mapbox GL JS** for its interactive geospatial interface.

Project map style:

```text
mapbox://styles/marwin2323/cmswv687u002u01so2xzd7mrs
```

Regional route records are initially represented in a clustered form to maintain map readability.

When a route is selected, its ordered screening coordinates are used to request a road-following geometry through Mapbox Directions.

Large coordinate sequences are divided into groups of no more than **25 coordinates per request**.

The resulting geometries are combined into a GeoJSON route representation and displayed on the map.

A successful road-following result is identified in the interface as:

```text
Street-following route ready · Mapbox Directions
```

Mapbox routing improves the presentation of the screening geometry. It does not verify whether the exact path remains part of current franchise or operating conditions.

If a reliable road path cannot be produced, Route2Zero preserves the underlying screening information and exposes the corresponding confidence limitation rather than presenting the route as verified.

---

## Data Pipeline

Route2Zero uses an ordered Python pipeline that separates source auditing, geometry construction, proxy generation, scoring, aggregation, and reporting.

```text
src/
├── 01_audit.py
├── 02_geometry.py
├── 03_frequency.py
├── 04_emissions_score.py
├── 05_equity_score.py
├── 06_grid_score.py
├── 07_operator_score.py
├── 08_composite_score.py
├── 09_city_aggregation.py
├── 10_policy_brief.py
├── 11_ai_explain.py
├── common.py
├── bedrock_client.py
└── run_pipeline.py
```

### Pipeline Responsibilities

**01 — GTFS Audit**
Validates the transport dataset and establishes the canonical PUJ route universe.

**02 — Geometry**
Selects representative trips and constructs the route geometry used for screening.

**03 — Frequency**
Estimates service windows, headways, and weekday trip activity.

**04 — Emissions Score**
Creates the activity-based emissions-reduction potential score.

**05 — Equity Score**
Builds the WorldPop density catchment proxy.

**06 — Grid Score**
Adds the Luzon renewable-generation context.

**07 — Operator Score**
Applies the neutral operator-readiness baseline and any verified overrides.

**08 — Composite Score**
Combines the four dimensions and generates completeness, confidence, and ranking fields.

**09 — City Aggregation**
Produces city summaries and route-city classifications.

**10 — Policy Brief**
Creates evidence-focused policy briefs from the processed route information.

**11 — AI Explanation**
Generates optional narrative explanations from completed deterministic results.

`run_pipeline.py` executes the complete ordered workflow.

Source files under `data/raw/` remain separate from processed outputs.

---

## Primary Data Outputs

The main dashboard dataset is:

```text
data/processed/route2zero_scores.csv
```

It contains route-level scores, rankings, confidence indicators, source information, and supporting attributes.

Additional outputs include:

```text
data/processed/routes_scored.geojson
data/processed/city_summary.csv
data/processed/score_weights.json
data/processed/explanations_cache.json
```

Other generated datasets include:

```text
audit_report.md
route_corridors.csv
jeepney_routes.geojson
route_frequency.csv
emissions_score.csv
equity_score.csv
grid_feasibility.csv
operator_readiness.csv
route2zero_scores.csv
routes_scored.geojson
city_summary.csv
route_explanations.json
```

Confidence labels and provenance fields remain attached to scored records so that rankings can be interpreted alongside the quality of their underlying evidence.

---

## Current Ranking Snapshot

Under the default **35 / 35 / 15 / 15** policy weighting, the highest-ranked record in the current processed dataset is:

**LTFRB_PUJ1353 — Francisco Homes–Cubao**

| Dimension           |     Score |
| ------------------- | --------: |
| Emissions           |     98.18 |
| Equity              |     77.42 |
| Grid                |     16.12 |
| Operator Readiness  |     50.00 |
| **Composite Score** | **71.38** |

The dashboard displays the composite score as **71.4**.

Rankings can change when users modify policy weights or apply city filters.

---

## AI Explanation Layer

Route2Zero includes an optional AI explanation layer for producing readable summaries of deterministic scoring results.

AI is deliberately separated from the ranking system.

The AI layer cannot:

* Modify component scores
* Change composite scores
* Change route rankings
* Modify policy weights
* Fill missing evidence automatically
* Override confidence labels

Its role is limited to explaining existing data and highlighting evidence gaps.

When an external AI service is unavailable or disabled, Route2Zero can use deterministic fallback explanations without affecting the rest of the platform.

The system maintains:

```text
ranking_ai_influence = false
```

throughout the scoring workflow.

---

## Environment and Secret Separation

Route2Zero distinguishes browser-safe configuration from server-side credentials.

The Mapbox browser token is a public `pk.` token intended for client-side use.

Optional AI credentials remain server-side through Netlify Functions.

Relevant environment variables include:

```text
MAPBOX_TOKEN
ABSK_KEY
MODEL
BASE_URL
AI_EXPLANATIONS_ENABLED
```

`MAPBOX_TOKEN` may override the approved browser token during deployment.

`ABSK_KEY` is reserved for server-side AI requests and is never exposed through the public dashboard configuration.

The Mapbox token can be restricted to approved production domains and localhost development origins.

---

## Dashboard Exports

Route2Zero produces decision-support outputs based on the currently selected scenario.

### PDF

Creates a formal report containing the active policy lens, route rankings, scenario context, and evidence limitations.

### Word

Creates an editable report containing the selected weighting configuration, recommendations, and supporting information.

### CSV

Exports the currently ranked scenario for additional analysis.

Exports preserve the active:

* City filter
* Policy weights
* Ranking scenario
* Confidence information
* Evidence limitations

---

## Policy Briefs and Submission Materials

The repository includes generated policy and demonstration artifacts supporting the Route2Zero pilot.

```text
output/
├── documents/
├── pdf/
├── presentation/
├── submission/
└── playwright/
```

Major artifacts include:

* Route2Zero Concept Deck
* Prototype Demonstration PDF
* Editable Demonstration presentation
* Team Pilot Plan
* Formal 24-page Pilot Plan
* 24-slide demonstration deck
* Presentation PDF
* Presentation narration
* Technical reference
* Generated policy briefs

These materials document both the prototype and the proposed pathway for validating the model with government, operators, utilities, and local stakeholders.

---

## Confidence and Evidence Policy

Route2Zero intentionally keeps uncertainty visible.

A high score means that a route is a stronger candidate for **further validation under the selected policy lens**.

It does not mean that electrification has already been proven technically, financially, socially, or operationally feasible.

The platform distinguishes between:

* Verified source data
* Historic data
* Derived values
* Proxy indicators
* Regional context
* Neutral placeholders
* Missing evidence

A complete composite score requires values for all four scoring dimensions.

Confidence information remains available alongside the ranking so decision-makers can distinguish strong evidence from screening assumptions.

---

## Release Assurance

The current Route2Zero release was checked across the data, dashboard, mapping, export, and presentation layers.

Verified release conditions include:

* Netlify build completed without requiring `MAPBOX_TOKEN`
* Dashboard loaded all **1,522 PUJ records**
* **1,521 records** contained complete composite scores
* Default leading dashboard score displayed as **71.4**
* Selected routes successfully reached Mapbox street-following status
* Desktop layout at **1,440 px** showed no horizontal overflow
* Mobile layout at **390 px** showed no horizontal overflow
* Policy-weight controls recomputed route rankings
* Route finder and ranking selections updated the map
* Confidence and assumption information remained available
* PDF, Word, and CSV export paths were verified
* AI-disabled operation retained deterministic explanation behavior
* Desktop and mobile browser captures were produced
* The 24-slide presentation passed overflow checks
* The 24-page demonstration PDF rendered successfully
* The 24-page Pilot Plan passed its document review without high-severity accessibility findings

---

## Known Limitations

### Historic Transport Network

The current GTFS service calendar ends in 2020.

The dataset provides a useful route-network baseline, though it cannot independently establish whether every listed service remains active in 2026.

---

### Sparse Route Shapes

Only **2 of 1,522 PUJ records** contain usable source GTFS shapes.

The remaining **1,520 records** use ordered stop sequences as the basis for screening geometry.

Mapbox road routing improves visualization of these routes without converting them into verified operating traces.

---

### Activity-Based Emissions Proxy

The emissions score represents route activity rather than measured emissions.

Actual electrification assessment would require additional fleet, fuel, passenger, engine, and air-quality information.

---

### Density-Based Equity Proxy

WorldPop density identifies population concentration rather than socioeconomic vulnerability.

Community and government datasets are required for stronger equity analysis.

---

### Regional Grid Context

The current grid dimension represents Luzon-level renewable-generation context.

It does not assess whether a specific depot or corridor can support electric-vehicle charging.

---

### Operator Readiness Placeholder

Operator readiness remains at a neutral value where verified cooperative and financing evidence has not yet been collected.

This dimension is intended to be replaced through structured and consent-based engagement with operators.

---

### Route-City Classification

Route-city tags require additional validation with LGUs, particularly for corridors crossing multiple administrative boundaries.

---

## Pilot Priorities

The next phase of Route2Zero focuses on converting screening assumptions into locally verified evidence.

Priority workstreams include:

1. Validate active routes, stops, headways, and service periods with LTFRB and participating LGUs.
2. Replace screening geometry with verified road traces for shortlisted corridors.
3. Expand equity analysis using locally validated socioeconomic and accessibility indicators.
4. Assess feeder, substation, depot, tariff, interconnection, and charging constraints with the relevant utility.
5. Replace operator-readiness placeholders with structured cooperative evidence.
6. Add actual fleet, fuel, ridership, and emissions information where available.
7. Validate cross-boundary route-city classifications.
8. Document stakeholder-approved weighting scenarios and sensitivity analysis.
9. Maintain restricted Mapbox browser-token origins for production deployments.
10. Use the formal Pilot Plan as the implementation and governance reference for future validation.

---

## Project Structure

```text
Route2Zero/
├── app/
│   └── dashboard.py
├── data/
│   ├── raw/
│   │   ├── gtfs_master/
│   │   ├── gtfs_dotc/
│   │   └── reference/
│   └── processed/
├── docs/
│   ├── data_provenance.md
│   ├── methodology.md
│   ├── demo_script.md
│   └── policy_briefs/
├── GTFS/
├── netlify-site/
│   ├── public/
│   ├── scripts/
│   └── netlify/
├── output/
│   ├── documents/
│   ├── pdf/
│   ├── presentation/
│   ├── submission/
│   └── playwright/
├── src/
│   ├── common.py
│   ├── 01_audit.py
│   ├── 02_geometry.py
│   ├── 03_frequency.py
│   ├── 04_emissions_score.py
│   ├── 05_equity_score.py
│   ├── 06_grid_score.py
│   ├── 07_operator_score.py
│   ├── 08_composite_score.py
│   ├── 09_city_aggregation.py
│   ├── 10_policy_brief.py
│   ├── 11_ai_explain.py
│   ├── bedrock_client.py
│   └── run_pipeline.py
├── tests/
├── README.md
├── technical.txt
├── script.txt
└── requirements.txt
```

---

## Team

**Team Larpers**

* John Marwin Ebona
* Prince Marl
* Joaquin Sarmiento
* Isaac Marcus
* Andrei Dela Cruz
* Russel Mendez
* Tj Moreno
* JM Palaganas

Detailed pilot responsibilities are documented in the project Pilot Plan.

---

## Data Sources

Route2Zero currently relies on the following primary datasets and references:

### Sakay Community GTFS

Metro Manila public-transport route, trip, stop, frequency, and geometry information.

`github.com/sakayph/gtfs`

### WorldPop

**Philippines 2020 1 km population grid**

Used as the current population-density input for the equity screening dimension.

Licensed under **CC BY 4.0**.

`hub.worldpop.org/geodata/summary?id=33241`

### Philippine Department of Energy

**2024 Key Energy Statistics**

Used for the Luzon renewable-generation baseline in the grid context score.

### Philippine Energy Plan 2023–2050

Used as supporting national and grid-development context.

Detailed provenance, branch comparisons, source decisions, checksums, and processing notes are documented in:

```text
docs/data_provenance.md
```

---

## Project Positioning

Route2Zero is not intended to provide a single definitive answer to Metro Manila's jeepney electrification challenge.

Its purpose is to make prioritization **inspectable**.

Every ranking exposes the policy weights behind it. Every proxy remains identifiable as a proxy. Missing evidence remains visible instead of being silently inferred.

The result is a structured starting point for determining **which corridors deserve deeper technical, social, financial, and operational validation first**.

---

## License

Upstream datasets remain subject to their original licenses and attribution requirements.

The original GTFS licensing information is retained with the corresponding source data.

Route2Zero-generated software and project artifacts should use the team's selected project license before public release.
