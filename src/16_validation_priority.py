"""Quantify which uncertain fields can materially change route decisions."""

from __future__ import annotations

import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, minmax_score, read_json, write_json


def rank_for_score(value: float, baseline_scores: np.ndarray) -> int:
    return int(np.sum(baseline_scores > value) + 1)


def main() -> int:
    ensure_output_dirs()
    policy = read_json(CONFIG_DIR / "policy_model.json")
    weights = policy["default_weights"]
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    baseline = scores["just_transition_score"].to_numpy(dtype=float)
    climate_low_score = minmax_score(scores["net_co2e_avoided_t_year_low"]).fillna(0.0)
    climate_high_score = minmax_score(scores["net_co2e_avoided_t_year_high"]).fillna(0.0)
    rows: list[dict[str, object]] = []
    for index, row in scores.iterrows():
        variants = [
            ("operator_readiness", 30.0, 70.0, "neutral prior range requiring operator evidence", "route2zero_operator_prior_v1"),
            ("charging_readiness", max(0.0, row["charging_readiness_score"] - 20.0), min(100.0, row["charging_readiness_score"] + 20.0), "mapped proximity cannot verify capacity or site control", "osm_power_snapshot_2026_08_20"),
            ("climate_assumptions", float(climate_low_score.iloc[index]), float(climate_high_score.iloc[index]), "vehicle efficiency, electrification share and grid assumptions", "route2zero_climate_scenario_v1"),
            ("equity_population_exposure", max(0.0, row["equity_score"] - 15.0), min(100.0, row["equity_score"] + 15.0), "WorldPop exposure does not establish socioeconomic need", "worldpop_phl_2020_1km"),
        ]
        current_components = {
            "operator_readiness": float(row["operator_effective_score"]),
            "charging_readiness": float(row["charging_readiness_score"]),
            "climate_assumptions": float(row["climate_impact_score"]),
            "equity_population_exposure": float(row["equity_score"]),
        }
        weight_map = {
            "operator_readiness": float(weights["operator_effective_score"]),
            "charging_readiness": float(weights["charging_readiness_score"]),
            "climate_assumptions": float(weights["climate_impact_score"]),
            "equity_population_exposure": float(weights["equity_score"]),
        }
        for field, low, high, reason, source_id in variants:
            current = current_components[field]
            weight = weight_map[field]
            low_score = float(row["just_transition_score"]) + (low - current) * weight
            high_score = float(row["just_transition_score"]) + (high - current) * weight
            rank_low = rank_for_score(min(low_score, high_score), baseline)
            rank_high = rank_for_score(max(low_score, high_score), baseline)
            swing = abs(rank_low - rank_high)
            crosses_top_k = min(rank_low, rank_high) <= 8 < max(rank_low, rank_high)
            selected = bool(row["phase1_selected"])
            flip = bool(crosses_top_k or (selected and max(rank_low, rank_high) > 20))
            missing_bonus = 20 if field in {"operator_readiness", "charging_readiness"} else 8
            priority = min(100.0, swing / 4 + (30 if flip else 0) + missing_bonus)
            rows.append({
                "route_id": row["route_id"], "field_name": field, "current_status": row.get("operator_claim_status", "") if field == "operator_readiness" else "uncertain_or_scenario",
                "current_value": round(current, 3), "low_assumption": round(low, 3), "high_assumption": round(high, 3),
                "rank_low": rank_low, "rank_high": rank_high, "max_rank_swing": swing,
                "portfolio_flip_possible": flip, "currently_selected": selected,
                "validation_priority_score": round(priority, 2), "deterministic_reason": reason,
                "assumption_source_id": source_id,
            })
    details = pd.DataFrame(rows).sort_values(["route_id", "validation_priority_score", "field_name"], ascending=[True, False, True])
    details.to_csv(PROCESSED_DIR / "validation_priorities.csv", index=False)
    payload_routes = []
    summaries = []
    for route_id, group in details.groupby("route_id", sort=False):
        top = group.head(4).to_dict("records")
        payload_routes.append({"route_id": route_id, "priorities": top})
        first = top[0]
        summaries.append({
            "route_id": route_id,
            "highest_value_missing_evidence": first["field_name"],
            "validation_priority_score": first["validation_priority_score"],
            "maximum_rank_swing": first["max_rank_swing"],
            "portfolio_flip_possible": bool(any(item["portfolio_flip_possible"] for item in top)),
            "validation_priority_reason": first["deterministic_reason"],
        })
    write_json(PROCESSED_DIR / "validation_priorities.json", {"method": "deterministic_field_perturbation_v1", "routes": payload_routes})
    summary = pd.DataFrame(summaries)
    columns = [column for column in summary.columns if column != "route_id"]
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    score_data = pd.read_csv(score_path, dtype={"route_id": str}).drop(columns=columns, errors="ignore").merge(summary, on="route_id", how="left")
    geo_data = gpd.read_file(geo_path).drop(columns=columns, errors="ignore").merge(summary, on="route_id", how="left")
    score_data.to_csv(score_path, index=False)
    geo_data.to_file(geo_path, driver="GeoJSON")
    print(f"[PASS] value-of-information: {len(details):,} route-field perturbations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
