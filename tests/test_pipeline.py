from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString


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
CLAIM_STATUSES = {
    "VERIFIED",
    "OBSERVED",
    "DERIVED",
    "ML_ESTIMATED",
    "PROXY",
    "SCENARIO",
    "NEUTRAL_PRIOR",
    "MISSING",
}
VALIDATION_STATUSES = {
    "historic_only",
    "desk_checked",
    "operator_confirmed",
    "lgu_confirmed",
    "field_checked",
    "conflicting_evidence",
}
ACTIVE_STATUSES = {"active", "inactive", "uncertain"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pipeline_module(filename: str, module_name: str):
    sys.path.insert(0, str(ROOT / "src"))
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "src" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    for source in source_manifest["sources"]:
        assert isinstance(source["required"], bool)
        assert source["availability_status"] in {"AVAILABLE", "MISSING_OPTIONAL"}
        if source["available"]:
            assert SHA256_PATTERN.fullmatch(source["checksum_sha256"])
        else:
            assert source["required"] is False
            assert source["checksum_sha256"] is None

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
        "sensitivity_modes.csv",
        "portfolio_scenarios.json",
        "route_planner_cache.json",
        "route2zero_scores.csv",
        "route2zero_scores.geojson",
        "pipeline_report.json",
        "flagship_route.json",
    }
    output_checksums = build_manifest["output_checksums"]
    assert required_outputs <= output_checksums.keys()
    for filename, expected in output_checksums.items():
        output_path = PROCESSED / filename
        assert output_path.is_file(), filename
        assert SHA256_PATTERN.fullmatch(expected)
        assert sha256(output_path) == expected, filename
    model_checksums = build_manifest["model_artifact_checksums"]
    assert set(model_checksums) == {
        "service_intensity.joblib",
        "service_intensity_metadata.json",
        "corridor_typology.joblib",
        "corridor_typology_metadata.json",
    }
    for filename, expected in model_checksums.items():
        assert SHA256_PATTERN.fullmatch(expected)
        assert sha256(MODELS / filename) == expected


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


def test_geometry_reliability_handles_verified_and_extreme_cases() -> None:
    module = load_pipeline_module("02b_geometry_reliability.py", "route2zero_geometry_reliability")

    invalid = module.score_geometry(
        pd.Series(
            {
                "geometry": LineString(),
                "geometry_source": "stop_sequence_approx",
                "length_km": 0,
                "stop_count": 0,
            }
        )
    )
    assert invalid["geometry_valid"] is False
    assert invalid["geometry_reliability_score"] == 0
    assert invalid["geometry_reliability_grade"] == "D"
    assert invalid["geometry_validation_required"] is True

    line = LineString([(121.0, 14.0), (121.01, 14.01)])
    source_credit = module.score_geometry(
        pd.Series(
            {
                "geometry": line,
                "geometry_source": "shape",
                "length_km": 1.6,
                "stop_count": 20,
            }
        ),
        field_verified=True,
    )
    assert source_credit["geometry_reliability_grade"] == "A"
    assert source_credit["geometry_claim_status"] == "VERIFIED"
    assert source_credit["geometry_validation_required"] is False

    extreme = module.score_geometry(
        pd.Series(
            {
                "geometry": line,
                "geometry_source": "stop_sequence_approx",
                "length_km": 20,
                "stop_count": 20,
            }
        )
    )
    assert "extreme detour ratio" in extreme["geometry_reliability_reasons"]
    assert extreme["geometry_reliability_score"] < source_credit["geometry_reliability_score"]


