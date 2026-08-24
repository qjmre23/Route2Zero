# Route2Zero 2.1 data provenance

## Provenance contract

Route2Zero treats raw source snapshots as immutable, pilot evidence as controlled input, and processed outputs as reproducible derivatives. Every registered source records its organization, URL, retrieval date, reference period, geography, spatial resolution, license, source type, currentness, notes, local path, requirement status, availability, and SHA-256 checksum when available.

This document describes the source manifest used by build `r2z-d4c8d4cc709a`.

## Source inventory

| Source ID | Reference period | Type | Requirement | Principal use |
|---|---|---|---|---|
| `sakay_gtfs_master_historic` | 2013-2020 | Administrative/community GTFS | Required | Route universe, stops, schedules, screening geometry |
| `worldpop_phl_2020_1km` | 2020 | Proxy raster | Optional | Population-exposure equity proxy |
| `doe_luzon_generation_2024` | 2024 | Government administrative context | Required | Grid and climate scenario context |
| `osm_power_snapshot_2026_08_20` | Snapshot 20 Aug 2026 | Proxy map data | Optional | Mapped substation and charger proximity |
| `osm_share_taxi_routes_2026_08_24` | Snapshot 24 Aug 2026 | Observed external map data | Required | Dated route records and member-way geometry |
| `osm_metro_manila_route_conventions_2026_08_24` | Retrieved 24 Aug 2026 | Method reference | Required | Local `route=bus` + `bus=share_taxi` interpretation |
| `ltfrb_lptrp_index_2026_08_24` | Retrieved 24 Aug 2026 | Administrative reference | Required | Official-plan cross-check; no route-level match accepted |
| `doe_energy_investment_kit_2024` | 2024 | Government publication | Required | Vehicle and charger planning-cost proxies |
| `pna_ejeepney_trial_2023` | 2023 | Reported observation | Required | 120 km fleet-sizing proxy |
| `psa_poverty_sae_candidate_2026_08_24` | 2023 estimates | Candidate proxy | Required | Registered next equity source; not integrated |
| `route2zero_climate_scenario_v1` | Pilot scenario | Project assumption set | Required | Low/base/high climate and energy calculations |
| `route2zero_operator_prior_v1` | Pilot prior | Project placeholder | Required | Neutral operator prior when evidence is missing |

The generated source manifest is authoritative for the exact registry checksum, availability states, and source count of a build. Controlled route, operator, charging-site, and stakeholder ledgers are also registered inputs; a header-only ledger is an available input with no accepted evidence.

## Optional-source behavior

WorldPop and the OSM infrastructure snapshot are optional enrichment layers, not prerequisites for preserving the route universe. When either file is absent, the source manifest records `available = false` and a null checksum. Dependent fields are emitted as null with claim status `MISSING` where feasible. The pipeline must not substitute zero, a favorable default, or a fabricated terminal/site count. A downstream portfolio may consequently be explicitly infeasible under its configured equity or evidence constraints.

## 1. Historic GTFS baseline

### Source

- Repository: <https://github.com/sakayph/gtfs/tree/master>
- Organization: Sakay.ph contributors
- Local path: `data/raw/gtfs_master/`
- Retrieval date: 14 August 2026
- Reference period: 2013-2020
- Manifest checksum: `3a16a1cdce421bf7240355540bdc72f6eea7ecadaa4789c349f501ca1845d4c7`
- License: upstream `LICENSE.md`

The feed is a historic network baseline. Route2Zero does not represent its records as active 2026 service.

### Audit result

| GTFS file | Rows |
|---|---:|
| `routes.txt` | 1,717 |
| `trips.txt` | 1,864 |
| `stops.txt` | 4,858 |
| `stop_times.txt` | 79,414 |
| `shapes.txt` | 520 |
| `frequencies.txt` | 1,864 |
| `calendar.txt` | 20 |
| `agency.txt` | 6 |

The referential audit reports zero missing trip-to-route, stop-time-to-stop, and frequency-to-trip references.

### Route universe

The build selects LTFRB route IDs containing `PUJ`, producing 1,522 route-direction records. It preserves one row per route ID and also creates a grouped corridor view. `PUJ` identifies the feed's jeepney route records; it does not establish current franchise or operating status.

### Geometry

Twenty jeepney records use reviewed OSM member-way geometry and two use GTFS shapes. The remaining 1,500 records use representative-trip stops connected in order. Each feature records `geometry_source`; every approximate geometry is marked for validation.

### Service

Frequency and calendar fields produce a historic typical-weekday service proxy for 1,521 routes. This is `DERIVED` from the feed. It is not an observation and does not establish actual completed trips.

## 2. WorldPop population raster

- Title: Philippines 2020 population-count raster
- DOI: <https://doi.org/10.5258/SOTON/WP00670>
- Organization: WorldPop, University of Southampton
- Local path: `data/raw/reference/phl_ppp_2020_1km_Aggregated.tif`
- Retrieval date: 14 August 2026
- Reference period: 2020
- Approximate resolution: 1 km
- Manifest checksum: `db87b488519157ec83fb43e2c867016ca72115fde193a9565b650ee35d6699fd`

