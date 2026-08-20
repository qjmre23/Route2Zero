"""Build route-specific charging evidence from a cached OSM infrastructure snapshot."""

from __future__ import annotations

import json
import math
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

from common import CONFIG_DIR, PROCESSED_DIR, ROOT, ensure_output_dirs, minmax_score, read_json


EARTH_RADIUS_KM = 6371.0088


def osm_points(payload: dict, key: str, value: str) -> tuple[np.ndarray, list[str]]:
    coords: list[tuple[float, float]] = []
    ids: list[str] = []
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        if tags.get(key) != value:
            continue
        lat = element.get("lat", element.get("center", {}).get("lat"))
        lon = element.get("lon", element.get("center", {}).get("lon"))
        if lat is None or lon is None:
            continue
        coords.append((float(lat), float(lon)))
        ids.append(f"{element.get('type', 'feature')}/{element.get('id')}")
    return np.asarray(coords, dtype=float), ids


def nearest_for_routes(routes: gpd.GeoDataFrame, infrastructure: np.ndarray, ids: list[str]) -> tuple[list[float], list[str]]:
    if len(infrastructure) == 0:
        return [math.nan] * len(routes), [""] * len(routes)
    tree = BallTree(np.radians(infrastructure), metric="haversine")
    distances: list[float] = []
    nearest_ids: list[str] = []
    for geometry in routes.geometry:
        points = np.asarray([(geometry.coords[0][1], geometry.coords[0][0]), (geometry.coords[-1][1], geometry.coords[-1][0])])
        values, indexes = tree.query(np.radians(points), k=1)
        position = int(np.argmin(values[:, 0]))
        distances.append(float(values[position, 0] * EARTH_RADIUS_KM))
        nearest_ids.append(ids[int(indexes[position, 0])])
    return distances, nearest_ids


def proximity_score(value: float, thresholds: list[float]) -> float:
    if pd.isna(value):
        return 0.0
    scores = [100.0, 82.0, 58.0, 32.0]
    for threshold, score in zip(thresholds, scores, strict=False):
        if value <= threshold:
            return score
    return 8.0


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "charging_config.json")
    snapshot_path = ROOT / "data" / "raw" / "osm_power" / "metro_manila_overpass.json"
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    substations, substation_ids = osm_points(payload, "power", "substation")
    chargers, charger_ids = osm_points(payload, "amenity", "charging_station")
    if len(substations) == 0:
        raise ValueError("OSM snapshot contains no mapped substations")
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson").sort_values("route_id").reset_index(drop=True)
    climate = pd.read_csv(PROCESSED_DIR / "climate_impact.csv", dtype={"route_id": str})
    sub_distance, sub_ids = nearest_for_routes(routes, substations, substation_ids)
    charger_distance, charger_nearest_ids = nearest_for_routes(routes, chargers, charger_ids)
    output = routes[["route_id"]].copy()
    output["nearest_substation_distance_km"] = np.round(sub_distance, 3)
    output["nearest_substation_osm_id"] = sub_ids
    output["nearest_mapped_charger_distance_km"] = np.round(charger_distance, 3)
    output["nearest_charger_osm_id"] = charger_nearest_ids
    output = output.merge(climate[["route_id", "electricity_kwh_day_low", "electricity_kwh_day_base", "electricity_kwh_day_high"]], on="route_id", how="left")
    output["mapped_substation_proximity_score"] = output["nearest_substation_distance_km"].map(lambda value: proximity_score(value, config["substation_distance_thresholds_km"]))
    output["mapped_charger_proximity_score"] = output["nearest_mapped_charger_distance_km"].map(lambda value: proximity_score(value, config["charger_distance_thresholds_km"]))
    output["candidate_terminal_count"] = 2
    output["terminal_evidence_score"] = 40.0
    output["energy_manageability_score"] = (100.0 - minmax_score(output["electricity_kwh_day_base"])).fillna(0.0)
    weights = config["component_weights"]
    output["charging_readiness_score"] = (
        output["mapped_substation_proximity_score"] * float(weights["mapped_substation_proximity"])
        + output["mapped_charger_proximity_score"] * float(weights["mapped_charger_proximity"])
        + output["terminal_evidence_score"] * float(weights["terminal_evidence"])
        + output["energy_manageability_score"] * float(weights["energy_manageability"])
    ).round(2)
    output["utility_capacity_verified"] = False
    output["charging_site_verified"] = False
    output["charging_evidence_confidence"] = np.where(output["nearest_mapped_charger_distance_km"].notna(), 38.0, 30.0)
    output["charging_source_ids"] = config["source_id"] + "|route2zero_climate_scenario_v1"
    output["charging_claim_status"] = "PROXY"
    output["charging_method_version"] = config["version"]
    output["charging_limitation"] = config["warning"]
    output.to_csv(PROCESSED_DIR / "charging_readiness.csv", index=False)
    print(f"[PASS] charging evidence: {len(substations)} substations, {len(chargers)} charging stations; utility capacity verified=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
