"""Finalize build identity, output checksums, observability and flagship selection."""

from __future__ import annotations

import subprocess
import sys

import geopandas as gpd
import pandas as pd

from common import CONFIG_DIR, MODELS_DIR, PROCESSED_DIR, ROOT, ensure_output_dirs, read_json, sha256_file, stable_hash, utc_now_iso, write_json


REQUIRED_OUTPUTS = [
    "route_features.csv", "ml_service_intensity.csv", "corridor_typology.csv", "climate_impact.csv",
    "equity_v2.csv", "charging_readiness.csv", "operator_readiness_v2.csv", "geometry_reliability.csv",
    "evidence_confidence.csv", "route2zero_scores.csv", "route2zero_scores.geojson", "sensitivity.csv",
    "portfolio_scenarios.json", "validation_priorities.json", "route_planner_cache.json", "source_manifest.json",
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
        raise FileNotFoundError(f"Required Route2Zero 2.0 outputs missing: {missing}")
    config_checksums = {path.name: sha256_file(path) for path in sorted(CONFIG_DIR.glob("*.json"))}
    source_manifest = read_json(PROCESSED_DIR / "source_manifest.json")
    source_checksums = {source["source_id"]: source["checksum_sha256"] for source in source_manifest["sources"]}
    service_meta = read_json(MODELS_DIR / "service_intensity_metadata.json")
    typology_meta = read_json(MODELS_DIR / "corridor_typology_metadata.json")
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    portfolio = read_json(PROCESSED_DIR / "portfolio_scenarios.json")["scenarios"][0]
    build_timestamp = utc_now_iso()
    identity = {
        "pipeline_version": "2.0.0",
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

    output_checksums = {name: sha256_file(PROCESSED_DIR / name) for name in REQUIRED_OUTPUTS if name not in {"route2zero_scores.csv", "route2zero_scores.geojson"}}
    output_checksums["route2zero_scores.csv"] = sha256_file(score_path)
    output_checksums["route2zero_scores.geojson"] = sha256_file(geo_path)
    selected_candidates = scores[
        scores["phase1_selected"].astype(bool)
        & scores["robustness_label"].eq("ROBUST PRIORITY")
    ]
    candidates = selected_candidates if not selected_candidates.empty else scores[scores["phase1_selected"].astype(bool)]
    flagship = candidates.sort_values(["overall_evidence_confidence", "just_transition_score", "route_id"], ascending=[False, False, True]).iloc[0]
    flagship_payload = {
        "selection_rule": "Among Phase-1 corridors, prefer ROBUST PRIORITY; then highest evidence confidence, priority score and stable route ID.",
        "route_id": flagship["route_id"],
        "route_long_name": flagship["route_long_name"],
        "rank": int(flagship["rank"]),
        "priority_score": round(float(flagship["just_transition_score"]), 2),
        "evidence_grade": flagship["evidence_grade"],
        "evidence_confidence": round(float(flagship["overall_evidence_confidence"]), 2),
        "top_10_probability": round(float(flagship["top_10_probability"]), 4),
        "climate_low_t_year": round(float(flagship["net_co2e_avoided_t_year_low"]), 1),
        "climate_high_t_year": round(float(flagship["net_co2e_avoided_t_year_high"]), 1),
        "scenario_id": flagship["scenario_id"],
        "portfolio_scenario_id": flagship["portfolio_scenario_id"],
        "build_id": build_id,
    }
    write_json(PROCESSED_DIR / "flagship_route.json", flagship_payload)

    validation_count = int((~scores["validation_status"].eq("historic_only")).sum())
    warnings = []
    if validation_count == 0:
        warnings.append("No current route validation records have been supplied; all service status remains historic-only.")
    if int((~scores["operator_readiness_placeholder"].astype(bool)).sum()) == 0:
        warnings.append("No consent-based operator evidence has been supplied; the neutral prior remains active.")
    if int(scores["utility_capacity_verified"].astype(bool).sum()) == 0:
        warnings.append("No utility capacity is verified; charging scores use mapped proximity and energy-demand screening only.")
    if not bool(service_meta["meaningful_vs_baseline"]):
        warnings.append("The service-intensity model did not beat the configured baseline and is experimental only.")
    report = {
        "status": "PASS_WITH_WARNINGS" if warnings else "PASS",
        "pipeline_version": "2.0.0",
        "build_id": build_id,
        "build_timestamp_utc": build_timestamp,
        "rows_processed": len(scores),
        "score_complete_count": int(scores["score_complete"].sum()),
        "current_validation_count": validation_count,
        "robust_priority_count": int(scores["robustness_label"].eq("ROBUST PRIORITY").sum()),
        "phase1_corridor_count": int(scores["phase1_selected"].astype(bool).sum()),
        "warnings": warnings,
    }
    write_json(PROCESSED_DIR / "pipeline_report.json", report)
    manifest = {
        "build_id": build_id,
        "build_timestamp_utc": build_timestamp,
        "git_commit": git_commit(),
        "pipeline_version": "2.0.0",
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
        "default_scenario_id": str(scores["scenario_id"].iloc[0]),
        "default_portfolio_scenario_id": portfolio["scenario_id"],
        "random_seeds": {"model_and_typology": 20260820, "sensitivity": 20260820},
        "flagship_route_id": flagship_payload["route_id"],
        "pipeline_report": report,
    }
    write_json(PROCESSED_DIR / "build_manifest.json", manifest)
    print(f"[PASS] final build manifest: {build_id}; flagship={flagship_payload['route_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
