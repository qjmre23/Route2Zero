"""Train a grouped, leakage-aware model of historic route service activity."""

from __future__ import annotations

import platform
import sys

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline

from common import CONFIG_DIR, MODELS_DIR, PROCESSED_DIR, ensure_output_dirs, read_json, stable_hash, utc_now_iso, write_json


LEAKAGE_COLUMNS = {
    "trips_per_day_estimate", "avg_headway_min", "daily_service_window_hrs",
    "daily_vehicle_km_proxy", "emissions_potential_score", "climate_impact_score",
    "just_transition_score", "rank",
}


def validate_feature_contract(feature_columns: list[str], configured_forbidden: list[str]) -> None:
    forbidden = LEAKAGE_COLUMNS | set(configured_forbidden)
    leaked = sorted(set(feature_columns) & forbidden)
    if leaked:
        raise ValueError(f"ML feature leakage detected: {leaked}")


def candidate_models(seed: int) -> dict[str, object]:
    return {
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            learning_rate=0.06, max_iter=220, max_leaf_nodes=20, l2_regularization=0.2,
            random_state=seed,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=260, min_samples_leaf=3, max_features=0.8,
            random_state=seed, n_jobs=-1,
        ),
    }


def make_pipeline(model: object, features: list[str]) -> Pipeline:
    preprocessing = ColumnTransformer(
        [("numeric", SimpleImputer(strategy="median"), features)],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return Pipeline([("features", preprocessing), ("model", model)])


def evaluate_candidate(
    pipeline: Pipeline,
    x: pd.DataFrame,
    y: pd.Series,
    groups: pd.Series,
    folds: int,
) -> dict[str, float]:
    splitter = GroupKFold(n_splits=min(folds, groups.nunique()))
    predictions = np.full(len(y), np.nan, dtype=float)
    baseline = np.full(len(y), np.nan, dtype=float)
    for train, test in splitter.split(x, y, groups):
        fitted = clone(pipeline).fit(x.iloc[train], y.iloc[train])
        predictions[test] = fitted.predict(x.iloc[test])
        baseline[test] = float(np.median(y.iloc[train]))
    mae = mean_absolute_error(y, predictions)
    baseline_mae = mean_absolute_error(y, baseline)
    return {
        "mae": round(float(mae), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y, predictions))), 4),
        "r2": round(float(r2_score(y, predictions)), 4),
        "baseline_mae": round(float(baseline_mae), 4),
        "relative_mae_improvement": round(float((baseline_mae - mae) / baseline_mae), 4) if baseline_mae else 0.0,
    }


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "model_config.json")
    model_config = config["service_intensity"]
    features = list(model_config["feature_columns"])
    validate_feature_contract(features, model_config["forbidden_leakage_columns"])
    seed = int(config["random_seed"])

    frame = pd.read_csv(PROCESSED_DIR / "route_features.csv", dtype={"route_id": str})
    target = model_config["target"]
    training = frame.loc[frame[target].notna()].copy()
    if len(training) < 100 or training["normalized_corridor_id"].nunique() < 5:
        raise ValueError("Insufficient grouped training evidence for the service-activity model")
    x = training[features]
    y = training[target].astype(float)
    groups = training["normalized_corridor_id"].astype(str)

    evaluations: dict[str, dict[str, float]] = {}
    pipelines: dict[str, Pipeline] = {}
    available = candidate_models(seed)
    for name in model_config["model_candidates"]:
        pipeline = make_pipeline(available[name], features)
        evaluations[name] = evaluate_candidate(pipeline, x, y, groups, int(model_config["cv_folds"]))
        pipelines[name] = pipeline
    selected_name = min(evaluations, key=lambda name: evaluations[name]["mae"])
    selected_metrics = evaluations[selected_name]
    meaningful = selected_metrics["relative_mae_improvement"] >= float(model_config["minimum_relative_mae_improvement"])
    selected = pipelines[selected_name].fit(x, y)
    predictions = np.maximum(0.0, selected.predict(frame[features]))

    model_version = "service-v1-" + stable_hash({
        "target": target, "features": features, "model": selected_name, "seed": seed,
    }, 8)
    joblib.dump(selected, MODELS_DIR / "service_intensity.joblib")
    metadata = {
        "model_version": model_version,
        "model_name": selected_name,
        "target": target,
        "target_description": "Historic schedule-based vehicle-kilometres per day proxy; not passenger demand or ridership.",
        "features": features,
        "excluded_leakage_features": sorted(LEAKAGE_COLUMNS),
        "training_rows": len(training),
        "corridor_groups": int(groups.nunique()),
        "cross_validation": f"GroupKFold({min(int(model_config['cv_folds']), groups.nunique())}) by normalized_corridor_id",
        "candidate_metrics": evaluations,
        "selected_metrics": selected_metrics,
        "meaningful_vs_baseline": bool(meaningful),
        "influences_climate_when_historic_value_missing": bool(meaningful),
        "random_seed": seed,
        "trained_at_utc": utc_now_iso(),
        "python_version": platform.python_version(),
        "scikit_learn_version": sklearn.__version__,
        "limitations": [
            "The target is derived from a historic 2013-2020 schedule baseline.",
            "The model estimates service activity, not ridership, passenger demand or 2026 operations.",
            "Observed or validated current evidence must override the model during a pilot.",
        ],
    }
    write_json(MODELS_DIR / "service_intensity_metadata.json", metadata)
    write_json(PROCESSED_DIR / "model_metrics.json", {"service_intensity": metadata})

    output = frame[["route_id", "normalized_corridor_id", target]].copy()
    output["ml_service_intensity_prediction"] = np.round(predictions, 3)
    output["ml_service_intensity_residual"] = np.where(
        output[target].notna(), output[target] - output["ml_service_intensity_prediction"], np.nan
    )
    residual_limit = float(np.nanquantile(np.abs(output["ml_service_intensity_residual"]), 0.95))
    output["ml_service_intensity_anomaly_flag"] = output["ml_service_intensity_residual"].abs() >= residual_limit
    output["ml_prediction_source"] = "grouped_cv_historic_service_activity_model"
    output["ml_prediction_claim_status"] = "ML_ESTIMATED"
    output["ml_model_version"] = model_version
    output["ml_model_meaningful_vs_baseline"] = bool(meaningful)
    output["ml_service_intensity_used"] = output[target].isna() & bool(meaningful)
    output.to_csv(PROCESSED_DIR / "ml_service_intensity.csv", index=False)
    print(f"[PASS] service model {model_version}: {selected_name}, MAE={selected_metrics['mae']}, baseline={selected_metrics['baseline_mae']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
