# Route2Zero 2.1 model card

## Card scope

This card covers the two fitted machine-learning components in build `r2z-0cd49ad56aaa`:

1. the supervised historic service-intensity model; and
2. the unsupervised corridor-typology model.

It does not describe the deterministic climate engine, evidence-confidence rules, Monte Carlo rank-stability calculation, value-of-information perturbation, or Phase-1 portfolio selector as machine-learning models. It also distinguishes machine learning from the optional LLM planning assistant.

## System boundary

Machine learning has two limited roles:

- estimate a historic schedule-derived service-activity proxy when that proxy is missing; and
- describe structural corridor similarity.

Machine learning does not set policy weights, infer settlement status, select the Phase-1 portfolio, authorize investment, or decide which operator or community receives support.

The LLM, when enabled, has a third and separate role: summarize already-generated fields. It cannot write numeric analytical inputs or change rank.

## Model A: historic service intensity

### Identification

| Field | Value |
|---|---|
| Model version | `service-v1-266e0b1d` |
| Selected algorithm | Histogram gradient-boosting regressor |
| Alternative evaluated | Random forest regressor |
| Random seed | 20260820 |
| Python | 3.12.13 |
| scikit-learn | 1.9.0 |
| Training timestamp | `2026-08-24T15:23:20Z` |
| Serialized model | `models/service_intensity.joblib` |

### Intended use

The model estimates `historic_daily_vehicle_km_proxy` when the schedule-derived historic value is missing. The target is:

```text
route_length_km x historic_typical_weekday_trips_per_day
```

The prediction can feed the climate scenario engine only when:

1. the historic target is missing; and
2. grouped cross-validation beats the configured median baseline by at least 2% MAE.

### Non-intended uses

The prediction must not be described or used as:

- passenger demand;
- ridership;
- fare revenue;
- present-day vehicle-kilometres;
- observed headway;
- current route activity;
- route profitability;
- fleet requirement;
- driver income;
- social need; or
- a reason to approve procurement.

### Training data

The model is trained on 1,521 route records from the historic 2013-2020 Sakay GTFS baseline. The target is derived, not observed.

The grouping key is `normalized_corridor_id`. The current metadata records 714 groups. Opposite directions or name variants assigned to one normalized corridor remain within the same fold.

### Features

The model uses nine numeric features:

1. stop count;
2. stops per kilometre;
3. mean stop spacing in metres;
4. endpoint distance in kilometres;
5. geometry detour ratio;
6. corridor population proxy;
7. population-exposure overlap percentage;
8. hub-connectivity count; and
9. GTFS-shape indicator.

Missing feature values are median-imputed within the fitted pipeline.

### Leakage controls

The following are prohibited as features:

- average headway;
- daily service window;
- trips-per-day estimate;
- daily vehicle-kilometre proxy;
- emissions-potential score;
- climate-impact score;
- final priority score; and
- rank.

The code validates the feature list against the prohibited set before training.

### Validation design

Five-fold `GroupKFold` uses normalized corridor ID as the group. Each fold trains preprocessing and the candidate model only on its training partition. Predictions are collected for held-out groups.

The baseline for each fold is the median target value from the training partition. Candidate selection uses lower out-of-fold MAE.

### Recorded performance

| Candidate | MAE | RMSE | R-squared | Baseline MAE | Relative MAE improvement |
|---|---:|---:|---:|---:|---:|
| Histogram gradient boosting | 267.6992 | 574.1447 | 0.9907 | 4,850.3377 | 0.9448 |
| Random forest | 284.7374 | 653.4361 | 0.9880 | 4,850.3377 | 0.9413 |

The histogram gradient-boosting model is selected by MAE.

### Interpretation of performance

The strong results show that the available structural features reconstruct the historic derived target well under grouped validation. They do not establish accuracy for 2026 operations, passenger demand, or another city.

The target shares historic-source and feature-construction context with the predictors. R-squared should therefore not be marketed as general real-world predictive accuracy. The proper pilot test is performance against date-stamped present observations and a simple operational baseline.

### Use in the current build

The historic proxy exists for 1,521 routes. The model prediction is used for one route:

- Route ID: `LTFRB_PUJ2451`
- Route name: Alabang-Bbayan via Bicutan
- Prediction: 6,656.52 historic-proxy vehicle-kilometres per day
- Claim status: `ML_ESTIMATED`
- Default rank: 1,334

For the other 1,521 routes, the prediction is retained for comparison and residual analysis but does not replace the historic derived value.

### Anomaly flag

Where the historic target exists, the residual is historic target minus full-model prediction. An absolute residual at or above the 95th percentile is flagged. The current output contains 77 anomaly flags.

The anomaly flag means the route is unusual relative to this model and feature set. It does not mean the source is wrong or the route is fraudulent.

### Known risks

- Historic schedule data may not reflect actual historical operations.
- Route-name normalization can group or separate corridors imperfectly.
- Approximate geometry influences several features.
- WorldPop exposure contributes a coarse historic proxy.
- Hub connectivity is based on stop-name pattern matching.
- The one ML-filled route has no current observation for confirmation.
- Distribution shift is expected when current service patterns or a new city are introduced.

### Required pilot validation