Route2Zero uses this raster only for population exposure. It is not a poverty layer, accessibility survey, tenure map, vulnerability index, or informal-settlement boundary.

The route method uses a 300 m buffer and a high-density cutoff calculated within the documented NCR analysis window. Because the raster resolution is coarser than the buffer width, the output is explicitly a proxy with low conceptual and spatial confidence.

No socioeconomic, accessibility-gap, or underserved-settlement input is available in the current build. Those fields remain null.

If the raster is unavailable in a later build, the population adapter preserves route IDs but emits null population-exposure and equity values with `MISSING` status. Absence of the optional raster is not evidence of low exposure.

## 3. Philippine Department of Energy context

- Source organization: Philippine Department of Energy
- Local path: `data/raw/reference/doe_2024_luzon_generation_mix.csv`
- Retrieval date: 14 August 2026
- Reference period: 2024
- Geography: Luzon
- Manifest checksum: `9c6928ae13f3f4b98c4e16aa8e12bf1c5b4cc547368f3ef426bce35464e1b5d6`

The source provides regional generation and grid-emissions context. It does not contain route-, depot-, feeder-, transformer-, or charging-site capacity.

The retained legacy grid proxy uses 14,550 GWh renewable generation divided by 90,269 GWh total generation, or 16.118%. Route2Zero 2.1 also uses a 0.7181 kgCO2e/kWh current-grid context in the climate configuration.

These values are historic regional context. They must not be presented as present route-level electrical capacity.

## 4. OpenStreetMap infrastructure snapshot

- Source: <https://www.openstreetmap.org/copyright>
- Organization: OpenStreetMap contributors
- Local path: `data/raw/osm_power/metro_manila_overpass.json`
- Retrieval date: 20 August 2026
- Geography: Metro Manila regional bounding box
- License: ODbL 1.0
- Manifest checksum: `92d52bde6f3f00640693d5c6a2e4234d1fd7fd6ca46a918a1261e776aba32516`

The cached snapshot contains 138 qualifying elements used by the parser: 117 mapped substations and 21 mapped charging stations with usable coordinates.

The source is `mixed` currentness because mapping completeness, feature existence, and tags may vary. Nearest-feature distance is a screening proxy only. It does not establish:

- utility ownership;
- feeder or transformer capacity;
- interconnection feasibility;
- site control;
- charger power, compatibility, uptime, or public access;
- depot access; or
- tariff and connection cost.

Mapped proximity is combined only with accepted rows from `data/validated/charging_site_evidence.csv`. Candidate-terminal counts, site-control flags, utility-capacity flags, verified capacity, and terminal evidence are data-driven from that ledger; no route receives a fixed terminal count or terminal-evidence score. In a header-only ledger, the mapped snapshot remains proxy evidence and verification flags remain false. If both mapped infrastructure and accepted site evidence are unavailable, charging proximity/readiness fields are null with status `MISSING`.

## 5. Climate scenario configuration

- Local path: `config/climate_scenarios.json`
- Version: `climate-v1.0`
- Manifest source ID: `route2zero_climate_scenario_v1`
- Checksum: `1e6645f7ff7dec0c272816cfde3ea986559d0ad2f5d51438c8951f32ef75593c`

The file defines low, base, and high planning assumptions for vehicle efficiency, electric energy use, grid factor, electrification share, charger efficiency, and operating days.

This is a project scenario source, not an observed dataset. Every climate result is `SCENARIO`. The assumptions require pilot calibration with actual vehicles, operators, charging design, and utility evidence.

The current low case is intentionally conservative and produces negative net scenario CO2e throughout the route universe. Negative results are retained.

## 6. Operator neutral prior

- Local path: `config/operator_readiness_config.json`
- Version: `operator-v2.0`
- Manifest source ID: `route2zero_operator_prior_v1`
- Checksum: `52fcf040b400c757380c3aca16542d3b4132c9869a9511f2c12773dedb1c50cc`

The neutral prior is 50/100. It is used only when fewer than three evidence components are present in the consent-based operator ledger.

The operator method consumes all eight configured components when supplied: verified fleet size, depot control, financing, organizational capacity, maintenance capability, willingness to participate, modernization experience, and charging-site access. Fleet-size conversion, weights, completeness, and sufficiency thresholds are versioned assumptions; missing components are omitted and present weights are re-normalized rather than treating missing as zero.

The current operator ledger is header-only. Therefore:

- observed operator routes: 0;
- neutral-prior routes: 1,522; and
- operator claim status: `NEUTRAL_PRIOR` for every route.

The prior is not a measurement of willingness, capacity, finance readiness, organization, fleet, or depot control.

## Validated pilot ledgers

The repository defines four controlled ledgers under `data/validated/`:

### `route_validation.csv`

