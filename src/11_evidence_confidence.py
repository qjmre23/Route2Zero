"""Calculate evidence confidence separately from prediction error and rank stability."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, read_json


def evidence_grade(score: float, thresholds: dict[str, float]) -> str:
    for grade in ("A", "B", "C", "D"):
        if score >= float(thresholds[grade]):
            return grade
    return "D"


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "evidence_confidence_config.json")
    validation = pd.read_csv(PROCESSED_DIR / "route_validation.csv", dtype={"route_id": str})
    geometry = pd.read_csv(PROCESSED_DIR / "geometry_reliability.csv", dtype={"route_id": str})
    equity = pd.read_csv(PROCESSED_DIR / "equity_v2.csv", dtype={"route_id": str})
    charging = pd.read_csv(PROCESSED_DIR / "charging_readiness.csv", dtype={"route_id": str})
    operator = pd.read_csv(PROCESSED_DIR / "operator_readiness_v2.csv", dtype={"route_id": str})
    ml = pd.read_csv(PROCESSED_DIR / "ml_service_intensity.csv", dtype={"route_id": str})
    output = validation[["route_id", "validation_status", "active_status"]]
    for frame in (geometry, equity, charging, operator, ml):
        output = output.merge(frame, on="route_id", how="left")

    validation_scores = config["validation_status_scores"]
    output["freshness_score"] = output["validation_status"].map(validation_scores).fillna(10.0)
    output["climate_evidence_confidence"] = np.where(output["ml_service_intensity_used"].fillna(False).astype(bool), 45.0, 35.0)
    output["equity_evidence_confidence"] = output["equity_evidence_confidence"].fillna(0.0)
    output["charging_evidence_confidence"] = output["charging_evidence_confidence"].fillna(0.0)
    output["operator_evidence_confidence"] = output["operator_evidence_confidence"].fillna(0.0)
    output["geometry_evidence_confidence"] = output["geometry_reliability_score"].fillna(0.0)
    output["directness_score"] = output[[
        "climate_evidence_confidence", "equity_evidence_confidence", "charging_evidence_confidence", "operator_evidence_confidence",
    ]].mean(axis=1)
    output["spatial_specificity_score"] = (
        output["geometry_evidence_confidence"] * 0.65 + output["charging_evidence_confidence"] * 0.35
    )
    available = pd.DataFrame({
        "climate": output["climate_evidence_confidence"] > 0,
        "equity": output["equity_evidence_confidence"] > 0,
        "charging": output["charging_evidence_confidence"] > 0,
        "operator": ~output["operator_readiness_placeholder"].fillna(True).astype(bool),
        "geometry": output["geometry_evidence_confidence"] > 0,
    })
    output["completeness_score"] = available.mean(axis=1) * 100
    output["external_validation_score"] = output["freshness_score"]
    output["model_reliability_score"] = np.where(output["ml_model_meaningful_vs_baseline"].fillna(False).astype(bool), 75.0, 25.0)
    weights = config["weights"]
    output["overall_evidence_confidence"] = (
        output["freshness_score"] * float(weights["freshness"])
        + output["directness_score"] * float(weights["directness"])
        + output["spatial_specificity_score"] * float(weights["spatial_specificity"])
        + output["completeness_score"] * float(weights["completeness"])
        + output["external_validation_score"] * float(weights["external_validation"])
        + output["model_reliability_score"] * float(weights["model_reliability"])
    ).round(2)
    output["evidence_grade"] = output["overall_evidence_confidence"].map(lambda value: evidence_grade(float(value), config["grade_thresholds"]))
    output["highest_value_missing_evidence"] = np.select(
        [
            output["operator_readiness_placeholder"].fillna(True).astype(bool),
            ~output["utility_capacity_verified"].fillna(False).astype(bool),
            output["validation_status"].eq("historic_only"),
        ],
        ["operator readiness evidence", "utility capacity and charging-site evidence", "current route status"],
        default="no critical evidence gap recorded",
    )
    output["evidence_limitations"] = (
        "Historic service baseline; population exposure proxy; utility capacity unverified; "
        + np.where(output["operator_readiness_placeholder"].fillna(True).astype(bool), "operator neutral prior.", "operator evidence supplied.")
    )
    output["evidence_confidence_method"] = config["version"] + "_deterministic_rules"
    output["evidence_claim_status"] = "DERIVED"
    keep = [
        "route_id", "validation_status", "active_status", "freshness_score", "directness_score",
        "spatial_specificity_score", "completeness_score", "external_validation_score", "model_reliability_score",
        "climate_evidence_confidence", "equity_evidence_confidence", "charging_evidence_confidence",
        "operator_evidence_confidence", "geometry_evidence_confidence", "overall_evidence_confidence",
        "evidence_grade", "highest_value_missing_evidence", "evidence_limitations",
        "evidence_confidence_method", "evidence_claim_status",
    ]
    output[keep].to_csv(PROCESSED_DIR / "evidence_confidence.csv", index=False)
    print(f"[PASS] evidence confidence grades: {output['evidence_grade'].value_counts().to_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
