# Route2Zero city adapter guide

## Purpose

This guide defines how to adapt Route2Zero to another city or to a locally validated Metro Manila deployment without assuming that the current model, weights, data, or thresholds transfer unchanged.

Route2Zero is an architecture and governance pattern. It is not a universal pretrained city model.

## Transferability principle

The transferable elements are:

- source registry and checksums;
- claim-status vocabulary;
- route and evidence ledgers;
- leakage-aware model workflow;
- deterministic climate and evidence calculations;
- scenario IDs and change records;
- rank-stability analysis;
- constrained portfolio pattern;
- structured explanation boundary; and
- reproducible build manifest.

The non-transferable elements include:

- current GTFS route universe;
- corridor-name normalization;
- city alias dictionary;
- WorldPop-only equity interpretation;
- Luzon grid context;
- Metro Manila OSM snapshot;
- vehicle and energy assumptions;
- model coefficients;
- typology labels;
- evidence thresholds;
- policy weights; and
- portfolio constraints.

## Adapter readiness checklist

Before implementation, identify:

1. the city decision owner;
2. the transport decision question;
3. the corridor unit of analysis;
4. the source licensing and data-sharing basis;
5. current-service evidence;
6. route geometry evidence;
7. local equity and accessibility evidence;
8. grid and charging evidence;
9. operator or fleet evidence;
10. vehicle and climate assumptions;
11. implementation constraints;
12. privacy and consent requirements;
13. validation partners; and
14. handover owner.

Do not begin by copying the Metro Manila ranking.

## 1. Source registry adapter

Create or revise `config/source_registry.json` so every required source has:

- stable source ID;
- title and organization;
- authoritative URL;
- local path;
- retrieval date;
- reference period;
- geography;
- spatial resolution;
- license;
- source type;
- currentness; and
- limitations.

Run the source-manifest stage before any transformation. Do not register a remote URL without preserving the actual local snapshot used in the build where licensing permits.

## 2. Transport-data adapter

GTFS is preferred when available, but the city may use another route registry if it can provide stable identifiers and sufficient lineage.

Minimum route fields are:

- route ID;
- route name;
- mode;
- direction or corridor relationship;
- geometry or ordered stops;
- service-status evidence;
- service schedule or observation;
- source date; and
- source reference.

If the source contains both directions, decide whether ranking, validation, and portfolio limits operate on route direction or normalized corridor. Preserve the raw ID in all cases.

Validate referential integrity, duplicates, coordinate range, and route count before feature generation.

## 3. Current-status adapter

Populate `data/validated/route_validation.csv` through an approved process. Do not set all imported routes active by default.

The adapter should map local statuses to:

- active;
- inactive;
- suspended;
- uncertain; or
- another documented extension.

Validation status should distinguish desk check, operator confirmation, city confirmation, field check, and conflict.

## 4. Geometry adapter

Choose a hierarchy appropriate to the city:

1. verified official or field trace;
2. current high-quality GTFS shape;
3. current ordered stops with road routing;
4. historic shape;
5. historic ordered-stop approximation; and
6. missing.

Preserve both source and display geometry where they differ. A road-routed display line is not automatically official geometry.

Recalibrate the geometry-reliability rules when source conventions, stop spacing, road form, or route lengths differ materially from Metro Manila.

## 5. Service-intensity adapter

Define the local target before training. Options may include verified scheduled vehicle-kilometres, observed departures, or another accepted service measure.

The target must have:

- units;
- reference period;
- collection method;
- missingness policy;
- grouping unit;
- baseline; and
- intended use.

Do not reuse `service-v1-266e0b1d` without evaluating distribution shift and current holdout performance. Retrain when the city feature distribution, source definitions, route form, or target differs.

Retain leakage controls. Group validation by a key that prevents opposite directions or near-duplicate corridors from leaking across folds.

## 6. Typology adapter

Re-evaluate the feature set, scaling, viable cluster sizes, cluster count, silhouette, outliers, and human labels. Local planners should review representative routes.

Typology remains interpretive. Do not use a cluster label as a socioeconomic or investment category.

## 7. Climate adapter

Replace or calibrate:

- operating days;
- current vehicle efficiency;
- fuel emissions factor;
- electric vehicle energy use;
- charger efficiency;
- grid emissions factor;
- electrification share; and
- service intensity.

Use local units and preserve low, base, and high assumptions. Record source IDs for each parameter.

If the conservative case is negative, retain it. If all cases are positive, do not imply certainty. The result remains a scenario until monitored deployment data exist.

## 8. Equity and accessibility adapter

WorldPop may remain a population-exposure baseline, but it should not be the only equity input when stronger local evidence exists.

Potential dimensions include:

- access to jobs, schools, markets, and health care;
- travel time and transfers;
- affordability;
- service alternatives;
- disability access;
- community-identified service gaps;
- lawful aggregate socioeconomic indicators; and
- validated underserved-area datasets.

