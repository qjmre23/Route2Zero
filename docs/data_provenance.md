# Route2Zero data provenance

## GTFS source

- Repository: `https://github.com/sakayph/gtfs`
- Retrieval date: 14 August 2026
- Local canonical source: `data/raw/gtfs_master/`
- Convenience links: `GTFS/master/` and `GTFS/dotc/`
- Master commit: `b7394ccd0c22e7fcc18cc6b53baa1200e99e8a87` (24 March 2015, "Add feed info")
- DOTC commit: `0e06b806258267ae0dd34f0772dfff1f4fccebff` (2 February 2014, "Update schedule validity (unofficial update)")

The repository is historic. The service calendar spans 2013-2020 on `master`; it is not a representation of live 2026 service. Route2Zero displays this limitation prominently and treats the feed as an MVP route-network baseline.

## Master versus dotc

| Check | master | dotc | Decision |
|---|---:|---:|---|
| Total routes | 1,717 | 1,715 | master has two more routes |
| LTFRB jeepney routes (`PUJ`) | 1,522 | 1,522 | equivalent jeepney universe |
| LTFRB bus routes (`PUB`) | 189 | 189 | equivalent bus universe |
| Calendar maximum end date | 2020-06-30 | 2014-09-19 | master is materially fresher |
| Additional route field | none | `route_bikes_allowed` | not useful to electrification ranking |

`master` is therefore the canonical build source. The `dotc` branch is retained unchanged for auditability but is not merged into processed outputs.

## Integrity and mutability rules

Everything under `data/raw/` is treated as immutable source data. All cleaning, joins, derived geometries, proxies, scores, and generated narratives are written under `data/processed/`, `docs/`, or `output/`. Each processed dataset carries source/confidence fields where a measurement, proxy, or placeholder distinction is required.

## Known GTFS geometry constraint

`shapes.txt` contains only 10 shape IDs and covers six routes, primarily rail. Route geometry therefore follows the documented two-tier method: use a real GTFS shape where available; otherwise connect the ordered stops from a representative trip and label the result `stop_sequence_approx`.

## Equity proxy

No retrievable NAMRIA or PSA informal-settlement polygon layer was identified at corridor resolution. The MVP therefore uses the build specification's weaker WorldPop fallback: **The spatial distribution of population in 2020 Philippines**, 1 km population-count GeoTIFF, DOI `10.5258/SOTON/WP00670`.

- Source page: `https://hub.worldpop.org/geodata/summary?id=33241`
- Download: `https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/2020/PHL/phl_ppp_2020_1km_Aggregated.tif`
- Local file: `data/raw/reference/phl_ppp_2020_1km_Aggregated.tif`
- SHA-256: `DB87B488519157EC83FB43E2C867016CA72115FDE193A9565B650EE35D6699FD`
- License: Creative Commons Attribution 4.0

This raster is population density, not an informal-settlement boundary. Route2Zero measures the population-weighted share of each 300 m route catchment that intersects high-density cells. Every affected field is labeled `worldpop_2020_1km_population_density_proxy`, and the dashboard describes its low spatial and conceptual confidence.

## Grid proxy

The regional grid inputs are manually transcribed from the Philippine Department of Energy's official 2024 Key Energy Statistics and 2019-2021 National Grid Emission Factor publications. Metro Manila is represented by one Luzon-grid baseline because no public route- or depot-level capacity dataset is available.

- 2024 Key Energy Statistics: `https://prod-cms.doe.gov.ph/documents/d/guest/-final-11-20-25_doe-key-energy-stat-pocket-size-2024-pdf`
- National Grid Emission Factor reference: `https://doe.gov.ph/sites/default/files/pdf/pep/PEP_2023-2050_Volume_III.pdf`
- Extracted lookup: `data/raw/reference/doe_2024_luzon_generation_mix.csv`

The score equals the 2024 Luzon renewable-generation share, 14,550 / 90,269 GWh. It is intentionally constant across routes and must not be interpreted as local charger availability.
