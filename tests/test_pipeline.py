from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
CONFIG = ROOT / "config"
MODELS = ROOT / "models"
NETLIFY_SITE = ROOT / "netlify-site"

EXPECTED_ROUTE_COUNT = 1_522
EXPECTED_SIMULATIONS = 5_000
EXPECTED_SENSITIVITY_SEED = 20_260_820
BUILD_ID_PATTERN = re.compile(r"^r2z-[0-9a-f]{12}$")
SCENARIO_ID_PATTERN = re.compile(r"^scn-[0-9a-f]{10}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@pytest.fixture(scope="session")
def scores() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "route2zero_scores.csv", dtype={"route_id": str})


@pytest.fixture(scope="session")
def features() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "route_features.csv", dtype={"route_id": str})


def test_manifests_are_complete_and_build_ids_match(scores: pd.DataFrame) -> None:
    source_manifest = load_json(PROCESSED / "source_manifest.json")
    build_manifest = load_json(PROCESSED / "build_manifest.json")

    assert source_manifest["registry_version"].startswith("2.")
    assert source_manifest["source_count"] == len(source_manifest["sources"])
    source_ids = [source["source_id"] for source in source_manifest["sources"]]
    assert source_ids and len(source_ids) == len(set(source_ids))
    assert all(SHA256_PATTERN.fullmatch(source["checksum_sha256"]) for source in source_manifest["sources"])

    build_id = build_manifest["build_id"]
    assert BUILD_ID_PATTERN.fullmatch(build_id)
    assert build_manifest["pipeline_version"].startswith("2.")
    assert build_manifest["model_versions"]["service_intensity"]
    assert build_manifest["model_versions"]["corridor_typology"]
    assert set(scores["build_id"].dropna().unique()) == {build_id}
    scenario_ids = set(scores["scenario_id"].dropna().unique())
    assert len(scenario_ids) == 1
    assert SCENARIO_ID_PATTERN.fullmatch(next(iter(scenario_ids)))

    for filename, expected in build_manifest["config_checksums"].items():
        assert SHA256_PATTERN.fullmatch(expected)
        assert sha256(CONFIG / filename) == expected

    required_outputs = {
        "route_features.csv",
        "ml_service_intensity.csv",
        "climate_impact.csv",
        "evidence_confidence.csv",
        "sensitivity.csv",
        "portfolio_scenarios.json",
        "route_planner_cache.json",
        "route2zero_scores.csv",
        "route2zero_scores.geojson",
    }
    output_checksums = build_manifest["output_checksums"]
    assert required_outputs <= output_checksums.keys()
    for filename, expected in output_checksums.items():
        output_path = PROCESSED / filename
        assert output_path.is_file(), filename
        assert SHA256_PATTERN.fullmatch(expected)
        assert sha256(output_path) == expected, filename


def test_route_universe_is_complete_unique_and_governed(
    scores: pd.DataFrame, features: pd.DataFrame
) -> None:
    assert len(scores) == EXPECTED_ROUTE_COUNT
    assert scores["route_id"].nunique() == EXPECTED_ROUTE_COUNT
    assert not scores["route_id"].isna().any()
    assert len(features) == EXPECTED_ROUTE_COUNT
    assert features["route_id"].is_unique
    assert set(features["route_id"]) == set(scores["route_id"])
    assert not scores["llm_ranking_influence"].astype(bool).any()
    assert scores["human_policy_control"].astype(bool).all()
    assert scores["policy_weights_human_controlled"].astype(bool).all()


def test_service_model_feature_list_has_no_target_leakage() -> None:
    config = load_json(CONFIG / "model_config.json")["service_intensity"]
    metadata = load_json(MODELS / "service_intensity_metadata.json")
    features = set(config["feature_columns"])
    forbidden = set(config["forbidden_leakage_columns"])
    known_post_target_fields = {
        config["target"],
        "trips_per_day_estimate",
        "avg_headway_min",
        "daily_service_window_hrs",
        "daily_vehicle_km_proxy",
        "emissions_potential_score",
        "climate_impact_score",
        "just_transition_score",
        "rank",
    }

    assert features
    assert features.isdisjoint(forbidden)
    assert features.isdisjoint(known_post_target_fields)
    assert set(metadata["features"]) == features
    assert forbidden <= set(metadata["excluded_leakage_features"])
    assert metadata["target"] == config["target"]


def test_service_model_beats_baseline_with_grouped_cross_validation() -> None:
    model_document = load_json(CONFIG / "model_config.json")
    model_config = model_document["service_intensity"]
    metrics = load_json(PROCESSED / "model_metrics.json")["service_intensity"]
    metadata = load_json(MODELS / "service_intensity_metadata.json")
    selected = metrics["selected_metrics"]

    assert selected["mae"] < selected["baseline_mae"]
    assert selected["rmse"] > 0
    assert selected["relative_mae_improvement"] >= model_config["minimum_relative_mae_improvement"]
    assert metrics["meaningful_vs_baseline"] is True
    assert selected["mae"] == min(candidate["mae"] for candidate in metrics["candidate_metrics"].values())
    assert metrics["training_rows"] == EXPECTED_ROUTE_COUNT - 1
    assert 1 < metrics["corridor_groups"] < metrics["training_rows"]
    expected_cv = f"GroupKFold({model_config['cv_folds']}) by normalized_corridor_id"
    assert metrics["cross_validation"] == expected_cv
    assert metadata["cross_validation"] == expected_cv
    assert metrics["random_seed"] == model_document["random_seed"]
    assert (MODELS / "service_intensity.joblib").is_file()


