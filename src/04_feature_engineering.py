"""Build the canonical, leakage-aware route feature store for Route2Zero 2.0."""

from __future__ import annotations

import re
import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from common import PROCESSED_DIR, ROOT, ensure_output_dirs, load_gtfs, normalize_corridor_name


HUB_PATTERN = re.compile(r"terminal|station|market|palengke|mall|plaza|crossing|junction", re.IGNORECASE)


def load_validation_defaults(routes: pd.DataFrame) -> pd.DataFrame:
    path = ROOT / "data" / "validated" / "route_validation.csv"
    supplied = pd.read_csv(path, dtype={"route_id": str})
    defaults = routes[["route_id", "route_long_name"]].copy()
    defaults["validation_status"] = "historic_only"
    defaults["active_status"] = "uncertain"
    defaults["validation_date"] = ""
    defaults["validator"] = ""
    defaults["source_type"] = "historic_gtfs_baseline"
    defaults["source_reference"] = "sakay_gtfs_master_historic"
    defaults["notes"] = "No current route validation supplied."
    defaults["observed_headway_min"] = np.nan
    defaults["observed_service_window_hrs"] = np.nan
    defaults["geometry_verified"] = False
    defaults["operator_name_if_verified"] = ""
    defaults["evidence_quality"] = "historic_only"
    if supplied.empty:
        return defaults
    supplied = supplied.drop_duplicates("route_id", keep="last")
    merged = defaults.set_index("route_id")
    for column in supplied.columns:
        if column == "route_id":
            continue
        merged.loc[supplied["route_id"], column] = supplied.set_index("route_id")[column]
    return merged.reset_index()


def representative_hub_counts(routes: pd.DataFrame) -> pd.DataFrame:
    stop_times = load_gtfs("stop_times.txt")
    stops = load_gtfs("stops.txt")
    joined = (
        routes[["route_id", "representative_trip_id"]]
        .merge(stop_times[["trip_id", "stop_id"]], left_on="representative_trip_id", right_on="trip_id", how="left")
        .merge(stops[["stop_id", "stop_name"]], on="stop_id", how="left")
    )
    joined["hub_like"] = joined["stop_name"].fillna("").str.contains(HUB_PATTERN)
    return joined.groupby("route_id")["hub_like"].sum().astype(int).rename("hub_connectivity_count").reset_index()


def main() -> int:
    ensure_output_dirs()
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson")
    frequency = pd.read_csv(PROCESSED_DIR / "route_frequency.csv", dtype={"route_id": str})
    emissions = pd.read_csv(PROCESSED_DIR / "emissions_score.csv", dtype={"route_id": str})
    equity = pd.read_csv(PROCESSED_DIR / "equity_score.csv", dtype={"route_id": str})
    geometry = pd.read_csv(PROCESSED_DIR / "geometry_reliability.csv", dtype={"route_id": str})
    validation = load_validation_defaults(routes)
    validation.to_csv(PROCESSED_DIR / "route_validation.csv", index=False)

    output = routes.drop(columns="geometry").merge(frequency.drop(columns=["route_long_name"], errors="ignore"), on="route_id", how="left")
    output = output.merge(emissions[["route_id", "daily_vehicle_km_proxy"]], on="route_id", how="left")
    output = output.merge(equity[["route_id", "corridor_population_proxy", "equity_overlap_pct"]], on="route_id", how="left")
    output = output.merge(geometry, on=["route_id", "geometry_source"], how="left")
    output = output.merge(representative_hub_counts(routes), on="route_id", how="left")
    output = output.merge(validation.drop(columns="route_long_name", errors="ignore"), on="route_id", how="left")

    output["normalized_corridor_id"] = output["route_long_name"].map(normalize_corridor_name)
    output["stops_per_km"] = output["stop_count"] / output["length_km"].replace(0, np.nan)
    output["mean_stop_spacing_m"] = output["length_km"] * 1000 / (output["stop_count"] - 1).replace(0, np.nan)
    output["geometry_source_is_shape"] = output["geometry_source"].eq("shape").astype(int)
    output["historic_daily_vehicle_km_proxy"] = output["daily_vehicle_km_proxy"]
    output["service_input_claim_status"] = np.where(output["trips_per_day_estimate"].notna(), "DERIVED", "MISSING")
    output["feature_source_ids"] = "sakay_gtfs_master_historic|worldpop_phl_2020_1km"
    output = output.sort_values("route_id").reset_index(drop=True)
    if output["route_id"].duplicated().any() or len(output) != 1522:
        raise AssertionError("Feature store must contain one row per 1,522 route IDs")
    output.to_csv(PROCESSED_DIR / "route_features.csv", index=False)
    print(f"[PASS] feature store: {len(output):,} rows, {len(output.columns)} columns")
    return 0


if __name__ == "__main__":
    sys.exit(main())
