"""Merge Route2Zero 2.0 analytical layers into a versioned human policy model."""

from __future__ import annotations

import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, read_json, stable_hash


def main() -> int:
    ensure_output_dirs()
    policy = read_json(CONFIG_DIR / "policy_model.json")
    weights = policy["default_weights"]
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson")
    features = pd.read_csv(PROCESSED_DIR / "route_features.csv", dtype={"route_id": str})
    legacy_emissions = pd.read_csv(PROCESSED_DIR / "emissions_score.csv", dtype={"route_id": str})
    legacy_equity = pd.read_csv(PROCESSED_DIR / "equity_score.csv", dtype={"route_id": str})
    legacy_grid = pd.read_csv(PROCESSED_DIR / "grid_feasibility.csv", dtype={"route_id": str})
    legacy_operator = pd.read_csv(PROCESSED_DIR / "operator_readiness.csv", dtype={"route_id": str})
    frames = [
        pd.read_csv(PROCESSED_DIR / "ml_service_intensity.csv", dtype={"route_id": str}),
        pd.read_csv(PROCESSED_DIR / "corridor_typology.csv", dtype={"route_id": str}),
        pd.read_csv(PROCESSED_DIR / "climate_impact.csv", dtype={"route_id": str}),
        pd.read_csv(PROCESSED_DIR / "equity_v2.csv", dtype={"route_id": str}),
        pd.read_csv(PROCESSED_DIR / "charging_readiness.csv", dtype={"route_id": str}),
        pd.read_csv(PROCESSED_DIR / "operator_readiness_v2.csv", dtype={"route_id": str}),
        pd.read_csv(PROCESSED_DIR / "geometry_reliability.csv", dtype={"route_id": str}),
        pd.read_csv(PROCESSED_DIR / "evidence_confidence.csv", dtype={"route_id": str}),
        pd.read_csv(PROCESSED_DIR / "route_validation.csv", dtype={"route_id": str}),
    ]
    output = routes.merge(features.drop(columns=["route_long_name", "route_short_name", "route_desc", "geometry_source", "stop_count", "length_km"], errors="ignore"), on="route_id", how="left")
    for frame in frames:
        columns = ["route_id"] + [column for column in frame.columns if column != "route_id" and column not in output.columns]
        output = output.merge(frame[columns], on="route_id", how="left")

    output = output.merge(legacy_emissions[["route_id", "emissions_potential_score"]].rename(columns={"emissions_potential_score": "legacy_emissions_activity_score"}), on="route_id", how="left")
    output = output.merge(legacy_equity[["route_id", "equity_score"]].rename(columns={"equity_score": "legacy_equity_density_score"}), on="route_id", how="left")
    output = output.merge(legacy_grid[["route_id", "grid_feasibility_score", "grid_renewable_share_pct"]].rename(columns={"grid_feasibility_score": "legacy_grid_regional_proxy_score"}), on="route_id", how="left")
    output = output.merge(legacy_operator[["route_id", "operator_readiness_score"]].rename(columns={"operator_readiness_score": "legacy_operator_prior_score"}), on="route_id", how="left")
    legacy_weights = policy["legacy_weights"]
    output["legacy_just_transition_score"] = (
        output["legacy_emissions_activity_score"] * float(legacy_weights["emissions"])
        + output["legacy_equity_density_score"] * float(legacy_weights["equity"])
        + output["legacy_grid_regional_proxy_score"] * float(legacy_weights["grid"])
        + output["legacy_operator_prior_score"] * float(legacy_weights["operator"])
    ).round(2)

    required = list(weights)
    output["score_complete"] = output[required].notna().all(axis=1)
    output["just_transition_score"] = np.nan
    complete = output["score_complete"]
    output.loc[complete, "just_transition_score"] = sum(
        output.loc[complete, column] * float(weight) for column, weight in weights.items()
    )
    output["just_transition_score"] = output["just_transition_score"].round(2)
    output["rank"] = output["just_transition_score"].rank(method="first", ascending=False).astype("Int64")
    scenario_payload = {
        "title": policy["default_title"],
        "weights": weights,
        "climate_assumption_set": output["climate_assumption_set"].dropna().iloc[0],
        "validation_filter": "all_statuses",
        "policy_model_version": policy["version"],
    }
    scenario_id = "scn-" + stable_hash(scenario_payload, 10)
    output["scenario_id"] = scenario_id
    output["scenario_title"] = policy["default_title"]
    output["policy_model_version"] = policy["version"]
    output["default_weights"] = json.dumps(weights, sort_keys=True, separators=(",", ":"))
    output["ranking_method"] = "versioned_human_controlled_weighted_sum"
    output["llm_ranking_influence"] = False
    output["ml_features_used"] = output["ml_service_intensity_used"].fillna(False).astype(bool)
    output["ml_typology_used_for_score"] = False
    output["climate_model_type"] = "deterministic_low_base_high_scenario"
    output["sensitivity_method"] = "monte_carlo_policy_weights"
    output["optimization_method"] = "deterministic_selection"
    output["human_policy_control"] = True
    output["policy_weights_human_controlled"] = True
    output["build_id"] = "pending-final-manifest"
    output["decision_support_disclaimer"] = "Decision support only; not authorization for procurement, lending, franchise cancellation or investment."
    output = output.sort_values(["rank", "route_id"], na_position="last").reset_index(drop=True)
    output.drop(columns="geometry").to_csv(PROCESSED_DIR / "route2zero_scores.csv", index=False)
    output.to_file(PROCESSED_DIR / "route2zero_scores.geojson", driver="GeoJSON")
    print(f"[PASS] policy model {policy['version']}: {int(output['score_complete'].sum()):,}/{len(output):,}; scenario={scenario_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
