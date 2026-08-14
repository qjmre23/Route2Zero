"""Task 7: assign the official, coarse Luzon-grid renewable-share proxy."""

from __future__ import annotations

import sys

import geopandas as gpd
import pandas as pd

from common import PROCESSED_DIR, ROOT, ensure_output_dirs


DOE_LOOKUP = ROOT / "data" / "raw" / "reference" / "doe_2024_luzon_generation_mix.csv"
LUZON_VISAYAS_NGEF_OTHER_PROJECTS_TCO2_MWH = 0.7181


def main() -> int:
    ensure_output_dirs()
    lookup = pd.read_csv(DOE_LOOKUP)
    renewable = float(lookup.loc[lookup["category"].eq("Renewable energy"), "generation_gwh"].iloc[0])
    total = float(lookup.loc[lookup["category"].eq("Total"), "generation_gwh"].iloc[0])
    renewable_share_pct = renewable / total * 100.0
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson")[["route_id"]]
    output = pd.DataFrame({"route_id": routes["route_id"]})
    output["grid_feasibility_score"] = round(renewable_share_pct, 2)
    output["grid_renewable_share_pct"] = round(renewable_share_pct, 3)
    output["grid_emission_factor_tco2_mwh"] = LUZON_VISAYAS_NGEF_OTHER_PROJECTS_TCO2_MWH
    output["grid_region"] = "Luzon"
    output["grid_source"] = "DOE_2024_Luzon_renewable_generation_share"
    output["grid_confidence"] = "coarse_regional_proxy_no_depot_capacity_data"
    output["route_level_spatial_variation_available"] = False
    output.to_csv(PROCESSED_DIR / "grid_feasibility.csv", index=False)
    print(f"[PASS] Luzon renewable share proxy: {renewable_share_pct:.3f}%")
    print(f"[PASS] wrote {PROCESSED_DIR / 'grid_feasibility.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