def test_climate_scenarios_preserve_semantics_and_units(scores: pd.DataFrame) -> None:
    climate = pd.read_csv(PROCESSED / "climate_impact.csv", dtype={"route_id": str})
    config = load_json(CONFIG / "climate_scenarios.json")
    assert len(climate) == EXPECTED_ROUTE_COUNT
    assert climate["route_id"].is_unique
    assert set(climate["route_id"]) == set(scores["route_id"])
    assert climate["impact_is_scenario_not_measurement"].astype(bool).all()
    assert set(climate["climate_claim_status"]) == {"SCENARIO"}

    operating_days = config["operating_days_per_year"]["value"]
    charger_efficiency = config["charger_efficiency"]["value"]
    for scenario in ("low", "base", "high"):
        assumptions = config["scenarios"][scenario]
        electrification_share = assumptions["electrification_share"]["value"]
        diesel_km_per_liter = assumptions["diesel_km_per_liter"]["value"]
        electric_kwh_per_km = assumptions["electric_kwh_per_km"]["value"]

        assert np.allclose(
            climate[f"electrified_vkt_{scenario}"],
            climate["daily_vkt"] * electrification_share,
            atol=0.002,
        )
        assert np.allclose(
            climate[f"diesel_liters_avoided_{scenario}"],
            climate[f"electrified_vkt_{scenario}"] / diesel_km_per_liter,
            atol=0.002,
        )
        assert np.allclose(
            climate[f"electricity_kwh_day_{scenario}"],
            climate[f"electrified_vkt_{scenario}"] * electric_kwh_per_km / charger_efficiency,
            atol=0.002,
        )
        assert np.allclose(
            climate[f"net_co2e_avoided_kg_day_{scenario}"],
            climate[f"baseline_co2e_kg_day_{scenario}"] - climate[f"grid_co2e_kg_day_{scenario}"],
            atol=0.002,
        )
        assert np.allclose(
            climate[f"net_co2e_avoided_t_year_{scenario}"],
            climate[f"net_co2e_avoided_kg_day_{scenario}"] * operating_days / 1_000,
            atol=0.002,
        )

    assert (
        climate["net_co2e_avoided_t_year_low"]
        <= climate["net_co2e_avoided_t_year_base"]
    ).all()
    assert (
        climate["net_co2e_avoided_t_year_base"]
        <= climate["net_co2e_avoided_t_year_high"]
    ).all()
    assert (climate["net_co2e_avoided_t_year_low"] < 0).any(), "negative impacts must not be clipped"


def test_evidence_scores_map_to_configured_grades(scores: pd.DataFrame) -> None:
    evidence = pd.read_csv(PROCESSED / "evidence_confidence.csv", dtype={"route_id": str})
    thresholds = load_json(CONFIG / "evidence_confidence_config.json")["grade_thresholds"]
    ordered_thresholds = sorted(thresholds.items(), key=lambda item: item[1], reverse=True)

    def expected_grade(value: float) -> str:
        return next(grade for grade, threshold in ordered_thresholds if value >= threshold)

    assert len(evidence) == EXPECTED_ROUTE_COUNT
    assert evidence["route_id"].is_unique
    assert evidence["overall_evidence_confidence"].between(0, 100).all()
    assert set(evidence["evidence_grade"]) <= set(thresholds)
    expected = evidence["overall_evidence_confidence"].map(expected_grade)
    assert expected.equals(evidence["evidence_grade"])

    placeholder_heavy = scores[
        scores["operator_readiness_placeholder"].astype(bool)
        & ~scores["utility_capacity_verified"].astype(bool)
        & scores["validation_status"].eq("historic_only")
    ]
    assert not placeholder_heavy.empty
    assert not placeholder_heavy["evidence_grade"].eq("A").any()


