# Route2Zero 2.1 methodology

## Method scope

Route2Zero is a corridor-screening and evidence-acquisition system. Its output is a documented order for validation and a constrained Phase-1 shortlist. It does not determine funding, franchise status, procurement, lending, fares, or route cancellation.

This document describes pipeline version `2.1.0` and build `r2z-0cd49ad56aaa`. The default policy scenario is `scn-e0f12f397e`; the default portfolio scenario is `prt-fd6de9d793`.

## Decision unit

The unit of analysis is one LTFRB public-utility-jeepney route-direction record from the historic Sakay GTFS `master` branch.

- The source feed contains 1,717 route-direction records.
- Route identifiers containing `PUJ` within the LTFRB agency define 1,522 scored records.
- The feature store and final score table contain one row per route ID.
- `normalized_corridor_id` groups route names for model splitting and portfolio direction limits.
- The current model metadata records 714 normalized corridor groups.
- `data/processed/route_corridors.csv` preserves an agency/name corridor view without discarding route IDs.

Twenty records are `current` because a reviewed OpenStreetMap route relation was edited on or after 1 January 2023; 1,502 remain `historic_only`. Every record retains `active_status = uncertain` because route-record recency does not establish current operation or franchise authority.

## Claim and currentness controls

Route2Zero uses a fixed claim vocabulary:

| Status | Use |
|---|---|
| `VERIFIED` | Accepted field or external verification |
| `OBSERVED` | Directly recorded external or pilot evidence with an identified source and date, without agency-certification claim |
| `DERIVED` | Deterministic calculation |
| `ML_ESTIMATED` | Versioned model output |
| `PROXY` | Indirect screening indicator |
| `SCENARIO` | Assumption-dependent result |
| `NEUTRAL_PRIOR` | Deliberate default in the absence of evidence |
| `MISSING` | No defensible value |

Source currentness is tracked separately as historic, current, mixed, or scenario. A current configuration file can still contain a scenario or neutral prior; a historic source can still support a correctly labeled derived field.

## Stage 1: source registry

`src/00_source_manifest.py` validates every source entry in `config/source_registry.json`. Required metadata include source ID, title, organization, URL, local path, retrieval date, reference period, geography, spatial resolution, license, source type, currentness, notes, and whether the source is required.

The stage hashes each available file or, for a directory, a stable ordered list of relative paths and file hashes. A missing required source stops the build. A missing optional WorldPop or OSM layer remains in the manifest with `available = false` and a null checksum, and its dependent fields degrade to `MISSING`/null where feasible. The resolved output is `data/processed/source_manifest.json`.

City-specific access is isolated behind formal transport/GTFS, population, charging, operator, and boundary/city adapter interfaces. The Metro Manila adapters wire the current paths and text-fallback city method; another city implements the same contracts rather than changing the analytical stages.

## Stage 2: GTFS audit

`src/01_audit.py` reads the immutable GTFS files as strings and checks:

- `trips.route_id` references `routes.route_id`;
- `stop_times.stop_id` references `stops.stop_id`; and
- `frequencies.trip_id` references `trips.trip_id`.

The current audit reports 100% referential coverage and zero missing references in all three relationships. It also writes the de-duplicated corridor view.

The audit is an internal consistency check. It does not establish that the schedule represents current service.

## Stage 3: route geometry

`src/02_geometry.py` selects one representative trip per route using the greatest stop-time count, with trip ID as a stable tie-breaker.

Geometry follows a two-tier rule:

1. Use the ordered GTFS shape points when the representative trip has a valid shape ID with at least two coordinates.
2. Otherwise, connect representative-trip stops in `stop_sequence` order.

Consecutive duplicate coordinates are removed. Length is the WGS84 geodesic length of the resulting line.

The current route universe contains:

| Geometry source | Count |
|---|---:|
| GTFS shape | 2 |
| Reviewed OSM relation member ways | 20 |
| Ordered-stop approximation | 1,500 |

The approximate geometry is a screening line. A Mapbox Directions rendering is also a planning visualization and does not convert the line into verified franchise geometry.

## Stage 4: geometry reliability

`src/02b_geometry_reliability.py` calculates deterministic diagnostics:

- endpoint distance;
- line-to-endpoint detour ratio;
- duplicate-coordinate fraction;
- maximum consecutive-stop gap;
- validity;
- self-intersection; and
- representative stop count.

