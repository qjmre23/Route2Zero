"""Task 6: calculate a clearly labeled WorldPop density equity proxy."""

from __future__ import annotations

import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from rasterio.windows import from_bounds
from shapely.geometry import box, mapping

from common import PROCESSED_DIR, ROOT, ensure_output_dirs, minmax_score


WORLDPOP_RASTER = ROOT / "data" / "raw" / "reference" / "phl_ppp_2020_1km_Aggregated.tif"
NCR_BOUNDS_WGS84 = (120.85, 14.35, 121.20, 14.85)
BUFFER_METERS = 300


def valid_values(array: np.ndarray, nodata: float | None) -> np.ndarray:
    values = array.astype(float).ravel()
    values = values[np.isfinite(values)]
    if nodata is not None:
        values = values[~np.isclose(values, nodata)]
    return values[values >= 0]


def main() -> int:
    ensure_output_dirs()
    if not WORLDPOP_RASTER.exists():
        raise FileNotFoundError(
            f"Missing {WORLDPOP_RASTER}. Retrieve the documented WorldPop fallback before running."
        )
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson").to_crs("EPSG:32651")
    route_buffers = routes[["route_id", "geometry"]].copy()
    route_buffers["geometry"] = route_buffers.geometry.buffer(BUFFER_METERS)

    rows: list[dict] = []
    with rasterio.open(WORLDPOP_RASTER) as dataset:
        if dataset.crs is None:
            raise ValueError("WorldPop raster is missing a CRS")
        ncr_bounds = (
            gpd.GeoSeries([box(*NCR_BOUNDS_WGS84)], crs="EPSG:4326")
            .to_crs(dataset.crs)
            .total_bounds
        )
        window = from_bounds(*ncr_bounds, transform=dataset.transform)
        ncr_values = valid_values(dataset.read(1, window=window), dataset.nodata)
        positive = ncr_values[ncr_values > 0]
        if positive.size == 0:
            raise ValueError("No positive WorldPop cells found in the NCR analysis window")
        high_density_cutoff = float(np.percentile(positive, 75))

        raster_buffers = route_buffers.to_crs(dataset.crs)
        for row in raster_buffers.itertuples(index=False):
            try:
                clipped, _ = mask(
                    dataset,
                    [mapping(row.geometry)],
                    crop=True,
                    all_touched=True,
                    filled=False,
                )
                values = clipped[0].compressed().astype(float)
                values = values[np.isfinite(values) & (values >= 0)]
            except ValueError:
                values = np.array([], dtype=float)
            total_population = float(values.sum()) if values.size else float("nan")
            high_population = float(values[values >= high_density_cutoff].sum()) if values.size else float("nan")
            overlap_pct = (
                high_population / total_population * 100.0
                if pd.notna(total_population) and total_population > 0
                else float("nan")
            )
            rows.append(
                {
                    "route_id": row.route_id,
                    "equity_overlap_pct": overlap_pct,
                    "corridor_population_proxy": total_population,
                }
            )

    output = pd.DataFrame(rows)
    output["equity_score"] = minmax_score(output["equity_overlap_pct"]).round(2)
    output["equity_overlap_pct"] = output["equity_overlap_pct"].round(3)
    output["corridor_population_proxy"] = output["corridor_population_proxy"].round(1)
    output["equity_source"] = "worldpop_2020_1km_population_density_proxy"
    output["equity_confidence"] = "low_resolution_density_not_settlement_boundaries"
    output["manually_digitized"] = False
    output["high_density_cutoff_people_per_cell"] = round(high_density_cutoff, 3)
    output["catchment_buffer_m"] = BUFFER_METERS
    output.to_csv(PROCESSED_DIR / "equity_score.csv", index=False)
    print(f"[PASS] equity density proxy scored: {output['equity_score'].notna().sum():,}/{len(output):,}")
    print(f"[INFO] NCR high-density threshold: {high_density_cutoff:.3f} people per 1 km cell")
    print(f"[PASS] wrote {PROCESSED_DIR / 'equity_score.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
