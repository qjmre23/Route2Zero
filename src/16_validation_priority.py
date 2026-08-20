"""Quantify decision value by perturbing evidence and re-running selection."""

from __future__ import annotations

import math
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, minmax_score, read_json, write_json
from portfolio_selection import PortfolioSelectionError, PortfolioSelector


DIMENSIONS = ["climate_impact_score", "equity_score", "charging_readiness_score", "operator_effective_score"]


def rank_for_score(value: float, baseline_scores: np.ndarray) -> int:
    if not np.isfinite(value):
        return len(baseline_scores)
    return int(np.sum(baseline_scores > value) + 1)


def fixed_scale_score(value: float, baseline_values: pd.Series) -> float:
    valid = pd.to_numeric(baseline_values, errors="coerce").dropna()
    if not np.isfinite(value) or valid.empty:
        return math.nan
    low, high = float(valid.min()), float(valid.max())
    if math.isclose(low, high):
        return 50.0
    return float(np.clip((value - low) / (high - low) * 100.0, 0.0, 100.0))


def selected_set(selector: PortfolioSelector, override: dict[str, float] | None = None) -> tuple[set[str], bool]:
    try:
        return set(selector.select(override)), True
    except PortfolioSelectionError:
        return set(), False


def effective_component_weight(row: pd.Series, component: str, weights: dict[str, float], penalty: float) -> float:
    available = [name for name in DIMENSIONS if pd.notna(row.get(name))]
    available_weight = sum(float(weights[name]) for name in available)
    if component not in available or available_weight <= 0:
        return 0.0
    multiplier = 1.0 if len(available) == len(DIMENSIONS) else penalty
    return float(weights[component]) / available_weight * multiplier