A GTFS shape begins at 88 points and an ordered-stop approximation at 52. Rules add or subtract points for stop count, detour ratio, gap length, duplicates, self-intersection, and validity. A field-verified geometry receives at least 92.

Grades are A at 85 or above, B at 70 or above, C at 50 or above, and D below 50.

The current build has two A, 17 B, 1,128 C, and 375 D geometry grades. Twenty reviewed OSM relations and two GTFS shapes are treated as usable source geometries; all 1,500 ordered-stop approximations require validation.

## Stage 5: historic service-frequency proxy

`src/03_frequency.py` includes a GTFS service when Monday is enabled or the service ID is explicitly `WEEKDAYS` or `DAILY`.

For each route:

```text
avg_headway_min = mean(headway_secs) / 60
daily_service_window_hrs = union of valid frequency intervals / 3600
trips_per_day_estimate = daily_service_window_hrs x 60 / avg_headway_min
```

Overlapping service intervals are merged before duration is calculated. This avoids double-counting overlapping frequency blocks.

The result is a schedule-derived planning proxy. It is not a block schedule, vehicle count, completed-trip count, passenger-demand measurement, or current observation.

The proxy is available for 1,521 records. One route lacks a qualifying historic value.

## Stage 6: compatibility layers

The original MVP layers are retained for audit and comparison:

- `emissions_score.csv` uses route length multiplied by estimated historic trips;
- `equity_score.csv` uses WorldPop population exposure within a 300 m buffer;
- `grid_feasibility.csv` uses the Luzon renewable-generation share; and
- `operator_readiness.csv` uses a neutral 50 or an authorized override.

Earlier proxy layers remain intermediate audit artifacts only and do not define the current default policy score or final score-table schema.

## Stage 7: canonical feature store

`src/04_feature_engineering.py` merges route, geometry, service, population, reliability, hub, and validation fields into `route_features.csv`.

Derived features include:

- normalized corridor ID;
- stops per kilometre;
- mean stop spacing;
- endpoint distance;
- geometry detour ratio;
- shape-source indicator;
- hub-like stop count based on a disclosed name pattern; and
- historic daily vehicle-kilometre proxy.

Validation fields come from `data/validated/route_validation.csv`. When no supplied row exists, the route is initialized as historic-only, active status uncertain, and unverified.

## Stage 8: ML service-intensity estimate

### Target

The target is `historic_daily_vehicle_km_proxy`:

```text
historic_daily_vehicle_km_proxy = route_length_km x historic_trips_per_day_estimate
```

It is not ridership, passenger demand, revenue, fuel use, or present-day vehicle-kilometres.

### Features

The supervised model uses:

- stop count;
- stops per kilometre;
- mean stop spacing;
- endpoint distance;
- geometry detour ratio;
- corridor population proxy;
- population-exposure overlap percentage;
- hub-connectivity count; and
- GTFS-shape indicator.

Headway, service window, trips per day, daily vehicle-kilometres, emissions score, climate score, final score, and rank are forbidden leakage fields.

### Training and selection

The training set contains 1,521 rows and 714 corridor groups. Five-fold `GroupKFold` keeps normalized corridor directions in the same fold. Numeric features use median imputation.

Two candidates are evaluated:

- histogram gradient boosting; and
- random forest.

The candidate with lower grouped-validation MAE is selected. The selected histogram gradient-boosting model records:

| Metric | Value |
|---|---:|
| MAE | 267.6992 |
| RMSE | 574.1447 |
| R-squared | 0.9907 |
| Median-baseline MAE | 4,850.3377 |
| Relative MAE improvement | 0.9448 |

The configured usefulness gate requires at least 2% relative MAE improvement. The selected model clears that gate.

### Use rule

The model prediction replaces nothing when the historic proxy is available. It is used only when the historic proxy is missing and the model passed the usefulness gate. In build `r2z-0cd49ad56aaa`, it supplies the daily VKT input for one route, `LTFRB_PUJ2451`.

This precedence is deliberate:

```text
validated current observation
  > accepted current administrative evidence
  > historic schedule-derived value
  > ML estimate
  > missing
```

The present implementation contains the historic-versus-ML fallback. The pilot protocol governs the future current-evidence overrides.

## Stage 9: corridor typology

