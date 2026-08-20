"""Run reproducible policy-weight sensitivity modes and quantify rank stability."""

from __future__ import annotations

import sys

import geopandas as gpd
import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, read_json


DIMENSIONS = ["climate_impact_score", "equity_score", "charging_readiness_score", "operator_effective_score"]


def generate_weight_draws(
    config: dict,
    default_weights: np.ndarray,
    mode: str,
) -> np.ndarray:
    """Generate one deterministic simplex sample for the requested configured mode."""
    if mode not in config["modes"]:
        raise ValueError(f"Unknown sensitivity mode: {mode}")
    mode_config = config["modes"][mode]
    simulations = int(config["simulations"])
    seed = int(config["random_seed"]) + int(mode_config.get("seed_offset", 0))
    rng = np.random.default_rng(seed)
    method = mode_config["method"]
    if method == "dirichlet_around_default":
        alpha = default_weights * float(mode_config["dirichlet_concentration"])
        draws = rng.dirichlet(alpha, size=simulations)
    elif method == "dirichlet_broad_simplex":
        alpha = np.full(len(default_weights), float(mode_config["alpha"]), dtype=float)
        draws = rng.dirichlet(alpha, size=simulations)
    elif method == "bounded_simplex_rejection":
        bounds = np.asarray([mode_config["weight_bounds"][name] for name in DIMENSIONS], dtype=float)
        if bounds.shape != (len(DIMENSIONS), 2) or np.any(bounds[:, 0] < 0) or np.any(bounds[:, 1] > 1):
            raise ValueError("Custom sensitivity weight bounds must be [low, high] pairs within [0, 1]")
        if bounds[:, 0].sum() > 1 or bounds[:, 1].sum() < 1:
            raise ValueError("Custom sensitivity weight bounds do not intersect the simplex")
        accepted: list[np.ndarray] = []
        accepted_count = 0
        attempts = 0
        while accepted_count < simulations and attempts < 200:
            batch_size = max(2000, (simulations - accepted_count) * 5)
            raw = rng.uniform(bounds[:, 0], bounds[:, 1], size=(batch_size, len(DIMENSIONS)))
            candidates = raw / raw.sum(axis=1, keepdims=True)
            mask = ((candidates >= bounds[:, 0]) & (candidates <= bounds[:, 1])).all(axis=1)
            if mask.any():
                accepted.append(candidates[mask])
                accepted_count += int(mask.sum())
            attempts += 1
        if accepted_count < simulations:
            raise ValueError("Unable to draw enough custom bounded-simplex weights; revise configured bounds")
        draws = np.vstack(accepted)[:simulations]
    else:
        raise ValueError(f"Unsupported sensitivity method: {method}")
    if draws.shape != (simulations, len(DIMENSIONS)) or not np.allclose(draws.sum(axis=1), 1.0):
        raise AssertionError("Sensitivity draw generator violated the simplex contract")
    return draws.astype(np.float32)


def score_draws(matrix: np.ndarray, draws: np.ndarray, reduced_penalty: float) -> np.ndarray:
    """Renormalize weights over available evidence and penalize reduced-information scores."""
    available = np.isfinite(matrix).astype(np.float32)
    values = np.nan_to_num(matrix, nan=0.0).astype(np.float32)
    numerator = values @ draws.T
    denominator = available @ draws.T
    result = np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan, dtype=np.float32),
        where=denominator > 0,
    )
    incomplete = available.sum(axis=1) < matrix.shape[1]
    result[incomplete] *= float(reduced_penalty)
    return result


def summarize_mode(
    scores: pd.DataFrame,
    scenario_scores: np.ndarray,
    config: dict,
    mode: str,
) -> pd.DataFrame:
    simulations = scenario_scores.shape[1]
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
    output["score_p10"] = np.nanquantile(scenario_scores, 0.10, axis=1).round(2)
    output["score_p90"] = np.nanquantile(scenario_scores, 0.90, axis=1).round(2)
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
    output["sensitivity_mode"] = mode
    output["sensitivity_method"] = config["modes"][mode]["method"]
    output["sensitivity_seed"] = int(config["random_seed"]) + int(config["modes"][mode].get("seed_offset", 0))
    return output


def attach_output(frame: pd.DataFrame, columns: list[str]) -> None:
    score_path = PROCESSED_DIR / "route2zero_scores.csv"
    geo_path = PROCESSED_DIR / "route2zero_scores.geojson"
    scores = pd.read_csv(score_path, dtype={"route_id": str})
    geodata = gpd.read_file(geo_path)
    scores = scores.drop(columns=[column for column in columns if column in scores.columns], errors="ignore").merge(
        frame[["route_id", *columns]], on="route_id", how="left"
    )
    geodata = geodata.drop(columns=[column for column in columns if column in geodata.columns], errors="ignore").merge(
        frame[["route_id", *columns]], on="route_id", how="left"
    )
    scores.to_csv(score_path, index=False)
    geodata.to_file(geo_path, driver="GeoJSON")


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "sensitivity_config.json")
    policy = read_json(CONFIG_DIR / "policy_model.json")
    scores = pd.read_csv(PROCESSED_DIR / "route2zero_scores.csv", dtype={"route_id": str})
    matrix = scores[DIMENSIONS].to_numpy(dtype=np.float32)
    default_weights = np.asarray([float(policy["default_weights"][name]) for name in DIMENSIONS], dtype=float)
    outputs: list[pd.DataFrame] = []
    for mode in config["modes"]:
        draws = generate_weight_draws(config, default_weights, mode)
        scenario_scores = score_draws(matrix, draws, float(policy["reduced_information_penalty"]))
        outputs.append(summarize_mode(scores, scenario_scores, config, mode))
    modes_output = pd.concat(outputs, ignore_index=True)
    modes_output.to_csv(PROCESSED_DIR / "sensitivity_modes.csv", index=False)
    default_mode = config["default_mode"]
    output = modes_output[modes_output["sensitivity_mode"].eq(default_mode)].copy()
    output.to_csv(PROCESSED_DIR / "sensitivity.csv", index=False)
    columns = [column for column in output.columns if column not in {"route_id", "rank", "evidence_grade"}]
    attach_output(output, columns)
    print(
        f"[PASS] sensitivity: {len(config['modes'])} modes x {int(config['simulations']):,} fixed-seed scenarios; "
        f"default={default_mode}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