def test_sensitivity_contract_uses_fixed_seed_and_5000_runs(scores: pd.DataFrame) -> None:
    sensitivity = pd.read_csv(PROCESSED / "sensitivity.csv", dtype={"route_id": str})
    config = load_json(CONFIG / "sensitivity_config.json")
    assert config["simulations"] == EXPECTED_SIMULATIONS
    assert config["random_seed"] == EXPECTED_SENSITIVITY_SEED
    assert len(sensitivity) == EXPECTED_ROUTE_COUNT
    assert sensitivity["route_id"].is_unique
    assert set(sensitivity["route_id"]) == set(scores["route_id"])
    assert set(sensitivity["simulations"]) == {EXPECTED_SIMULATIONS}
    assert set(sensitivity["sensitivity_seed"]) == {EXPECTED_SENSITIVITY_SEED}
    assert set(sensitivity["sensitivity_mode"]) == {config["mode"]}

    for column in ("top_5_probability", "top_10_probability", "top_20_probability"):
        assert sensitivity[column].between(0, 1).all(), column
    assert (sensitivity["top_5_probability"] <= sensitivity["top_10_probability"]).all()
    assert (sensitivity["top_10_probability"] <= sensitivity["top_20_probability"]).all()
    assert sensitivity["rank_p10"].between(1, EXPECTED_ROUTE_COUNT).all()
    assert sensitivity["rank_p90"].between(1, EXPECTED_ROUTE_COUNT).all()
    assert (sensitivity["rank_p10"] <= sensitivity["median_rank"]).all()
    assert (sensitivity["median_rank"] <= sensitivity["rank_p90"]).all()
    assert sensitivity["rank_stability_score"].between(0, 100).all()


def test_phase1_optimizer_selects_eight_unique_corridors_and_changes_top8(
    scores: pd.DataFrame,
) -> None:
    payload = load_json(PROCESSED / "portfolio_scenarios.json")
    assert len(payload["scenarios"]) == 1
    scenario = payload["scenarios"][0]
    constraints = scenario["constraints"]
    selected = scenario["selected_route_ids"]
    naive = scenario["simple_top_n_route_ids"]

    assert scenario["status"] == "feasible"
    assert scenario["optimization_method"] == "deterministic_selection"
    assert constraints["max_corridors"] == 8
    assert constraints["maximum_route_directions_per_corridor"] == 1
    assert len(selected) == len(set(selected)) == 8
    assert len(naive) == len(set(naive)) == 8
    assert set(selected) != set(naive)
    assert set(scenario["added_by_constraints"]) == set(selected) - set(naive)
    assert set(scenario["removed_by_constraints"]) == set(naive) - set(selected)

    by_route = scores.set_index("route_id")
    assert set(selected) <= set(by_route.index)
    selected_corridors = by_route.loc[selected, "normalized_corridor_id"]
    assert selected_corridors.notna().all()
    assert selected_corridors.is_unique
    assert by_route.loc[selected, "phase1_selected"].astype(bool).all()


def test_planner_cache_is_route_and_scenario_aware(scores: pd.DataFrame) -> None:
    cache = load_json(PROCESSED / "route_planner_cache.json")
    portfolio = load_json(PROCESSED / "portfolio_scenarios.json")["scenarios"][0]
    score_scenario_ids = set(scores["scenario_id"].dropna().unique())
    assert len(score_scenario_ids) == 1
    scenario_id = next(iter(score_scenario_ids))

    assert set(cache) == set(scores["route_id"])
    for route_id, entry in cache.items():
        assert entry["scenario_id"] == scenario_id
        assert entry["portfolio_scenario_id"] == portfolio["scenario_id"]
        assert scenario_id in entry["answer"]
        assert route_id in entry["cited_route_ids"]
        assert entry["cited_fields"]
        assert entry["source"] in {"api", "deterministic_fallback"}
        assert entry["llm_ranking_influence"] is False
        assert isinstance(entry["evidence_points"], list)
        assert isinstance(entry["uncertainty_notes"], list)
        assert isinstance(entry["validation_actions"], list)


def test_netlify_build_smoke_publishes_route2zero_2_data() -> None:
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    assert npm, "npm is required for the Netlify build smoke test"

    temporary_parent = Path(os.environ.get("RUNNER_TEMP", ROOT / "tmp"))
    temporary_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="netlify-build-", dir=temporary_parent) as directory:
        temporary_root = Path(directory) / "route2zero"
        temporary_site = temporary_root / "netlify-site"
        shutil.copytree(
            NETLIFY_SITE,
            temporary_site,
            ignore=shutil.ignore_patterns("data", "config.js", "node_modules"),
        )
        shutil.copytree(PROCESSED, temporary_root / "data" / "processed")

        env = os.environ.copy()
        env["MAPBOX_TOKEN"] = "pk.test-ci-public-token"
        result = subprocess.run(
            [npm, "run", "build"],
            cwd=temporary_site,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr

        published_data = temporary_site / "public" / "data"
        required_public_files = {
            "route2zero_scores.csv",
            "route2zero_scores.geojson",
            "route_cities.csv",
            "city_summary.csv",
            "sensitivity.csv",
            "corridor_typology.csv",
            "validation_priorities.json",
            "portfolio_scenarios.json",
            "source_manifest.json",
            "build_manifest.json",
            "model_metrics.json",
            "route_planner_cache.json",
        }
        assert required_public_files <= {path.name for path in published_data.iterdir()}
        config_js = (temporary_site / "public" / "config.js").read_text(encoding="utf-8")
        assert "pk.test-ci-public-token" in config_js
        assert "ABSK_KEY" not in config_js