`src/06_corridor_typology.py` applies median imputation, standardization, K-means, and a two-dimensional PCA projection.

Candidate cluster counts from 3 through 8 are evaluated. A cluster count is viable only when its smallest cluster contains at least 10 routes and at least 1% of the route universe. The viable candidate with the highest silhouette score is selected.

Three clusters are selected with silhouette 0.3730. Human-readable labels are assigned from cluster-centre patterns:

- Dense Urban Trunk;
- Long Regional Connector;
- High-Stop-Density Core; and
- Local Feeder.

Within each cluster, distance above the 95th percentile is flagged as an outlier. The current build contains 80 cluster outliers.

Typology is `ML_ESTIMATED`, interpretive, and excluded from the policy score.

## Stage 10: climate and energy engine

The climate engine selects daily VKT from the historic proxy or, for the one missing record, the approved ML estimate.

For each scenario:

```text
electrified_vkt = daily_vkt x electrification_share
diesel_liters_avoided = electrified_vkt / diesel_km_per_liter
baseline_co2e_kg_day = diesel_liters_avoided x diesel_kgco2e_per_liter
traction_kwh_day = electrified_vkt x electric_kwh_per_km
electricity_kwh_day = traction_kwh_day / charger_efficiency
grid_co2e_kg_day = electricity_kwh_day x grid_kgco2e_per_kwh
net_co2e_avoided_kg_day = baseline_co2e_kg_day - grid_co2e_kg_day
net_co2e_avoided_t_year = net_co2e_avoided_kg_day x operating_days / 1000
```

Shared assumptions are 300 operating days per year and 0.90 charger efficiency.

| Assumption | Low | Base | High |
|---|---:|---:|---:|
| Diesel efficiency, km/L | 6.00 | 5.00 | 4.00 |
| Diesel factor, kgCO2e/L | 2.68 | 2.68 | 2.68 |
| Electric energy, kWh/km | 1.05 | 0.75 | 0.55 |
| Grid factor, kgCO2e/kWh | 0.7181 | 0.55 | 0.35 |
| Electrification share | 0.30 | 0.50 | 0.70 |

`climate_impact_score` is the min-max score of the base-case annual net CO2e result. The climate fields are `SCENARIO`. They are not measured emissions or verified reductions.

The conservative low case is negative for every route in the current build. Base and high cases are positive for every route. Negative values are retained because they communicate technology and grid risk.

## Stage 11: equity

The WorldPop 2020 Philippines population-count raster is the only equity input in the documented reference build and is accessed through the optional population adapter.

The legacy spatial stage:

1. projects route lines to UTM Zone 51N;
2. buffers each line by 300 metres;
3. finds the 75th percentile of positive raster cells in a documented NCR analysis window;
4. calculates each buffer's population-weighted share in cells at or above that cutoff; and
5. min-max scales the share to 0-100.

Route2Zero 2.1 exposes this as `population_exposure_score`. The socioeconomic, accessibility-gap, and underserved-overlap components are null. Their weights are zero.

When available, the current equity score is therefore a `PROXY`. It must not be described as poverty, vulnerability, tenure, disability, accessibility, informal-settlement, or marginalized-community status. If the raster is absent, route IDs are preserved while population-exposure and dependent equity values are null with claim status `MISSING`; zero is not substituted.

## Stage 12: charging readiness

The charging stage uses the charging adapter to combine an optional cached OpenStreetMap screening snapshot with accepted records in `data/validated/charging_site_evidence.csv`. When the snapshot is present, nearest distances are measured from the route's two screening endpoints using a haversine BallTree.

Distance thresholds map to scores of 100, 82, 58, 32, or 8. Substation thresholds are 1, 3, 6, and 12 km. Charger thresholds are 1, 3, 8, and 15 km.

The score is:

```text
charging_readiness_score =
  0.35 x mapped_substation_proximity
  + 0.25 x mapped_charger_proximity
  + 0.15 x terminal_evidence
  + 0.25 x energy_manageability
```

Candidate-terminal counts and terminal/site evidence come only from accepted ledger rows. Site-control, utility-capacity, verified-capacity, and charging-site flags are aggregated from their recorded fields; a header-only ledger contributes no evidence. Energy manageability is the inverse min-max score of base-case electricity demand.

