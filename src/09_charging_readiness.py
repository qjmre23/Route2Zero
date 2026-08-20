"""Build route charging readiness from optional mapped and validated evidence."""

from __future__ import annotations

import math
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree

from adapters import MetroManilaChargingAdapter
from common import CONFIG_DIR, PROCESSED_DIR, ROOT, ensure_output_dirs, minmax_score, read_json


EARTH_RADIUS_KM = 6371.0088


def as_boolean(values: pd.Series) -> pd.Series:
    return values.fillna(False).astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


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


def nearest_for_routes(
    routes: gpd.GeoDataFrame,
    infrastructure: np.ndarray,
    ids: list[str],
) -> tuple[list[float], list[str]]:
    if len(infrastructure) == 0:
        return [math.nan] * len(routes), [""] * len(routes)
    tree = BallTree(np.radians(infrastructure), metric="haversine")
    distances: list[float] = []
    nearest_ids: list[str] = []
    for geometry in routes.geometry:
        points = np.asarray([
            (geometry.coords[0][1], geometry.coords[0][0]),
            (geometry.coords[-1][1], geometry.coords[-1][0]),
        ])
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


def aggregate_site_evidence(
    route_ids: pd.Series,
    evidence: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Aggregate site rows without converting an empty ledger into evidence."""
    base = pd.DataFrame({"route_id": route_ids.astype(str)}).drop_duplicates()
    defaults = {
        "candidate_terminal_count": 0,
        "site_control_verified": False,
        "utility_capacity_verified": False,
        "charging_site_verified": False,
        "verified_available_capacity_kw": np.nan,
        "terminal_evidence_score": 0.0,
        "site_evidence_reference_count": 0,
    }
    for column, value in defaults.items():
        base[column] = value
    if evidence.empty:
        return base

    unknown = sorted(set(evidence["route_id"].dropna().astype(str)) - set(base["route_id"]))
    if unknown:
        raise ValueError(f"Charging evidence references unknown route IDs: {unknown[:5]}")
    frame = evidence.copy()
    frame["route_id"] = frame["route_id"].astype(str)
    frame["site_control_bool"] = as_boolean(frame["site_control_verified"])
    frame["utility_capacity_bool"] = as_boolean(frame["utility_capacity_verified"])
    frame["site_verified_bool"] = frame["site_control_bool"] & frame["utility_capacity_bool"]
    frame["available_capacity_numeric"] = pd.to_numeric(frame["available_capacity_kw"], errors="coerce")
    if frame["available_capacity_numeric"].lt(0).any():
        raise ValueError("Charging evidence available_capacity_kw must be non-negative")
    score_config = config["terminal_evidence_scores"]
    frame["site_row_score"] = float(score_config["site_recorded"])
    frame.loc[frame["site_control_bool"], "site_row_score"] = float(score_config["site_control_verified"])
    frame.loc[frame["site_verified_bool"], "site_row_score"] = float(score_config["site_and_utility_verified"])
    frame["verified_capacity"] = frame["available_capacity_numeric"].where(frame["utility_capacity_bool"])
    frame["reference_present"] = frame["source_reference"].fillna("").astype(str).str.strip().ne("")

    grouped = frame.groupby("route_id", sort=False).agg(
        candidate_terminal_count=("route_id", "size"),
        site_control_verified=("site_control_bool", "any"),
        utility_capacity_verified=("utility_capacity_bool", "any"),
        charging_site_verified=("site_verified_bool", "any"),
        verified_available_capacity_kw=("verified_capacity", "sum"),
        terminal_evidence_score=("site_row_score", "max"),
        site_evidence_reference_count=("reference_present", "sum"),
    ).reset_index()
    has_verified_capacity = frame.groupby("route_id")["verified_capacity"].apply(lambda values: values.notna().any())
    grouped.loc[
        grouped["route_id"].isin(has_verified_capacity[~has_verified_capacity].index),
        "verified_available_capacity_kw",
    ] = np.nan
    result = base.drop(columns=list(defaults)).merge(grouped, on="route_id", how="left")
    for column in ("candidate_terminal_count", "terminal_evidence_score", "site_evidence_reference_count"):
        result[column] = pd.to_numeric(result[column], errors="coerce").fillna(0)
    for column in ("site_control_verified", "utility_capacity_verified", "charging_site_verified"):
        result[column] = result[column].eq(True).fillna(False).astype(bool)  # noqa: E712
    return result


def weighted_readiness(output: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    components = {
        "mapped_substation_proximity": output["mapped_substation_proximity_score"],
        "mapped_charger_proximity": output["mapped_charger_proximity_score"],
        "terminal_evidence": output["terminal_evidence_score"],
        "energy_manageability": output["energy_manageability_score"],
    }
    numerator = pd.Series(0.0, index=output.index)
    denominator = pd.Series(0.0, index=output.index)
    for key, values in components.items():
        available = values.notna()
        weight = float(weights[key])
        numerator += values.fillna(0.0) * weight
        denominator += available.astype(float) * weight
    return numerator.div(denominator.replace(0, np.nan))


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "charging_config.json")
    adapter = MetroManilaChargingAdapter(ROOT)
    payload = adapter.load_snapshot()
    osm_available = payload is not None
    substations, substation_ids = osm_points(payload or {}, "power", "substation")
    chargers, charger_ids = osm_points(payload or {}, "amenity", "charging_station")
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson").sort_values("route_id").reset_index(drop=True)
    climate = pd.read_csv(PROCESSED_DIR / "climate_impact.csv", dtype={"route_id": str})
    site = aggregate_site_evidence(routes["route_id"], adapter.load_site_evidence(), config)

    if osm_available:
        sub_distance, sub_ids = nearest_for_routes(routes, substations, substation_ids)
        charger_distance, charger_nearest_ids = nearest_for_routes(routes, chargers, charger_ids)
    else:
        sub_distance = charger_distance = [math.nan] * len(routes)
        sub_ids = charger_nearest_ids = [""] * len(routes)

    output = routes[["route_id"]].copy()
    output["nearest_substation_distance_km"] = np.round(sub_distance, 3)
    output["nearest_substation_osm_id"] = sub_ids
    output["nearest_mapped_charger_distance_km"] = np.round(charger_distance, 3)
    output["nearest_charger_osm_id"] = charger_nearest_ids
    output = output.merge(
        climate[["route_id", "electricity_kwh_day_low", "electricity_kwh_day_base", "electricity_kwh_day_high"]],
        on="route_id", how="left",
    ).merge(site, on="route_id", how="left")
    if osm_available:
        output["mapped_substation_proximity_score"] = output["nearest_substation_distance_km"].map(
            lambda value: proximity_score(value, config["substation_distance_thresholds_km"])
        )
        output["mapped_charger_proximity_score"] = output["nearest_mapped_charger_distance_km"].map(
            lambda value: proximity_score(value, config["charger_distance_thresholds_km"])
        )
    else:
        output["mapped_substation_proximity_score"] = np.nan
        output["mapped_charger_proximity_score"] = np.nan
    output["energy_manageability_score"] = 100.0 - minmax_score(output["electricity_kwh_day_base"])
    output["charging_readiness_score"] = weighted_readiness(output, config["component_weights"]).round(2)
    has_site_evidence = output["candidate_terminal_count"].gt(0)
    if not osm_available:
        output.loc[~has_site_evidence, "charging_readiness_score"] = np.nan

    confidence = config["confidence_scores"]
    output["charging_evidence_confidence"] = float(confidence["missing"])
    if osm_available:
        output["charging_evidence_confidence"] = np.where(
            output["nearest_mapped_charger_distance_km"].notna(),
            float(confidence["mapped_charger"]), float(confidence["mapped_infrastructure"]),
        )
    output.loc[has_site_evidence, "charging_evidence_confidence"] = float(confidence["site_recorded"])
    output.loc[output["site_control_verified"].astype(bool), "charging_evidence_confidence"] = float(confidence["site_control_verified"])
    output.loc[output["charging_site_verified"].astype(bool), "charging_evidence_confidence"] = float(confidence["site_and_utility_verified"])
    output["charging_claim_status"] = np.select(
        [
            output["charging_site_verified"].astype(bool),
            has_site_evidence,
            pd.Series(osm_available, index=output.index),
        ],
        ["VERIFIED", "OBSERVED", "PROXY"],
        default="MISSING",
    )
    output["charging_source_ids"] = [
        "|".join(
            [
                *([config["source_id"]] if osm_available else []),
                *([config["site_evidence_source_id"]] if bool(has_site_evidence.iloc[index]) else []),
                "route2zero_climate_scenario_v1",
            ]
        ) if (osm_available or bool(has_site_evidence.iloc[index])) else ""
        for index in output.index
    ]
    output["charging_method_version"] = config["version"]
    output["charging_optional_osm_available"] = osm_available
    output["charging_limitation"] = config["warning"]
    output.to_csv(PROCESSED_DIR / "charging_readiness.csv", index=False)
    print(
        f"[PASS] charging evidence: OSM={'available' if osm_available else 'MISSING'}, "
        f"{len(substations)} substations, {len(chargers)} charging stations; "
        f"site records={int(site['candidate_terminal_count'].sum())}, verified sites={int(site['charging_site_verified'].sum())}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
