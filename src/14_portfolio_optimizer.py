"""Create an evidence-constrained Phase-1 shortlist without fabricated budgets."""

from __future__ import annotations

import sys
from collections import Counter

import geopandas as gpd
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, parse_grade, read_json, stable_hash, write_json


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
    minimum_grade = parse_grade(scenario["minimum_evidence_grade"])
    eligible = scores[
        scores["evidence_grade"].map(parse_grade).ge(minimum_grade)
        & scores["equity_score"].ge(float(scenario["minimum_equity_score"]))
    ].copy()
    if scenario.get("exclude_inactive_routes", True):
        eligible = eligible[~eligible["active_status"].eq("inactive")]
    eligible = eligible.sort_values(["portfolio_objective", "just_transition_score", "route_id"], ascending=[False, False, True])
    selected_rows = []
    city_counts: Counter[str] = Counter()
    corridor_counts: Counter[str] = Counter()
    evidence_limited = 0
    for row in eligible.itertuples(index=False):
        if len(selected_rows) >= int(scenario["max_corridors"]):
            break
        city = str(row.primary_city)
        if city_counts[city] >= int(scenario["maximum_corridors_per_primary_city"]):
            continue
        corridor = str(row.normalized_corridor_id)
        if corridor_counts[corridor] >= int(scenario["maximum_route_directions_per_corridor"]):
            continue
        is_limited = row.robustness_label == "EVIDENCE-LIMITED"
        if is_limited and evidence_limited >= int(scenario["maximum_evidence_limited_corridors"]):
            continue
        selected_rows.append(row)
        city_counts[city] += 1
        corridor_counts[corridor] += 1
        evidence_limited += int(is_limited)
    if len(selected_rows) != int(scenario["max_corridors"]):
        raise ValueError(f"Portfolio scenario infeasible: selected {len(selected_rows)} of {scenario['max_corridors']} corridors")
    selected_ids = [row.route_id for row in selected_rows]
    top_n_ids = scores.sort_values(["rank", "route_id"]).head(int(scenario["max_corridors"]))["route_id"].tolist()
    selected = scores[scores["route_id"].isin(selected_ids)].copy()
    scenario_payload = {
        "source_scenario_id": str(scores["scenario_id"].iloc[0]),
        "constraints": scenario,
        "selected_route_ids": selected_ids,
    }
    scenario_id = "prt-" + stable_hash(scenario_payload, 10)
    result = {
        "scenario_id": scenario_id,
        "title": scenario["title"],
        "source_scenario_id": str(scores["scenario_id"].iloc[0]),
        "mode": scenario["mode"],
        "optimization_method": "deterministic_selection",
        "constraints": scenario,
        "status": "feasible",
        "selected_route_ids": selected_ids,
        "selected_routes": [
            {
                "route_id": row.route_id,
                "route_long_name": row.route_long_name,
                "primary_city": row.primary_city,
                "priority_score": round(float(row.just_transition_score), 2),
                "evidence_grade": row.evidence_grade,
                "robustness_label": row.robustness_label,
                "climate_low_t_year": round(float(row.net_co2e_avoided_t_year_low), 1),
                "climate_high_t_year": round(float(row.net_co2e_avoided_t_year_high), 1),
            }
            for row in selected_rows
        ],
        "simple_top_n_route_ids": top_n_ids,
        "added_by_constraints": sorted(set(selected_ids) - set(top_n_ids)),
        "removed_by_constraints": sorted(set(top_n_ids) - set(selected_ids)),
        "portfolio_climate_impact_t_year": {
            "low": round(float(selected["net_co2e_avoided_t_year_low"].sum()), 1),
            "base": round(float(selected["net_co2e_avoided_t_year_base"].sum()), 1),
            "high": round(float(selected["net_co2e_avoided_t_year_high"].sum()), 1),
        },
        "average_equity_score": round(float(selected["equity_score"].mean()), 1),
        "average_evidence_confidence": round(float(selected["overall_evidence_confidence"].mean()), 1),
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
    membership["portfolio_exclusion_reason"] = "not selected after evidence, equity and city-coverage constraints"
    membership.loc[membership["phase1_selected"], "portfolio_exclusion_reason"] = "selected"
    membership.to_csv(PROCESSED_DIR / "portfolio_membership.csv", index=False)
    columns = ["portfolio_scenario_id", "phase1_selected", "simple_top_n_selected", "portfolio_exclusion_reason"]
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    base_scores = pd.read_csv(score_path, dtype={"route_id": str}).drop(columns=columns, errors="ignore").merge(membership, on="route_id", how="left")
    geodata = gpd.read_file(geo_path).drop(columns=columns, errors="ignore").merge(membership, on="route_id", how="left")
    base_scores.to_csv(score_path, index=False)
    geodata.to_file(geo_path, driver="GeoJSON")
    print(f"[PASS] Phase-1 portfolio {scenario_id}: {len(selected_ids)} corridors; differs from top-N={set(selected_ids) != set(top_n_ids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
