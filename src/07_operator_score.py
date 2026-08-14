"""Task 8: apply a transparent neutral operator-readiness placeholder."""

from __future__ import annotations

import sys

import geopandas as gpd
import pandas as pd

from common import PROCESSED_DIR, ensure_output_dirs


DEFAULT_OPERATOR_READINESS_SCORE = 50.0


def main() -> int:
    ensure_output_dirs()
    routes = gpd.read_file(PROCESSED_DIR / "jeepney_routes.geojson")[["route_id"]]
    override_path = PROCESSED_DIR / "operator_overrides.csv"
    if not override_path.exists():
        pd.DataFrame(columns=["route_id", "operator_readiness_score", "notes"]).to_csv(
            override_path, index=False
        )
    overrides = pd.read_csv(override_path, dtype={"route_id": str})
    if not overrides.empty:
        overrides["operator_readiness_score"] = pd.to_numeric(
            overrides["operator_readiness_score"], errors="coerce"
        )
        invalid = overrides["operator_readiness_score"].dropna().loc[
            lambda values: ~values.between(0, 100)
        ]
        if not invalid.empty:
            raise ValueError("Operator overrides must be between 0 and 100")

    output = pd.DataFrame({"route_id": routes["route_id"]})
    output["operator_readiness_score"] = DEFAULT_OPERATOR_READINESS_SCORE
    output["operator_notes"] = ""
    output["operator_source"] = "neutral_placeholder_awaiting_cooperative_financing_data"
    if not overrides.empty:
        output = output.merge(overrides, on="route_id", how="left", suffixes=("", "_override"))
        has_override = output["operator_readiness_score_override"].notna()
        output.loc[has_override, "operator_readiness_score"] = output.loc[
            has_override, "operator_readiness_score_override"
        ]
        output.loc[has_override, "operator_notes"] = output.loc[has_override, "notes"].fillna("")
        output.loc[has_override, "operator_source"] = "pilot_workshop_override"
        output = output.drop(columns=["operator_readiness_score_override", "notes"])
    output["operator_readiness_placeholder"] = output["operator_source"].str.startswith("neutral_placeholder")
    output.to_csv(PROCESSED_DIR / "operator_readiness.csv", index=False)
    print(f"[PASS] operator readiness rows: {len(output):,}")
    print(f"[INFO] placeholders: {int(output['operator_readiness_placeholder'].sum()):,}")
    print(f"[PASS] wrote {PROCESSED_DIR / 'operator_readiness.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