Holds route status, activity status, date, validator, source type and reference, observed origin and destination, observed headway and service window, geometry-verification flag, operator name, and evidence quality.

### `operator_evidence.csv`

Holds consent-based operator name, evidence date, fleet size, depot control, financing, organizational capacity, maintenance capability, willingness, modernization experience, charging-site access, source reference, verifier, and notes. Accepted rows are consumed directly by the operator adapter and scored with all eight configured components.

### `charging_site_evidence.csv`

Holds site name, date, coordinates, site-control status, utility-capacity status, available capacity where formally provided, source reference, verifier, and notes. Accepted rows drive terminal counts and site/utility verification; coordinates alone do not verify capacity.

### `stakeholder_validation.csv`

Holds stakeholder type, organization, date, route, workflow component, feedback, evidence change, permission to quote, and source reference.

All four controlled ledgers contain headers only in build `r2z-d4c8d4cc709a`. A separate reviewed OSM configuration supplies 20 dated current external route records and observed member-way geometries. The score table still reports zero field-confirmed active-service records, zero observed operator readiness scores, zero verified utility-capacity records, and zero verified charging sites.

### Reviewed OSM route evidence

The immutable Overpass snapshot contains 299 Metro Manila and adjoining `route=bus` + `bus=share_taxi` relations. `config/osm_route_matching.json` records 20 manually reviewed one-to-one name/endpoint matches with relation IDs, matching rationale, and a minimum edit date of 1 January 2023. The pipeline derives `osm_route_validation.csv` and `osm_route_geometry.geojson`; it never treats the configuration as proof of active service. OSM data remains under ODbL 1.0 and must retain contributor attribution and share-alike obligations where an adapted database is publicly distributed.

## Evidence precedence

The intended precedence for a field is:

1. accepted, date-stamped, current verification;
2. accepted current observation;
3. accepted current administrative source;
4. historic administrative or schedule-derived value;
5. versioned model estimate;
6. proxy;
7. neutral prior; and
8. missing.

Higher precedence does not automatically mean higher quality. Conflicting evidence must be recorded and resolved, not silently overwritten.

## Transformation lineage

The principal lineage is:

```text
source_registry.json
  -> source_manifest.json
historic GTFS
  -> audit_report.md
  -> jeepney_routes.geojson
  -> geometry_reliability.csv
  -> route_frequency.csv
  -> route_features.csv
route_features.csv
  -> ml_service_intensity.csv
  -> corridor_typology.csv
service input + climate config
  -> climate_impact.csv
WorldPop
  -> equity_score.csv
  -> equity_v2.csv
optional OSM + charging-site ledger + climate demand
  -> charging_readiness.csv
validated operator ledger + prior config
  -> operator_readiness_v2.csv
all evidence layers
  -> evidence_confidence.csv
policy config + analytical layers
  -> route2zero_scores.csv/.geojson
scores
  -> sensitivity.csv
  -> sensitivity_modes.csv
  -> portfolio_scenarios.json
  -> validation_priorities.json
  -> route_planner_cache.json
all required outputs
  -> build_manifest.json
```

## Manifest and checksum behavior

`src/19_finalize_manifest.py` records:

- configuration checksums;
- source checksums;
- output checksums;
- model versions;
- scenario IDs;
- random seeds;
- build ID;
- build timestamp;
- flagship route; and
- pipeline warnings.

A missing required source remains a build error. A missing optional source remains a manifest row with `available = false`, null checksum, and an explicit warning; it is excluded from checksum derivation without being erased from provenance. Available but empty ledgers retain their file checksum and zero accepted rows.

The build ID is derived from configuration checksums, source checksums, model versions, policy scenario ID, and portfolio scenario ID. It is stable for identical logical inputs. The timestamp is recorded separately.

The current manifest records Git commit `47cf3c9554ab392938f2ba5ae3ca98d5d369ff61`. Because the Route2Zero 2.1 work was present in a working tree during generation, a release process seeking a one-to-one code attestation should commit the final files and rerun the pipeline so the manifest records that release commit.

## Source-status rules for publication

- Never call the historic GTFS current service.
- Never call WorldPop a marginalized-settlement map.
- Never call OSM proximity utility capacity.
- Never call the operator prior observed readiness.
- Never call climate scenarios measured reductions.
- Never call a model estimate passenger demand.
- Never treat city text tags as validated administrative joins.
- Never convert absence of evidence into evidence of low need.
- Publish missing optional WorldPop or OSM layers as `MISSING`/null, not zero.
- Never treat a header-only operator or charging ledger as accepted evidence.

## Updating a source

When a source changes:

1. preserve the prior snapshot or tag its release;
2. update `config/source_registry.json` with the new reference period and retrieval date;
3. record license and attribution changes;
4. run the complete pipeline;
5. compare row counts, checksums, model metrics, scenario IDs, ranks, stability, and portfolio membership;
6. review any claim-status changes;
7. update documentation only from regenerated outputs; and
8. retain a change record for material decision changes.

Partial manual edits to `data/processed/` are not a valid update process.