def test_claim_statuses_and_validation_ledger_follow_shared_contract(
    scores: pd.DataFrame,
) -> None:
    claim_columns = [column for column in scores.columns if column.endswith("claim_status")]
    assert claim_columns
    for column in claim_columns:
        assert not scores[column].isna().any(), column
        assert set(scores[column]) <= CLAIM_STATUSES, column

    ledger = pd.read_csv(ROOT / "data" / "validated" / "route_validation.csv", dtype=str)
    required_ledger_fields = {
        "route_id",
        "route_long_name",
        "validation_status",
        "active_status",
        "validation_date",
        "validator",
        "source_type",
        "source_reference",
        "notes",
        "observed_origin",
        "observed_destination",
        "observed_headway_min",
        "observed_service_window_hrs",
        "geometry_verified",
        "operator_name_if_verified",
        "evidence_quality",
    }
    assert required_ledger_fields <= set(ledger.columns)
    assert set(scores["validation_status"]) <= VALIDATION_STATUSES
    assert set(scores["active_status"]) <= ACTIVE_STATUSES

    stakeholder = pd.read_csv(
        ROOT / "data" / "validated" / "stakeholder_validation.csv", dtype=str
    )
    assert {
        "stakeholder_type",
        "organization",
        "date",
        "route_id",
        "workflow_component",
        "feedback_summary",
        "evidence_change",
        "permission_to_quote",
        "source_reference",
    } <= set(stakeholder.columns)


def test_external_numeric_assumptions_reference_registered_sources() -> None:
    registered = {
        source["source_id"]
        for source in load_json(CONFIG / "source_registry.json")["sources"]
    }
    climate = load_json(CONFIG / "climate_scenarios.json")

    sourced_parameters = [
        climate["operating_days_per_year"],
        climate["charger_efficiency"],
        climate["current_grid_kgco2e_per_kwh"],
    ]
    for scenario in climate["scenarios"].values():
        sourced_parameters.extend(scenario.values())
    assert sourced_parameters
    for parameter in sourced_parameters:
        assert isinstance(parameter["value"], (int, float))
        assert parameter["source_id"] in registered

    charging = load_json(CONFIG / "charging_config.json")
    operator = load_json(CONFIG / "operator_readiness_config.json")
    assert {charging["source_id"], charging["site_evidence_source_id"]} <= registered
    assert {
        operator["prior_source_id"], operator["evidence_source_id"], operator["scoring_source_id"]
    } <= registered


def test_source_ledgers_are_registered_and_schema_complete() -> None:
    registry = load_json(CONFIG / "source_registry.json")
    sources = {source["source_id"]: source for source in registry["sources"]}
    ledger_contracts = {
        "route_validation_ledger": {
            "path": "data/validated/route_validation.csv",
            "columns": {"route_id", "validation_status", "active_status", "source_reference"},
        },
        "charging_site_evidence_ledger": {
            "path": "data/validated/charging_site_evidence.csv",
            "columns": {
                "route_id", "site_name", "site_control_verified", "utility_capacity_verified",
                "available_capacity_kw", "source_reference", "verifier",
            },
        },
        "operator_evidence_ledger": {
            "path": "data/validated/operator_evidence.csv",
            "columns": {
                "route_id", "verified_fleet_size", "modernization_experience_score",
                "charging_site_access_score", "source_reference", "verifier",
            },
        },
        "stakeholder_validation_ledger": {
            "path": "data/validated/stakeholder_validation.csv",
            "columns": {"route_id", "stakeholder_type", "evidence_change", "permission_to_quote"},
        },
    }
    for source_id, contract in ledger_contracts.items():
        assert source_id in sources
        assert sources[source_id]["required"] is True
        assert sources[source_id]["local_path"] == contract["path"]
        frame = pd.read_csv(ROOT / contract["path"], dtype=str)
        assert contract["columns"] <= set(frame.columns)


