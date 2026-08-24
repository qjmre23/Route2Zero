# Route2Zero 2.1 changelog

Release date: 24 August 2026

Route2Zero 2.1 hardens the evidence layer behind the hackathon submission. The release keeps the historic 1,522-record screening universe but adds dated external route evidence, observed road geometry, feasibility proxies, visible claim labels, and a tighter reproducibility and licensing boundary.

## A1 and A7 — current route evidence and usable geometry

- Retrieved a dated Overpass snapshot of Metro Manila `route=bus` + `bus=share_taxi` relations using the documented local OpenStreetMap convention.
- Added a reviewed, one-to-one configuration for 20 corridor/relation matches edited on or after 1 January 2023.
- Added a pipeline stage that emits `osm_route_validation.csv` and `osm_route_geometry.geojson` from the saved snapshot.
- Labels each match `current` only as a dated external record, keeps active service `uncertain`, and labels member-way geometry `OBSERVED` rather than agency-verified.
- Uses the actual OSM member-way geometry for route length and map rendering. The usable-geometry count rises from two GTFS shapes to 22 source geometries: two GTFS shapes and 20 OSM relations.
- Checked the current LTFRB LPTRP index. No defensible route-level Metro Manila match was accepted, so `official_plan_status` remains `MISSING`.

## A2 — operator evidence search

- Recorded a route-specific desk-search attempt for all eight Phase-1 corridors.
- Accepted one named current external reference for Bagong Silang Transport Service Cooperative on `LTFRB_PUJ1405`.
- Kept every readiness score at `NEUTRAL_PRIOR` because a name alone does not establish fleet, depot, financing, maintenance, willingness, or charging-site readiness.

## A3 — climate communication

- Changed Route Lens, leaderboard, portfolio, and export framing to lead with the deterministic base case.
- Shows low/high values as a bounded range and explains that the negative low case results from high electricity use combined with a carbon-intensive grid.
- Identifies vehicle efficiency as the dominant low-case sensitivity, followed by grid intensity; electrification share changes magnitude rather than sign.

## A4 — feasibility proxy

- Added route-level fleet, charger, vehicle-capital, charger-capital, and total-capital proxy fields.
- Added `feasibility_cost_routes.csv` and `feasibility_cost_scenarios.json`.
- Uses a reported 120 km vehicle range and DOE planning values for a four-wheel BEV, EV charging station, and vehicles served per station.
- Labels fleet and cost outputs `PROXY`, financing `MISSING`, and lists depot, interconnection, civil works, battery, tariff, insurance, financing, and operating costs that are excluded.

## A5 and A6 — reproducibility and licensing

- Extended the final manifest to checksum OSM evidence and feasibility outputs and record current-evidence, geometry, and operator-search counts.
- Added an MIT license for project-authored code and documentation only.
- Added a notice that preserves the separate DOTC GTFS terms, OSM ODbL attribution/share-alike obligation, WorldPop CC BY 4.0 attribution, Mapbox terms, and publication-specific boundaries.
- Removed the tracked local `.env` file from version control and added a non-secret `.env.example`.

## A8 and A10 — visible claim labels and model restraint

- Added color-coded badges for all eight claim statuses across Route Lens, map popups, evidence requests, climate explanation, validation evidence, and feasibility fields.
- Added a model-restraint comparison showing the single corridor where an ML estimate fills a missing historic activity input. The model does not infer current service or ridership.

## A9 — second equity signal investigation

- Registered the current PSA city and municipal poverty small-area estimates as a candidate source.
- Did not integrate them because route-to-city assignment remains text-derived and the source is city-level; integration now would create false spatial precision.
- Kept socioeconomic, accessibility-gap, and settlement-status fields `MISSING` and named spatial route-city validation as the next step.

## A11 and A12 — narrative cleanup

- Removed superseded score, weighting, and slogan references from current code and documentation.
- Reframed the README for a non-technical city decision-maker before the release snapshot.

## Responsible-AI boundary preserved

ML still estimates one missing input at a time. Deterministic models calculate climate, evidence, sensitivity, and portfolio outputs. Humans control weights and constraints. The language model may explain structured evidence but has no ranking influence and cannot edit scores, ranks, climate values, weights, or portfolio constraints.