def main() -> int:
    ensure_output_dirs()
    policy = read_json(CONFIG_DIR / "policy_model.json")
    config = read_json(CONFIG_DIR / "validation_priority_config.json")
    optimization = read_json(CONFIG_DIR / "optimization_scenarios.json")["scenarios"][0]
    weights = policy["default_weights"]
    penalty = float(policy["reduced_information_penalty"])
    perturb = config["perturbations"]
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    baseline = scores["just_transition_score"].to_numpy(dtype=float)
    climate_low_score = minmax_score(scores["net_co2e_avoided_t_year_low"])
    climate_high_score = minmax_score(scores["net_co2e_avoided_t_year_high"])
    base_climate_raw = pd.to_numeric(scores["net_co2e_avoided_t_year_base"], errors="coerce")
    selector = PortfolioSelector(scores, optimization)
    baseline_selected, baseline_feasible = selected_set(selector)
    rows: list[dict[str, object]] = []

    for index, row in scores.iterrows():
        geometry_grade = str(row.get("geometry_reliability_grade", "D"))
        geometry_relative = float(perturb["geometry_reliability"]["relative_uncertainty_by_grade"].get(geometry_grade, 0.35))
        service_status = str(row.get("service_intensity_claim_status", "MISSING"))
        service_relative = float(perturb["service_intensity"]["relative_uncertainty_by_claim_status"].get(service_status, 0.50))
        raw_base = float(base_climate_raw.iloc[index]) if pd.notna(base_climate_raw.iloc[index]) else math.nan
        geometry_scores = sorted([
            fixed_scale_score(raw_base * (1.0 - geometry_relative), base_climate_raw),
            fixed_scale_score(raw_base * (1.0 + geometry_relative), base_climate_raw),
        ])
        service_scores = sorted([
            fixed_scale_score(raw_base * (1.0 - service_relative), base_climate_raw),
            fixed_scale_score(raw_base * (1.0 + service_relative), base_climate_raw),
        ])
        charging_delta = float(perturb["charging_readiness"]["absolute_delta"])
        equity_delta = float(perturb["equity_population_exposure"]["absolute_delta"])
        charging_current = pd.to_numeric(pd.Series([row.get("charging_readiness_score")]), errors="coerce").iloc[0]
        equity_current = pd.to_numeric(pd.Series([row.get("equity_score")]), errors="coerce").iloc[0]
        variants = [
            (
                "operator_readiness", "operator_effective_score",
                float(perturb["operator_readiness"]["low"]), float(perturb["operator_readiness"]["high"]),
                row.get("operator_claim_status", ""),
            ),
            (
                "charging_readiness", "charging_readiness_score",
                max(0.0, float(charging_current) - charging_delta) if pd.notna(charging_current) else math.nan,
                min(100.0, float(charging_current) + charging_delta) if pd.notna(charging_current) else math.nan,
                row.get("charging_claim_status", ""),
            ),
            (
                "climate_assumptions", "climate_impact_score",
                float(climate_low_score.iloc[index]) if pd.notna(climate_low_score.iloc[index]) else math.nan,
                float(climate_high_score.iloc[index]) if pd.notna(climate_high_score.iloc[index]) else math.nan,
                row.get("climate_claim_status", ""),
            ),
            (
                "equity_population_exposure", "equity_score",
                max(0.0, float(equity_current) - equity_delta) if pd.notna(equity_current) else math.nan,
                min(100.0, float(equity_current) + equity_delta) if pd.notna(equity_current) else math.nan,
                row.get("equity_claim_status", ""),
            ),
            (
                "geometry_reliability", "climate_impact_score",
                geometry_scores[0], geometry_scores[1], row.get("geometry_claim_status", ""),
            ),
            (
                "service_intensity", "climate_impact_score",
                service_scores[0], service_scores[1], row.get("service_intensity_claim_status", ""),
            ),
        ]
        for field, component, low, high, current_status in variants:
            current = float(row[component]) if pd.notna(row.get(component)) else math.nan
            component_weight = effective_component_weight(row, component, weights, penalty)
            if not np.isfinite(current) or not np.isfinite(low) or not np.isfinite(high) or component_weight == 0:
                low_score = high_score = float(row["just_transition_score"])
                perturbation_available = False
            else:
                low_score = float(row["just_transition_score"]) + (low - current) * component_weight
                high_score = float(row["just_transition_score"]) + (high - current) * component_weight
                perturbation_available = True
            low_score, high_score = sorted([low_score, high_score])
            rank_low = rank_for_score(low_score, baseline)
            rank_high = rank_for_score(high_score, baseline)
            low_selected, low_feasible = selected_set(selector, {row["route_id"]: low_score})
            high_selected, high_feasible = selected_set(selector, {row["route_id"]: high_score})
            flip = bool(
                low_selected != baseline_selected
                or high_selected != baseline_selected
                or low_feasible != baseline_feasible
                or high_feasible != baseline_feasible
            )
            swing = abs(rank_low - rank_high)
            missing_bonus = 20 if current_status in {"MISSING", "NEUTRAL_PRIOR", "PROXY"} else 8
            priority = min(100.0, swing / 4 + (30 if flip else 0) + missing_bonus)
            details = perturb[field]
            rows.append({
                "route_id": row["route_id"],
                "field_name": field,
                "affected_score_component": component,
                "current_status": current_status,
                "current_value": round(current, 3) if np.isfinite(current) else np.nan,
                "low_assumption": round(low, 3) if np.isfinite(low) else np.nan,
                "high_assumption": round(high, 3) if np.isfinite(high) else np.nan,
                "rank_low": rank_low,
                "rank_high": rank_high,
                "max_rank_swing": swing,
                "portfolio_flip_possible": flip,
                "baseline_portfolio_feasible": baseline_feasible,
                "low_portfolio_feasible": low_feasible,
                "high_portfolio_feasible": high_feasible,
                "currently_selected": row["route_id"] in baseline_selected,
                "perturbation_available": perturbation_available,
                "validation_priority_score": round(priority, 2),
                "deterministic_reason": details["reason"],
                "assumption_source_id": details["source_id"],
                "perturbation_config_source_id": "route2zero_validation_priority_v2",
                "selection_method": config["portfolio_selector_method"],
            })

    details = pd.DataFrame(rows).sort_values(
        ["route_id", "validation_priority_score", "field_name"], ascending=[True, False, True]
    )
    details.to_csv(PROCESSED_DIR / "validation_priorities.csv", index=False)
    payload_routes = []
    summaries = []
    for route_id, group in details.groupby("route_id", sort=False):
        top = group.head(6).to_dict("records")
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
    write_json(PROCESSED_DIR / "validation_priorities.json", {
        "method": config["version"],
        "selection_method": config["portfolio_selector_method"],
        "baseline_portfolio_feasible": baseline_feasible,
        "routes": payload_routes,
    })
    summary = pd.DataFrame(summaries)
    columns = [column for column in summary.columns if column != "route_id"]
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    score_data = pd.read_csv(score_path, dtype={"route_id": str}).drop(columns=columns, errors="ignore").merge(summary, on="route_id", how="left")
    geo_data = gpd.read_file(geo_path).drop(columns=columns, errors="ignore").merge(summary, on="route_id", how="left")
    score_data.to_csv(score_path, index=False)
    geo_data.to_file(geo_path, driver="GeoJSON")
    print(f"[PASS] value-of-information: {len(details):,} route-field perturbations; actual selector reruns enabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