Mapped proximity is `PROXY`; accepted site or utility records retain the status supported by their evidence. Proximity does not establish ownership, capacity, interconnection approval, tariff, site control, access, or charger availability. If OSM is absent but accepted site evidence exists, only ledger-supported fields remain. If both sources are unavailable, proximity and charging-readiness values are null with claim status `MISSING`.

## Stage 13: operator readiness

The operator ledger accepts route-level, consent-based evidence. The scoring configuration covers all eight recorded components:

- verified fleet size;
- depot control;
- financing;
- organizational capacity;
- maintenance capability;
- willingness to participate;
- modernization experience; and
- charging-site access.

Fleet size is converted to a 0-100 component through versioned breakpoints. At least three component fields are required before the observed score is used. Present component weights are re-normalized over supplied fields, so missing evidence is not treated as zero. Evidence confidence increases with completeness but is capped at 90.

If sufficient evidence is not present:

- `operator_effective_score = 50`;
- `operator_claim_status = NEUTRAL_PRIOR`;
- `operator_evidence_confidence = 5`; and
- `operator_readiness_placeholder = true`.

The current ledger is empty, so all 1,522 routes retain the neutral prior.

## Stage 14: evidence confidence

Evidence confidence is not model accuracy and is not rank stability.

The deterministic score uses:

| Component | Weight |
|---|---:|
| Freshness | 0.20 |
| Directness | 0.20 |
| Spatial specificity | 0.20 |
| Completeness | 0.20 |
| External validation | 0.15 |
| Model reliability | 0.05 |

Validation-status values map to freshness and external-validation scores. `historic_only` maps to 10; field checked maps to 90. Directness is the mean of climate, equity, charging, and operator confidence. Spatial specificity combines 65% geometry reliability and 35% charging evidence confidence. Completeness counts available climate, equity, charging, operator, and geometry evidence.

Grades are A at 80 or above, B at 65 or above, C at 35 or above, and D below 35.

The current grade distribution is 1,519 C and 3 D. No route has A or B evidence in this build.

## Stage 15: human-controlled priority model

The default score is:

```text
priority_score =
  0.40 x climate_impact_score
  + 0.30 x equity_score
  + 0.15 x charging_readiness_score
  + 0.15 x operator_effective_score
```

All four components are complete for all 1,522 records. Ranks use descending score order with stable first-occurrence tie handling.

The scenario identity hashes the title, weights, climate assumption set, validation filter, and policy-model version. The current scenario is `scn-e0f12f397e`.

The score stage records:

- `ranking_method = versioned_human_controlled_weighted_sum`;
- `llm_ranking_influence = false`;
- `ml_typology_used_for_score = false`;
- `climate_model_type = deterministic_low_base_high_scenario`; and
- `human_policy_control = true`.

## Stage 16: city tags

Route descriptions and names are matched against a disclosed alias dictionary. Ordered matches become `cities_served`; the first becomes `primary_city`.

Every current city tag has method `text_fallback` and confidence `low_requires_boundary_validation`. The tags are not administrative-boundary joins and must be checked with city partners, especially for cross-boundary corridors.

## Stage 17: rank stability

Sensitivity runs three reproducible fixed-seed modes with 5,000 draws each:

- `around_default`: concentrated Dirichlet draws around the approved default weights;
- `broad_simplex`: broad Dirichlet draws across the policy-weight simplex; and
- `custom`: configured bounded per-dimension draws, normalized to sum to one.

The default `sensitivity.csv` fields attached to route scores continue to use `around_default`. The combined mode output is written separately so broad and custom stress tests do not silently redefine the default rank-stability interpretation.

For each route, Route2Zero records:

- top-5 probability;
- top-10 probability;
- top-20 probability;
- median rank;
- P10 and P90 rank;
- P10 and P90 score; and
- a derived stability score.

The stability score assigns 70% weight to top-10 frequency and 30% to a capped P10-P90 rank-width term.

Robust priority requires at least 0.70 top-10 probability. A route can remain scenario-dependent even when selected into the constrained portfolio. Stability does not upgrade evidence grade.

## Stage 18: Phase-1 portfolio selection

The selector calculates:

```text
portfolio_objective =
  0.60 x priority_score
  + 0.25 x (top_10_probability x 100)
  + 0.15 x evidence_confidence
```

