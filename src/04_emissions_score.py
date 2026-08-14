"""Task 5: score the emissions-reduction activity proxy."""

from __future__ import annotations

import sys

import geopandas as gpd
import pandas as pd

from common import PROCESSED_DIR, ensure_output_dirs, minmax_score


def main() -> int:
    ensure_output_dirs()
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson").drop(columns="geometry")
    frequency = pd.read_csv(PROCESSED_DIR / "route_frequency.csv", dtype={"route_id": str})
    output = routes[["route_id", "route_long_name", "length_km"]].merge(
        frequency[["route_id", "trips_per_day_estimate"]], on="route_id", how="left"
    )
    output["daily_vehicle_km_proxy"] = (
        pd.to_numeric(output["length_km"], errors="coerce")
        * pd.to_numeric(output["trips_per_day_estimate"], errors="coerce")
    )
    output["emissions_potential_score"] = minmax_score(output["daily_vehicle_km_proxy"]).round(2)
    output["emissions_source"] = "gtfs_route_length_x_estimated_trips_proxy"
    output["emissions_confidence"] = "proxy_not_measured_emissions"
    output.to_csv(PROCESSED_DIR / "emissions_score.csv", index=False)
    print(f"[PASS] emissions proxy scored: {output['emissions_potential_score'].notna().sum():,}/{len(output):,}")
    print(f"[PASS] wrote {PROCESSED_DIR / 'emissions_score.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