def test_optional_city_adapters_return_explicit_absence(tmp_path: Path) -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from adapters import (
        CHARGING_EVIDENCE_COLUMNS,
        OPERATOR_EVIDENCE_COLUMNS,
        MetroManilaChargingAdapter,
        MetroManilaCityBoundaryAdapter,
        MetroManilaOperatorEvidenceAdapter,
        MetroManilaPopulationAdapter,
    )

    assert MetroManilaPopulationAdapter(tmp_path).available is False
    charging = MetroManilaChargingAdapter(tmp_path)
    assert charging.load_snapshot() is None
    assert list(charging.load_site_evidence().columns) == CHARGING_EVIDENCE_COLUMNS
    assert charging.load_site_evidence().empty
    operator = MetroManilaOperatorEvidenceAdapter(tmp_path).load_evidence()
    assert list(operator.columns) == OPERATOR_EVIDENCE_COLUMNS
    assert operator.empty
    city = MetroManilaCityBoundaryAdapter()
    assert city.method == "text_fallback"
    assert city.boundary_source_id == ""
    assert city.cities_for_route("Makati City to Pasig City", "Sample")[:2] == ["Makati", "Pasig"]
    equity_module = load_pipeline_module("05_equity_score.py", "route2zero_equity_score")
    missing_equity = equity_module.missing_equity_output(pd.Series(["R1", "R2"]), "test_missing")
    assert missing_equity["equity_score"].isna().all()
    assert set(missing_equity["equity_source"]) == {"MISSING"}
    assert set(missing_equity["equity_missing_reason"]) == {"test_missing"}


def test_charging_site_evidence_drives_terminal_and_verification_fields() -> None:
    module = load_pipeline_module("09_charging_readiness.py", "route2zero_charging_readiness")
    config = load_json(CONFIG / "charging_config.json")
    evidence = pd.DataFrame([
        {
            "route_id": "R1", "site_name": "Terminal A", "evidence_date": "2026-08-20",
            "site_lat": 14.5, "site_lon": 121.0, "site_control_verified": False,
            "utility_capacity_verified": False, "available_capacity_kw": np.nan,
            "source_reference": "field-note-a", "verifier": "validator", "notes": "candidate only",
        },
        {
            "route_id": "R1", "site_name": "Terminal B", "evidence_date": "2026-08-21",
            "site_lat": 14.6, "site_lon": 121.1, "site_control_verified": True,
            "utility_capacity_verified": True, "available_capacity_kw": 500,
            "source_reference": "utility-letter-b", "verifier": "validator", "notes": "verified",
        },
    ])
    output = module.aggregate_site_evidence(pd.Series(["R1", "R2"]), evidence, config).set_index("route_id")
    assert output.loc["R1", "candidate_terminal_count"] == 2
    assert bool(output.loc["R1", "site_control_verified"])
    assert bool(output.loc["R1", "utility_capacity_verified"])
    assert bool(output.loc["R1", "charging_site_verified"])
    assert output.loc["R1", "verified_available_capacity_kw"] == 500
    assert output.loc["R1", "terminal_evidence_score"] == config["terminal_evidence_scores"]["site_and_utility_verified"]
    assert output.loc["R2", "candidate_terminal_count"] == 0
    assert not bool(output.loc["R2", "charging_site_verified"])
    assert output.loc["R2", "terminal_evidence_score"] == 0
    assert pd.isna(output.loc["R2", "verified_available_capacity_kw"])


def test_operator_scoring_uses_all_eight_configured_components() -> None:
    module = load_pipeline_module("10_operator_readiness.py", "route2zero_operator_readiness")
    config = load_json(CONFIG / "operator_readiness_config.json")
    base = {
        "route_id": "R1", "operator_name": "Cooperative", "evidence_date": "2026-08-20",
        "verified_fleet_size": 25, "depot_control_score": 60, "financing_score": 65,
        "organizational_capacity_score": 70, "maintenance_capability_score": 75,
        "willingness_to_participate_score": 80, "modernization_experience_score": 0,
        "charging_site_access_score": 0, "source_reference": "consented-record",
        "verifier": "validator", "notes": "synthetic test",
    }
    low = module.score_operator_evidence(pd.DataFrame({"route_id": ["R1"]}), pd.DataFrame([base]), config)
    high_evidence = {**base, "modernization_experience_score": 100, "charging_site_access_score": 100}
    high = module.score_operator_evidence(pd.DataFrame({"route_id": ["R1"]}), pd.DataFrame([high_evidence]), config)
    assert low.loc[0, "operator_evidence_component_count"] == 8
    assert low.loc[0, "operator_evidence_completeness"] == 100
    assert not bool(low.loc[0, "operator_readiness_placeholder"])
    assert high.loc[0, "operator_observed_score"] > low.loc[0, "operator_observed_score"]
    assert set(low.loc[0, "operator_components_configured"].split("|")) == set(config["observed_component_weights"])
    assert "operator_evidence_ledger" in low.loc[0, "operator_source_ids"]


