# Route2Zero

**A transparent, equity-aware priority index for e-jeepney rollout in Metro Manila.**

Route2Zero helps transport regulators, local governments, operators, and financiers decide which jeepney corridors should enter electrification validation first. It combines four visible dimensions—emissions-reduction potential, equity, grid feasibility, and operator readiness—into an interactive, adjustable Just Transition Score.

The MVP is built for the **AI x City Climate Action Hackathon 2026**. Its pilot lens is Metro Manila, with Marikina, Makati, and Malabon included as spotlight cities.

> Route2Zero is not a rider-facing trip planner. It is a supply-side decision-support and evidence-gap tool. Every proxy, placeholder, stale source, and missing value is deliberately surfaced.

## What is included

- A responsive, Netlify-ready 2026 web dashboard plus the legacy Streamlit analysis view
- Interactive Mapbox map with clustered priorities and on-demand street-following routes
- Live score-weight controls and city filters
- A route detail view with four-factor score breakdown
- A ranked action queue plus PDF, Word, and CSV decision-pack exports
- An impact-versus-equity comparison chart
- A visible data-confidence banner
- Optional AI explanations that never affect ranking
- Reproducible GTFS audit, geometry, frequency, and scoring scripts
- Eight generated one-page policy briefs
- Pilot Plan and demonstration submission artifacts under `output/`
- Full methodology, provenance, technical guide, and presentation script

## Live demo

### Netlify-ready dashboard (recommended)

```powershell
cd netlify-site
npm run build
cd ..
python -m http.server 8899 --directory netlify-site\public
```

Then open `http://127.0.0.1:8899/`. The approved public Mapbox token is included as a build fallback, so `MAPBOX_TOKEN` is optional.

### Legacy Streamlit analysis view

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\run_pipeline.py
.\.venv\Scripts\streamlit.exe run app\dashboard.py
```

Then open `http://localhost:8501`.

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/run_pipeline.py
streamlit run app/dashboard.py
```

The processed outputs are already included for a fast demo. Re-running the pipeline is optional unless source or override data changed.

## Netlify deployment

This project now includes a Netlify-ready static dashboard in `netlify-site/public/` plus a Netlify Function for optional AI answers. Netlify does not run the Streamlit server directly; the deployed site uses the same processed route data from `data/processed/`.

The web dashboard uses Mapbox GL JS with the project style `mapbox://styles/marwin2323/cmswv687u002u01so2xzd7mrs`. When a route is selected, its ordered GTFS coordinates are sent to the Mapbox Directions API in groups of at most 25 waypoints and the returned full GeoJSON geometry is drawn along drivable streets. The site deliberately shows no fallback straight line when Mapbox cannot return a reliable road path. Results are cached for the current browser session.

Use these Netlify settings:

```text
Base directory: netlify-site
Build command: npm run build
Publish directory: public
Functions directory: netlify/functions
```

Add these environment variables in Netlify under Site configuration > Environment variables. The four AI values need **Functions** scope (and may also include Builds):

```text
ABSK_KEY=your_api_key_here
BASE_URL=your_openai_compatible_base_url_here
MODEL=your_model_name_here
AI_EXPLANATIONS_ENABLED=true
```

`ABSK_KEY` is the variable that holds the API key. Do not add the key to browser JavaScript, `.env.example`, `netlify.toml`, or `netlify-site/public/`. The Netlify Function reads it with `process.env.ABSK_KEY`, so the key stays server-side. Redeploy after changing Netlify environment variables.

The Mapbox token begins with `pk.` and is intentionally a public browser token. The build includes the approved public token as an offline-safe default and still accepts an optional `MAPBOX_TOKEN` build variable as an override. It generates an ignored `public/config.js` file and limits Netlify's scan exception to that deliberate public output path. No Mapbox variable is required for the standard deploy. Restrict the token to the production Netlify domain in the Mapbox account after the final site URL is known. Mapbox Directions requests are made only for the selected route and may count toward the account's Mapbox usage.

## Optional AI explanation layer

Copy `.env.example` to `.env` and set the API values for your environment:

```text
ABSK_KEY=paste_key_here
BASE_URL=paste_openai_compatible_base_url_here
MODEL=paste_model_name_here
AI_EXPLANATIONS_ENABLED=true
```

`.env` is gitignored. Do not commit it. Deployment should provide these values through the host's environment-variable or secrets manager.

Generate offline-safe explanations for every ranked route:

```powershell
.\.venv\Scripts\python.exe src\11_ai_explain.py
```

Generate or refresh API-backed explanations for only the highest-ranked routes:

```powershell
.\.venv\Scripts\python.exe src\11_ai_explain.py --use-api --limit 10
```

If the API is missing, slow, or unreachable, Route2Zero uses deterministic sentences and the dashboard remains fully functional. The LLM is a narrative layer only; `ranking_ai_influence` is always false.

## Scoring model

The default Just Transition Score is:

```text
0.35 × emissions activity proxy
+ 0.35 × equity density proxy
+ 0.15 × grid regional proxy
+ 0.15 × operator readiness placeholder/override
```

### 1. Emissions-reduction potential — 35%

`route length × estimated weekday trips` is min-max scaled across routes. This represents relative service activity, not measured emissions. It does not claim route-level fuel use, engine age, ridership, or tonnes of CO₂ avoided.

### 2. Equity — 35%

Each route is buffered by 300 metres. The score uses the population-weighted share of the catchment intersecting high-density cells in the WorldPop 2020 Philippines 1 km raster. This is a density-only fallback, not an informal-settlement, poverty, or tenure boundary.

### 3. Grid feasibility — 15%

Every route receives the official 2024 Luzon renewable-generation share: `14,550 / 90,269 GWh = 16.118%`. No public route- or depot-level capacity source was available, so this value is intentionally constant and marked coarse.

### 4. Operator readiness — 15%

Every route starts at the neutral midpoint, 50/100. This is an explicit placeholder pending cooperative financing and governance data. Pilot teams can edit `data/processed/operator_overrides.csv` without changing the upstream pipeline.

Weights are named constants in `src/08_composite_score.py` and adjustable in the dashboard. The ranking is deterministic weighted arithmetic.

## Data snapshot

The canonical source is the Sakay community GTFS `master` branch:

- 1,717 total routes
- 1,711 LTFRB routes
- 1,522 jeepney route-direction records (`PUJ`)
- 189 bus route-direction records (`PUB`)
- 1,864 trips
- 4,858 stops
- 79,414 stop-time records
- 1,864 frequency rows
- 10 shape IDs covering six routes total
- 2 jeepney routes with usable shapes
- 1,520 jeepney routes using ordered-stop approximations

The feed validity window spans 2013–2020. It is a historic MVP network baseline and is not represented as live 2026 service.

Both requested branches are available:

- `data/raw/gtfs_master/` — canonical build source
- `data/raw/gtfs_dotc/` — comparison source
- `GTFS/master/` and `GTFS/dotc/` — convenience links

`master` has 1,717 routes and a calendar through 2020. `dotc` has 1,715 routes, includes `route_bikes_allowed`, and ends in 2014. The project therefore continues on `master`.

## Pipeline

Run one task at a time:

```powershell
.\.venv\Scripts\python.exe src\01_audit.py
.\.venv\Scripts\python.exe src\02_geometry.py
.\.venv\Scripts\python.exe src\03_frequency.py
.\.venv\Scripts\python.exe src\04_emissions_score.py
.\.venv\Scripts\python.exe src\05_equity_score.py
.\.venv\Scripts\python.exe src\06_grid_score.py
.\.venv\Scripts\python.exe src\07_operator_score.py
.\.venv\Scripts\python.exe src\08_composite_score.py
.\.venv\Scripts\python.exe src\09_city_aggregation.py
.\.venv\Scripts\python.exe src\11_ai_explain.py
.\.venv\Scripts\python.exe src\10_policy_brief.py
```

Or run the entire deterministic pipeline:

```powershell
.\.venv\Scripts\python.exe src\run_pipeline.py
```

Every stage is idempotent. Source data under `data/raw/` is never overwritten.

## Project structure

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
├── output/
│   ├── pdf/
│   ├── presentation/
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