It filters by minimum evidence grade and equity score, then scans eligible routes in descending objective order while enforcing city, corridor-direction, evidence-limited, and maximum-count constraints. Baseline selection and value-of-information tests call the same deterministic selector.

This is deterministic constrained selection, not mixed-integer optimization and not a financial optimizer. It has no budget constraint. A separate 2.1 feasibility screen supplies order-of-magnitude fleet and capital proxies but explicitly excludes depot, civil, grid, battery, operating, tax, insurance, and financing costs. If the requested count cannot be filled, the selector returns an explicit `infeasible` result with no selected routes and constraint diagnostics; it never relaxes constraints silently.

## Stage 19: feasibility cost screen

`src/14b_feasibility_cost.py` divides daily VKT by a 120 km/day vehicle proxy, rounds fleet and charger counts upward, and applies DOE planning values of PHP 2.5 million per four-wheel BEV and PHP 0.5 million per four-wheel charging station. All resulting fleet and cost fields are `PROXY`; financing is `MISSING`. The Phase-1 output is approximately 1,943 vehicles, 102 charging stations, and PHP 4.9085 billion in vehicle-plus-charger capital. This is an evidence-acquisition starting point, not a quote or budget.

The current scenario selects eight routes and is feasible. It differs from the simple top-eight list by four added and four removed route IDs.

## Stage 20: value of information

For every route, six uncertain fields are perturbed through configured low/high ranges:

- geometry reliability;
- service intensity;
- climate assumptions;
- operator readiness from 30 to 70;
- charging readiness by plus or minus 20, bounded to 0-100;
- equity population exposure by plus or minus 15, bounded to 0-100.

Geometry and service perturbations propagate through their affected climate inputs rather than being added as policy dimensions. Each perturbation recomputes the affected score and reruns the same deterministic selector used for the baseline portfolio. The stage records maximum rank swing, actual low/high membership changes, `portfolio_flip_possible`, and a validation-priority score.

The method creates six route-field records per route. It is a deterministic local perturbation screen, not a causal value-of-information model and not a monetary valuation.

## Stage 21: planning assistant

The current pipeline writes structured deterministic route explanations and a portfolio summary. Each response cites route IDs, fields, scenario ID, portfolio ID, uncertainty notes, and validation actions.

The current cache source is `deterministic_fallback`. The Netlify Function can optionally call an OpenAI-compatible chat endpoint using a server-side key. Its prompt restricts the model to supplied ranked facts.

LLM output never enters the scoring table, climate engine, sensitivity simulation, constraint set, or portfolio selector. `llm_ranking_influence` is false.

## Stage 22: final manifest

The finalizer checks for all required outputs, hashes configuration and source inputs, records model versions and random seeds, writes build IDs into the score files, selects the flagship route using the declared rule, and writes the pipeline report.

Build `r2z-0cd49ad56aaa`, generated from commit `fc151f33f366407ea7de18ad0184e8fb3faef341`, reports:

- 1,522 rows processed;
- 1,522 complete scores;
- 20 dated current external route records, all with active status uncertain;
- 22 usable source geometries, including 20 OSM relations and two GTFS shapes;
- 9 robust priorities;
- 8 Phase-1 corridors; and
- `PASS_WITH_WARNINGS`.

The build identity depends on configuration checksums, source checksums, model versions, policy scenario ID, and portfolio scenario ID. The build timestamp is not part of the identity.

## Interpretation rules

1. Priority answers what rises under the selected policy lens.
2. Evidence confidence answers how strong and specific the current evidence is.
3. Prediction metrics answer how the service model performed against its historic target.
4. Rank stability answers how rank changes under tested policy weights.
5. Value of information answers which tested input range can change the decision most.
6. Portfolio membership answers which routes satisfy the current constraints.
7. None of these fields alone establishes implementation feasibility.

## Required pilot overrides

Before investment use, a city pilot must:

- confirm whether shortlisted routes currently operate;
- collect present headway and service-window observations;
- verify route geometry;
- record consent-based operator evidence;
- request formal utility and site evidence;
- calibrate vehicle-efficiency, electricity, and operating-day assumptions;
- add defensible socioeconomic and accessibility indicators;
- validate city boundaries and corridor normalization;
- test model performance against current observations; and
- approve weights, constraints, and decision rights.

The validation protocol in `docs/validation_protocol.md` defines the minimum process.