def test_pipeline_report_exposes_health_and_missingness(scores: pd.DataFrame) -> None:
    report = load_json(PROCESSED / "pipeline_report.json")
    manifest = load_json(PROCESSED / "build_manifest.json")
    assert report["build_id"] == manifest["build_id"]
    assert report["rows_processed"] == EXPECTED_ROUTE_COUNT
    assert report["status"] in {"PASS", "PASS_WITH_WARNINGS"}
    assert set(report["model_versions"]) == {"service_intensity", "corridor_typology"}
    assert report["source_dates"]
    assert report["claim_status_columns_checked"]
    assert report["active_validation_count"] == int(scores["active_status"].eq("active").sum())
    expected_missing = {
        column: int(scores[column].isna().sum())
        for column in report["critical_missing_values"]
    }
    assert report["critical_missing_values"] == expected_missing


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
    modes = pd.read_csv(PROCESSED / "sensitivity_modes.csv", dtype={"route_id": str})
    config = load_json(CONFIG / "sensitivity_config.json")
    assert config["simulations"] == EXPECTED_SIMULATIONS
    assert config["random_seed"] == EXPECTED_SENSITIVITY_SEED
    assert len(sensitivity) == EXPECTED_ROUTE_COUNT
    assert sensitivity["route_id"].is_unique
    assert set(sensitivity["route_id"]) == set(scores["route_id"])
    assert set(sensitivity["simulations"]) == {EXPECTED_SIMULATIONS}
    assert set(sensitivity["sensitivity_seed"]) == {EXPECTED_SENSITIVITY_SEED}
    assert set(sensitivity["sensitivity_mode"]) == {config["default_mode"]}
    assert len(modes) == EXPECTED_ROUTE_COUNT * len(config["modes"])
    assert set(modes["sensitivity_mode"]) == set(config["modes"])
    assert modes.groupby("sensitivity_mode")["route_id"].nunique().eq(EXPECTED_ROUTE_COUNT).all()

    for column in ("top_5_probability", "top_10_probability", "top_20_probability"):
        assert sensitivity[column].between(0, 1).all(), column
    assert (sensitivity["top_5_probability"] <= sensitivity["top_10_probability"]).all()
    assert (sensitivity["top_10_probability"] <= sensitivity["top_20_probability"]).all()
    assert sensitivity["rank_p10"].between(1, EXPECTED_ROUTE_COUNT).all()
    assert sensitivity["rank_p90"].between(1, EXPECTED_ROUTE_COUNT).all()
    assert (sensitivity["rank_p10"] <= sensitivity["median_rank"]).all()
    assert (sensitivity["median_rank"] <= sensitivity["rank_p90"]).all()
    assert sensitivity["rank_stability_score"].between(0, 100).all()