The pilot must collect current headway and service-window observations, define an observed target, compare MAE and RMSE against at least a transparent baseline, assess error by city and corridor type, review outliers, and document whether the model should be retrained, limited, or disabled.

If current performance is weak, observed or high-quality administrative evidence takes precedence and the model remains experimental.

## Model B: corridor typology

### Identification

| Field | Value |
|---|---|
| Model version | `typology-v1-ab8203c9` |
| Method | Median imputation, standardization, K-means |
| Projection | Two-component PCA for visualization |
| Random seed | 20260820 |
| Selected clusters | 3 |
| Silhouette score | 0.3730 |
| Training timestamp | `2026-08-24T15:23:23Z` |
| Serialized model | `models/corridor_typology.joblib` |

### Intended use

The typology provides a descriptive lens for comparing structurally similar routes, selecting diverse validation cases, and reviewing model error or evidence gaps by corridor form.

### Features

- route length;
- stop count;
- stops per kilometre;
- endpoint distance;
- geometry detour ratio;
- corridor population proxy; and
- population-exposure overlap percentage.

### Cluster-count selection

Candidate values from 3 through 8 are evaluated. A candidate is considered viable when its minimum cluster size is at least 10 and at least 1% of the 1,522-route universe. The viable candidate with the highest silhouette score is selected.

| k | Silhouette | Minimum cluster size | Viable under rule |
|---:|---:|---:|---|
| 3 | 0.3730 | 22 | Yes |
| 4 | 0.2864 | 22 | Yes |
| 5 | 0.2927 | 22 | Yes |
| 6 | 0.2822 | 22 | Yes |
| 7 | 0.2515 | 22 | Yes |
| 8 | 0.2567 | 22 | Yes |

Every candidate meets the minimum-cluster-size rule in this build. The selected k is three because it has the highest silhouette score.

### Current cluster distribution

| Label | Cluster ID | Routes |
|---|---:|---:|
| Dense Urban Trunk | 0 | 631 |
| High-Stop-Density Core | 1 | 869 |
| Long Regional Connector | 2 | 22 |

Human-readable labels are assigned from relative cluster-centre patterns. They are descriptive conveniences, not ground truth.

### Outlier flag

Distance to the assigned cluster center is calculated in standardized feature space. A route at or above the within-cluster 95th percentile is flagged. The current output contains 78 typology outliers.

### Non-intended uses

Typology must not be used to infer:

- poverty or wealth;
- vulnerability;
- informal-settlement status;
- current passenger demand;
- operator quality;
- climate benefit;
- investment readiness;
- franchise compliance; or
- a funding category.

The typology is not included in the priority score.

### Known risks

- Cluster labels depend on relative patterns in this historic route universe.
- Approximate geometry affects length, detour, and density features.
- K-means favors roughly spherical clusters in standardized space.
- The PCA projection does not preserve all distances.
- A silhouette score of 0.27 indicates only moderate separation.
- Human labels can encourage over-interpretation if limitations are omitted.

### Required pilot validation

Transport planners should review representative and outlier routes from each cluster, determine whether the labels are operationally meaningful, and test whether validation needs or model error differ by type. The typology may be renamed or removed without affecting the policy score.

## Machine learning versus deterministic analytics

| Component | Method | Can affect priority? |
|---|---|---|
| Service-intensity estimate | Supervised ML | Indirectly, for one missing historic input in this build |
| Corridor typology | Unsupervised ML | No |
| Climate and energy | Deterministic scenarios | Yes, through climate score |
| Equity | Deterministic proxy transformation | Yes |
| Charging readiness | Deterministic proxy rules | Yes |
| Operator readiness | Deterministic evidence/prior rules | Yes |
| Evidence confidence | Deterministic rules | No direct score points in the policy score |
| Rank stability | Fixed-seed Monte Carlo weights | No change to default score; informs interpretation and portfolio objective |
| Portfolio selection | Deterministic constrained scan | Selects Phase-1 membership |
| Value of information | Deterministic perturbation | No change to score; sets validation priority |

## LLM planning assistant

The planning assistant is not one of the fitted models above. The pipeline produces deterministic route-scoped explanations and a portfolio summary. A Netlify Function may optionally send a bounded question and structured facts to an OpenAI-compatible endpoint.

LLM responses are not trusted sources. They must be labeled by source, remain traceable to cited route fields, and fall back to deterministic text when the API is disabled or unavailable.

The following invariant applies:

```text
llm_ranking_influence = false
```

## Monitoring and change control

A model release must record:

- target definition;
- source reference period;
- training rows and groups;
- feature list;
- leakage exclusions;
- validation design;
- candidate and selected metrics;
- seed and library versions;
- serialized artifact checksum;
- current-evidence evaluation when available;
- subgroup and outlier findings;
- use rule and override precedence; and
- approval to deploy or disable.

Any change to target, features, grouping, preprocessing, algorithm, seed, or usefulness gate requires a new model version and a regenerated build manifest.

## Current disposition

The service model is suitable for prototype fallback and pilot validation against its historic target. It is not yet validated for current operations. The typology is suitable for exploratory comparison and case sampling. Neither model is suitable for autonomous public-investment decisions.