For every indicator, document construct, population, resolution, date, uncertainty, and governance. Leave unsupported dimensions null.

## 9. Charging and utility adapter

Replace the Metro Manila OSM snapshot with a local, dated infrastructure source. Separate:

- mapped infrastructure;
- site control;
- existing electrical service;
- available capacity;
- interconnection status;
- charger availability; and
- final engineering feasibility.

Only formal evidence should set capacity or site-verification flags. Proximity thresholds may require local recalibration for network density and geography.

## 10. Operator adapter

Define lawful, consent-based evidence with operator partners. Adapt fields to local institutions without converting missing data into a penalty.

Review:

- neutral prior;
- minimum observed fields;
- component definitions;
- component weights;
- completeness calculation;
- consent;
- confidentiality; and
- challenge process.

An adapter may disable operator scoring and leave it missing if a neutral prior would be misleading. That decision must be explicit.

## 11. Evidence-confidence adapter

Review component weights and status scores with the city. The current Metro Manila grade thresholds are A 80, B 65, C 35, and D 0; they are not universal standards.

Test the score on example evidence cards. A grade should respond to stronger current evidence without hiding persistent conceptual limitations.

Keep evidence confidence separate from model error and rank stability.

## 12. Policy adapter

The city should define named scenarios through a workshop. Record:

- decision question;
- dimensions;
- excluded dimensions;
- weights;
- rationale;
- owner;
- approval date;
- climate assumption set;
- validation filter; and
- permitted use.

The Metro Manila 40/30/15/15 default is a prototype lens, not a recommended universal policy.

## 13. Sensitivity adapter

Review the number of simulations, Dirichlet concentration, seed, and robust-priority thresholds. The current values are 5,000 simulations, concentration 60, and 0.70 top-10 probability.

If the city evaluates a small route universe, replace top-10 thresholds with a size-appropriate criterion. Document the new interpretation.

## 14. Portfolio adapter

Define a local validation portfolio before adding an investment budget. Review:

- maximum corridors;
- evidence floor;
- equity floor;
- geographic coverage;
- corridor-direction duplication;
- inactive-route policy;
- evidence-limited quota; and
- feasibility behavior.

Add financial constraints only with defensible, comparable cost inputs. If a solver is introduced, document objective, variables, constraints, optimality status, and infeasibility behavior.

## 15. Value-of-information adapter

Replace generic perturbation ranges with locally defensible ranges. Record why each range is plausible.

Possible fields include current service, operator evidence, charging capacity, vehicle efficiency, grid factor, accessibility, and cost. Do not convert rank swing into monetary value without an appropriate decision model.

## 16. Planning-assistant adapter

Translate or localize prompts only after the structured fields and prohibited claims are defined. Keep the API server-side, use bounded facts, label the source, and preserve deterministic fallback.

Evaluate the assistant with local planners. Disable it if it produces unsupported claims or distracts from evidence review.

## 17. Interface and map adapter

Configure:

- map style and token restrictions;
- default bounds;
- local place names;
- route search;
- units and number formats;
- accessible colors and keyboard interactions;
- mobile layout;
- export language; and
- local disclaimers.

Do not expose secret API keys. A Mapbox `pk.` token is public but should be origin-restricted.

## 18. Netlify adapter

The current site uses:

```text
Base directory: netlify-site
Build command: npm run build
Publish directory: public
Functions directory: netlify/functions
```

The build generates a browser-safe Mapbox configuration and copies processed data to the publish directory. The optional explanation function reads `ABSK_KEY`, `BASE_URL`, `MODEL`, and `AI_EXPLANATIONS_ENABLED` from server-side environment variables.

For another host, preserve the same separation between public configuration and server-side secrets.

## 19. Acceptance tests

An adapter is ready for pilot use only when:

- source registry and manifest pass;
- route universe is explainable;
- currentness labels are correct;
- geometry sources and reliability are visible;
- current-validation ledger is operational;
- model target and validation are local;
- climate units and assumptions are reviewed;
- equity indicators are lawful and interpretable;
- utility claims are correctly limited;
- operator evidence follows consent rules;
- scenario weights and constraints are approved;
- rank sensitivity is reproducible;
- portfolio infeasibility is transparent;
- LLM fallback works;
- exports retain scenario and source context;
- tests pass; and
- the production build works at desktop and mobile widths.

## 20. Handover package

Provide the city with:

- final source registry and snapshots;
- validated ledgers;
- configuration files;
- model card and fitted artifacts where permitted;
- build manifest;
- scenario library;
- portfolio record;
- decision pack;
- issue and conflict log;
- data dictionary;
- refresh and retraining runbook;
- deployment settings; and
- named owners for unresolved evidence.

## Transfer claim

The defensible statement is:

> Route2Zero can be adapted to another city through source adapters, local calibration, field validation, policy workshops, and governance review.

The indefensible statement is:

> The Metro Manila model can rank another city unchanged.
