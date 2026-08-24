"""Run the complete Route2Zero pipeline in dependency order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "00_source_manifest.py",
    "01_audit.py",
    "01b_osm_route_validation.py",
    "02_geometry.py",
    "02b_geometry_reliability.py",
    "03_frequency.py",
    "04_emissions_score.py",
    "05_equity_score.py",
    "06_grid_score.py",
    "07_operator_score.py",
    "04_feature_engineering.py",
    "05_ml_service_intensity.py",
    "06_corridor_typology.py",
    "07_climate_impact.py",
    "08_equity_v2.py",
    "09_charging_readiness.py",
    "10_operator_readiness.py",
    "11_evidence_confidence.py",
    "12_composite_score.py",
    "15_city_aggregation.py",
    "13_sensitivity.py",
    "14_portfolio_optimizer.py",
    "14b_feasibility_cost.py",
    "16_validation_priority.py",
    "17_ai_planner.py",
    "18_policy_brief.py",
    "19_finalize_manifest.py",
]


def main() -> int:
    for script in SCRIPTS:
        print(f"\n=== {script} ===", flush=True)
        subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=ROOT, check=True)
    print("\n[PASS] Route2Zero pipeline complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
