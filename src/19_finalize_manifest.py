"""Finalize build identity, output checksums, observability and flagship selection."""

from __future__ import annotations

import subprocess
import sys

import geopandas as gpd
import pandas as pd

from common import (
    CONFIG_DIR,
    MODELS_DIR,
    PROCESSED_DIR,
    ROOT,
    ensure_output_dirs,
    normalize_text_newlines,
    read_json,
    sha256_file,
    stable_hash,
    utc_now_iso,
    validate_claim_status_columns,
    write_json,
)


REQUIRED_OUTPUTS = [
    "route_features.csv", "ml_service_intensity.csv", "corridor_typology.csv", "climate_impact.csv",
    "equity_v2.csv", "charging_readiness.csv", "operator_readiness_v2.csv", "geometry_reliability.csv",
    "evidence_confidence.csv", "route2zero_scores.csv", "route2zero_scores.geojson", "sensitivity.csv",
    "sensitivity_modes.csv",
    "portfolio_scenarios.json", "validation_priorities.json", "route_planner_cache.json", "source_manifest.json",
    "route_validation.csv", "route_cities.csv", "city_summary.csv", "model_metrics.json",
    "portfolio_membership.csv", "validation_priorities.csv", "planner_summary.json",
    "osm_route_validation.csv", "osm_route_geometry.geojson", "feasibility_cost_routes.csv",
    "feasibility_cost_scenarios.json",
]

FINAL_REPORT_OUTPUTS = ["pipeline_report.json", "flagship_route.json"]
MODEL_ARTIFACTS = [
    "service_intensity.joblib",
    "service_intensity_metadata.json",
    "corridor_typology.joblib",
    "corridor_typology_metadata.json",
]


def git_commit() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "unavailable"


