"""Create an evidence-constrained Phase-1 shortlist without fabricated budgets."""

from __future__ import annotations

import sys

import geopandas as gpd
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, read_json, stable_hash, write_json
from portfolio_selection import PortfolioSelectionError, PortfolioSelector


def optional_round(value: object, digits: int = 1) -> float | None:
    return None if pd.isna(value) else round(float(value), digits)


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "optimization_scenarios.json")
    scenario = config["scenarios"][0]
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    scores["portfolio_objective"] = (
        scores["just_transition_score"] * 0.60
        + scores["top_10_probability"] * 100 * 0.25
        + scores["overall_evidence_confidence"] * 0.15
    )
    selector = PortfolioSelector(scores, scenario)
    diagnostics: dict[str, object] | None = None
    try:
        selected_ids = selector.select()
        status = "feasible"
    except PortfolioSelectionError as error:
        selected_ids = []
        status = "infeasible"
        diagnostics = error.diagnostics

    max_corridors = int(scenario["max_corridors"])
    top_n_ids = scores.sort_values(["rank", "route_id"], na_position="last").head(max_corridors)["route_id"].tolist()
    indexed = scores.set_index("route_id", drop=False)
    selected = indexed.loc[selected_ids].copy() if selected_ids else scores.iloc[0:0].copy()
    scenario_payload = {
        "source_scenario_id": str(scores["scenario_id"].iloc[0]),
        "constraints": scenario,
        "selection_engine_version": "deterministic-selection-v2",
    }
    scenario_id = "prt-" + stable_hash(scenario_payload, 10)
    selected_routes = []
    for route_id in selected_ids:
        row = indexed.loc[route_id]
        selected_routes.append({
            "route_id": route_id,
            "route_long_name": row["route_long_name"],
            "primary_city": row["primary_city"],
            "priority_score": optional_round(row["just_transition_score"], 2),
            "evidence_grade": row["evidence_grade"],
            "robustness_label": row["robustness_label"],
            "climate_low_t_year": optional_round(row["net_co2e_avoided_t_year_low"]),
            "climate_high_t_year": optional_round(row["net_co2e_avoided_t_year_high"]),
        })
    climate_summary = {
        name: (round(float(selected[column].sum()), 1) if status == "feasible" else None)
        for name, column in {
            "low": "net_co2e_avoided_t_year_low",
            "base": "net_co2e_avoided_t_year_base",
            "high": "net_co2e_avoided_t_year_high",
        }.items()
    }
    result = {
        "scenario_id": scenario_id,
        "title": scenario["title"],
        "source_scenario_id": str(scores["scenario_id"].iloc[0]),
        "mode": scenario["mode"],
        "optimization_method": "deterministic_selection",
        "selection_engine_version": "deterministic-selection-v2",
        "constraints": scenario,
        "status": status,
        "infeasibility_diagnostics": diagnostics,
        "selected_route_ids": selected_ids,
        "selected_routes": selected_routes,
        "simple_top_n_route_ids": top_n_ids,
        "added_by_constraints": sorted(set(selected_ids) - set(top_n_ids)),
        "removed_by_constraints": sorted(set(top_n_ids) - set(selected_ids)),
        "portfolio_climate_impact_t_year": climate_summary,
        "average_equity_score": optional_round(selected["equity_score"].mean()) if status == "feasible" else None,
        "average_evidence_confidence": optional_round(selected["overall_evidence_confidence"].mean()) if status == "feasible" else None,
        "evidence_grade_distribution": selected["evidence_grade"].value_counts().to_dict(),
        "city_distribution": selected["primary_city"].value_counts().to_dict(),
        "binding_constraints": [
            f"maximum {scenario['max_corridors']} corridors",
            f"maximum {scenario['maximum_corridors_per_primary_city']} corridors per primary city",
            f"maximum {scenario['maximum_route_directions_per_corridor']} route direction per normalized corridor",
            f"minimum equity score {scenario['minimum_equity_score']}",
            f"minimum evidence grade {scenario['minimum_evidence_grade']}",
        ],
        "hypothetical_budget_used": False,
        "disclaimer": "This is an evidence-validation shortlist, not a procurement or investment authorization.",
    }
    write_json(PROCESSED_DIR / "portfolio_scenarios.json", {"version": config["version"], "scenarios": [result]})

    membership = scores[["route_id"]].copy()
    membership["portfolio_scenario_id"] = scenario_id
    membership["phase1_selected"] = membership["route_id"].isin(selected_ids)
    membership["simple_top_n_selected"] = membership["route_id"].isin(top_n_ids)
    membership["portfolio_exclusion_reason"] = (
        "portfolio scenario infeasible; no route selected"
        if status == "infeasible"
        else "not selected after evidence, equity and city-coverage constraints"
    )
    membership.loc[membership["phase1_selected"], "portfolio_exclusion_reason"] = "selected"
    membership.to_csv(PROCESSED_DIR / "portfolio_membership.csv", index=False)
    columns = ["portfolio_scenario_id", "phase1_selected", "simple_top_n_selected", "portfolio_exclusion_reason"]
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    base_scores = pd.read_csv(score_path, dtype={"route_id": str}).drop(columns=columns, errors="ignore").merge(membership, on="route_id", how="left")
    geodata = gpd.read_file(geo_path).drop(columns=columns, errors="ignore").merge(membership, on="route_id", how="left")
    base_scores.to_csv(score_path, index=False)
    geodata.to_file(geo_path, driver="GeoJSON")
    prefix = "[PASS]" if status == "feasible" else "[WARN]"
    print(f"{prefix} Phase-1 portfolio {scenario_id}: status={status}; selected={len(selected_ids)}/{max_corridors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
