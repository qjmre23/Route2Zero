"""Run the full deterministic Route2Zero pipeline in dependency order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "01_audit.py",
    "02_geometry.py",
    "03_frequency.py",
    "04_emissions_score.py",
    "05_equity_score.py",
    "06_grid_score.py",
    "07_operator_score.py",
    "08_composite_score.py",
    "09_city_aggregation.py",
    "11_ai_explain.py",
    "10_policy_brief.py",
]


def main() -> int:
    for script in SCRIPTS:
        print(f"\n=== {script} ===", flush=True)
        subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=ROOT, check=True)
    print("\n[PASS] Route2Zero pipeline complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())

