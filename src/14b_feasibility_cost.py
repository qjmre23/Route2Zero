"""Create order-of-magnitude fleet and capital scenarios without inventing a budget."""

from __future__ import annotations

import math
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, read_json, write_json


def optional_sum(frame: pd.DataFrame, column: str) -> float | None:
    values = pd.to_numeric(frame[column], errors="coerce")
    return None if values.notna().sum() == 0 else round(float(values.sum()), 2)


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "feasibility_cost_config.json")
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    km_per_vehicle = float(config["assumed_vehicle_km_per_day"]["value"])
    vehicle_cost = float(config["vehicle_unit_cost_php"]["value"])
    vehicles_per_charger = float(config["vehicles_per_charger_per_day"]["value"])
    charger_cost = float(config["charger_unit_cost_php"]["value"])

    daily_vkt = pd.to_numeric(scores["daily_vkt"], errors="coerce")
    scores["fleet_size_proxy"] = daily_vkt.map(lambda value: math.ceil(value / km_per_vehicle) if pd.notna(value) else np.nan)
    scores["charger_count_proxy"] = scores["fleet_size_proxy"].map(
        lambda value: math.ceil(float(value) / vehicles_per_charger) if pd.notna(value) else np.nan
    )
    scores["vehicle_capex_proxy_php"] = scores["fleet_size_proxy"] * vehicle_cost
    scores["charger_capex_proxy_php"] = scores["charger_count_proxy"] * charger_cost
    scores["total_capex_proxy_php"] = scores["vehicle_capex_proxy_php"] + scores["charger_capex_proxy_php"]
    scores["fleet_proxy_claim_status"] = np.where(daily_vkt.notna(), "PROXY", "MISSING")
    scores["vehicle_cost_claim_status"] = np.where(scores["vehicle_capex_proxy_php"].notna(), "PROXY", "MISSING")
    scores["charger_cost_claim_status"] = np.where(scores["charger_capex_proxy_php"].notna(), "PROXY", "MISSING")
    scores["financing_claim_status"] = "MISSING"
    scores["feasibility_source_ids"] = "doe_energy_investment_kit_2024|pna_ejeepney_trial_2023"
    scores["feasibility_method_version"] = config["version"]

    route_columns = [
        "route_id", "route_long_name", "corridor_type_label", "phase1_selected", "daily_vkt",
        "fleet_size_proxy", "charger_count_proxy", "vehicle_capex_proxy_php",
        "charger_capex_proxy_php", "total_capex_proxy_php", "fleet_proxy_claim_status",
        "vehicle_cost_claim_status", "charger_cost_claim_status", "financing_claim_status",
        "feasibility_source_ids", "feasibility_method_version",
    ]
    scores[route_columns].to_csv(PROCESSED_DIR / "feasibility_cost_routes.csv", index=False)

    phase1 = scores[scores["phase1_selected"].astype(bool)]
    type_summary = []
    for corridor_type, frame in scores.groupby("corridor_type_label", dropna=False):
        type_summary.append({
            "corridor_type": str(corridor_type),
            "route_count": int(len(frame)),
            "median_fleet_size_proxy": round(float(frame["fleet_size_proxy"].median()), 1),
            "median_total_capex_proxy_php": round(float(frame["total_capex_proxy_php"].median()), 2),
            "claim_status": "PROXY",
        })
    payload = {
        "version": config["version"],
        "currency": config["currency"],
        "scope": "order-of-magnitude validation scenario; not a budget or procurement estimate",
        "assumptions": config,
        "phase1": {
            "route_count": int(len(phase1)),
            "fleet_size_proxy": optional_sum(phase1, "fleet_size_proxy"),
            "charger_count_proxy": optional_sum(phase1, "charger_count_proxy"),
            "vehicle_capex_proxy_php": optional_sum(phase1, "vehicle_capex_proxy_php"),
            "charger_capex_proxy_php": optional_sum(phase1, "charger_capex_proxy_php"),
            "total_capex_proxy_php": optional_sum(phase1, "total_capex_proxy_php"),
            "financing_terms": None,
            "fleet_claim_status": "PROXY",
            "cost_claim_status": "PROXY",
            "financing_claim_status": "MISSING",
        },
        "corridor_type_summary": type_summary,
        "excluded_costs": config["excluded_costs"],
        "disclaimer": "Confirm route-level fleet, duty cycle, depot, tariff, interconnection and financing evidence before using these figures for any decision.",
    }
    write_json(PROCESSED_DIR / "feasibility_cost_scenarios.json", payload)

    score_columns = [column for column in scores.columns if column not in {
        "fleet_size_proxy", "charger_count_proxy", "vehicle_capex_proxy_php", "charger_capex_proxy_php",
        "total_capex_proxy_php", "fleet_proxy_claim_status", "vehicle_cost_claim_status",
        "charger_cost_claim_status", "financing_claim_status", "feasibility_source_ids", "feasibility_method_version"
    }]
    new_columns = [column for column in scores.columns if column not in score_columns]
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    scores.to_csv(score_path, index=False)
    geodata = gpd.read_file(geo_path).drop(columns=new_columns, errors="ignore")
    geodata = geodata.merge(scores[["route_id", *new_columns]], on="route_id", how="left")
    geodata.to_file(geo_path, driver="GeoJSON")
    print(f"[PASS] feasibility scenarios: {len(scores):,} routes; Phase-1 fleet proxy={optional_sum(phase1, 'fleet_size_proxy')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
