# Deployment runbook

This runbook covers the current Route2Zero Netlify deployment. It names only settings and functions that exist in this version.

## Netlify settings

Set these environment variables in the site settings with the scopes shown below:

| Variable | Scope | Purpose |
|---|---|---|
| `MAPBOX_TOKEN` | Builds | Injects the browser-safe public Mapbox token during the static build |
| `MAPBOX_STYLE_URL` | Builds | Selects the Mapbox style used by the dashboard |
| `ABSK_KEY` | Functions | Enables the structured Planning & Evidence Assistant |
| `BASE_URL` | Functions | Optional canonical origin used by the explanation function |
| `MODEL` | Functions | Optional model identifier for the assistant provider |
| `AI_EXPLANATIONS_ENABLED` | Functions | Set to `true` to allow live explanations |
| `ELEVENLABS_API_KEY` | Functions | Enables live narration for the dynamic assistant step |
| `ELEVENLABS_VOICE_ID` | Functions | Selects the ElevenLabs voice for that step |
| `ELEVENLABS_MODEL_ID` | Functions | Optional ElevenLabs model override |

`MAPBOX_TOKEN` and `MAPBOX_STYLE_URL` are build-time values because the static browser configuration is generated during `npm run build`. Never commit a secret key. The committed deterministic tour MP3 files do not require ElevenLabs at deploy time; only the dynamic assistant narration does.

## Pre-deploy checks

From the repository root:

```text
python scripts/validate_field_observation.py --input netlify-site/public/templates/field_observation_intake.csv
python -m pytest tests -q
Set-Location netlify-site
npm run check
npm run build
```

The build copies the canonical processed outputs into `netlify-site/public/data`, writes the browser configuration, and publishes the `public` directory. A successful deploy should serve `/`, `/data/build_manifest.json`, `/templates/field_observation_intake.csv`, and `/templates/field_observation.schema.json`.

## Functions and boundaries

`/.netlify/functions/explain` accepts the bounded route, scenario, portfolio, and evidence context assembled by the dashboard. It may summarize those facts, but it cannot write ledgers or change rankings. `/.netlify/functions/narrate` is used only for the dynamic assistant response. Field observations are reviewed and ingested through the controlled repository workflow; the public site has no anonymous write endpoint.

After a deploy, confirm that the headline metrics populate in a JavaScript-enabled browser, the map loads with a valid Mapbox token, TOUR ME opens and the final export control is reachable on a 320px-wide viewport, and the assistant response is readable in the configured theme.
