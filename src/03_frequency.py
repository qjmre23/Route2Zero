"""Task 4: calculate weekday frequency and service-level metrics."""

from __future__ import annotations

import sys

import pandas as pd

from common import PROCESSED_DIR, ensure_output_dirs, load_gtfs, merge_intervals, parse_gtfs_time


def main() -> int:
    ensure_output_dirs()
    frequencies = load_gtfs("frequencies.txt")
    trips = load_gtfs("trips.txt")
    routes = load_gtfs("routes.txt")
    calendar = load_gtfs("calendar.txt")

    calendar["monday_num"] = pd.to_numeric(calendar["monday"], errors="coerce").fillna(0)
    weekday_services = set(
        calendar.loc[
            calendar["monday_num"].eq(1)
            | calendar["service_id"].str.upper().isin({"WEEKDAYS", "DAILY"}),
            "service_id",
        ]
    )
    joined = (
        frequencies.merge(trips[["trip_id", "route_id", "service_id"]], on="trip_id", how="inner")
        .merge(routes[["route_id", "agency_id", "route_long_name"]], on="route_id", how="inner")
    )
    joined = joined[
        joined["service_id"].isin(weekday_services)
        & joined["agency_id"].eq("LTFRB")
        & joined["route_id"].str.contains("PUJ", na=False)
    ].copy()
    joined["headway_secs_num"] = pd.to_numeric(joined["headway_secs"], errors="coerce")
    joined["start_seconds"] = joined["start_time"].map(parse_gtfs_time)
    joined["end_seconds"] = joined["end_time"].map(parse_gtfs_time)

    rows: list[dict] = []
    for route_id, group in joined.groupby("route_id"):
        avg_headway_min = group["headway_secs_num"].mean() / 60.0
        window_seconds = merge_intervals(zip(group["start_seconds"], group["end_seconds"], strict=False))
        window_hours = window_seconds / 3600.0 if pd.notna(window_seconds) else float("nan")
        trips_per_day = (
            window_hours * 60.0 / avg_headway_min
            if pd.notna(window_hours) and pd.notna(avg_headway_min) and avg_headway_min > 0
            else float("nan")
        )
        rows.append(
            {
                "route_id": route_id,
                "avg_headway_min": round(float(avg_headway_min), 3),
                "daily_service_window_hrs": round(float(window_hours), 3),
                "trips_per_day_estimate": round(float(trips_per_day), 3),
                "weekday_frequency_rows": int(len(group)),
                "frequency_source": "gtfs_frequencies_typical_weekday",
            }
        )

    jeepney_routes = routes[
        routes["agency_id"].eq("LTFRB") & routes["route_id"].str.contains("PUJ", na=False)
    ][["route_id", "route_long_name"]]
    output = jeepney_routes.merge(pd.DataFrame(rows), on="route_id", how="left")
    output.to_csv(PROCESSED_DIR / "route_frequency.csv", index=False)
    print(f"[PASS] weekday frequency metrics available: {output['avg_headway_min'].notna().sum():,}/{len(output):,}")
    print(f"[PASS] wrote {PROCESSED_DIR / 'route_frequency.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

