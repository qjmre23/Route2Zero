"""Apply verified operator evidence where available, otherwise preserve a neutral prior."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ROOT, ensure_output_dirs, read_json


COMPONENTS = {
    "depot_control_score": "depot",
    "financing_score": "financing",
    "organizational_capacity_score": "organization",
    "maintenance_capability_score": "maintenance",
    "willingness_to_participate_score": "participation",
}


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "operator_readiness_config.json")
    routes = pd.read_csv(PROCESSED_DIR / "route_features.csv", dtype={"route_id": str})[["route_id"]]
    evidence = pd.read_csv(ROOT / "data" / "validated" / "operator_evidence.csv", dtype={"route_id": str})
    if not evidence.empty:
        evidence = evidence.drop_duplicates("route_id", keep="last")
    output = routes.merge(evidence, on="route_id", how="left")
    prior = float(config["neutral_prior"])
    output["operator_policy_prior"] = prior
    available_count = pd.Series(0, index=output.index, dtype=int)
    weighted_sum = pd.Series(0.0, index=output.index)
    weight_sum = pd.Series(0.0, index=output.index)
    for column, key in COMPONENTS.items():
        values = pd.to_numeric(output.get(column), errors="coerce")
        weight = float(config["observed_component_weights"][key])
        present = values.notna()
        available_count += present.astype(int)
        weighted_sum += values.fillna(0) * weight
        weight_sum += present.astype(float) * weight
    fleet_present = pd.to_numeric(output.get("verified_fleet_size"), errors="coerce").notna()
    available_count += fleet_present.astype(int)
    minimum = int(config["minimum_observed_evidence_fields"])
    sufficient = available_count >= minimum
    output["operator_observed_score"] = np.where(sufficient & weight_sum.gt(0), weighted_sum / weight_sum.replace(0, np.nan), np.nan)
    output["operator_effective_score"] = pd.Series(output["operator_observed_score"]).fillna(prior).round(2)
    output["operator_evidence_completeness"] = (available_count / (len(COMPONENTS) + 1) * 100).round(1)
    output["operator_evidence_confidence"] = np.where(sufficient, np.minimum(90, 45 + output["operator_evidence_completeness"] * 0.5), 5.0)
    output["operator_readiness_placeholder"] = ~sufficient
    output["operator_claim_status"] = np.where(sufficient, "OBSERVED", "NEUTRAL_PRIOR")
    output["operator_source_ids"] = np.where(sufficient, "operator_evidence_ledger", config["prior_source_id"])
    output["operator_method_version"] = config["version"]
    keep = [
        "route_id", "operator_name", "evidence_date", "operator_policy_prior", "operator_observed_score",
        "operator_effective_score", "operator_evidence_completeness", "operator_evidence_confidence",
        "operator_readiness_placeholder", "operator_claim_status", "operator_source_ids", "operator_method_version",
    ]
    output[[column for column in keep if column in output.columns]].to_csv(PROCESSED_DIR / "operator_readiness_v2.csv", index=False)
    print(f"[PASS] operator readiness v2: observed={int(sufficient.sum())}, neutral priors={int((~sufficient).sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
