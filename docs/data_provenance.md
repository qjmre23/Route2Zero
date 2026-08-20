# Route2Zero 2.0 data provenance

## Provenance contract

Route2Zero treats raw source snapshots as immutable, pilot evidence as controlled input, and processed outputs as reproducible derivatives. Every registered source records its organization, URL, retrieval date, reference period, geography, spatial resolution, license, source type, currentness, notes, local path, and SHA-256 checksum.

This document describes the source manifest used by build `r2z-16690ccbe328`.

## Source inventory

| Source ID | Reference period | Type | Currentness | Principal use |
|---|---|---|---|---|
| `sakay_gtfs_master_historic` | 2013-2020 | Administrative/community GTFS | Historic | Route universe, stops, schedules, screening geometry |
| `worldpop_phl_2020_1km` | 2020 | Proxy raster | Historic | Population-exposure equity proxy |
| `doe_luzon_generation_2024` | 2024 | Government administrative context | Historic | Grid and climate scenario context |
| `osm_power_snapshot_2026_08_20` | Snapshot 20 Aug 2026 | Proxy map data | Mixed | Mapped substation and charger proximity |
| `route2zero_climate_scenario_v1` | Pilot scenario | Project assumption set | Current configuration | Low/base/high climate and energy calculations |
| `route2zero_operator_prior_v1` | Pilot prior | Project placeholder | Current configuration | Neutral operator prior when evidence is missing |

The manifest contains six registered sources. Its registry checksum is `8dd43371168d76a8a6cd298d10a9a3a43aaf2533143afd2e6db405c4d38395c9`.

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

Two jeepney route records have usable GTFS shapes. The remaining 1,520 records use representative-trip stops connected in order. Each feature records `geometry_source`. All approximate geometries are marked for validation.

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

## 3. Philippine Department of Energy context

- Source organization: Philippine Department of Energy
- Local path: `data/raw/reference/doe_2024_luzon_generation_mix.csv`
- Retrieval date: 14 August 2026
- Reference period: 2024
- Geography: Luzon
- Manifest checksum: `9c6928ae13f3f4b98c4e16aa8e12bf1c5b4cc547368f3ef426bce35464e1b5d6`

The source provides regional generation and grid-emissions context. It does not contain route-, depot-, feeder-, transformer-, or charging-site capacity.

The retained legacy grid proxy uses 14,550 GWh renewable generation divided by 90,269 GWh total generation, or 16.118%. Route2Zero 2.0 also uses a 0.7181 kgCO2e/kWh current-grid context in the climate configuration.

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

Both `utility_capacity_verified` and `charging_site_verified` are false for every route in this build.

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

Holds consent-based operator name, evidence date, fleet size, depot control, financing, organizational capacity, maintenance capability, willingness, modernization experience, charging-site access, source reference, verifier, and notes.

### `charging_site_evidence.csv`

Holds site name, date, coordinates, site-control status, utility-capacity status, available capacity where formally provided, source reference, verifier, and notes.

### `stakeholder_validation.csv`

Holds stakeholder type, organization, date, route, workflow component, feedback, evidence change, permission to quote, and source reference.

All four ledgers contain headers only in build `r2z-16690ccbe328`. The processed score table therefore reports zero current validations, zero observed operator scores, zero verified utility-capacity records, and zero verified charging sites.

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
OSM + climate demand
  -> charging_readiness.csv
validated operator ledger + prior config
  -> operator_readiness_v2.csv
all evidence layers
  -> evidence_confidence.csv
policy config + analytical layers
  -> route2zero_scores.csv/.geojson
scores
  -> sensitivity.csv
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

The build ID is derived from configuration checksums, source checksums, model versions, policy scenario ID, and portfolio scenario ID. It is stable for identical logical inputs. The timestamp is recorded separately.

The current manifest records Git commit `47cf3c9554ab392938f2ba5ae3ca98d5d369ff61`. Because the Route2Zero 2.0 work was present in a working tree during generation, a release process seeking a one-to-one code attestation should commit the final files and rerun the pipeline so the manifest records that release commit.

## Source-status rules for publication

- Never call the historic GTFS current service.
- Never call WorldPop a marginalized-settlement map.
- Never call OSM proximity utility capacity.
- Never call the operator prior observed readiness.
- Never call climate scenarios measured reductions.
- Never call a model estimate passenger demand.
- Never treat city text tags as validated administrative joins.
- Never convert absence of evidence into evidence of low need.

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
