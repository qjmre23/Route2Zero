"""Apply transparent text-fallback city tags and refresh city summaries."""

from __future__ import annotations

import re
import sys

import geopandas as gpd
import pandas as pd

from common import PROCESSED_DIR, ensure_output_dirs


CITY_ALIASES = {
    "Quezon City": ["Quezon City"], "Caloocan": ["Caloocan City", "Caloocan"],
    "Las Pinas": ["Las Piñas City", "Las Pinas City", "Las Piñas", "Las Pinas"],
    "Makati": ["Makati City", "Makati"], "Malabon": ["Malabon City", "Malabon"],
    "Mandaluyong": ["Mandaluyong City", "Mandaluyong"], "Marikina": ["Marikina City", "Marikina"],
    "Muntinlupa": ["Muntinlupa City", "Muntinlupa"], "Navotas": ["Navotas City", "Navotas"],
    "Paranaque": ["Parañaque City", "Paranaque City", "Parañaque", "Paranaque"],
    "Pasay": ["Pasay City", "Pasay"], "Pasig": ["Pasig City", "Pasig"],
    "San Juan": ["San Juan City", "San Juan"], "Taguig": ["Taguig City", "Taguig"],
    "Valenzuela": ["Valenzuela City", "Valenzuela"], "Pateros": ["Pateros"],
    "Antipolo": ["Antipolo City", "Antipolo"], "Bacoor": ["Bacoor City", "Bacoor"],
    "Dasmarinas": ["Dasmariñas City", "Dasmarinas City", "Dasmariñas", "Dasmarinas"],
    "San Jose del Monte": ["San Jose del Monte City", "San Jose del Monte"],
    "Binan": ["Biñan City", "Binan City", "Biñan", "Binan"], "Carmona": ["Carmona City", "Carmona"],
    "General Mariano Alvarez": ["General Mariano Alvarez", "GMA, Cavite"],
}


def cities_for_route(description: object, route_name: object) -> list[str]:
    text = f"{description or ''} | {route_name or ''}"
    hits: list[tuple[int, str]] = []
    cleaned = text
    for city, aliases in CITY_ALIASES.items():
        positions = [cleaned.lower().find(alias.lower()) for alias in aliases]
        positions = [position for position in positions if position >= 0]
        if positions:
            hits.append((min(positions), city))
        for alias in aliases:
            cleaned = re.sub(re.escape(alias) + r"\s*,?\s*Manila", alias, cleaned, flags=re.I)
    positions = [match.start() for match in re.finditer(r"(?<!Metro )\bManila\b", cleaned, flags=re.I)]
    if positions:
        hits.append((min(positions), "Manila"))
    ordered: list[str] = []
    for _, city in sorted(hits):
        if city not in ordered:
            ordered.append(city)
    return ordered or ["Unspecified"]


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
            "city_tag_method": "text_fallback",
            "city_tag_confidence": "low_requires_boundary_validation",
            "boundary_source_id": "",
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
            "city_tag_method": "text_fallback",
        })
    pd.DataFrame(summaries).sort_values("route_count", ascending=False).to_csv(PROCESSED_DIR / "city_summary.csv", index=False)
    print(f"[PASS] city text fallback: {len(route_cities):,} routes; spatial boundary validation remains pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())
