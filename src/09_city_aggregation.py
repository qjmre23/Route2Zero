"""Task 10: tag routes by city names in GTFS descriptions and aggregate."""

from __future__ import annotations

import re
import sys

import pandas as pd

from common import PROCESSED_DIR, ensure_output_dirs


CITY_ALIASES = {
    "Quezon City": ["Quezon City"],
    "Caloocan": ["Caloocan City", "Caloocan"],
    "Las Piñas": ["Las Piñas City", "Las Pinas City", "Las Piñas", "Las Pinas"],
    "Makati": ["Makati City", "Makati"],
    "Malabon": ["Malabon City", "Malabon"],
    "Mandaluyong": ["Mandaluyong City", "Mandaluyong"],
    "Marikina": ["Marikina City", "Marikina"],
    "Muntinlupa": ["Muntinlupa City", "Muntinlupa"],
    "Navotas": ["Navotas City", "Navotas"],
    "Parañaque": ["Parañaque City", "Paranaque City", "Parañaque", "Paranaque"],
    "Pasay": ["Pasay City", "Pasay"],
    "Pasig": ["Pasig City", "Pasig"],
    "San Juan": ["San Juan City", "San Juan"],
    "Taguig": ["Taguig City", "Taguig"],
    "Valenzuela": ["Valenzuela City", "Valenzuela"],
    "Pateros": ["Pateros"],
    "Antipolo": ["Antipolo City", "Antipolo"],
    "Bacoor": ["Bacoor City", "Bacoor"],
    "Dasmariñas": ["Dasmariñas City", "Dasmarinas City", "Dasmariñas", "Dasmarinas"],
    "San Jose del Monte": ["San Jose del Monte City", "San Jose del Monte"],
    "Biñan": ["Biñan City", "Binan City", "Biñan", "Binan"],
    "Binangonan": ["Binangonan"],
    "Carmona": ["Carmona City", "Carmona"],
    "General Mariano Alvarez": ["General Mariano Alvarez", "GMA, Cavite"],
}


def cities_for_route(description: object, route_name: object) -> list[str]:
    text = f"{description or ''} | {route_name or ''}"
    hits: list[tuple[int, str]] = []
    cleaned = text
    for city, aliases in CITY_ALIASES.items():
        positions = [
            match.start()
            for alias in aliases
            for match in re.finditer(rf"(?<!\w){re.escape(alias)}(?!\w)", cleaned, flags=re.I)
        ]
        if positions:
            hits.append((min(positions), city))
        for alias in aliases:
            cleaned = re.sub(
                rf"(?<!\w){re.escape(alias)}(?!\w)\s*,?\s*Manila\b",
                alias,
                cleaned,
                flags=re.I,
            )
    if re.search(r"(?<!Metro )\bManila\b", cleaned, flags=re.I):
        positions = [match.start() for match in re.finditer(r"(?<!Metro )\bManila\b", cleaned, flags=re.I)]
        hits.append((min(positions), "Manila"))
    ordered = []
    for _, city in sorted(hits):
        if city not in ordered:
            ordered.append(city)
    return ordered or ["Unspecified"]


def main() -> int:
    ensure_output_dirs()
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    route_rows: list[dict] = []
    for row in scores.itertuples(index=False):
        cities = cities_for_route(row.route_desc, row.route_long_name)
        route_rows.append(
            {
                "route_id": row.route_id,
                "primary_city": cities[0],
                "cities_served": "|".join(cities),
                "city_tag_source": "gtfs_route_desc_text",
            }
        )
    route_cities = pd.DataFrame(route_rows)
    route_cities.to_csv(PROCESSED_DIR / "route_cities.csv", index=False)

    expanded = scores[["route_id", "route_long_name", "just_transition_score", "rank"]].merge(
        route_cities, on="route_id", how="left"
    )
    expanded["city"] = expanded["cities_served"].str.split("|")
    expanded = expanded.explode("city")
    summary_rows: list[dict] = []
    for city, group in expanded.groupby("city", dropna=False):
        ranked = group.dropna(subset=["just_transition_score"]).sort_values(
            ["just_transition_score", "route_id"], ascending=[False, True]
        )
        summary_rows.append(
            {
                "city": city,
                "route_count": int(group["route_id"].nunique()),
                "avg_just_transition_score": round(float(group["just_transition_score"].mean()), 2),
                "top_5_route_ids": "|".join(ranked.head(5)["route_id"]),
                "top_5_route_names": "|".join(ranked.head(5)["route_long_name"].fillna("Unnamed route")),
            }
        )
    pd.DataFrame(summary_rows).sort_values("route_count", ascending=False).to_csv(
        PROCESSED_DIR / "city_summary.csv", index=False
    )
    print(f"[PASS] routes city-tagged: {len(route_cities):,}")
    print(f"[PASS] distinct city labels: {expanded['city'].nunique():,}")
    print(f"[PASS] wrote {PROCESSED_DIR / 'city_summary.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
