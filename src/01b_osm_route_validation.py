"""Build reviewed current-route evidence from a dated OpenStreetMap snapshot."""

from __future__ import annotations

import json
import sys
from datetime import date

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString

from common import CONFIG_DIR, PROCESSED_DIR, ROOT, ensure_output_dirs, load_gtfs, read_json


def member_way_geometry(relation: dict) -> MultiLineString:
    lines = []
    for member in relation.get("members", []):
        if member.get("type") != "way" or not member.get("geometry"):
            continue
        coords = [(float(point["lon"]), float(point["lat"])) for point in member["geometry"]]
        if len(coords) >= 2:
            lines.append(LineString(coords))
    if not lines:
        raise ValueError(f"OSM relation {relation.get('id')} has no member-way geometry")
    return MultiLineString(lines)


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "osm_route_matching.json")
    snapshot_path = ROOT / "data" / "raw" / "osm_routes" / "metro_manila_share_taxi_2026-08-24.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    relations = {int(item["id"]): item for item in snapshot.get("elements", []) if item.get("type") == "relation"}
    routes = load_gtfs("routes.txt")[['route_id', 'route_long_name']].drop_duplicates("route_id").set_index("route_id")
    cutoff = date.fromisoformat(config["minimum_relation_edit_date"])

    records = []
    geometry_records = []
    seen_routes: set[str] = set()
    seen_relations: set[int] = set()
    for match in config["matches"]:
        route_id = str(match["route_id"])
        relation_id = int(match["osm_relation_id"])
        if route_id in seen_routes or relation_id in seen_relations:
            raise ValueError("OSM route-match config must be one-to-one")
        if route_id not in routes.index or relation_id not in relations:
            raise ValueError(f"Unresolved route match: {route_id} -> {relation_id}")
        relation = relations[relation_id]
        tags = relation.get("tags", {})
        if tags.get("route") != "bus" or tags.get("bus") != "share_taxi":
            raise ValueError(f"Relation {relation_id} is not tagged route=bus + bus=share_taxi")
        observed_date = str(relation.get("timestamp", ""))[:10]
        if date.fromisoformat(observed_date) < cutoff:
            raise ValueError(f"Relation {relation_id} is older than the configured recency threshold")
        relation_name = tags.get("name") or " - ".join(filter(None, [tags.get("from"), tags.get("to")]))
        source_reference = f"https://www.openstreetmap.org/relation/{relation_id}"
        route_name = str(routes.loc[route_id, "route_long_name"])
        geometry = member_way_geometry(relation)
        records.append({
            "route_id": route_id,
            "route_long_name": route_name,
            "validation_status": config["validation_status"],
            "active_status": config["active_status"],
            "validation_date": observed_date,
            "validator": "Route2Zero reviewed OSM desk match",
            "source_type": "osm_route_relation",
            "source_reference": source_reference,
            "notes": "Dated external route record and member-way geometry; OSM recency does not prove active service or franchise authority.",
            "observed_origin": tags.get("from", ""),
            "observed_destination": tags.get("to", ""),
            "observed_headway_min": None,
            "observed_service_window_hrs": None,
            "geometry_verified": False,
            "operator_name_if_verified": "",
            "evidence_quality": "osm_desk_observed",
            "osm_relation_id": relation_id,
            "osm_relation_name": relation_name,
            "osm_relation_timestamp": relation.get("timestamp", ""),
            "osm_operator_reference": tags.get("operator", ""),
            "osm_network": tags.get("network", ""),
            "match_basis": match["match_basis"],
            "route_geometry_claim_status": config["geometry_claim_status"],
            "official_plan_status": "MISSING",
            "official_plan_source_reference": "ltfrb_lptrp_index_2026_08_24",
        })
        geometry_records.append({
            "route_id": route_id,
            "osm_relation_id": relation_id,
            "osm_relation_name": relation_name,
            "osm_relation_timestamp": relation.get("timestamp", ""),
            "geometry_source": "osm_relation",
            "geometry": geometry,
        })
        seen_routes.add(route_id)
        seen_relations.add(relation_id)

    validation = pd.DataFrame(records).sort_values("route_id").reset_index(drop=True)
    validation.to_csv(PROCESSED_DIR / "osm_route_validation.csv", index=False)
    geodata = gpd.GeoDataFrame(geometry_records, geometry="geometry", crs="EPSG:4326")
    geodata.to_file(PROCESSED_DIR / "osm_route_geometry.geojson", driver="GeoJSON")
    print(f"[PASS] reviewed OSM route matches: {len(validation)} current records with member-way geometry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
