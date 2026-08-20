"""Apply transparent text-fallback city tags and refresh city summaries."""

from __future__ import annotations

import sys

import geopandas as gpd
import pandas as pd

from adapters import MetroManilaCityBoundaryAdapter
from common import PROCESSED_DIR, ensure_output_dirs


CITY_ADAPTER = MetroManilaCityBoundaryAdapter()


def cities_for_route(description: object, route_name: object) -> list[str]:
    return CITY_ADAPTER.cities_for_route(description, route_name)


def main() -> int:
    ensure_output_dirs()
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    scores = pd.read_csv(score_path, dtype={"route_id": str})
    geodata = gpd.read_file(geo_path)
    rows = []
    for row in scores.itertuples(index=False):
        cities = cities_for_route(row.route_desc, row.route_long_name)
        rows.append({
            "route_id": row.route_id,
            "primary_city": cities[0],
            "cities_served": "|".join(cities),
            "city_count": len(cities),
            "city_tag_method": CITY_ADAPTER.method,
            "city_tag_confidence": "low_requires_boundary_validation",
            "boundary_source_id": CITY_ADAPTER.boundary_source_id,
        })
    route_cities = pd.DataFrame(rows)
    route_cities.to_csv(PROCESSED_DIR / "route_cities.csv", index=False)
    scores = scores.drop(columns=[column for column in route_cities.columns if column != "route_id" and column in scores.columns], errors="ignore").merge(route_cities, on="route_id", how="left")
    geodata = geodata.drop(columns=[column for column in route_cities.columns if column != "route_id" and column in geodata.columns], errors="ignore").merge(route_cities, on="route_id", how="left")
    scores.to_csv(score_path, index=False)
    geodata.to_file(geo_path, driver="GeoJSON")
    expanded = scores[["route_id", "route_long_name", "just_transition_score", "rank", "net_co2e_avoided_t_year_low", "net_co2e_avoided_t_year_high", "cities_served"]].copy()
    expanded["city"] = expanded["cities_served"].str.split("|")
    expanded = expanded.explode("city")
    summaries = []
    for city, group in expanded.groupby("city", dropna=False):
        ranked = group.sort_values(["just_transition_score", "route_id"], ascending=[False, True])
        summaries.append({
            "city": city,
            "route_count": int(group["route_id"].nunique()),
            "avg_just_transition_score": round(float(group["just_transition_score"].mean()), 2),
            "portfolio_climate_low_t_year_if_all": round(float(group["net_co2e_avoided_t_year_low"].sum()), 1),
            "portfolio_climate_high_t_year_if_all": round(float(group["net_co2e_avoided_t_year_high"].sum()), 1),
            "top_5_route_ids": "|".join(ranked.head(5)["route_id"]),
            "top_5_route_names": "|".join(ranked.head(5)["route_long_name"].fillna("Unnamed route")),
            "city_tag_method": CITY_ADAPTER.method,
        })
    pd.DataFrame(summaries).sort_values("route_count", ascending=False).to_csv(PROCESSED_DIR / "city_summary.csv", index=False)
    print(f"[PASS] city text fallback: {len(route_cities):,} routes; spatial boundary validation remains pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
