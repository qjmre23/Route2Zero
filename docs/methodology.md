# Route2Zero scoring methodology

## Decision question

Route2Zero asks a supply-side policy question: **which Metro Manila jeepney corridors should enter electrification validation first, and why?** It is not a rider trip planner and it does not automate an investment decision. It produces an auditable shortlist for regulators, LGUs, operators, financiers, and affected communities.

## Unit of analysis

The canonical `master` branch of the Sakay GTFS feed contains 1,717 routes. Route IDs self-classify exactly: LTFRB IDs containing `PUJ` define 1,522 jeepney route-direction records; IDs containing `PUB` define 189 bus records. Route2Zero scores only the 1,522 jeepney records.

Routes with the same `route_long_name` commonly represent opposite directions. `data/processed/route_corridors.csv` offers a de-duplicated corridor view with `direction_count`, while map geometry and scores preserve each GTFS route ID as required by the MVP specification.

## Geometry and distance

Geometry uses a two-tier method:

1. **GTFS shape:** use the ordered points in `shapes.txt` when a representative trip has a valid shape ID.
2. **Stop-sequence approximation:** select the trip with the most stop-time records for each route, resolve its stops, and connect them in `stop_sequence` order.

Only 2 jeepney routes have usable shapes; 1,520 use stop-sequence approximations. Every feature carries `geometry_source`. Approximate paths connect stops directly and are not snapped to the road network. Length is the WGS84 geodesic distance along the resulting line, not endpoint distance.

## Service-frequency estimate

Trips are eligible when their calendar service has `monday = 1` or an explicit `WEEKDAYS`/`DAILY` service ID. Frequency rows are joined to trips and routes. For each route:

- `avg_headway_min` is the mean `headway_secs / 60` across eligible frequency rows.
- `daily_service_window_hrs` is the union of eligible start/end intervals, preventing overlapping intervals from being double-counted.
- `trips_per_day_estimate = daily_service_window_hrs × 60 / avg_headway_min`.

This is a planning proxy, not a vehicle-block simulation. One route has no qualifying weekday frequency and retains null frequency, emissions, composite score, and rank.

## Dimension 1: emissions-reduction potential

### Formula

`daily_vehicle_km_proxy = length_km × trips_per_day_estimate`

The result is min-max scaled over routes with available values:

`emissions_potential_score = 100 × (value - minimum) / (maximum - minimum)`

### Interpretation

The metric is relative service activity. It prioritizes longer, more frequently served routes because replacing combustion vehicles on active corridors may address more vehicle-kilometres. It is **not measured emissions**: the feed lacks route-level fuel use, engine condition, occupancy, fleet age, and actual completed trips. The dashboard always calls it an emissions *activity proxy*.

## Dimension 2: equity

### Source-selection outcome

No retrievable NAMRIA or PSA informal-settlement polygon layer was available at corridor resolution. Route2Zero therefore uses the documented WorldPop fallback: the 2020 Philippines 1 km population-count raster, DOI `10.5258/SOTON/WP00670`.

### Formula

1. Project route lines into UTM Zone 51N and create a 300 m buffer.
2. Within a documented NCR analysis window, calculate the 75th percentile of positive WorldPop cells.
3. For each buffered route, calculate the population-weighted share lying in cells at or above that threshold.
4. Min-max scale that share to a 0-100 `equity_score`.

### Interpretation

This is a **high-density service-exposure proxy**, not a map of informal settlements, poverty, tenure, vulnerability, or individual riders. Its 1 km resolution is coarse relative to a 300 m catchment. It is useful for an MVP screen but must be replaced or validated with barangay and community data during the pilot. Fields explicitly state `worldpop_2020_1km_population_density_proxy` and low confidence.

## Dimension 3: grid feasibility

### Source and formula

Philippine DOE 2024 Key Energy Statistics report 14,550 GWh renewable generation and 90,269 GWh total generation for Luzon. Route2Zero uses:

