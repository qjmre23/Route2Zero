"""Run fixed-seed policy-weight simulations and quantify rank stability."""

from __future__ import annotations

import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, read_json


DIMENSIONS = ["climate_impact_score", "equity_score", "charging_readiness_score", "operator_effective_score"]


def attach_output(frame: pd.DataFrame, columns: list[str]) -> None:
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    scores = pd.read_csv(score_path, dtype={"route_id": str})
    geodata = gpd.read_file(geo_path)
    scores = scores.drop(columns=[column for column in columns if column in scores.columns], errors="ignore").merge(frame[["route_id", *columns]], on="route_id", how="left")
    geodata = geodata.drop(columns=[column for column in columns if column in geodata.columns], errors="ignore").merge(frame[["route_id", *columns]], on="route_id", how="left")
    scores.to_csv(score_path, index=False)
    geodata.to_file(geo_path, driver="GeoJSON")


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "sensitivity_config.json")
    policy = read_json(CONFIG_DIR / "policy_model.json")
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    matrix = scores[DIMENSIONS].to_numpy(dtype=np.float32)
    simulations = int(config["simulations"])
    seed = int(config["random_seed"])
    rng = np.random.default_rng(seed)
    default = np.asarray([float(policy["default_weights"][name]) for name in DIMENSIONS], dtype=float)
    alpha = default * float(config["dirichlet_concentration"])
    draws = rng.dirichlet(alpha, size=simulations).astype(np.float32)
    scenario_scores = matrix @ draws.T
    order = np.argsort(-scenario_scores, axis=0, kind="stable")
    ranks = np.empty(order.shape, dtype=np.int32)
    ranks[order, np.arange(simulations)] = np.arange(1, len(scores) + 1, dtype=np.int32)[:, None]

    output = scores[["route_id", "rank", "evidence_grade"]].copy()
    output["simulations"] = simulations
    output["top_5_probability"] = np.mean(ranks <= 5, axis=1).round(4)
    output["top_10_probability"] = np.mean(ranks <= 10, axis=1).round(4)
    output["top_20_probability"] = np.mean(ranks <= 20, axis=1).round(4)
    output["median_rank"] = np.median(ranks, axis=1).round().astype(int)
    output["rank_p10"] = np.quantile(ranks, 0.10, axis=1).round().astype(int)
    output["rank_p90"] = np.quantile(ranks, 0.90, axis=1).round().astype(int)
    output["score_p10"] = np.quantile(scenario_scores, 0.10, axis=1).round(2)
    output["score_p90"] = np.quantile(scenario_scores, 0.90, axis=1).round(2)
    width = (output["rank_p90"] - output["rank_p10"]).clip(lower=0)
    output["rank_stability_score"] = (
        output["top_10_probability"] * 70 + (1 - (width / 250).clip(upper=1)) * 30
    ).round(2)
    robust_threshold = float(config["robust_priority_top10_probability"])
    scenario_threshold = float(config["scenario_dependent_top10_probability"])
    conditions = [
        output["evidence_grade"].eq("D") & output["rank"].le(100),
        output["top_10_probability"].ge(robust_threshold),
        output["rank"].le(60) & output["top_10_probability"].ge(scenario_threshold),
        output["median_rank"].gt(100) & width.le(60),
    ]
    labels = ["EVIDENCE-LIMITED", "ROBUST PRIORITY", "SCENARIO-DEPENDENT", "LOW-PRIORITY ROBUST"]
    output["robustness_label"] = np.select(conditions, labels, default="SCENARIO-DEPENDENT")
    output["sensitivity_mode"] = config["mode"]
    output["sensitivity_seed"] = seed
    output.to_csv(PROCESSED_DIR / "sensitivity.csv", index=False)
    columns = [column for column in output.columns if column not in {"route_id", "rank", "evidence_grade"}]
    attach_output(output, columns)
    print(f"[PASS] sensitivity: {simulations:,} fixed-seed scenarios; labels={output['robustness_label'].value_counts().to_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
