"""Apply consent-based operator evidence or an explicit neutral policy prior."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from adapters import MetroManilaOperatorEvidenceAdapter
from common import CONFIG_DIR, PROCESSED_DIR, ROOT, ensure_output_dirs, read_json


def fleet_size_score(values: pd.Series, breakpoints: list[dict[str, float]]) -> pd.Series:
    """Map verified fleet size through transparent, configured planning breakpoints."""
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.lt(0).any():
        raise ValueError("verified_fleet_size must be non-negative")
    ordered = sorted(breakpoints, key=lambda item: float(item["fleet_size"]))
    x = np.asarray([0.0, *[float(item["fleet_size"]) for item in ordered]], dtype=float)
    y = np.asarray([0.0, *[float(item["score"]) for item in ordered]], dtype=float)
    scored = pd.Series(np.nan, index=values.index, dtype=float)
    present = numeric.notna()
    scored.loc[present] = np.interp(numeric.loc[present], x, y, left=0.0, right=float(y[-1]))
    return scored


def score_operator_evidence(
    routes: pd.DataFrame,
    evidence: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    weights = {str(column): float(weight) for column, weight in config["observed_component_weights"].items()}
    if not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("Operator observed component weights must sum to 1.0")
    required_components = set(weights)
    valid_components = {
        "verified_fleet_size", "depot_control_score", "financing_score",
        "organizational_capacity_score", "maintenance_capability_score",
        "willingness_to_participate_score", "modernization_experience_score",
        "charging_site_access_score",
    }
    if required_components != valid_components:
        raise ValueError(
            "Operator weights must configure all and only the eight evidence components; "
            f"found={sorted(required_components)}"
        )
    route_ids = set(routes["route_id"].astype(str))
    unknown = sorted(set(evidence.get("route_id", pd.Series(dtype=str)).dropna().astype(str)) - route_ids)
    if unknown:
        raise ValueError(f"Operator evidence references unknown route IDs: {unknown[:5]}")
    if not evidence.empty:
        evidence = evidence.copy()
        evidence["evidence_date_sort"] = pd.to_datetime(evidence["evidence_date"], errors="coerce")
        evidence = evidence.sort_values(["route_id", "evidence_date_sort"], na_position="first").drop_duplicates("route_id", keep="last")
        evidence = evidence.drop(columns="evidence_date_sort")
    output = routes[["route_id"]].copy().merge(evidence, on="route_id", how="left")
    prior = float(config["neutral_prior"])
    output["operator_policy_prior"] = prior
    output["verified_fleet_size_score"] = fleet_size_score(
        output["verified_fleet_size"], config["fleet_size_score_breakpoints"]
    )

    available_count = pd.Series(0, index=output.index, dtype=int)
    weighted_sum = pd.Series(0.0, index=output.index)
    weight_sum = pd.Series(0.0, index=output.index)
    used_columns: list[str] = []
    for column, weight in weights.items():
        values = output["verified_fleet_size_score"] if column == "verified_fleet_size" else pd.to_numeric(output[column], errors="coerce")
        if column != "verified_fleet_size":
            invalid = values.notna() & ~values.between(0, 100)
            if invalid.any():
                raise ValueError(f"Operator evidence {column} must be between 0 and 100")
        present = values.notna()
        available_count += present.astype(int)
        weighted_sum += values.fillna(0.0) * weight
        weight_sum += present.astype(float) * weight
        used_columns.append(column)
    minimum = int(config["minimum_observed_evidence_fields"])
    sufficient = available_count >= minimum
    output["operator_observed_score"] = np.where(
        sufficient & weight_sum.gt(0), weighted_sum / weight_sum.replace(0, np.nan), np.nan
    )
    output["operator_effective_score"] = pd.Series(output["operator_observed_score"]).fillna(prior).round(2)
    output["operator_evidence_component_count"] = available_count
    output["operator_evidence_completeness"] = (available_count / len(weights) * 100).round(1)
    output["operator_evidence_confidence"] = np.where(
        sufficient, np.minimum(90.0, 45.0 + output["operator_evidence_completeness"] * 0.5), 5.0
    ).round(1)
    output["operator_readiness_placeholder"] = ~sufficient
    output["operator_claim_status"] = np.where(sufficient, "OBSERVED", "NEUTRAL_PRIOR")
    output["operator_source_ids"] = np.where(
        sufficient,
        config["evidence_source_id"] + "|" + config["scoring_source_id"],
        config["prior_source_id"],
    )
    output["operator_components_configured"] = "|".join(used_columns)
    output["operator_method_version"] = config["version"]
    keep = [
        "route_id", "operator_name", "evidence_date", "operator_policy_prior",
        "verified_fleet_size_score", "operator_observed_score", "operator_effective_score",
        "operator_evidence_component_count", "operator_evidence_completeness",
        "operator_evidence_confidence", "operator_readiness_placeholder", "operator_claim_status",
        "operator_source_ids", "operator_components_configured", "operator_method_version",
    ]
    return output[[column for column in keep if column in output.columns]]


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "operator_readiness_config.json")
    routes = pd.read_csv(PROCESSED_DIR / "route_features.csv", dtype={"route_id": str})[["route_id"]]
    evidence = MetroManilaOperatorEvidenceAdapter(ROOT).load_evidence()
    output = score_operator_evidence(routes, evidence, config)
    output.to_csv(PROCESSED_DIR / "operator_readiness_v2.csv", index=False)
    observed = ~output["operator_readiness_placeholder"].astype(bool)
    print(f"[PASS] operator readiness v2: observed={int(observed.sum())}, neutral priors={int((~observed).sum())}; components=8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
