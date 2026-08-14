from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def test_expected_route_universe_and_geometry_sources() -> None:
    routes = gpd.read_file(PROCESSED / "jeepney_routes.geojson")
    assert len(routes) == 1522
    assert routes["route_id"].is_unique
    assert set(routes["geometry_source"]) == {"shape", "stop_sequence_approx"}
    assert (routes["geometry_source"] == "shape").sum() == 2


def test_scores_are_bounded_and_ai_never_ranks() -> None:
    scores = pd.read_csv(PROCESSED / "route2zero_scores.csv")
    for column in [
        "emissions_potential_score", "equity_score", "grid_feasibility_score",
        "operator_readiness_score", "just_transition_score",
    ]:
        values = scores[column].dropna()
        assert values.between(0, 100).all(), column
    assert not scores["ranking_ai_influence"].astype(bool).any()
    assert scores["just_transition_score"].notna().sum() == 1521


def test_proxy_and_placeholder_labels_are_explicit() -> None:
    scores = pd.read_csv(PROCESSED / "route2zero_scores.csv")
    assert scores["emissions_confidence"].str.contains("proxy").all()
    assert scores["equity_source"].str.contains("proxy").all()
    assert scores["grid_confidence"].str.contains("proxy").all()
    assert scores["operator_readiness_placeholder"].astype(bool).all()


def test_explanation_cache_is_downstream_only() -> None:
    payload = json.loads((PROCESSED / "route_explanations.json").read_text(encoding="utf-8"))
    assert len(payload) == 1521
    assert all(entry["ranking_ai_influence"] is False for entry in payload.values())
    assert any(entry["source"] == "mantle_bedrock_api" for entry in payload.values())


def test_secret_is_not_committed_to_example_or_source() -> None:
    key_prefix = "ABSKQmVkcm9ja0FQSUtleS"
    paths = [ROOT / ".env.example", *list((ROOT / "src").glob("*.py")), ROOT / "app" / "dashboard.py"]
    assert all(key_prefix not in path.read_text(encoding="utf-8") for path in paths)
