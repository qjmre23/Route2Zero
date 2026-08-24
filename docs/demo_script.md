# Route2Zero 2.1 live demonstration script

## Duration and setup

Target duration: 80-88 seconds.

Use the production application at <https://route2zero.netlify.app/> or the generated local Netlify preview. Use desktop width for the primary walkthrough and keep the browser zoom at 100%.

Before recording:

- confirm build `r2z-0cd49ad56aaa` is displayed or documented;
- confirm scenario `scn-e0f12f397e`;
- confirm 1,522 routes, 20 dated current external records, 9 robust priorities, and 8 Phase-1 corridors;
- preselect `LTFRB_PUJ1353` as the flagship;
- allow the Mapbox style to finish loading;
- close unrelated tabs and notifications;
- test the export button; and
- keep the optional AI endpoint disabled unless its source label has been verified.

Do not show superseded proxy-era scores or controls, or a section labeled “Judge guide.”

## Shot sequence

### 0:00-0:10 — Decision and scale

**Screen:** Hero and release metrics.

**Action:** Let the metric count-up finish, then move the pointer from 1,522 routes to 20 current external records and 9 robust priorities.

**Narration:**

“Route2Zero helps a city decide which jeepney corridors to validate for electrification first. This build screens 1,522 historic route records, identifies nine robust priorities, and adds 20 dated external route records without pretending they prove active service.”

**Transition:** Click the primary map action. Use the native smooth scroll; do not cut before the map settles.

### 0:10-0:24 — Observed and interpreted route geometry

**Screen:** Interactive map.

**Action:** Select a reviewed OSM corridor such as `LTFRB_PUJ1034` first and show its relation/date evidence, then return to Francisco Homes - Cubao, route `LTFRB_PUJ1353`, to show the labelled Mapbox interpretation.

**Narration:**

“Reviewed OSM matches use their actual member-way geometry and show the relation date. Other corridors use a Mapbox street-following interpretation. Neither one alone proves active service or franchise authority.”

**Transition:** Click the selected route panel or next-step control to reveal the route lens.

### 0:24-0:39 — Separate priority from evidence

**Screen:** Route decision lens.

**Action:** Point first to priority 79.07 and rank 1, then to evidence grade C and confidence 38.34. Highlight the top-10 frequency of 100%.

**Narration:**

“The route is first under the default human-controlled policy lens, but its evidence is only grade C. The 100% top-ten frequency means the rank survives the tested weights; it does not make the historic evidence current.”

**Transition:** Open the climate range with one click.

### 0:39-0:51 — Climate uncertainty

**Screen:** Low/base/high climate and energy range.

**Action:** Point first to the base result, plus 368.0 tonnes per year, then show the bounded range from minus 1,111.8 to plus 3,025.3.

**Narration:**

“The base case is plus 368 tonnes per year. The low case turns negative when high electricity use meets a carbon-intensive grid; vehicle efficiency is the strongest sensitivity. These are scenarios to calibrate, not claimed reductions.”

**Transition:** Click “What to validate next.”

### 0:51-1:03 — Value of information

**Screen:** Validation-priority panel.

**Action:** Reveal the highest-value missing fields and rank-swing or portfolio-flip indicator.

**Narration:**

“Instead of hiding missing data, Route2Zero tests which field could change the decision most, then creates an evidence request for the city, operator, or utility.”

**Transition:** Click the Phase-1 portfolio tab or anchor.

### 1:03-1:17 — Constrained portfolio

**Screen:** Eight-corridor portfolio and simple-top-N comparison.

**Action:** Animate or highlight the four removed and four added routes, then show the eight-corridor count.

**Narration:**

“The Phase-1 portfolio is not the top eight copied into a list. Corridor and city constraints replace four records, producing eight validation cases with no fabricated budget.”

**Transition:** Open the planning summary.

### 1:17-1:26 — AI boundary and close

**Screen:** Structured planning summary and export action.

**Action:** Show the response source label, then click the export button once.

**Narration:**

“The assistant explains structured outputs and works with deterministic fallback. It never changes a score, climate value, or rank. Route2Zero turns uncertainty into a city-owned validation plan.”

End on the exported decision-record title or the Route2Zero mark with the live and GitHub links visible.

## Interaction choreography

- Use one deliberate click per transition.
- Keep the pointer visible but stationary during narration.
- Allow metric, route-line, and panel transitions to complete before moving.
- Use a short click ripple or button-state change rather than decorative cursor trails.
- Avoid rapid scrolling.
- Avoid opening browser developer tools in the submitted walkthrough.
- If a network call is slow, use a clean cut after the status appears; do not claim success before the line renders.
- If Mapbox fails, state that the screening geometry remains available and continue. Do not draw a straight line and call it road-following.
- If the AI endpoint fails, show the deterministic fallback source label and continue.

## Claims checklist

The narration may state:

- 1,522 route-direction records are screened;
- 20 dated current external route records are supplied, while active service remains uncertain;
- 9 records are robust priorities;
- 8 corridors are selected for Phase 1;
- the flagship score is 79.07 under the named default scenario;
- its evidence is grade C, 38.34;
- its top-10 frequency is 100% across 5,000 scenarios;
- its base climate case is +368.0 tCO2e/year, bounded by -1,111.8 to +3,025.3; and
- the LLM has no ranking influence.

The narration must not state:

- that all routes operate in 2026;
- that the map is an official route trace;
- that population density identifies informal settlements;
- that a nearby substation has capacity;
- that operator readiness is observed;
- that scenario CO2e has been achieved;
- that the portfolio is financially optimized; or
- that AI selected a public investment.

## Recovery paths

### Map request unavailable

Say: “The application has preserved the source screening geometry and lowered the route-path claim. Field verification remains required.”

### Optional AI unavailable

Say: “The explanation has returned through deterministic fallback. All analytical and export functions remain available.”

### Export blocked by browser

Use the print preview already prepared for the same build and scenario. Do not substitute an outdated artifact.

### Timing overrun

Cut the value-of-information explanation to: “It identifies the evidence most likely to change the decision.” Keep the climate caveat and AI boundary.
