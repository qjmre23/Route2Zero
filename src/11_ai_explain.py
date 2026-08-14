"""Task 14: cache optional AI narratives downstream of deterministic ranking."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

import pandas as pd

from bedrock_client import deterministic_route_rationale, generate_explanation_with_status
from common import PROCESSED_DIR, ensure_output_dirs, write_json


def prompt_for(row: object, city: str) -> str:
    return f"""You are writing a one-sentence, plain-English rationale for a city transport planner.
Route: {row.route_long_name} ({city})
Scores (0-100): emissions potential {row.emissions_potential_score:.1f}, equity density proxy {row.equity_score:.1f}, grid feasibility {row.grid_feasibility_score:.1f}, operator readiness {row.operator_readiness_score:.1f}. Composite Just Transition Score: {row.just_transition_score:.1f}.
Length: {row.length_km:.1f} km. Estimated trips/day: {row.trips_per_day_estimate:.1f}.
Write ONE sentence explaining why this route ranks where it does. State only what the numbers support. Do not call proxies measured emissions, informal-settlement boundaries, local grid capacity, or verified financing readiness."""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-api", action="store_true", help="Call the configured API for selected routes")
    parser.add_argument("--limit", type=int, default=20, help="Maximum API calls, ordered by rank")
    parser.add_argument("--refresh", action="store_true", help="Replace existing API cache entries")
    args = parser.parse_args()
    ensure_output_dirs()
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    scores = scores.dropna(subset=["just_transition_score"]).sort_values("rank")
    cities = pd.read_csv(PROCESSED_DIR / "route_cities.csv", dtype={"route_id": str})
    scores = scores.merge(cities[["route_id", "primary_city"]], on="route_id", how="left")
    output_path = PROCESSED_DIR / "route_explanations.json"
    cache = json.loads(output_path.read_text(encoding="utf-8")) if output_path.exists() else {}
    api_candidates = set(scores.head(max(args.limit, 0))["route_id"]) if args.use_api else set()

    api_count = 0
    for row in scores.itertuples(index=False):
        fallback = deterministic_route_rationale(row)
        existing = cache.get(row.route_id, {})
        should_call = row.route_id in api_candidates and (args.refresh or existing.get("source") != "mantle_bedrock_api")
        if should_call:
            text, source = generate_explanation_with_status(
                prompt_for(row, row.primary_city or "Metro Manila"), max_tokens=120, fallback=fallback
            )
            api_count += int(source == "mantle_bedrock_api")
        elif existing.get("source") == "mantle_bedrock_api":
            text, source = existing["text"], existing["source"]
        else:
            text, source = fallback, "deterministic_fallback"
        cache[row.route_id] = {
            "text": text,
            "source": source,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ranking_ai_influence": False,
        }
    write_json(output_path, cache)
    print(f"[PASS] cached explanations: {len(cache):,}")
    print(f"[INFO] API-backed explanations this run: {api_count:,}")
    print("[PASS] ranking_ai_influence=false for every route")
    return 0


if __name__ == "__main__":
    sys.exit(main())

