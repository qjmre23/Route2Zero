"""Calculate low/base/high climate and energy scenarios from route service activity."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, minmax_score, read_json


def scenario_result(daily_vkt: pd.Series, params: dict, shared: dict) -> dict[str, pd.Series]:
    share = float(params["electrification_share"]["value"])
    diesel_efficiency = float(params["diesel_km_per_liter"]["value"])
    diesel_factor = float(params["diesel_kgco2e_per_liter"]["value"])
    electric_efficiency = float(params["electric_kwh_per_km"]["value"])
    charger_efficiency = float(shared["charger_efficiency"]["value"])
    grid_factor = float(params["grid_kgco2e_per_kwh"]["value"])
    days = float(shared["operating_days_per_year"]["value"])
    electrified_vkt = daily_vkt * share
    diesel_liters = electrified_vkt / diesel_efficiency
    baseline_co2e = diesel_liters * diesel_factor
    traction_energy = electrified_vkt * electric_efficiency
    electricity = traction_energy / charger_efficiency
    grid_co2e = electricity * grid_factor
    net_co2e = baseline_co2e - grid_co2e
    return {
        "electrified_vkt": electrified_vkt,
        "diesel_liters_avoided": diesel_liters,
        "electricity_kwh_day": electricity,
        "baseline_co2e_kg_day": baseline_co2e,
        "grid_co2e_kg_day": grid_co2e,
        "net_co2e_avoided_kg_day": net_co2e,
        "net_co2e_avoided_t_year": net_co2e * days / 1000.0,
    }


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "climate_scenarios.json")
    features = pd.read_csv(PROCESSED_DIR / "route_features.csv", dtype={"route_id": str})
    ml = pd.read_csv(PROCESSED_DIR / "ml_service_intensity.csv", dtype={"route_id": str})
    output = features[["route_id", "historic_daily_vehicle_km_proxy"]].merge(
        ml[["route_id", "ml_service_intensity_prediction", "ml_model_version", "ml_model_meaningful_vs_baseline"]],
        on="route_id", how="left",
    )
    use_ml = output["historic_daily_vehicle_km_proxy"].isna() & output["ml_model_meaningful_vs_baseline"].fillna(False).astype(bool)
    output["daily_vkt"] = output["historic_daily_vehicle_km_proxy"].where(~use_ml, output["ml_service_intensity_prediction"])
    output["service_intensity_source"] = np.where(use_ml, "ml_service_intensity_prediction", "historic_gtfs_service_activity_proxy")
    output["service_intensity_claim_status"] = np.where(use_ml, "ML_ESTIMATED", np.where(output["daily_vkt"].notna(), "DERIVED", "MISSING"))
    output["ml_service_intensity_used"] = use_ml

    for scenario_name in ("low", "base", "high"):
        values = scenario_result(output["daily_vkt"], config["scenarios"][scenario_name], config)
        for field, series in values.items():
            output[f"{field}_{scenario_name}"] = series.round(3)
    output["climate_impact_score"] = minmax_score(output["net_co2e_avoided_t_year_base"]).round(2)
    output["climate_assumption_set"] = config["version"]
    output["impact_is_scenario_not_measurement"] = True
    output["climate_claim_status"] = "SCENARIO"
    output["climate_source_ids"] = "sakay_gtfs_master_historic|doe_luzon_generation_2024|route2zero_climate_scenario_v1"
    output["grid_kgco2e_per_kwh_current"] = float(config["current_grid_kgco2e_per_kwh"]["value"])
    output["grid_kgco2e_per_kwh_low"] = float(config["scenarios"]["low"]["grid_kgco2e_per_kwh"]["value"])
    output["grid_kgco2e_per_kwh_base"] = float(config["scenarios"]["base"]["grid_kgco2e_per_kwh"]["value"])
    output["grid_kgco2e_per_kwh_high"] = float(config["scenarios"]["high"]["grid_kgco2e_per_kwh"]["value"])
    output["operating_days_per_year"] = int(config["operating_days_per_year"]["value"])
    output["electrification_share_low"] = float(config["scenarios"]["low"]["electrification_share"]["value"])
    output["electrification_share_base"] = float(config["scenarios"]["base"]["electrification_share"]["value"])
    output["electrification_share_high"] = float(config["scenarios"]["high"]["electrification_share"]["value"])
    output.to_csv(PROCESSED_DIR / "climate_impact.csv", index=False)
    negative = int((output["net_co2e_avoided_t_year_base"] < 0).sum())
    print(f"[PASS] climate scenarios: {output['climate_impact_score'].notna().sum():,}/{len(output):,}; negative base results={negative}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