def main() -> int:
    ensure_output_dirs()
    missing = [name for name in REQUIRED_OUTPUTS if not (PROCESSED_DIR / name).exists()]
    if missing:
        raise FileNotFoundError(f"Required Route2Zero outputs missing: {missing}")
    for name in REQUIRED_OUTPUTS:
        normalize_text_newlines(PROCESSED_DIR / name)
    for name in MODEL_ARTIFACTS:
        if name.endswith(".json"):
            normalize_text_newlines(MODELS_DIR / name)
    config_checksums = {path.name: sha256_file(path) for path in sorted(CONFIG_DIR.glob("*.json"))}
    source_manifest = read_json(PROCESSED_DIR / "source_manifest.json")
    source_checksums = {source["source_id"]: source.get("checksum_sha256") for source in source_manifest["sources"]}
    service_meta = read_json(MODELS_DIR / "service_intensity_metadata.json")
    typology_meta = read_json(MODELS_DIR / "corridor_typology_metadata.json")
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    claim_columns = validate_claim_status_columns(scores)
    portfolio = read_json(PROCESSED_DIR / "portfolio_scenarios.json")["scenarios"][0]
    build_timestamp = utc_now_iso()
    identity = {
        "pipeline_version": "2.1.0",
        "config_checksums": config_checksums,
        "source_checksums": source_checksums,
        "model_versions": [service_meta["model_version"], typology_meta["model_version"]],
        "scenario_id": str(scores["scenario_id"].iloc[0]),
        "portfolio_scenario_id": portfolio["scenario_id"],
    }
    build_id = "r2z-" + stable_hash(identity, 12)
    scores["build_id"] = build_id
    scores["build_timestamp_utc"] = build_timestamp
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    scores.to_csv(score_path, index=False)
    geodata = gpd.read_file(geo_path)
    geodata["build_id"] = build_id
    geodata["build_timestamp_utc"] = build_timestamp
    geodata.to_file(geo_path, driver="GeoJSON")
    normalize_text_newlines(score_path)
    normalize_text_newlines(geo_path)

    selected_candidates = scores[
        scores["phase1_selected"].astype(bool)
        & scores["robustness_label"].eq("ROBUST PRIORITY")
    ]
    candidates = selected_candidates if not selected_candidates.empty else scores[scores["phase1_selected"].astype(bool)]
    flagship_is_phase1_selected = not candidates.empty
    if candidates.empty:
        candidates = scores[scores["just_transition_score"].notna()]
    if candidates.empty:
        raise ValueError("No scored route is available for the analytical flagship record")
    flagship = candidates.sort_values(["overall_evidence_confidence", "just_transition_score", "route_id"], ascending=[False, False, True]).iloc[0]
    flagship_payload = {
        "selection_rule": (
            "Among Phase-1 corridors, prefer ROBUST PRIORITY; then highest evidence confidence, priority score and stable route ID."
            if flagship_is_phase1_selected
            else "Portfolio infeasible: analytical example only, chosen by evidence confidence, priority score and stable route ID; not Phase-1 selected."
        ),
        "phase1_selected": flagship_is_phase1_selected,
        "route_id": flagship["route_id"],
        "route_long_name": flagship["route_long_name"],
        "rank": int(flagship["rank"]),
        "priority_score": round(float(flagship["just_transition_score"]), 2),
        "evidence_grade": flagship["evidence_grade"],
        "evidence_confidence": round(float(flagship["overall_evidence_confidence"]), 2),
        "top_10_probability": round(float(flagship["top_10_probability"]), 4),
        "climate_low_t_year": round(float(flagship["net_co2e_avoided_t_year_low"]), 1),
        "climate_base_t_year": round(float(flagship["net_co2e_avoided_t_year_base"]), 1),
        "climate_high_t_year": round(float(flagship["net_co2e_avoided_t_year_high"]), 1),
        "validation_status": flagship.get("validation_status", "historic_only"),
        "active_status": flagship.get("active_status", "uncertain"),
        "validation_date": flagship.get("validation_date", ""),
        "validation_source_reference": flagship.get("source_reference", ""),
        "geometry_source": flagship.get("geometry_source", ""),
        "geometry_claim_status": flagship.get("route_geometry_claim_status", "DERIVED"),
        "scenario_id": flagship["scenario_id"],
        "portfolio_scenario_id": flagship["portfolio_scenario_id"],
        "build_id": build_id,
    }
    write_json(PROCESSED_DIR / "flagship_route.json", flagship_payload)

    validation_count = int((~scores["validation_status"].eq("historic_only")).sum())
    active_validation_count = int(scores["active_status"].eq("active").sum())
    usable_geometry_count = int(scores["geometry_source"].isin(["shape", "osm_relation"]).sum())
    operator_search_attempt_count = int(scores["operator_search_note"].fillna("").ne("No route-specific desk search recorded in this release.").sum())
    operator_reference_observed_count = int(scores["operator_reference_status"].eq("OBSERVED").sum())
    critical_missing_values = {
        column: int(scores[column].isna().sum())
        for column in [
            "just_transition_score",
            "ml_service_intensity_prediction",
            "net_co2e_avoided_t_year_base",
            "equity_score",
            "charging_readiness_score",
            "operator_effective_score",
            "overall_evidence_confidence",
        ]
    }
    warnings = []
    if validation_count == 0:
        warnings.append("No current route validation records have been supplied; all service status remains historic-only.")
    if int((~scores["operator_readiness_placeholder"].astype(bool)).sum()) == 0:
        warnings.append(
            f"No consent-based operator readiness evidence has been supplied; the neutral prior remains active. "
            f"Desk searches are recorded for {operator_search_attempt_count} Phase-1 corridors and found "
            f"{operator_reference_observed_count} named operator reference that does not satisfy the readiness-evidence threshold."
        )
    if int(scores["utility_capacity_verified"].astype(bool).sum()) == 0:
        warnings.append("No utility capacity is verified; charging scores use mapped proximity and energy-demand screening only.")
    if portfolio["status"] == "infeasible":
        warnings.append("The configured Phase-1 portfolio is infeasible; no constraint was relaxed and no route was selected.")
    if not bool(service_meta["meaningful_vs_baseline"]):
        warnings.append("The service-intensity model did not beat the configured baseline and is experimental only.")
    report = {
        "status": "PASS_WITH_WARNINGS" if warnings else "PASS",
        "pipeline_version": "2.1.0",
        "build_id": build_id,
        "build_timestamp_utc": build_timestamp,
        "rows_processed": len(scores),
        "score_complete_count": int(scores["score_complete"].sum()),
        "reduced_information_score_count": int(scores.get("reduced_information_score", pd.Series(False, index=scores.index)).astype(bool).sum()),
        "current_validation_count": validation_count,
        "active_validation_count": active_validation_count,
        "usable_geometry_count": usable_geometry_count,
        "osm_observed_geometry_count": int(scores["geometry_source"].eq("osm_relation").sum()),
        "operator_search_attempt_count": operator_search_attempt_count,
        "operator_reference_observed_count": operator_reference_observed_count,
        "robust_priority_count": int(scores["robustness_label"].eq("ROBUST PRIORITY").sum()),
        "phase1_corridor_count": int(scores["phase1_selected"].astype(bool).sum()),
        "source_dates": {
            source["source_id"]: source["retrieval_date"] for source in source_manifest["sources"]
        },
        "optional_sources_missing": [
            source["source_id"] for source in source_manifest["sources"]
            if not source.get("required", True) and not source.get("available", True)
        ],
        "model_versions": {
            "service_intensity": service_meta["model_version"],
            "corridor_typology": typology_meta["model_version"],
        },
        "claim_status_columns_checked": claim_columns,
        "critical_missing_values": critical_missing_values,
        "warnings": warnings,
    }
    write_json(PROCESSED_DIR / "pipeline_report.json", report)
    for name in [*REQUIRED_OUTPUTS, *FINAL_REPORT_OUTPUTS]:
        normalize_text_newlines(PROCESSED_DIR / name)
    output_checksums = {
        name: sha256_file(PROCESSED_DIR / name)
        for name in [*REQUIRED_OUTPUTS, *FINAL_REPORT_OUTPUTS]
    }
    model_artifact_checksums = {
        name: sha256_file(MODELS_DIR / name) for name in MODEL_ARTIFACTS
    }
    manifest = {
        "build_id": build_id,
        "build_timestamp_utc": build_timestamp,
        "git_commit": git_commit(),
        "pipeline_version": "2.1.0",
        "model_versions": {
            "service_intensity": service_meta["model_version"],
            "corridor_typology": typology_meta["model_version"],
        },
        "model_metrics_summary": {
            "service_model": service_meta["model_name"],
            "service_mae": service_meta["selected_metrics"]["mae"],
            "service_rmse": service_meta["selected_metrics"]["rmse"],
            "service_r2": service_meta["selected_metrics"]["r2"],
            "baseline_mae": service_meta["selected_metrics"]["baseline_mae"],
            "typology_k": typology_meta["selected_k"],
            "typology_silhouette": typology_meta["selected_silhouette_score"],
        },
        "config_checksums": config_checksums,
        "source_checksums": source_checksums,
        "output_checksums": output_checksums,
        "model_artifact_checksums": model_artifact_checksums,
        "default_scenario_id": str(scores["scenario_id"].iloc[0]),
        "default_portfolio_scenario_id": portfolio["scenario_id"],
        "random_seeds": {
            "model_and_typology": 20260820,
            "sensitivity_around_default": 20260820,
            "sensitivity_broad_simplex": 20260821,
            "sensitivity_custom": 20260822
        },
        "flagship_route_id": flagship_payload["route_id"],
        "pipeline_report": report,
    }
    write_json(PROCESSED_DIR / "build_manifest.json", manifest)
    print(f"[PASS] final build manifest: {build_id}; flagship={flagship_payload['route_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
