# Route2Zero notices and data attributions

The MIT license in `LICENSE` applies only to software and documentation authored for Route2Zero. Each upstream dataset, map source, and publication remains governed by its own terms. The generated `data/processed/source_manifest.json` is the build-specific inventory of source URLs, retrieval dates, availability, checksums, and limitations.

## OpenStreetMap

Map features, power infrastructure, and reviewed Metro Manila route relations include data © OpenStreetMap contributors, available under the Open Data Commons Open Database License 1.0. Route2Zero displays the required attribution in the interactive map and retains source relation URLs in route evidence records.

- Copyright and license: https://www.openstreetmap.org/copyright
- ODbL 1.0: https://opendatacommons.org/licenses/odbl/1-0/
- Metro Manila route-convention wiki text: CC BY-SA 2.0, https://wiki.openstreetmap.org/wiki/Metro_Manila/Jeepney_and_UV_Express_routes

Any public redistribution of an adapted OSM-derived database must continue to follow the ODbL notice, attribution, and share-alike requirements.

## Historic GTFS

The historic Sakay community GTFS snapshot contains data governed by the Department of Transportation and Communications Developer License Agreement and Terms of Use stored at `data/raw/gtfs_master/LICENSE.md`. It is not relicensed under MIT. Route2Zero uses it to promote public-transport planning and does not imply sponsorship, endorsement, or proof of current service.

## WorldPop

The Philippines 2020 population-count raster is from WorldPop, University of Southampton, DOI 10.5258/SOTON/WP00670, under Creative Commons Attribution 4.0 International. Route2Zero uses it only as a population-exposure proxy.

## Philippine public-sector and published references

- Philippine Department of Energy generation context and 2024 Energy Investment Kit are credited to the Department of Energy. The retrieved publications state no separate reuse license; factual planning values are summarized with attribution.
- The LTFRB LPTRP index is credited to the Land Transportation Franchising and Regulatory Board. No route-level Metro Manila match is accepted in the current source set.
- Philippine Statistics Authority small-area poverty estimates are registered as a candidate source under CC BY 4.0 unless otherwise stated. They are not integrated in the current score.
- The Philippine News Agency e-jeepney trial report is all rights reserved. Route2Zero records only the attributed factual range value needed for a clearly labelled proxy and does not reproduce the article.

## Mapbox

The interface uses Mapbox GL JS and a Mapbox-hosted style under Mapbox's applicable service terms. The public `pk.` access token is a browser credential and should be origin-restricted in the Mapbox account. Mapbox attribution remains visible in the map.

## No endorsement

Source attribution does not imply that any data provider, agency, operator, city, or publisher endorses Route2Zero or its results.
