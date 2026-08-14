"""Task 3: classify jeepneys and construct auditable route geometry."""

from __future__ import annotations

import sys

import geopandas as gpd
import pandas as pd
from pyproj import Geod
from shapely.geometry import LineString

from common import PROCESSED_DIR, ensure_output_dirs, load_gtfs


GEOD = Geod(ellps="WGS84")


def geodesic_length_km(line: LineString) -> float:
    lons, lats = line.xy
    return abs(float(GEOD.line_length(lons, lats))) / 1000.0


def unique_consecutive(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
    clean: list[tuple[float, float]] = []
    for coord in coords:
        if not clean or coord != clean[-1]:
            clean.append(coord)
    return clean


def main() -> int:
    ensure_output_dirs()
    routes = load_gtfs("routes.txt")
    trips = load_gtfs("trips.txt")
    stop_times = load_gtfs("stop_times.txt")
    stops = load_gtfs("stops.txt")
    shapes = load_gtfs("shapes.txt")

    jeepneys = routes[
        routes["agency_id"].eq("LTFRB") & routes["route_id"].str.contains("PUJ", na=False)
    ].copy()
    context = routes[~routes["route_id"].isin(jeepneys["route_id"])].copy()
    context["mode_context"] = context["route_id"].map(
        lambda value: "bus" if "PUB" in str(value) else "rail_or_other"
    )
    context.to_csv(PROCESSED_DIR / "comparison_routes.csv", index=False)

    trip_stop_counts = (
        stop_times.groupby("trip_id").size().rename("stop_count").reset_index()
        .merge(trips[["trip_id", "route_id", "shape_id"]], on="trip_id", how="inner")
    )
    representatives = (
        trip_stop_counts[trip_stop_counts["route_id"].isin(jeepneys["route_id"])]
        .sort_values(["route_id", "stop_count", "trip_id"], ascending=[True, False, True])
        .drop_duplicates("route_id")
    )

    shapes_work = shapes.copy()
    shapes_work["shape_pt_sequence_num"] = pd.to_numeric(
        shapes_work["shape_pt_sequence"], errors="coerce"
    )
    shapes_work["shape_pt_lon_num"] = pd.to_numeric(shapes_work["shape_pt_lon"], errors="coerce")
    shapes_work["shape_pt_lat_num"] = pd.to_numeric(shapes_work["shape_pt_lat"], errors="coerce")
    shape_lines: dict[str, LineString] = {}
    for shape_id, group in shapes_work.sort_values("shape_pt_sequence_num").groupby("shape_id"):
        coords = unique_consecutive(
            list(zip(group["shape_pt_lon_num"], group["shape_pt_lat_num"], strict=False))
        )
        coords = [(lon, lat) for lon, lat in coords if pd.notna(lon) and pd.notna(lat)]
        if len(coords) >= 2:
            shape_lines[str(shape_id)] = LineString(coords)

    rep_stops = (
        representatives[["route_id", "trip_id"]]
        .merge(stop_times[["trip_id", "stop_id", "stop_sequence"]], on="trip_id", how="left")
        .merge(stops[["stop_id", "stop_lon", "stop_lat"]], on="stop_id", how="left")
    )
    rep_stops["stop_sequence_num"] = pd.to_numeric(rep_stops["stop_sequence"], errors="coerce")
    rep_stops["stop_lon_num"] = pd.to_numeric(rep_stops["stop_lon"], errors="coerce")
    rep_stops["stop_lat_num"] = pd.to_numeric(rep_stops["stop_lat"], errors="coerce")
    stop_lines: dict[str, LineString] = {}
    for route_id, group in rep_stops.sort_values("stop_sequence_num").groupby("route_id"):
        coords = unique_consecutive(
            [
                (float(row.stop_lon_num), float(row.stop_lat_num))
                for row in group.itertuples()
                if pd.notna(row.stop_lon_num) and pd.notna(row.stop_lat_num)
            ]
        )
        if len(coords) >= 2:
            stop_lines[str(route_id)] = LineString(coords)

    representative_lookup = representatives.set_index("route_id").to_dict("index")
    records: list[dict] = []
    for route in jeepneys.itertuples(index=False):
        meta = representative_lookup.get(route.route_id)
        if meta is None:
            raise ValueError(f"No representative trip for {route.route_id}")
        shape_id = str(meta.get("shape_id")) if pd.notna(meta.get("shape_id")) else ""
        if shape_id in shape_lines:
            geometry = shape_lines[shape_id]
            geometry_source = "shape"
        else:
            geometry = stop_lines.get(route.route_id)
            geometry_source = "stop_sequence_approx"
        if geometry is None:
            raise ValueError(f"Unable to construct geometry for {route.route_id}")
        records.append(
            {
                "route_id": route.route_id,
                "route_short_name": route.route_short_name,
                "route_long_name": route.route_long_name,
                "route_desc": route.route_desc,
                "representative_trip_id": meta["trip_id"],
                "length_km": round(geodesic_length_km(geometry), 3),
                "geometry_source": geometry_source,
                "stop_count": int(meta["stop_count"]),
                "geometry": geometry,
            }
        )

    output = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    if len(output) != len(jeepneys):
        raise AssertionError(f"Expected {len(jeepneys)} routes, produced {len(output)}")
    output.to_file(PROCESSED_DIR / "jeepney_routes.geojson", driver="GeoJSON")
    source_counts = output["geometry_source"].value_counts().to_dict()
    print(f"[PASS] jeepney routes: {len(output):,}")
    print(f"[PASS] geometry sources: {source_counts}")
    print(f"[PASS] wrote {PROCESSED_DIR / 'jeepney_routes.geojson'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