`grid_feasibility_score = 100 × 14,550 / 90,269 = 16.118`

The supporting 2019-2021 Luzon-Visayas combined-margin factor for other projects is 0.7181 tCO2/MWh and is stored as context.

### Interpretation

Every route receives the same score because Metro Manila is modeled with a single regional electricity baseline. This is the least granular dimension. It does not measure feeder headroom, transformer condition, depot access, charger interconnection time, tariff, renewable procurement, or resiliency. Depot-level utility data is the highest-value pilot refinement.

## Dimension 4: operator readiness

No public per-route cooperative financing dataset was found. Every route therefore receives a neutral `operator_readiness_score = 50`. This value is a visible placeholder, never presented as evidence.

`data/processed/operator_overrides.csv` allows authorized pilot teams to add route ID, 0-100 score, and notes. Re-running Tasks 8 onward applies valid overrides and labels them `pilot_workshop_override`; all other routes remain placeholders.

## Composite Just Transition Score

Default weights are named constants:

| Dimension | Default weight |
|---|---:|
| Emissions activity proxy | 0.35 |
| Equity density proxy | 0.35 |
| Grid regional proxy | 0.15 |
| Operator placeholder/override | 0.15 |

For complete rows:

`just_transition_score = 0.35E + 0.35Q + 0.15G + 0.15O`

Routes are ranked descending. The dashboard lets users adjust weights and normalizes them to sum to one. A hypothetical route with missing equity stays out of ranked results by default. If explicitly included, its score is renormalized over available dimensions and multiplied by 0.85 to communicate reduced confidence. No current route needs that fallback because WorldPop covers all 1,522 geometries.

## City tagging

Primary and served cities are extracted from `route_desc` and `route_long_name` using a documented alias dictionary for NCR and adjacent cities. The result is a text-derived planning index, not an administrative-boundary spatial join. Users should validate cross-city routes in the pilot.

## AI explanation boundary

The ranking is 100% deterministic weighted arithmetic. Qwen through the Mantle/Bedrock gateway is used only after scoring to phrase already-computed facts in plain language. Prompts explicitly prohibit new claims. Outputs are cached per route and labeled `mantle_bedrock_api`; any error returns a deterministic score-based sentence. The dashboard remains fully functional offline. Every record carries `ranking_ai_influence = false`.

## Reproducibility and safeguards

- Raw GTFS and reference files are never overwritten.
- All scripts resolve paths from the project root and are safe to re-run.
- Processed outputs preserve nulls rather than inventing values.
- Proxy, placeholder, source, and confidence fields travel with each route.
- The audit checks every trip-route, stop-time-stop, and frequency-trip reference.
- Dashboard language distinguishes measured fields, derived values, proxies, and placeholders.

## MVP limitations and pilot refinements

1. Refresh the historic 2013-2020 GTFS baseline through LTFRB/LGU validation.
2. Replace stop chords with verified, road-snapped paths.
3. Replace 1 km density with settlement, poverty, tenure, and community-validated accessibility evidence.
4. Add depot, feeder, tariff, and interconnection data from Meralco and LGUs.
5. Collect cooperative fleet, financing, governance, and consolidation-readiness information.
6. Validate weights in workshops and publish sensitivity analysis.
7. Add actual fuel, fleet, ridership, and air-quality measurements before estimating tonnes of emissions avoided.

## Primary sources

- Sakay GTFS: `https://github.com/sakayph/gtfs`
- WorldPop 2020 Philippines population grid: `https://hub.worldpop.org/geodata/summary?id=33241`
- Philippine DOE 2024 Key Energy Statistics: `https://prod-cms.doe.gov.ph/documents/d/guest/-final-11-20-25_doe-key-energy-stat-pocket-size-2024-pdf`
- Philippine DOE National Grid Emission Factor context: `https://doe.gov.ph/sites/default/files/pdf/pep/PEP_2023-2050_Volume_III.pdf`