def test_sensitivity_weight_modes_are_reproducible_and_bounded() -> None:
    module = load_pipeline_module("13_sensitivity.py", "route2zero_sensitivity")
    config = load_json(CONFIG / "sensitivity_config.json")
    config = {**config, "simulations": 128}
    policy = load_json(CONFIG / "policy_model.json")
    default = np.asarray([policy["default_weights"][name] for name in module.DIMENSIONS], dtype=float)
    generated = {}
    for mode in config["modes"]:
        first = module.generate_weight_draws(config, default, mode)
        second = module.generate_weight_draws(config, default, mode)
        assert np.array_equal(first, second)
        assert first.shape == (128, 4)
        assert np.allclose(first.sum(axis=1), 1.0)
        assert (first >= 0).all() and (first <= 1).all()
        generated[mode] = first
    assert not np.array_equal(generated["around_default"], generated["broad_simplex"])
    bounds = config["modes"]["custom"]["weight_bounds"]
    for index, name in enumerate(module.DIMENSIONS):
        low, high = bounds[name]
        assert (generated["custom"][:, index] >= low - 1e-7).all()
        assert (generated["custom"][:, index] <= high + 1e-7).all()


def test_optimizer_reports_infeasible_constraints_without_relaxation() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    from portfolio_selection import PortfolioSelectionError, PortfolioSelector

    scores = pd.DataFrame([
        {
            "route_id": "R1", "evidence_grade": "C", "equity_score": 70,
            "active_status": "active", "just_transition_score": 90,
            "top_10_probability": 0.8, "overall_evidence_confidence": 60,
            "primary_city": "City A", "normalized_corridor_id": "C1",
            "robustness_label": "ROBUST PRIORITY",
        },
        {
            "route_id": "R2", "evidence_grade": "C", "equity_score": 65,
            "active_status": "active", "just_transition_score": 85,
            "top_10_probability": 0.7, "overall_evidence_confidence": 60,
            "primary_city": "City B", "normalized_corridor_id": "C2",
            "robustness_label": "ROBUST PRIORITY",
        },
        {
            "route_id": "R3", "evidence_grade": "D", "equity_score": 80,
            "active_status": "active", "just_transition_score": 95,
            "top_10_probability": 0.9, "overall_evidence_confidence": 20,
            "primary_city": "City C", "normalized_corridor_id": "C3",
            "robustness_label": "EVIDENCE-LIMITED",
        },
    ])
    scenario = {
        "max_corridors": 3,
        "minimum_evidence_grade": "C",
        "minimum_equity_score": 40,
        "maximum_evidence_limited_corridors": 1,
        "maximum_corridors_per_primary_city": 2,
        "maximum_route_directions_per_corridor": 1,
        "exclude_inactive_routes": True,
    }
    selector = PortfolioSelector(scores, scenario)
    with pytest.raises(PortfolioSelectionError) as caught:
        selector.select()
    diagnostics = caught.value.diagnostics
    assert diagnostics["required_count"] == 3
    assert diagnostics["selected_count"] == 2
    assert diagnostics["eligible_count"] == 2
    assert diagnostics["selected_route_ids"] == ["R1", "R2"]
    assert "No relaxation" in diagnostics["message"]


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


def test_validation_priority_covers_six_fields_and_reuses_selector(scores: pd.DataFrame) -> None:
    details = pd.read_csv(PROCESSED / "validation_priorities.csv", dtype={"route_id": str})
    payload = load_json(PROCESSED / "validation_priorities.json")
    expected_fields = {
        "operator_readiness",
        "charging_readiness",
        "climate_assumptions",
        "equity_population_exposure",
        "geometry_reliability",
        "service_intensity",
    }
    assert len(details) == EXPECTED_ROUTE_COUNT * len(expected_fields)
    assert set(details["field_name"]) == expected_fields
    assert details.groupby("route_id")["field_name"].nunique().eq(len(expected_fields)).all()
    assert set(details["selection_method"]) == {"deterministic_selection_v2"}
    assert details["portfolio_flip_possible"].notna().all()
    assert details["assumption_source_id"].notna().all()
    assert payload["selection_method"] == "deterministic_selection_v2"
    assert len(payload["routes"]) == EXPECTED_ROUTE_COUNT
    assert all(len(route["priorities"]) == 6 for route in payload["routes"])
    assert set(details["route_id"]) == set(scores["route_id"])


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
