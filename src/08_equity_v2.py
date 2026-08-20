"""Expose equity components without inferring vulnerability from population density."""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from common import CONFIG_DIR, PROCESSED_DIR, ensure_output_dirs, read_json


def main() -> int:
    ensure_output_dirs()
    config = read_json(CONFIG_DIR / "equity_config.json")
    legacy = pd.read_csv(PROCESSED_DIR / "equity_score.csv", dtype={"route_id": str})
    output = legacy[["route_id", "equity_score", "equity_overlap_pct", "corridor_population_proxy"]].copy()
    output = output.rename(columns={"equity_score": "population_exposure_score"})
    output["socioeconomic_score"] = np.nan
    output["accessibility_gap_score"] = np.nan
    output["underserved_overlap_score"] = np.nan
    output["underserved_overlap_available"] = bool(config["underserved_overlap_available"])
    output["equity_score"] = output["population_exposure_score"]
    output["equity_evidence_confidence"] = np.where(output["equity_score"].notna(), 25.0, 0.0)
    output["equity_source_ids"] = np.where(output["equity_score"].notna(), "worldpop_phl_2020_1km", "")
    output["equity_claim_status"] = np.where(output["equity_score"].notna(), "PROXY", "MISSING")
    output["equity_method_version"] = config["version"]
    output["equity_limitation"] = "Population exposure only; no validated socioeconomic, accessibility-gap or settlement-status layer is available."
    output.to_csv(PROCESSED_DIR / "equity_v2.csv", index=False)
    print("[WARN] Equity v2 retains the WorldPop population-exposure proxy; no settlement-status claim is made")
    return 0


if __name__ == "__main__":
    sys.exit(main())
