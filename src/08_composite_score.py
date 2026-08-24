"""Task 9: merge dimension scores and rank routes deterministically."""

from __future__ import annotations

import sys

import geopandas as gpd
import pandas as pd

from common import PROCESSED_DIR, ensure_output_dirs


DEFAULT_WEIGHTS = {
    "emissions_potential_score": 0.4,
    "equity_score": 0.3,
    "grid_feasibility_score": 0.15,
    "operator_readiness_score": 0.15,
}


def main() -> int:
    ensure_output_dirs()
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson")
    frequency = pd.read_csv(PROCESSED_DIR / "route_frequency.csv", dtype={"route_id": str})
    emissions = pd.read_csv(PROCESSED_DIR / "emissions_score.csv", dtype={"route_id": str})
    equity = pd.read_csv(PROCESSED_DIR / "equity_score.csv", dtype={"route_id": str})
    grid = pd.read_csv(PROCESSED_DIR / "grid_feasibility.csv", dtype={"route_id": str})
    operator = pd.read_csv(PROCESSED_DIR / "operator_readiness.csv", dtype={"route_id": str})

    output = routes.merge(
        frequency.drop(columns=["route_long_name"], errors="ignore"), on="route_id", how="left"
    )
    for frame in (emissions, equity, grid, operator):
        new_columns = ["route_id"] + [
            column for column in frame.columns if column != "route_id" and column not in output.columns
        ]
        output = output.merge(frame[new_columns], on="route_id", how="left")

    required = list(DEFAULT_WEIGHTS)
    output["score_complete"] = output[required].notna().all(axis=1)
    output["equity_verified"] = output["equity_score"].notna()
    output["just_transition_score"] = float("nan")
    complete = output["score_complete"]
    output.loc[complete, "just_transition_score"] = sum(
        output.loc[complete, column] * weight for column, weight in DEFAULT_WEIGHTS.items()
    )
    output["just_transition_score"] = output["just_transition_score"].round(2)
    output["rank"] = output["just_transition_score"].rank(method="first", ascending=False).astype("Int64")
    output["ranking_method"] = "deterministic_weighted_sum"
    output["ranking_ai_influence"] = False
    output["default_weights"] = "emissions=0.40|equity=0.30|grid=0.15|operator=0.15"
    output["overall_confidence"] = output.apply(
        lambda row: "incomplete_missing_metric"
        if not row["score_complete"]
        else "proxy_mix_with_operator_placeholder",
        axis=1,
    )
    output = output.sort_values(["rank", "route_id"], na_position="last").reset_index(drop=True)
    output.drop(columns="geometry").to_csv(PROCESSED_DIR / "route2zero_scores.csv", index=False)
    output.to_file(PROCESSED_DIR / "route2zero_scores.geojson", driver="GeoJSON")
    print(f"[PASS] complete composite scores: {int(output['score_complete'].sum()):,}/{len(output):,}")
    print(f"[PASS] wrote {PROCESSED_DIR / 'route2zero_scores.csv'}")
    print(f"[PASS] wrote {PROCESSED_DIR / 'route2zero_scores.geojson'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