## Submission artifacts

- `output/documents/Route2Zero_Pilot_Plan.docx` — editable, accessible 24-page formal Pilot Plan
- `output/pdf/Route2Zero_Pilot_Plan.pdf` — visually verified 24-page Pilot Plan
- `output/presentation/Route2Zero_Demonstration_Deck.pptx` — editable 24-slide 2026 demonstration deck with source notes
- `output/pdf/Route2Zero_Demonstration_Deck.pdf` — visually verified 24-page presentation PDF
- `script.txt` — narration aligned to all 24 slides plus a live-demo checklist
- `technical.txt` — Netlify, Mapbox, data, QA, deployment and handover reference

## Key processed outputs

- `audit_report.md` — row counts and referential-integrity pass/fail results
- `route_corridors.csv` — de-duplicated bidirectional corridor view
- `jeepney_routes.geojson` — one feature per jeepney route ID
- `route_frequency.csv` — headway, service window, and estimated trips
- `emissions_score.csv` — route activity proxy and normalized score
- `equity_score.csv` — WorldPop density exposure and confidence labels
- `grid_feasibility.csv` — official Luzon baseline and NGEF context
- `operator_readiness.csv` — placeholders or workshop overrides
- `route2zero_scores.csv` / `.geojson` — merged scores, ranks, confidence, geometry
- `city_summary.csv` — city route counts, averages, and top-five routes
- `route_explanations.json` — cached API or deterministic narratives

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The tests verify the 1,522-route universe, the two real jeepney shapes, score bounds, proxy/placeholder labels, the one intentionally incomplete rank, absence of AI influence, and absence of the key from committed source/example files.

## Demo path

1. Start on the map and point to the confidence banner.
2. Select a high-ranked route and show its four-factor breakdown.
3. Select a lower-ranked route for contrast.
4. Change one weight, then restore the defaults.
5. Filter to Marikina, Makati, or Malabon.
6. Show the impact-equity scatterplot.
7. Download the filtered rankings.
8. Close on one generated policy brief.

See `docs/demo_script.md` for a timed three-minute version and `script.txt` for the presentation talk track.

## Known limitations and roadmap

- **Historic GTFS:** refresh routes, stops, headways, and service periods with LTFRB and LGUs.
- **Sparse shapes:** replace straight stop chords with verified road-snapped paths.
- **Density-only equity:** add community-validated settlement, poverty, tenure, accessibility, and rider data.
- **Coarse grid proxy:** add Meralco feeder, substation, depot, tariff, and interconnection evidence.
- **Operator placeholder:** collect cooperative financing, fleet, governance, and consolidation readiness.
- **Activity, not emissions:** add actual fleet, fuel, ridership, and air-quality measurements.
- **Text-based cities:** validate route-city tags with administrative boundaries and local staff.
- **Weight governance:** publish workshop decisions and sensitivity analysis.

These are pilot workstreams, not hidden defects.

## Team

- John Marwin Ebona
- Prince Marl
- Joaquin Sarmiento
- Isaac Marcus
- Andrei Dela Cruz
- Russel Mendez
- Tj Moreno
- JM Palaganas

Pilot roles and responsibilities are detailed in the Pilot Plan submission.

## Sources and licensing

- Sakay GTFS: <https://github.com/sakayph/gtfs>
- WorldPop 2020 Philippines 1 km population grid, CC BY 4.0: <https://hub.worldpop.org/geodata/summary?id=33241>
- Philippine DOE 2024 Key Energy Statistics: <https://prod-cms.doe.gov.ph/documents/d/guest/-final-11-20-25_doe-key-energy-stat-pocket-size-2024-pdf>
- Philippine DOE grid-emission context: <https://doe.gov.ph/sites/default/files/pdf/pep/PEP_2023-2050_Volume_III.pdf>

See `docs/data_provenance.md` for commit hashes, branch comparison, file checksum, and source decisions.

## License note

Respect the licenses and attribution requirements of all upstream datasets. The repository's original GTFS license is retained in each cloned source directory. Route2Zero-generated code and submission artifacts should be assigned the team’s chosen license before public release.
